"""Service for mapping incoming channel phones to registered demo user identities."""

import os
import json
import re
from typing import Optional, Dict, Any, List
from app.core.config import settings

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
    """Resolves phone number to user metadata from phone_user_map.json or DEMO_WHATSAPP_NUMBER."""
    normalized = normalize_phone_number(phone)

    # 1. Check if configured in phone_user_map.json
    if os.path.exists(_DATA_PATH):
        try:
            with open(_DATA_PATH, "r", encoding="utf-8") as f:
                phone_map = json.load(f)
            mapped = phone_map.get(normalized)
            if mapped:
                return mapped
        except Exception:
            pass

    # 2. Check if DEMO_WHATSAPP_NUMBER environment variable is configured
    demo_env_phone = getattr(settings, "DEMO_WHATSAPP_NUMBER", None)
    if demo_env_phone:
        norm_demo = normalize_phone_number(demo_env_phone)
        if normalized == norm_demo:
            return {
                "user_id": 1,
                "name": "Rohit Sharma (Live Demo)",
                "paytm_id": "rohit@paytm",
                "language": "hi",
                "phone": normalized,
            }

    return None


def get_demo_users_for_frontend() -> List[Dict[str, Any]]:
    """Returns list of pre-seeded demo user profiles for the frontend simulator selector."""
    if not os.path.exists(_DATA_PATH):
        return []

    try:
        with open(_DATA_PATH, "r", encoding="utf-8") as f:
            phone_map = json.load(f)

        demo_users = []
        for phone, u in phone_map.items():
            demo_users.append({
                "user_id": u["user_id"],
                "phone": phone,
                "name": u["name"],
                "paytm_id": u["paytm_id"],
                "language": u.get("language", "hi"),
            })
        demo_users.sort(key=lambda x: x["user_id"])
        return demo_users
    except Exception:
        return []
