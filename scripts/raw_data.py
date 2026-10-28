from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW_FILE = ROOT / "data_analysis/data/household_power_consumption.txt"
HOURLY_FILE = ROOT / "data_analysis/data/processed/hourly_power.csv"

POWER_COLS = ["Global_active_power", "Global_reactive_power", "Voltage", "Global_intensity"]
SUB_COLS = ["Sub_metering_1", "Sub_metering_2", "Sub_metering_3"]

HOUSEHOLD = {"household_id": 1, "name": "UCI household", "city": "Sceaux", "country": "France"}
SUB_METERS = [
    {"sub_meter_id": 1, "name": "kitchen", "appliances": "dishwasher, oven, microwave"},
    {"sub_meter_id": 2, "name": "laundry", "appliances": "washing machine, tumble dryer, refrigerator, light"},
    {"sub_meter_id": 3, "name": "water_heater_ac", "appliances": "electric water heater, air conditioner"},
]


def read_raw():
    df = pd.read_csv(RAW_FILE, sep=";", na_values="?", low_memory=False)
    df["measured_at"] = pd.to_datetime(df["Date"] + " " + df["Time"], format="%d/%m/%Y %H:%M:%S")
    return df.drop(columns=["Date", "Time"]).sort_values("measured_at").reset_index(drop=True)


def read_hourly():
    return pd.read_csv(HOURLY_FILE, parse_dates=["datetime"])
