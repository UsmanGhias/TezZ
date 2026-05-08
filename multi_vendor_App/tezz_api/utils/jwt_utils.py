"""JWT helpers for the TezZ API.

The signing secret and lifetimes are read from ``ir.config_parameter`` so they
can be rotated without redeploying. Defaults are dev-friendly but unsafe for
production — operators must set ``tezz_api.jwt_secret`` to a long random value.
"""
from __future__ import annotations

import logging
import secrets
import time
from typing import Any

try:
    import jwt  # PyJWT
except ImportError:  # pragma: no cover - surfaced at install time
    jwt = None

from odoo import api, SUPERUSER_ID
from odoo.exceptions import AccessDenied

_logger = logging.getLogger(__name__)

ALGORITHM = "HS256"
ACCESS_TOKEN_TTL_SECONDS = 60 * 30          # 30 minutes
REFRESH_TOKEN_TTL_SECONDS = 60 * 60 * 24 * 30  # 30 days

PARAM_SECRET = "tezz_api.jwt_secret"
PARAM_ISSUER = "tezz_api.jwt_issuer"
PARAM_ACCESS_TTL = "tezz_api.access_ttl"
PARAM_REFRESH_TTL = "tezz_api.refresh_ttl"


def _params(env):
    return env["ir.config_parameter"].sudo()


def get_secret(env) -> str:
    """Return the JWT signing secret, generating one on first call."""
    secret = _params(env).get_param(PARAM_SECRET)
    if not secret:
        secret = secrets.token_urlsafe(64)
        _params(env).set_param(PARAM_SECRET, secret)
        _logger.warning(
            "tezz_api: generated new JWT secret on first use. "
            "Set %s explicitly in production.", PARAM_SECRET,
        )
    return secret


def get_issuer(env) -> str:
    return _params(env).get_param(PARAM_ISSUER) or "tezz-api"


def get_access_ttl(env) -> int:
    return int(_params(env).get_param(PARAM_ACCESS_TTL) or ACCESS_TOKEN_TTL_SECONDS)


def get_refresh_ttl(env) -> int:
    return int(_params(env).get_param(PARAM_REFRESH_TTL) or REFRESH_TOKEN_TTL_SECONDS)


def encode(env, *, uid: int, role: str, kind: str = "access",
           extra: dict[str, Any] | None = None) -> tuple[str, int]:
    """Encode a JWT and return ``(token, exp_unix)``."""
    if jwt is None:
        raise RuntimeError("PyJWT is not installed; add `pyjwt` to requirements.")
    now = int(time.time())
    ttl = get_access_ttl(env) if kind == "access" else get_refresh_ttl(env)
    payload: dict[str, Any] = {
        "sub": str(uid),
        "role": role,
        "kind": kind,
        "iss": get_issuer(env),
        "iat": now,
        "nbf": now,
        "exp": now + ttl,
        "jti": secrets.token_urlsafe(16),
    }
    if extra:
        payload.update(extra)
    token = jwt.encode(payload, get_secret(env), algorithm=ALGORITHM)
    if isinstance(token, bytes):  # PyJWT < 2 compat
        token = token.decode("ascii")
    return token, payload["exp"]


def decode(env, token: str) -> dict[str, Any]:
    """Decode and validate a JWT. Raises ``AccessDenied`` on failure."""
    if jwt is None:
        raise RuntimeError("PyJWT is not installed; add `pyjwt` to requirements.")
    try:
        return jwt.decode(
            token,
            get_secret(env),
            algorithms=[ALGORITHM],
            issuer=get_issuer(env),
            options={"require": ["exp", "iat", "sub", "role", "kind"]},
        )
    except Exception as exc:  # noqa: BLE001 - PyJWT raises a hierarchy
        _logger.debug("tezz_api: token rejected: %s", exc)
        raise AccessDenied("Invalid or expired token") from exc
