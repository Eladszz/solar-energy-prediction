from unittest.mock import Mock

import pytest

pytest.importorskip("geopy")

from geopy.exc import GeocoderQuotaExceeded, GeocoderTimedOut, GeocoderUnavailable

from solar_ui.utils import geocode_address, reverse_geocode


def test_geocode_address_success(monkeypatch):
    mock_geolocator = Mock()
    mock_geolocator.geocode.return_value = Mock(
        latitude=32.0853,
        longitude=34.7818,
        address="Tel Aviv-Yafo, Israel",
    )
    monkeypatch.setattr(
        "solar_ui.utils.build_geolocator",
        lambda: mock_geolocator,
    )

    result = geocode_address("Tel Aviv")

    assert result.is_success is True
    assert result.latitude == 32.0853
    assert result.longitude == 34.7818
    assert result.address == "Tel Aviv-Yafo, Israel"
    assert result.error_message is None


def test_geocode_address_timeout_returns_user_friendly_error(monkeypatch):
    mock_geolocator = Mock()
    mock_geolocator.geocode.side_effect = GeocoderTimedOut("timed out")
    monkeypatch.setattr(
        "solar_ui.utils.build_geolocator",
        lambda: mock_geolocator,
    )

    result = geocode_address("Jerusalem")

    assert result.is_success is False
    assert result.error_message == "Address lookup timed out. Please try again."


def test_geocode_address_rate_limit_returns_user_friendly_error(monkeypatch):
    mock_geolocator = Mock()
    mock_geolocator.geocode.side_effect = GeocoderQuotaExceeded("quota exceeded")
    monkeypatch.setattr(
        "solar_ui.utils.build_geolocator",
        lambda: mock_geolocator,
    )

    result = geocode_address("Haifa")

    assert result.is_success is False
    assert (
        result.error_message
        == "Address lookup is temporarily rate limited. Please wait a minute and try again."
    )


def test_reverse_geocode_unavailable_preserves_coordinates(monkeypatch):
    mock_geolocator = Mock()
    mock_geolocator.reverse.side_effect = GeocoderUnavailable("service unavailable")
    monkeypatch.setattr(
        "solar_ui.utils.build_geolocator",
        lambda: mock_geolocator,
    )

    result = reverse_geocode(32.0853, 34.7818)

    assert result.is_success is True
    assert result.latitude == 32.0853
    assert result.longitude == 34.7818
    assert result.address is None
    assert (
        result.error_message
        == "Reverse geocoding is temporarily unavailable. Coordinates will be shown instead."
    )


def test_geocode_address_demo_mode_uses_bundled_scenario():
    result = geocode_address(
        "100 Dizengoff St, Tel Aviv-Yafo, Israel",
        demo_mode=True,
        demo_scenario_id="tel_aviv_rooftop",
    )

    assert result.is_success is True
    assert result.address == "100 Dizengoff St, Tel Aviv-Yafo, Israel"
    assert result.latitude == 32.0853
    assert result.longitude == 34.7818


def test_reverse_geocode_demo_mode_returns_scenario_address():
    result = reverse_geocode(
        33.4342,
        -112.0116,
        demo_mode=True,
        demo_scenario_id="phoenix_distribution_center",
    )

    assert result.is_success is True
    assert result.address == "3400 E Sky Harbor Blvd, Phoenix, Arizona, United States"
