import math
from geopy.geocoders import Nominatim # type: ignore

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


def reverse_geocode(lat: float, lon: float) -> str | None:
    try:
        geolocator = Nominatim(user_agent="solar_app")
        location = geolocator.reverse((lat, lon), language="en")
        return location.address if location else None
    except Exception:
        return None
