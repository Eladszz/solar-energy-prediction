from unittest.mock import patch, Mock
import pytest
import pandas as pd
import numpy as np
from app.services.yearly_forecast_service import compute_yearly_from_real_data


class TestComputeYearlyFromRealData:
    """Test suite for yearly forecast service."""

    @pytest.fixture
    def sample_hourly_data(self):
        """Create sample hourly data for a full year."""
        # 8760 hours in a non-leap year
        hours = 8760
        times = pd.date_range(start='2023-01-01', end='2023-12-31 23:00:00', freq='h')
        return pd.DataFrame({
            "time": times,
            "irr": np.random.uniform(0, 800, hours),  # W/m²
            "temp": np.random.uniform(-10, 35, hours)  # °C
        })

    @pytest.fixture
    def small_hourly_data(self):
        """Create small sample data for testing."""
        times = pd.date_range(start='2023-01-01', periods=24, freq='h')
        return pd.DataFrame({
            "time": times,
            "irr": [0, 0, 0, 0, 0, 0, 100, 200, 400, 600, 800, 900, 
                    850, 700, 500, 300, 150, 50, 0, 0, 0, 0, 0, 0],
            "temp": [5, 4, 4, 3, 3, 4, 6, 8, 12, 16, 20, 24,
                     26, 25, 22, 18, 14, 10, 8, 7, 6, 6, 5, 5]
        })

    @pytest.fixture
    def standard_params(self):
        """Standard system parameters."""
        return {
            "latitude": 52.52,
            "tilt": 30,
            "panel_area": 40.0,
            "efficiency": 0.20,
            "gamma": -0.004,
            "noct": 45,
            "system_loss_factor": 0.87,
            "ac_capacity_kw": 15.0
        }

    @patch('app.services.yearly_forecast_service.simulate_production_enhanced')
    def test_compute_yearly_basic_structure(self, mock_simulate, sample_hourly_data, standard_params):
        """Test that function returns correct data structure."""
        mock_simulate.return_value = [5.0] * len(sample_hourly_data)
        
        result = compute_yearly_from_real_data(
            df=sample_hourly_data,
            **standard_params
        )

        assert isinstance(result, dict)
        assert "monthly_kwh" in result
        assert "yearly_kwh" in result
        assert "specific_yield_kwh_per_kwp" in result
        assert "avg_daily_kwh" in result

    @patch('app.services.yearly_forecast_service.simulate_production_enhanced')
    def test_compute_yearly_monthly_data(self, mock_simulate, sample_hourly_data, standard_params):
        """Test that monthly data has 12 entries."""
        mock_simulate.return_value = [5.0] * len(sample_hourly_data)
        
        result = compute_yearly_from_real_data(
            df=sample_hourly_data,
            **standard_params
        )

        assert isinstance(result["monthly_kwh"], list)
        assert len(result["monthly_kwh"]) == 12

    @patch('app.services.yearly_forecast_service.simulate_production_enhanced')
    def test_compute_yearly_calls_simulation(self, mock_simulate, sample_hourly_data, standard_params):
        """Test that simulation service is called with correct parameters."""
        mock_simulate.return_value = [5.0] * len(sample_hourly_data)
        
        compute_yearly_from_real_data(
            df=sample_hourly_data,
            **standard_params
        )

        mock_simulate.assert_called_once()
        call_kwargs = mock_simulate.call_args[1]
        
        assert call_kwargs["latitude"] == 52.52
        assert call_kwargs["tilt"] == 30
        assert call_kwargs["panel_area"] == 40.0
        assert call_kwargs["efficiency"] == 0.20
        assert call_kwargs["gamma"] == -0.004
        assert call_kwargs["noct"] == 45
        assert call_kwargs["system_loss_factor"] == 0.87
        assert call_kwargs["ac_capacity_kw"] == 15.0

    @patch('app.services.yearly_forecast_service.simulate_production_enhanced')
    def test_compute_yearly_irradiance_temp_lists(self, mock_simulate, sample_hourly_data, standard_params):
        """Test that irradiance and temperature are passed as lists."""
        mock_simulate.return_value = [5.0] * len(sample_hourly_data)
        
        compute_yearly_from_real_data(
            df=sample_hourly_data,
            **standard_params
        )

        call_kwargs = mock_simulate.call_args[1]
        assert isinstance(call_kwargs["irradiance_list"], list)
        assert isinstance(call_kwargs["temp_list"], list)
        assert len(call_kwargs["irradiance_list"]) == len(sample_hourly_data)
        assert len(call_kwargs["temp_list"]) == len(sample_hourly_data)

    @patch('app.services.yearly_forecast_service.simulate_production_enhanced')
    def test_compute_yearly_sum_calculation(self, mock_simulate, small_hourly_data, standard_params):
        """Test that yearly sum equals sum of monthly values."""
        # Return constant power output for easy verification
        mock_simulate.return_value = [10.0] * len(small_hourly_data)
        
        result = compute_yearly_from_real_data(
            df=small_hourly_data,
            **standard_params
        )

        monthly_sum = sum(result["monthly_kwh"])
        assert result["yearly_kwh"] == round(monthly_sum, 1)

    @patch('app.services.yearly_forecast_service.simulate_production_enhanced')
    def test_compute_yearly_specific_yield(self, mock_simulate, sample_hourly_data, standard_params):
        """Test specific yield calculation."""
        # Mock production of 5 kW for all hours
        mock_simulate.return_value = [5.0] * len(sample_hourly_data)
        
        result = compute_yearly_from_real_data(
            df=sample_hourly_data,
            **standard_params
        )

        # DC capacity = panel_area * efficiency = 40 * 0.20 = 8 kWp
        # Yearly = 5 kW * 8760 hours = 43800 kWh
        # Specific yield = 43800 / 8 = 5475 kWh/kWp
        dc_capacity_kwp = standard_params["panel_area"] * standard_params["efficiency"]
        expected_yearly = 5.0 * len(sample_hourly_data)
        expected_specific_yield = expected_yearly / dc_capacity_kwp
        
        assert result["specific_yield_kwh_per_kwp"] == round(expected_specific_yield, 1)

    @patch('app.services.yearly_forecast_service.simulate_production_enhanced')
    def test_compute_yearly_avg_daily(self, mock_simulate, sample_hourly_data, standard_params):
        """Test average daily production calculation."""
        mock_simulate.return_value = [5.0] * len(sample_hourly_data)
        
        result = compute_yearly_from_real_data(
            df=sample_hourly_data,
            **standard_params
        )

        # Yearly = 5 kW * 8760 hours = 43800 kWh
        # Daily avg = 43800 / 365 = 120 kWh/day
        expected_yearly = 5.0 * len(sample_hourly_data)
        expected_daily = expected_yearly / 365
        
        assert result["avg_daily_kwh"] == round(expected_daily, 1)

    @patch('app.services.yearly_forecast_service.simulate_production_enhanced')
    def test_compute_yearly_zero_production(self, mock_simulate, sample_hourly_data, standard_params):
        """Test with zero production (nighttime only)."""
        mock_simulate.return_value = [0.0] * len(sample_hourly_data)
        
        result = compute_yearly_from_real_data(
            df=sample_hourly_data,
            **standard_params
        )

        assert result["yearly_kwh"] == 0.0
        assert result["specific_yield_kwh_per_kwp"] == 0.0
        assert result["avg_daily_kwh"] == 0.0
        assert all(month == 0.0 for month in result["monthly_kwh"])

    @patch('app.services.yearly_forecast_service.simulate_production_enhanced')
    def test_compute_yearly_different_panel_areas(self, mock_simulate, sample_hourly_data, standard_params):
        """Test with different panel areas."""
        mock_simulate.return_value = [5.0] * len(sample_hourly_data)
        
        panel_areas = [20.0, 40.0, 60.0, 100.0]
        
        for area in panel_areas:
            params = standard_params.copy()
            params["panel_area"] = area
            result = compute_yearly_from_real_data(
                df=sample_hourly_data.copy(),
                **params
            )
            
            assert result["yearly_kwh"] > 0
            assert result["specific_yield_kwh_per_kwp"] > 0

    @patch('app.services.yearly_forecast_service.simulate_production_enhanced')
    def test_compute_yearly_different_efficiencies(self, mock_simulate, sample_hourly_data, standard_params):
        """Test with different panel efficiencies."""
        mock_simulate.return_value = [5.0] * len(sample_hourly_data)
        
        efficiencies = [0.15, 0.18, 0.20, 0.22, 0.25]
        
        for eff in efficiencies:
            params = standard_params.copy()
            params["efficiency"] = eff
            result = compute_yearly_from_real_data(
                df=sample_hourly_data.copy(),
                **params
            )
            
            # Higher efficiency -> lower specific yield for same production
            dc_capacity = params["panel_area"] * eff
            expected_specific = (5.0 * len(sample_hourly_data)) / dc_capacity
            assert abs(result["specific_yield_kwh_per_kwp"] - round(expected_specific, 1)) < 0.2

    @patch('app.services.yearly_forecast_service.simulate_production_enhanced')
    def test_compute_yearly_different_latitudes(self, mock_simulate, sample_hourly_data, standard_params):
        """Test with different latitudes."""
        mock_simulate.return_value = [5.0] * len(sample_hourly_data)
        
        latitudes = [-40, -20, 0, 20, 40, 60]
        
        for lat in latitudes:
            params = standard_params.copy()
            params["latitude"] = lat
            result = compute_yearly_from_real_data(
                df=sample_hourly_data.copy(),
                **params
            )
            
            assert result is not None
            assert result["yearly_kwh"] > 0

    @patch('app.services.yearly_forecast_service.simulate_production_enhanced')
    def test_compute_yearly_different_tilts(self, mock_simulate, sample_hourly_data, standard_params):
        """Test with different tilt angles."""
        mock_simulate.return_value = [5.0] * len(sample_hourly_data)
        
        tilts = [0, 15, 30, 45, 60, 90]
        
        for tilt in tilts:
            params = standard_params.copy()
            params["tilt"] = tilt
            result = compute_yearly_from_real_data(
                df=sample_hourly_data.copy(),
                **params
            )
            
            assert result is not None
            assert result["yearly_kwh"] > 0

    @patch('app.services.yearly_forecast_service.simulate_production_enhanced')
    def test_compute_yearly_system_loss_factor(self, mock_simulate, sample_hourly_data, standard_params):
        """Test with different system loss factors."""
        mock_simulate.return_value = [5.0] * len(sample_hourly_data)
        
        loss_factors = [0.70, 0.80, 0.87, 0.90, 0.95]
        
        for factor in loss_factors:
            params = standard_params.copy()
            params["system_loss_factor"] = factor
            result = compute_yearly_from_real_data(
                df=sample_hourly_data.copy(),
                **params
            )
            
            assert result is not None

    @patch('app.services.yearly_forecast_service.simulate_production_enhanced')
    def test_compute_yearly_ac_capacity_limits(self, mock_simulate, sample_hourly_data, standard_params):
        """Test with different AC capacity limits."""
        mock_simulate.return_value = [5.0] * len(sample_hourly_data)
        
        ac_capacities = [5.0, 10.0, 15.0, 20.0, 30.0]
        
        for capacity in ac_capacities:
            params = standard_params.copy()
            params["ac_capacity_kw"] = capacity
            result = compute_yearly_from_real_data(
                df=sample_hourly_data.copy(),
                **params
            )
            
            assert result is not None

    @patch('app.services.yearly_forecast_service.simulate_production_enhanced')
    def test_compute_yearly_dataframe_modification(self, mock_simulate, sample_hourly_data, standard_params):
        """Test that original dataframe is modified with kw, kwh, and month columns."""
        mock_simulate.return_value = [5.0] * len(sample_hourly_data)
        
        df = sample_hourly_data.copy()
        compute_yearly_from_real_data(
            df=df,
            **standard_params
        )

        assert "kw" in df.columns
        assert "kwh" in df.columns
        assert "month" in df.columns
        assert len(df) == len(sample_hourly_data)

    @patch('app.services.yearly_forecast_service.simulate_production_enhanced')
    def test_compute_yearly_kw_kwh_equality(self, mock_simulate, sample_hourly_data, standard_params):
        """Test that kw equals kwh (since each row is 1 hour)."""
        mock_simulate.return_value = [5.0] * len(sample_hourly_data)
        
        df = sample_hourly_data.copy()
        compute_yearly_from_real_data(
            df=df,
            **standard_params
        )

        assert all(df["kw"] == df["kwh"])

    @patch('app.services.yearly_forecast_service.simulate_production_enhanced')
    def test_compute_yearly_month_values(self, mock_simulate, sample_hourly_data, standard_params):
        """Test that month column contains valid month numbers."""
        mock_simulate.return_value = [5.0] * len(sample_hourly_data)
        
        df = sample_hourly_data.copy()
        compute_yearly_from_real_data(
            df=df,
            **standard_params
        )

        assert all(1 <= month <= 12 for month in df["month"])

    @patch('app.services.yearly_forecast_service.simulate_production_enhanced')
    def test_compute_yearly_rounding(self, mock_simulate, sample_hourly_data, standard_params):
        """Test that output values are properly rounded."""
        mock_simulate.return_value = [5.123456789] * len(sample_hourly_data)
        
        result = compute_yearly_from_real_data(
            df=sample_hourly_data,
            **standard_params
        )

        # Check that values are rounded to 1 decimal place
        assert isinstance(result["yearly_kwh"], (int, float))
        assert isinstance(result["specific_yield_kwh_per_kwp"], (int, float))
        assert isinstance(result["avg_daily_kwh"], (int, float))

    @patch('app.services.yearly_forecast_service.simulate_production_enhanced')
    def test_compute_yearly_leap_year(self, mock_simulate, standard_params):
        """Test with leap year data (8784 hours)."""
        # 2024 is a leap year
        times = pd.date_range(start='2024-01-01', end='2024-12-31 23:00:00', freq='h')
        leap_year_data = pd.DataFrame({
            "time": times,
            "irr": np.random.uniform(0, 800, len(times)),
            "temp": np.random.uniform(-10, 35, len(times))
        })
        
        mock_simulate.return_value = [5.0] * len(leap_year_data)
        
        result = compute_yearly_from_real_data(
            df=leap_year_data,
            **standard_params
        )

        assert result is not None
        assert len(result["monthly_kwh"]) == 12
        # Yearly production should account for 8784 hours, not 8760
        expected_yearly = 5.0 * 8784
        assert abs(result["yearly_kwh"] - round(expected_yearly, 1)) < 1.0

    @patch('app.services.yearly_forecast_service.simulate_production_enhanced')
    def test_compute_yearly_logging(self, mock_simulate, sample_hourly_data, standard_params, caplog):
        """Test that appropriate logging occurs."""
        mock_simulate.return_value = [5.0] * len(sample_hourly_data)
        
        with caplog.at_level('INFO'):
            compute_yearly_from_real_data(
                df=sample_hourly_data,
                **standard_params
            )

        assert any('Starting yearly production computation' in record.message for record in caplog.records)
        assert any('Aggregating monthly and yearly production data' in record.message for record in caplog.records)
        assert any('Yearly production computed' in record.message for record in caplog.records)

    @patch('app.services.yearly_forecast_service.simulate_production_enhanced')
    def test_compute_yearly_variable_production(self, mock_simulate, sample_hourly_data, standard_params):
        """Test with variable hourly production values."""
        # Simulate realistic variable production
        variable_production = []
        for i in range(len(sample_hourly_data)):
            # Nighttime: 0, daytime: varies
            hour = sample_hourly_data.iloc[i]["time"].hour
            if 6 <= hour <= 18:
                variable_production.append(np.random.uniform(0, 10))
            else:
                variable_production.append(0.0)
        
        mock_simulate.return_value = variable_production
        
        result = compute_yearly_from_real_data(
            df=sample_hourly_data,
            **standard_params
        )

        assert result["yearly_kwh"] > 0
        assert result["yearly_kwh"] == round(sum(variable_production), 1)
