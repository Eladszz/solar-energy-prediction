import pytest
import math
from app.services.simulation_service import (
    calculate_power_kw,
    calculate_poa,
    calculate_cell_temp,
    calculate_dc_power_kw,
    apply_system_losses,
    apply_inverter_clipping,
    simulate_production_enhanced
)


class TestCalculatePowerKw:
    """Test suite for power calculation with thermal derating."""

    def test_calculate_power_basic(self):
        """Test basic power calculation."""
        # 1000 W/m², 25°C cell temp, 80m², 20% eff, 0.004 gamma
        power = calculate_power_kw(1000, 25, 80, 0.20, 0.004)
        # At STC temp (25°C), thermal_factor = 1.0
        # power = 1000 * 80 * 0.20 * 1.0 / 1000 = 16.0 kW
        assert pytest.approx(power, rel=1e-6) == 16.0

    def test_calculate_power_with_thermal_derating(self):
        """Test power calculation with temperature above STC."""
        # Cell temp 45°C (20°C above STC)
        power = calculate_power_kw(1000, 45, 80, 0.20, 0.004)
        # thermal_factor = 1 - 0.004 * (45 - 25) = 1 - 0.08 = 0.92
        # power = 1000 * 80 * 0.20 * 0.92 / 1000 = 14.72 kW
        assert pytest.approx(power, rel=1e-6) == 14.72

    def test_calculate_power_cold_temperature(self):
        """Test power calculation with temperature below STC."""
        # Cell temp 15°C (10°C below STC)
        power = calculate_power_kw(1000, 15, 80, 0.20, 0.004)
        # thermal_factor = 1 - 0.004 * (15 - 25) = 1 + 0.04 = 1.04
        # power = 1000 * 80 * 0.20 * 1.04 / 1000 = 16.64 kW
        assert pytest.approx(power, rel=1e-6) == 16.64

    def test_calculate_power_zero_irradiance(self):
        """Test power calculation with zero irradiance."""
        power = calculate_power_kw(0, 25, 80, 0.20, 0.004)
        assert power == 0.0

    def test_calculate_power_extreme_temperature(self):
        """Test that extreme temperature doesn't produce negative power."""
        # Very high temperature that would make thermal_factor negative
        power = calculate_power_kw(1000, 300, 80, 0.20, 0.004)
        # thermal_factor would be 1 - 0.004 * 275 = -0.1, but max(0, -0.1) = 0
        assert power == 0.0

    def test_calculate_power_different_panel_sizes(self):
        """Test power calculation with different panel areas."""
        power_small = calculate_power_kw(1000, 25, 40, 0.20, 0.004)
        power_large = calculate_power_kw(1000, 25, 120, 0.20, 0.004)
        
        assert pytest.approx(power_small, rel=1e-6) == 8.0
        assert pytest.approx(power_large, rel=1e-6) == 24.0
        assert power_large == 3 * power_small

    def test_calculate_power_different_efficiencies(self):
        """Test power calculation with different panel efficiencies."""
        power_standard = calculate_power_kw(1000, 25, 80, 0.20, 0.004)
        power_high = calculate_power_kw(1000, 25, 80, 0.22, 0.004)
        
        assert pytest.approx(power_standard, rel=1e-6) == 16.0
        assert pytest.approx(power_high, rel=1e-6) == 17.6
        assert power_high / power_standard == pytest.approx(1.1, rel=1e-6)


