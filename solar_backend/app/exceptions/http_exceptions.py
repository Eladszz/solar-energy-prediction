from typing import Protocol

from fastapi import HTTPException


class HttpExceptionConvertible(Protocol):
    http_status_code: int
    user_message: str


def exception_to_http_exception(exc: HttpExceptionConvertible) -> HTTPException:
    return HTTPException(status_code=exc.http_status_code, detail=exc.user_message)
