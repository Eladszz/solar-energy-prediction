import pytest
from app.services.loss_service import (
    get_cleanliness_loss,
    get_shading_loss,
    compute_system_loss_factor,
)


class TestGetCleanlinessLoss:
    """Test suite for cleanliness loss calculation."""

    def test_cleanliness_clean(self):
        """Test cleanliness loss for clean panels."""
        loss = get_cleanliness_loss("clean")
        assert loss == 0.02

    def test_cleanliness_normal(self):
        """Test cleanliness loss for normal panels."""
        loss = get_cleanliness_loss("normal")
        assert loss == 0.05

    def test_cleanliness_dusty(self):
        """Test cleanliness loss for dusty panels."""
        loss = get_cleanliness_loss("dusty")
        assert loss == 0.10

    def test_cleanliness_invalid_defaults_to_normal(self):
        """Test that invalid cleanliness level defaults to normal (0.05)."""
        loss = get_cleanliness_loss("invalid")
        assert loss == 0.05

    def test_cleanliness_empty_string(self):
        """Test that empty string defaults to normal."""
        loss = get_cleanliness_loss("")
        assert loss == 0.05

    def test_cleanliness_case_sensitive(self):
        """Test that cleanliness level is case sensitive."""
        loss = get_cleanliness_loss("Clean")  # Capital C
        assert loss == 0.05  # Should default to normal

    def test_cleanliness_none_defaults(self):
        """Test that None defaults to normal."""
        loss = get_cleanliness_loss("none")
        assert loss == 0.05

    def test_cleanliness_loss_range(self):
        """Test that all cleanliness losses are valid percentages."""
        valid_levels = ["clean", "normal", "dusty"]
        for level in valid_levels:
            loss = get_cleanliness_loss(level)
            assert 0.0 <= loss <= 1.0, f"Loss for {level} should be between 0 and 1"

    def test_cleanliness_loss_ordering(self):
        """Test that cleanliness losses are ordered correctly."""
        clean_loss = get_cleanliness_loss("clean")
        normal_loss = get_cleanliness_loss("normal")
        dusty_loss = get_cleanliness_loss("dusty")

        assert clean_loss < normal_loss < dusty_loss


class TestGetShadingLoss:
    """Test suite for shading loss calculation."""

    def test_shading_none(self):
        """Test shading loss for no shading."""
        loss = get_shading_loss("none")
        assert loss == 0.00

    def test_shading_low(self):
        """Test shading loss for low shading."""
        loss = get_shading_loss("low")
        assert loss == 0.03

    def test_shading_medium(self):
        """Test shading loss for medium shading."""
        loss = get_shading_loss("medium")
        assert loss == 0.07

    def test_shading_high(self):
        """Test shading loss for high shading."""
        loss = get_shading_loss("high")
        assert loss == 0.15

    def test_shading_invalid_defaults_to_low(self):
        """Test that invalid shading level defaults to low (0.03)."""
        loss = get_shading_loss("invalid")
        assert loss == 0.03

    def test_shading_empty_string(self):
        """Test that empty string defaults to low."""
        loss = get_shading_loss("")
        assert loss == 0.03

    def test_shading_case_sensitive(self):
        """Test that shading level is case sensitive."""
        loss = get_shading_loss("None")  # Capital N
        assert loss == 0.03  # Should default to low

    def test_shading_none_defaults(self):
        """Test that None defaults to low."""
        loss = get_shading_loss("none")
        assert loss == 0.00

    def test_shading_loss_range(self):
        """Test that all shading losses are valid percentages."""
        valid_levels = ["none", "low", "medium", "high"]
        for level in valid_levels:
            loss = get_shading_loss(level)
            assert 0.0 <= loss <= 1.0, f"Loss for {level} should be between 0 and 1"

    def test_shading_loss_ordering(self):
        """Test that shading losses are ordered correctly."""
        none_loss = get_shading_loss("none")
        low_loss = get_shading_loss("low")
        medium_loss = get_shading_loss("medium")
        high_loss = get_shading_loss("high")

        assert none_loss < low_loss < medium_loss < high_loss