class TestCalculatePoa:
    """Test suite for plane-of-array irradiance calculation."""

    def test_calculate_poa_optimal_tilt(self):
        """Test POA when tilt equals latitude (optimal)."""
        ghi = 1000
        latitude = 32.0
        tilt = 32.0
        poa = calculate_poa(ghi, latitude, tilt)
        # angle_diff = 0, cos(0) = 1.0
        assert pytest.approx(poa, rel=1e-6) == 1000.0

    def test_calculate_poa_with_tilt_difference(self):
        """Test POA with difference between tilt and latitude."""
        ghi = 1000
        latitude = 32.0
        tilt = 42.0  # 10 degrees difference
        poa = calculate_poa(ghi, latitude, tilt)
        # angle_diff = 10, cos(10°) ≈ 0.9848
        expected = 1000 * math.cos(math.radians(10))
        assert pytest.approx(poa, rel=1e-3) == expected

    def test_calculate_poa_flat_panel(self):
        """Test POA with flat panel (0° tilt)."""
        ghi = 1000
        latitude = 32.0
        tilt = 0.0
        poa = calculate_poa(ghi, latitude, tilt)
        expected = 1000 * math.cos(math.radians(32))
        assert pytest.approx(poa, rel=1e-3) == expected

    def test_calculate_poa_zero_ghi(self):
        """Test POA with zero GHI."""
        poa = calculate_poa(0, 32.0, 30.0)
        assert poa == 0.0

    def test_calculate_poa_negative_result_protection(self):
        """Test that POA cannot be negative."""
        # Extreme case that might produce negative value
        poa = calculate_poa(1000, 0, 90)
        assert poa >= 0.0

    def test_calculate_poa_various_latitudes(self):
        """Test POA calculation at various latitudes."""
        ghi = 1000
        latitudes = [0, 20, 40, 60, 80]
        
        for lat in latitudes:
            poa = calculate_poa(ghi, lat, lat)  # Optimal tilt
            assert poa == pytest.approx(ghi, rel=1e-6)


class TestCalculateCellTemp:
    """Test suite for cell temperature calculation."""

    def test_calculate_cell_temp_noct_model(self):
        """Test cell temperature using NOCT model."""
        poa = 800
        ambient_temp = 20
        noct = 45
        
        t_cell = calculate_cell_temp(poa, ambient_temp, noct)
        # t_cell = 20 + (45 - 20) / 800 * 800 = 20 + 25 = 45°C
        assert pytest.approx(t_cell, rel=1e-6) == 45.0

    def test_calculate_cell_temp_zero_irradiance(self):
        """Test cell temperature with zero irradiance equals ambient."""
        t_cell = calculate_cell_temp(0, 25, 45)
        assert t_cell == 25.0

    def test_calculate_cell_temp_high_irradiance(self):
        """Test cell temperature with high irradiance."""
        poa = 1000
        ambient_temp = 30
        noct = 45
        
        t_cell = calculate_cell_temp(poa, ambient_temp, noct)
        # t_cell = 30 + (45 - 20) / 800 * 1000 = 30 + 31.25 = 61.25°C
        assert pytest.approx(t_cell, rel=1e-6) == 61.25

    def test_calculate_cell_temp_cold_ambient(self):
        """Test cell temperature with cold ambient temperature."""
        t_cell = calculate_cell_temp(800, 0, 45)
        # t_cell = 0 + (45 - 20) / 800 * 800 = 25°C
        assert pytest.approx(t_cell, rel=1e-6) == 25.0

    def test_calculate_cell_temp_different_noct(self):
        """Test cell temperature with different NOCT values."""
        poa = 800
        ambient = 25
        
        t_cell_low_noct = calculate_cell_temp(poa, ambient, 40)
        t_cell_high_noct = calculate_cell_temp(poa, ambient, 50)
        
        # Higher NOCT means more heating
        assert t_cell_high_noct > t_cell_low_noct


