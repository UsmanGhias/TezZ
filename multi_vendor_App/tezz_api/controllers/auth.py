"""Authentication endpoints for TezZ API.

Routes (all under ``/api/v1/auth/``):

* ``POST signup``                 — create customer account
* ``POST login``                  — exchange credentials for token pair
* ``POST logout``                 — revoke a refresh token
* ``POST refresh``                — rotate refresh token, return new pair
* ``POST forgot``                 — request password-reset OTP
* ``POST reset``                  — submit OTP + new password
* ``POST otp/request``            — issue an OTP for signup / phone verification
* ``POST otp/verify``             — confirm an OTP

All endpoints return the canonical ``{data, error, meta}`` envelope.
"""
from __future__ import annotations

import logging

from odoo import http, _
from odoo.exceptions import AccessDenied
from odoo.http import request

from ..utils import jwt_utils, rate_limit, validators
from ..utils.envelope import ErrorCode, ok
from .main import API_PREFIX, TezzController, _ApiError, parse_json_body

_logger = logging.getLogger(__name__)

AUTH_BASE = f"{API_PREFIX}/auth"


def _token_pair(env, user, *, role: str, request_meta: dict | None = None):
    """Issue an access + refresh JWT pair and persist the refresh token."""
    access, access_exp = jwt_utils.encode(env, uid=user.id, role=role, kind="access")
    refresh, refresh_exp = jwt_utils.encode(env, uid=user.id, role=role, kind="refresh")
    refresh_payload = jwt_utils.decode(env, refresh)
    env["tezz.refresh_token"].issue(
        user,
        raw_token=refresh,
        jti=refresh_payload["jti"],
        ttl_seconds=jwt_utils.get_refresh_ttl(env),
        device_label=(request_meta or {}).get("device"),
        user_agent=(request_meta or {}).get("user_agent"),
        ip_address=(request_meta or {}).get("ip"),
    )
    return {
        "token_type": "Bearer",
        "access_token": access,
        "access_expires_at": access_exp,
        "refresh_token": refresh,
        "refresh_expires_at": refresh_exp,
        "user": _user_brief(user, role),
    }


def _user_brief(user, role: str) -> dict:
    partner = user.partner_id
    return {
        "id": user.id,
        "name": user.name,
        "email": user.login,
        "phone": partner.phone or partner.mobile or None,
        "role": role,
        "image_url": f"/web/image?model=res.partner&id={partner.id}&field=avatar_128",
    }


def _resolve_role(user) -> str:
    # Late import to avoid circular dep with auth_decorator at module load.
    from ..utils.auth_decorator import _resolve_role  # noqa: PLC0415
    return _resolve_role(request.env, user)


def _request_meta() -> dict:
    body = {}
    try:
        body = parse_json_body()
    except Exception:  # noqa: BLE001
        body = {}
    return {
        "ip": rate_limit.client_ip(),
        "user_agent": request.httprequest.headers.get("User-Agent"),
        "device": (body.get("device") or {}).get("label") if isinstance(body, dict) else None,
    }


