from fastapi import FastAPI
from app.routers import forecast_router, simulate_router, health_router, yearly_real_router

app = FastAPI(
    title="Solar Energy Forecasting API",
    version="0.1.0",
    description="Backend for the Solar Production Prediction Final Project",
    docs_url="/swagger",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Routers
app.include_router(health_router.router)
app.include_router(simulate_router.router, prefix="/simulate", tags=["Simulation"])
app.include_router(forecast_router.router, prefix="/forecast", tags=["Forecasting"])
app.include_router(yearly_real_router.router, prefix="/forecast/year", tags=["Year Forecast"])

@app.get("/")
def root():
    return {"message": "Solar Forecasting Backend is running 🚀"}
