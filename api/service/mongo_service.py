#!/usr/bin/env python3

from datetime import date, datetime, timedelta
from typing import Literal

from fastapi import HTTPException
from pymongo.asynchronous.database import AsyncDatabase

from api.schema.mongo_reading import (
    MongoReadingCreate,
    MongoReadingUpdate,
    MongoReadingResponse,
    PaginatedMongoReadings,
    DailyReadingResponse,
    PaginatedDailyReadings,
)

# Same order as sub_metering_wh in every reading
SUB_METER_NAMES = ["kitchen", "laundry", "water_heater_ac"]

READING_FIELDS = ["time", "global_active_power", "global_reactive_power",
                  "voltage", "global_intensity", "sub_metering_wh"]


def start_of_day(moment:datetime):
    """
    Midnight of the day the moment falls in, which is how day documents are keyed
    """
    return datetime.combine(moment.date(), datetime.min.time())


def build_summary(readings:list, minutes_missing:int):
    """
    Recompute a day's summary from its minute readings, the same way the loader does
    """
    if not readings:
        return None
    peak_reading = max(readings, key=lambda reading: reading["global_active_power"])
    return {
        "minutes_recorded": len(readings),
        "minutes_missing": minutes_missing,
        "total_kwh": round(sum(reading["global_active_power"] for reading in readings) / 60, 3),
        "avg_voltage": round(sum(reading["voltage"] for reading in readings) / len(readings), 2),
        "peak_power_kw": float(peak_reading["global_active_power"]),
        "peak_time": peak_reading["time"],
        "sub_metering_kwh": {
            sub_meter_name: round(sum(reading["sub_metering_wh"][position] for reading in readings) / 1000, 3)
            for position, sub_meter_name in enumerate(SUB_METER_NAMES)
        },
    }


