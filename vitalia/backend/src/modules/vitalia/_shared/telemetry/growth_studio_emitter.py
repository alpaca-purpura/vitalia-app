# cap: brand_studio.brand-studio-medical-sections
# story-origin: vitalia-fase2-s1-TBD
"""Growth Studio event emitter — brand-local UX/funnel telemetry.

Rule (03-arch § 3.3 + § 10):
  vitalia_growth_studio_event separates UX funnel events from agentic
  engine-level traces (LLM cost concerns). Fire-forget is ALLOWED
  here (unlike audit_log which is mandatory sync pre-response).

  7 critical events per 03-arch § 10:
    create_appointment, status_changed, appointment_detail_read,
    charge_completed, fiscal_emitted, notification_sent, reminder_sent

PHI safety: props sanitized via sanitize_phi_payload (vitalia brand-local wrapper) before insert.
Event names are snake_case identifiers (no PHI values in event_name).

Table: vitalia_growth_studio_event
  id UUID PK, tenant_id, clinic_id, user_id (nullable),
  event_name VARCHAR(64), props JSONB DEFAULT '{}', occurred_at TIMESTAMPTZ

Usage:
    emitter = GrowthStudioEmitter(session=async_session)
    await emitter.emit_event(
        event_type="create_appointment",
        tenant_id=tenant_id,
        clinic_id=clinic_id,
        entity_id=entity_uuid,
        props={"origin": "walk_in", "duration_minutes": 30},
    )
"""

from __future__ import annotations

import json
from typing import Any
from uuid import UUID

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()

# Whitelist of known event names for audit / arch-fitness verification.
# DO NOT inline PHI in event names. Values are snake_case identifiers only.
#
# F2-S1 core events (7 original):
#   create_appointment, status_changed, appointment_detail_read,
#   charge_completed, fiscal_emitted, notification_sent, reminder_sent
#
# F2-S7 lisa_marca_* events (13 new — per 03-arch § 10.2):
#   lisa_marca_viewed, lisa_marca_subsubtab_changed,
#   lisa_marca_identity_saved, lisa_marca_visuals_saved,
#   lisa_marca_personality_saved, lisa_marca_contact_saved,
#   lisa_marca_voice_warning_shown, lisa_marca_voice_warning_overridden,
#   lisa_marca_logo_uploaded, lisa_marca_logo_oversized,
#   lisa_marca_extract_website_clicked, lisa_marca_team_preview_clicked,
#   lisa_marca_clinic_config_edit_clicked,
#   lisa_marca_autosave_failed, lisa_marca_trust_signal_added
#
# Arch test `test_growth_studio_event_no_phi.py` validates this constant.
_KNOWN_EVENT_NAMES: frozenset[str] = frozenset(
    {
        # F2-S1 core scheduling events
        "create_appointment",
        "status_changed",
        "appointment_detail_read",
        "charge_completed",
        "fiscal_emitted",
        "notification_sent",
        "reminder_sent",
        # F2-S7 lisa_marca_* brand config events
        "lisa_marca_viewed",
        "lisa_marca_subsubtab_changed",
        "lisa_marca_identity_saved",
        "lisa_marca_visuals_saved",
        "lisa_marca_personality_saved",
        "lisa_marca_contact_saved",
        "lisa_marca_voice_warning_shown",
        "lisa_marca_voice_warning_overridden",
        "lisa_marca_logo_uploaded",
        "lisa_marca_logo_oversized",
        "lisa_marca_extract_website_clicked",
        "lisa_marca_team_preview_clicked",
        "lisa_marca_clinic_config_edit_clicked",
        "lisa_marca_autosave_failed",
        "lisa_marca_trust_signal_added",
        # F2-S8 lisa_staff_* doctor events (T-BE-1)
        "lisa_staff_doctor_created",
        "lisa_staff_doctor_updated",
        "lisa_staff_doctor_deactivated",
        "lisa_staff_doctor_viewed",
        # T-BE-2 adrian_embudo events (vitalia-fase2-adrian-embudo)
        "embudo_stage_changed",
        "embudo_lead_created",
        "embudo_lead_reactivated",
        "embudo_lead_frozen",
    }
)


class GrowthStudioEmitter:
    """Async emitter for Vitalia brand UX/funnel telemetry events.

    Fire-forget: failures are logged at WARNING level but do NOT propagate.
    PHI sanitization: applied before writing props to DB.
    """

    def __init__(self, *, session: AsyncSession) -> None:
        """Initialize GrowthStudioEmitter.

        Args:
            session: Async SQLAlchemy session (from FastAPI DI).
        """
        self._session = session

    async def emit_event(
        self,
        *,
        event_type: str,
        tenant_id: UUID,
        clinic_id: UUID | None = None,
        entity_id: UUID | None = None,
        user_id: UUID | None = None,
        props: dict[str, Any] | None = None,
    ) -> None:
        """Emit a growth studio event (fire-forget).

        PHI safety: props dict is sanitized via sanitize_phi_payload (vitalia
        brand-local wrapper) before insertion. PHI fields (name, dni, phone, email)
        are stripped.

        Args:
            event_type: Snake_case event identifier (e.g. 'create_appointment').
                Max 64 chars. Must NOT contain PHI values.
            tenant_id: Root tenant UUID.
            clinic_id: Clinic UUID (optional for tenant-level events).
            entity_id: Primary entity UUID (entity_uuid, payment_id, etc.)
                stored as a prop keyed 'entity_id'. Not stored as FK column.
            user_id: Actor user UUID (optional for system-triggered events).
            props: Additional event metadata. PHI fields auto-stripped.
                Example: {"origin": "walk_in", "duration_minutes": 30}

        Note:
            Failures are swallowed + logged at WARNING. Never propagates.
        """
        try:
            from src.modules.vitalia.compliance.application.compliance_service_adapter import (  # noqa: PLC0415
                sanitize_phi_payload,
            )

            # Build props dict (PHI-safe)
            raw_props: dict[str, Any] = dict(props or {})
            if entity_id is not None:
                raw_props["entity_id"] = str(entity_id)

            # sanitize_phi_payload: engine generic PII redaction + 22 vitalia PHI fields
            sanitized = sanitize_phi_payload(raw_props)

            await self._session.execute(
                text(
                    """
                    INSERT INTO vitalia_growth_studio_event
                        (id, tenant_id, clinic_id, user_id, event_name, props, occurred_at)
                    VALUES
                        (gen_random_uuid(), :tenant_id, :clinic_id, :user_id,
                         :event_name, CAST(:props AS jsonb), NOW())
                    """
                ),
                {
                    "tenant_id": str(tenant_id),
                    "clinic_id": str(clinic_id) if clinic_id else None,
                    "user_id": str(user_id) if user_id else None,
                    "event_name": event_type[:64],
                    "props": json.dumps(sanitized),
                },
            )

            logger.debug(
                "growth_studio_event_emitted",
                event_type=event_type,
                tenant_id=str(tenant_id),
            )

        except Exception as exc:  # noqa: BLE001
            # Fire-forget: log but never propagate (contrast with audit_log which propagates)
            logger.warning(
                "growth_studio_emit_failed",
                event_type=event_type,
                tenant_id=str(tenant_id),
                error=str(exc),
            )
