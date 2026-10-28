import os

import pandas as pd
import pymysql

from scripts.raw_data import HOUSEHOLD, POWER_COLS, SUB_COLS, SUB_METERS, read_hourly, read_raw

CHUNK = 20_000


def connect():
    return pymysql.connect(
        host=os.getenv("MYSQL_HOST", "127.0.0.1"),
        port=int(os.getenv("MYSQL_PORT", 3307)),
        user=os.getenv("MYSQL_USER", "power"),
        password=os.getenv("MYSQL_PASSWORD", "powerpass"),
        database="household_power",
    )


def rows(df):
    return list(df.astype(object).where(df.notna(), None).itertuples(index=False, name=None))


def insert_chunks(cur, sql, df):
    for start in range(0, len(df), CHUNK):
        cur.executemany(sql, rows(df.iloc[start:start + CHUNK]))


def main():
    raw = read_raw()
    raw["reading_id"] = raw.index + 1
    raw["household_id"] = HOUSEHOLD["household_id"]
    hid = HOUSEHOLD["household_id"]

    conn = connect()
    with conn.cursor() as cur:
        for table in ["sub_meter_readings", "power_readings", "hourly_power", "sub_meters", "households"]:
            cur.execute(f"DELETE FROM {table}")

        cur.execute(
            "INSERT INTO households VALUES (%s, %s, %s, %s, %s, %s)",
            (hid, HOUSEHOLD["name"], HOUSEHOLD["city"], HOUSEHOLD["country"],
             raw["measured_at"].min().to_pydatetime(), raw["measured_at"].max().to_pydatetime()),
        )
        cur.executemany(
            "INSERT INTO sub_meters VALUES (%s, %s, %s, %s)",
            [(m["sub_meter_id"], hid, m["name"], m["appliances"]) for m in SUB_METERS],
        )

        insert_chunks(
            cur,
            "INSERT INTO power_readings VALUES (%s, %s, %s, %s, %s, %s, %s)",
            raw[["reading_id", "household_id", "measured_at"] + POWER_COLS],
        )
        print(f"power_readings: {len(raw)}")

        sub = raw.melt(id_vars="reading_id", value_vars=SUB_COLS, var_name="sub_meter_id", value_name="energy_wh")
        sub["sub_meter_id"] = sub["sub_meter_id"].str[-1].astype(int)
        sub = sub.dropna(subset=["energy_wh"]).sort_values(["reading_id", "sub_meter_id"])
        insert_chunks(cur, "INSERT INTO sub_meter_readings VALUES (%s, %s, %s)", sub)
        print(f"sub_meter_readings: {len(sub)}")

        hourly = read_hourly()
        hourly.insert(0, "household_id", hid)
        insert_chunks(cur, "INSERT INTO hourly_power VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)", hourly)
        print(f"hourly_power: {len(hourly)}")

    conn.commit()
    conn.close()


if __name__ == "__main__":
    main()
