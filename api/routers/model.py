#!/usr/bin/env python3

from fastapi.routing import APIRouter

router = APIRouter(
    prefix="/model",
    tags=["Model Prediction"]
    )

@router.post("/predict")
async def forecast():
    """
    Forecast household electricity consumption
    """
    pass
