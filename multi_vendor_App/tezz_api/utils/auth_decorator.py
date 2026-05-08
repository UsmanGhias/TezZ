"""``@tezz_jwt_required`` decorator and request-context helpers.

Reads the bearer token from ``Authorization: Bearer <token>``, validates it,
loads the corresponding ``res.users`` record, and binds it to ``request.env``
so downstream code runs with the authenticated user's ACLs.
"""
from __future__ import annotations

import functools
import logging
from typing import Callable, Iterable

from odoo import api, SUPERUSER_ID
from odoo.exceptions import AccessDenied
from odoo.http import request

from . import jwt_utils
from .envelope import ErrorCode, fail

_logger = logging.getLogger(__name__)

ROLE_CUSTOMER = "customer"
ROLE_VENDOR = "vendor"
ROLE_ADMIN = "admin"
ALL_ROLES = (ROLE_CUSTOMER, ROLE_VENDOR, ROLE_ADMIN)

# Group XML-IDs that map to API roles. Vendor/admin groups are checked at
# runtime — if Webkul isn't installed the vendor group simply won't match.
GROUP_VENDOR_XMLIDS = (
    "odoo_marketplace.marketplace_seller_group",
    "tezz_api.group_tezz_vendor",
)
GROUP_ADMIN_XMLIDS = (
    "base.group_system",
    "odoo_marketplace.marketplace_officer_group",
)


def _extract_token() -> str | None:
    auth = request.httprequest.headers.get("Authorization", "")
    if not auth.lower().startswith("bearer "):
        return None
    return auth.split(" ", 1)[1].strip() or None


def _user_has_group(env, user, xmlids: Iterable[str]) -> bool:
    for xmlid in xmlids:
        try:
            if user.has_group(xmlid):
                return True
        except ValueError:
            # Group not installed; ignore.
            continue
    return False


def _resolve_role(env, user) -> str:
    if _user_has_group(env, user, GROUP_ADMIN_XMLIDS):
        return ROLE_ADMIN
    if _user_has_group(env, user, GROUP_VENDOR_XMLIDS):
        return ROLE_VENDOR
    return ROLE_CUSTOMER


def tezz_jwt_required(role: str | Iterable[str] | None = None,
                      kind: str = "access") -> Callable:
    """Wrap a controller method so it requires a valid JWT.

    :param role: optional required role(s). ``"customer"`` is accepted by all
        authenticated users; ``"vendor"`` and ``"admin"`` enforce the
        corresponding marketplace groups.
    :param kind: token kind to accept (``"access"`` or ``"refresh"``).
    """
    required: tuple[str, ...]
    if role is None:
        required = ()
    elif isinstance(role, str):
        required = (role,)
    else:
        required = tuple(role)
    for r in required:
        if r not in ALL_ROLES:
            raise ValueError(f"Unknown role: {r!r}")

    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            token = _extract_token()
            if not token:
                return fail(ErrorCode.UNAUTHORIZED, "Missing bearer token")
            try:
                payload = jwt_utils.decode(request.env, token)
            except AccessDenied as exc:
                return fail(ErrorCode.UNAUTHORIZED, str(exc) or "Invalid token")
            if payload.get("kind") != kind:
                return fail(ErrorCode.UNAUTHORIZED,
                            f"Expected {kind} token, got {payload.get('kind')!r}")
            try:
                uid = int(payload["sub"])
            except (KeyError, TypeError, ValueError):
                return fail(ErrorCode.UNAUTHORIZED, "Malformed token subject")

            su_env = api.Environment(request.env.cr, SUPERUSER_ID, request.env.context)
            user = su_env["res.users"].browse(uid).exists()
            if not user or not user.active:
                return fail(ErrorCode.UNAUTHORIZED, "User no longer exists")

            actual_role = _resolve_role(su_env, user)
            if required and actual_role not in required and ROLE_ADMIN not in (actual_role,):
                # Admins implicitly satisfy any role requirement.
                if actual_role != ROLE_ADMIN:
                    return fail(ErrorCode.FORBIDDEN,
                                f"Requires role {required!r}, have {actual_role!r}")

            # Re-bind request.env to the authenticated user.
            request.update_env(user=user.id)
            request.tezz_user = user
            request.tezz_role = actual_role
            request.tezz_jwt_payload = payload
            return func(self, *args, **kwargs)

        return wrapper

    return decorator
