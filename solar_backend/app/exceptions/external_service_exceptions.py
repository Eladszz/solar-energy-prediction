import requests


class ExternalServiceError(Exception):
    http_status_code = 502

    def __init__(
        self,
        provider: str,
        user_message: str,
        detail: str | None = None,
    ) -> None:
        self.provider = provider
        self.user_message = user_message
        self.detail = detail or user_message
        super().__init__(self.detail)


class ExternalServiceTimeoutError(ExternalServiceError, requests.exceptions.Timeout):
    http_status_code = 504


class ExternalServiceRateLimitError(
    ExternalServiceError,
    requests.exceptions.HTTPError,
):
    http_status_code = 503


class ExternalServiceUnavailableError(
    ExternalServiceError,
    requests.exceptions.RequestException,
):
    http_status_code = 503


class ExternalServiceResponseError(
    ExternalServiceError,
    requests.exceptions.HTTPError,
    ValueError,
):
    http_status_code = 502
