#!/usr/bin/env python3
"""
Task 4 - Prediction script.
 
End-to-end flow:
    1. Fetch recent hourly records from the FastAPI service (Task 3, SQL endpoints)
    2. Preprocess them with the same functions used in Task 1 (data_analysis/features.py)
    3. Load the trained model bundle (data_analysis/outputs/best_model.pkl)
    4. Predict the average active power (kW) of the NEXT hour
 
The model was trained to predict `y_next`, i.e. the hour after the last observed hour,
so the forecast is made for (last hour_start + 1 hour).
 
Usage (from the project root, with the API running on port 8000):
    python -m scripts.predict
    python -m scripts.predict --as-of 2010-11-20        # forecast using data up to a past day
    python -m scripts.predict --source csv              # offline demo, no API needed
    python -m scripts.predict --api-url http://localhost:8000 --json
"""
 
import argparse
import json
import sys
import warnings
import urllib.error
import urllib.parse
import urllib.request

from datetime import date, timedelta
from pathlib import Path
 
import joblib
import pandas as pd
from sklearn.exceptions import InconsistentVersionWarning
 
ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT / "data_analysis"))
import features  # noqa: E402  (Task 1 preprocessing, reused so training and serving match)
 
MODEL_PATH = ROOT / "data_analysis" / "outputs" / "best_model.pkl"
CSV_PATH = ROOT / "data_analysis" / "data" / "processed" / "hourly_power.csv"
 
# The hourly API returns snake_case fields; the Task 1 pipeline uses the original dataset names.
API_TO_MODEL = {
    "global_active_power": "Global_active_power",
    "global_reactive_power": "Global_reactive_power",
    "voltage": "Voltage",
    "global_intensity": "Global_intensity",
    "sub_metering_1": "Sub_metering_1",
    "sub_metering_2": "Sub_metering_2",
    "sub_metering_3": "Sub_metering_3",
}
 
# lag_168 needs 168 earlier hours, so at least 169 contiguous hours; the rest is a buffer
# so short gaps can be interpolated exactly like in training.
DEFAULT_HOURS = 336
MIN_HOURS = 169
PAGE_SIZE = 1000  # API maximum
 
 
# -- 1. fetch
def api_get(base_url, path, params):
    url = f"{base_url.rstrip('/')}{path}?{urllib.parse.urlencode(params)}"
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        raise SystemExit(f"API returned {error.code} for {url}: {error.read().decode()[:300]}")
    except urllib.error.URLError as error:
        raise SystemExit(f"Could not reach the API at {base_url} ({error.reason}). "
                         f"Start it with `uvicorn api.main:app` or use --source csv.")
 
 