class TezzAuth(TezzController):

    # ------------------------------------------------------------------ signup
    @http.route(f"{AUTH_BASE}/signup", type="http", auth="public",
                methods=["POST"], csrf=False, save_session=False)
    def signup(self, **_kw):
        return self._dispatch(self._signup)

    def _signup(self):
        body = parse_json_body()
        validators.require(body, ("email", "password", "name"))
        email = validators.email(body["email"])
        pwd = validators.password(body["password"])
        name = body["name"].strip()

        if rate_limit.hit(f"signup:{rate_limit.client_ip()}",
                          limit=int(request.env["ir.config_parameter"].sudo()
                                    .get_param("tezz_api.rl.signup.per_hour", 5)),
                          window_seconds=3600):
            raise _ApiError(ErrorCode.RATE_LIMITED, "Too many signups, slow down")

        env = request.env(su=True)
        if env["res.users"].search_count([("login", "=", email)]):
            raise _ApiError(ErrorCode.CONFLICT, "Email already registered")

        portal_group = env.ref("base.group_portal", raise_if_not_found=False)
        tezz_customer = env.ref("tezz_api.group_tezz_customer", raise_if_not_found=False)
        groups = []
        if portal_group:
            groups.append(portal_group.id)
        if tezz_customer:
            groups.append(tezz_customer.id)

        user = env["res.users"].with_context(no_reset_password=True).create({
            "name": name,
            "login": email,
            "password": pwd,
            "email": email,
            "groups_id": [(6, 0, groups)] if groups else False,
            "phone": body.get("phone") or False,
        })
        return ok(_token_pair(env, user, role="customer", request_meta=_request_meta()),
                  status=201)

    # ------------------------------------------------------------------- login
    @http.route(f"{AUTH_BASE}/login", type="http", auth="public",
                methods=["POST"], csrf=False, save_session=False)
    def login(self, **_kw):
        return self._dispatch(self._login)

    def _login(self):
        body = parse_json_body()
        validators.require(body, ("email", "password"))
        email = validators.email(body["email"])
        password = body["password"]

        ip = rate_limit.client_ip()
        if rate_limit.hit(f"login:{ip}",
                          limit=int(request.env["ir.config_parameter"].sudo()
                                    .get_param("tezz_api.rl.login.per_minute", 10)),
                          window_seconds=60):
            raise _ApiError(ErrorCode.RATE_LIMITED, "Too many login attempts")

        db = request.env.cr.dbname
        try:
            uid = request.env["res.users"].authenticate(db, email, password, {"interactive": False})
        except AccessDenied:
            uid = False
        if not uid:
            raise _ApiError(ErrorCode.UNAUTHORIZED, "Invalid email or password")

        env = request.env(su=True)
        user = env["res.users"].browse(uid)
        role = _resolve_role(user)
        return ok(_token_pair(env, user, role=role, request_meta=_request_meta()))

    # ----------------------------------------------------------------- refresh
    @http.route(f"{AUTH_BASE}/refresh", type="http", auth="public",
                methods=["POST"], csrf=False, save_session=False)
    def refresh(self, **_kw):
        return self._dispatch(self._refresh)

    def _refresh(self):
        body = parse_json_body()
        token = body.get("refresh_token")
        if not token:
            raise _ApiError(ErrorCode.BAD_REQUEST, "refresh_token is required")
        try:
            payload = jwt_utils.decode(request.env, token)
        except AccessDenied:
            raise _ApiError(ErrorCode.UNAUTHORIZED, "Invalid refresh token")
        if payload.get("kind") != "refresh":
            raise _ApiError(ErrorCode.UNAUTHORIZED, "Not a refresh token")

        env = request.env(su=True)
        rec = env["tezz.refresh_token"].find_active(token)
        if not rec:
            raise _ApiError(ErrorCode.UNAUTHORIZED, "Refresh token revoked or unknown")
        user = rec.user_id
        rec.revoke()
        role = _resolve_role(user)
        return ok(_token_pair(env, user, role=role, request_meta=_request_meta()))

    # ------------------------------------------------------------------ logout
    @http.route(f"{AUTH_BASE}/logout", type="http", auth="public",
                methods=["POST"], csrf=False, save_session=False)
    def logout(self, **_kw):
        return self._dispatch(self._logout)

    def _logout(self):
        body = parse_json_body()
        token = body.get("refresh_token")
        if token:
            rec = request.env(su=True)["tezz.refresh_token"].find_active(token)
            if rec:
                rec.revoke()
        return ok({"logged_out": True})

    # --------------------------------------------------------------- forgot pw
    @http.route(f"{AUTH_BASE}/forgot", type="http", auth="public",
                methods=["POST"], csrf=False, save_session=False)
    def forgot(self, **_kw):
        return self._dispatch(self._forgot)

    def _forgot(self):
        body = parse_json_body()
        email = validators.email(body.get("email", ""))
        env = request.env(su=True)
        # Always claim success — never leak whether an account exists.
        user = env["res.users"].search([("login", "=", email)], limit=1)
        if user:
            code = env["tezz.otp"].issue(email, "reset")
            _logger.info("tezz_api: password-reset OTP issued to %s", email)
            # In production, dispatch via email queue / SMS provider here.
            user.message_post(
                body=_("Password reset code: %s (valid 10 minutes)") % code,
                subject=_("TezZ password reset"),
            )
        return ok({"sent": True})

    # ---------------------------------------------------------------- reset pw
    @http.route(f"{AUTH_BASE}/reset", type="http", auth="public",
                methods=["POST"], csrf=False, save_session=False)
    def reset(self, **_kw):
        return self._dispatch(self._reset)

    def _reset(self):
        body = parse_json_body()
        validators.require(body, ("email", "code", "new_password"))
        email = validators.email(body["email"])
        new_pwd = validators.password(body["new_password"])
        env = request.env(su=True)
        if not env["tezz.otp"].verify(email, "reset", body["code"]):
            raise _ApiError(ErrorCode.UNAUTHORIZED, "Invalid or expired code")
        user = env["res.users"].search([("login", "=", email)], limit=1)
        if not user:
            raise _ApiError(ErrorCode.NOT_FOUND, "User not found")
        user.write({"password": new_pwd})
        # Revoke all outstanding refresh tokens for safety.
        env["tezz.refresh_token"].search([
            ("user_id", "=", user.id), ("revoked_at", "=", False),
        ]).revoke()
        return ok({"reset": True})

    # -------------------------------------------------------------- otp routes
    @http.route(f"{AUTH_BASE}/otp/request", type="http", auth="public",
                methods=["POST"], csrf=False, save_session=False)
    def otp_request(self, **_kw):
        return self._dispatch(self._otp_request)

    def _otp_request(self):
        body = parse_json_body()
        identifier = (body.get("email") or body.get("phone") or "").strip()
        purpose = body.get("purpose") or "signup"
        if not identifier:
            raise _ApiError(ErrorCode.BAD_REQUEST, "email or phone is required")
        if purpose not in ("signup", "login", "phone"):
            raise _ApiError(ErrorCode.BAD_REQUEST, "invalid purpose")
        if rate_limit.hit(f"otp:{rate_limit.client_ip()}:{identifier}",
                          limit=int(request.env["ir.config_parameter"].sudo()
                                    .get_param("tezz_api.rl.otp.per_hour", 5)),
                          window_seconds=3600):
            raise _ApiError(ErrorCode.RATE_LIMITED, "Too many OTP requests")
        code = request.env(su=True)["tezz.otp"].issue(identifier, purpose)
        _logger.info("tezz_api: OTP %s issued for %s", purpose, identifier)
        # TODO: dispatch via SMS/email provider; intentionally never returned.
        return ok({"sent": True})

    @http.route(f"{AUTH_BASE}/otp/verify", type="http", auth="public",
                methods=["POST"], csrf=False, save_session=False)
    def otp_verify(self, **_kw):
        return self._dispatch(self._otp_verify)

    def _otp_verify(self):
        body = parse_json_body()
        identifier = (body.get("email") or body.get("phone") or "").strip()
        purpose = body.get("purpose") or "signup"
        code = body.get("code")
        if not identifier or not code:
            raise _ApiError(ErrorCode.BAD_REQUEST, "identifier and code are required")
        verified = request.env(su=True)["tezz.otp"].verify(identifier, purpose, code)
        if not verified:
            raise _ApiError(ErrorCode.UNAUTHORIZED, "Invalid or expired code")
        return ok({"verified": True})
