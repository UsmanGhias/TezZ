"""TezZ demo seed.

Run inside the Odoo container::

    docker compose exec odoo python3 /mnt/extra-addons/../scripts/seed_demo.py

The script connects via `odoo.cli.shell`-style execution and creates a small
catalog (categories, sample products, a vendor user) so the mobile app has
data to render in development. Idempotent — safe to re-run.
"""
from __future__ import annotations

import os
import sys

import odoo  # type: ignore[import-not-found]
from odoo.api import Environment

DB = os.environ.get("DEFAULT_DB", "teez_marketplace")


def seed(env: Environment) -> None:
    Cat = env["product.category"]
    Tmpl = env["product.template"]
    Users = env["res.users"]

    fashion = Cat.search([("name", "=", "Fashion")], limit=1) or Cat.create({"name": "Fashion"})
    electronics = Cat.search([("name", "=", "Electronics")], limit=1) \
        or Cat.create({"name": "Electronics"})

    samples = [
        {"name": "TezZ T-Shirt", "list_price": 19.99, "categ_id": fashion.id},
        {"name": "TezZ Hoodie", "list_price": 39.99, "categ_id": fashion.id},
        {"name": "TezZ Wireless Earbuds", "list_price": 49.99, "categ_id": electronics.id},
    ]
    for vals in samples:
        if not Tmpl.search([("name", "=", vals["name"])], limit=1):
            Tmpl.create({**vals, "sale_ok": True, "type": "consu"})

    vendor_email = "vendor@tezz.local"
    if not Users.search([("login", "=", vendor_email)], limit=1):
        groups = []
        for xmlid in ("base.group_portal", "tezz_api.group_tezz_vendor",
                      "odoo_marketplace.marketplace_seller_group"):
            grp = env.ref(xmlid, raise_if_not_found=False)
            if grp:
                groups.append(grp.id)
        Users.with_context(no_reset_password=True).create({
            "name": "Demo Vendor",
            "login": vendor_email,
            "password": "Vendor123!",
            "email": vendor_email,
            "groups_id": [(6, 0, groups)] if groups else False,
        })

    print("✓ TezZ demo seed complete")


def main() -> int:
    odoo.tools.config.parse_config(["-d", DB])
    odoo.cli.server.report_configuration()
    with odoo.api.Environment.manage():
        registry = odoo.registry(DB)
        with registry.cursor() as cr:
            env = Environment(cr, odoo.SUPERUSER_ID, {})
            seed(env)
            cr.commit()
    return 0


if __name__ == "__main__":
    sys.exit(main())
