#!/usr/bin/env python3

from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator

from api.schema.sub_power_Reading import SubMeterReading, SubMeterReadingResponse


def check_unique_sub_meters(sub_meter_readings):
    """
    Each sub-meter can appear at most once per reading
    """
    if sub_meter_readings is not None:
        sub_meter_ids = [sub_meter_reading.sub_meter_id for sub_meter_reading in sub_meter_readings]
        if len(sub_meter_ids) != len(set(sub_meter_ids)):
            raise ValueError("Each sub_meter_id can only appear once")
    return sub_meter_readings


class PowerReading(BaseModel):
    """
    Schema for power reading
    """
    measured_at:datetime = Field(description="Date and time records was measured")
    global_active_power:Decimal = Field(description="Global Active Power in Kw", ge=0, max_digits=6, decimal_places=3)
    global_reactive_power:Decimal = Field(description="Global reactive power in Kw", ge=0, max_digits=6, decimal_places=3)
    voltage:Decimal = Field(description="Voltage power in V", ge=0, max_digits=6, decimal_places=3)
    global_intensity:Decimal = Field(description="Global intensity in A", ge=0, max_digits=6, decimal_places=3)


class PowerReadingCreate(PowerReading):
    """
    Schema for POST: register a new reading
    """
    model_config = ConfigDict(extra="forbid")

    household_id:int = Field(default=1, description="Household the reading belongs to (only household 1 exists)")
    sub_meter_readings:list[SubMeterReading] = Field(default=[], description="Up to 3 sub-meter readings", max_length=3)

    @field_validator("sub_meter_readings")
    @classmethod
    def validate_unique_sub_meters(cls, sub_meter_readings):
        return check_unique_sub_meters(sub_meter_readings)


class PowerReadingUpdate(BaseModel):
    """
    Schema for PUT: every field is optional, only the fields sent are updated
    """
    model_config = ConfigDict(extra="forbid")

    measured_at:datetime | None = Field(default=None, description="Date and time records was measured")
    global_active_power:Decimal | None = Field(default=None, description="Global Active Power in Kw", ge=0, max_digits=6, decimal_places=3)
    global_reactive_power:Decimal | None = Field(default=None, description="Global reactive power in Kw", ge=0, max_digits=6, decimal_places=3)
    voltage:Decimal | None = Field(default=None, description="Voltage power in V", ge=0, max_digits=6, decimal_places=3)
    global_intensity:Decimal | None = Field(default=None, description="Global intensity in A", ge=0, max_digits=6, decimal_places=3)
    sub_meter_readings:list[SubMeterReading] | None = Field(default=None, description="If sent, replaces the reading's sub-meter readings", max_length=3)

    @field_validator("sub_meter_readings")
    @classmethod
    def validate_unique_sub_meters(cls, sub_meter_readings):
        return check_unique_sub_meters(sub_meter_readings)


class PowerReadingResponse(BaseModel):
    """
    Schema for GET: a stored reading.
    Measurements can be null because the dataset has missing minutes.
    """
    model_config = ConfigDict(from_attributes=True)

    reading_id:int = Field(description="Reading ID")
    household_id:int = Field(description="Household the reading belongs to")
    measured_at:datetime = Field(description="Date and time records was measured")
    global_active_power:Decimal | None = Field(description="Global Active Power in Kw")
    global_reactive_power:Decimal | None = Field(description="Global reactive power in Kw")
    voltage:Decimal | None = Field(description="Voltage power in V")
    global_intensity:Decimal | None = Field(description="Global intensity in A")
    sub_meter_readings:list[SubMeterReadingResponse] = Field(description="Sub-meter readings for this minute")


class PaginatedPowerReadings(BaseModel):
    """
    Schema for paginated GET responses
    """
    page:int = Field(description="Current page number")
    size:int = Field(description="Number of records per page")
    total:int = Field(description="Total number of matching records")
    records:list[PowerReadingResponse] = Field(description="Records on this page")
