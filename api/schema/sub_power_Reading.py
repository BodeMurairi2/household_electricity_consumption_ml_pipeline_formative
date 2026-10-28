#!/usr/bin/env python3

from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field

class SubMeterReading(BaseModel):
    """
    Schema for one sub-meter reading (one minute)
    """
    sub_meter_id:int = Field(description="Sub-meter: 1 = kitchen, 2 = laundry, 3 = water heater and AC", ge=1, le=3)
    energy_wh:Decimal = Field(description="Energy used by the sub-meter in Wh", ge=0, max_digits=6, decimal_places=1)


class SubMeterReadingResponse(SubMeterReading):
    """
    Schema returned for a stored sub-meter reading
    """
    model_config = ConfigDict(from_attributes=True)

    reading_id:int = Field(description="ID of the power reading this sub-meter reading belongs to")