class TestComputeSystemLossFactor:
    """Test suite for system loss factor computation."""

    def test_system_loss_clean_none(self):
        """Test system loss factor for clean panels with no shading."""
        factor = compute_system_loss_factor("clean", "none")
        # (1-0.02) * (1-0.00) * (1-0.02) * 0.96 = 0.98 * 1.0 * 0.98 * 0.96
        expected = 0.98 * 1.0 * 0.98 * 0.96
        assert pytest.approx(factor, rel=1e-6) == expected

    def test_system_loss_normal_low(self):
        """Test system loss factor for normal panels with low shading."""
        factor = compute_system_loss_factor("normal", "low")
        # (1-0.05) * (1-0.03) * (1-0.02) * 0.96 = 0.95 * 0.97 * 0.98 * 0.96
        expected = 0.95 * 0.97 * 0.98 * 0.96
        assert pytest.approx(factor, rel=1e-6) == expected

    def test_system_loss_dusty_high(self):
        """Test system loss factor for dusty panels with high shading."""
        factor = compute_system_loss_factor("dusty", "high")
        # (1-0.10) * (1-0.15) * (1-0.02) * 0.96 = 0.90 * 0.85 * 0.98 * 0.96
        expected = 0.90 * 0.85 * 0.98 * 0.96
        assert pytest.approx(factor, rel=1e-6) == expected

    def test_system_loss_best_case(self):
        """Test system loss factor for best case scenario."""
        factor = compute_system_loss_factor("clean", "none")
        # This should be the highest possible factor
        assert factor > 0.90

    def test_system_loss_worst_case(self):
        """Test system loss factor for worst case scenario."""
        factor = compute_system_loss_factor("dusty", "high")
        # This should be the lowest possible factor
        assert factor < 0.80

    def test_system_loss_factor_range(self):
        """Test that system loss factor is always between 0 and 1."""
        cleanliness_levels = ["clean", "normal", "dusty"]
        shading_levels = ["none", "low", "medium", "high"]

        for cleanliness in cleanliness_levels:
            for shading in shading_levels:
                factor = compute_system_loss_factor(cleanliness, shading)
                assert (
                    0.0 <= factor <= 1.0
                ), f"Factor for {cleanliness}/{shading} should be between 0 and 1"

    def test_system_loss_factor_decreases_with_cleanliness(self):
        """Test that system loss factor decreases as cleanliness worsens."""
        shading = "low"

        clean_factor = compute_system_loss_factor("clean", shading)
        normal_factor = compute_system_loss_factor("normal", shading)
        dusty_factor = compute_system_loss_factor("dusty", shading)

        assert clean_factor > normal_factor > dusty_factor

    def test_system_loss_factor_decreases_with_shading(self):
        """Test that system loss factor decreases as shading increases."""
        cleanliness = "normal"

        none_factor = compute_system_loss_factor(cleanliness, "none")
        low_factor = compute_system_loss_factor(cleanliness, "low")
        medium_factor = compute_system_loss_factor(cleanliness, "medium")
        high_factor = compute_system_loss_factor(cleanliness, "high")

        assert none_factor > low_factor > medium_factor > high_factor

    def test_system_loss_invalid_cleanliness(self):
        """Test system loss factor with invalid cleanliness (should use default)."""
        factor = compute_system_loss_factor("invalid", "low")
        expected_normal = compute_system_loss_factor("normal", "low")
        assert pytest.approx(factor, rel=1e-6) == expected_normal

    def test_system_loss_invalid_shading(self):
        """Test system loss factor with invalid shading (should use default)."""
        factor = compute_system_loss_factor("normal", "invalid")
        expected_low = compute_system_loss_factor("normal", "low")
        assert pytest.approx(factor, rel=1e-6) == expected_low

    def test_system_loss_both_invalid(self):
        """Test system loss factor with both parameters invalid."""
        factor = compute_system_loss_factor("invalid", "invalid")
        expected = compute_system_loss_factor("normal", "low")
        assert pytest.approx(factor, rel=1e-6) == expected

    def test_system_loss_wiring_loss_constant(self):
        """Test that wiring loss is constant at 2%."""
        # The wiring loss should be the same regardless of cleanliness/shading
        # We can verify this by checking that the ratio between different configs
        # matches the expected ratio without wiring loss

        factor1 = compute_system_loss_factor("clean", "none")
        factor2 = compute_system_loss_factor("normal", "none")

        # Both should include the same wiring loss (0.98) and inverter (0.96)
        # Ratio should be (0.98)/(0.95) for cleanliness difference only
        expected_ratio = 0.98 / 0.95
        actual_ratio = factor1 / factor2

        assert pytest.approx(actual_ratio, rel=1e-6) == expected_ratio

    def test_system_loss_inverter_efficiency_constant(self):
        """Test that inverter efficiency is constant at 96%."""
        # All factors should include 0.96 inverter efficiency
        factor = compute_system_loss_factor("clean", "none")

        # If we reverse calculate, we should get 0.96 as part of the factor
        # factor = 0.98 * 1.0 * 0.98 * 0.96
        # factor / (0.98 * 1.0 * 0.98) should equal 0.96
        inverter_component = factor / (0.98 * 1.0 * 0.98)
        assert pytest.approx(inverter_component, rel=1e-6) == 0.96

    def test_system_loss_all_combinations(self):
        """Test system loss factor for all valid combinations."""
        cleanliness_levels = ["clean", "normal", "dusty"]
        shading_levels = ["none", "low", "medium", "high"]

        results = {}
        for cleanliness in cleanliness_levels:
            for shading in shading_levels:
                factor = compute_system_loss_factor(cleanliness, shading)
                results[f"{cleanliness}_{shading}"] = factor

        # Verify all results are unique and reasonable
        assert len(set(results.values())) == len(
            results
        ), "All combinations should produce unique factors"
        assert all(
            0.6 <= f <= 1.0 for f in results.values()
        ), "All factors should be reasonable"

    def test_system_loss_factor_precision(self):
        """Test that system loss factor has reasonable precision."""
        factor = compute_system_loss_factor("normal", "low")

        # Should have at least 4 decimal places of precision
        factor_str = f"{factor:.10f}"
        assert len(factor_str.split(".")[1].rstrip("0")) >= 4

    def test_system_loss_empty_strings(self):
        """Test system loss factor with empty strings."""
        factor = compute_system_loss_factor("", "")
        # Should default to normal and low
        expected = compute_system_loss_factor("normal", "low")
        assert pytest.approx(factor, rel=1e-6) == expected

    def test_system_loss_mixed_case(self):
        """Test that parameters are case sensitive."""
        factor = compute_system_loss_factor("Clean", "Low")
        # Should default to normal and low
        expected = compute_system_loss_factor("normal", "low")
        assert pytest.approx(factor, rel=1e-6) == expected

    @pytest.mark.parametrize(
        "cleanliness,shading,min_expected,max_expected",
        [
            ("clean", "none", 0.920, 0.925),
            ("normal", "low", 0.860, 0.870),
            ("dusty", "medium", 0.760, 0.790),
            ("dusty", "high", 0.715, 0.725),
        ],
    )
    def test_system_loss_expected_ranges(
        self, cleanliness, shading, min_expected, max_expected
    ):
        """Test that system loss factors fall within expected ranges for specific configurations."""
        factor = compute_system_loss_factor(cleanliness, shading)
        assert (
            min_expected <= factor <= max_expected
        ), f"Factor {factor} for {cleanliness}/{shading} not in expected range [{min_expected}, {max_expected}]"

    def test_system_loss_multiplicative_nature(self):
        """Test that losses are multiplicative, not additive."""
        # If losses were additive, clean+none would be: 1 - (0.02 + 0.00 + 0.02 + 0.04) = 0.92
        # But they're multiplicative: 0.98 * 1.0 * 0.98 * 0.96 ≈ 0.922
        factor = compute_system_loss_factor("clean", "none")

        # Should NOT equal additive result
        additive_result = 1 - (0.02 + 0.00 + 0.02 + 0.04)
        assert factor != additive_result

        # Should equal multiplicative result
        multiplicative_result = 0.98 * 1.0 * 0.98 * 0.96
        assert pytest.approx(factor, rel=1e-6) == multiplicative_result
