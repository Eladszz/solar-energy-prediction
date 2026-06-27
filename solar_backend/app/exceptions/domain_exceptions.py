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


class ForecastTrainingDataUnavailableError(DomainError, ValueError):
    http_status_code = 502

    def __init__(
        self,
        user_message: str = "Cannot train ML forecast model without historical weather data",
        detail: str | None = None,
    ) -> None:
        super().__init__(user_message=user_message, detail=detail)


class BenchmarkTrainingDataUnavailableError(ForecastTrainingDataUnavailableError):
    def __init__(
        self,
        user_message: str = "No historical weather data was available for naive benchmark training",
        detail: str | None = None,
    ) -> None:
        super().__init__(user_message=user_message, detail=detail)
