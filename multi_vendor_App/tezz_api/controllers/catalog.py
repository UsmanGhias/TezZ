"""Catalog: home, categories, products, search."""
from __future__ import annotations

import logging

from odoo import http
from odoo.http import request

from ..utils import validators
from ..utils.envelope import ErrorCode, ok
from .main import API_PREFIX, TezzController, _ApiError

_logger = logging.getLogger(__name__)

DEFAULT_PAGE_SIZE = 24
MAX_PAGE_SIZE = 100


# ---------------------------------------------------------------------------
# Serializers — keep small and explicit so the wire shape stays under control.
# ---------------------------------------------------------------------------
def _image_url(model: str, rec_id: int, field: str = "image_512") -> str:
    return f"/web/image?model={model}&id={rec_id}&field={field}"


def _category_brief(cat) -> dict:
    return {
        "id": cat.id,
        "name": cat.name,
        "parent_id": cat.parent_id.id if cat.parent_id else None,
        "image_url": _image_url("product.public.category", cat.id),
    }


def _product_brief(tmpl) -> dict:
    vendor_id = None
    if "marketplace_seller_id" in tmpl._fields:
        seller = tmpl.marketplace_seller_id
        vendor_id = seller.id if seller else None
    return {
        "id": tmpl.id,
        "name": tmpl.name,
        "list_price": tmpl.list_price,
        "currency": tmpl.currency_id.name if tmpl.currency_id else "USD",
        "image_url": _image_url("product.template", tmpl.id),
        "rating": getattr(tmpl, "rating_avg", 0.0),
        "vendor_id": vendor_id,
    }


def _product_detail(tmpl) -> dict:
    out = _product_brief(tmpl)
    out.update({
        "description": tmpl.description_sale or "",
        "default_code": tmpl.default_code or "",
        "qty_available": tmpl.qty_available,
        "categ_id": tmpl.categ_id.id,
        "attributes": [{
            "name": line.attribute_id.name,
            "values": line.value_ids.mapped("name"),
        } for line in tmpl.attribute_line_ids],
        "variants": [{
            "id": v.id,
            "name": v.display_name,
            "price": v.lst_price,
            "default_code": v.default_code or "",
            "qty_available": v.qty_available,
            "image_url": _image_url("product.product", v.id),
        } for v in tmpl.product_variant_ids],
    })
    return out


