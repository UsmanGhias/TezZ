"""Per-key counter used by :mod:`tezz_api.utils.rate_limit`."""
from odoo import fields, models


class TezzRateLimit(models.Model):
    _name = "tezz.rate_limit"
    _description = "TezZ API rate-limit counter"
    _rec_name = "key"

    key = fields.Char(required=True, index=True)
    count = fields.Integer(default=0)
    window_start = fields.Integer(help="Unix timestamp the current window started at.")

    _sql_constraints = [
        ("key_unique", "unique(key)", "Rate-limit key must be unique."),
    ]
