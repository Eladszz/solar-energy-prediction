import math

import pandas as pd
import pytest

from app.exceptions.domain_exceptions import ForecastTrainingDataUnavailableError
from app.services.ml_forecast_service import (
    build_ml_metadata,
    build_hourly_time_index,
    predict_weather_profile,
    train_weather_regression_model,
)


def test_train_and_predict_weather_regression_model():
    timestamps = build_hourly_time_index(2024)
    history_df = pd.DataFrame(
        {
            "time": timestamps,
            "irr": [
                max(0.0, 650.0 * math.sin(((timestamp.hour - 6) / 12.0) * math.pi))
                for timestamp in timestamps
            ],
            "temp": [
                18.0
                + 8.0 * math.sin((timestamp.dayofyear / 365.25) * 2.0 * math.pi)
                for timestamp in timestamps
            ],
        }
    )

    model = train_weather_regression_model(history_df, training_years=[2024])
    predicted_df = predict_weather_profile(model, 2025)
    metadata = build_ml_metadata(model)

    assert len(predicted_df) == 8760
    assert set(predicted_df.columns) == {"time", "irr", "temp"}
    assert predicted_df["irr"].min() >= 0.0
    assert metadata["training_years"] == [2024]
    assert metadata["feature_count"] > 10


def test_train_weather_regression_model_rejects_empty_history():
    empty_history = pd.DataFrame(columns=["time", "irr", "temp"])

    with pytest.raises(
        ForecastTrainingDataUnavailableError,
        match="without historical weather data",
    ):
        train_weather_regression_model(empty_history, training_years=[])
