# cap: sales_agent.adrian-3-tools-mvp
# story-origin: TBD
"""ScreeningOutcome enum — domain layer (pure Python, no framework deps).

Values match the migration 021 CHECK constraint on ``lead_screening_events.outcome``:
  ('ok_proceed', 'derivar_doctor', 'derivar_emergencia', 'awaiting_response')

Per 03-arch-be.md § 1 + vitalia/.claude/rules/hipaa-lite.md:
  - ok_proceed         → cleared, proceed with payment link flow
  - derivar_doctor     → refer to medical professional for consultation
  - derivar_emergencia → urgent case, route to emergency care
  - awaiting_response  → patient has not yet answered screening questions

downstream-regression-na: brand-local enum for vitalia sales_agent screening
"""

from __future__ import annotations

from enum import StrEnum


class ScreeningOutcome(StrEnum):
    """Outcome of a medical screening assessment for a lead.

    Used by ScreeningQuestionsService to classify whether the lead is
    cleared for booking (OK_PROCEED) or requires special handling
    (refer to doctor / emergency / awaiting patient response).

    String values match DB CHECK constraint — MUST NOT be changed without
    an accompanying migration that updates the constraint.
    """

    OK_PROCEED = "ok_proceed"
    """Lead has no contraindications — proceed with payment link / booking flow."""

    DERIVAR_DOCTOR = "derivar_doctor"
    """Lead has risk factors requiring medical consultation before treatment."""

    DERIVAR_EMERGENCIA = "derivar_emergencia"
    """Lead has symptoms requiring immediate emergency care — abort booking."""

    AWAITING_RESPONSE = "awaiting_response"
    """Lead has not yet answered screening questions — conversation pending."""
