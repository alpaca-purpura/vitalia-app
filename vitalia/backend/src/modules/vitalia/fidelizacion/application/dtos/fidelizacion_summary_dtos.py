# cap: fidelizacion.re-engagement
# story-origin: TBD
"""DTOs de resumen de fidelización — capa API para fidelización vitalia.

Agregados de estado de fidelización para dashboards y reportes.
Sin PHI per-paciente.

downstream-regression-na: brand-local fidelizacion summary DTOs vitalia
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from src.modules.vitalia.fidelizacion.domain.entities.treatment_plan import TreatmentPlanStatus


class TreatmentPlanSummaryResponse(BaseModel):
    """Resumen de un plan de tratamiento (sin PHI — notes excluido).

    PHI excluido: notes (campo cifrado pgcrypto).
    Solo se exponen estado y métricas del plan.
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
    last_session_at: datetime | None = None
    paused_until: datetime | None = None
    pause_reason: str | None = None
    created_at: datetime
    updated_at: datetime


class FidelizacionDashboardResponse(BaseModel):
    """Resumen del dashboard de fidelización para un tenant+clínica.

    Estadísticas agregadas para operaciones de la clínica.
    Sin PHI per-paciente.
    """

    tenant_id: UUID
    clinic_id: UUID
    snapshot_at: datetime

    # Tratamientos activos
    active_treatment_plans: int
    plans_with_gap: int
    plans_overdue_for_followup: int

    # Re-engagement enviados (últimos 30 días)
    re_engagements_sent_30d: int
    re_engagements_by_pattern: dict[str, int]

    # NPS
    nps_score_30d: float | None = None
    detractors_pending_attention: int

    # Estado opt-out
    opted_out_patients: int


class OptOutPatientResponse(BaseModel):
    """Respuesta de dar de baja a un paciente del sistema de fidelización."""

    patient_id: UUID
    clinic_id: UUID
    opted_out_at: datetime
    pending_events_cancelled: int
    event_id: UUID
