import pandas as pd
import logging
import requests

from app.services.external_service import (
    DEFAULT_EXTERNAL_TIMEOUT_SECONDS,
    ExternalServiceResponseError,
    fetch_json_from_provider,
    require_list_fields,
)

logger = logging.getLogger(__name__)
ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
WEATHER_ARCHIVE_PROVIDER = "Historical weather provider"
WEATHER_ARCHIVE_TIMEOUT_SECONDS = DEFAULT_EXTERNAL_TIMEOUT_SECONDS


def get_year_archive(lat, lon, year):
    start = f"{year}-01-01"
    end = f"{year}-12-31"
    logger.info(
        f"Fetching weather archive data for lat: {lat}, lon: {lon}, year: {year}"
    )
    url = (
        f"{ARCHIVE_URL}?latitude={lat}&longitude={lon}"
        f"&start_date={start}&end_date={end}"
        "&hourly=shortwave_radiation,temperature_2m"
    )
    logger.info(f"Request URL: {url}")
    data = fetch_json_from_provider(
        url=url,
        provider=WEATHER_ARCHIVE_PROVIDER,
        timeout=WEATHER_ARCHIVE_TIMEOUT_SECONDS,
        request_get=requests.get,
    )
    logger.info("Received weather archive data for year %s", year)
    hourly = data.get("hourly", {})
    if not isinstance(hourly, dict):
        raise ExternalServiceResponseError(
            provider=WEATHER_ARCHIVE_PROVIDER,
            user_message="Historical weather provider returned malformed hourly data. Please try again shortly.",
            detail="Missing 'hourly' object in archive response.",
        )

    hourly_values = require_list_fields(
        container=hourly,
        fields=("time", "shortwave_radiation", "temperature_2m"),
        provider=WEATHER_ARCHIVE_PROVIDER,
        context="archive hourly data",
    )
    logger.info(f"Number of hourly records fetched: {len(hourly_values['time'])}")
    return pd.DataFrame(
        {
            "time": pd.to_datetime(hourly_values["time"]),
            "irr": hourly_values["shortwave_radiation"],
            "temp": hourly_values["temperature_2m"],
        }
    )
