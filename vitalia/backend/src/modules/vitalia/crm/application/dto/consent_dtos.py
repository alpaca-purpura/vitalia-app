# cap: crm.crm-consent-optout
# story-origin: TBD
"""Consent DTOs — opt-out and marketing opt-in request/response models.

PII allowlist enforced via response_model= on all routes (tessl pii-sanitisation).
No PHI fields beyond patient_id and consent flags are included.

Per vitalia/.claude/rules/hipaa-lite.md: PHI fields MUST NOT appear in
response bodies accessible to unauthorized roles. These DTOs expose only
consent state — no clinical data.
"""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict


class OptOutRequest(BaseModel):
    """Request body for POST /patients/{id}/opt-out.

    The reason field is stored in audit log (payload_redacted) but NOT
    returned in the response to prevent PHI leakage in logs.
    """

    model_config = ConfigDict(from_attributes=True)

    reason: str


class OptOutResponse(BaseModel):
    """Response for POST /patients/{id}/opt-out.

    Returns only non-PHI fields: patient_id (UUID) + consent state + message.
    """

    model_config = ConfigDict(from_attributes=True)

    patient_id: UUID
    opted_out: bool
    message: str


class MarketingOptInRequest(BaseModel):
    """Request body for PATCH /patients/{id}/marketing-opt-in."""

    model_config = ConfigDict(from_attributes=True)

    opt_in: bool


class MarketingOptInResponse(BaseModel):
    """Response for PATCH /patients/{id}/marketing-opt-in.

    Returns consent state confirmation. No PHI exposed.
    """

    model_config = ConfigDict(from_attributes=True)

    patient_id: UUID
    marketing_opt_in: bool
    message: str
