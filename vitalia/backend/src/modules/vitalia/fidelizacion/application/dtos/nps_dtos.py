# cap: patients.nps-tracking
# story-origin: TBD
"""DTOs de NPS — capa API para fidelización vitalia.

PHI: comment (texto libre del paciente) excluido de respuestas API.
Solo se exponen score, band, y metadatos de trazabilidad.

downstream-regression-na: brand-local fidelizacion NPS DTOs vitalia
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.modules.vitalia.fidelizacion.domain.value_objects.nps_band import NPSBand


class NPSSubmitRequest(BaseModel):
    """Solicitud para registrar una respuesta NPS de un paciente."""

    patient_id: UUID
    clinic_id: UUID
    score: int = Field(ge=0, le=10)
    comment_plain: str | None = None
    appointment_id: UUID | None = None
    responded_via: str = "whatsapp"

    @field_validator("score")
    @classmethod
    def validate_score_range(cls, v: int) -> int:
        """Valida que el score NPS esté en el rango permitido (0-10)."""
        if v < 0 or v > 10:
            msg = f"Score NPS debe estar entre 0 y 10, recibido: {v}"
            raise ValueError(msg)
        return v


class NPSResponseResponse(BaseModel):
    """Respuesta de una encuesta NPS (sin PHI — comment excluido).

    PHI excluido: comment (texto libre del paciente cifrado con pgcrypto).
    Solo se exponen score, band, y metadatos de trazabilidad.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    clinic_id: UUID
    patient_id: UUID
    score: int
    band: NPSBand
    appointment_id: UUID | None = None
    responded_via: str
    responded_at: datetime
    tagged_in_inbox: bool
    created_at: datetime


class NPSSummaryResponse(BaseModel):
    """Resumen NPS agregado por tenant + clínica + periodo.

    NO incluye data per-patient para evitar PHI leak en endpoints no PHI.
    Estadísticas anónimas agregadas.
    """

    tenant_id: UUID
    clinic_id: UUID
    period_start: datetime
    period_end: datetime
    total_responses: int
    promoters: int
    passives: int
    detractors: int
    nps_score: float
    response_rate: float | None = None
    detractors_untagged: int = 0
