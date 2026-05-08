"""Shared controller helpers for TezZ API.

Endpoint authors should subclass :class:`TezzController` so they get:

* JSON request parsing with consistent error envelopes
* The ``handle`` context manager that turns ``ValidationError`` and uncaught
  exceptions into proper API errors
* Easy access to ``request.tezz_user`` / ``request.tezz_role`` set by the
  ``@tezz_jwt_required`` decorator
"""
from __future__ import annotations

import json
import logging
from contextlib import contextmanager

from odoo import http
from odoo.http import request

from ..utils.envelope import ErrorCode, fail, ok
from ..utils.validators import ValidationError

_logger = logging.getLogger(__name__)

API_PREFIX = "/api/v1"


def parse_json_body() -> dict:
    """Return the decoded JSON body or ``{}``. Empty bodies are tolerated."""
    raw = request.httprequest.get_data(cache=False, as_text=True) or ""
    if not raw:
        return {}
    try:
        body = json.loads(raw)
    except (ValueError, TypeError) as exc:
        raise ValidationError({"body": f"invalid JSON: {exc}"})
    if not isinstance(body, dict):
        raise ValidationError({"body": "expected a JSON object"})
    return body


@contextmanager
def handle():
    """Convert exceptions into API errors so endpoints stay tidy."""
    try:
        yield
    except ValidationError as exc:
        # Surface the field map as ``details`` for client-side form rendering.
        raise _ApiError(ErrorCode.VALIDATION, "Validation failed", details=exc.errors)


class _ApiError(Exception):
    def __init__(self, code: str, message: str, *, status: int | None = None, details=None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status
        self.details = details


class TezzController(http.Controller):
    """Base class providing a tiny dispatcher with consistent error handling."""

    def _dispatch(self, fn, *args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except _ApiError as exc:
            return fail(exc.code, exc.message, status=exc.status, details=exc.details)
        except ValidationError as exc:
            return fail(ErrorCode.VALIDATION, "Validation failed", details=exc.errors)
        except Exception:  # noqa: BLE001
            _logger.exception("tezz_api: unhandled exception")
            return fail(ErrorCode.INTERNAL, "Internal server error")


# ---------------------------------------------------------------------------
# Public health-check endpoint
# ---------------------------------------------------------------------------
class TezzHealth(TezzController):

    @http.route(f"{API_PREFIX}/health", type="http", auth="public",
                methods=["GET"], csrf=False, save_session=False)
    def health(self, **_kw):
        return ok({"status": "ok", "service": "tezz_api"})

    @http.route(f"{API_PREFIX}/version", type="http", auth="public",
                methods=["GET"], csrf=False, save_session=False)
    def version(self, **_kw):
        return ok({"api": "v1", "module": "tezz_api", "version": "1.0.0"})
