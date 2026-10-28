import os

from pymongo import ASCENDING, MongoClient

from scripts.raw_data import HOUSEHOLD, POWER_COLS, SUB_COLS, SUB_METERS, read_raw

DAILY_VALIDATOR = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["household_id", "date", "summary", "readings"],
        "properties": {
            "household_id": {"bsonType": "int"},
            "date": {"bsonType": "date"},
            "summary": {"bsonType": "object"},
            "readings": {"bsonType": "array"},
        },
    }
}


def day_document(day, group):
    valid = group.dropna(subset=POWER_COLS)
    readings = [
        {
            "time": r.measured_at.to_pydatetime(),
            "global_active_power": r.Global_active_power,
            "global_reactive_power": r.Global_reactive_power,
            "voltage": r.Voltage,
            "global_intensity": r.Global_intensity,
            "sub_metering_wh": [r.Sub_metering_1, r.Sub_metering_2, r.Sub_metering_3],
        }
        for r in valid.itertuples(index=False)
    ]
    peak = valid.loc[valid["Global_active_power"].idxmax()] if len(valid) else None
    summary = {
        "minutes_recorded": len(valid),
        "minutes_missing": len(group) - len(valid),
        "total_kwh": round(valid["Global_active_power"].sum() / 60, 3),
        "avg_voltage": round(valid["Voltage"].mean(), 2) if len(valid) else None,
        "peak_power_kw": float(peak["Global_active_power"]) if peak is not None else None,
        "peak_time": peak["measured_at"].to_pydatetime() if peak is not None else None,
        "sub_metering_kwh": {
            m["name"]: round(valid[col].sum() / 1000, 3) for m, col in zip(SUB_METERS, SUB_COLS)
        },
    }
    return {
        "household_id": HOUSEHOLD["household_id"],
        "date": day.to_pydatetime(),
        "summary": summary,
        "readings": readings,
    }


def main():
    client = MongoClient(os.getenv("MONGO_URI", "mongodb://127.0.0.1:27017"))
    db = client["household_power"]
    db.drop_collection("households")
    db.drop_collection("daily_readings")

    raw = read_raw()
    db["households"].insert_one({
        "_id": HOUSEHOLD["household_id"],
        "name": HOUSEHOLD["name"],
        "location": {"city": HOUSEHOLD["city"], "country": HOUSEHOLD["country"]},
        "data_start": raw["measured_at"].min().to_pydatetime(),
        "data_end": raw["measured_at"].max().to_pydatetime(),
        "sub_meters": SUB_METERS,
    })

    daily = db.create_collection("daily_readings", validator=DAILY_VALIDATOR)
    daily.create_index([("household_id", ASCENDING), ("date", ASCENDING)], unique=True)
    daily.create_index("summary.total_kwh")

    docs = [day_document(day, group) for day, group in raw.groupby(raw["measured_at"].dt.normalize())]
    daily.insert_many(docs)
    print(f"daily_readings: {len(docs)}")


if __name__ == "__main__":
    main()
