{
    "name": "TezZ API",
    "version": "17.0.1.0.0",
    "summary": "Mobile-friendly REST API layer for the TezZ marketplace.",
    "description": """
TezZ API
========

Versioned JSON REST surface that sits on top of Odoo + Webkul Marketplace
models. Provides JWT authentication, role-based access (customer / vendor /
admin), and a stable ``/api/v1/...`` contract for the TezZ Flutter apps.

This module does not modify Webkul addons — it only reads/writes their
records through the Odoo ORM, which keeps the marketplace upgrade-safe.
""",
    "author": "TezZ",
    "website": "https://tezz.example.com",
    "category": "Marketplace/API",
    "license": "LGPL-3",
    "depends": [
        "base",
        "web",
        "mail",
        "product",
        "sale",
        "sale_management",
        "stock",
        "account",
    ],
    "external_dependencies": {
        "python": ["pyjwt"],
    },
    "data": [
        "security/tezz_security.xml",
        "security/ir.model.access.csv",
        "data/ir_config_parameter.xml",
        "data/ir_cron.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
