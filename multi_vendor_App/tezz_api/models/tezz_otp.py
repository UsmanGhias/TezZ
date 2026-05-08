"""One-time-password records for signup, phone verification and reset flows.

The plain OTP is never stored — only its salted hash. ``purpose`` distinguishes
between signup, login, password reset, etc., so a code issued for one flow
cannot be used in another.
"""
from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import timedelta

from odoo import api, fields, models

PURPOSES = [
    ("signup", "Signup"),
    ("login", "Login"),
    ("reset", "Password reset"),
    ("phone", "Phone verification"),
]


def _hash(code: str, salt: str) -> str:
    return hashlib.sha256(f"{salt}:{code}".encode("utf-8")).hexdigest()


class TezzOtp(models.Model):
    _name = "tezz.otp"
    _description = "TezZ API one-time password"
    _order = "create_date desc"

    identifier = fields.Char(required=True, index=True,
                             help="Email or phone number receiving the code.")
    purpose = fields.Selection(PURPOSES, required=True, index=True)
    code_hash = fields.Char(required=True)
    salt = fields.Char(required=True)
    expires_at = fields.Datetime(required=True, index=True)
    consumed_at = fields.Datetime()
    attempts = fields.Integer(default=0)

    @api.model
    def issue(self, identifier: str, purpose: str, *, ttl_seconds: int = 600) -> str:
        """Create a 6-digit code and return it (caller must dispatch it)."""
        code = f"{secrets.randbelow(1_000_000):06d}"
        salt = secrets.token_hex(8)
        self.sudo().create({
            "identifier": identifier,
            "purpose": purpose,
            "code_hash": _hash(code, salt),
            "salt": salt,
            "expires_at": fields.Datetime.now() + timedelta(seconds=ttl_seconds),
        })
        return code

    @api.model
    def verify(self, identifier: str, purpose: str, code: str) -> bool:
        rec = self.sudo().search([
            ("identifier", "=", identifier),
            ("purpose", "=", purpose),
            ("consumed_at", "=", False),
            ("expires_at", ">=", fields.Datetime.now()),
        ], order="create_date desc", limit=1)
        if not rec:
            return False
        rec.attempts += 1
        if rec.attempts > 5:
            rec.consumed_at = fields.Datetime.now()
            return False
        if not hmac.compare_digest(rec.code_hash, _hash(code, rec.salt)):
            return False
        rec.consumed_at = fields.Datetime.now()
        return True

    @api.model
    def gc(self) -> int:
        """Cron entry point — purge OTPs older than 1 day."""
        cutoff = fields.Datetime.now() - timedelta(days=1)
        old = self.sudo().search([("create_date", "<", cutoff)])
        n = len(old)
        old.unlink()
        return n
