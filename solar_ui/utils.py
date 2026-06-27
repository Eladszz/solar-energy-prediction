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


def geocode_address(address: str) -> GeocodingLookupResult:
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


def reverse_geocode(lat: float, lon: float) -> GeocodingLookupResult:
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
