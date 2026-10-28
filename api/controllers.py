#!/usr/bin/env python3

from fastapi import FastAPI
from api.routers.sql_router import router as sql_router
from api.routers.mongo_router import router as mongo_router
from api.routers.model import router as model_router

def routing(app:FastAPI):
    """
    Main API Routers for all routers
    """
    app.include_router(sql_router)
    app.include_router(mongo_router)
    app.include_router(model_router)
