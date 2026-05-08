"""Lightweight DB-backed rate limiter.

Uses the ``tezz.rate_limit`` model as a sliding window counter keyed by an
arbitrary string (typically ``"<endpoint>:<ip>"`` or ``"<endpoint>:<uid>"``).
Redis would be faster, but DB-only keeps the module dependency-free; swap in
Redis later by replacing :func:`hit`.
"""
from __future__ import annotations

import logging
import time

from odoo import api, SUPERUSER_ID
from odoo.http import request

_logger = logging.getLogger(__name__)


def client_ip() -> str:
    req = request.httprequest
    fwd = req.headers.get("X-Forwarded-For", "")
    if fwd:
        return fwd.split(",")[0].strip()
    return req.remote_addr or "0.0.0.0"


def hit(key: str, *, limit: int, window_seconds: int) -> bool:
    """Record an attempt for ``key``. Return ``True`` when over the limit."""
    env = api.Environment(request.env.cr, SUPERUSER_ID, {})
    Model = env["tezz.rate_limit"]
    now = int(time.time())
    window_start = now - window_seconds
    rec = Model.search([("key", "=", key)], limit=1)
    if not rec:
        Model.create({"key": key, "count": 1, "window_start": now})
        return False
    if rec.window_start < window_start:
        rec.write({"count": 1, "window_start": now})
        return False
    if rec.count >= limit:
        return True
    rec.count = rec.count + 1
    return False
