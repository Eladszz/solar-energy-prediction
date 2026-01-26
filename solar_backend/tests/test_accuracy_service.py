import pytest
from unittest.mock import patch
import pandas as pd
import numpy as np
from app.services.accuracy_service import (
    calculate_mape,
    evaluate_yearly_accuracy
)


class TestCalculateMAPE:
    """Test suite for MAPE calculation."""

    def test_mape_basic_calculation(self):
        """Test basic MAPE calculation."""
        actual = 100.0
        predicted = 90.0
        mape = calculate_mape(actual, predicted)
        assert mape == 10.0

    def test_mape_perfect_prediction(self):
        """Test MAPE when prediction is perfect."""
        actual = 100.0
        predicted = 100.0
        mape = calculate_mape(actual, predicted)
        assert mape == 0.0

    def test_mape_overprediction(self):
        """Test MAPE when prediction is higher than actual."""
        actual = 100.0
        predicted = 120.0
        mape = calculate_mape(actual, predicted)
        assert mape == 20.0

    def test_mape_zero_actual(self):
        """Test MAPE when actual value is zero."""
        actual = 0.0
        predicted = 50.0
        mape = calculate_mape(actual, predicted)
        assert mape == 0.0

    def test_mape_negative_values(self):
        """Test MAPE with negative values (should use absolute difference)."""
        actual = -100.0
        predicted = -90.0
        mape = calculate_mape(actual, predicted)
        assert mape == 10.0

    def test_mape_small_values(self):
        """Test MAPE with small decimal values."""
        actual = 0.5
        predicted = 0.45
        mape = calculate_mape(actual, predicted)
        assert pytest.approx(mape, rel=1e-2) == 10.0

    def test_mape_large_error(self):
        """Test MAPE with large error."""
        actual = 100.0
        predicted = 200.0
        mape = calculate_mape(actual, predicted)
        assert mape == 100.0


