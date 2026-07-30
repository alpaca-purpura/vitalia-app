# cap: scheduling.mateo-agenda
"""Shared PHI name masking for the agenda repos (grid + detail).

The patient name is decrypted server-side (pgp_sym_decrypt + KEK) and masked to
"M. López" before the dict ever leaves the repo; the raw decrypted name is stripped.
Single home so grid + detail mask identically (anti-duplication).
"""

from __future__ import annotations

from typing import Any


def mask_name(full: str | None) -> str:
    """Mask a decrypted patient name → "M. López" (first initial + last surname). Empty → '—'."""
    if not full or not full.strip():
        return "—"
    parts = full.strip().split()
    initial = parts[0][0].upper()
    surname = parts[-1] if len(parts) > 1 else ""
    return f"{initial}. {surname}".strip()


def apply_name_mask(row: dict[str, Any]) -> dict[str, Any]:
    """Replace raw_patient_name with patient_name_masked + drop the raw key (PHI safety)."""
    row["patient_name_masked"] = mask_name(row.pop("raw_patient_name", None))
    return row
