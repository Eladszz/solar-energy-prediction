from __future__ import annotations

from dataclasses import dataclass
import logging
import math
from typing import Sequence

import numpy as np
import pandas as pd


logger = logging.getLogger(__name__)


@dataclass
class RegressionMetrics:
    mae: float
    rmse: float
    r2: float


@dataclass
class WeatherRegressionModel:
    irradiance_coefficients: np.ndarray
    temperature_coefficients: np.ndarray
    irradiance_metrics: RegressionMetrics
    temperature_metrics: RegressionMetrics
    training_years: list[int]
    feature_names: list[str]


def build_hourly_time_index(year: int) -> pd.DatetimeIndex:
    return pd.date_range(
        start=f"{year}-01-01 00:00:00",
        end=f"{year}-12-31 23:00:00",
        freq="h",
    )


def build_time_features(timestamps: Sequence[pd.Timestamp]) -> tuple[np.ndarray, list[str]]:
    time_series = pd.Series(pd.to_datetime(list(timestamps)))
    hour = time_series.dt.hour.to_numpy(dtype=float)
    day_of_year = time_series.dt.dayofyear.to_numpy(dtype=float)
    month = time_series.dt.month.to_numpy(dtype=int)
    year = time_series.dt.year.to_numpy(dtype=float)
    daylight_proxy = np.clip(np.cos((hour - 12.0) * math.pi / 12.0), 0.0, None)

    features = [
        np.ones(len(time_series), dtype=float),
        np.sin(2.0 * math.pi * hour / 24.0),
        np.cos(2.0 * math.pi * hour / 24.0),
        np.sin(4.0 * math.pi * hour / 24.0),
        np.cos(4.0 * math.pi * hour / 24.0),
        np.sin(2.0 * math.pi * day_of_year / 365.25),
        np.cos(2.0 * math.pi * day_of_year / 365.25),
        np.sin(4.0 * math.pi * day_of_year / 365.25),
        np.cos(4.0 * math.pi * day_of_year / 365.25),
        daylight_proxy,
        year - year.min(),
    ]
    feature_names = [
        "bias",
        "hour_sin_1",
        "hour_cos_1",
        "hour_sin_2",
        "hour_cos_2",
        "day_sin_1",
        "day_cos_1",
        "day_sin_2",
        "day_cos_2",
        "daylight_proxy",
        "year_trend",
    ]

    for month_number in range(1, 13):
        features.append((month == month_number).astype(float))
        feature_names.append(f"month_{month_number:02d}")

    return np.column_stack(features), feature_names


def calculate_regression_metrics(
    actual: np.ndarray,
    predicted: np.ndarray,
) -> RegressionMetrics:
    residuals = actual - predicted
    mae = float(np.mean(np.abs(residuals)))
    rmse = float(np.sqrt(np.mean(np.square(residuals))))
    total_variance = float(np.sum(np.square(actual - np.mean(actual))))
    if total_variance == 0.0:
        r2 = 1.0
    else:
        r2 = float(1.0 - (np.sum(np.square(residuals)) / total_variance))
    return RegressionMetrics(
        mae=round(mae, 3),
        rmse=round(rmse, 3),
        r2=round(r2, 4),
    )


def fit_ridge_regression(
    design_matrix: np.ndarray,
    target: np.ndarray,
    alpha: float = 1.0,
) -> np.ndarray:
    penalty = np.eye(design_matrix.shape[1], dtype=float) * alpha
    penalty[0, 0] = 0.0
    left = design_matrix.T @ design_matrix + penalty
    right = design_matrix.T @ target
    return np.linalg.pinv(left) @ right


def train_weather_regression_model(
    history_df: pd.DataFrame,
    training_years: Sequence[int],
    alpha: float = 1.0,
) -> WeatherRegressionModel:
    if history_df.empty:
        raise ValueError("Cannot train ML forecast model without historical weather data")

    design_matrix, feature_names = build_time_features(history_df["time"])

    irr_target = history_df["irr"].astype(float).to_numpy()
    temp_target = history_df["temp"].astype(float).to_numpy()

    irr_mask = ~np.isnan(irr_target)
    temp_mask = ~np.isnan(temp_target)

    irradiance_coefficients = fit_ridge_regression(
        design_matrix[irr_mask],
        irr_target[irr_mask],
        alpha=alpha,
    )
    temperature_coefficients = fit_ridge_regression(
        design_matrix[temp_mask],
        temp_target[temp_mask],
        alpha=alpha,
    )

    irradiance_pred = design_matrix[irr_mask] @ irradiance_coefficients
    temperature_pred = design_matrix[temp_mask] @ temperature_coefficients

    return WeatherRegressionModel(
        irradiance_coefficients=irradiance_coefficients,
        temperature_coefficients=temperature_coefficients,
        irradiance_metrics=calculate_regression_metrics(
            irr_target[irr_mask],
            irradiance_pred,
        ),
        temperature_metrics=calculate_regression_metrics(
            temp_target[temp_mask],
            temperature_pred,
        ),
        training_years=list(training_years),
        feature_names=feature_names,
    )


def predict_weather_profile(
    model: WeatherRegressionModel,
    target_year: int,
) -> pd.DataFrame:
    timestamps = build_hourly_time_index(target_year)
    design_matrix, _ = build_time_features(timestamps)

    irradiance_pred = design_matrix @ model.irradiance_coefficients
    temperature_pred = design_matrix @ model.temperature_coefficients

    irradiance_pred = np.clip(irradiance_pred, 0.0, None)
    daylight_proxy = np.clip(
        np.cos((timestamps.hour.to_numpy(dtype=float) - 12.0) * math.pi / 12.0),
        0.0,
        None,
    )
    irradiance_pred = irradiance_pred * np.where(daylight_proxy > 0.0, 1.0, 0.0)
    temperature_pred = np.clip(temperature_pred, -35.0, 65.0)

    return pd.DataFrame(
        {
            "time": timestamps,
            "irr": np.round(irradiance_pred, 3),
            "temp": np.round(temperature_pred, 3),
        }
    )


def build_ml_metadata(model: WeatherRegressionModel) -> dict:
    return {
        "training_years": model.training_years,
        "feature_count": len(model.feature_names),
        "features": model.feature_names,
        "training_metrics": {
            "irradiance": model.irradiance_metrics.__dict__,
            "temperature": model.temperature_metrics.__dict__,
        },
    }