class TestEvaluateYearlyAccuracy:
    """Test suite for yearly accuracy evaluation."""

    @pytest.fixture
    def mock_weather_data(self):
        """Create mock weather data DataFrame."""
        hours = 8760  # Full year
        dates = pd.date_range(start='2024-01-01', periods=hours, freq='h')
        return pd.DataFrame({
            'time': dates,
            'irr': np.random.uniform(0, 1000, hours),  # W/m²
            'temp': np.random.uniform(10, 35, hours)   # °C
        })

    @pytest.fixture
    def sample_params(self):
        """Sample parameters for testing."""
        return {
            'latitude': 32.08,
            'longitude': 34.78,
            'year': 2024,
            'tilt': 30.0,
            'panel_area': 80.0,
            'efficiency': 0.20,
            'cleanliness': 'normal',
            'shading': 'low',
            'gamma': 0.004,
            'noct': 45.0,
            'ac_capacity_kw': 20.0
        }

    @patch('app.services.accuracy_service.get_year_archive')
    @patch('app.services.accuracy_service.compute_system_loss_factor')
    @patch('app.services.accuracy_service.compute_yearly_from_real_data')
    def test_evaluate_yearly_accuracy_excellent(
        self,
        mock_forecast,
        mock_loss_factor,
        mock_archive,
        mock_weather_data,
        sample_params
    ):
        """Test accuracy evaluation with excellent prediction (MAPE < 10%)."""
        # Setup mocks
        mock_archive.return_value = mock_weather_data
        mock_loss_factor.return_value = 0.85
        mock_forecast.return_value = {
            'yearly_kwh': 6850.5,
            'monthly_kwh': [500] * 12
        }

        # Execute
        result = evaluate_yearly_accuracy(**sample_params)

        # Verify
        assert 'year' in result
        assert 'actual_yearly_kwh' in result
        assert 'predicted_yearly_kwh' in result
        assert 'mape_percent' in result
        assert 'quality' in result
        
        assert result['year'] == 2024
        assert result['predicted_yearly_kwh'] == 6850.5
        assert isinstance(result['actual_yearly_kwh'], float)
        assert isinstance(result['mape_percent'], float)
        
        # Verify function calls
        mock_archive.assert_called_once_with(32.08, 34.78, 2024)
        mock_loss_factor.assert_called_once_with(
            cleanliness='normal',
            shading='low'
        )

    @patch('app.services.accuracy_service.get_year_archive')
    @patch('app.services.accuracy_service.compute_system_loss_factor')
    @patch('app.services.accuracy_service.compute_yearly_from_real_data')
    def test_evaluate_yearly_accuracy_good(
        self,
        mock_forecast,
        mock_loss_factor,
        mock_archive,
        mock_weather_data,
        sample_params
    ):
        """Test accuracy evaluation with good prediction (10% <= MAPE < 25%)."""
        mock_archive.return_value = mock_weather_data
        mock_loss_factor.return_value = 0.85
        
        # Create scenario where MAPE is between 10-25%
        actual_kwh = 7000.0
        predicted_kwh = 5600.0  # ~20% difference
        
        # Set irr values to produce desired actual_kwh
        irr_sum_needed = actual_kwh * 1000 / (80.0 * 0.20)
        avg_irr = irr_sum_needed / 8760
        mock_weather_data['irr'] = avg_irr
        
        mock_forecast.return_value = {
            'yearly_kwh': predicted_kwh,
            'monthly_kwh': [predicted_kwh/12] * 12
        }

        result = evaluate_yearly_accuracy(**sample_params)

        assert result['quality'] == 'GOOD'
        assert 10 <= result['mape_percent'] < 25

    @patch('app.services.accuracy_service.get_year_archive')
    @patch('app.services.accuracy_service.compute_system_loss_factor')
    @patch('app.services.accuracy_service.compute_yearly_from_real_data')
    def test_evaluate_yearly_accuracy_poor(
        self,
        mock_forecast,
        mock_loss_factor,
        mock_archive,
        mock_weather_data,
        sample_params
    ):
        """Test accuracy evaluation with poor prediction (MAPE >= 25%)."""
        mock_archive.return_value = mock_weather_data
        mock_loss_factor.return_value = 0.85
        
        # Create scenario where MAPE is > 25%
        actual_kwh = 7000.0
        predicted_kwh = 4500.0  # ~36% difference
        
        irr_sum_needed = actual_kwh * 1000 / (80.0 * 0.20)
        avg_irr = irr_sum_needed / 8760
        mock_weather_data['irr'] = avg_irr
        
        mock_forecast.return_value = {
            'yearly_kwh': predicted_kwh,
            'monthly_kwh': [predicted_kwh/12] * 12
        }

        result = evaluate_yearly_accuracy(**sample_params)

        assert result['quality'] == 'POOR'
        assert result['mape_percent'] >= 25

    @patch('app.services.accuracy_service.get_year_archive')
    @patch('app.services.accuracy_service.compute_system_loss_factor')
    @patch('app.services.accuracy_service.compute_yearly_from_real_data')
    def test_evaluate_yearly_accuracy_different_locations(
        self,
        mock_forecast,
        mock_loss_factor,
        mock_archive,
        mock_weather_data,
        sample_params
    ):
        """Test accuracy evaluation with different locations."""
        mock_archive.return_value = mock_weather_data
        mock_loss_factor.return_value = 0.85
        mock_forecast.return_value = {
            'yearly_kwh': 5000.0,
            'monthly_kwh': [416.67] * 12
        }

        # Test different location
        sample_params['latitude'] = 51.5074  # London
        sample_params['longitude'] = -0.1278
        
        result = evaluate_yearly_accuracy(**sample_params)

        assert result is not None
        mock_archive.assert_called_with(51.5074, -0.1278, 2024)

    @patch('app.services.accuracy_service.get_year_archive')
    @patch('app.services.accuracy_service.compute_system_loss_factor')
    @patch('app.services.accuracy_service.compute_yearly_from_real_data')
    def test_evaluate_yearly_accuracy_different_years(
        self,
        mock_forecast,
        mock_loss_factor,
        mock_archive,
        mock_weather_data,
        sample_params
    ):
        """Test accuracy evaluation with different years."""
        mock_archive.return_value = mock_weather_data
        mock_loss_factor.return_value = 0.85
        mock_forecast.return_value = {
            'yearly_kwh': 6000.0,
            'monthly_kwh': [500] * 12
        }

        for year in [2020, 2021, 2022, 2023, 2024]:
            sample_params['year'] = year
            result = evaluate_yearly_accuracy(**sample_params)
            assert result['year'] == year

    @patch('app.services.accuracy_service.get_year_archive')
    @patch('app.services.accuracy_service.compute_system_loss_factor')
    @patch('app.services.accuracy_service.compute_yearly_from_real_data')
    def test_evaluate_yearly_accuracy_different_system_configs(
        self,
        mock_forecast,
        mock_loss_factor,
        mock_archive,
        mock_weather_data,
        sample_params
    ):
        """Test accuracy evaluation with different system configurations."""
        mock_archive.return_value = mock_weather_data
        
        configs = [
            {'cleanliness': 'clean', 'shading': 'none', 'loss_factor': 0.90},
            {'cleanliness': 'normal', 'shading': 'low', 'loss_factor': 0.85},
            {'cleanliness': 'dusty', 'shading': 'high', 'loss_factor': 0.75},
        ]

        for config in configs:
            mock_loss_factor.return_value = config['loss_factor']
            mock_forecast.return_value = {
                'yearly_kwh': 6000.0,
                'monthly_kwh': [500] * 12
            }
            
            sample_params['cleanliness'] = config['cleanliness']
            sample_params['shading'] = config['shading']
            
            result = evaluate_yearly_accuracy(**sample_params)
            assert result is not None
            mock_loss_factor.assert_called_with(
                cleanliness=config['cleanliness'],
                shading=config['shading']
            )

    @patch('app.services.accuracy_service.get_year_archive')
    @patch('app.services.accuracy_service.compute_system_loss_factor')
    @patch('app.services.accuracy_service.compute_yearly_from_real_data')
    def test_evaluate_yearly_accuracy_rounding(
        self,
        mock_forecast,
        mock_loss_factor,
        mock_archive,
        mock_weather_data,
        sample_params
    ):
        """Test that results are properly rounded."""
        mock_archive.return_value = mock_weather_data
        mock_loss_factor.return_value = 0.85
        mock_forecast.return_value = {
            'yearly_kwh': 6850.123456,
            'monthly_kwh': [500.123456] * 12
        }

        result = evaluate_yearly_accuracy(**sample_params)

        # Check rounding
        assert result['predicted_yearly_kwh'] == 6850.1
        assert isinstance(result['actual_yearly_kwh'], float)
        assert isinstance(result['mape_percent'], float)
        
        # MAPE should be rounded to 2 decimal places
        str_mape = str(result['mape_percent'])
        if '.' in str_mape:
            decimal_places = len(str_mape.split('.')[1])
            assert decimal_places <= 2

    @patch('app.services.accuracy_service.get_year_archive')
    def test_evaluate_yearly_accuracy_archive_failure(
        self,
        mock_archive,
        sample_params
    ):
        """Test handling of archive service failure."""
        mock_archive.side_effect = Exception("API Error")

        with pytest.raises(Exception):
            evaluate_yearly_accuracy(**sample_params)

    @patch('app.services.accuracy_service.get_year_archive')
    @patch('app.services.accuracy_service.compute_system_loss_factor')
    @patch('app.services.accuracy_service.compute_yearly_from_real_data')
    def test_evaluate_yearly_accuracy_zero_irradiance(
        self,
        mock_forecast,
        mock_loss_factor,
        mock_archive,
        sample_params
    ):
        """Test handling of zero irradiance data."""
        # Create DataFrame with zero irradiance
        hours = 8760
        dates = pd.date_range(start='2024-01-01', periods=hours, freq='h')
        zero_irr_data = pd.DataFrame({
            'time': dates,
            'irr': np.zeros(hours),
            'temp': np.random.uniform(10, 35, hours)
        })
        
        mock_archive.return_value = zero_irr_data
        mock_loss_factor.return_value = 0.85
        mock_forecast.return_value = {
            'yearly_kwh': 100.0,  # Some prediction despite zero irradiance
            'monthly_kwh': [8.33] * 12
        }

        result = evaluate_yearly_accuracy(**sample_params)

        assert result['actual_yearly_kwh'] == 0.0
        assert result['mape_percent'] == 0.0  # Zero actual should return 0 MAPE
