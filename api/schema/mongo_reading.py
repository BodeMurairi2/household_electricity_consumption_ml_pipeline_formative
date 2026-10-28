#!/usr/bin/env python3

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator


def check_start_of_minute(reading_time):
    """
    A minute reading must be exactly on the minute (seconds at 0)
    """
    if reading_time is not None and (reading_time.second, reading_time.microsecond) != (0, 0):
        raise ValueError("time must be on the minute, e.g. 2010-11-26T21:02:00")
    return reading_time


class MongoReadingCreate(BaseModel):
    """
    Schema for POST: register a new minute reading inside its day document
    """
    model_config = ConfigDict(extra="forbid")

    household_id:int = Field(default=1, description="Household the reading belongs to (only household 1 exists)")
    time:datetime = Field(description="Date and time the reading was measured, on the minute")
    global_active_power:float = Field(description="Global Active Power in kW", ge=0)
    global_reactive_power:float = Field(description="Global reactive power in kW", ge=0)
    voltage:float = Field(description="Voltage in V", ge=0)
    global_intensity:float = Field(description="Global intensity in A", ge=0)
    sub_metering_wh:list[float] = Field(description="Energy in Wh for [kitchen, laundry, water heater and AC]",
                                        min_length=3, max_length=3)

    @field_validator("time")
    @classmethod
    def validate_start_of_minute(cls, reading_time):
        return check_start_of_minute(reading_time)

    @field_validator("sub_metering_wh")
    @classmethod
    def validate_sub_metering_not_negative(cls, sub_metering_wh):
        if any(energy_wh < 0 for energy_wh in sub_metering_wh):
            raise ValueError("sub_metering_wh values must be 0 or more")
        return sub_metering_wh


class MongoReadingUpdate(BaseModel):
    """
    Schema for PUT: every field is optional, only the fields sent are updated
    """
    model_config = ConfigDict(extra="forbid")

    time:datetime | None = Field(default=None, description="New date and time of the reading, on the minute")
    global_active_power:float | None = Field(default=None, description="Global Active Power in kW", ge=0)
    global_reactive_power:float | None = Field(default=None, description="Global reactive power in kW", ge=0)
    voltage:float | None = Field(default=None, description="Voltage in V", ge=0)
    global_intensity:float | None = Field(default=None, description="Global intensity in A", ge=0)
    sub_metering_wh:list[float] | None = Field(default=None, description="Energy in Wh for [kitchen, laundry, water heater and AC]",
                                               min_length=3, max_length=3)

    @field_validator("time")
    @classmethod
    def validate_start_of_minute(cls, reading_time):
        return check_start_of_minute(reading_time)

    @field_validator("sub_metering_wh")
    @classmethod
    def validate_sub_metering_not_negative(cls, sub_metering_wh):
        if sub_metering_wh is not None and any(energy_wh < 0 for energy_wh in sub_metering_wh):
            raise ValueError("sub_metering_wh values must be 0 or more")
        return sub_metering_wh


class MongoReadingResponse(BaseModel):
    """
    Schema for GET: one minute reading
    """
    household_id:int = Field(description="Household the reading belongs to")
    time:datetime = Field(description="Date and time the reading was measured")
    global_active_power:float = Field(description="Global Active Power in kW")
    global_reactive_power:float = Field(description="Global reactive power in kW")
    voltage:float = Field(description="Voltage in V")
    global_intensity:float = Field(description="Global intensity in A")
    sub_metering_wh:list[float] = Field(description="Energy in Wh for [kitchen, laundry, water heater and AC]")


class PaginatedMongoReadings(BaseModel):
    """
    Schema for paginated GET responses of minute readings
    """
    page:int = Field(description="Current page number")
    size:int = Field(description="Number of records per page")
    total:int = Field(description="Total number of matching records")
    records:list[MongoReadingResponse] = Field(description="Records on this page")


class DailySummary(BaseModel):
    """
    Precomputed totals for one day
    """
    minutes_recorded:int = Field(description="Number of minute readings stored for the day")
    minutes_missing:int = Field(description="Minutes with missing values in the source data")
    total_kwh:float = Field(description="Energy used over the day in kWh")
    avg_voltage:float | None = Field(description="Average voltage over the day in V")
    peak_power_kw:float | None = Field(description="Highest active power of the day in kW")
    peak_time:datetime | None = Field(description="Time of the highest active power")
    sub_metering_kwh:dict[str, float] = Field(description="Energy per sub-meter over the day in kWh")


class DailyReadingResponse(BaseModel):
    """
    Schema for GET: one day (summary only, without the minute readings)
    """
    household_id:int = Field(description="Household the day belongs to")
    date:datetime = Field(description="Day, at midnight")
    summary:DailySummary = Field(description="Totals for the day")


class PaginatedDailyReadings(BaseModel):
    """
    Schema for paginated GET responses of days
    """
    page:int = Field(description="Current page number")
    size:int = Field(description="Number of records per page")
    total:int = Field(description="Total number of matching records")
    records:list[DailyReadingResponse] = Field(description="Records on this page")
