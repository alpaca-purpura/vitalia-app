# cap: __shared__
# story-origin: TBD
"""Amount bucket utility — privacy-preserving monetary range bucketing for telemetry.

Rule (03-arch § 10 + hipaa-lite.md):
  Monetary amounts MUST NOT be stored as exact values in growth_studio_event props.
  Use range buckets to prevent re-identification via payment history correlation.

  Standard buckets (in cents, currency-agnostic):
    - < 500_00     → "low"       (bajo: menos de 500 unidades)
    - < 2000_00    → "medium"    (medio: 500-1999 unidades)
    - < 10000_00   → "high"      (alto: 2000-9999 unidades)
    - ≥ 10000_00   → "very_high" (muy alto: 10000+ unidades)

Usage:
    from src.modules.vitalia._shared.telemetry.amount_bucket import bucket_amount

    bucket = bucket_amount(15000)  # → "low" (150.00 in main currency unit)
    bucket = bucket_amount(150000) # → "medium" (1500.00 in main currency unit)
"""

from __future__ import annotations

__all__ = ["bucket_amount"]


def bucket_amount(amount_cents: int) -> str:
    """Map an amount in cents to a privacy-preserving range bucket.

    Avoids storing exact amounts in telemetry to prevent re-identification.
    Currency-agnostic: buckets defined in terms of cents regardless of ISO code.

    Args:
        amount_cents: Monetary amount in smallest currency unit (cents/centavos).
            Must be non-negative.

    Returns:
        One of: "low" | "medium" | "high" | "very_high"

    Examples:
        bucket_amount(0)         → "low"
        bucket_amount(49_999)    → "low"       (< 500.00)
        bucket_amount(50_000)    → "medium"    (= 500.00)
        bucket_amount(199_999)   → "medium"    (< 2000.00)
        bucket_amount(200_000)   → "high"      (= 2000.00)
        bucket_amount(999_999)   → "high"      (< 10000.00)
        bucket_amount(1_000_000) → "very_high" (= 10000.00)
    """
    if amount_cents < 50_000:
        return "low"
    if amount_cents < 200_000:
        return "medium"
    if amount_cents < 1_000_000:
        return "high"
    return "very_high"
