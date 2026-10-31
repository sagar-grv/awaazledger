"""Unit tests for OCR safe fallback behavior."""

import pytest
from app.services.ocr_service import extract_ocr_from_image
from app.core.config import settings


def test_ocr_fallback_when_disabled(monkeypatch):
    """Verifies mock OCR fallback when real OCR is disabled."""
    monkeypatch.setattr(settings, "ENABLE_OCR_REAL", False)

    res = extract_ocr_from_image("screenshot_scn01_valid.jpg", b"MOCK_JPEG_BYTES")
    assert res["source"] in ("MOCK_OCR_FALLBACK", "MOCK_FILENAME_MATCH")
    assert res["entities"].utr == "987654321012"
    assert res["entities"].amount == 450.0
