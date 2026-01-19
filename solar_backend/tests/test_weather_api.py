from app.services.weather_service import get_weather_forecast

def test_weather_api_fields():
    lat = 52.52  # Berlin
    lon = 13.405
    data = get_weather_forecast(lat, lon, days=1)
    assert data is not None, "Response should not be None"
    assert isinstance(data, dict), "Response should be a dictionary"
    assert "hourly" in data, "Response should contain 'hourly' key"
    hourly = data["hourly"]
    assert "shortwave_radiation" in hourly, "Hourly data should contain 'shortwave_radiation'"
    assert "temperature_2m" in hourly, "Hourly data should contain 'temperature_2m'"