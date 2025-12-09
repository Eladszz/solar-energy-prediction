import requests

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
    res = requests.get(url)
    res.raise_for_status()
    return res.json()



