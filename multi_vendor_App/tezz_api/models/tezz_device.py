"""Mobile-device registry for push notifications."""
from __future__ import annotations

from odoo import api, fields, models

PLATFORMS = [
    ("android", "Android"),
    ("ios", "iOS"),
    ("web", "Web"),
]


class TezzDevice(models.Model):
    _name = "tezz.device"
    _description = "TezZ mobile device / push token"
    _order = "write_date desc"

    user_id = fields.Many2one("res.users", required=True, ondelete="cascade", index=True)
    push_token = fields.Char(required=True, index=True)
    platform = fields.Selection(PLATFORMS, required=True)
    app_version = fields.Char()
    locale = fields.Char()
    last_seen = fields.Datetime(default=fields.Datetime.now)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ("push_token_unique", "unique(push_token)", "Device already registered."),
    ]

    @api.model
    def upsert(self, user, *, push_token: str, platform: str,
               app_version: str | None = None, locale: str | None = None) -> "TezzDevice":
        rec = self.sudo().search([("push_token", "=", push_token)], limit=1)
        vals = {
            "user_id": user.id,
            "platform": platform,
            "app_version": app_version,
            "locale": locale,
            "last_seen": fields.Datetime.now(),
            "active": True,
        }
        if rec:
            rec.write(vals)
            return rec
        vals["push_token"] = push_token
        return self.sudo().create(vals)
