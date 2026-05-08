"""Payment scaffolding.

v1 directly supports COD; JazzCash/Easypaisa/Stripe/PayPal/Razorpay endpoints
are stubs that document the contract and refuse cleanly until provider
credentials are configured. Webhook routes verify signatures (when configured)
and post a confirmation message on the matching ``sale.order``.
"""
from __future__ import annotations

import logging

from odoo import http
from odoo.http import request

from ..utils import validators
from ..utils.auth_decorator import tezz_jwt_required
from ..utils.envelope import ErrorCode, ok
from .main import API_PREFIX, TezzController, _ApiError, parse_json_body

_logger = logging.getLogger(__name__)
PAY_BASE = f"{API_PREFIX}/payments"

SUPPORTED_METHODS = ("cod", "jazzcash", "easypaisa", "stripe", "paypal", "razorpay")


class TezzPayments(TezzController):

    # ------------------------------------------------------------- intents
    @http.route(f"{PAY_BASE}/intents", type="http", auth="public",
                methods=["POST"], csrf=False, save_session=False)
    @tezz_jwt_required(role="customer")
    def create_intent(self, **_kw):
        return self._dispatch(self._create_intent)

    def _create_intent(self):
        body = parse_json_body()
        validators.require(body, ("order_id", "method"))
        order_id = validators.positive_int(body["order_id"], field="order_id")
        method = body["method"]
        if method not in SUPPORTED_METHODS:
            raise _ApiError(ErrorCode.BAD_REQUEST, "Unsupported method")
        env = request.env(su=True)
        order = env["sale.order"].browse(order_id).exists()
        if not order or order.partner_id != request.tezz_user.partner_id:
            raise _ApiError(ErrorCode.NOT_FOUND, "Order not found")

        if method == "cod":
            order.message_post(body="COD selected — cash collected on delivery.")
            return ok({
                "method": "cod",
                "status": "confirmed",
                "amount": order.amount_total,
                "currency": order.currency_id.name,
                "redirect_url": None,
            }, status=201)

        # External providers — refuse until credentials are wired.
        raise _ApiError(
            ErrorCode.UNAVAILABLE,
            f"Payment method {method!r} is not configured on this server",
        )

    # ------------------------------------------------------------ webhooks
    @http.route(f"{PAY_BASE}/webhooks/<string:provider>", type="http", auth="public",
                methods=["POST"], csrf=False, save_session=False)
    def webhook(self, provider, **_kw):
        return self._dispatch(self._webhook, provider)

    def _webhook(self, provider: str):
        if provider not in SUPPORTED_METHODS:
            raise _ApiError(ErrorCode.NOT_FOUND, "Unknown provider")
        # TODO: provider-specific signature verification before trusting body.
        body = parse_json_body()
        _logger.info("tezz_api: %s webhook: %s", provider, list(body))
        return ok({"received": True})
