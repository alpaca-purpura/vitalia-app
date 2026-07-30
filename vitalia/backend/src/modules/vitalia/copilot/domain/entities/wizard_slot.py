# cap: copilot.valeria-wizard-onboarding-agentic
# story-origin: TBD
"""WizardSlot — frozen value object for onboarding wizard slot state.

Represents a single data slot captured during the Valeria onboarding wizard.
Immutable (frozen dataclass) — value object in DDD terms.

No PHI: wizard onboarding config data (clinic name, vertical, location, tone).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Union


@dataclass(frozen=True)
class WizardSlot:
    """Frozen value object representing a wizard slot's current state.

    Attributes:
        slot_id: Dot-notation identifier, e.g. "tenant.name", "brand.tone_default".
        value: Extracted or user-provided value. str, dict, or None (unfilled).
        confidence: LLM extraction confidence score 0.0–1.0.
        confirmed_at: UTC datetime when user confirmed the slot, None if pending.
        source: How the value was obtained — "extracted", "user_text", or "user_correction".
    """

    slot_id: str
    value: Union[str, dict, None]  # noqa: UP007 — Union kept for py3.9 compat in runtime
    confidence: float
    confirmed_at: datetime | None
    source: str
