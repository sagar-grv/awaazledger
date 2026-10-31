"""Unit tests for OCR screenshot ingestion and field parsing."""

from app.services.ocr_service import extract_ocr_from_image


def test_ocr_valid_receipt_scenario():
    filename = "screenshot_scn01_valid.jpg"
    content = b"MOCK_JPEG_BYTES"
    res = extract_ocr_from_image(filename, content)

    ocr_json = res["ocr_json"]
    assert ocr_json["utr"] == "987654321012"
    assert ocr_json["amount"] == 450.0
    assert ocr_json["bank"] == "HDFC"
    assert res["entities"].utr == "987654321012"
    assert res["entities"].amount == 450.0


def test_ocr_fraud_scenario():
    filename = "screenshot_scn05_fraud.jpg"
    content = b"MOCK_JPEG_BYTES"
    res = extract_ocr_from_image(filename, content)

    assert res["entities"].utr == "000000000000"
    assert res["entities"].amount == 1999.0


def test_ocr_unknown_fallback():
    filename = "unrelated_photo.jpg"
    content = b""
    res = extract_ocr_from_image(filename, content)

    assert res["entities"].utr is None
    assert res["entities"].confidence <= 0.20
    assert "utr" in res["entities"].missing_fields
