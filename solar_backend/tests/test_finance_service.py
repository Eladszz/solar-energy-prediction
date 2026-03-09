from app.services.finance_service import build_financial_summary, estimate_energy_value


def test_estimate_energy_value():
    assert estimate_energy_value(100.0, 0.2) == 20.0
    assert estimate_energy_value(-5.0, 0.2) == 0.0


def test_build_financial_summary():
    summary = build_financial_summary([100.0] * 12, 0.15, "USD")

    assert summary["monthly_estimated_value"] == [15.0] * 12
    assert summary["yearly_estimated_value"] == 180.0
    assert summary["avg_monthly_estimated_value"] == 15.0
    assert summary["financial_assumptions"]["currency"] == "USD"
