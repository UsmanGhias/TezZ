"""Vendor endpoints — dashboard, products, orders, wallet, withdrawals.

These are intentionally minimal but functional: they read from
``product.template`` / ``sale.order`` filtered by the vendor's partner.
Webkul-specific seller models (``mp.product.refund``, ``mp.bank.detail`` …)
are referenced lazily so the module still loads without Webkul installed.
"""
from __future__ import annotations

from datetime import timedelta

from odoo import fields, http
from odoo.http import request

from ..utils import validators
from ..utils.auth_decorator import tezz_jwt_required
from ..utils.envelope import ErrorCode, ok
from .main import API_PREFIX, TezzController, _ApiError, parse_json_body

VENDOR_BASE = f"{API_PREFIX}/vendor"


def _vendor_partner():
    """Return the partner record representing this vendor (== seller)."""
    return request.tezz_user.partner_id


def _vendor_product_domain(env, partner):
    if "marketplace_seller_id" in env["product.template"]._fields:
        return [("marketplace_seller_id", "=", partner.id)]
    # Fallback: products created by this user.
    return [("create_uid", "=", request.tezz_user.id)]


class TezzVendor(TezzController):

    # ----------------------------------------------------------- dashboard
    @http.route(f"{VENDOR_BASE}/dashboard", type="http", auth="public",
                methods=["GET"], csrf=False, save_session=False)
    @tezz_jwt_required(role="vendor")
    def dashboard(self, **_kw):
        return self._dispatch(self._dashboard)

    def _dashboard(self):
        env = request.env(su=True)
        partner = _vendor_partner()
        Product = env["product.template"]
        SO = env["sale.order"]
        product_domain = _vendor_product_domain(env, partner)
        # Sale lines for this vendor's products in confirmed orders.
        SOL = env["sale.order.line"]
        line_domain = [("state", "in", ("sale", "done"))]
        if "marketplace_seller_id" in Product._fields:
            line_domain.append(("product_id.product_tmpl_id.marketplace_seller_id",
                                "=", partner.id))
        else:
            line_domain.append(("product_id.product_tmpl_id.create_uid",
                                "=", request.tezz_user.id))
        last_30 = fields.Datetime.now() - timedelta(days=30)
        recent_lines = SOL.search(line_domain + [("create_date", ">=", last_30)])
        revenue_30d = sum(recent_lines.mapped("price_subtotal"))
        return ok({
            "products_count": Product.search_count(product_domain),
            "orders_count_30d": len({l.order_id.id for l in recent_lines}),
            "revenue_30d": revenue_30d,
            "currency": (recent_lines and recent_lines[0].currency_id.name) or "USD",
        })

    # ----------------------------------------------------------- products
    @http.route(f"{VENDOR_BASE}/products", type="http", auth="public",
                methods=["GET"], csrf=False, save_session=False)
    @tezz_jwt_required(role="vendor")
    def list_products(self, **kw):
        return self._dispatch(self._list_products, kw)

    def _list_products(self, kw):
        env = request.env(su=True)
        domain = _vendor_product_domain(env, _vendor_partner())
        page = validators.bounded_int(kw.get("page"), field="page", lo=1, hi=10_000, default=1)
        page_size = validators.bounded_int(
            kw.get("page_size"), field="page_size", lo=1, hi=100, default=20,
        )
        Tmpl = env["product.template"]
        total = Tmpl.search_count(domain)
        items = Tmpl.search(domain, offset=(page - 1) * page_size,
                            limit=page_size, order="create_date desc")
        return ok(
            {"items": [{
                "id": p.id, "name": p.name,
                "list_price": p.list_price,
                "qty_available": p.qty_available,
                "active": p.active,
            } for p in items]},
            meta={"page": page, "page_size": page_size, "total": total},
        )

    @http.route(f"{VENDOR_BASE}/products", type="http", auth="public",
                methods=["POST"], csrf=False, save_session=False)
    @tezz_jwt_required(role="vendor")
    def create_product(self, **_kw):
        return self._dispatch(self._create_product)

    def _create_product(self):
        body = parse_json_body()
        validators.require(body, ("name", "list_price"))
        env = request.env(su=True)
        vals = {
            "name": body["name"].strip(),
            "list_price": float(body["list_price"]),
            "default_code": body.get("default_code") or False,
            "description_sale": body.get("description") or False,
            "sale_ok": True,
            "type": body.get("type") or "consu",
        }
        if "marketplace_seller_id" in env["product.template"]._fields:
            vals["marketplace_seller_id"] = _vendor_partner().id
        product = env["product.template"].create(vals)
        return ok({"id": product.id}, status=201)

    @http.route(f"{VENDOR_BASE}/products/<int:product_id>", type="http", auth="public",
                methods=["PATCH", "PUT"], csrf=False, save_session=False)
    @tezz_jwt_required(role="vendor")
    def update_product(self, product_id, **_kw):
        return self._dispatch(self._update_product, product_id)

    def _update_product(self, product_id: int):
        body = parse_json_body()
        env = request.env(su=True)
        product = env["product.template"].browse(product_id).exists()
        if not product or not self._owns(product):
            raise _ApiError(ErrorCode.NOT_FOUND, "Product not found")
        allowed = {"name", "list_price", "default_code", "description_sale", "active"}
        vals = {k: body[k] for k in allowed if k in body}
        if vals:
            product.write(vals)
        return ok({"id": product.id})

    @http.route(f"{VENDOR_BASE}/products/<int:product_id>", type="http", auth="public",
                methods=["DELETE"], csrf=False, save_session=False)
    @tezz_jwt_required(role="vendor")
    def delete_product(self, product_id, **_kw):
        return self._dispatch(self._delete_product, product_id)

    def _delete_product(self, product_id: int):
        env = request.env(su=True)
        product = env["product.template"].browse(product_id).exists()
        if not product or not self._owns(product):
            raise _ApiError(ErrorCode.NOT_FOUND, "Product not found")
        product.active = False     # Soft-delete to preserve sale history.
        return ok({"id": product.id, "active": False})

    def _owns(self, product) -> bool:
        if "marketplace_seller_id" in product._fields and product.marketplace_seller_id:
            return product.marketplace_seller_id == _vendor_partner()
        return product.create_uid.id == request.tezz_user.id

    # ------------------------------------------------------------- orders
    @http.route(f"{VENDOR_BASE}/orders", type="http", auth="public",
                methods=["GET"], csrf=False, save_session=False)
    @tezz_jwt_required(role="vendor")
    def list_orders(self, **kw):
        return self._dispatch(self._list_orders, kw)

    def _list_orders(self, kw):
        env = request.env(su=True)
        partner = _vendor_partner()
        SOL = env["sale.order.line"]
        line_domain = [("state", "in", ("sale", "done"))]
        if "marketplace_seller_id" in env["product.template"]._fields:
            line_domain.append(("product_id.product_tmpl_id.marketplace_seller_id",
                                "=", partner.id))
        else:
            line_domain.append(("product_id.product_tmpl_id.create_uid",
                                "=", request.tezz_user.id))
        order_ids = list({l.order_id.id for l in SOL.search(line_domain)})
        orders = env["sale.order"].browse(order_ids)
        return ok({"items": [{
            "id": o.id, "name": o.name, "state": o.state,
            "amount_total": o.amount_total,
            "date_order": o.date_order,
        } for o in orders.sorted("date_order", reverse=True)]})

    # ------------------------------------------------------------- wallet
    @http.route(f"{VENDOR_BASE}/wallet", type="http", auth="public",
                methods=["GET"], csrf=False, save_session=False)
    @tezz_jwt_required(role="vendor")
    def wallet(self, **_kw):
        return self._dispatch(self._wallet)

    def _wallet(self):
        env = request.env(su=True)
        partner = _vendor_partner()
        # Webkul stores seller balances on res.partner; expose 0.0 fallback.
        balance = getattr(partner, "wallet_balance", 0.0) or 0.0
        return ok({"balance": balance, "currency": env.company.currency_id.name})
