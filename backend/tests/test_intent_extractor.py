"""Unit tests for deterministic natural language and regex intent/entity extraction."""

import pytest
from app.services.intent_extractor import extract_entities_from_text
from app.schemas.ingest import IntentType


def test_extract_hindi_hinglish_utr_and_amount():
    text = "Bhaiya maine 450 rupees ka payment kiya, account se kat gaya lekin dukandar ko nahi mila. UTR 987654321012 hai."
    res = extract_entities_from_text(text)
    assert res.utr == "987654321012"
    assert res.amount == 450.0
    assert res.intent == IntentType.UPI_PENDING_DISPUTE
    assert res.confidence >= 0.90
    assert "utr" not in res.missing_fields
    assert "amount" not in res.missing_fields


def test_extract_english_with_currency_symbol():
    text = "I paid ₹18,500 for flight ticket but merchant did not receive. UTR 998877665544."
    res = extract_entities_from_text(text)
    assert res.utr == "998877665544"
    assert res.amount == 18500.0
    assert res.language == "en"
    assert res.intent == IntentType.UPI_PENDING_DISPUTE


def test_detect_missing_utr():
    text = "Mera paisa kat gaya 500 rupaye dukandar ko nahi mile please help."
    res = extract_entities_from_text(text)
    assert res.utr is None
    assert res.amount == 500.0
    assert "utr" in res.missing_fields
    assert res.confidence < 0.80


def test_detect_fraud_keywords():
    text = "Mere sath fraud hua hai, fake QR code scan karwaya aur 2000 rupaye kat liye. UTR 123456789012."
    res = extract_entities_from_text(text)
    assert res.intent == IntentType.FRAUD_REPORT


def test_detect_human_request_keywords():
    text = "I want to talk to an executive or human agent right now."
    res = extract_entities_from_text(text)
    assert res.intent == IntentType.HUMAN_REQUEST
