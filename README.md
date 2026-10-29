# Household Electricity Consumption ML Pipeline

An end-to-end machine learning pipeline built on minute-level household power data. It covers data analysis, database storage, model training and a FastAPI service that serves predictions.

> **Status:** this repository is at the initial structure stage. The sections below describe the intended layout, and each module will be filled in as the work progresses.

## Dataset

This project uses the [Individual Household Electric Power Consumption](https://archive.ics.uci.edu/dataset/235/individual+household+electric+power+consumption) dataset from the UCI Machine Learning Repository.

- About 2.07 million measurements, taken once a minute from December 2006 to November 2010 in one house in Sceaux, France
- The file is semicolon-separated, and missing values (about 1.25% of rows) are written as `?`

| Column | Description | Unit |
| --- | --- | --- |
| `Date` | Date (dd/mm/yyyy) | — |
| `Time` | Time (hh:mm:ss) | — |
| `Global_active_power` | Household global minute-averaged active power | kW |
| `Global_reactive_power` | Household global minute-averaged reactive power | kW |
| `Voltage` | Minute-averaged voltage | V |
| `Global_intensity` | Household global minute-averaged current intensity | A |
| `Sub_metering_1` | Kitchen (dishwasher, oven, microwave) | Wh |
| `Sub_metering_2` | Laundry room (washing machine, tumble dryer, fridge, light) | Wh |
| `Sub_metering_3` | Electric water heater and air conditioner | Wh |

### Getting the data

The raw file is about 127 MB, which is over GitHub's 100 MB file limit, so it is **not committed** to this repository. Download it and place it here:

```
data_analysis/data/household_power_consumption.txt
```

```bash
mkdir -p data_analysis/data
curl -L -o /tmp/household_power_consumption.zip \
  "https://archive.ics.uci.edu/static/public/235/individual+household+electric+power+consumption.zip"
unzip /tmp/household_power_consumption.zip -d data_analysis/data/
```

## Project structure

```
.
├── api/                  # FastAPI application
│   ├── main.py           # App entry point
│   ├── router/           # Route definitions
│   ├── schema/           # Pydantic request/response models
│   ├── service/          # Business logic (prediction, data access)
│   └── model/            # Trained model loading
├── data_analysis/        # Exploratory data analysis and notebooks
│   └── data/             # Raw dataset (git-ignored)
├── db/                   # MySQL + MongoDB (Docker), schema, ERD, queries — see db/README.md
├── scripts/              # Helper scripts (data loading, training, etc.)
├── requirements.txt
└── README.md
```

## Setup

Requires Python 3.10 or later.

```bash
git clone https://github.com/BodeMurairi2/household_electricity_consumption_ml_pipeline_formative.git
cd household_electricity_consumption_ml_pipeline_formative

python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Then follow [Getting the data](#getting-the-data) to download the dataset.

## Running the API

Once the API is implemented, start it from the project root:

```bash
pip install "uvicorn[standard]"
uvicorn api.main:app --reload
```

The interactive docs will be at http://127.0.0.1:8000/docs.

## Roadmap

- [ ] Exploratory data analysis (`data_analysis/`)
- [x] Data cleaning and loading into a database (`db/`, `scripts/`) — see [db/README.md](db/README.md)
- [ ] Feature engineering and model training
- [ ] Prediction endpoints in the FastAPI service (`api/`)

## Prediction script (Task 4)

`scripts/predict.py` ties the pipeline together. It:

1. fetches the most recent hourly records from the API (`GET /sql_records/latest?info_type=hour`),
2. preprocesses them with the same functions as Task 1 (`data_analysis/features.py`): short-gap interpolation, lag features (1, 24, 168 h), moving averages (24, 168 h) and calendar features,
3. loads the trained model from `data_analysis/outputs/best_model.pkl` (HistGradientBoosting),
4. predicts the average active power (kW) of the next hour.

### Usage

Run from the project root, with the API running on port 8000:

```bash
python -m scripts.predict                                   # latest data from the API
python -m scripts.predict --api-url http://localhost:8000   # custom API address
python -m scripts.predict --as-of 2010-06-15                # use history up to a past day (date-range endpoint)
python -m scripts.predict --source csv                      # offline demo, no API needed
python -m scripts.predict --json                            # machine-readable output
```

Example output:

```
Model:               Exp 4 - HistGradientBoosting
Last observed hour:  2010-11-26 21:00:00  (0.9347 kW)
Forecast for:        2010-11-26 22:00:00
Predicted power:     1.0797 kW
```

At least 169 hours of history are needed because the model uses a 168-hour lag and moving average. The script fetches 336 hours by default.