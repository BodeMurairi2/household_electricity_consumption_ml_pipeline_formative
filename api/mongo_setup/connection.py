from pymongo import AsyncMongoClient

# API running in Docker (docker compose up)
MONGO_URL = "mongodb://mongo:27017"
DATABASE_NAME = "household_power"

# One client (connection pool) for the whole app
mongo_client = AsyncMongoClient(MONGO_URL)

async def get_database():
    """
    FastAPI dependency
    """
    yield mongo_client[DATABASE_NAME]
