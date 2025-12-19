from rest_framework.response import Response as DRFResponse


def api_response(
    data=None,
    success=True,
    error_code=None,
    message=None,
    status_code=200,
    extra_error_details=None,
):
    """Вернуть стандартизованный JSON-ответ вида {status, data, error}."""
    body = {
        "status": success,
        "data": data if success else None,
        "error": None
        if success
        else {
            "code": error_code or "ERROR",
            "message": message,
            "details": extra_error_details,
        },
    }
    return DRFResponse(body, status=status_code)


def get_session_key(request):
    """Гарантированно получить session_key, создавая сессию при необходимости."""
    session = request.session
    if not session.session_key:
        session.save()
    return session.session_key
