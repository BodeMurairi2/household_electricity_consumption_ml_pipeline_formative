#!/usr/bin/env python3

from datetime import date
from fastapi.routing import APIRouter


router = APIRouter(prefix="/sql_records", tags=["SQL Management"])

@router.get("/")
async def get_all_records(nbr_page:int,
                          nbr_data:int
                          ):
    """
    get all records paginated
    """
    pass

@router.get("/latest")
async def get_latest_records(limit:int):
    """
    Get K most recents records
    """
    pass

@router.get("/latest/date_range")
async def get_records_range(start_date:date,
                            end_date:date,
                            limit:int,
                            page:int):
    """
    Get records by date range with limit and paginated
    """
    pass

@router.post("/record/create")
async def create_new_record():
    """
    Create a new record inside SQL db
    """
    pass

@router.put("/record/update/{record_id}")
async def update_record(record_id:str):
    """
    update one past record using ID
    """
    pass

@router.delete("/record/delete/{record_id}")
async def delete_record(record_id:str):
    """
    delete one past record using ID
    """
    pass
