"""OCR client stub for payment receipt screenshots."""

from typing import Dict, Any


class OCRClient:
    """Extracts UPI transaction details (UTR, Amount, Timestamp) from screenshots."""

    def extract_receipt_data(self, image_bytes: bytes) -> Dict[str, Any]:
        """Placeholder OCR extraction."""
        return {
            "utr": "987654321012",
            "amount": 500.0,
            "timestamp": "2026-10-30T10:14:22Z",
            "payee_vpa": "kirana_store@paytm",
            "status_text": "Payment in Progress / Pending",
            "confidence": 0.96,
        }
