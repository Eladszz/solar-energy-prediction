from __future__ import annotations

import logging
from typing import Any, Callable

import requests

from app.exceptions.external_service_exceptions import (
    ExternalServiceError,  # noqa: F401
    ExternalServiceResponseError,
    ExternalServiceTimeoutError,
    ExternalServiceRateLimitError,
    ExternalServiceUnavailableError,
)

logger = logging.getLogger(__name__)

DEFAULT_EXTERNAL_TIMEOUT_SECONDS = 15


def fetch_json_from_provider(
    *,
    url: str,
    provider: str,
    timeout: int = DEFAULT_EXTERNAL_TIMEOUT_SECONDS,
    request_get: Callable[..., Any] = requests.get,
) -> dict[str, Any]:
    logger.info("Requesting %s from %s", provider, url)

    try:
        response = request_get(url, timeout=timeout)
    except requests.exceptions.Timeout as exc:
        raise ExternalServiceTimeoutError(
            provider=provider,
            user_message=f"{provider} timed out. Please try again in a moment.",
            detail=str(exc),
        ) from exc
    except requests.exceptions.ConnectionError as exc:
        raise ExternalServiceUnavailableError(
            provider=provider,
            user_message=f"{provider} is temporarily unavailable. Please try again shortly.",
            detail=str(exc),
        ) from exc
    except requests.exceptions.RequestException as exc:
        raise ExternalServiceUnavailableError(
            provider=provider,
            user_message=f"{provider} could not be reached. Please try again shortly.",
            detail=str(exc),
        ) from exc
    response_text = getattr(response, "text", "")
    response_snippet = response_text[:200] if isinstance(response_text, str) else ""

    if response.status_code == 429:
        raise ExternalServiceRateLimitError(
            provider=provider,
            user_message=f"{provider} is temporarily rate limited. Please retry in a minute.",
            detail=f"HTTP 429 from provider. {response_snippet}".strip(),
        )
    if response.status_code >= 500:
        raise ExternalServiceUnavailableError(
            provider=provider,
            user_message=f"{provider} is temporarily unavailable. Please try again shortly.",
            detail=f"HTTP {response.status_code} from provider. {response_snippet}".strip(),
        )
    if response.status_code >= 400:
        raise ExternalServiceResponseError(
            provider=provider,
            user_message=f"{provider} rejected the request. Verify the selected location and try again.",
            detail=f"HTTP {response.status_code} from provider. {response_snippet}".strip(),
        )

    try:
        payload = response.json()
    except (requests.exceptions.JSONDecodeError, ValueError) as exc:
        raise ExternalServiceResponseError(
            provider=provider,
            user_message=f"{provider} returned malformed data. Please try again shortly.",
            detail=str(exc),
        ) from exc

    if not isinstance(payload, dict):
        raise ExternalServiceResponseError(
            provider=provider,
            user_message=f"{provider} returned malformed data. Please try again shortly.",
            detail=f"Expected JSON object, received {type(payload).__name__}",
        )

    logger.info("Received %s data with status code %s", provider, response.status_code)
    return payload


def require_list_fields(
    *,
    container: dict[str, Any],
    fields: tuple[str, ...],
    provider: str,
    context: str,
) -> dict[str, list[Any]]:
    extracted: dict[str, list[Any]] = {}

    for field in fields:
        value = container.get(field)
        if not isinstance(value, list):
            raise ExternalServiceResponseError(
                provider=provider,
                user_message=f"{provider} returned malformed {context}. Please try again shortly.",
                detail=f"Expected list field '{field}' in {context}.",
            )
        extracted[field] = value

    lengths = {len(value) for value in extracted.values()}
    if len(lengths) != 1:
        raise ExternalServiceResponseError(
            provider=provider,
            user_message=f"{provider} returned inconsistent {context}. Please try again shortly.",
            detail=f"Mismatched list lengths in {context}: {sorted(lengths)}",
        )

    if not extracted[fields[0]]:
        raise ExternalServiceResponseError(
            provider=provider,
            user_message=f"{provider} returned empty {context}. Please try again shortly.",
            detail=f"Empty list for '{fields[0]}' in {context}.",
        )

    return extracted