# ---------------------------------------------------------------------------
class TezzCatalog(TezzController):

    # ------------------------------------------------------------------- home
    @http.route(f"{API_PREFIX}/home", type="http", auth="public",
                methods=["GET"], csrf=False, save_session=False)
    def home(self, **kw):
        return self._dispatch(self._home, kw)

    def _home(self, kw):
        env = request.env(su=True)
        product = env["product.template"]
        published_domain = [("sale_ok", "=", True), ("active", "=", True)]
        if "website_published" in product._fields:
            published_domain.append(("website_published", "=", True))

        trending = product.search(published_domain, limit=12, order="create_date desc")
        # Best-sellers via sale_order_line aggregation, fallback to recent.
        try:
            sol = env["sale.order.line"].read_group(
                domain=[("state", "in", ("sale", "done"))],
                fields=["product_id", "product_uom_qty:sum"],
                groupby=["product_id"], orderby="product_uom_qty desc", limit=12,
            )
            best_ids = [row["product_id"][0] for row in sol if row.get("product_id")]
            best_variants = env["product.product"].browse(best_ids).exists()
            best_sellers = best_variants.mapped("product_tmpl_id")[:12]
        except Exception:  # noqa: BLE001
            best_sellers = trending

        if "product.public.category" in env.registry:
            categories = env["product.public.category"].search(
                [("parent_id", "=", False)], limit=12,
            )
        else:
            categories = env["product.category"].search([], limit=12)

        return ok({
            "banners": [],  # Placeholder — wire to a future ``tezz.banner`` model.
            "categories": [_category_brief(c) for c in categories],
            "trending": [_product_brief(p) for p in trending],
            "best_sellers": [_product_brief(p) for p in best_sellers],
        })

    # ------------------------------------------------------------ categories
    @http.route(f"{API_PREFIX}/categories", type="http", auth="public",
                methods=["GET"], csrf=False, save_session=False)
    def categories(self, **kw):
        return self._dispatch(self._categories)

    def _categories(self):
        env = request.env(su=True)
        if "product.public.category" in env.registry:
            Cat = env["product.public.category"]
        else:
            Cat = env["product.category"]
        roots = Cat.search([("parent_id", "=", False)], order="sequence, name")
        return ok({"categories": [_category_brief(c) for c in roots]})

    # ------------------------------------------------------------- products
    @http.route(f"{API_PREFIX}/products", type="http", auth="public",
                methods=["GET"], csrf=False, save_session=False)
    def products(self, **kw):
        return self._dispatch(self._products, kw)

    def _products(self, kw):
        page = validators.bounded_int(kw.get("page"), field="page", lo=1, hi=10_000, default=1)
        page_size = validators.bounded_int(
            kw.get("page_size"), field="page_size",
            lo=1, hi=MAX_PAGE_SIZE, default=DEFAULT_PAGE_SIZE,
        )
        env = request.env(su=True)
        domain = [("sale_ok", "=", True), ("active", "=", True)]
        if kw.get("category_id"):
            try:
                domain.append(("categ_id", "child_of", int(kw["category_id"])))
            except (TypeError, ValueError):
                raise _ApiError(ErrorCode.BAD_REQUEST, "category_id must be an integer")
        if kw.get("vendor_id"):
            if "marketplace_seller_id" not in env["product.template"]._fields:
                raise _ApiError(ErrorCode.BAD_REQUEST,
                                "vendor filter requires the marketplace module")
            try:
                domain.append(("marketplace_seller_id", "=", int(kw["vendor_id"])))
            except (TypeError, ValueError):
                raise _ApiError(ErrorCode.BAD_REQUEST, "vendor_id must be an integer")
        if kw.get("min_price"):
            domain.append(("list_price", ">=", float(kw["min_price"])))
        if kw.get("max_price"):
            domain.append(("list_price", "<=", float(kw["max_price"])))

        order_map = {
            "newest": "create_date desc",
            "price_asc": "list_price asc",
            "price_desc": "list_price desc",
            "name": "name asc",
        }
        order = order_map.get(kw.get("sort") or "newest", "create_date desc")

        Tmpl = env["product.template"]
        total = Tmpl.search_count(domain)
        items = Tmpl.search(domain, offset=(page - 1) * page_size,
                            limit=page_size, order=order)
        return ok(
            {"items": [_product_brief(p) for p in items]},
            meta={"page": page, "page_size": page_size, "total": total},
        )

    # ------------------------------------------------------- product details
    @http.route(f"{API_PREFIX}/products/<int:product_id>", type="http", auth="public",
                methods=["GET"], csrf=False, save_session=False)
    def product_detail(self, product_id, **_kw):
        return self._dispatch(self._product_detail, product_id)

    def _product_detail(self, product_id: int):
        env = request.env(su=True)
        tmpl = env["product.template"].browse(product_id).exists()
        if not tmpl or not tmpl.sale_ok or not tmpl.active:
            raise _ApiError(ErrorCode.NOT_FOUND, "Product not found")
        return ok(_product_detail(tmpl))

    # ------------------------------------------------------------- search
    @http.route(f"{API_PREFIX}/products/search", type="http", auth="public",
                methods=["GET"], csrf=False, save_session=False)
    def product_search(self, **kw):
        return self._dispatch(self._product_search, kw)

    def _product_search(self, kw):
        q = (kw.get("q") or "").strip()
        if len(q) < 2:
            raise _ApiError(ErrorCode.BAD_REQUEST, "q must be at least 2 characters")
        page = validators.bounded_int(kw.get("page"), field="page", lo=1, hi=10_000, default=1)
        page_size = validators.bounded_int(
            kw.get("page_size"), field="page_size",
            lo=1, hi=MAX_PAGE_SIZE, default=DEFAULT_PAGE_SIZE,
        )
        env = request.env(su=True)
        domain = [
            ("sale_ok", "=", True), ("active", "=", True),
            "|", ("name", "ilike", q), ("default_code", "ilike", q),
        ]
        Tmpl = env["product.template"]
        total = Tmpl.search_count(domain)
        items = Tmpl.search(domain, offset=(page - 1) * page_size,
                            limit=page_size, order="name asc")
        return ok(
            {"items": [_product_brief(p) for p in items], "query": q},
            meta={"page": page, "page_size": page_size, "total": total},
        )
