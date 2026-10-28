#!/usr/bin/env python3

from datetime import date
from typing import Literal

from fastapi.routing import APIRouter
from fastapi import Depends, HTTPException, Query
from pydantic import ValidationError

from sqlalchemy.ext.asyncio import AsyncSession
from api.mysql_setup.connection import get_session
from api.service.mysql_service import HouseholdSQLCRUD
from api.schema.power_reading import PowerReadingCreate, PowerReadingUpdate
from api.schema.hourly_power import HourlyPowerCreate, HourlyPowerUpdate

router = APIRouter(prefix="/sql_records", tags=["SQL Management"])


def match_body_to_info_type(record_data, info_type, minute_schema, hour_schema):
    """
    Make sure the request body is validated with the schema of the chosen info_type
    """
    expected_schema = hour_schema if info_type == "hour" else minute_schema
    if isinstance(record_data, expected_schema):
        return record_data
    try:
        return expected_schema.model_validate(record_data.model_dump(exclude_unset=True))
    except ValidationError as validation_error:
        raise HTTPException(status_code=422,
                            detail=validation_error.errors(include_url=False, include_context=False, include_input=False))


@router.get("/")
async def get_all_records(nbr_page:int = Query(ge=1),
                          nbr_data:int = Query(ge=1, le=1000),
                          info_type:Literal["minute", "hour"] = "minute",
                          session:AsyncSession = Depends(get_session)
                          ):
    """
    get all records paginated
    """
    power_consumption = HouseholdSQLCRUD(db_session=session)
    return await power_consumption.get_all_records(nbr_data=nbr_data, nbr_page=nbr_page, type=info_type)

@router.get("/latest")
async def get_latest_records(limit:int = Query(ge=1, le=1000),
                             nbr_page:int = Query(default=1, ge=1),
                             info_type:Literal["minute", "hour"] = "minute",
                             session:AsyncSession = Depends(get_session)
                             ):
    """
    Get K most recents power records in hour or minute
    """
    power_consumption = HouseholdSQLCRUD(db_session=session)
    return await power_consumption.get_latest_record(limit=limit, nbr_page=nbr_page, type=info_type)

@router.get("/latest/date_range")
async def get_records_range(start_date:date,
                            end_date:date,
                            limit:int = Query(ge=1, le=1000),
                            page:int = Query(default=1, ge=1),
                            info_type:Literal["minute", "hour"] = "minute",
                            session:AsyncSession = Depends(get_session)):
    """
    Get records by date range with limit and paginated (start_date and end_date are both included)
    """
    power_consumption = HouseholdSQLCRUD(db_session=session)
    return await power_consumption.get_records_by_date_range(start_date=start_date, end_date=end_date,
                                                             limit=limit, nbr_page=page, type=info_type)

@router.post("/record/create", status_code=201)
async def create_new_record(record_data:PowerReadingCreate | HourlyPowerCreate,
                            info_type:Literal["minute", "hour"] = "minute",
                            session:AsyncSession = Depends(get_session)):
    """
    Create a new record inside SQL db
    """
    record_data = match_body_to_info_type(record_data, info_type, PowerReadingCreate, HourlyPowerCreate)
    power_consumption = HouseholdSQLCRUD(db_session=session)
    return await power_consumption.create_record(record_data=record_data)

@router.put("/record/update/{record_id}")
async def update_record(record_id:str,
                        record_data:PowerReadingUpdate | HourlyPowerUpdate,
                        info_type:Literal["minute", "hour"] = "minute",
                        household_id:int = 1,
                        session:AsyncSession = Depends(get_session)):
    """
    update one past record using ID (reading ID for minute data, hour start such as 2010-11-26T21:00:00 for hourly data)
    """
    record_data = match_body_to_info_type(record_data, info_type, PowerReadingUpdate, HourlyPowerUpdate)
    power_consumption = HouseholdSQLCRUD(db_session=session)
    return await power_consumption.update_record(record_id=record_id, record_data=record_data,
                                                 type=info_type, household_id=household_id)

@router.delete("/record/delete/{record_id}", status_code=204)
async def delete_record(record_id:str,
                        info_type:Literal["minute", "hour"] = "minute",
                        household_id:int = 1,
                        session:AsyncSession = Depends(get_session)):
    """
    delete one past record using ID (reading ID for minute data, hour start such as 2010-11-26T21:00:00 for hourly data)
    """
    power_consumption = HouseholdSQLCRUD(db_session=session)
    await power_consumption.delete_record(record_id=record_id, type=info_type, household_id=household_id)
