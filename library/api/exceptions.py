"""The one place that turns exceptions into {"error": {"code", "message"}}.

handle_exception is DRF's EXCEPTION_HANDLER (see settings). The three views at
the bottom replace Django's HTML pages for unknown routes and crashes.
"""

import logging

from django.http import Http404, JsonResponse
from rest_framework import exceptions as drf
from rest_framework.response import Response

from library.services.errors import Conflict, InvalidInput, LibraryError, NotFound

logger = logging.getLogger("library.api")

SERVICE_STATUS = ((InvalidInput, 400), (NotFound, 404), (Conflict, 409))


def error_body(code: str, message: str) -> dict:
    return {"error": {"code": code, "message": message}}


def first_message(detail) -> str:
    """The first message in a DRF error detail (a string, a list or a dict of them)."""
    if isinstance(detail, dict):
        return first_message(next(iter(detail.values()), "invalid request"))
    if isinstance(detail, list):
        return first_message(detail[0]) if detail else "invalid request"
    return str(detail)


def handle_exception(exc, context):
    if isinstance(exc, LibraryError):
        for family, status in SERVICE_STATUS:
            if isinstance(exc, family):
                return Response(error_body(exc.code, exc.message), status=status)
    if isinstance(exc, drf.ValidationError):
        return Response(error_body("validation_error", first_message(exc.detail)), status=400)
    if isinstance(exc, (drf.ParseError, drf.UnsupportedMediaType)):
        return Response(error_body("validation_error", "body must be a JSON object"), status=400)
    if isinstance(exc, drf.MethodNotAllowed):
        return Response(error_body("method_not_allowed", "method not allowed"), status=405)
    if isinstance(exc, (Http404, drf.NotFound)):
        return Response(error_body("not_found", "not found"), status=404)
    logger.exception("unexpected problem", exc_info=exc)
    return Response(error_body("internal_error", "unexpected problem"), status=500)


def _json(code: str, message: str, status: int) -> JsonResponse:
    # Compact separators, the same as DRF's JSONRenderer.
    return JsonResponse(error_body(code, message), status=status, json_dumps_params={"separators": (",", ":")})


def bad_request_view(request, exception=None):
    return _json("validation_error", "bad request", 400)


def not_found_view(request, exception=None):
    return _json("not_found", "not found", 404)


def server_error_view(request):
    return _json("internal_error", "unexpected problem", 500)
