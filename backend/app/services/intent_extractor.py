"""Deterministic natural language and regex intent/entity extractor for Indian UPI dispute channels."""

import re
from typing import Optional, List
from app.schemas.ingest import IntentType, ExtractedEntity


_MARATHI_DEVANAGARI = ["झाले", "नाही", "मिळाले", "मिळाला", "केले", "आहे", "मधून", "रुपये चे"]
_MARATHI_LATIN = ["jhale", "nahi", "mila nahi", "kele", "ahe", "madhun", "rupaya che", "dukan"]
_HINDI_LATIN = ["bhaiya", "kat gaya", "kat gaye", "kata", "mera", "meri", "paisa", "rupaye", "rupe", "nahi mila", "dukandar", "ho gaya", "debit ho"]
_ENGLISH_WORDS = ["paid", "payment", "flight", "ticket", "merchant", "received", "receive", "deducted", "failed", "pending", "account", "transaction", "bank"]


def detect_language(text: str, default_language: Optional[str] = None) -> str:
    """Detects primary language: Hindi (hi), Marathi (mr), or English (en)."""
    text_lower = text.lower()

    # Check Devanagari script presence
    has_devanagari = bool(re.search(r"[\u0900-\u097F]", text))
    if has_devanagari:
        for m_token in _MARATHI_DEVANAGARI:
            if m_token in text:
                return "mr"
        return "hi"

    # Check Latin script tokens
    for m_token in _MARATHI_LATIN:
        if m_token in text_lower:
            return "mr"

    for h_token in _HINDI_LATIN:
        if h_token in text_lower:
            return "hi"

    # Check English
    en_matches = sum(1 for w in _ENGLISH_WORDS if re.search(rf"\b{w}\b", text_lower))
    if en_matches >= 2:
        return "en"

    return default_language or "hi"


def extract_utr(text: str) -> Optional[str]:
    """Finds 12 to 20 digit numeric reference strings, prioritizing 12-digit UPI UTRs."""
    # First search for explicit UTR pattern e.g. "UTR 987654321012" or "UTR: 9876..."
    explicit_match = re.search(r"\bUTR[\s:\-=]*(\d{12,20})\b", text, re.IGNORECASE)
    if explicit_match:
        return explicit_match.group(1)

    # General search for 12-20 digit standalone numeric strings
    matches = re.findall(r"\b\d{12,20}\b", text)
    if not matches:
        return None

    # Filter out potential timestamps like 20261031101500 if there's a 12-digit alternative
    twelve_digits = [m for m in matches if len(m) == 12]
    if twelve_digits:
        return twelve_digits[0]

    return matches[0]


def extract_amount(text: str) -> Optional[float]:
    """Extracts numeric monetary amount from text in standard Indian currency notations."""
    patterns = [
        # ₹18,500, ₹450, ₹ 450, ₹450.50
        r"₹\s*([0-9]+(?:,[0-9]+)*(?:\.[0-9]{1,2})?)",
        # Rs 18,500, Rs. 450, INR 18,500
        r"(?:Rs\.?|INR)\s*([0-9]+(?:,[0-9]+)*(?:\.[0-9]{1,2})?)",
        # 18,500 rupees, 450 rupaye, 450 rupye, 450 rs
        r"([0-9]+(?:,[0-9]+)*(?:\.[0-9]{1,2})?)\s*(?:rupees|rupee|rupaye|rupye|rupya|rs\.?)\b",
        # 18,500 रुपये, 450 रुपए, 450 रु
        r"([0-9]+(?:,[0-9]+)*(?:\.[0-9]{1,2})?)\s*(?:रुपये|रुपए|रु)",
        # 18,500
        r"\b([0-9]{1,3}(?:,[0-9]{2,3})+)\b",
    ]

    for pat in patterns:
        match = re.search(pat, text, re.IGNORECASE)
        if match:
            raw_val = match.group(1).replace(",", "")
            try:
                return float(raw_val)
            except ValueError:
                continue

    return None


def detect_intent(text: str) -> IntentType:
    """Classifies dispute intent using keyword rules."""
    text_lower = text.lower()

    fraud_tokens = ["fraud", "scam", "fake", "cheating", "dhokhadhadi", "धोखा", "धोखेबाजी"]
    if any(t in text_lower for t in fraud_tokens):
        return IntentType.FRAUD_REPORT

    human_tokens = ["human", "agent", "operator", "talk to person", "customer care", "representative", "बात करनी", "एजेंट"]
    if any(t in text_lower for t in human_tokens):
        return IntentType.HUMAN_REQUEST

    receipt_tokens = ["receipt", "merchant receipt", "shopkeeper proof", "proof", "parchi", "रसीद", "पावती"]
    if any(t in text_lower for t in receipt_tokens):
        return IntentType.MERCHANT_RECEIPT_HELP

    status_tokens = ["status", "check status", "where is my money", "kahan gaya", "kaha gaya", "update", "स्थिति", "का क्या हुआ"]
    if any(t in text_lower for t in status_tokens):
        return IntentType.STATUS_CHECK

    pending_dispute_tokens = [
        "pending", "not received", "merchant ko nahi mila", "dukandar ko nahi mila",
        "credit nahi hua", "kat gaya", "kat gaye", "kata", "debit ho gaya", "payment fail",
        "money deducted", "paisa katta", "paisa kat", "कट गया", "जमा नहीं", "मिल नहीं रहा",
        "कटले", "झाले नाही", "मिळाले नाही", "pending दिख", "pending dikh", "deducted",
        "did not receive", "failed", "काट लिए",
    ]
    if any(t in text_lower for t in pending_dispute_tokens):
        return IntentType.UPI_PENDING_DISPUTE

    return IntentType.UNKNOWN


def extract_entities_from_text(text: str, default_language: Optional[str] = None) -> ExtractedEntity:
    """Extracts structured entities, intent, confidence, and missing fields from unconstrained input."""
    clean_text = (text or "").strip()
    utr = extract_utr(clean_text)
    amount = extract_amount(clean_text)
    intent = detect_intent(clean_text)
    language = detect_language(clean_text, default_language)

    # Calculate Confidence Score
    if utr and amount:
        confidence = 0.95
    elif utr:
        confidence = 0.80
    elif amount:
        confidence = 0.60
    elif intent != IntentType.UNKNOWN:
        confidence = 0.40
    else:
        confidence = 0.10

    # Determine Missing Fields
    missing_fields: List[str] = []
    if not utr:
        missing_fields.append("utr")
    if amount is None:
        missing_fields.append("amount")
    if confidence < 0.50:
        missing_fields.append("clearer_evidence")

    return ExtractedEntity(
        utr=utr,
        amount=amount,
        currency="INR",
        language=language,
        intent=intent,
        confidence=confidence,
        missing_fields=missing_fields,
        raw_text=clean_text,
    )
