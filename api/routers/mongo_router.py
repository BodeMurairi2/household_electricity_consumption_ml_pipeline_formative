#!/usr/bin/env python3

from datetime import date
from typing import Literal

from fastapi.routing import APIRouter
from fastapi import Depends, Query

from pymongo.asynchronous.database import AsyncDatabase
from api.mongo_setup.connection import get_database
from api.service.mongo_service import HouseholdMongoCRUD
from api.schema.mongo_reading import MongoReadingCreate, MongoReadingUpdate

router = APIRouter(prefix="/mongo_db", tags=["MongoDB Management"])

@router.get("/")
async def get_all_records(nbr_page:int = Query(ge=1),
                          nbr_data:int = Query(ge=1, le=1000),
                          info_type:Literal["minute", "day"] = "minute",
                          database:AsyncDatabase = Depends(get_database)
                          ):
    """
    get all records paginated (minute readings, or days with their summary)
    """
    power_consumption = HouseholdMongoCRUD(database=database)
    return await power_consumption.get_all_records(nbr_data=nbr_data, nbr_page=nbr_page, type=info_type)

@router.get("/latest")
async def get_latest_records(limit:int = Query(ge=1, le=1000),
                             nbr_page:int = Query(default=1, ge=1),
                             info_type:Literal["minute", "day"] = "minute",
                             database:AsyncDatabase = Depends(get_database)
                             ):
    """
    Get K most recents power records in minute or day
    """
    power_consumption = HouseholdMongoCRUD(database=database)
    return await power_consumption.get_latest_record(limit=limit, nbr_page=nbr_page, type=info_type)

@router.get("/latest/date_range")
async def get_records_range(start_date:date,
                            end_date:date,
                            limit:int = Query(ge=1, le=1000),
                            page:int = Query(default=1, ge=1),
                            info_type:Literal["minute", "day"] = "minute",
                            database:AsyncDatabase = Depends(get_database)):
    """
    Get records by date range with limit and paginated (start_date and end_date are both included)
    """
    power_consumption = HouseholdMongoCRUD(database=database)
    return await power_consumption.get_records_by_date_range(start_date=start_date, end_date=end_date,
                                                             limit=limit, nbr_page=page, type=info_type)

@router.post("/record/create", status_code=201)
async def create_new_record(record_data:MongoReadingCreate,
                            database:AsyncDatabase = Depends(get_database)):
    """
    Create a new minute reading inside MongoDB
    """
    power_consumption = HouseholdMongoCRUD(database=database)
    return await power_consumption.create_record(record_data=record_data)

@router.put("/record/update/{record_id}")
async def update_record(record_id:str,
                        record_data:MongoReadingUpdate,
                        household_id:int = 1,
                        database:AsyncDatabase = Depends(get_database)):
    """
    update one past minute reading using its time, e.g. 2010-11-26T21:02:00
    """
    power_consumption = HouseholdMongoCRUD(database=database)
    return await power_consumption.update_record(record_id=record_id, record_data=record_data,
                                                 household_id=household_id)

@router.delete("/record/delete/{record_id}", status_code=204)
async def delete_record(record_id:str,
                        household_id:int = 1,
                        database:AsyncDatabase = Depends(get_database)):
    """
    delete one past minute reading using its time, e.g. 2010-11-26T21:02:00
    """
    power_consumption = HouseholdMongoCRUD(database=database)
    await power_consumption.delete_record(record_id=record_id, household_id=household_id)