class HouseholdMongoCRUD:
    def __init__(self, database:AsyncDatabase):
        self.database = database
        self.daily_readings = database["daily_readings"]

    def resolve_info_type(self, type:Literal["minute", "day"]):
        """
        Return the record schema and paginated schema for minute or daily data
        """
        if type == "day":
            return DailyReadingResponse, PaginatedDailyReadings
        return MongoReadingResponse, PaginatedMongoReadings

    async def paginate(self,
                       type:Literal["minute", "day"],
                       nbr_page:int,
                       nbr_data:int,
                       newest_first:bool = False,
                       start_day:datetime | None = None,
                       end_day:datetime | None = None
                       ):
        """
        Return one page of minute readings or days, optionally from start_day (included) to end_day (excluded)
        """
        record_schema, paginated_schema = self.resolve_info_type(type)

        day_filter = {}
        if start_day is not None or end_day is not None:
            day_filter["date"] = {}
            if start_day is not None:
                day_filter["date"]["$gte"] = start_day
            if end_day is not None:
                day_filter["date"]["$lt"] = end_day

        sort_direction = -1 if newest_first else 1
        # Sorting on the {household_id, date} index keys avoids sorting large documents in memory
        sort_order = {"household_id": sort_direction, "date": sort_direction}

        if type == "day":
            total_records = await self.daily_readings.count_documents(day_filter)
            day_cursor = (
                self.daily_readings.find(day_filter, {"_id": 0, "readings": 0})
                .sort(sort_order)
                .skip((nbr_page - 1) * nbr_data)
                .limit(nbr_data)
            )
            page_records = await day_cursor.to_list()
        else:
            total_cursor = await self.daily_readings.aggregate([
                {"$match": day_filter},
                {"$group": {"_id": None, "total": {"$sum": "$summary.minutes_recorded"}}},
            ])
            total_result = await total_cursor.to_list()
            total_records = total_result[0]["total"] if total_result else 0

            # Readings are stored oldest first inside each day, so reverse them for newest first
            readings_in_order = {"$reverseArray": "$readings"} if newest_first else "$readings"
            minute_cursor = await self.daily_readings.aggregate([
                {"$match": day_filter},
                {"$sort": sort_order},
                {"$project": {"_id": 0, "household_id": 1, "readings": readings_in_order}},
                {"$unwind": "$readings"},
                {"$skip": (nbr_page - 1) * nbr_data},
                {"$limit": nbr_data},
                {"$project": {"household_id": 1,
                              **{field_name: f"$readings.{field_name}" for field_name in READING_FIELDS}}},
            ])
            page_records = await minute_cursor.to_list()

        return paginated_schema(
            page=nbr_page,
            size=nbr_data,
            total=total_records,
            records=[record_schema.model_validate(record) for record in page_records],
        )

    async def get_all_records(self,
                              nbr_page:int,
                              nbr_data:int,
                              type:Literal["minute", "day"] = "minute"
                              ):
        """
        return minute readings or days paginated, oldest first
        """
        return await self.paginate(type=type, nbr_page=nbr_page, nbr_data=nbr_data)

    async def get_latest_record(self,
                                limit:int,
                                nbr_page:int = 1,
                                type:Literal["minute", "day"] = "minute"
                                ):
        """
        Get latest minute readings or days with limit l, newest first and paginated
        """
        return await self.paginate(type=type, nbr_page=nbr_page, nbr_data=limit, newest_first=True)

    async def get_records_by_date_range(self,
                                        start_date:date,
                                        end_date:date,
                                        limit:int,
                                        nbr_page:int = 1,
                                        type:Literal["minute", "day"] = "minute"
                                        ):
        """
        Get minute readings or days from start_date to end_date (both days included), oldest first and paginated
        """
        if start_date > end_date:
            raise HTTPException(status_code=400, detail="start_date must be on or before end_date")

        start_day = datetime.combine(start_date, datetime.min.time())
        end_day = datetime.combine(end_date + timedelta(days=1), datetime.min.time())
        return await self.paginate(type=type, nbr_page=nbr_page, nbr_data=limit,
                                   start_day=start_day, end_day=end_day)

    async def check_household_exists(self, household_id:int):
        """
        Raise 404 if the household does not exist
        """
        household = await self.database["households"].find_one({"_id": household_id})
        if household is None:
            raise HTTPException(status_code=404, detail=f"Household {household_id} not found")

    def parse_record_id(self, record_id:str):
        """
        A minute reading is identified by its time, e.g. 2010-11-26T21:02:00
        """
        try:
            return datetime.fromisoformat(record_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="record_id must be the reading time, e.g. 2010-11-26T21:02:00")

    async def get_day_document(self, household_id:int, day:datetime):
        """
        Return the day document, or None if the day has no readings yet
        """
        return await self.daily_readings.find_one({"household_id": household_id, "date": day})

    async def save_day(self, household_id:int, day:datetime, readings:list, minutes_missing:int):
        """
        Store a day's readings (sorted by time) with a recomputed summary; delete the day if it has no readings left
        """
        day_key = {"household_id": household_id, "date": day}
        if not readings:
            await self.daily_readings.delete_one(day_key)
            return
        sorted_readings = sorted(readings, key=lambda reading: reading["time"])
        await self.daily_readings.update_one(
            day_key,
            {"$set": {"readings": sorted_readings, "summary": build_summary(sorted_readings, minutes_missing)}},
            upsert=True,
        )

    async def create_record(self, record_data:MongoReadingCreate):
        """
        Add a new minute reading to its day document (created if needed) and recompute the day's summary
        """
        await self.check_household_exists(record_data.household_id)

        new_reading = record_data.model_dump(include=set(READING_FIELDS))
        day = start_of_day(record_data.time)
        day_document = await self.get_day_document(record_data.household_id, day)
        day_readings = day_document["readings"] if day_document else []
        minutes_missing = day_document["summary"]["minutes_missing"] if day_document else 0

        if any(reading["time"] == record_data.time for reading in day_readings):
            raise HTTPException(status_code=409, detail="A reading already exists for this household at this time")

        await self.save_day(record_data.household_id, day, day_readings + [new_reading], minutes_missing)
        return MongoReadingResponse(household_id=record_data.household_id, **new_reading)

    async def update_record(self,
                            record_id:str,
                            record_data:MongoReadingUpdate,
                            household_id:int = 1
                            ):
        """
        Update only the fields sent; if the time changes, the reading moves to its new day
        """
        old_time = self.parse_record_id(record_id)
        old_day = start_of_day(old_time)
        old_day_document = await self.daily_readings.find_one(
            {"household_id": household_id, "date": old_day, "readings.time": old_time}
        )
        if old_day_document is None:
            raise HTTPException(status_code=404, detail=f"No minute reading found for {record_id}")

        old_reading = next(reading for reading in old_day_document["readings"] if reading["time"] == old_time)
        changed_fields = record_data.model_dump(exclude_unset=True, exclude_none=True)
        updated_reading = old_reading | changed_fields
        new_time = updated_reading["time"]
        new_day = start_of_day(new_time)

        old_day_readings = [reading for reading in old_day_document["readings"] if reading["time"] != old_time]
        old_minutes_missing = old_day_document["summary"]["minutes_missing"]

        if new_day == old_day:
            if any(reading["time"] == new_time for reading in old_day_readings):
                raise HTTPException(status_code=409, detail="A reading already exists for this household at this time")
            await self.save_day(household_id, old_day, old_day_readings + [updated_reading], old_minutes_missing)
        else:
            new_day_document = await self.get_day_document(household_id, new_day)
            new_day_readings = new_day_document["readings"] if new_day_document else []
            if any(reading["time"] == new_time for reading in new_day_readings):
                raise HTTPException(status_code=409, detail="A reading already exists for this household at this time")
            new_minutes_missing = new_day_document["summary"]["minutes_missing"] if new_day_document else 0
            await self.save_day(household_id, new_day, new_day_readings + [updated_reading], new_minutes_missing)
            await self.save_day(household_id, old_day, old_day_readings, old_minutes_missing)

        return MongoReadingResponse(household_id=household_id, **updated_reading)

    async def delete_record(self, record_id:str, household_id:int = 1):
        """
        Remove one minute reading and recompute its day's summary (the day is removed if it becomes empty)
        """
        reading_time = self.parse_record_id(record_id)
        day = start_of_day(reading_time)
        day_document = await self.daily_readings.find_one(
            {"household_id": household_id, "date": day, "readings.time": reading_time}
        )
        if day_document is None:
            raise HTTPException(status_code=404, detail=f"No minute reading found for {record_id}")

        remaining_readings = [reading for reading in day_document["readings"] if reading["time"] != reading_time]
        await self.save_day(household_id, day, remaining_readings, day_document["summary"]["minutes_missing"])
