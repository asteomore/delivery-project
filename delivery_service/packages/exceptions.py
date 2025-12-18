import logging

from rest_framework import status
from rest_framework.views import exception_handler as drf_exception_handler

from .utils import api_response

logger = logging.getLogger(__name__)


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
    if isinstance(detail, dict) and "detail" in detail:
        message = detail["detail"]
    else:
        message = detail

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
    elif response.status_code == status.HTTP_404_NOT_FOUND:
        code = "NOT_FOUND"
    elif response.status_code == status.HTTP_403_FORBIDDEN:
        code = "FORBIDDEN"
    else:
        code = "ERROR"

    return api_response(
        success=False,
        error_code=code,
        message=message,
        status_code=response.status_code,
    )
