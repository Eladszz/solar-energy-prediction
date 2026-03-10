from __future__ import annotations

from dataclasses import dataclass
import logging
import math

from geopy.exc import (  # type: ignore
    GeocoderParseError,
    GeocoderQuotaExceeded,
    GeocoderServiceError,
    GeocoderTimedOut,
    GeocoderUnavailable,
)
from geopy.geocoders import Nominatim  # type: ignore

try:
    from solar_ui.config import (
        get_default_demo_scenario_id,
        get_demo_scenario_by_id,
        get_demo_scenarios,
    )
except ModuleNotFoundError:
    from config import (
        get_default_demo_scenario_id,
        get_demo_scenario_by_id,
        get_demo_scenarios,
    )


logger = logging.getLogger(__name__)

GEOCODER_TIMEOUT_SECONDS = 8
GEOCODER_USER_AGENT = "solar_energy_prediction_alpha"


@dataclass(frozen=True)
class GeocodingLookupResult:
    latitude: float | None = None
    longitude: float | None = None
    address: str | None = None
    error_message: str | None = None

    @property
    def is_success(self) -> bool:
        return self.latitude is not None and self.longitude is not None


def estimate_area_m2_from_bounds(bounds):
    """
    bounds = [[lat1, lon1], [lat2, lon2]]
    """
    (lat1, lon1), (lat2, lon2) = bounds

    # Rough meters per degree
    meters_per_deg_lat = 111_000
    meters_per_deg_lon = 111_000 * math.cos(math.radians((lat1 + lat2) / 2))

    width = abs(lon2 - lon1) * meters_per_deg_lon
    height = abs(lat2 - lat1) * meters_per_deg_lat

    return width * height


def build_geolocator(user_agent: str = GEOCODER_USER_AGENT) -> Nominatim:
    return Nominatim(user_agent=user_agent, timeout=GEOCODER_TIMEOUT_SECONDS)


def normalize_address(value: str) -> str:
    return " ".join(value.lower().replace(",", " ").split())


def find_demo_scenario_by_address(address: str) -> dict | None:
    normalized_address = normalize_address(address)
    for scenario in get_demo_scenarios():
        searchable_parts = [
            scenario["address"],
            f"{scenario['street']} {scenario['number']}, {scenario['city']}, {scenario['country']}",
            scenario["name"],
        ]
        if any(normalize_address(part) == normalized_address for part in searchable_parts):
            return scenario
        scenario_address = normalize_address(str(scenario["address"]))
        if normalized_address and all(token in scenario_address for token in normalized_address.split()):
            return scenario
    return None


def find_demo_scenario_by_coordinates(lat: float, lon: float) -> dict:
    return min(
        get_demo_scenarios(),
        key=lambda scenario: (
            (float(scenario["latitude"]) - lat) ** 2
            + (float(scenario["longitude"]) - lon) ** 2
        ),
    )


def build_demo_lookup_result(scenario: dict) -> GeocodingLookupResult:
    return GeocodingLookupResult(
        latitude=float(scenario["latitude"]),
        longitude=float(scenario["longitude"]),
        address=str(scenario["address"]),
    )


def geocode_address(
    address: str,
    *,
    demo_mode: bool = False,
    demo_scenario_id: str | None = None,
) -> GeocodingLookupResult:
    if demo_mode:
        scenario = (
            get_demo_scenario_by_id(demo_scenario_id)
            if demo_scenario_id
            else find_demo_scenario_by_address(address)
        )
        if scenario is None:
            scenario = get_demo_scenario_by_id(get_default_demo_scenario_id())
        return build_demo_lookup_result(scenario)

    try:
        geolocator = build_geolocator()
        location = geolocator.geocode(address)
        if location is None:
            return GeocodingLookupResult(
                error_message="Address could not be resolved. Try a more specific address.",
            )
        return GeocodingLookupResult(
            latitude=float(location.latitude),
            longitude=float(location.longitude),
            address=location.address or address,
        )
    except GeocoderTimedOut:
        return GeocodingLookupResult(
            error_message="Address lookup timed out. Please try again.",
        )
    except GeocoderQuotaExceeded:
        return GeocodingLookupResult(
            error_message="Address lookup is temporarily rate limited. Please wait a minute and try again.",
        )
    except (GeocoderUnavailable, GeocoderServiceError, GeocoderParseError) as exc:
        logger.warning("Geocoding service error for '%s': %s", address, exc)
        return GeocodingLookupResult(
            error_message="Address lookup service is temporarily unavailable. Please try again shortly.",
        )
    except Exception as exc:
        logger.exception("Unexpected geocoding failure for '%s': %s", address, exc)
        return GeocodingLookupResult(
            error_message="Address lookup failed unexpectedly. Please try again.",
        )


def reverse_geocode(
    lat: float,
    lon: float,
    *,
    demo_mode: bool = False,
    demo_scenario_id: str | None = None,
) -> GeocodingLookupResult:
    if demo_mode:
        scenario = (
            get_demo_scenario_by_id(demo_scenario_id)
            if demo_scenario_id
            else find_demo_scenario_by_coordinates(lat, lon)
        )
        return build_demo_lookup_result(scenario)

    try:
        geolocator = build_geolocator()
        location = geolocator.reverse((lat, lon), language="en")
        if location is None:
            return GeocodingLookupResult(
                latitude=lat,
                longitude=lon,
                error_message="Reverse geocoding could not resolve this point. Coordinates will be shown instead.",
            )
        return GeocodingLookupResult(
            latitude=lat,
            longitude=lon,
            address=location.address,
        )
    except GeocoderTimedOut:
        return GeocodingLookupResult(
            latitude=lat,
            longitude=lon,
            error_message="Reverse geocoding timed out. Coordinates will be shown instead.",
        )
    except GeocoderQuotaExceeded:
        return GeocodingLookupResult(
            latitude=lat,
            longitude=lon,
            error_message="Reverse geocoding is temporarily rate limited. Coordinates will be shown instead.",
        )
    except (GeocoderUnavailable, GeocoderServiceError, GeocoderParseError) as exc:
        logger.warning("Reverse geocoding service error for (%s, %s): %s", lat, lon, exc)
        return GeocodingLookupResult(
            latitude=lat,
            longitude=lon,
            error_message="Reverse geocoding is temporarily unavailable. Coordinates will be shown instead.",
        )
    except Exception as exc:
        logger.exception("Unexpected reverse geocoding failure for (%s, %s): %s", lat, lon, exc)
        return GeocodingLookupResult(
            latitude=lat,
            longitude=lon,
            error_message="Reverse geocoding failed unexpectedly. Coordinates will be shown instead.",
        )
