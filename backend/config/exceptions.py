"""Consistent structured error responses per API specification."""

from __future__ import annotations

from typing import Any

from rest_framework import exceptions, status
from rest_framework.response import Response
from rest_framework.views import exception_handler


class SlotChefAPIError(exceptions.APIException):
    """Base API exception carrying an explicit SlotChef error code."""

    default_code = "VALIDATION_ERROR"
    status_code = status.HTTP_400_BAD_REQUEST

    def __init__(
        self,
        detail: Any = None,
        code: str | None = None,
        status_code: int | None = None,
    ) -> None:
        if status_code is not None:
            self.status_code = status_code
        super().__init__(detail=detail, code=code or self.default_code)
        self.error_code = code or self.default_code


def _map_exception_code(exc: Exception, response: Response) -> str:
    if isinstance(exc, SlotChefAPIError):
        return exc.error_code
    if isinstance(exc, exceptions.NotAuthenticated | exceptions.AuthenticationFailed):
        return "AUTHENTICATION_REQUIRED"
    if isinstance(exc, exceptions.PermissionDenied):
        return "FORBIDDEN"
    if isinstance(exc, exceptions.NotFound):
        return "RESOURCE_NOT_FOUND"
    if response.status_code == status.HTTP_409_CONFLICT:
        return "SCHEDULE_CONFLICT"
    if response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE:
        return "SCHEDULER_UNAVAILABLE"
    return "VALIDATION_ERROR"


def structured_exception_handler(exc: Exception, context: dict[str, Any]) -> Response | None:
    """Wrap DRF exception responses in a consistent structured error envelope."""
    response = exception_handler(exc, context)
    if response is None:
        return None

    error_code = _map_exception_code(exc, response)
    raw_data = response.data
    message = "Request could not be processed."
    if isinstance(raw_data, dict) and "detail" in raw_data:
        message = str(raw_data["detail"])
    elif isinstance(raw_data, list) and raw_data:
        message = str(raw_data[0])

    response.data = {
        "error": {
            "code": error_code,
            "message": message,
            "details": raw_data,
        }
    }
    return response

