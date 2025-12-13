from pydantic import BaseModel
from typing import List

class ForecastRequest(BaseModel):
    hourly_production: List[float]



