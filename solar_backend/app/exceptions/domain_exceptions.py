class DomainError(Exception):
    http_status_code = 400

    def __init__(self, user_message: str, detail: str | None = None) -> None:
        self.user_message = user_message
        self.detail = detail or user_message
        super().__init__(self.detail)


class EmptyScenarioComparisonError(DomainError, ValueError):
    def __init__(
        self,
        user_message: str = "At least one scenario is required",
        detail: str | None = None,
    ) -> None:
        super().__init__(user_message=user_message, detail=detail)


class InvalidWeatherProfileError(DomainError, ValueError):
    http_status_code = 502

    def __init__(
        self, user_message: str = "Weather data is not a valid hourly profile."
    ) -> None:
        super().__init__(user_message=user_message)
