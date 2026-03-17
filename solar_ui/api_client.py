from __future__ import annotations

from typing import Any

from loguru import logger
import requests
import streamlit as st  # type: ignore

try:
    from solar_ui.config import BACKEND_URL, REQUEST_TIMEOUT_SECONDS
except ModuleNotFoundError:
    from config import BACKEND_URL, REQUEST_TIMEOUT_SECONDS


def parse_api_error(response: requests.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        payload = {}
    return payload.get("detail") or response.text or "Unknown backend error"


def format_request_exception(exc: requests.RequestException) -> str:
    if isinstance(exc, requests.Timeout):
        return (
            "The backend request timed out. A weather or geocoding provider may be slow right now. "
            "Please try again."
        )
    if isinstance(exc, requests.ConnectionError):
        return (
            f"Could not reach the backend at {BACKEND_URL}. "
            "Make sure the FastAPI server is running and try again."
        )
    return f"Request to backend failed: {exc}"


def api_post(path: str, payload: Any) -> dict[str, Any] | None:
    try:
        response = requests.post(
            f"{BACKEND_URL}{path}",
            json=payload,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        logger.error("Frontend request to {} failed: {}", path, exc)
        st.error(format_request_exception(exc))
        return None

    if response.status_code != 200:
        error_message = parse_api_error(response)
        logger.error(
            "Backend request {} returned status {}: {}",
            path,
            response.status_code,
            error_message,
        )
        st.error(error_message)
        return None

    try:
        return response.json()
    except ValueError:
        logger.error("Backend response for {} was not valid JSON.", path)
        st.error("Backend response was not valid JSON.")
        return None
