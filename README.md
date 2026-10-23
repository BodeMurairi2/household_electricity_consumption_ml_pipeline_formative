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
├── db/                   # Database setup and access
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
- [ ] Data cleaning and loading into a database (`db/`, `scripts/`)
- [ ] Feature engineering and model training
- [ ] Prediction endpoints in the FastAPI service (`api/`)
