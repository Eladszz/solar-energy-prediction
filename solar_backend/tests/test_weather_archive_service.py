from unittest.mock import patch, Mock
import pytest
import requests
import pandas as pd
from app.services.external_service import (
    ExternalServiceResponseError,
    ExternalServiceUnavailableError,
)
from app.services.weather_archive_service import get_year_archive


class TestGetYearArchive:
    """Test suite for weather archive service."""

    @pytest.fixture
    def mock_archive_response(self):
        """Create a mock successful archive API response for a full year."""
        # Generate hourly data for one year (8760 hours)
        times = pd.date_range(start='2023-01-01', end='2023-12-31 23:00:00', freq='h')
        return {
            "latitude": 52.52,
            "longitude": 13.405,
            "generationtime_ms": 150.5,
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
                "time": [t.strftime("%Y-%m-%dT%H:%M") for t in times],
                "shortwave_radiation": [100.0 + i % 500 for i in range(len(times))],
                "temperature_2m": [15.0 + (i % 20) - 10 for i in range(len(times))]
            }
        }

    @pytest.fixture
    def mock_partial_archive_response(self):
        """Create a mock response with partial data."""
        times = ["2023-01-01T00:00", "2023-01-01T01:00", "2023-01-01T02:00"]
        return {
            "hourly": {
                "time": times,
                "shortwave_radiation": [0.0, 0.0, 50.5],
                "temperature_2m": [2.5, 2.1, 1.8]
            }
        }

    @patch('app.services.weather_archive_service.requests.get')
    def test_get_year_archive_success(self, mock_get, mock_archive_response):
        """Test successful retrieval of yearly archive data."""
        mock_response = Mock()
        mock_response.json.return_value = mock_archive_response
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        result = get_year_archive(52.52, 13.405, 2023)

        assert result is not None
        assert isinstance(result, pd.DataFrame)
        assert 'time' in result.columns
        assert 'irr' in result.columns
        assert 'temp' in result.columns
        assert len(result) == 8760  # Hours in a year
        
        mock_get.assert_called_once()
        call_url = mock_get.call_args[0][0]
        assert 'latitude=52.52' in call_url
        assert 'longitude=13.405' in call_url
        assert 'start_date=2023-01-01' in call_url
        assert 'end_date=2023-12-31' in call_url

    @patch('app.services.weather_archive_service.requests.get')
    def test_get_year_archive_url_parameters(self, mock_get, mock_archive_response):
        """Test that URL contains all required parameters."""
        mock_response = Mock()
        mock_response.json.return_value = mock_archive_response
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        get_year_archive(52.52, 13.405, 2022)
        
        call_url = mock_get.call_args[0][0]
        assert 'latitude=' in call_url
        assert 'longitude=' in call_url
        assert 'start_date=' in call_url
        assert 'end_date=' in call_url
        assert 'hourly=shortwave_radiation,temperature_2m' in call_url

    @patch('app.services.weather_archive_service.requests.get')
    def test_get_year_archive_different_years(self, mock_get, mock_archive_response):
        """Test archive retrieval for different years."""
        mock_response = Mock()
        mock_response.json.return_value = mock_archive_response
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        years = [2020, 2021, 2022, 2023, 2024]
        for year in years:
            result = get_year_archive(52.52, 13.405, year)
            assert result is not None
            call_url = mock_get.call_args[0][0]
            assert f'start_date={year}-01-01' in call_url
            assert f'end_date={year}-12-31' in call_url

    @patch('app.services.weather_archive_service.requests.get')
    def test_get_year_archive_different_locations(self, mock_get, mock_archive_response):
        """Test archive retrieval for different locations."""
        mock_response = Mock()
        mock_response.json.return_value = mock_archive_response
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        locations = [
            (52.52, 13.405),      # Berlin
            (51.5074, -0.1278),   # London
            (40.7128, -74.0060),  # New York
            (35.6762, 139.6503),  # Tokyo
            (-33.8688, 151.2093)  # Sydney
        ]

        for lat, lon in locations:
            result = get_year_archive(lat, lon, 2023)
            assert result is not None
            assert isinstance(result, pd.DataFrame)

    @patch('app.services.weather_archive_service.requests.get')
    def test_get_year_archive_dataframe_structure(self, mock_get, mock_archive_response):
        """Test that returned DataFrame has correct structure."""
        mock_response = Mock()
        mock_response.json.return_value = mock_archive_response
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        result = get_year_archive(52.52, 13.405, 2023)

        assert isinstance(result, pd.DataFrame)
        assert list(result.columns) == ['time', 'irr', 'temp']
        assert pd.api.types.is_datetime64_any_dtype(result['time'])
        assert all(isinstance(val, (int, float)) for val in result['irr'])
        assert all(isinstance(val, (int, float)) for val in result['temp'])

    @patch('app.services.weather_archive_service.requests.get')
    def test_get_year_archive_leap_year(self, mock_get):
        """Test archive retrieval for leap year (366 days = 8784 hours)."""
        # 2024 is a leap year
        times = pd.date_range(start='2024-01-01', end='2024-12-31 23:00:00', freq='h')
        leap_year_response = {
            "hourly": {
                "time": [t.strftime("%Y-%m-%dT%H:%M") for t in times],
                "shortwave_radiation": [100.0] * len(times),
                "temperature_2m": [15.0] * len(times)
            }
        }
        
        mock_response = Mock()
        mock_response.json.return_value = leap_year_response
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        result = get_year_archive(52.52, 13.405, 2024)

        assert len(result) == 8784  # Hours in a leap year

    @patch('app.services.weather_archive_service.requests.get')
    def test_get_year_archive_http_error_404(self, mock_get):
        """Test handling of 404 error."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        with pytest.raises(ExternalServiceResponseError):
            get_year_archive(52.52, 13.405, 2023)

    @patch('app.services.weather_archive_service.requests.get')
    def test_get_year_archive_http_error_500(self, mock_get):
        """Test handling of 500 server error."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        with pytest.raises(ExternalServiceUnavailableError):
            get_year_archive(52.52, 13.405, 2023)

    @patch('app.services.weather_archive_service.requests.get')
    def test_get_year_archive_request_exception(self, mock_get):
        """Test handling of general request exception."""
        mock_get.side_effect = requests.exceptions.RequestException("Connection error")

        with pytest.raises(ExternalServiceUnavailableError):
            get_year_archive(52.52, 13.405, 2023)

    @patch('app.services.weather_archive_service.requests.get')
    def test_get_year_archive_missing_hourly_data(self, mock_get):
        """Test handling when hourly data is missing."""
        mock_response = Mock()
        mock_response.json.return_value = {}
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        with pytest.raises(ExternalServiceResponseError):
            get_year_archive(52.52, 13.405, 2023)

    @patch('app.services.weather_archive_service.requests.get')
    def test_get_year_archive_partial_fields(self, mock_get):
        """Test handling when only some fields are present."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "hourly": {
                "time": ["2023-01-01T00:00"],
                "shortwave_radiation": [100.0]
                # Missing temperature_2m
            }
        }
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        with pytest.raises(ExternalServiceResponseError):
            get_year_archive(52.52, 13.405, 2023)

    @patch('app.services.weather_archive_service.requests.get')
    def test_get_year_archive_null_values(self, mock_get):
        """Test handling of null values in data arrays."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "hourly": {
                "time": ["2023-01-01T00:00", "2023-01-01T01:00", "2023-01-01T02:00"],
                "shortwave_radiation": [100.0, None, 150.0],
                "temperature_2m": [15.0, 16.0, None]
            }
        }
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        result = get_year_archive(52.52, 13.405, 2023)

        assert len(result) == 3
        assert result['irr'][1] is None or pd.isna(result['irr'][1])
        assert result['temp'][2] is None or pd.isna(result['temp'][2])

    @patch('app.services.weather_archive_service.requests.get')
    def test_get_year_archive_boundary_coordinates(self, mock_get, mock_archive_response):
        """Test archive retrieval with boundary coordinate values."""
        mock_response = Mock()
        mock_response.json.return_value = mock_archive_response
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        # Test boundary latitudes
        for lat in [-90, -89.9, 0, 89.9, 90]:
            result = get_year_archive(lat, 0, 2023)
            assert result is not None

        # Test boundary longitudes
        for lon in [-180, -179.9, 0, 179.9, 180]:
            result = get_year_archive(0, lon, 2023)
            assert result is not None

    @patch('app.services.weather_archive_service.requests.get')
    def test_get_year_archive_old_year(self, mock_get, mock_archive_response):
        """Test archive retrieval for older years."""
        mock_response = Mock()
        mock_response.json.return_value = mock_archive_response
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        # Test years from 1950 to 2000
        for year in [1950, 1970, 1990, 2000]:
            result = get_year_archive(52.52, 13.405, year)
            assert result is not None
            call_url = mock_get.call_args[0][0]
            assert f'start_date={year}-01-01' in call_url

    @patch('app.services.weather_archive_service.requests.get')
    def test_get_year_archive_radiation_values(self, mock_get, mock_archive_response):
        """Test that radiation values are numeric and non-negative."""
        mock_response = Mock()
        mock_response.json.return_value = mock_archive_response
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        result = get_year_archive(52.52, 13.405, 2023)

        assert all(isinstance(val, (int, float)) for val in result['irr'])
        assert all(val >= 0 for val in result['irr'])

    @patch('app.services.weather_archive_service.requests.get')
    def test_get_year_archive_temperature_values(self, mock_get, mock_archive_response):
        """Test that temperature values are numeric and in reasonable range."""
        mock_response = Mock()
        mock_response.json.return_value = mock_archive_response
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        result = get_year_archive(52.52, 13.405, 2023)

        assert all(isinstance(val, (int, float)) for val in result['temp'])
        # Temperature should be in a reasonable range (-100 to 100 °C)
        assert all(-100 <= val <= 100 for val in result['temp'])

    @patch('app.services.weather_archive_service.requests.get')
    def test_get_year_archive_time_column_sorted(self, mock_get, mock_archive_response):
        """Test that time column is properly sorted chronologically."""
        mock_response = Mock()
        mock_response.json.return_value = mock_archive_response
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        result = get_year_archive(52.52, 13.405, 2023)

        time_values = result['time'].values
        assert all(time_values[i] <= time_values[i+1] for i in range(len(time_values)-1))

    @patch('app.services.weather_archive_service.requests.get')
    def test_get_year_archive_json_decode_error(self, mock_get):
        """Test handling when response is not valid JSON."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = requests.exceptions.JSONDecodeError("Expecting value", "", 0)
        mock_get.return_value = mock_response

        with pytest.raises(ExternalServiceResponseError):
            get_year_archive(52.52, 13.405, 2023)

    @patch('app.services.weather_archive_service.requests.get')
    def test_get_year_archive_logging(self, mock_get, mock_archive_response, caplog):
        """Test that appropriate logging occurs."""
        mock_response = Mock()
        mock_response.json.return_value = mock_archive_response
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        with caplog.at_level('INFO'):
            get_year_archive(52.52, 13.405, 2023)

        assert any('Fetching weather archive data' in record.message for record in caplog.records)
        assert any('Received weather archive data' in record.message for record in caplog.records)
