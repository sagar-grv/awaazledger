"""OCR extraction service supporting Tesseract and deterministic hackathon mock fallbacks."""

import os
import io
import json
import logging
from typing import Dict, Any, List
from app.core.config import settings
from app.schemas.ingest import ExtractedEntity, IntentType
from app.services.intent_extractor import extract_entities_from_text

logger = logging.getLogger(__name__)

_OCR_DATA_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "mock_ocr_outputs.json")
)


class AwaitableDict(dict):
    """Dictionary that can be used directly or awaited in async contexts."""

    def __await__(self):
        async def _coro():
            return self
        return _coro().__await__()


def extract_ocr_from_image(
    filename: str,
    content: bytes,
) -> AwaitableDict:
    """Extracts payment receipt fields and entities from screenshot images."""
    source = "MOCK_OCR_FALLBACK"
    raw_text = ""
    utr = None
    amount = None
    bank = None
    merchant_name = None
    confidence = 0.20

    # 1. Attempt optional real Tesseract OCR if enabled
    if settings.ENABLE_OCR_REAL and content:
        try:
            from PIL import Image
            import pytesseract

            img = Image.open(io.BytesIO(content))
            extracted_text = pytesseract.image_to_string(img)
            if extracted_text and extracted_text.strip():
                raw_text = extracted_text.strip()
                parsed_entities = extract_entities_from_text(raw_text)
                if parsed_entities.utr or parsed_entities.amount:
                    source = "TESSERACT"
                    utr = parsed_entities.utr
                    amount = parsed_entities.amount
                    bank = parsed_entities.bank
                    merchant_name = parsed_entities.merchant_name
                    confidence = 0.88
        except Exception as e:
            logger.warning(f"Real OCR failed: {e}. Falling back to deterministic mock.")

    # 2. Fallback to mock filename matching if not extracted via Tesseract
    if source != "TESSERACT":
        filename_lower = (filename or "").lower()

        ocr_map = {}
        if os.path.exists(_OCR_DATA_PATH):
            try:
                with open(_OCR_DATA_PATH, "r", encoding="utf-8") as f:
                    ocr_map = json.load(f)
            except Exception:
                ocr_map = {}

        matched_ocr = None
        for key, val in ocr_map.items():
            if key.lower() in filename_lower:
                matched_ocr = val
                break

        if matched_ocr:
            source = "MOCK_FILENAME_MATCH"
            utr = matched_ocr.get("utr")
            amount = matched_ocr.get("amount")
            bank = matched_ocr.get("bank")
            merchant_name = matched_ocr.get("merchant_name")
            confidence = matched_ocr.get("confidence", 0.95)
            raw_text = matched_ocr.get("raw_text", "")
        else:
            source = "MOCK_OCR_FALLBACK"
            confidence = 0.20

    missing: List[str] = []
    if not utr:
        missing.append("utr")
    if not amount:
        missing.append("amount")

    entities = ExtractedEntity(
        utr=utr,
        amount=amount,
        bank=bank,
        merchant_name=merchant_name,
        confidence=confidence,
        intent=IntentType.UPI_PENDING_DISPUTE,
        raw_text=raw_text,
        missing_fields=missing,
    )

    return AwaitableDict({
        "raw_text": raw_text,
        "ocr_json": {
            "utr": utr,
            "amount": amount,
            "bank": bank,
            "merchant_name": merchant_name,
            "confidence": confidence,
        },
        "entities": entities,
        "source": source,
    })
