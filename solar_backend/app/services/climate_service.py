import requests
import logging

logger = logging.getLogger(__name__)


def get_climate_daily(lat: float, lon: float):
    """
    Fetch 30-year climate irradiance normals (daily averages).
    """
    url = (
        "https://climate-api.open-meteo.com/v1/climate"
        f"?latitude={lat}&longitude={lon}"
        "&start_year=1991&end_year=2020"
        "&daily=shortwave_radiation_sum,temperature_2m_mean"
        "&models=best_match"
    )
    logger.info(f"Fetching climate data from {url}")
    res = requests.get(url)
    res.raise_for_status()
    logger.info(f"Received climate data with status code {res.status_code}")
    return res.json()
