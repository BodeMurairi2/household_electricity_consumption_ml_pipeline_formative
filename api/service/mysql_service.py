#!/usr/bin/env python3

from datetime import date, datetime, timedelta
from typing import Literal

from fastapi import HTTPException
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from api.schema.power_reading import (
    PowerReadingCreate,
    PowerReadingUpdate,
    PowerReadingResponse,
    PaginatedPowerReadings,
)
from api.schema.hourly_power import (
    HourlyPowerCreate,
    HourlyPowerUpdate,
    HourlyPowerResponse,
    PaginatedHourlyPower,
)

from api.mysql_setup import models as database_model

class HouseholdSQLCRUD:
    def __init__(self, db_session:AsyncSession):
        self.session = db_session

    def resolve_info_type(self, type:Literal["minute", "hour"]):
        """
        Return the table, time column, record schema and paginated schema for minute or hourly data
        """
        if type == "hour":
            return (
                database_model.HourlyPower,
                database_model.HourlyPower.hour_start,
                HourlyPowerResponse,
                PaginatedHourlyPower,
            )
        return (
            database_model.PowerReading,
            database_model.PowerReading.measured_at,
            PowerReadingResponse,
            PaginatedPowerReadings,
        )

    async def paginate(self,
                       type:Literal["minute", "hour"],
                       nbr_page:int,
                       nbr_data:int,
                       newest_first:bool = False,
                       start_time:datetime | None = None,
                       end_time:datetime | None = None
                       ):
        """
        Count, sort and slice minute or hourly records, optionally between start_time (included)
        and end_time (excluded), and return one page
        """
        table_model, time_column, record_schema, paginated_schema = self.resolve_info_type(type)

        time_filters = []
        if start_time is not None:
            time_filters.append(time_column >= start_time)
        if end_time is not None:
            time_filters.append(time_column < end_time)

        total_records = await self.session.scalar(
            select(func.count()).select_from(table_model).where(*time_filters)
        )

        page_query = (
            select(table_model)
            .where(*time_filters)
            .order_by(time_column.desc() if newest_first else time_column)
            .offset((nbr_page - 1) * nbr_data)
            .limit(nbr_data)
        )
        page_result = await self.session.execute(page_query)
        page_records = page_result.scalars().all()

        return paginated_schema(
            page=nbr_page,
            size=nbr_data,
            total=total_records,
            records=[record_schema.model_validate(record) for record in page_records],
        )

    async def get_all_records(self,
                              nbr_page:int,
                              nbr_data:int,
                              type:Literal["minute", "hour"] = "minute"
                              ):
        """
        return minutes or hourly power paginated response
        """
        return await self.paginate(type=type, nbr_page=nbr_page, nbr_data=nbr_data)

    async def get_latest_record(self,
                                limit:int,
                                nbr_page:int = 1,
                                type:Literal["minute", "hour"] = "minute"
                                ):
        """
        Get latest minute or hourly records with limit l, newest first and paginated
        """
        return await self.paginate(type=type, nbr_page=nbr_page, nbr_data=limit, newest_first=True)

    async def get_records_by_date_range(self,
                                        start_date:date,
                                        end_date:date,
                                        limit:int,
                                        nbr_page:int = 1,
                                        type:Literal["minute", "hour"] = "minute"
                                        ):
        """
        Get minute or hourly records from start_date to end_date (both days included), oldest first and paginated
        """
        if start_date > end_date:
            raise HTTPException(status_code=400, detail="start_date must be on or before end_date")

        start_time = datetime.combine(start_date, datetime.min.time())
        end_time = datetime.combine(end_date + timedelta(days=1), datetime.min.time())
        return await self.paginate(type=type, nbr_page=nbr_page, nbr_data=limit,
                                   start_time=start_time, end_time=end_time)

    async def check_household_exists(self, household_id:int):
        """
        Raise 404 if the household does not exist
        """
        household = await self.session.get(database_model.Household, household_id)
        if household is None:
            raise HTTPException(status_code=404, detail=f"Household {household_id} not found")

    async def find_record(self,
                          record_id:str,
                          type:Literal["minute", "hour"],
                          household_id:int = 1
                          ):
        """
        Find one record: by reading ID for minute data, by hour start (e.g. 2010-11-26T21:00:00) for hourly data
        """
        if type == "hour":
            try:
                hour_start = datetime.fromisoformat(record_id)
            except ValueError:
                raise HTTPException(status_code=400, detail="For hourly records, record_id must be the hour start, e.g. 2010-11-26T21:00:00")
            record = await self.session.get(database_model.HourlyPower, (household_id, hour_start))
        else:
            if not record_id.isdigit():
                raise HTTPException(status_code=400, detail="For minute records, record_id must be the numeric reading ID")
            record = await self.session.get(database_model.PowerReading, int(record_id))

        if record is None:
            raise HTTPException(status_code=404, detail=f"No {type} record found for {record_id}")
        return record

    async def save_changes(self):
        """
        Commit, turning database conflicts (duplicate time, unknown reference) into a 409 error
        """
        try:
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()
            raise HTTPException(status_code=409, detail="A record already exists for this household at this time")

    async def create_record(self, record_data:PowerReadingCreate | HourlyPowerCreate):
        """
        Create a new minute reading (with its sub-meter readings) or a new hourly record
        """
        await self.check_household_exists(record_data.household_id)

        if isinstance(record_data, HourlyPowerCreate):
            new_record = database_model.HourlyPower(**record_data.model_dump())
            record_schema = HourlyPowerResponse
        else:
            # reading_id is not AUTO_INCREMENT in the schema, so the next ID is computed here
            highest_reading_id = await self.session.scalar(select(func.max(database_model.PowerReading.reading_id)))
            reading_values = record_data.model_dump(exclude={"sub_meter_readings"})
            new_record = database_model.PowerReading(
                reading_id=(highest_reading_id or 0) + 1,
                **reading_values,
                sub_meter_readings=[
                    database_model.SubMeterReading(sub_meter_id=sub_meter_reading.sub_meter_id,
                                                   energy_wh=sub_meter_reading.energy_wh)
                    for sub_meter_reading in record_data.sub_meter_readings
                ],
            )
            record_schema = PowerReadingResponse

        self.session.add(new_record)
        await self.save_changes()
        return record_schema.model_validate(new_record)

    async def update_record(self,
                            record_id:str,
                            record_data:PowerReadingUpdate | HourlyPowerUpdate,
                            type:Literal["minute", "hour"] = "minute",
                            household_id:int = 1
                            ):
        """
        Update only the fields sent; for minute data, sending sub_meter_readings replaces them
        """
        record = await self.find_record(record_id, type, household_id)
        changed_fields = record_data.model_dump(exclude_unset=True, exclude_none=True)

        new_sub_meter_readings = changed_fields.pop("sub_meter_readings", None)
        for field_name, new_value in changed_fields.items():
            setattr(record, field_name, new_value)

        if new_sub_meter_readings is not None:
            record.sub_meter_readings = [
                database_model.SubMeterReading(sub_meter_id=sub_meter_reading["sub_meter_id"],
                                               energy_wh=sub_meter_reading["energy_wh"])
                for sub_meter_reading in new_sub_meter_readings
            ]

        await self.save_changes()
        record_schema = HourlyPowerResponse if type == "hour" else PowerReadingResponse
        return record_schema.model_validate(record)

    async def delete_record(self,
                            record_id:str,
                            type:Literal["minute", "hour"] = "minute",
                            household_id:int = 1
                            ):
        """
        Delete one record; for minute data its sub-meter readings are deleted with it
        """
        record = await self.find_record(record_id, type, household_id)
        await self.session.delete(record)
        await self.save_changes()
