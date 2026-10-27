import uvicorn
from fastapi import FastAPI
from api.controllers import routing

app = FastAPI(
    description="Household Energy Consumption API application",
    version="0.0.1"
)

routing(app=app)

if __name__ == "__main__":
    uvicorn.run(
        "api.main:app",
        port=8000,
        reload=True
    )