class TestCalculateDcPowerKw:
    """Test suite for DC power calculation."""

    def test_calculate_dc_power_at_stc(self):
        """Test DC power at standard test conditions."""
        poa = 1000
        t_cell = 25
        panel_area = 80
        efficiency = 0.20
        gamma = 0.004
        
        dc_kw = calculate_dc_power_kw(poa, t_cell, panel_area, efficiency, gamma)
        # thermal_factor = 1.0, dc = 1000 * 80 * 0.20 * 1.0 / 1000 = 16 kW
        assert pytest.approx(dc_kw, rel=1e-6) == 16.0

    def test_calculate_dc_power_with_derating(self):
        """Test DC power with thermal derating."""
        poa = 1000
        t_cell = 45  # 20°C above STC
        dc_kw = calculate_dc_power_kw(poa, t_cell, 80, 0.20, 0.004)
        # thermal_factor = 1 - 0.004 * 20 = 0.92
        assert pytest.approx(dc_kw, rel=1e-6) == 14.72

    def test_calculate_dc_power_zero_poa(self):
        """Test DC power with zero POA."""
        dc_kw = calculate_dc_power_kw(0, 25, 80, 0.20, 0.004)
        assert dc_kw == 0.0

    def test_calculate_dc_power_extreme_temp(self):
        """Test DC power doesn't go negative with extreme temperature."""
        dc_kw = calculate_dc_power_kw(1000, 300, 80, 0.20, 0.004)
        assert dc_kw == 0.0


class TestApplySystemLosses:
    """Test suite for system loss application."""

    def test_apply_system_losses_typical(self):
        """Test system losses with typical loss factor."""
        dc_kw = 16.0
        loss_factor = 0.85
        ac_kw = apply_system_losses(dc_kw, loss_factor)
        assert pytest.approx(ac_kw, rel=1e-6) == 13.6

    def test_apply_system_losses_no_losses(self):
        """Test system losses with no losses (factor = 1.0)."""
        dc_kw = 16.0
        ac_kw = apply_system_losses(dc_kw, 1.0)
        assert ac_kw == 16.0

    def test_apply_system_losses_high_losses(self):
        """Test system losses with high losses."""
        dc_kw = 16.0
        loss_factor = 0.70
        ac_kw = apply_system_losses(dc_kw, loss_factor)
        assert pytest.approx(ac_kw, rel=1e-6) == 11.2

    def test_apply_system_losses_zero_power(self):
        """Test system losses with zero power."""
        ac_kw = apply_system_losses(0.0, 0.85)
        assert ac_kw == 0.0

    def test_apply_system_losses_negative_protection(self):
        """Test that negative power is prevented."""
        # Shouldn't happen in practice, but test protection
        ac_kw = apply_system_losses(-5.0, 0.85)
        assert ac_kw == 0.0


class TestApplyInverterClipping:
    """Test suite for inverter clipping."""

    def test_apply_inverter_clipping_below_capacity(self):
        """Test inverter with power below capacity."""
        ac_kw = 12.0
        capacity = 15.0
        clipped = apply_inverter_clipping(ac_kw, capacity)
        assert clipped == 12.0

    def test_apply_inverter_clipping_above_capacity(self):
        """Test inverter clipping when power exceeds capacity."""
        ac_kw = 18.0
        capacity = 15.0
        clipped = apply_inverter_clipping(ac_kw, capacity)
        assert clipped == 15.0

    def test_apply_inverter_clipping_at_capacity(self):
        """Test inverter at exact capacity."""
        ac_kw = 15.0
        capacity = 15.0
        clipped = apply_inverter_clipping(ac_kw, capacity)
        assert clipped == 15.0

    def test_apply_inverter_clipping_no_limit(self):
        """Test inverter with no capacity limit (None)."""
        ac_kw = 20.0
        clipped = apply_inverter_clipping(ac_kw, None)
        assert clipped == 20.0

    def test_apply_inverter_clipping_zero_capacity(self):
        """Test inverter with zero capacity returns unclipped."""
        ac_kw = 15.0
        clipped = apply_inverter_clipping(ac_kw, 0)
        assert clipped == 15.0

    def test_apply_inverter_clipping_negative_capacity(self):
        """Test inverter with negative capacity returns unclipped."""
        ac_kw = 15.0
        clipped = apply_inverter_clipping(ac_kw, -5)
        assert clipped == 15.0


