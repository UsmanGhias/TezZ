"""Order endpoints — checkout, history, tracking, cancel, return."""
from __future__ import annotations

from odoo import http
from odoo.http import request

from ..utils import validators
from ..utils.auth_decorator import tezz_jwt_required
from ..utils.envelope import ErrorCode, ok
from .main import API_PREFIX, TezzController, _ApiError, parse_json_body

ORDERS_BASE = f"{API_PREFIX}/orders"
CHECKOUT_BASE = f"{API_PREFIX}/checkout"


def _serialize_order(order) -> dict:
    return {
        "id": order.id,
        "name": order.name,
        "state": order.state,
        "currency": order.currency_id.name,
        "amount_total": order.amount_total,
        "date_order": order.date_order,
        "delivery_status": getattr(order, "delivery_status", None),
        "items": [{
            "product_id": l.product_id.id,
            "name": l.name,
            "qty": l.product_uom_qty,
            "subtotal": l.price_subtotal,
        } for l in order.order_line],
    }


class TezzOrders(TezzController):

    # ----------------------------------------------------------------- list
    @http.route(ORDERS_BASE, type="http", auth="public",
                methods=["GET"], csrf=False, save_session=False)
    @tezz_jwt_required(role="customer")
    def list_orders(self, **kw):
        return self._dispatch(self._list, kw)

    def _list(self, kw):
        page = validators.bounded_int(kw.get("page"), field="page", lo=1, hi=10_000, default=1)
        page_size = validators.bounded_int(
            kw.get("page_size"), field="page_size", lo=1, hi=100, default=20,
        )
        env = request.env(su=True)
        domain = [
            ("partner_id", "=", request.tezz_user.partner_id.id),
            ("state", "!=", "draft"),
        ]
        SO = env["sale.order"]
        total = SO.search_count(domain)
        orders = SO.search(domain, order="date_order desc",
                           offset=(page - 1) * page_size, limit=page_size)
        return ok(
            {"items": [_serialize_order(o) for o in orders]},
            meta={"page": page, "page_size": page_size, "total": total},
        )

    # --------------------------------------------------------------- detail
    @http.route(f"{ORDERS_BASE}/<int:order_id>", type="http", auth="public",
                methods=["GET"], csrf=False, save_session=False)
    @tezz_jwt_required(role="customer")
    def get_order(self, order_id, **_kw):
        return self._dispatch(self._get, order_id)

    def _get(self, order_id: int):
        env = request.env(su=True)
        order = env["sale.order"].browse(order_id).exists()
        if not order or order.partner_id != request.tezz_user.partner_id:
            raise _ApiError(ErrorCode.NOT_FOUND, "Order not found")
        return ok(_serialize_order(order))

    # --------------------------------------------------------------- track
    @http.route(f"{ORDERS_BASE}/<int:order_id>/track", type="http", auth="public",
                methods=["GET"], csrf=False, save_session=False)
    @tezz_jwt_required(role="customer")
    def track(self, order_id, **_kw):
        return self._dispatch(self._track, order_id)

    def _track(self, order_id: int):
        env = request.env(su=True)
        order = env["sale.order"].browse(order_id).exists()
        if not order or order.partner_id != request.tezz_user.partner_id:
            raise _ApiError(ErrorCode.NOT_FOUND, "Order not found")
        events = []
        for picking in order.picking_ids.sorted("scheduled_date"):
            events.append({
                "name": picking.name,
                "state": picking.state,
                "scheduled_date": picking.scheduled_date,
                "carrier_tracking_ref": picking.carrier_tracking_ref or None,
                "origin_address": picking.location_id.display_name,
                "dest_address": picking.location_dest_id.display_name,
            })
        return ok({"order_id": order.id, "state": order.state, "events": events})

    # -------------------------------------------------------------- cancel
    @http.route(f"{ORDERS_BASE}/<int:order_id>/cancel", type="http", auth="public",
                methods=["POST"], csrf=False, save_session=False)
    @tezz_jwt_required(role="customer")
    def cancel(self, order_id, **_kw):
        return self._dispatch(self._cancel, order_id)

    def _cancel(self, order_id: int):
        env = request.env(su=True)
        order = env["sale.order"].browse(order_id).exists()
        if not order or order.partner_id != request.tezz_user.partner_id:
            raise _ApiError(ErrorCode.NOT_FOUND, "Order not found")
        if order.state in ("done", "cancel"):
            raise _ApiError(ErrorCode.CONFLICT, f"Cannot cancel order in state {order.state!r}")
        order._action_cancel() if hasattr(order, "_action_cancel") else order.action_cancel()
        return ok(_serialize_order(order))


class TezzCheckout(TezzController):

    # --------------------------------------------------------------- quote
    @http.route(f"{CHECKOUT_BASE}/quote", type="http", auth="public",
                methods=["GET"], csrf=False, save_session=False)
    @tezz_jwt_required(role="customer")
    def quote(self, **_kw):
        return self._dispatch(self._quote)

    def _quote(self):
        env = request.env(su=True)
        order = env["sale.order"].search([
            ("partner_id", "=", request.tezz_user.partner_id.id),
            ("state", "=", "draft"),
        ], limit=1)
        if not order or not order.order_line:
            raise _ApiError(ErrorCode.CONFLICT, "Cart is empty")
        return ok({
            "amount_untaxed": order.amount_untaxed,
            "amount_tax": order.amount_tax,
            "amount_total": order.amount_total,
            "currency": order.currency_id.name,
            "shipping_options": [],   # Wire to delivery providers in a follow-up.
            "payment_methods": ["cod", "jazzcash", "easypaisa"],
        })

    # --------------------------------------------------------------- place
    @http.route(f"{CHECKOUT_BASE}/place", type="http", auth="public",
                methods=["POST"], csrf=False, save_session=False)
    @tezz_jwt_required(role="customer")
    def place(self, **_kw):
        return self._dispatch(self._place)

    def _place(self):
        body = parse_json_body()
        validators.require(body, ("address_id", "payment_method"))
        address_id = validators.positive_int(body["address_id"], field="address_id")
        method = body["payment_method"]
        if method not in ("cod", "jazzcash", "easypaisa"):
            raise _ApiError(ErrorCode.BAD_REQUEST, "Unsupported payment_method")

        env = request.env(su=True)
        partner = request.tezz_user.partner_id
        address = env["res.partner"].browse(address_id).exists()
        if not address or (address != partner and address.parent_id != partner):
            raise _ApiError(ErrorCode.NOT_FOUND, "Address not found")

        order = env["sale.order"].search([
            ("partner_id", "=", partner.id), ("state", "=", "draft"),
        ], limit=1)
        if not order or not order.order_line:
            raise _ApiError(ErrorCode.CONFLICT, "Cart is empty")

        order.write({
            "partner_shipping_id": address.id,
            "partner_invoice_id": address.id,
        })
        order.action_confirm()
        return ok({
            "order_id": order.id,
            "name": order.name,
            "amount_total": order.amount_total,
            "payment_method": method,
            # Real payment intent creation will live in payments.py.
            "payment_redirect_url": None,
        }, status=201)
