"""Security utilities and authentication placeholders."""

import hashlib
import secrets
from typing import Optional


def hash_sensitive_identifier(val: str) -> str:
    """Hashes sensitive data like VPA or account numbers for audit masking."""
    return hashlib.sha256(val.encode()).hexdigest()[:16]


def generate_token(nbytes: int = 16) -> str:
    """Generates a secure random hex token."""
    return secrets.token_hex(nbytes)


def verify_api_key(provided_key: Optional[str], expected_key: Optional[str]) -> bool:
    """Simple API key verification placeholder."""
    if not expected_key:
        return True
    return provided_key == expected_key
