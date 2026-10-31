"""Optional Visual Tracker Card image generator for WhatsApp media sharing."""

import os
import logging
from typing import Optional, Dict, Any
from app.core.config import settings

logger = logging.getLogger(__name__)


def generate_tracker_image(dispute_code: str, tracker_data: Dict[str, Any]) -> Optional[str]:
    """Generates a branded PNG tracker card using Pillow if enabled."""
    if not settings.ENABLE_TRACKER_IMAGE:
        return None

    try:
        from PIL import Image, ImageDraw, ImageFont

        width, height = 800, 500
        img = Image.new("RGB", (width, height), color=(11, 44, 88))  # Paytm Navy
        draw = ImageDraw.Draw(img)

        # Header
        draw.text((40, 30), "Paytm AwaazLedger — Live Dispute Tracker", fill=(0, 186, 242))

        # Box
        draw.rectangle([(40, 80), (760, 440)], fill=(255, 255, 255))

        # Dispute Info
        draw.text((60, 100), f"Dispute Code: {dispute_code}", fill=(20, 20, 20))
        draw.text((60, 130), f"Status: {tracker_data.get('status', 'PENDING')}", fill=(0, 150, 0))
        draw.text((60, 160), f"Risk Level: {tracker_data.get('risk_level', 'LOW')}", fill=(50, 50, 50))

        # Checkpoints
        y = 210
        draw.text((60, y), "Multi-Node Verification Trace:", fill=(11, 44, 88))
        y += 30
        nodes = tracker_data.get("nodes", [])
        for node in nodes[:5]:
            status_symbol = "✓" if node.get("status") in ("DONE", "SUCCESS") else "⏳"
            line = f"{status_symbol} {node.get('name')}: {node.get('details', '')}"
            draw.text((80, y), line[:70], fill=(60, 60, 60))
            y += 28

        # Save image
        out_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "tmp", "tracker"))
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, f"{dispute_code}.png")
        img.save(out_path)

        return out_path
    except Exception as e:
        logger.warning(f"Tracker image generation failed: {e}")
        return None
