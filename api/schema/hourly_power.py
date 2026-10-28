#!/usr/bin/env python3

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator


def check_start_of_hour(hour_start):
    """
    An hourly record must start exactly on the hour (minutes and seconds at 0)
    """
    if hour_start is not None and (hour_start.minute, hour_start.second, hour_start.microsecond) != (0, 0, 0):
        raise ValueError("hour_start must be on the hour, e.g. 2010-11-26T21:00:00")
    return hour_start


class HourlyPowerCreate(BaseModel):
    """
    Schema for POST: register a new hourly record
    """
    model_config = ConfigDict(extra="forbid")

    household_id:int = Field(default=1, description="Household the hour belongs to (only household 1 exists)")
    hour_start:datetime = Field(description="Start of the hour")
    global_active_power:float = Field(description="Average active power over the hour in kW", ge=0)
    global_reactive_power:float = Field(description="Average reactive power over the hour in kW", ge=0)
    voltage:float = Field(description="Average voltage over the hour in V", ge=0)
    global_intensity:float = Field(description="Average current intensity over the hour in A", ge=0)
    sub_metering_1:float = Field(description="Kitchen energy used in the hour in Wh", ge=0)
    sub_metering_2:float = Field(description="Laundry room energy used in the hour in Wh", ge=0)
    sub_metering_3:float = Field(description="Water heater and AC energy used in the hour in Wh", ge=0)

    @field_validator("hour_start")
    @classmethod
    def validate_start_of_hour(cls, hour_start):
        return check_start_of_hour(hour_start)


class HourlyPowerUpdate(BaseModel):
    """
    Schema for PUT: every field is optional, only the fields sent are updated
    """
    model_config = ConfigDict(extra="forbid")

    hour_start:datetime | None = Field(default=None, description="Start of the hour")
    global_active_power:float | None = Field(default=None, description="Average active power over the hour in kW", ge=0)
    global_reactive_power:float | None = Field(default=None, description="Average reactive power over the hour in kW", ge=0)
    voltage:float | None = Field(default=None, description="Average voltage over the hour in V", ge=0)
    global_intensity:float | None = Field(default=None, description="Average current intensity over the hour in A", ge=0)
    sub_metering_1:float | None = Field(default=None, description="Kitchen energy used in the hour in Wh", ge=0)
    sub_metering_2:float | None = Field(default=None, description="Laundry room energy used in the hour in Wh", ge=0)
    sub_metering_3:float | None = Field(default=None, description="Water heater and AC energy used in the hour in Wh", ge=0)

    @field_validator("hour_start")
    @classmethod
    def validate_start_of_hour(cls, hour_start):
        return check_start_of_hour(hour_start)


class HourlyPowerResponse(BaseModel):
    """
    Schema for GET: one hour of aggregated readings (hourly_power table)
    """
    model_config = ConfigDict(from_attributes=True)

    household_id:int = Field(description="Household the hour belongs to")
    hour_start:datetime = Field(description="Start of the hour")
    global_active_power:float | None = Field(description="Average active power over the hour in kW")
    global_reactive_power:float | None = Field(description="Average reactive power over the hour in kW")
    voltage:float | None = Field(description="Average voltage over the hour in V")
    global_intensity:float | None = Field(description="Average current intensity over the hour in A")
    sub_metering_1:float | None = Field(description="Kitchen energy used in the hour in Wh")
    sub_metering_2:float | None = Field(description="Laundry room energy used in the hour in Wh")
    sub_metering_3:float | None = Field(description="Water heater and AC energy used in the hour in Wh")


class PaginatedHourlyPower(BaseModel):
    """
    Schema for paginated GET responses of hourly records
    """
    page:int = Field(description="Current page number")
    size:int = Field(description="Number of records per page")
    total:int = Field(description="Total number of matching records")
    records:list[HourlyPowerResponse] = Field(description="Records on this page")
