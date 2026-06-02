"""Shared string and credential validators used across Pydantic schemas.

Centralised so the rules (whitespace handling, control-char rejection,
password strength) are consistent across every request schema.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Final

#: 100,000 ha is a generous upper bound for any single farm record.
MAX_FARM_SIZE_HA: Final[float] = 100_000.0

#: RFC 5321 caps email local+domain at 254 octets.
MAX_EMAIL_LENGTH: Final[int] = 254

#: Upper bound for any free-form text field the user can submit.
MAX_TEXT_LENGTH: Final[int] = 2_000

#: Copilot prompts can be longer, but still bounded to prevent abuse.
MAX_COPILOT_MESSAGE_LENGTH: Final[int] = 4_000

#: Image URLs / storage paths are not expected to exceed 2 KB.
MAX_URL_LENGTH: Final[int] = 2_048

#: Risk alert_type is a controlled vocabulary; keep it short.
MAX_ALERT_TYPE_LENGTH: Final[int] = 80

#: Password must contain at least this many of the four character classes.
PASSWORD_MIN_CLASSES: Final[int] = 3

_CONTROL_CHARS = {chr(c) for c in range(32) if c not in (9, 10, 13)}  # exclude \t \n \r

_PASSWORD_CLASS_PATTERNS: Final[dict[str, re.Pattern[str]]] = {
    "lower": re.compile(r"[a-z]"),
    "upper": re.compile(r"[A-Z]"),
    "digit": re.compile(r"\d"),
    "symbol": re.compile(r"[^A-Za-z0-9\s]"),
}


def _strip_and_check(
    value: str,
    *,
    field_name: str,
    min_length: int,
    max_length: int,
) -> str:
    """Strip surrounding whitespace and reject control characters.

    Empty or whitespace-only inputs are rejected. Non-printable / control
    characters (other than tab/newline/carriage-return) raise a ValueError so
    callers receive a 422 instead of letting weird bytes reach the database.
    """
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    stripped = value.strip()
    if len(stripped) < min_length:
        raise ValueError(
            f"{field_name} must be at least {min_length} characters after trimming"
        )
    if len(stripped) > max_length:
        raise ValueError(
            f"{field_name} must be at most {max_length} characters after trimming"
        )
    for ch in stripped:
        if ch in _CONTROL_CHARS:
            raise ValueError(f"{field_name} must not contain control characters")
        if unicodedata.category(ch) == "Cc":
            raise ValueError(f"{field_name} must not contain control characters")
    return stripped


def clean_short_text(value: str, *, field_name: str = "value") -> str:
    """Validate a 1..MAX_TEXT_LENGTH free-form text field."""
    return _strip_and_check(
        value, field_name=field_name, min_length=1, max_length=MAX_TEXT_LENGTH
    )


def clean_short_text_optional(
    value: str | None, *, field_name: str = "value"
) -> str | None:
    if value is None:
        return None
    return _strip_and_check(
        value, field_name=field_name, min_length=0, max_length=MAX_TEXT_LENGTH
    )


def clean_copilot_message(value: str) -> str:
    return _strip_and_check(
        value,
        field_name="message",
        min_length=1,
        max_length=MAX_COPILOT_MESSAGE_LENGTH,
    )


def clean_alert_type(value: str) -> str:
    return _strip_and_check(
        value,
        field_name="alert_type",
        min_length=1,
        max_length=MAX_ALERT_TYPE_LENGTH,
    )


def clean_email(value: str) -> str:
    """Normalise and validate an email: trim, lowercase, length-bounded."""
    if not isinstance(value, str):
        raise ValueError("email must be a string")
    stripped = value.strip()
    if not stripped:
        raise ValueError("email must not be empty")
    if len(stripped) > MAX_EMAIL_LENGTH:
        raise ValueError(f"email must be at most {MAX_EMAIL_LENGTH} characters")
    return stripped.lower()


def clean_display_name(value: str) -> str:
    return _strip_and_check(value, field_name="name", min_length=1, max_length=255)


def validate_password_strength(value: str) -> str:
    """Reject passwords below the policy floor.

    Policy (NIST-inspired, deliberately pragmatic for MVP):

    - length already enforced at the schema level (8..128)
    - must contain at least 3 of {lowercase, uppercase, digit, symbol}
    - must not be the literal string ``"password"`` (cheap blocklist
      for the worst offenders)
    """
    if not isinstance(value, str):
        raise ValueError("password must be a string")
    classes_present = sum(
        1 for pattern in _PASSWORD_CLASS_PATTERNS.values() if pattern.search(value)
    )
    if classes_present < PASSWORD_MIN_CLASSES:
        raise ValueError(
            "password must contain at least 3 of: lowercase, uppercase, digit, symbol"
        )
    if value.strip().lower() in {"password", "changeme", "admin123"}:
        raise ValueError("password is too common")
    return value
