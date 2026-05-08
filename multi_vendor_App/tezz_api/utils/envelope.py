"""JSON envelope and standardized error responses for TezZ API.

Every endpoint returns a JSON document of shape::

    {
        "data":  <object | list | null>,
        "error": <object | null>,
        "meta":  {"request_id": str, "ts": int, ...}
    }

This keeps client code uniform and forward-compatible (adding pagination
metadata, deprecation notices, etc. doesn't break clients).
"""
from __future__ import annotations

import json
import logging
import time
import uuid
from typing import Any

from odoo.http import Response

_logger = logging.getLogger(__name__)


# Canonical error codes — keep in sync with the OpenAPI spec.
class ErrorCode:
    BAD_REQUEST = "bad_request"
    UNAUTHORIZED = "unauthorized"
    FORBIDDEN = "forbidden"
    NOT_FOUND = "not_found"
    CONFLICT = "conflict"
    RATE_LIMITED = "rate_limited"
    VALIDATION = "validation_error"
    INTERNAL = "internal_error"
    UPSTREAM = "upstream_error"
    UNAVAILABLE = "service_unavailable"


_HTTP_FOR_CODE = {
    ErrorCode.BAD_REQUEST: 400,
    ErrorCode.UNAUTHORIZED: 401,
    ErrorCode.FORBIDDEN: 403,
    ErrorCode.NOT_FOUND: 404,
    ErrorCode.CONFLICT: 409,
    ErrorCode.RATE_LIMITED: 429,
    ErrorCode.VALIDATION: 422,
    ErrorCode.INTERNAL: 500,
    ErrorCode.UPSTREAM: 502,
    ErrorCode.UNAVAILABLE: 503,
}


def _meta(extra: dict[str, Any] | None = None) -> dict[str, Any]:
    meta = {"request_id": uuid.uuid4().hex, "ts": int(time.time())}
    if extra:
        meta.update(extra)
    return meta


def _json_response(payload: dict[str, Any], status: int) -> Response:
    body = json.dumps(payload, default=str, separators=(",", ":"))
    headers = [
        ("Content-Type", "application/json; charset=utf-8"),
        ("X-Request-ID", payload.get("meta", {}).get("request_id", "")),
        # Conservative caching defaults for an API.
        ("Cache-Control", "no-store"),
    ]
    return Response(body, status=status, headers=headers)


def ok(data: Any = None, *, status: int = 200,
       meta: dict[str, Any] | None = None) -> Response:
    """Return a success envelope."""
    payload = {"data": data, "error": None, "meta": _meta(meta)}
    return _json_response(payload, status)


def fail(code: str, message: str, *, status: int | None = None,
         details: Any = None, meta: dict[str, Any] | None = None) -> Response:
    """Return an error envelope."""
    http_status = status or _HTTP_FOR_CODE.get(code, 400)
    payload = {
        "data": None,
        "error": {"code": code, "message": message, "details": details},
        "meta": _meta(meta),
    }
    if http_status >= 500:
        _logger.error("tezz_api error %s: %s", code, message)
    return _json_response(payload, http_status)
