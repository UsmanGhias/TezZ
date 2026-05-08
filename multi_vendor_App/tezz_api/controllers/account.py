"""Customer-account endpoints — profile, addresses, wishlist, reviews."""
from __future__ import annotations

from odoo import http
from odoo.http import request

from ..utils import validators
from ..utils.auth_decorator import tezz_jwt_required
from ..utils.envelope import ErrorCode, ok
from .main import API_PREFIX, TezzController, _ApiError, parse_json_body

ME_BASE = f"{API_PREFIX}/me"


def _serialize_partner(p) -> dict:
    return {
        "id": p.id,
        "name": p.name,
        "phone": p.phone,
        "street": p.street,
        "street2": p.street2,
        "city": p.city,
        "zip": p.zip,
        "state_id": p.state_id.id if p.state_id else None,
        "country_id": p.country_id.id if p.country_id else None,
        "type": p.type,
    }


class TezzMe(TezzController):

    # -------------------------------------------------------------- profile
    @http.route(ME_BASE, type="http", auth="public",
                methods=["GET"], csrf=False, save_session=False)
    @tezz_jwt_required()
    def me(self, **_kw):
        return self._dispatch(self._me)

    def _me(self):
        u = request.tezz_user
        p = u.partner_id
        return ok({
            "id": u.id,
            "name": u.name,
            "email": u.login,
            "phone": p.phone or p.mobile,
            "role": request.tezz_role,
        })

    # ------------------------------------------------------------ addresses
    @http.route(f"{ME_BASE}/addresses", type="http", auth="public",
                methods=["GET"], csrf=False, save_session=False)
    @tezz_jwt_required(role="customer")
    def addresses(self, **_kw):
        return self._dispatch(self._addresses)

    def _addresses(self):
        env = request.env(su=True)
        partner = request.tezz_user.partner_id
        addrs = env["res.partner"].search([
            "|", ("id", "=", partner.id), ("parent_id", "=", partner.id),
        ])
        return ok({"items": [_serialize_partner(a) for a in addrs]})

    @http.route(f"{ME_BASE}/addresses", type="http", auth="public",
                methods=["POST"], csrf=False, save_session=False)
    @tezz_jwt_required(role="customer")
    def create_address(self, **_kw):
        return self._dispatch(self._create_address)

    def _create_address(self):
        body = parse_json_body()
        validators.require(body, ("name", "street", "city"))
        env = request.env(su=True)
        addr = env["res.partner"].create({
            "parent_id": request.tezz_user.partner_id.id,
            "name": body["name"].strip(),
            "phone": body.get("phone") or False,
            "street": body["street"],
            "street2": body.get("street2") or False,
            "city": body["city"],
            "zip": body.get("zip") or False,
            "country_id": int(body["country_id"]) if body.get("country_id") else False,
            "state_id": int(body["state_id"]) if body.get("state_id") else False,
            "type": body.get("type") or "delivery",
        })
        return ok(_serialize_partner(addr), status=201)

    @http.route(f"{ME_BASE}/addresses/<int:address_id>", type="http", auth="public",
                methods=["DELETE"], csrf=False, save_session=False)
    @tezz_jwt_required(role="customer")
    def delete_address(self, address_id, **_kw):
        return self._dispatch(self._delete_address, address_id)

    def _delete_address(self, address_id: int):
        env = request.env(su=True)
        partner = request.tezz_user.partner_id
        addr = env["res.partner"].browse(address_id).exists()
        if not addr or addr.parent_id != partner:
            raise _ApiError(ErrorCode.NOT_FOUND, "Address not found")
        addr.unlink()
        return ok({"deleted": True})

    # -------------------------------------------------------------- wishlist
    @http.route(f"{ME_BASE}/wishlist", type="http", auth="public",
                methods=["GET"], csrf=False, save_session=False)
    @tezz_jwt_required(role="customer")
    def wishlist(self, **_kw):
        return self._dispatch(self._wishlist)

    def _wishlist(self):
        env = request.env(su=True)
        partner = request.tezz_user.partner_id
        if "product.wishlist" not in env.registry:
            return ok({"items": []})
        items = env["product.wishlist"].search([("partner_id", "=", partner.id)])
        return ok({"items": [{
            "id": w.id,
            "product_id": w.product_id.id,
            "name": w.product_id.display_name,
        } for w in items]})

    @http.route(f"{ME_BASE}/wishlist/<int:product_id>", type="http", auth="public",
                methods=["POST"], csrf=False, save_session=False)
    @tezz_jwt_required(role="customer")
    def add_wishlist(self, product_id, **_kw):
        return self._dispatch(self._add_wishlist, product_id)

    def _add_wishlist(self, product_id: int):
        env = request.env(su=True)
        if "product.wishlist" not in env.registry:
            raise _ApiError(ErrorCode.UNAVAILABLE,
                            "Wishlist module is not installed on this server")
        partner = request.tezz_user.partner_id
        if not env["product.product"].browse(product_id).exists():
            raise _ApiError(ErrorCode.NOT_FOUND, "Product not found")
        existing = env["product.wishlist"].search([
            ("partner_id", "=", partner.id), ("product_id", "=", product_id),
        ], limit=1)
        if not existing:
            env["product.wishlist"].create({
                "partner_id": partner.id, "product_id": product_id,
            })
        return ok({"added": True})

    @http.route(f"{ME_BASE}/wishlist/<int:product_id>", type="http", auth="public",
                methods=["DELETE"], csrf=False, save_session=False)
    @tezz_jwt_required(role="customer")
    def remove_wishlist(self, product_id, **_kw):
        return self._dispatch(self._remove_wishlist, product_id)

    def _remove_wishlist(self, product_id: int):
        env = request.env(su=True)
        if "product.wishlist" not in env.registry:
            return ok({"removed": True})
        partner = request.tezz_user.partner_id
        env["product.wishlist"].search([
            ("partner_id", "=", partner.id), ("product_id", "=", product_id),
        ]).unlink()
        return ok({"removed": True})
