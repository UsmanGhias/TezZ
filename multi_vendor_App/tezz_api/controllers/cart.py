"""Cart endpoints — backed by ``sale.order`` in draft state.

Each authenticated user has at most one open draft order; we look it up by
partner. Multi-vendor splits are computed at read time so the storage stays a
single ``sale.order`` (Webkul splits into per-seller sub-orders at confirm).
"""
from __future__ import annotations

from collections import defaultdict

from odoo import http
from odoo.http import request

from ..utils import validators
from ..utils.auth_decorator import tezz_jwt_required
from ..utils.envelope import ErrorCode, ok
from .main import API_PREFIX, TezzController, _ApiError, parse_json_body

CART_BASE = f"{API_PREFIX}/cart"


def _get_or_create_cart(env, partner):
    order = env["sale.order"].search([
        ("partner_id", "=", partner.id), ("state", "=", "draft"),
    ], limit=1, order="create_date desc")
    if order:
        return order
    return env["sale.order"].create({"partner_id": partner.id})


def _vendor_for_line(line) -> tuple[int | None, str | None]:
    tmpl = line.product_id.product_tmpl_id
    if "marketplace_seller_id" in tmpl._fields and tmpl.marketplace_seller_id:
        return tmpl.marketplace_seller_id.id, tmpl.marketplace_seller_id.name
    return None, None


def _serialize_cart(order) -> dict:
    groups: dict[int | None, dict] = defaultdict(
        lambda: {"vendor_id": None, "vendor_name": None, "items": [], "subtotal": 0.0},
    )
    for line in order.order_line:
        vid, vname = _vendor_for_line(line)
        bucket = groups[vid]
        bucket["vendor_id"] = vid
        bucket["vendor_name"] = vname
        bucket["items"].append({
            "id": line.id,
            "product_id": line.product_id.id,
            "product_template_id": line.product_id.product_tmpl_id.id,
            "name": line.name,
            "qty": line.product_uom_qty,
            "unit_price": line.price_unit,
            "subtotal": line.price_subtotal,
            "image_url": f"/web/image?model=product.product&id={line.product_id.id}&field=image_512",
        })
        bucket["subtotal"] += line.price_subtotal
    return {
        "id": order.id,
        "currency": order.currency_id.name,
        "amount_untaxed": order.amount_untaxed,
        "amount_tax": order.amount_tax,
        "amount_total": order.amount_total,
        "vendors": list(groups.values()),
    }


class TezzCart(TezzController):

    # ------------------------------------------------------------------- read
    @http.route(CART_BASE, type="http", auth="public",
                methods=["GET"], csrf=False, save_session=False)
    @tezz_jwt_required(role="customer")
    def get_cart(self, **_kw):
        return self._dispatch(self._get_cart)

    def _get_cart(self):
        env = request.env(su=True)
        order = _get_or_create_cart(env, request.tezz_user.partner_id)
        return ok(_serialize_cart(order))

    # -------------------------------------------------------------- add line
    @http.route(f"{CART_BASE}/items", type="http", auth="public",
                methods=["POST"], csrf=False, save_session=False)
    @tezz_jwt_required(role="customer")
    def add_item(self, **_kw):
        return self._dispatch(self._add_item)

    def _add_item(self):
        body = parse_json_body()
        validators.require(body, ("product_id",))
        product_id = validators.positive_int(body["product_id"], field="product_id")
        qty = validators.bounded_int(body.get("qty"), field="qty",
                                     lo=1, hi=999, default=1)
        env = request.env(su=True)
        product = env["product.product"].browse(product_id).exists()
        if not product or not product.sale_ok:
            raise _ApiError(ErrorCode.NOT_FOUND, "Product not available")
        order = _get_or_create_cart(env, request.tezz_user.partner_id)
        existing = order.order_line.filtered(lambda l: l.product_id.id == product.id)
        if existing:
            existing.product_uom_qty += qty
        else:
            env["sale.order.line"].create({
                "order_id": order.id,
                "product_id": product.id,
                "product_uom_qty": qty,
            })
        return ok(_serialize_cart(order))

    # ------------------------------------------------------------ update qty
    @http.route(f"{CART_BASE}/items/<int:line_id>", type="http", auth="public",
                methods=["PATCH", "PUT"], csrf=False, save_session=False)
    @tezz_jwt_required(role="customer")
    def update_item(self, line_id, **_kw):
        return self._dispatch(self._update_item, line_id)

    def _update_item(self, line_id: int):
        body = parse_json_body()
        qty = validators.bounded_int(body.get("qty"), field="qty",
                                     lo=0, hi=999, default=1)
        env = request.env(su=True)
        line = env["sale.order.line"].browse(line_id).exists()
        if not line or line.order_id.partner_id != request.tezz_user.partner_id:
            raise _ApiError(ErrorCode.NOT_FOUND, "Cart line not found")
        if qty == 0:
            order = line.order_id
            line.unlink()
        else:
            line.product_uom_qty = qty
            order = line.order_id
        return ok(_serialize_cart(order))

    # ------------------------------------------------------------ remove line
    @http.route(f"{CART_BASE}/items/<int:line_id>", type="http", auth="public",
                methods=["DELETE"], csrf=False, save_session=False)
    @tezz_jwt_required(role="customer")
    def delete_item(self, line_id, **_kw):
        return self._dispatch(self._delete_item, line_id)

    def _delete_item(self, line_id: int):
        env = request.env(su=True)
        line = env["sale.order.line"].browse(line_id).exists()
        if not line or line.order_id.partner_id != request.tezz_user.partner_id:
            raise _ApiError(ErrorCode.NOT_FOUND, "Cart line not found")
        order = line.order_id
        line.unlink()
        return ok(_serialize_cart(order))
