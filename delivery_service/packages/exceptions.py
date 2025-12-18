import logging

from rest_framework import status
from rest_framework.views import exception_handler as drf_exception_handler

from .utils import api_response

logger = logging.getLogger("packages")


def custom_exception_handler(exc, context):
    response = drf_exception_handler(exc, context)

    view = context.get("view")
    request = context.get("request")

    if response is None:
        logger.exception(
            "Unhandled exception in view",
            extra={"view": str(view), "path": getattr(request, "path", None)},
        )
        return api_response(
            success=False,
            error_code="SERVER_ERROR",
            message="Внутренняя ошибка сервера",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    detail = response.data

    if isinstance(detail, dict):
        if "detail" in detail:
            message = str(detail["detail"])
            extra_details = None
        else:
            message = "Ошибка валидации данных"
            extra_details = detail
    elif isinstance(detail, list):
        message = str(detail[0]) if detail else "Ошибка запроса"
        extra_details = detail if len(detail) > 1 else None
    else:
        message = str(detail)
        extra_details = None

    logger.warning(
        "Handled API exception",
        extra={
            "view": str(view),
            "path": getattr(request, "path", None),
            "status": response.status_code,
            "detail": detail,
        },
    )

    if response.status_code == status.HTTP_400_BAD_REQUEST:
        code = "VALIDATION_ERROR"
    elif response.status_code == status.HTTP_401_UNAUTHORIZED:
        code = "UNAUTHORIZED"
    elif response.status_code == status.HTTP_403_FORBIDDEN:
        code = "FORBIDDEN"
    elif response.status_code == status.HTTP_404_NOT_FOUND:
        code = "NOT_FOUND"
    elif response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED:
        code = "METHOD_NOT_ALLOWED"
    elif response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
        code = "RATE_LIMIT_EXCEEDED"
    elif response.status_code >= 500:
        code = "SERVER_ERROR"
    else:
        code = "ERROR"

    return api_response(
        success=False,
        error_code=code,
        message=message,
        status_code=response.status_code,
        extra_error_details=extra_details,
    )
