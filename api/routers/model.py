#!/usr/bin/env python3

from fastapi.routing import APIRouter
from api.schema.prediction_schema import Prediction

router = APIRouter(
    prefix="/model",
    tags=["Model Prediction"]
    )

@router.post("/predict")
async def forecast(predicion:Prediction):
    """
    Forecast household electricity consumption
    """
    pass
