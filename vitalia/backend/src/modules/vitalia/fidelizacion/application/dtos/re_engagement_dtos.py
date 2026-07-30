# cap: fidelizacion.re-engagement
# story-origin: TBD
"""DTOs de re-engagement — capa API para fidelización vitalia.

Todos los campos PHI excluidos de las respuestas API (PII allowlist).
Dual filter tenant_id + clinic_id reforzado via parámetros de entrada.

downstream-regression-na: brand-local fidelizacion DTOs vitalia
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.modules.vitalia.fidelizacion.domain.value_objects.re_engagement_outcome import (
    ReEngagementOutcome,
)
from src.modules.vitalia.fidelizacion.domain.value_objects.re_engagement_pattern import (
    ReEngagementPattern,
)


class ReEngagementEventResponse(BaseModel):
    """Respuesta de un evento de re-engagement (sin PHI).

    PHI excluido: payload_phi. Solo se expone metadata de trazabilidad.
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
    retry_count: int
    created_at: datetime
    updated_at: datetime


class TriggerReEngagementRequest(BaseModel):
    """Solicitud para disparar un re-engagement manual."""

    patient_id: UUID
    clinic_id: UUID
    pattern: ReEngagementPattern
    template_id: str | None = None
    trigger_source: str = "manual"
    throttle_days: int = Field(default=7, ge=1, le=90)


class ListPatternsRequest(BaseModel):
    """Solicitud para listar eventos de re-engagement por patrón."""

    clinic_id: UUID
    pattern: ReEngagementPattern
    limit: int = Field(default=100, ge=1, le=500)


class PatternSummaryResponse(BaseModel):
    """Resumen de un patrón de re-engagement para un tenant+clínica."""

    pattern: ReEngagementPattern
    total_sent: int
    total_responded: int
    total_converted: int
    response_rate: float
    conversion_rate: float


class ProactiveReminderRequest(BaseModel):
    """Solicitud para enviar un recordatorio proactivo a un paciente."""

    patient_id: UUID
    clinic_id: UUID
    patient_phone: str
    patient_name: str
    template_id: str
    pattern: ReEngagementPattern
    channel: str = "whatsapp"
    idempotency_key: str | None = None
    throttle_days: int = Field(default=7, ge=1, le=90)


class ProactiveReminderResponse(BaseModel):
    """Resultado del envío de un recordatorio proactivo."""

    event_id: UUID
    patient_id: UUID
    status: str
    sent_at: datetime | None = None
    throttled: bool = False
    blocked_reason: str | None = None


class PausePatientRequest(BaseModel):
    """Solicitud para pausar re-engagement de un paciente."""

    patient_id: UUID
    clinic_id: UUID
    pause_until: datetime
    pause_reason: str | None = None
    paused_by_user_id: UUID | None = None


class PausePatientResponse(BaseModel):
    """Resultado de pausar el re-engagement de un paciente."""

    patient_id: UUID
    paused_until: datetime
    event_id: UUID


class ManualCallRequest(BaseModel):
    """Solicitud para registrar una llamada manual a un paciente."""

    patient_id: UUID
    clinic_id: UUID
    outcome: ReEngagementOutcome
    notes_plain: str | None = None
    called_by_user_id: UUID
    converted_to_appointment_id: UUID | None = None


class ManualCallResponse(BaseModel):
    """Resultado de registrar una llamada manual."""

    event_id: UUID
    patient_id: UUID
    outcome: ReEngagementOutcome
    recorded_at: datetime


# ---------------------------------------------------------------------------
# DTOs adicionales para T-7 (mark_external, mark_no_continue, activity_stream)
# ---------------------------------------------------------------------------


class MarkExternalRequest(BaseModel):
    """Solicitud para registrar que el paciente respondió fuera del canal automatizado."""

    patient_id: UUID
    clinic_id: UUID
    event_id: UUID | None = None
    comment: str | None = None
    converted_to_appointment_id: UUID | None = None
    recorded_by_user_id: UUID | None = None


class MarkExternalResponse(BaseModel):
    """Resultado de registrar respuesta externa del paciente."""

    event_id: UUID
    patient_id: UUID
    outcome: ReEngagementOutcome
    recorded_at: datetime


class MarkNoContinueRequest(BaseModel):
    """Solicitud para registrar que el paciente decidió no continuar el tratamiento."""

    patient_id: UUID
    clinic_id: UUID
    event_id: UUID | None = None
    reason: str | None = None
    recorded_by_user_id: UUID | None = None


class MarkNoContinueResponse(BaseModel):
    """Resultado de registrar decisión de no continuar del paciente."""

    event_id: UUID
    patient_id: UUID
    outcome: ReEngagementOutcome
    recorded_at: datetime


class ActivityStreamItem(BaseModel):
    """Item individual del Activity Stream de fidelización."""

    event_id: UUID
    patient_id: UUID
    event_type: str
    description: str
    occurred_at: datetime
    clinic_id: UUID


class ActivityStreamResponse(BaseModel):
    """Respuesta del Activity Stream de fidelización (poll 5s).

    Sin PHI per-patient — solo metadata de trazabilidad.
    """

    tenant_id: UUID
    clinic_id: UUID
    since: datetime | None = None
    items: list[ActivityStreamItem] = Field(default_factory=list)
    total: int = 0


class ReEngagementPatternListResponse(BaseModel):
    """Lista de resúmenes de patrones de re-engagement activos."""

    tenant_id: UUID
    clinic_id: UUID
    patterns: list[PatternSummaryResponse] = Field(default_factory=list)


class FidelizacionSummaryResponse(BaseModel):
    """Resumen de 5 KPIs de fidelización para el hero dashboard.

    Sin PHI per-patient — solo métricas agregadas.
    """

    tenant_id: UUID
    clinic_id: UUID
    snapshot_at: datetime

    # KPI 1: pacientes activos en seguimiento
    patients_in_followup: int

    # KPI 2: pacientes cerca de abandono (con gap alert)
    near_abandonment: int

    # KPI 3: tasa de retorno (re-engaged / total contacted en 30d)
    return_rate: float

    # KPI 4: cantidad de re-engagements exitosos en periodo
    re_engaged_count_period: int

    # KPI 5: NPS promedio (None si sin datos)
    nps_average: float | None = None
