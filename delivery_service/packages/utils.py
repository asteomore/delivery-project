from rest_framework.response import Response as DRFResponse


def api_response(data=None, success=True, error_code=None, message=None, status_code=200):
    body = {
        "status": success,
        "data": data if success else None,
        "error": None
        if success
        else {
            "code": error_code or "ERROR",
            "message": message,
        },
    }
    return DRFResponse(body, status=status_code)
