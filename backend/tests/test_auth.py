"""Auth utilities: password hashing + JWT round-trip with role."""

from __future__ import annotations

import time

import pytest

from app.models.enums import UserRole
from app.utils.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_hash_and_verify_password_roundtrip():
    password = "Correct1Horse!Staple"
    h = hash_password(password)
    assert h != password
    assert verify_password(password, h)
    assert not verify_password("wrong password", h)


def test_jwt_roundtrip_with_role():
    token = create_access_token("user-1234", role=UserRole.farmer.value)
    payload = decode_access_token(token)
    assert payload["sub"] == "user-1234"
    assert payload["role"] == "farmer"


def test_jwt_roundtrip_without_role():
    token = create_access_token("user-1234")
    payload = decode_access_token(token)
    assert payload["sub"] == "user-1234"
    assert "role" not in payload


def test_jwt_expiry_is_set():
    token = create_access_token("u-1", expires_minutes=1)
    payload = decode_access_token(token)
    assert "exp" in payload
    assert payload["exp"] > int(time.time())
