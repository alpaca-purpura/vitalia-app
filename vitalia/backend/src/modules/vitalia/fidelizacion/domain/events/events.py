# cap: fidelizacion.re-engagement
# story-origin: TBD
"""Eventos de dominio del módulo fidelizacion (vitalia).

Subclases de DomainEvent (luana_core_platform). Emitidos via outbox pattern.
USE_OUTBOX_PATTERN_* = True (post 2026-04-30).

Patrón de herencia: DomainEvent es @dataclass con event_name como primer campo
requerido. Subclases son también @dataclass y definen campos adicionales con
defaults. Se crea cada evento llamando al constructor con los campos explícitos.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID

from luana_core_platform.domain.events import DomainEvent

# ─────────────────────────────────────────────
# Constantes event_name (SSoT)
# ─────────────────────────────────────────────

FIDELIZACION_RE_ENGAGEMENT_TRIGGERED = "vitalia.fidelizacion.re_engagement_triggered"
FIDELIZACION_NPS_SCORE_COLLECTED = "vitalia.fidelizacion.nps_score_collected"
FIDELIZACION_PATIENT_OPTED_OUT = "vitalia.fidelizacion.patient_opted_out"
FIDELIZACION_PATIENT_PAUSED_RE_ENGAGEMENT = "vitalia.fidelizacion.patient_paused_re_engagement"


# ─────────────────────────────────────────────
# Helpers de construcción segura
# ─────────────────────────────────────────────


def _make_re_engagement_triggered(
    *,
    tenant_id: UUID,
    clinic_id: UUID,
    patient_id: UUID,
    pattern: str,
    re_engagement_event_id: UUID,
    template_id: str | None = None,
    triggered_by_user_id: UUID | None = None,
    occurred_at: datetime | None = None,
) -> "ReEngagementTriggered":
    """Factory para ReEngagementTriggered con event_name correcto."""
    return ReEngagementTriggered(
        event_name=FIDELIZACION_RE_ENGAGEMENT_TRIGGERED,
        tenant_id=tenant_id,
        occurred_at=occurred_at or datetime.now(UTC),
        payload={},
        clinic_id=clinic_id,
        patient_id=patient_id,
        pattern=pattern,
        re_engagement_event_id=re_engagement_event_id,
        template_id=template_id,
        triggered_by_user_id=triggered_by_user_id,
    )


def _make_nps_score_collected(
    *,
    tenant_id: UUID,
    clinic_id: UUID,
    patient_id: UUID,
    nps_response_id: UUID,
    score: int,
    band: str,
    appointment_id: UUID | None = None,
    occurred_at: datetime | None = None,
) -> "NPSScoreCollected":
    """Factory para NPSScoreCollected con event_name correcto."""
    return NPSScoreCollected(
        event_name=FIDELIZACION_NPS_SCORE_COLLECTED,
        tenant_id=tenant_id,
        occurred_at=occurred_at or datetime.now(UTC),
        payload={},
        clinic_id=clinic_id,
        patient_id=patient_id,
        nps_response_id=nps_response_id,
        score=score,
        band=band,
        appointment_id=appointment_id,
    )


def _make_patient_opted_out(
    *,
    tenant_id: UUID,
    clinic_id: UUID,
    patient_id: UUID,
    reason: str | None = None,
    triggered_by_user_id: UUID | None = None,
    occurred_at: datetime | None = None,
) -> "PatientOptedOut":
    """Factory para PatientOptedOut con event_name correcto."""
    return PatientOptedOut(
        event_name=FIDELIZACION_PATIENT_OPTED_OUT,
        tenant_id=tenant_id,
        occurred_at=occurred_at or datetime.now(UTC),
        payload={},
        clinic_id=clinic_id,
        patient_id=patient_id,
        reason=reason,
        triggered_by_user_id=triggered_by_user_id,
    )


def _make_patient_paused_re_engagement(
    *,
    tenant_id: UUID,
    clinic_id: UUID,
    patient_id: UUID,
    duration_days: int,
    reason: str | None = None,
    resume_at: datetime | None = None,
    triggered_by_user_id: UUID | None = None,
    occurred_at: datetime | None = None,
) -> "PatientPausedReEngagement":
    """Factory para PatientPausedReEngagement con event_name correcto."""
    return PatientPausedReEngagement(
        event_name=FIDELIZACION_PATIENT_PAUSED_RE_ENGAGEMENT,
        tenant_id=tenant_id,
        occurred_at=occurred_at or datetime.now(UTC),
        payload={},
        clinic_id=clinic_id,
        patient_id=patient_id,
        duration_days=duration_days,
        reason=reason,
        resume_at=resume_at,
        triggered_by_user_id=triggered_by_user_id,
    )


# ─────────────────────────────────────────────
# Eventos (dataclasses que heredan DomainEvent)
# ─────────────────────────────────────────────


@dataclass
class ReEngagementTriggered(DomainEvent):
    """Evento emitido cuando se dispara un re-engagement hacia un paciente.

    Consumers: sales_agent (escalation tool), copilot (inbox classifier),
    analytics pipeline (re_engagement_triggered metric).
    """

    clinic_id: UUID = field(default_factory=lambda: UUID(int=0))
    patient_id: UUID = field(default_factory=lambda: UUID(int=0))
    pattern: str = ""
    re_engagement_event_id: UUID = field(default_factory=lambda: UUID(int=0))
    template_id: str | None = None
    triggered_by_user_id: UUID | None = None

    # Factory class method — preferred construction
    @classmethod
    def create(
        cls,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        patient_id: UUID,
        pattern: str,
        re_engagement_event_id: UUID,
        template_id: str | None = None,
        triggered_by_user_id: UUID | None = None,
    ) -> "ReEngagementTriggered":
        """Constructor semántico con event_name fijo."""
        return _make_re_engagement_triggered(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            patient_id=patient_id,
            pattern=pattern,
            re_engagement_event_id=re_engagement_event_id,
            template_id=template_id,
            triggered_by_user_id=triggered_by_user_id,
        )


@dataclass
class NPSScoreCollected(DomainEvent):
    """Evento emitido cuando un paciente responde una encuesta NPS.

    Consumers: copilot inbox classifier (tag detractores), analytics.
    """

    clinic_id: UUID = field(default_factory=lambda: UUID(int=0))
    patient_id: UUID = field(default_factory=lambda: UUID(int=0))
    nps_response_id: UUID = field(default_factory=lambda: UUID(int=0))
    score: int = 0
    band: str = ""
    appointment_id: UUID | None = None

    @classmethod
    def create(
        cls,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        patient_id: UUID,
        nps_response_id: UUID,
        score: int,
        band: str,
        appointment_id: UUID | None = None,
    ) -> "NPSScoreCollected":
        """Constructor semántico con event_name fijo."""
        return _make_nps_score_collected(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            patient_id=patient_id,
            nps_response_id=nps_response_id,
            score=score,
            band=band,
            appointment_id=appointment_id,
        )


@dataclass
class PatientOptedOut(DomainEvent):
    """Evento emitido cuando un paciente se da de baja de re-engagements.

    Consumers: crm (flag do_not_contact), sales_agent (filtro previo a contacto).
    """

    clinic_id: UUID = field(default_factory=lambda: UUID(int=0))
    patient_id: UUID = field(default_factory=lambda: UUID(int=0))
    reason: str | None = None
    triggered_by_user_id: UUID | None = None

    @classmethod
    def create(
        cls,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        patient_id: UUID,
        reason: str | None = None,
        triggered_by_user_id: UUID | None = None,
    ) -> "PatientOptedOut":
        """Constructor semántico con event_name fijo."""
        return _make_patient_opted_out(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            patient_id=patient_id,
            reason=reason,
            triggered_by_user_id=triggered_by_user_id,
        )


@dataclass
class PatientPausedReEngagement(DomainEvent):
    """Evento emitido cuando se pausa el re-engagement de un paciente.

    Consumers: cron_fidelizacion (skip patient until resume_at).
    """

    clinic_id: UUID = field(default_factory=lambda: UUID(int=0))
    patient_id: UUID = field(default_factory=lambda: UUID(int=0))
    duration_days: int = 0
    reason: str | None = None
    resume_at: datetime | None = None
    triggered_by_user_id: UUID | None = None

    @classmethod
    def create(
        cls,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        patient_id: UUID,
        duration_days: int,
        reason: str | None = None,
        resume_at: datetime | None = None,
        triggered_by_user_id: UUID | None = None,
    ) -> "PatientPausedReEngagement":
        """Constructor semántico con event_name fijo."""
        return _make_patient_paused_re_engagement(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            patient_id=patient_id,
            duration_days=duration_days,
            reason=reason,
            resume_at=resume_at,
            triggered_by_user_id=triggered_by_user_id,
        )
