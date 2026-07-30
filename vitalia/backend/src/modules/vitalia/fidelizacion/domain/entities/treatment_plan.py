# cap: treatments.treatment-followup-workflow
# story-origin: TBD
"""Entidad de dominio: TreatmentPlan (Plan de Tratamiento).

PHI — contiene datos médicos sensibles (HIPAA-lite vitalia).
Dual filter obligatorio: tenant_id + clinic_id en todas las queries.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class TreatmentPlanStatus(StrEnum):
    """Estado del plan de tratamiento."""

    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"
    PAUSED = "paused"


class TreatmentPlan(BaseModel):
    """Plan de tratamiento multi-sesión de un paciente en una clínica.

    Campos PHI: notes_encrypted (bytes pgcrypto).
    Aislamiento: tenant_id + clinic_id (HIPAA-lite dual filter).
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    clinic_id: UUID
    patient_id: UUID

    offer_id: UUID | None = None
    doctor_id: UUID | None = None

    sessions_total: int
    sessions_completed: int
    next_session_due_at: datetime | None = None
    gap_alert_days: int | None = None
    status: TreatmentPlanStatus

    # PHI — almacenado cifrado vía pgcrypto (BYTEA en DB, columna 'notes')
    notes: bytes | None = None

    last_session_at: datetime | None = None
    paused_until: datetime | None = None
    pause_reason: str | None = None

    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None
