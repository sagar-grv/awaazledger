"""Unit tests for phone normalization and demo user identity resolution."""

import pytest
from app.services.channel_identity_service import (
    normalize_phone_number,
    resolve_user_by_phone,
    get_demo_users_for_frontend,
)


def test_normalize_phone():
    assert normalize_phone_number("+919876543210") == "+919876543210"
    assert normalize_phone_number("919876543210") == "+919876543210"
    assert normalize_phone_number("9876543210") == "+919876543210"
    assert normalize_phone_number("+91 98765 43210") == "+919876543210"


def test_resolve_known_user():
    user = resolve_user_by_phone("+919876543210")
    assert user is not None
    assert user["user_id"] == 1
    assert user["name"] == "Rohit Verma"

    # Also works with 10-digit unnormalized form
    user_raw = resolve_user_by_phone("9876543211")
    assert user_raw is not None
    assert user_raw["user_id"] == 2
    assert user_raw["name"] == "Priya Sharma"


def test_resolve_unknown_phone():
    user = resolve_user_by_phone("+911111111111")
    assert user is None


def test_get_demo_users_list():
    users = get_demo_users_for_frontend()
    assert len(users) >= 5
    ids = [u["user_id"] for u in users]
    assert 1 in ids
    assert 2 in ids