def fetch_records(base_url, hours, as_of=None):
    """
    Return hourly records as a list of dicts.
    - default: the `hours` most recent hours (GET /sql_records/latest)
    - as_of:   everything up to and including that day (GET /sql_records/latest/date_range)
    """
    records, page = [], 1
    while True:
        if as_of is None:
            payload = api_get(base_url, "/sql_records/latest",
                              {"limit": min(hours - len(records), PAGE_SIZE), "nbr_page": page, "info_type": "hour"})
        else:
            start = as_of - timedelta(days=hours // 24 + 1)
            payload = api_get(base_url, "/sql_records/latest/date_range",
                              {"start_date": start.isoformat(), "end_date": as_of.isoformat(),
                               "limit": PAGE_SIZE, "page": page, "info_type": "hour"})
        records += payload["records"]
        if len(records) >= payload["total"] or (as_of is None and len(records) >= hours) or not payload["records"]:
            return records
        page += 1
 
 
def to_hourly_frame(records):
    """API records -> hourly DataFrame with the Task 1 column names, one row per hour."""
    if not records:
        raise SystemExit("The API returned no hourly records. Is the database loaded?")
    df = pd.DataFrame(records)
    df["datetime"] = pd.to_datetime(df["hour_start"])
    df = (df.drop_duplicates("datetime").set_index("datetime").sort_index()
            .rename(columns=API_TO_MODEL)[list(API_TO_MODEL.values())]
            .astype(float))                       # None -> NaN
    return df.asfreq("h")                         # missing hours become NaN rows, as in training
 
 
def read_csv_frame(hours, as_of=None):
    df = pd.read_csv(CSV_PATH, parse_dates=["datetime"], index_col="datetime").asfreq("h")
    if as_of is not None:
        df = df.loc[: pd.Timestamp(as_of) + pd.Timedelta(hours=23)]
    return df.iloc[-hours:]
 
 
# -- 2. preprocess
def preprocess(hourly):
    """Same steps as Task 1: fill short gaps (<= 6 h), then lags, moving averages, calendar features."""
    return features.build_features(features.fill_short_gaps(hourly))
 
 
# -- 3. model
def load_bundle(path=MODEL_PATH):
    """
    Load {"model", "feature_cols", "target", "horizon", "experiment"} saved in the Task 1 notebook.
    The pickle was written by a scikit-learn build that stored one internal class under the module
    name `_loss`; aliasing it to sklearn._loss._loss lets newer scikit-learn versions load it.
    """
    import sklearn._loss._loss as sk_loss
    sys.modules.setdefault("_loss", sk_loss)
    if not Path(path).exists():
        raise SystemExit(f"Model file not found: {path}")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", InconsistentVersionWarning)
    bundle = joblib.load(path)
    print("Note: the model was saved with scikit-learn 1.6.1; predictions were checked against "
          "the training pipeline.", file=sys.stderr)
    return bundle
 
 
# -- 4. predict
def predict_next_hour(hourly, bundle):
    featured = preprocess(hourly)
    cols = bundle["feature_cols"]                 # exact feature names and order used in training
    row = featured.iloc[[-1]][cols]
    missing = row.columns[row.isna().any()].tolist()
    if missing:
        raise SystemExit(f"Cannot predict for {row.index[0]}: missing values in {missing}. "
                         f"Fetch more history (--hours) or pick another --as-of date.")
    prediction = float(bundle["model"].predict(row)[0])
    return row.index[0], row.iloc[0], prediction
 
 
def main():
    parser = argparse.ArgumentParser(description="Forecast the next hour of household active power (kW).")
    parser.add_argument("--source", choices=["api", "csv"], default="api",
                        help="api = fetch from the FastAPI service (default); csv = offline demo")
    parser.add_argument("--api-url", default="http://127.0.0.1:8000")
    parser.add_argument("--hours", type=int, default=DEFAULT_HOURS,
                        help=f"hours of history to fetch (default {DEFAULT_HOURS}, minimum {MIN_HOURS})")
    parser.add_argument("--as-of", type=date.fromisoformat, default=None, metavar="YYYY-MM-DD",
                        help="use history up to the end of this day instead of the latest record")
    parser.add_argument("--json", action="store_true", help="print the result as JSON")
    args = parser.parse_args()
 
    if args.hours < MIN_HOURS:
        raise SystemExit(f"--hours must be at least {MIN_HOURS} (lag_168 needs a week of history)")
 
    # 1. fetch
    if args.source == "api":
        hourly = to_hourly_frame(fetch_records(args.api_url, args.hours, args.as_of))
    else:
        hourly = read_csv_frame(args.hours, args.as_of)
 
    # 2-4. preprocess, load model, predict
    bundle = load_bundle()
    last_hour, inputs, prediction = predict_next_hour(hourly, bundle)
    forecast_hour = last_hour + pd.Timedelta(hours=1)
 
    result = {
        "source": args.source,
        "model": bundle["experiment"],
        "last_observed_hour": str(last_hour),
        "last_observed_power_kw": round(float(inputs["Global_active_power"]), 4),
        "forecast_hour": str(forecast_hour),
        "predicted_active_power_kw": round(prediction, 4),
    }
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Model:               {result['model']}")
        print(f"Last observed hour:  {result['last_observed_hour']}  ({result['last_observed_power_kw']} kW)")
        print(f"Forecast for:        {result['forecast_hour']}")
        print(f"Predicted power:     {result['predicted_active_power_kw']} kW")
 
 
if __name__ == "__main__":
    main()

