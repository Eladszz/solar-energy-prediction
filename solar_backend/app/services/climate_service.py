import logging
import requests

from app.services.external_service import (
    DEFAULT_EXTERNAL_TIMEOUT_SECONDS,
    ExternalServiceResponseError,
    fetch_json_from_provider,
    require_list_fields,
)

logger = logging.getLogger(__name__)
CLIMATE_PROVIDER = "Climate data provider"
CLIMATE_PROVIDER_TIMEOUT_SECONDS = DEFAULT_EXTERNAL_TIMEOUT_SECONDS


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
    data = fetch_json_from_provider(
        url=url,
        provider=CLIMATE_PROVIDER,
        timeout=CLIMATE_PROVIDER_TIMEOUT_SECONDS,
        request_get=requests.get,
    )
    logger.info("Received climate data for (%s, %s)", lat, lon)
    daily = data.get("daily")
    if not isinstance(daily, dict):
        raise ExternalServiceResponseError(
            provider=CLIMATE_PROVIDER,
            user_message="Climate data provider returned malformed daily data. Please try again shortly.",
            detail="Missing 'daily' object in climate response.",
        )

    require_list_fields(
        container=daily,
        fields=("time", "shortwave_radiation_sum", "temperature_2m_mean"),
        provider=CLIMATE_PROVIDER,
        context="climate daily data",
    )
    return data
