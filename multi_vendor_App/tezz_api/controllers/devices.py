"""FCM device registration endpoints."""
from __future__ import annotations

from odoo import http
from odoo.http import request

from ..utils import validators
from ..utils.auth_decorator import tezz_jwt_required
from ..utils.envelope import ErrorCode, ok
from .main import API_PREFIX, TezzController, _ApiError, parse_json_body

DEV_BASE = f"{API_PREFIX}/devices"


class TezzDevices(TezzController):

    @http.route(DEV_BASE, type="http", auth="public",
                methods=["POST"], csrf=False, save_session=False)
    @tezz_jwt_required()
    def register(self, **_kw):
        return self._dispatch(self._register)

    def _register(self):
        body = parse_json_body()
        validators.require(body, ("push_token", "platform"))
        platform = body["platform"]
        if platform not in ("android", "ios", "web"):
            raise _ApiError(ErrorCode.BAD_REQUEST, "platform must be android|ios|web")
        rec = request.env(su=True)["tezz.device"].upsert(
            request.tezz_user,
            push_token=body["push_token"],
            platform=platform,
            app_version=body.get("app_version"),
            locale=body.get("locale"),
        )
        return ok({"id": rec.id})

    @http.route(f"{DEV_BASE}/<string:push_token>", type="http", auth="public",
                methods=["DELETE"], csrf=False, save_session=False)
    @tezz_jwt_required()
    def unregister(self, push_token, **_kw):
        return self._dispatch(self._unregister, push_token)

    def _unregister(self, push_token: str):
        env = request.env(su=True)
        rec = env["tezz.device"].search([
            ("push_token", "=", push_token),
            ("user_id", "=", request.tezz_user.id),
        ], limit=1)
        if rec:
            rec.active = False
        return ok({"unregistered": True})
