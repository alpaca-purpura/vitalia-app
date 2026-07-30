"""Tests for fidelización domain entities (TDD RED phase).

Verifica: TreatmentPlan, ReEngagementEvent, NPSResponse — construcción,
campos obligatorios, from_attributes, y value objects embebidos.
"""

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from src.modules.vitalia.fidelizacion.domain.entities.nps_response import (
    NPSResponse,
)
from src.modules.vitalia.fidelizacion.domain.entities.re_engagement_event import (
    ReEngagementEvent,
)
from src.modules.vitalia.fidelizacion.domain.entities.treatment_plan import (
    TreatmentPlan,
    TreatmentPlanStatus,
)
from src.modules.vitalia.fidelizacion.domain.value_objects.nps_band import (
    NPSBand,
)
from src.modules.vitalia.fidelizacion.domain.value_objects.re_engagement_outcome import (
    ReEngagementOutcome,
)
from src.modules.vitalia.fidelizacion.domain.value_objects.re_engagement_pattern import (
    ReEngagementPattern,
)

_NOW = datetime.now(timezone.utc)
_TENANT = uuid4()
_CLINIC = uuid4()
_PATIENT = uuid4()


class TestTreatmentPlanStatus:
    """TreatmentPlanStatus StrEnum — 4 valores."""

    def test_values(self) -> None:
        assert TreatmentPlanStatus.ACTIVE == "active"
        assert TreatmentPlanStatus.COMPLETED == "completed"
        assert TreatmentPlanStatus.ABANDONED == "abandoned"
        assert TreatmentPlanStatus.PAUSED == "paused"

    def test_all_four(self) -> None:
        assert len(list(TreatmentPlanStatus)) == 4


class TestTreatmentPlan:
    """TreatmentPlan — entidad dominio Pydantic v2."""

    def _minimal(self) -> TreatmentPlan:
        return TreatmentPlan(
            id=uuid4(),
            tenant_id=_TENANT,
            clinic_id=_CLINIC,
            patient_id=_PATIENT,
            sessions_total=4,
            sessions_completed=0,
            status=TreatmentPlanStatus.ACTIVE,
            created_at=_NOW,
            updated_at=_NOW,
        )

    def test_construction_minimal(self) -> None:
        plan = self._minimal()
        assert plan.status == TreatmentPlanStatus.ACTIVE
        assert plan.sessions_completed == 0
        assert plan.notes is None
        assert plan.deleted_at is None

    def test_from_attributes_config(self) -> None:
        """ConfigDict(from_attributes=True) permite construir desde ORM model."""
        plan = self._minimal()

        # Simula ORM model con atributos
        class FakeModel:
            id = plan.id
            tenant_id = plan.tenant_id
            clinic_id = plan.clinic_id
            patient_id = plan.patient_id
            offer_id = None
            doctor_id = None
            sessions_total = 4
            sessions_completed = 0
            next_session_due_at = None
            gap_alert_days = None
            status = "active"
            notes = None
            last_session_at = None
            paused_until = None
            pause_reason = None
            created_at = _NOW
            updated_at = _NOW
            deleted_at = None

        result = TreatmentPlan.model_validate(FakeModel(), from_attributes=True)
        assert result.id == plan.id
        assert result.status == TreatmentPlanStatus.ACTIVE

    def test_tenant_id_required(self) -> None:
        with pytest.raises(ValidationError):
            TreatmentPlan(  # type: ignore[call-arg]
                id=uuid4(),
                clinic_id=_CLINIC,
                patient_id=_PATIENT,
                sessions_total=4,
                sessions_completed=0,
                status=TreatmentPlanStatus.ACTIVE,
                created_at=_NOW,
                updated_at=_NOW,
            )

    def test_clinic_id_required(self) -> None:
        with pytest.raises(ValidationError):
            TreatmentPlan(  # type: ignore[call-arg]
                id=uuid4(),
                tenant_id=_TENANT,
                patient_id=_PATIENT,
                sessions_total=4,
                sessions_completed=0,
                status=TreatmentPlanStatus.ACTIVE,
                created_at=_NOW,
                updated_at=_NOW,
            )

    def test_notes_is_bytes_or_none(self) -> None:
        plan = self._minimal()
        # notes puede ser bytes (de pgcrypto) o None
        assert plan.notes is None
        plan2 = TreatmentPlan(**plan.model_dump() | {"notes": b"encrypted_bytes"})
        assert isinstance(plan2.notes, bytes)

    def test_soft_delete_field(self) -> None:
        plan = self._minimal()
        deleted = TreatmentPlan(**plan.model_dump() | {"deleted_at": _NOW})
        assert deleted.deleted_at == _NOW


