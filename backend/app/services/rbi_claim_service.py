"""RBI Turnaround Time (TAT) delay compensation service."""

from typing import Dict, Any
from datetime import datetime, timezone, timedelta


class RbiClaimService:
    """Calculates RBI auto-reversal delay compensation (₹100/day beyond T+1)."""

    def calculate_compensation(self, transaction_time: datetime) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        elapsed_days = (now - transaction_time).days
        breached_days = max(0, elapsed_days - 1)  # T+1 allowed
        penalty = breached_days * 100.0

        return {
            "breached": breached_days > 0,
            "days_delayed": breached_days,
            "compensation_inr": penalty,
        }
