import pytest
from unittest.mock import patch
import pandas as pd
import numpy as np
from app.services.scenario_comparison_service import compare_yearly_scenarios
from app.models.requests import BasePVRequest


class TestCompareYearlyScenarios:
    """Test suite for scenario comparison service."""

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
    def base_scenario(self):
        """Create a base scenario for testing."""
        return BasePVRequest(
            latitude=32.08,
            longitude=34.78,
            tilt=30.0,
            panel_area=80.0,
            panel_efficiency=0.20,
            cleanliness="normal",
            shading="low",
            ac_capacity_kw=15.0,
            gamma=0.004,
            noct=45.0
        )

    @pytest.fixture
    def alternative_scenarios(self):
        """Create alternative scenarios for comparison."""
        return [
            BasePVRequest(
                latitude=32.08,
                longitude=34.78,
                tilt=35.0,  # Different tilt
                panel_area=80.0,
                panel_efficiency=0.20,
                cleanliness="normal",
                shading="low",
                ac_capacity_kw=15.0,
                gamma=0.004,
                noct=45.0
            ),
            BasePVRequest(
                latitude=32.08,
                longitude=34.78,
                tilt=30.0,
                panel_area=100.0,  # Larger area
                panel_efficiency=0.20,
                cleanliness="normal",
                shading="low",
                ac_capacity_kw=15.0,
                gamma=0.004,
                noct=45.0
            ),
            BasePVRequest(
                latitude=32.08,
                longitude=34.78,
                tilt=30.0,
                panel_area=80.0,
                panel_efficiency=0.22,  # Higher efficiency
                cleanliness="clean",  # Better cleanliness
                shading="none",  # No shading
                ac_capacity_kw=15.0,
                gamma=0.004,
                noct=45.0
            ),
        ]

    @patch('app.services.scenario_comparison_service.get_year_archive')
    @patch('app.services.scenario_comparison_service.compute_system_loss_factor')
    @patch('app.services.scenario_comparison_service.compute_yearly_from_real_data')
    @patch('app.services.scenario_comparison_service.pd.Timestamp')
    def test_compare_single_scenario(
        self,
        mock_timestamp,
        mock_forecast,
        mock_loss_factor,
        mock_archive,
        mock_weather_data,
        base_scenario
    ):
        """Test comparison with a single scenario."""
        # Setup mocks
        mock_timestamp.now.return_value.year = 2025
        mock_archive.return_value = mock_weather_data
        mock_loss_factor.return_value = 0.85
        mock_forecast.return_value = {
            'yearly_kwh': 7000.0,
            'monthly_kwh': [583.33] * 12
        }

        # Execute
        result = compare_yearly_scenarios(32.08, 34.78, [base_scenario])

        # Verify
        assert 'year' in result
        assert 'baseline_yearly_kwh' in result
        assert 'results' in result
        assert result['year'] == 2024  # 2025 - 1
        assert result['baseline_yearly_kwh'] == 7000.0
        assert len(result['results']) == 1
        assert result['results'][0]['yearly_kwh'] == 7000.0
        assert result['results'][0]['deviation_percent'] == 0.0  # Baseline has 0% deviation

        # Verify archive called once
        mock_archive.assert_called_once_with(32.08, 34.78, 2024)

    @patch('app.services.scenario_comparison_service.get_year_archive')
    @patch('app.services.scenario_comparison_service.compute_system_loss_factor')
    @patch('app.services.scenario_comparison_service.compute_yearly_from_real_data')
    @patch('app.services.scenario_comparison_service.pd.Timestamp')
    def test_compare_multiple_scenarios(
        self,
        mock_timestamp,
        mock_forecast,
        mock_loss_factor,
        mock_archive,
        mock_weather_data,
        base_scenario,
        alternative_scenarios
    ):
        """Test comparison with multiple scenarios."""
        mock_timestamp.now.return_value.year = 2025
        mock_archive.return_value = mock_weather_data
        mock_loss_factor.return_value = 0.85
        
        # Set up different forecasts for each scenario
        forecasts = [7000.0, 7350.0, 8750.0, 8400.0]  # Base + 3 alternatives
        mock_forecast.side_effect = [
            {'yearly_kwh': kwh, 'monthly_kwh': [kwh/12] * 12}
            for kwh in forecasts
        ]

        scenarios = [base_scenario] + alternative_scenarios

        # Execute
        result = compare_yearly_scenarios(32.08, 34.78, scenarios)

        # Verify
        assert len(result['results']) == 4
        assert result['baseline_yearly_kwh'] == 7000.0
        
        # Check deviations
        assert result['results'][0]['deviation_percent'] == 0.0  # Baseline
        assert result['results'][1]['deviation_percent'] == pytest.approx(5.0, rel=1e-2)  # (7350-7000)/7000*100
        assert result['results'][2]['deviation_percent'] == pytest.approx(25.0, rel=1e-2)  # (8750-7000)/7000*100
        assert result['results'][3]['deviation_percent'] == pytest.approx(20.0, rel=1e-2)  # (8400-7000)/7000*100

        # Archive should be called only once
        mock_archive.assert_called_once()

    @patch('app.services.scenario_comparison_service.get_year_archive')
    @patch('app.services.scenario_comparison_service.compute_system_loss_factor')
    @patch('app.services.scenario_comparison_service.compute_yearly_from_real_data')
    @patch('app.services.scenario_comparison_service.pd.Timestamp')
    def test_compare_negative_deviation(
        self,
        mock_timestamp,
        mock_forecast,
        mock_loss_factor,
        mock_archive,
        mock_weather_data,
        base_scenario
    ):
        """Test comparison with scenarios that perform worse than baseline."""
        mock_timestamp.now.return_value.year = 2025
        mock_archive.return_value = mock_weather_data
        mock_loss_factor.return_value = 0.85
        
        # Set up forecasts where second scenario is worse
        forecasts = [7000.0, 6300.0]  # Second is -10%
        mock_forecast.side_effect = [
            {'yearly_kwh': kwh, 'monthly_kwh': [kwh/12] * 12}
            for kwh in forecasts
        ]

        worse_scenario = BasePVRequest(
            latitude=32.08,
            longitude=34.78,
            tilt=30.0,
            panel_area=60.0,  # Smaller area
            panel_efficiency=0.20,
            cleanliness="dusty",
            shading="high",
            ac_capacity_kw=15.0,
            gamma=0.004,
            noct=45.0
        )

        # Execute
        result = compare_yearly_scenarios(32.08, 34.78, [base_scenario, worse_scenario])

        # Verify negative deviation
        assert result['results'][1]['deviation_percent'] == pytest.approx(-10.0, rel=1e-2)

    @patch('app.services.scenario_comparison_service.get_year_archive')
    @patch('app.services.scenario_comparison_service.compute_system_loss_factor')
    @patch('app.services.scenario_comparison_service.compute_yearly_from_real_data')
    @patch('app.services.scenario_comparison_service.pd.Timestamp')
    def test_compare_uses_previous_year(
        self,
        mock_timestamp,
        mock_forecast,
        mock_loss_factor,
        mock_archive,
        mock_weather_data,
        base_scenario
    ):
        """Test that comparison uses previous year (current year - 1)."""
        mock_timestamp.now.return_value.year = 2026
        mock_archive.return_value = mock_weather_data
        mock_loss_factor.return_value = 0.85
        mock_forecast.return_value = {
            'yearly_kwh': 7000.0,
            'monthly_kwh': [583.33] * 12
        }

        # Execute
        result = compare_yearly_scenarios(32.08, 34.78, [base_scenario])

        # Verify year is previous year
        assert result['year'] == 2025
        mock_archive.assert_called_once_with(32.08, 34.78, 2025)

    @patch('app.services.scenario_comparison_service.get_year_archive')
    @patch('app.services.scenario_comparison_service.compute_system_loss_factor')
    @patch('app.services.scenario_comparison_service.compute_yearly_from_real_data')
    @patch('app.services.scenario_comparison_service.pd.Timestamp')
    def test_compare_different_system_losses(
        self,
        mock_timestamp,
        mock_forecast,
        mock_loss_factor,
        mock_archive,
        mock_weather_data,
        base_scenario
    ):
        """Test that different scenarios use different system loss factors."""
        mock_timestamp.now.return_value.year = 2025
        mock_archive.return_value = mock_weather_data
        
        # Different loss factors for different scenarios
        loss_factors = [0.85, 0.92]
        mock_loss_factor.side_effect = loss_factors
        
        mock_forecast.return_value = {
            'yearly_kwh': 7000.0,
            'monthly_kwh': [583.33] * 12
        }

        clean_scenario = BasePVRequest(
            latitude=32.08,
            longitude=34.78,
            tilt=30.0,
            panel_area=80.0,
            panel_efficiency=0.20,
            cleanliness="clean",
            shading="none",
            ac_capacity_kw=15.0,
            gamma=0.004,
            noct=45.0
        )

        # Execute
        compare_yearly_scenarios(32.08, 34.78, [base_scenario, clean_scenario])

        # Verify loss factor was called twice with different parameters
        assert mock_loss_factor.call_count == 2
        mock_loss_factor.assert_any_call(cleanliness="normal", shading="low")
        mock_loss_factor.assert_any_call(cleanliness="clean", shading="none")

    @patch('app.services.scenario_comparison_service.get_year_archive')
    @patch('app.services.scenario_comparison_service.compute_system_loss_factor')
    @patch('app.services.scenario_comparison_service.compute_yearly_from_real_data')
    @patch('app.services.scenario_comparison_service.pd.Timestamp')
    def test_compare_each_scenario_gets_copy_of_dataframe(
        self,
        mock_timestamp,
        mock_forecast,
        mock_loss_factor,
        mock_archive,
        mock_weather_data,
        base_scenario,
        alternative_scenarios
    ):
        """Test that each scenario gets a copy of the weather data."""
        mock_timestamp.now.return_value.year = 2025
        mock_archive.return_value = mock_weather_data
        mock_loss_factor.return_value = 0.85
        mock_forecast.return_value = {
            'yearly_kwh': 7000.0,
            'monthly_kwh': [583.33] * 12
        }

        scenarios = [base_scenario] + alternative_scenarios

        # Execute
        compare_yearly_scenarios(32.08, 34.78, scenarios)

        # Verify compute_yearly_from_real_data was called for each scenario
        assert mock_forecast.call_count == 4
        
        # Each call should have df as a parameter
        for call in mock_forecast.call_args_list:
            assert 'df' in call[1]

    @patch('app.services.scenario_comparison_service.get_year_archive')
    @patch('app.services.scenario_comparison_service.compute_system_loss_factor')
    @patch('app.services.scenario_comparison_service.compute_yearly_from_real_data')
    @patch('app.services.scenario_comparison_service.pd.Timestamp')
    def test_compare_includes_scenario_in_results(
        self,
        mock_timestamp,
        mock_forecast,
        mock_loss_factor,
        mock_archive,
        mock_weather_data,
        base_scenario
    ):
        """Test that results include the scenario object."""
        mock_timestamp.now.return_value.year = 2025
        mock_archive.return_value = mock_weather_data
        mock_loss_factor.return_value = 0.85
        mock_forecast.return_value = {
            'yearly_kwh': 7000.0,
            'monthly_kwh': [583.33] * 12
        }

        # Execute
        result = compare_yearly_scenarios(32.08, 34.78, [base_scenario])

        # Verify scenario is in results
        assert 'scenario' in result['results'][0]
        assert result['results'][0]['scenario'] == base_scenario

    @patch('app.services.scenario_comparison_service.get_year_archive')
    @patch('app.services.scenario_comparison_service.compute_system_loss_factor')
    @patch('app.services.scenario_comparison_service.compute_yearly_from_real_data')
    @patch('app.services.scenario_comparison_service.pd.Timestamp')
    def test_compare_includes_monthly_data(
        self,
        mock_timestamp,
        mock_forecast,
        mock_loss_factor,
        mock_archive,
        mock_weather_data,
        base_scenario
    ):
        """Test that results include monthly kWh data."""
        mock_timestamp.now.return_value.year = 2025
        mock_archive.return_value = mock_weather_data
        mock_loss_factor.return_value = 0.85
        
        monthly_data = [500, 520, 600, 650, 700, 720, 750, 740, 680, 620, 550, 510]
        mock_forecast.return_value = {
            'yearly_kwh': sum(monthly_data),
            'monthly_kwh': monthly_data
        }

        # Execute
        result = compare_yearly_scenarios(32.08, 34.78, [base_scenario])

        # Verify monthly data is in results
        assert 'monthly_kwh' in result['results'][0]
        assert result['results'][0]['monthly_kwh'] == monthly_data

    @patch('app.services.scenario_comparison_service.get_year_archive')
    @patch('app.services.scenario_comparison_service.compute_system_loss_factor')
    @patch('app.services.scenario_comparison_service.compute_yearly_from_real_data')
    @patch('app.services.scenario_comparison_service.pd.Timestamp')
    def test_compare_deviation_rounding(
        self,
        mock_timestamp,
        mock_forecast,
        mock_loss_factor,
        mock_archive,
        mock_weather_data,
        base_scenario
    ):
        """Test that deviation percentage is rounded to 2 decimal places."""
        mock_timestamp.now.return_value.year = 2025
        mock_archive.return_value = mock_weather_data
        mock_loss_factor.return_value = 0.85
        
        # Set up values that will produce non-round deviation
        forecasts = [7000.0, 7123.456]  # Deviation = 1.763371...%
        mock_forecast.side_effect = [
            {'yearly_kwh': kwh, 'monthly_kwh': [kwh/12] * 12}
            for kwh in forecasts
        ]

        scenario2 = BasePVRequest(
            latitude=32.08,
            longitude=34.78,
            tilt=32.0,
            panel_area=80.0,
            panel_efficiency=0.20,
            cleanliness="normal",
            shading="low",
            ac_capacity_kw=15.0,
            gamma=0.004,
            noct=45.0
        )

        # Execute
        result = compare_yearly_scenarios(32.08, 34.78, [base_scenario, scenario2])

        # Verify rounding
        deviation = result['results'][1]['deviation_percent']
        str_deviation = str(deviation)
        if '.' in str_deviation:
            decimal_places = len(str_deviation.split('.')[1])
            assert decimal_places <= 2

    @patch('app.services.scenario_comparison_service.get_year_archive')
    def test_compare_archive_failure(
        self,
        mock_archive,
        base_scenario
    ):
        """Test handling of archive service failure."""
        mock_archive.side_effect = Exception("API Error")

        with pytest.raises(Exception):
            compare_yearly_scenarios(32.08, 34.78, [base_scenario])

    @patch('app.services.scenario_comparison_service.get_year_archive')
    @patch('app.services.scenario_comparison_service.compute_system_loss_factor')
    @patch('app.services.scenario_comparison_service.compute_yearly_from_real_data')
    @patch('app.services.scenario_comparison_service.pd.Timestamp')
    def test_compare_empty_scenarios_list(
        self,
        mock_timestamp,
        mock_forecast,
        mock_loss_factor,
        mock_archive,
        mock_weather_data
    ):
        """Test handling of empty scenarios list."""
        mock_timestamp.now.return_value.year = 2025
        mock_archive.return_value = mock_weather_data
        mock_loss_factor.return_value = 0.85
        mock_forecast.return_value = {
            'yearly_kwh': 7000.0,
            'monthly_kwh': [583.33] * 12
        }

        # Execute with empty list should raise IndexError
        with pytest.raises(IndexError):
            compare_yearly_scenarios(32.08, 34.78, [])

    @patch('app.services.scenario_comparison_service.get_year_archive')
    @patch('app.services.scenario_comparison_service.compute_system_loss_factor')
    @patch('app.services.scenario_comparison_service.compute_yearly_from_real_data')
    @patch('app.services.scenario_comparison_service.pd.Timestamp')
    def test_compare_different_locations(
        self,
        mock_timestamp,
        mock_forecast,
        mock_loss_factor,
        mock_archive,
        mock_weather_data,
        base_scenario
    ):
        """Test scenario comparison for different locations."""
        mock_timestamp.now.return_value.year = 2025
        mock_archive.return_value = mock_weather_data
        mock_loss_factor.return_value = 0.85
        mock_forecast.return_value = {
            'yearly_kwh': 5000.0,  # Lower for different location
            'monthly_kwh': [416.67] * 12
        }

        # Different location (London)
        result = compare_yearly_scenarios(51.5074, -0.1278, [base_scenario])

        assert result is not None
        mock_archive.assert_called_with(51.5074, -0.1278, 2024)

    @patch('app.services.scenario_comparison_service.get_year_archive')
    @patch('app.services.scenario_comparison_service.compute_system_loss_factor')
    @patch('app.services.scenario_comparison_service.compute_yearly_from_real_data')
    @patch('app.services.scenario_comparison_service.pd.Timestamp')
    def test_compare_large_number_of_scenarios(
        self,
        mock_timestamp,
        mock_forecast,
        mock_loss_factor,
        mock_archive,
        mock_weather_data,
        base_scenario
    ):
        """Test comparison with a large number of scenarios."""
        mock_timestamp.now.return_value.year = 2025
        mock_archive.return_value = mock_weather_data
        mock_loss_factor.return_value = 0.85
        
        # Create many scenarios with different tilts
        num_scenarios = 20
        scenarios = [
            BasePVRequest(
                latitude=32.08,
                longitude=34.78,
                tilt=10.0 + i * 2,  # Different tilts from 10 to 48
                panel_area=80.0,
                panel_efficiency=0.20,
                cleanliness="normal",
                shading="low",
                ac_capacity_kw=15.0,
                gamma=0.004,
                noct=45.0
            )
            for i in range(num_scenarios)
        ]
        
        # Different outputs for each
        mock_forecast.side_effect = [
            {'yearly_kwh': 7000.0 + i * 100, 'monthly_kwh': [(7000.0 + i * 100)/12] * 12}
            for i in range(num_scenarios)
        ]

        # Execute
        result = compare_yearly_scenarios(32.08, 34.78, scenarios)

        # Verify all scenarios processed
        assert len(result['results']) == num_scenarios
        assert mock_forecast.call_count == num_scenarios
        
        # Archive should still be called only once
        mock_archive.assert_called_once()

    @patch('app.services.scenario_comparison_service.get_year_archive')
    @patch('app.services.scenario_comparison_service.compute_system_loss_factor')
    @patch('app.services.scenario_comparison_service.compute_yearly_from_real_data')
    @patch('app.services.scenario_comparison_service.pd.Timestamp')
    def test_compare_scenarios_with_different_parameters(
        self,
        mock_timestamp,
        mock_forecast,
        mock_loss_factor,
        mock_archive,
        mock_weather_data
    ):
        """Test scenarios with all different parameter variations."""
        mock_timestamp.now.return_value.year = 2025
        mock_archive.return_value = mock_weather_data
        mock_loss_factor.return_value = 0.85
        
        scenarios = [
            BasePVRequest(
                latitude=32.08, longitude=34.78,
                tilt=30.0, panel_area=80.0, panel_efficiency=0.20,
                cleanliness="normal", shading="low",
                ac_capacity_kw=15.0, gamma=0.004, noct=45.0
            ),
            BasePVRequest(
                latitude=32.08, longitude=34.78,
                tilt=35.0, panel_area=80.0, panel_efficiency=0.20,  # Different tilt
                cleanliness="normal", shading="low",
                ac_capacity_kw=15.0, gamma=0.004, noct=45.0
            ),
            BasePVRequest(
                latitude=32.08, longitude=34.78,
                tilt=30.0, panel_area=100.0, panel_efficiency=0.20,  # Different area
                cleanliness="normal", shading="low",
                ac_capacity_kw=15.0, gamma=0.004, noct=45.0
            ),
            BasePVRequest(
                latitude=32.08, longitude=34.78,
                tilt=30.0, panel_area=80.0, panel_efficiency=0.22,  # Different efficiency
                cleanliness="normal", shading="low",
                ac_capacity_kw=15.0, gamma=0.004, noct=45.0
            ),
            BasePVRequest(
                latitude=32.08, longitude=34.78,
                tilt=30.0, panel_area=80.0, panel_efficiency=0.20,
                cleanliness="clean", shading="low",  # Different cleanliness
                ac_capacity_kw=15.0, gamma=0.004, noct=45.0
            ),
            BasePVRequest(
                latitude=32.08, longitude=34.78,
                tilt=30.0, panel_area=80.0, panel_efficiency=0.20,
                cleanliness="normal", shading="none",  # Different shading
                ac_capacity_kw=15.0, gamma=0.004, noct=45.0
            ),
        ]
        
        mock_forecast.side_effect = [
            {'yearly_kwh': 7000.0 + i * 200, 'monthly_kwh': [(7000.0 + i * 200)/12] * 12}
            for i in range(len(scenarios))
        ]

        # Execute
        result = compare_yearly_scenarios(32.08, 34.78, scenarios)

        # Verify all processed
        assert len(result['results']) == 6
        assert all('deviation_percent' in r for r in result['results'])