class TestSimulateProductionEnhanced:
    """Test suite for full enhanced simulation."""

    def test_simulate_production_basic(self):
        """Test basic simulation with constant conditions."""
        irradiance = [1000.0] * 24
        temp = [25.0] * 24
        
        results = simulate_production_enhanced(
            irradiance_list=irradiance,
            temp_list=temp,
            latitude=32.0,
            tilt=32.0,
            panel_area=80.0,
            efficiency=0.20,
            gamma=0.004,
            noct=45.0,
            system_loss_factor=0.85,
            ac_capacity_kw=15.0
        )
        
        assert len(results) == 24
        assert all(isinstance(r, (int, float)) for r in results)
        # All values should be consistent
        assert all(r == pytest.approx(results[0], rel=1e-6) for r in results)
        # Output should be positive
        assert results[0] > 0

    def test_simulate_production_nighttime(self):
        """Test simulation with nighttime hours (zero irradiance)."""
        # 24 hours: first 6 and last 6 are night
        irradiance = [0.0] * 6 + [800.0] * 12 + [0.0] * 6
        temp = [20.0] * 24
        
        results = simulate_production_enhanced(
            irradiance_list=irradiance,
            temp_list=temp,
            latitude=32.0,
            tilt=30.0,
            panel_area=80.0,
            efficiency=0.20,
            gamma=0.004,
            noct=45.0,
            system_loss_factor=0.85,
            ac_capacity_kw=None
        )
        
        # First 6 hours should be zero
        assert all(r == 0.0 for r in results[:6])
        # Last 6 hours should be zero
        assert all(r == 0.0 for r in results[18:])
        # Daytime hours should be positive
        assert all(r > 0.0 for r in results[6:18])

    def test_simulate_production_varying_irradiance(self):
        """Test simulation with varying irradiance throughout the day."""
        # Simulated bell curve of irradiance
        irradiance = [0.0, 0.0, 0.0, 0.0, 100.0, 300.0, 600.0, 800.0, 900.0, 1000.0, 1000.0, 900.0,
                     800.0, 600.0, 300.0, 100.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        temp = [20.0] * 24
        
        results = simulate_production_enhanced(
            irradiance_list=irradiance,
            temp_list=temp,
            latitude=32.0,
            tilt=32.0,
            panel_area=80.0,
            efficiency=0.20,
            gamma=0.004,
            noct=45.0,
            system_loss_factor=0.85,
            ac_capacity_kw=None
        )
        
        assert len(results) == 24
        # Peak hours should have highest production
        peak_hour = results[9]  # 1000 W/m²
        assert peak_hour == max(results)

    def test_simulate_production_no_clipping(self):
        """Test simulation without inverter clipping."""
        irradiance = [1000.0] * 24
        temp = [25.0] * 24
        
        results = simulate_production_enhanced(
            irradiance_list=irradiance,
            temp_list=temp,
            latitude=32.0,
            tilt=32.0,
            panel_area=80.0,
            efficiency=0.20,
            gamma=0.004,
            noct=45.0,
            system_loss_factor=0.85,
            ac_capacity_kw=None  # No clipping
        )
        
        # All values should be same without clipping
        assert all(r == pytest.approx(results[0], rel=1e-6) for r in results)
        # Should be positive and reasonable (POA calculation affects final output)
        assert results[0] > 10.0
        assert results[0] < 20.0
    def test_simulate_production_with_clipping(self):
        """Test simulation with inverter clipping active."""
        irradiance = [1000.0] * 24
        temp = [25.0] * 24
        
        results_no_clip = simulate_production_enhanced(
            irradiance_list=irradiance,
            temp_list=temp,
            latitude=32.0,
            tilt=32.0,
            panel_area=80.0,
            efficiency=0.20,
            gamma=0.004,
            noct=45.0,
            system_loss_factor=0.85,
            ac_capacity_kw=None
        )
        
        results_with_clip = simulate_production_enhanced(
            irradiance_list=irradiance,
            temp_list=temp,
            latitude=32.0,
            tilt=32.0,
            panel_area=80.0,
            efficiency=0.20,
            gamma=0.004,
            noct=45.0,
            system_loss_factor=0.85,
            ac_capacity_kw=12.0  # Lower than unclipped output
        )
        
        # Clipped values should be lower
        assert all(c <= u for c, u in zip(results_with_clip, results_no_clip))
        # All clipped values should be at capacity
        assert all(r == pytest.approx(12.0, rel=1e-2) for r in results_with_clip)
    def test_simulate_production_temperature_effect(self):
        """Test that higher temperature reduces output."""
        irradiance = [1000.0] * 24
        temp_cool = [15.0] * 24
        temp_hot = [45.0] * 24
        
        results_cool = simulate_production_enhanced(
            irradiance_list=irradiance,
            temp_list=temp_cool,
            latitude=32.0,
            tilt=32.0,
            panel_area=80.0,
            efficiency=0.20,
            gamma=0.004,
            noct=45.0,
            system_loss_factor=0.85,
            ac_capacity_kw=None
        )
        
        results_hot = simulate_production_enhanced(
            irradiance_list=irradiance,
            temp_list=temp_hot,
            latitude=32.0,
            tilt=32.0,
            panel_area=80.0,
            efficiency=0.20,
            gamma=0.004,
            noct=45.0,
            system_loss_factor=0.85,
            ac_capacity_kw=None
        )
        
        # Cool temperature should produce more power
        assert sum(results_cool) > sum(results_hot)

    def test_simulate_production_empty_lists(self):
        """Test simulation with empty input lists."""
        results = simulate_production_enhanced(
            irradiance_list=[],
            temp_list=[],
            latitude=32.0,
            tilt=32.0,
            panel_area=80.0,
            efficiency=0.20,
            gamma=0.004,
            noct=45.0,
            system_loss_factor=0.85,
            ac_capacity_kw=15.0
        )
        
        assert results == []
    def test_simulate_production_single_hour(self):
        """Test simulation with single hour data."""
        results = simulate_production_enhanced(
            irradiance_list=[1000.0],
            temp_list=[25.0],
            latitude=32.0,
            tilt=32.0,
            panel_area=80.0,
            efficiency=0.20,
            gamma=0.004,
            noct=45.0,
            system_loss_factor=0.85,
            ac_capacity_kw=None
        )
        
        assert len(results) == 1
        assert results[0] > 0
    def test_simulate_production_different_system_losses(self):
        """Test that different system loss factors affect output."""
        irradiance = [1000.0] * 24
        temp = [25.0] * 24
        
        results_low_loss = simulate_production_enhanced(
            irradiance_list=irradiance,
            temp_list=temp,
            latitude=32.0,
            tilt=32.0,
            panel_area=80.0,
            efficiency=0.20,
            gamma=0.004,
            noct=45.0,
            system_loss_factor=0.90,  # Lower losses
            ac_capacity_kw=None
        )
        
        results_high_loss = simulate_production_enhanced(
            irradiance_list=irradiance,
            temp_list=temp,
            latitude=32.0,
            tilt=32.0,
            panel_area=80.0,
            efficiency=0.20,
            gamma=0.004,
            noct=45.0,
            system_loss_factor=0.75,  # Higher losses
            ac_capacity_kw=None
        )
        
        # Lower loss factor should produce more
        assert sum(results_low_loss) > sum(results_high_loss)

    def test_simulate_production_full_year(self):
        """Test simulation with full year of data (8760 hours)."""
        import numpy as np
        
        # Simple seasonal variation
        hours = 8760
        irradiance = list(np.random.uniform(0, 1000, hours))
        temp = list(np.random.uniform(10, 35, hours))
        
        results = simulate_production_enhanced(
            irradiance_list=irradiance,
            temp_list=temp,
            latitude=32.0,
            tilt=32.0,
            panel_area=80.0,
            efficiency=0.20,
            gamma=0.004,
            noct=45.0,
            system_loss_factor=0.85,
            ac_capacity_kw=15.0
        )
        
        assert len(results) == hours
        assert all(r >= 0 for r in results)
        assert all(r <= 15.0 for r in results)  # Clipped at capacity