class TestReEngagementEvent:
    """ReEngagementEvent — entidad dominio Pydantic v2."""

    def _minimal(self) -> ReEngagementEvent:
        return ReEngagementEvent(
            id=uuid4(),
            tenant_id=_TENANT,
            clinic_id=_CLINIC,
            patient_id=_PATIENT,
            pattern=ReEngagementPattern.MULTI_SESSION,
            trigger_source="cron_fidelizacion",
            trigger_at=_NOW,
            retry_count=0,
            created_at=_NOW,
            updated_at=_NOW,
        )

    def test_construction_minimal(self) -> None:
        event = self._minimal()
        assert event.pattern == ReEngagementPattern.MULTI_SESSION
        assert event.outcome is None
        assert event.sent_at is None
        assert event.payload_phi is None

    def test_tenant_and_clinic_required(self) -> None:
        with pytest.raises(ValidationError):
            ReEngagementEvent(  # type: ignore[call-arg]
                id=uuid4(),
                patient_id=_PATIENT,
                pattern=ReEngagementPattern.FOLLOW_UP,
                trigger_source="cron",
                trigger_at=_NOW,
                retry_count=0,
                created_at=_NOW,
                updated_at=_NOW,
            )

    def test_from_attributes_config(self) -> None:
        event = self._minimal()

        class FakeModel:
            id = event.id
            tenant_id = event.tenant_id
            clinic_id = event.clinic_id
            patient_id = event.patient_id
            pattern = "multi_session"
            trigger_source = "cron_fidelizacion"
            trigger_at = _NOW
            template_id = None
            sent_at = None
            response_at = None
            outcome = None
            converted_to_appointment_id = None
            audit_log_id = None
            payload_phi = None
            retry_count = 0
            last_error = None
            idempotency_key = None
            created_at = _NOW
            updated_at = _NOW
            deleted_at = None

        result = ReEngagementEvent.model_validate(FakeModel(), from_attributes=True)
        assert result.pattern == ReEngagementPattern.MULTI_SESSION

    def test_outcome_enum(self) -> None:
        event = self._minimal()
        updated = ReEngagementEvent(**event.model_dump() | {"outcome": ReEngagementOutcome.RESPONDED})
        assert updated.outcome == ReEngagementOutcome.RESPONDED

    def test_soft_delete_field(self) -> None:
        event = self._minimal()
        deleted = ReEngagementEvent(**event.model_dump() | {"deleted_at": _NOW})
        assert deleted.deleted_at == _NOW


class TestNPSResponse:
    """NPSResponse — entidad dominio Pydantic v2."""

    def _minimal(self) -> NPSResponse:
        return NPSResponse(
            id=uuid4(),
            tenant_id=_TENANT,
            clinic_id=_CLINIC,
            patient_id=_PATIENT,
            score=9,
            band=NPSBand.PROMOTER,
            source="post_appointment_sms",
            tagged_in_inbox=False,
            responded_at=_NOW,
            created_at=_NOW,
            updated_at=_NOW,
        )

    def test_construction_minimal(self) -> None:
        nps = self._minimal()
        assert nps.score == 9
        assert nps.band == NPSBand.PROMOTER
        assert nps.comment is None

    def test_tenant_and_clinic_required(self) -> None:
        with pytest.raises(ValidationError):
            NPSResponse(  # type: ignore[call-arg]
                id=uuid4(),
                patient_id=_PATIENT,
                score=7,
                band=NPSBand.PASSIVE,
                source="sms",
                tagged_in_inbox=False,
                responded_at=_NOW,
                created_at=_NOW,
                updated_at=_NOW,
            )

    def test_score_range(self) -> None:
        """Score 0-10 — Pydantic debe validar el rango."""
        for score in [0, 5, 10]:
            nps = NPSResponse(**self._minimal().model_dump() | {"score": score, "band": NPSBand.from_score(score)})
            assert nps.score == score

    def test_comment_bytes_or_none(self) -> None:
        nps = self._minimal()
        encrypted = NPSResponse(**nps.model_dump() | {"comment": b"pgcrypto_ciphertext"})
        assert isinstance(encrypted.comment, bytes)

    def test_from_attributes(self) -> None:
        nps = self._minimal()

        class FakeModel:
            id = nps.id
            tenant_id = nps.tenant_id
            clinic_id = nps.clinic_id
            patient_id = nps.patient_id
            appointment_id = None
            score = 9
            band = "promoter"
            comment = None
            source = "post_appointment_sms"
            trigger_re_engagement_event_id = None
            responded_at = _NOW
            tagged_in_inbox = False
            audit_log_id = None
            created_at = _NOW
            updated_at = _NOW
            deleted_at = None

        result = NPSResponse.model_validate(FakeModel(), from_attributes=True)
        assert result.band == NPSBand.PROMOTER
        assert result.score == 9
