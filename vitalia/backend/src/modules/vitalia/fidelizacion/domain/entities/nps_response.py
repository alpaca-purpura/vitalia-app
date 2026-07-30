# cap: patients.nps-tracking
# story-origin: TBD
"""Entidad de dominio: NPSResponse (Respuesta NPS del Paciente).

PHI — comment_encrypted contiene comentario libre del paciente (pgcrypto BYTEA).
Dual filter obligatorio: tenant_id + clinic_id (HIPAA-lite vitalia).
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator

from src.modules.vitalia.fidelizacion.domain.value_objects.nps_band import NPSBand


class NPSResponse(BaseModel):
    """Respuesta NPS de un paciente tras una cita o tratamiento.

    Aislamiento: tenant_id + clinic_id (HIPAA-lite dual filter).
    Score validado 0-10. Band deriva del score via NPSBand.from_score().
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    clinic_id: UUID
    patient_id: UUID

    appointment_id: UUID | None = None
    score: int
    band: NPSBand

    # PHI cifrado — comentario libre del paciente (pgcrypto BYTEA, columna 'comment')
    comment: bytes | None = None

    source: str
    trigger_re_engagement_event_id: UUID | None = None
    responded_at: datetime
    tagged_in_inbox: bool = False
    audit_log_id: UUID | None = None

    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None

    @field_validator("score")
    @classmethod
    def validate_score_range(cls, v: int) -> int:
        """Score NPS debe estar entre 0 y 10."""
        if not (0 <= v <= 10):
            raise ValueError(f"NPS score debe estar entre 0 y 10, recibido: {v}")
        return v
