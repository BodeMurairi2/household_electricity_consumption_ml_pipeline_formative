# Household Electricity Consumption ML Pipeline

An end-to-end machine learning pipeline built on minute-level household power data. It covers data analysis, database storage, model training, a FastAPI service for managing and querying the data, and a script that forecasts the next hour's consumption.

> **Status:** the data analysis, model training, MySQL and MongoDB databases, CRUD and time-series endpoints, and the prediction script are complete.

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

The raw file is about 127 MB, which is over GitHub's 100 MB file limit, so it is **not committed** to this repository.

1. Download `household_power_consumption.txt` from the [project's Google Drive folder](https://drive.google.com/drive/folders/1QTI3-LTFrOd1RGcSzoouFyfdohbNIfoY?usp=drive_link).
2. Put it at this exact path, keeping the same filename:

```
data_analysis/data/household_power_consumption.txt
```

Alternatively, download the same file from UCI:

```bash
mkdir -p data_analysis/data
curl -L -o /tmp/household_power_consumption.zip \
  "https://archive.ics.uci.edu/static/public/235/individual+household+electric+power+consumption.zip"
unzip /tmp/household_power_consumption.zip -d data_analysis/data/
```

## Project structure

```
.
├── api/                     # FastAPI application
│   ├── main.py              # App entry point
│   ├── controllers.py       # Registers the routers
│   ├── routers/             # Route definitions (MySQL, MongoDB)
│   ├── schema/              # Pydantic request/response models
│   ├── service/             # Database logic for MySQL and MongoDB
│   ├── mysql_setup/         # MySQL connection and ORM models
│   └── mongo_setup/         # MongoDB connection
├── data_analysis/           # Exploratory data analysis and model training
│   ├── task1_time_series_analysis.ipynb
│   ├── features.py          # Shared preprocessing and feature engineering
│   ├── data/                # Sample and processed data; raw dataset goes here (git-ignored)
│   └── outputs/             # Experiment results and trained model
├── db/                      # MySQL schema, MongoDB queries, ERD — see db/README.md
├── scripts/                 # Data loaders and prediction script
├── docker-compose.yml       # MySQL, MongoDB, data loader and API services
├── Dockerfile               # Image for the API and data loader
├── .dockerignore
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

## Running with Docker

This starts MySQL, MongoDB and the API, and loads the dataset into both databases. You need Docker with Docker Compose. Ports `8000`, `3307` and `27017` must be free.

1. Put the dataset in place by following [Getting the data](#getting-the-data). Do this first, because the file is copied into the image during the build and the data loader needs it.

2. From the project root, build and start everything:

   ```bash
   docker compose up -d --build
   ```

   The API starts only after the data has loaded, which takes several minutes. To follow the progress:

   ```bash
   docker logs -f power_loader
   ```

3. Open the interactive API docs at http://localhost:8000/docs.

To stop the containers:

```bash
docker compose down      # keeps the data
docker compose down -v   # also deletes the data
```

Every `docker compose up` runs the loader again, which wipes and reloads both databases. This also removes any records added through the API.

## Running the API

The API runs in Docker: follow [Running with Docker](#running-with-docker). Its database connections use the Docker service names `mysql` and `mongo`, so running `uvicorn` directly on your machine cannot reach the databases.

The interactive docs are at http://localhost:8000/docs.

The `api/` folder is mounted into the container, so saved changes in it reload automatically. After changing anything else, such as `requirements.txt` or `scripts/`, rebuild the image:

```bash
docker compose up -d --build --no-deps api
```

## API endpoints

| Method | Route | Purpose | Database |
| --- | --- | --- | --- |
| GET | `/sql_records/` | List minute or hourly records, oldest first, paginated | MySQL |
| GET | `/sql_records/latest` | List the most recent minute or hourly records, newest first, paginated | MySQL |
| GET | `/sql_records/latest/date_range` | List minute or hourly records between two dates (both included), paginated | MySQL |
| POST | `/sql_records/record/create` | Create a minute reading or an hourly record | MySQL |
| PUT | `/sql_records/record/update/{record_id}` | Update the fields sent for one minute reading or hourly record | MySQL |
| DELETE | `/sql_records/record/delete/{record_id}` | Delete one minute reading or hourly record | MySQL |
| GET | `/mongo_db/` | List minute readings or daily summaries, oldest first, paginated | MongoDB |
| GET | `/mongo_db/latest` | List the most recent minute readings or daily summaries, newest first, paginated | MongoDB |
| GET | `/mongo_db/latest/date_range` | List minute readings or daily summaries between two dates (both included), paginated | MongoDB |
| POST | `/mongo_db/record/create` | Add a minute reading to its day document | MongoDB |
| PUT | `/mongo_db/record/update/{record_id}` | Update the fields sent for one minute reading | MongoDB |
| DELETE | `/mongo_db/record/delete/{record_id}` | Delete one minute reading | MongoDB |

- **Choosing the data level:** the MySQL routes take `info_type=minute` (default) or `info_type=hour`. The MongoDB `GET` routes take `info_type=minute` (default) or `info_type=day`.
- **`record_id` in MySQL:** use the reading ID for minute data, or the hour start for hourly data, such as `2010-11-26T21:00:00`.
- **`record_id` in MongoDB:** use the reading time, such as `2010-11-26T21:02:00`.

## Roadmap

- [x] Exploratory data analysis (`data_analysis/`)
- [x] Data cleaning and loading into a database (`db/`, `scripts/`) — see [db/README.md](db/README.md)
- [x] Feature engineering and model training (`data_analysis/`)
- [x] CRUD and time-series endpoints for MySQL and MongoDB (`api/`)
- [x] Prediction script that uses the API (`scripts/predict.py`)

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