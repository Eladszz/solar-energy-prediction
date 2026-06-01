from __future__ import annotations

import math
from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


def _sanitize_validation_value(value: Any) -> Any:
    if isinstance(value, float) and not math.isfinite(value):
        return str(value)
    if isinstance(value, list):
        return [_sanitize_validation_value(item) for item in value]
    if isinstance(value, tuple):
        return [_sanitize_validation_value(item) for item in value]
    if isinstance(value, dict):
        return {
            key: _sanitize_validation_value(nested_value)
            for key, nested_value in value.items()
        }
    return value


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={"detail": _sanitize_validation_value(exc.errors())},
    )
