# cap: fidelizacion.re-engagement
# story-origin: TBD
"""Entidad de dominio: ReEngagementEvent (Evento de Re-engagement).

PHI — payload_phi contiene datos sensibles cifrados (pgcrypto BYTEA).
Dual filter obligatorio: tenant_id + clinic_id (HIPAA-lite vitalia).
Tabla particionada por trigger_at (migración 021).
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from src.modules.vitalia.fidelizacion.domain.value_objects.re_engagement_outcome import (
    ReEngagementOutcome,
)
from src.modules.vitalia.fidelizacion.domain.value_objects.re_engagement_pattern import (
    ReEngagementPattern,
)


class ReEngagementEvent(BaseModel):
    """Evento de re-engagement disparado hacia un paciente.

    Registra cada intento de contacto (WhatsApp, email, SMS) y su resultado.
    Aislamiento: tenant_id + clinic_id (HIPAA-lite dual filter).
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    clinic_id: UUID
    patient_id: UUID

    pattern: ReEngagementPattern
    trigger_source: str
    trigger_at: datetime

    template_id: str | None = None
    sent_at: datetime | None = None
    response_at: datetime | None = None
    outcome: ReEngagementOutcome | None = None
    converted_to_appointment_id: UUID | None = None
    audit_log_id: UUID | None = None

    # PHI cifrado — payload adicional del evento (pgcrypto BYTEA)
    payload_phi: bytes | None = None

    retry_count: int = 0
    last_error: str | None = None
    idempotency_key: str | None = None

    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None
