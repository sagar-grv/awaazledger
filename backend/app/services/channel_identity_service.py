"""Service for mapping incoming channel phones to registered demo user identities."""

import os
import json
import re
from typing import Optional, Dict, Any, List


_DATA_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "phone_user_map.json")
)


def normalize_phone_number(phone: str) -> str:
    """Normalizes Indian phone numbers to canonical E.164 +91XXXXXXXXXX format."""
    clean = re.sub(r"[\s\-\(\)]", "", str(phone or "").strip())
    if clean.startswith("+91") and len(clean) == 13 and clean[3:].isdigit():
        return clean
    if clean.startswith("91") and len(clean) == 12 and clean.isdigit():
        return f"+{clean}"
    if len(clean) == 10 and clean.isdigit():
        return f"+91{clean}"
    return clean


def resolve_user_by_phone(phone: str) -> Optional[Dict[str, Any]]:
    """Resolves phone number to user metadata from phone_user_map.json."""
    if not os.path.exists(_DATA_PATH):
        return None

    normalized = normalize_phone_number(phone)

    try:
        with open(_DATA_PATH, "r", encoding="utf-8") as f:
            phone_map = json.load(f)
        return phone_map.get(normalized)
    except Exception:
        return None


def get_demo_users_for_frontend() -> List[Dict[str, Any]]:
    """Returns list of pre-seeded demo user profiles for the frontend simulator selector."""
    if not os.path.exists(_DATA_PATH):
        return []

    try:
        with open(_DATA_PATH, "r", encoding="utf-8") as f:
            phone_map = json.load(f)

        demo_users = []
        for phone, info in phone_map.items():
            demo_users.append({
                "user_id": info["user_id"],
                "name": info["name"],
                "phone": phone,
                "paytm_id": info.get("paytm_id", ""),
                "language": info.get("language", "hi"),
            })
        return sorted(demo_users, key=lambda u: u["user_id"])
    except Exception:
        return []
