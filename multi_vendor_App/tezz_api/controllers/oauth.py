"""Social-login token-exchange endpoints (Google / Facebook / Apple).

The actual signature verification against each provider's JWKS is intentionally
left as a TODO — implementations vary and require provider credentials. The
endpoint shape and the user upsert path are wired so the Flutter app can be
built against a stable contract.
"""
from __future__ import annotations

import logging

from odoo import http
from odoo.http import request

from ..utils.envelope import ErrorCode
from .auth import _request_meta, _resolve_role, _token_pair
from .main import API_PREFIX, TezzController, _ApiError, parse_json_body

_logger = logging.getLogger(__name__)

OAUTH_BASE = f"{API_PREFIX}/auth/oauth"


def _verify_provider_token(provider: str, token: str) -> dict:
    """Verify ``token`` with the provider and return the user profile.

    Replace the body of this function with a real verification call (Google
    tokeninfo, Facebook debug_token, Apple JWKS) before going to production.
    The current implementation refuses tokens by default.
    """
    raise _ApiError(
        ErrorCode.UNAVAILABLE,
        f"OAuth provider {provider!r} not yet configured on this server",
    )


def _upsert_user(env, profile: dict):
    email = (profile.get("email") or "").strip().lower()
    if not email:
        raise _ApiError(ErrorCode.BAD_REQUEST, "Provider profile missing email")
    user = env["res.users"].search([("login", "=", email)], limit=1)
    if user:
        return user
    portal = env.ref("base.group_portal", raise_if_not_found=False)
    tezz_customer = env.ref("tezz_api.group_tezz_customer", raise_if_not_found=False)
    groups = [g.id for g in (portal, tezz_customer) if g]
    return env["res.users"].with_context(no_reset_password=True).create({
        "name": profile.get("name") or email.split("@")[0],
        "login": email,
        "email": email,
        "groups_id": [(6, 0, groups)] if groups else False,
    })


class TezzOAuth(TezzController):

    @http.route(f"{OAUTH_BASE}/<string:provider>", type="http", auth="public",
                methods=["POST"], csrf=False, save_session=False)
    def oauth(self, provider, **_kw):
        return self._dispatch(self._oauth, provider)

    def _oauth(self, provider: str):
        if provider not in ("google", "facebook", "apple"):
            raise _ApiError(ErrorCode.BAD_REQUEST, "Unknown provider")
        body = parse_json_body()
        token = body.get("id_token") or body.get("access_token")
        if not token:
            raise _ApiError(ErrorCode.BAD_REQUEST, "id_token or access_token is required")
        profile = _verify_provider_token(provider, token)
        env = request.env(su=True)
        user = _upsert_user(env, profile)
        role = _resolve_role(user)
        from ..utils.envelope import ok
        return ok(_token_pair(env, user, role=role, request_meta=_request_meta()))
