#!/usr/bin/env python3

from pydantic import BaseModel, Field

class Prediction(BaseModel):
    """
    Class for making a new prediction.
    Fields follow the model's feature order; bounds are the min/max seen in training,
    since the Random Forest cannot extrapolate beyond them.
    """
    Global_active_power:float = Field(description="House current hour's consumption (kW)", ge=0.124, le=6.561)
    lag_1:float = Field(description="House consumption 1 hour ago (kW)", ge=0.124, le=6.561)
    lag_24:float = Field(description="House consumption same hour yesterday (kW)", ge=0.124, le=6.561)
    lag_168:float = Field(description="House consumption same hour last week (kW)", ge=0.124, le=6.561)
    hour:int = Field(description="Hour of the day from 0 to 23, where 0 means midnight, 13 means 1pm and 23 means 11pm", ge=0, le=23)
    dayofweek:int = Field(description="Day of the week from 0 to 6, where 0 means Monday and 6 means Sunday", ge=0, le=6)
    month:int = Field(description="Month of the year, where 1 means January and 12 means December", ge=1, le=12)
    ma_24:float = Field(description="Average consumption of the last 24h including the current one (kW)", ge=0.173, le=3.502)
    ma_168:float = Field(description="Average consumption of the last 168h (1 week) including the current one (kW)", ge=0.179, le=2.100)
    Global_reactive_power:float = Field(description="House current hour's reactive power (kW)", ge=0.021, le=0.774)
    Voltage:float = Field(description="Current hour's average voltage (V)", ge=225.834, le=251.902)
    Global_intensity:float = Field(description="Current hour's average current intensity (A)", ge=0.503, le=28.383)
    Sub_metering_1:float = Field(description="Kitchen energy used in the current hour: dishwasher, oven, microwave (Wh)", ge=0, le=2902)
    Sub_metering_2:float = Field(description="Laundry room energy used in the current hour: washing machine, tumble dryer, fridge, light (Wh)", ge=0, le=2786)
    Sub_metering_3:float = Field(description="Water heater and air conditioner energy used in the current hour (Wh)", ge=0, le=1227)
