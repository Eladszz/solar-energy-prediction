import requests
import pandas as pd
import logging
logger = logging.getLogger(__name__)
ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"

def get_year_archive(lat, lon, year):
    start = f"{year}-01-01"
    end   = f"{year}-12-31"
    logger.info(f"Fetching weather archive data for lat: {lat}, lon: {lon}, year: {year}")
    url = (
        f"{ARCHIVE_URL}?latitude={lat}&longitude={lon}"
        f"&start_date={start}&end_date={end}"
        "&hourly=shortwave_radiation,temperature_2m"
    )
    logger.info(f"Request URL: {url}")
    res = requests.get(url)
    res.raise_for_status()
    logger.info(f"Received weather archive data with status code {res.status_code}")
    data = res.json()
    hourly = data.get("hourly", {})
    logger.info(f"Number of hourly records fetched: {len(hourly.get('time', []))}")
    return pd.DataFrame({
        "time": pd.to_datetime(hourly.get("time", [])),
        "irr": hourly.get("shortwave_radiation", []),
        "temp": hourly.get("temperature_2m", [])
    })
