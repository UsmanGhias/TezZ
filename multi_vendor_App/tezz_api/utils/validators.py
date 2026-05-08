"""Tiny request-validation helpers.

Avoids pulling in marshmallow/pydantic for what is a small, focused surface.
Each helper raises :class:`ValidationError` with a per-field error map that
controllers can surface verbatim through the JSON envelope.
"""
from __future__ import annotations

import re
from typing import Any, Iterable

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_RE = re.compile(r"^\+?[0-9 \-]{6,20}$")


class ValidationError(Exception):
    """Raised when request payload validation fails."""

    def __init__(self, errors: dict[str, str]):
        super().__init__("Validation failed")
        self.errors = errors


def require(payload: dict[str, Any] | None, fields: Iterable[str]) -> dict[str, Any]:
    """Return the subset of ``payload`` containing all required ``fields``."""
    payload = payload or {}
    missing = {f: "required" for f in fields if not payload.get(f)}
    if missing:
        raise ValidationError(missing)
    return {f: payload[f] for f in fields}


def email(value: str) -> str:
    if not value or not EMAIL_RE.match(value):
        raise ValidationError({"email": "invalid email"})
    return value.strip().lower()


def phone(value: str) -> str:
    if not value or not PHONE_RE.match(value):
        raise ValidationError({"phone": "invalid phone number"})
    return value.strip()


def password(value: str) -> str:
    if not value or len(value) < 8:
        raise ValidationError({"password": "must be at least 8 characters"})
    return value


def positive_int(value: Any, *, field: str = "value", default: int | None = None) -> int:
    if value is None or value == "":
        if default is not None:
            return default
        raise ValidationError({field: "required"})
    try:
        n = int(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError({field: "must be an integer"}) from exc
    if n <= 0:
        raise ValidationError({field: "must be positive"})
    return n


def bounded_int(value: Any, *, field: str, lo: int, hi: int, default: int) -> int:
    if value is None or value == "":
        return default
    try:
        n = int(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError({field: "must be an integer"}) from exc
    return max(lo, min(hi, n))
