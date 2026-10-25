
import pandas as pd

TARGET = "Global_active_power"
MEAN_COLS = ["Global_active_power", "Global_reactive_power", "Voltage", "Global_intensity"]
SUM_COLS = ["Sub_metering_1", "Sub_metering_2", "Sub_metering_3"]
MAX_GAP_HOURS = 6


def to_hourly(minute_df):

    means = minute_df[MEAN_COLS].resample("h").mean()
    sums = minute_df[SUM_COLS].resample("h").sum(min_count=1)
    return pd.concat([means, sums], axis=1)


def fill_short_gaps(hourly, max_gap=MAX_GAP_HOURS):
    """Linearly interpolate gaps of at most max_gap hours; longer gaps stay NaN."""
    out = hourly.copy()
    interpolated = out.interpolate(method="time", limit_area="inside")
    for col in out.columns:
        is_na = out[col].isna()
        run_id = (is_na != is_na.shift()).cumsum()
        gap_len = is_na.groupby(run_id).transform("sum")
        short = is_na & (gap_len <= max_gap)
        out.loc[short, col] = interpolated.loc[short, col]
    return out


def build_features(hourly):

    out = hourly.copy()
    for lag in (1, 24, 168):
        out[f"lag_{lag}"] = out[TARGET].shift(lag)
    out["ma_24"] = out[TARGET].rolling(24).mean()
    out["ma_168"] = out[TARGET].rolling(168).mean()
    out["hour"] = out.index.hour
    out["dayofweek"] = out.index.dayofweek
    out["month"] = out.index.month
    return out


CALENDAR = ["hour", "dayofweek", "month"]
LAGS = [TARGET, "lag_1", "lag_24", "lag_168"]          # TARGET = the current hour's value
MOVING_AVG = ["ma_24", "ma_168"]
ELECTRICAL = ["Global_reactive_power", "Voltage", "Global_intensity",
              "Sub_metering_1", "Sub_metering_2", "Sub_metering_3"]

FEATURE_SETS = {
    "A: current + lags + calendar": LAGS + CALENDAR,
    "B: A + moving averages": LAGS + CALENDAR + MOVING_AVG,
    "C: B + electrical measurements": LAGS + CALENDAR + MOVING_AVG + ELECTRICAL,
}
