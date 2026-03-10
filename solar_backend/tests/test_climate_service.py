import pytest
from unittest.mock import patch, Mock
import requests
from app.services.external_service import (
    ExternalServiceRateLimitError,
    ExternalServiceResponseError,
    ExternalServiceTimeoutError,
    ExternalServiceUnavailableError,
)
from app.services.climate_service import get_climate_daily


class TestGetClimateDaily:
    """Test suite for climate service."""

    @pytest.fixture
    def mock_climate_response(self):
        """Create a mock successful climate API response."""
        return {
            "latitude": 32.08,
            "longitude": 34.78,
            "generationtime_ms": 0.123,
            "utc_offset_seconds": 0,
            "timezone": "GMT",
            "timezone_abbreviation": "GMT",
            "daily": {
                "time": [
                    "1991-01-01", "1991-01-02", "1991-01-03", "1991-01-04",
                    "1991-01-05", "1991-01-06", "1991-01-07", "1991-01-08"
                ],
                "shortwave_radiation_sum": [
                    12500.5, 13200.3, 11800.7, 14300.2,
                    13500.8, 12900.4, 13700.6, 14100.9
                ],
                "temperature_2m_mean": [
                    15.2, 16.5, 14.8, 17.3,
                    16.1, 15.7, 16.9, 17.8
                ]
            }
        }

    @patch('app.services.climate_service.requests.get')
    def test_get_climate_daily_success(self, mock_get, mock_climate_response):
        """Test successful climate data retrieval."""
        # Setup mock
        mock_response = Mock()
        mock_response.json.return_value = mock_climate_response
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        # Execute
        result = get_climate_daily(32.08, 34.78)

        # Verify
        assert result is not None
        assert isinstance(result, dict)
        assert 'daily' in result
        assert 'shortwave_radiation_sum' in result['daily']
        assert 'temperature_2m_mean' in result['daily']
        assert result['latitude'] == 32.08
        assert result['longitude'] == 34.78

        # Verify API call
        mock_get.assert_called_once()
        call_url = mock_get.call_args[0][0]
        assert 'latitude=32.08' in call_url
        assert 'longitude=34.78' in call_url
        assert 'start_year=1991' in call_url
        assert 'end_year=2020' in call_url
        assert 'shortwave_radiation_sum' in call_url
        assert 'temperature_2m_mean' in call_url

    @patch('app.services.climate_service.requests.get')
    def test_get_climate_daily_response_structure(self, mock_get, mock_climate_response):
        """Test that response has expected structure."""
        mock_response = Mock()
        mock_response.json.return_value = mock_climate_response
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        result = get_climate_daily(32.08, 34.78)

        # Check structure
        assert 'daily' in result
        daily = result['daily']
        assert 'time' in daily
        assert 'shortwave_radiation_sum' in daily
        assert 'temperature_2m_mean' in daily
        
        # Check data types
        assert isinstance(daily['time'], list)
        assert isinstance(daily['shortwave_radiation_sum'], list)
        assert isinstance(daily['temperature_2m_mean'], list)
        
        # Check data lengths match
        assert len(daily['time']) == len(daily['shortwave_radiation_sum'])
        assert len(daily['time']) == len(daily['temperature_2m_mean'])

    @patch('app.services.climate_service.requests.get')
    def test_get_climate_daily_different_locations(self, mock_get, mock_climate_response):
        """Test climate data retrieval for different locations."""
        mock_response = Mock()
        mock_response.json.return_value = mock_climate_response
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        locations = [
            (32.08, 34.78),    # Tel Aviv
            (51.5074, -0.1278), # London
            (40.7128, -74.0060), # New York
            (-33.8688, 151.2093), # Sydney
            (0.0, 0.0)          # Null Island
        ]

        for lat, lon in locations:
            result = get_climate_daily(lat, lon)
            assert result is not None
            
            # Verify correct coordinates in URL
            call_url = mock_get.call_args[0][0]
            assert f'latitude={lat}' in call_url
            assert f'longitude={lon}' in call_url

    @patch('app.services.climate_service.requests.get')
    def test_get_climate_daily_extreme_coordinates(self, mock_get, mock_climate_response):
        """Test climate data retrieval with extreme coordinates."""
        mock_response = Mock()
        mock_response.json.return_value = mock_climate_response
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        # Test extreme values
        extreme_locations = [
            (90.0, 0.0),     # North Pole
            (-90.0, 0.0),    # South Pole
            (0.0, 180.0),    # Eastern edge
            (0.0, -180.0),   # Western edge
        ]

        for lat, lon in extreme_locations:
            result = get_climate_daily(lat, lon)
            assert result is not None

    @patch('app.services.climate_service.requests.get')
    def test_get_climate_daily_api_error_404(self, mock_get):
        """Test handling of 404 error from API."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        with pytest.raises(ExternalServiceResponseError):
            get_climate_daily(32.08, 34.78)

    @patch('app.services.climate_service.requests.get')
    def test_get_climate_daily_api_error_500(self, mock_get):
        """Test handling of 500 server error from API."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        with pytest.raises(ExternalServiceUnavailableError):
            get_climate_daily(32.08, 34.78)

    @patch('app.services.climate_service.requests.get')
    def test_get_climate_daily_connection_timeout(self, mock_get):
        """Test handling of connection timeout."""
        mock_get.side_effect = requests.exceptions.Timeout("Connection timeout")

        with pytest.raises(ExternalServiceTimeoutError):
            get_climate_daily(32.08, 34.78)

    @patch('app.services.climate_service.requests.get')
    def test_get_climate_daily_connection_error(self, mock_get):
        """Test handling of connection error."""
        mock_get.side_effect = requests.exceptions.ConnectionError("Failed to connect")

        with pytest.raises(ExternalServiceUnavailableError):
            get_climate_daily(32.08, 34.78)

    @patch('app.services.climate_service.requests.get')
    def test_get_climate_daily_url_format(self, mock_get, mock_climate_response):
        """Test that URL is properly formatted with all required parameters."""
        mock_response = Mock()
        mock_response.json.return_value = mock_climate_response
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        get_climate_daily(32.08, 34.78)

        call_url = mock_get.call_args[0][0]
        
        # Verify base URL
        assert call_url.startswith('https://climate-api.open-meteo.com/v1/climate')
        
        # Verify all required parameters
        assert 'latitude=' in call_url
        assert 'longitude=' in call_url
        assert 'start_year=1991' in call_url
        assert 'end_year=2020' in call_url
        assert 'daily=shortwave_radiation_sum,temperature_2m_mean' in call_url
        assert 'models=best_match' in call_url

    @patch('app.services.climate_service.requests.get')
    def test_get_climate_daily_negative_coordinates(self, mock_get, mock_climate_response):
        """Test climate data retrieval with negative coordinates."""
        mock_response = Mock()
        mock_response.json.return_value = mock_climate_response
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        # Southern hemisphere and western hemisphere
        result = get_climate_daily(-23.5505, -46.6333)  # São Paulo

        assert result is not None
        call_url = mock_get.call_args[0][0]
        assert 'latitude=-23.5505' in call_url
        assert 'longitude=-46.6333' in call_url

    @patch('app.services.climate_service.requests.get')
    def test_get_climate_daily_decimal_precision(self, mock_get, mock_climate_response):
        """Test that decimal precision in coordinates is preserved."""
        mock_response = Mock()
        mock_response.json.return_value = mock_climate_response
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        # High precision coordinates
        lat = 32.0853
        lon = 34.7818
        
        get_climate_daily(lat, lon)

        call_url = mock_get.call_args[0][0]
        assert f'latitude={lat}' in call_url
        assert f'longitude={lon}' in call_url

    @patch('app.services.climate_service.requests.get')
    def test_get_climate_daily_json_parsing_error(self, mock_get):
        """Test handling of JSON parsing error."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_get.return_value = mock_response

        with pytest.raises(ExternalServiceResponseError):
            get_climate_daily(32.08, 34.78)

    @patch('app.services.climate_service.requests.get')
    def test_get_climate_daily_empty_response(self, mock_get):
        """Test handling of empty response."""
        mock_response = Mock()
        mock_response.json.return_value = {}
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        with pytest.raises(ExternalServiceResponseError):
            get_climate_daily(32.08, 34.78)

    @patch('app.services.climate_service.requests.get')
    def test_get_climate_daily_partial_data(self, mock_get):
        """Test handling of partial data in response."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "daily": {
                "time": ["1991-01-01"],
                "shortwave_radiation_sum": [12500.5]
                # Missing temperature_2m_mean
            }
        }
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        with pytest.raises(ExternalServiceResponseError):
            get_climate_daily(32.08, 34.78)

    @patch('app.services.climate_service.requests.get')
    def test_get_climate_daily_logging(self, mock_get, mock_climate_response, caplog):
        """Test that appropriate logging occurs."""
        import logging
        
        mock_response = Mock()
        mock_response.json.return_value = mock_climate_response
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        with caplog.at_level(logging.INFO):
            get_climate_daily(32.08, 34.78)

        # Check that logging messages exist
        assert any('Fetching climate data' in record.message for record in caplog.records)
        assert any('Received climate data' in record.message for record in caplog.records)

    @patch('app.services.climate_service.requests.get')
    def test_get_climate_daily_radiation_values(self, mock_get, mock_climate_response):
        """Test that radiation values are in expected range."""
        mock_response = Mock()
        mock_response.json.return_value = mock_climate_response
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        result = get_climate_daily(32.08, 34.78)
        
        radiation_values = result['daily']['shortwave_radiation_sum']
        
        # All values should be positive (or zero)
        assert all(val >= 0 for val in radiation_values)
        
        # Reasonable maximum (e.g., < 50000 Wh/m²/day)
        assert all(val < 50000 for val in radiation_values)

    @patch('app.services.climate_service.requests.get')
    def test_get_climate_daily_temperature_values(self, mock_get, mock_climate_response):
        """Test that temperature values are in expected range."""
        mock_response = Mock()
        mock_response.json.return_value = mock_climate_response
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        result = get_climate_daily(32.08, 34.78)
        
        temperature_values = result['daily']['temperature_2m_mean']
        
        # Reasonable temperature range (-60°C to 60°C)
        assert all(-60 <= temp <= 60 for temp in temperature_values)

    @patch('app.services.climate_service.requests.get')
    def test_get_climate_daily_rate_limiting(self, mock_get):
        """Test handling of rate limiting (429 error)."""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_get.return_value = mock_response

        with pytest.raises(ExternalServiceRateLimitError):
            get_climate_daily(32.08, 34.78)

    @patch('app.services.climate_service.requests.get')
    def test_get_climate_daily_integer_coordinates(self, mock_get, mock_climate_response):
        """Test that integer coordinates work correctly."""
        mock_response = Mock()
        mock_response.json.return_value = mock_climate_response
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        # Use integer coordinates
        result = get_climate_daily(32, 34)

        assert result is not None
        call_url = mock_get.call_args[0][0]
        assert 'latitude=32' in call_url
        assert 'longitude=34' in call_url
