from fastapi import FastAPI
from app.routers import health_router, simulate_router, yearly_forecast_router

app = FastAPI(
    title="Solar Energy Forecasting API",
    version="0.2.0",
    description="Backend for the Solar Production Prediction Final Project",
    docs_url="/swagger",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Routers
app.include_router(health_router.router)
app.include_router(simulate_router.router, prefix="/simulate", tags=["Day Simulation"])
app.include_router(yearly_forecast_router.router, prefix="/forecast/yearly", tags=["Yearly Forecast"])

@app.get("/")
def root():
    return {"message": "Solar Forecasting Backend is running 🚀"}
