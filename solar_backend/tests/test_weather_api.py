import pytest
from unittest.mock import patch, Mock
import requests
from app.exceptions.external_service_exceptions import (
    ExternalServiceRateLimitError,
    ExternalServiceResponseError,
    ExternalServiceTimeoutError,
    ExternalServiceUnavailableError,
)
from app.services.weather_service import get_weather_forecast


class TestGetWeatherForecast:
    """Test suite for weather forecast service."""

    def test_weather_api_fields(self):
        """Test actual API call returns expected fields."""
        lat = 52.52  # Berlin
        lon = 13.405
        try:
            data = get_weather_forecast(lat, lon, days=1)
        except (
            ExternalServiceRateLimitError,
            ExternalServiceTimeoutError,
            ExternalServiceUnavailableError,
            ExternalServiceResponseError,
        ):
            pytest.skip("Live weather API is unavailable in the current test environment")
        assert isinstance(data, dict), "Response should be a dictionary"
        assert "hourly" in data, "Response should contain 'hourly' key"
        hourly = data["hourly"]
        assert "shortwave_radiation" in hourly, "Hourly data should contain 'shortwave_radiation'"
        assert "temperature_2m" in hourly, "Hourly data should contain 'temperature_2m'"

    @pytest.fixture
    def mock_weather_response(self):
        """Create a mock successful weather API response."""
        return {
            "latitude": 52.52,
            "longitude": 13.405,
            "generationtime_ms": 0.123,
            "utc_offset_seconds": 3600,
            "timezone": "Europe/Berlin",
            "timezone_abbreviation": "CET",
            "elevation": 38.0,
            "hourly_units": {
                "time": "iso8601",
                "shortwave_radiation": "W/m²",
                "temperature_2m": "°C"
            },
            "hourly": {
                "time": [
                    "2024-01-01T00:00", "2024-01-01T01:00", "2024-01-01T02:00",
                    "2024-01-01T03:00", "2024-01-01T04:00", "2024-01-01T05:00"
                ],
                "shortwave_radiation": [0.0, 0.0, 0.0, 50.5, 150.3, 300.8],
                "temperature_2m": [2.5, 2.1, 1.8, 1.5, 1.9, 3.2]
            }
        }

    @patch('app.services.weather_service.requests.get')
    def test_get_weather_forecast_success(self, mock_get, mock_weather_response):
        """Test successful weather forecast retrieval."""
        mock_response = Mock()
        mock_response.json.return_value = mock_weather_response
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        result = get_weather_forecast(52.52, 13.405, days=1)

        assert result is not None
        assert isinstance(result, dict)
        assert 'hourly' in result
        assert 'shortwave_radiation' in result.get('hourly', {})
        assert 'temperature_2m' in result.get('hourly', {})
        
        mock_get.assert_called_once()
        call_url = mock_get.call_args[0][0]
        assert 'latitude=52.52' in call_url
        assert 'longitude=13.405' in call_url
        assert 'forecast_days=1' in call_url

    @patch('app.services.weather_service.requests.get')
    def test_get_weather_forecast_different_locations(self, mock_get, mock_weather_response):
        """Test weather forecast for different locations."""
        mock_response = Mock()
        mock_response.json.return_value = mock_weather_response
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        locations = [
            (52.52, 13.405),    # Berlin
            (40.7128, -74.0060),  # New York
            (35.6762, 139.6503),  # Tokyo
            (-33.8688, 151.2093)  # Sydney
        ]

        for lat, lon in locations:
            result = get_weather_forecast(lat, lon, days=1)
            assert result is not None
            call_url = mock_get.call_args[0][0]
            assert f'latitude={lat}' in call_url
            assert f'longitude={lon}' in call_url

    @patch('app.services.weather_service.requests.get')
    def test_get_weather_forecast_different_days(self, mock_get, mock_weather_response):
        """Test weather forecast with different forecast days."""
        mock_response = Mock()
        mock_response.json.return_value = mock_weather_response
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        for days in [1, 3, 7, 14]:
            result = get_weather_forecast(52.52, 13.405, days=days)
            assert result is not None
            call_url = mock_get.call_args[0][0]
            assert f'forecast_days={days}' in call_url

    @patch('app.services.weather_service.requests.get')
    def test_get_weather_forecast_default_days(self, mock_get, mock_weather_response):
        """Test weather forecast with default forecast days."""
        mock_response = Mock()
        mock_response.json.return_value = mock_weather_response
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        result = get_weather_forecast(52.52, 13.405)
        
        assert result is not None
        call_url = mock_get.call_args[0][0]
        assert 'forecast_days=1' in call_url

    @patch('app.services.weather_service.requests.get')
    def test_get_weather_forecast_url_parameters(self, mock_get, mock_weather_response):
        """Test that URL contains all required parameters."""
        mock_response = Mock()
        mock_response.json.return_value = mock_weather_response
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        get_weather_forecast(52.52, 13.405, days=3)
        
        call_url = mock_get.call_args[0][0]
        assert 'latitude=' in call_url
        assert 'longitude=' in call_url
        assert 'hourly=shortwave_radiation,temperature_2m' in call_url
        assert 'forecast_days=' in call_url
        assert 'past_days=0' in call_url
        assert 'timezone=auto' in call_url

    @patch('app.services.weather_service.requests.get')
    def test_get_weather_forecast_http_error_404(self, mock_get):
        """Test handling of 404 error."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        with pytest.raises(ExternalServiceResponseError):
            get_weather_forecast(52.52, 13.405, days=1)

    @patch('app.services.weather_service.requests.get')
    def test_get_weather_forecast_http_error_500(self, mock_get):
        """Test handling of 500 server error."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        with pytest.raises(ExternalServiceUnavailableError):
            get_weather_forecast(52.52, 13.405, days=1)

    @patch('app.services.weather_service.requests.get')
    def test_get_weather_forecast_http_error_403(self, mock_get):
        """Test handling of 403 forbidden error."""
        mock_response = Mock()
        mock_response.status_code = 403
        mock_get.return_value = mock_response

        with pytest.raises(ExternalServiceResponseError):
            get_weather_forecast(52.52, 13.405, days=1)

    @patch('app.services.weather_service.requests.get')
    def test_get_weather_forecast_partial_data(self, mock_get):
        """Test handling of response with partial hourly data."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "hourly": {
                "time": ["2024-01-01T00:00"],
                "shortwave_radiation": [100.0]
                # Missing temperature_2m
            }
        }
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        with pytest.raises(ExternalServiceResponseError):
            get_weather_forecast(52.52, 13.405, days=1)

    @patch('app.services.weather_service.requests.get')
    def test_get_weather_forecast_zero_days(self, mock_get, mock_weather_response):
        """Test weather forecast with zero forecast days."""
        mock_response = Mock()
        mock_response.json.return_value = mock_weather_response
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        result = get_weather_forecast(52.52, 13.405, days=0)
        
        assert result is not None
        call_url = mock_get.call_args[0][0]
        assert 'forecast_days=0' in call_url

    @patch('app.services.weather_service.requests.get')
    def test_get_weather_forecast_request_exception(self, mock_get):
        """Test handling of general request exception."""
        mock_get.side_effect = requests.exceptions.RequestException("Request failed")

        with pytest.raises(ExternalServiceUnavailableError):
            get_weather_forecast(52.52, 13.405, days=1)

    @patch('app.services.weather_service.requests.get')
    def test_get_weather_forecast_response_text_instead_of_json(self, mock_get):
        """Test handling when response is text instead of JSON."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = requests.exceptions.JSONDecodeError("Expecting value", "", 0)
        mock_get.return_value = mock_response

        with pytest.raises(ExternalServiceResponseError):
            get_weather_forecast(52.52, 13.405, days=1)

    @patch('app.services.weather_service.requests.get')
    def test_get_weather_forecast_null_values_in_arrays(self, mock_get):
        """Test handling of null values in response arrays."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "hourly": {
                "time": ["2024-01-01T00:00", "2024-01-01T01:00"],
                "shortwave_radiation": [100.0, None],
                "temperature_2m": [15.0, 16.0]
            }
        }
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        result = get_weather_forecast(52.52, 13.405, days=1)
        
        assert result is not None
        assert result['hourly']['shortwave_radiation'][1] is None

    @patch('app.services.weather_service.requests.get')
    def test_get_weather_forecast_boundary_latitude(self, mock_get, mock_weather_response):
        """Test weather forecast with boundary latitude values."""
        mock_response = Mock()
        mock_response.json.return_value = mock_weather_response
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        for lat in [-90, -89.9, 0, 89.9, 90]:
            result = get_weather_forecast(lat, 0, days=1)
            assert result is not None

    @patch('app.services.weather_service.requests.get')
    def test_get_weather_forecast_boundary_longitude(self, mock_get, mock_weather_response):
        """Test weather forecast with boundary longitude values."""
        mock_response = Mock()
        mock_response.json.return_value = mock_weather_response
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        for lon in [-180, -179.9, 0, 179.9, 180]:
            result = get_weather_forecast(0, lon, days=1)
            assert result is not None

    @patch('app.services.weather_service.requests.get')
    def test_get_weather_forecast_data_structure(self, mock_get, mock_weather_response):
        """Test that returned data has expected structure."""
        mock_response = Mock()
        mock_response.json.return_value = mock_weather_response
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        result = get_weather_forecast(52.52, 13.405, days=1)
        
        assert result is not None and 'hourly' in result
        hourly = result['hourly']
        assert 'time' in hourly
        assert 'shortwave_radiation' in hourly
        assert 'temperature_2m' in hourly
        
        # Check that arrays have same length
        assert len(hourly['time']) == len(hourly['shortwave_radiation'])
        assert len(hourly['time']) == len(hourly['temperature_2m'])

    @patch('app.services.weather_service.requests.get')
    def test_get_weather_forecast_radiation_values(self, mock_get, mock_weather_response):
        """Test that radiation values are in expected range."""
        mock_response = Mock()
        mock_response.json.return_value = mock_weather_response
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        result = get_weather_forecast(52.52, 13.405, days=1)
        
        assert result is not None
        radiation_values = result['hourly']['shortwave_radiation']
        # All values should be non-negative
        assert all(val >= 0 for val in radiation_values)

    @patch('app.services.weather_service.requests.get')
    def test_get_weather_forecast_temperature_values(self, mock_get, mock_weather_response):
        """Test that temperature values are in reasonable range."""
        mock_response = Mock()
        mock_response.json.return_value = mock_weather_response
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        result = get_weather_forecast(52.52, 13.405, days=1)
        
        assert result is not None
        temperature_values = result['hourly']['temperature_2m']
        # Reasonable temperature range (-60°C to 60°C)
        assert all(-60 <= temp <= 60 for temp in temperature_values)

    @patch('app.services.weather_service.requests.get')
    def test_get_weather_forecast_rate_limiting(self, mock_get):
        """Test handling of rate limiting (429 error)."""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_get.return_value = mock_response

        with pytest.raises(ExternalServiceRateLimitError):
            get_weather_forecast(52.52, 13.405, days=1)

    @patch('app.services.weather_service.requests.get')
    def test_get_weather_forecast_logging(self, mock_get, mock_weather_response, caplog):
        """Test that appropriate logging occurs."""
        import logging
        
        mock_response = Mock()
        mock_response.json.return_value = mock_weather_response
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        with caplog.at_level(logging.INFO):
            get_weather_forecast(52.52, 13.405, days=1)

        # Check that logging messages exist
        assert any('Fetching weather forecast' in record.message for record in caplog.records)
        assert any('Received weather forecast data' in record.message for record in caplog.records)

    @patch('app.services.weather_service.requests.get')
    def test_get_weather_forecast_decimal_precision(self, mock_get, mock_weather_response):
        """Test that decimal precision in coordinates is preserved."""
        mock_response = Mock()
        mock_response.json.return_value = mock_weather_response
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        lat = 52.5235
        lon = 13.4050
        
        get_weather_forecast(lat, lon, days=1)
        
        call_url = mock_get.call_args[0][0]
        assert f'latitude={lat}' in call_url
        assert f'longitude={lon}' in call_url

    @patch('app.services.weather_service.requests.get')
    def test_get_weather_forecast_generic_exception(self, mock_get):
        """Test handling of generic exceptions."""
        mock_get.side_effect = Exception("Unexpected error")

        with pytest.raises(ExternalServiceUnavailableError):
            get_weather_forecast(52.52, 13.405, days=1)

    @patch('app.services.weather_service.requests.get')
    def test_get_weather_forecast_max_days(self, mock_get, mock_weather_response):
        """Test weather forecast with maximum forecast days."""
        mock_response = Mock()
        mock_response.json.return_value = mock_weather_response
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        # API typically supports up to 16 days
        result = get_weather_forecast(52.52, 13.405, days=16)
        
        assert result is not None
        call_url = mock_get.call_args[0][0]
        assert 'forecast_days=16' in call_url
