"""Hashed refresh-token store.

We never persist raw refresh tokens; only their SHA-256 digests, so a database
breach cannot be replayed against the API. Token rotation is handled by the
auth controller — every refresh issues a new token and revokes the old one.
"""
from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta

from odoo import api, fields, models


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class TezzRefreshToken(models.Model):
    _name = "tezz.refresh_token"
    _description = "TezZ API refresh token"
    _order = "create_date desc"

    user_id = fields.Many2one("res.users", required=True, ondelete="cascade", index=True)
    token_hash = fields.Char(required=True, index=True)
    jti = fields.Char(string="JWT ID", index=True)
    device_label = fields.Char()
    user_agent = fields.Char()
    ip_address = fields.Char()
    expires_at = fields.Datetime(required=True, index=True)
    revoked_at = fields.Datetime()

    _sql_constraints = [
        ("token_hash_unique", "unique(token_hash)", "Refresh token already exists."),
    ]

    @api.model
    def issue(self, user, *, raw_token: str, jti: str, ttl_seconds: int,
              device_label: str | None = None, user_agent: str | None = None,
              ip_address: str | None = None) -> "TezzRefreshToken":
        return self.sudo().create({
            "user_id": user.id,
            "token_hash": _hash(raw_token),
            "jti": jti,
            "device_label": device_label,
            "user_agent": user_agent,
            "ip_address": ip_address,
            "expires_at": fields.Datetime.now() + timedelta(seconds=ttl_seconds),
        })

    @api.model
    def find_active(self, raw_token: str) -> "TezzRefreshToken":
        rec = self.sudo().search([("token_hash", "=", _hash(raw_token))], limit=1)
        if not rec or rec.revoked_at or rec.expires_at < fields.Datetime.now():
            return self.browse()
        return rec

    def revoke(self) -> None:
        self.sudo().write({"revoked_at": fields.Datetime.now()})

    @api.model
    def gc(self) -> int:
        """Cron entry point — purge expired/revoked tokens older than 7 days."""
        cutoff = fields.Datetime.now() - timedelta(days=7)
        old = self.sudo().search([
            "|",
            ("expires_at", "<", cutoff),
            ("revoked_at", "<", cutoff),
        ])
        n = len(old)
        old.unlink()
        return n
