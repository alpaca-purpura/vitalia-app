# cap: scheduling.mateo-agenda
# story-origin: vitalia-fase2-s1-TBD
"""Notify API DTOs — template-only WhatsApp notification for Vitalia scheduling.

Per 03-arch § 4 (SendNotificationRequestDTO) + hipaa-lite.md:
  - template_id ONLY — no free-text body (PHI leakage risk in channel body).
  - channel is Literal["whatsapp"] — only pre-approved channel in F2-S1.
  - scheduled_for: optional datetime (UTC) for future-scheduled reminders.
  - locale: BCP-47 locale string for template localization (es-PE, es-AR, es-MX).
  - response_model= is MANDATORY on routes (arch test enforces).

downstream-regression-na: brand-local DTO layer for vitalia scheduling notify API
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------------------------
# Locale enum (BCP-47 subset — LatAm Spanish variants)
# ---------------------------------------------------------------------------

LocaleCode = Literal["es-PE", "es-AR", "es-MX", "es-CO", "es-CL", "es-US", "es"]
"""BCP-47 locale codes for template localization.

Used by the WhatsApp template catalog to select the correct translation.
Default: 'es' (generic Spanish neutro LatAm).
"""

# ---------------------------------------------------------------------------
# Request DTO
# ---------------------------------------------------------------------------


class SendNotificationRequestDTO(BaseModel):
    """Request body for POST /api/v1/scheduling/appointments/{id}/notify.

    HIPAA-lite constraints:
      - template_id required and non-empty (template-only rule — Q15 cement).
        Free-text body is PROHIBITED: PHI risk in channel transmission.
      - channel is Literal["whatsapp"] — only channel supported in F2-S1.
        Other channels (SMS, email_plaintext) are BLOCKED per hipaa-lite.md
        (unencrypted channels ban). portal_secure and https_api added in F2-Sx.
      - scheduled_for is optional UTC datetime for future delivery.
        None = send immediately. ISO-8601 UTC expected from FE.
      - locale is optional BCP-47 code for template localization.
        Defaults to 'es' (generic Spanish neutro LatAm) if not provided.

    Validation:
      - template_id: min_length=1, max_length=64 (per 03-arch § 4).
      - extra="forbid": rejects unknown keys (no PHI body injection).

    Example (valid):
        {
            "template_id": "recordatorio_cita_1d",
            "channel": "whatsapp",
            "scheduled_for": null,
            "locale": "es-PE"
        }

    Example (invalid — free text attempt):
        {
            "template_id": "",   # → FreeTextNotificationError → 422
            "channel": "whatsapp"
        }
    """

    model_config = ConfigDict(extra="forbid")

    template_id: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description=(
            "Pre-approved template identifier. REQUIRED and non-empty. "
            "Free-text body is PROHIBITED (HIPAA-lite PHI leakage prevention). "
            "Example: 'recordatorio_cita_1d', 'confirma_asistencia_24h', 'reagendar_opciones'."
        ),
    )
    channel: Literal["whatsapp"] = Field(
        "whatsapp",
        description=(
            "Outbound channel. F2-S1 supports 'whatsapp' only. "
            "SMS and email_plaintext are blocked per HIPAA-lite. "
            "ComplianceService validates channel before dispatch."
        ),
    )
    scheduled_for: datetime | None = Field(
        None,
        description=(
            "Optional UTC datetime for scheduled delivery. "
            "None = send immediately (default). "
            "ISO-8601 UTC format required when provided."
        ),
    )
    locale: LocaleCode = Field(
        "es",
        description=(
            "BCP-47 locale code for template language selection. "
            "Defaults to 'es' (Spanish neutro LatAm). "
            "Supported: es-PE, es-AR, es-MX, es-CO, es-CL, es-US, es."
        ),
    )


# ---------------------------------------------------------------------------
# Response DTOs
# ---------------------------------------------------------------------------


class NotificationSentResponse(BaseModel):
    """Response DTO for successful notification dispatch.

    Returns status="sent" + template_id echo for FE toast feedback.
    PHI fields (patient name, phone) are NEVER included in this response.
    The response_model enforces PII allowlist boundary.

    Per 03-arch § 5.1 routes table:
      POST /api/v1/scheduling/appointments/{id}/notify → response_model=NotificationSentResponse
    """

    model_config = ConfigDict(from_attributes=True)

    status: Literal["sent"] = "sent"
    template_id: str = Field(
        ...,
        description="Echo of the template_id dispatched (audit reference, no PHI).",
    )
    channel: str = Field(
        ...,
        description="Channel used for dispatch.",
    )


class NotificationBlockedResponse(BaseModel):
    """Response DTO when ComplianceService blocks the notification (422).

    Returned when VitaliaComplianceAdapter.validate_outbound_message raises
    BlockedChannelError. Maps to HTTP 422 Unprocessable Entity.

    Per hipaa-lite.md: unencrypted channel blocked = PHI protection active.
    The response body contains the block reason for FE toast display.
    PHI fields are NOT included — block_reason is a safe audit message.
    """

    model_config = ConfigDict(from_attributes=True)

    status: Literal["blocked"] = "blocked"
    block_reason: str = Field(
        ...,
        description="Human-readable block reason (no PHI). Shown in FE toast.",
    )
