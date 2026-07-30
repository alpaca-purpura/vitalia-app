"""Tests for fidelización domain events (TDD RED phase).

Verifica: subclassing DomainEvent, campos, event_name constants,
factories create() por evento.
"""

from datetime import datetime, timezone
from uuid import uuid4

from luana_core_platform.domain.events import DomainEvent

from src.modules.vitalia.fidelizacion.domain.events.events import (
    FIDELIZACION_NPS_SCORE_COLLECTED,
    FIDELIZACION_PATIENT_OPTED_OUT,
    FIDELIZACION_PATIENT_PAUSED_RE_ENGAGEMENT,
    FIDELIZACION_RE_ENGAGEMENT_TRIGGERED,
    NPSScoreCollected,
    PatientOptedOut,
    PatientPausedReEngagement,
    ReEngagementTriggered,
)

_NOW = datetime.now(timezone.utc)
_TENANT = uuid4()
_CLINIC = uuid4()
_PATIENT = uuid4()


class TestDomainEventConstants:
    """Los nombres de evento tienen el prefijo vitalia.fidelizacion."""

    def test_event_names_prefix(self) -> None:
        assert FIDELIZACION_RE_ENGAGEMENT_TRIGGERED.startswith("vitalia.fidelizacion.")
        assert FIDELIZACION_NPS_SCORE_COLLECTED.startswith("vitalia.fidelizacion.")
        assert FIDELIZACION_PATIENT_OPTED_OUT.startswith("vitalia.fidelizacion.")
        assert FIDELIZACION_PATIENT_PAUSED_RE_ENGAGEMENT.startswith("vitalia.fidelizacion.")

    def test_event_names_distinct(self) -> None:
        names = {
            FIDELIZACION_RE_ENGAGEMENT_TRIGGERED,
            FIDELIZACION_NPS_SCORE_COLLECTED,
            FIDELIZACION_PATIENT_OPTED_OUT,
            FIDELIZACION_PATIENT_PAUSED_RE_ENGAGEMENT,
        }
        assert len(names) == 4


class TestReEngagementTriggered:
    """ReEngagementTriggered es DomainEvent dataclass."""

    def test_is_domain_event_subclass(self) -> None:
        assert issubclass(ReEngagementTriggered, DomainEvent)

    def test_construction_via_create(self) -> None:
        evt = ReEngagementTriggered.create(
            tenant_id=_TENANT,
            clinic_id=_CLINIC,
            patient_id=_PATIENT,
            pattern="multi_session",
            re_engagement_event_id=uuid4(),
            template_id="tmpl_001",
            triggered_by_user_id=uuid4(),
        )
        assert evt.event_name == FIDELIZACION_RE_ENGAGEMENT_TRIGGERED
        assert evt.tenant_id == _TENANT
        assert evt.clinic_id == _CLINIC
        assert evt.pattern == "multi_session"

    def test_event_name_auto(self) -> None:
        """event_name se establece automáticamente al constant correcto."""
        evt = ReEngagementTriggered.create(
            tenant_id=_TENANT,
            clinic_id=_CLINIC,
            patient_id=_PATIENT,
            pattern="follow_up",
            re_engagement_event_id=uuid4(),
            template_id=None,
            triggered_by_user_id=None,
        )
        assert evt.event_name == FIDELIZACION_RE_ENGAGEMENT_TRIGGERED

    def test_occurred_at_defaults_to_utcnow(self) -> None:
        evt = ReEngagementTriggered.create(
            tenant_id=_TENANT,
            clinic_id=_CLINIC,
            patient_id=_PATIENT,
            pattern="nps",
            re_engagement_event_id=uuid4(),
            template_id=None,
            triggered_by_user_id=None,
        )
        assert evt.occurred_at.tzinfo is not None

    def test_template_id_optional(self) -> None:
        evt = ReEngagementTriggered.create(
            tenant_id=_TENANT,
            clinic_id=_CLINIC,
            patient_id=_PATIENT,
            pattern="absence",
            re_engagement_event_id=uuid4(),
        )
        assert evt.template_id is None


class TestNPSScoreCollected:
    """NPSScoreCollected es DomainEvent dataclass."""

    def test_is_domain_event_subclass(self) -> None:
        assert issubclass(NPSScoreCollected, DomainEvent)

    def test_construction_via_create(self) -> None:
        resp_id = uuid4()
        evt = NPSScoreCollected.create(
            tenant_id=_TENANT,
            clinic_id=_CLINIC,
            patient_id=_PATIENT,
            nps_response_id=resp_id,
            score=9,
            band="promoter",
            appointment_id=uuid4(),
        )
        assert evt.event_name == FIDELIZACION_NPS_SCORE_COLLECTED
        assert evt.score == 9
        assert evt.nps_response_id == resp_id

    def test_appointment_id_optional(self) -> None:
        evt = NPSScoreCollected.create(
            tenant_id=_TENANT,
            clinic_id=_CLINIC,
            patient_id=_PATIENT,
            nps_response_id=uuid4(),
            score=4,
            band="detractor",
            appointment_id=None,
        )
        assert evt.appointment_id is None


class TestPatientOptedOut:
    """PatientOptedOut es DomainEvent dataclass."""

    def test_is_domain_event_subclass(self) -> None:
        assert issubclass(PatientOptedOut, DomainEvent)

    def test_construction_via_create(self) -> None:
        evt = PatientOptedOut.create(
            tenant_id=_TENANT,
            clinic_id=_CLINIC,
            patient_id=_PATIENT,
            reason="no_interest",
            triggered_by_user_id=uuid4(),
        )
        assert evt.event_name == FIDELIZACION_PATIENT_OPTED_OUT
        assert evt.reason == "no_interest"

    def test_triggered_by_user_optional(self) -> None:
        evt = PatientOptedOut.create(
            tenant_id=_TENANT,
            clinic_id=_CLINIC,
            patient_id=_PATIENT,
            reason="unsubscribed",
            triggered_by_user_id=None,
        )
        assert evt.triggered_by_user_id is None

    def test_reason_optional(self) -> None:
        evt = PatientOptedOut.create(
            tenant_id=_TENANT,
            clinic_id=_CLINIC,
            patient_id=_PATIENT,
        )
        assert evt.reason is None


class TestPatientPausedReEngagement:
    """PatientPausedReEngagement es DomainEvent dataclass."""

    def test_is_domain_event_subclass(self) -> None:
        assert issubclass(PatientPausedReEngagement, DomainEvent)

    def test_construction_via_create(self) -> None:
        resume = datetime.now(timezone.utc)
        evt = PatientPausedReEngagement.create(
            tenant_id=_TENANT,
            clinic_id=_CLINIC,
            patient_id=_PATIENT,
            duration_days=30,
            reason="vacaciones",
            resume_at=resume,
            triggered_by_user_id=uuid4(),
        )
        assert evt.event_name == FIDELIZACION_PATIENT_PAUSED_RE_ENGAGEMENT
        assert evt.duration_days == 30
        assert evt.resume_at == resume

    def test_optional_fields(self) -> None:
        evt = PatientPausedReEngagement.create(
            tenant_id=_TENANT,
            clinic_id=_CLINIC,
            patient_id=_PATIENT,
            duration_days=14,
        )
        assert evt.reason is None
        assert evt.resume_at is None
        assert evt.triggered_by_user_id is None
