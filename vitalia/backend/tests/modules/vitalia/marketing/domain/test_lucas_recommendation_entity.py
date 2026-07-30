"""Tests for LucasRecommendation domain entity — gherkin coverage SC-MK-01.

Gherkin SC-MK-01: Lucas genera y gestiona recomendaciones de marketing.

Coverage:
- test_approve_transitions_status: approve() transitions status pending → approved
- test_approved_sets_undo_until_5min: approve() sets undo_until = approved_at + 5 min
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest

from src.modules.vitalia.marketing.domain.entities.lucas_recommendation import LucasRecommendation
from src.modules.vitalia.marketing.domain.enums import (
    BowtieStage,
    RecommendationStatus,
    RejectReason,
)


@pytest.fixture()
def open_recommendation() -> LucasRecommendation:
    """Fixture: a LucasRecommendation in OPEN status ready for approval."""
    return LucasRecommendation(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        clinic_id=uuid.uuid4(),
        stage=BowtieStage.ATTRACTION,
        recommendation_kind="increase_budget",
        title="Aumenta el presupuesto de Google Ads",
        body="Tu tasa de clic es alta. Aumentar el presupuesto puede generar más conversiones.",
        rationale_json={"reason": "high_ctr"},
        priority=1,
        status=RecommendationStatus.OPEN,
        expires_at=datetime.now(UTC) + timedelta(days=7),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


class TestApproveTransitionsStatus:
    """SC-MK-01 Given: recomendación abierta, When: usuario aprueba, Then: estado → approved."""

    def test_approve_transitions_status(self, open_recommendation: LucasRecommendation) -> None:
        """approve() debe cambiar status de OPEN a APPROVED."""
        user_id = uuid.uuid4()

        open_recommendation.approve(user_id=user_id)

        assert open_recommendation.status == RecommendationStatus.APPROVED

    def test_approved_sets_undo_until_5min(self, open_recommendation: LucasRecommendation) -> None:
        """approve() debe fijar undo_until = approved_at + 5 minutos."""
        user_id = uuid.uuid4()
        before = datetime.now(UTC)

        open_recommendation.approve(user_id=user_id)

        assert open_recommendation.approved_at is not None
        assert open_recommendation.undo_until is not None
        expected_undo = open_recommendation.approved_at + timedelta(minutes=5)
        assert open_recommendation.undo_until == expected_undo
        assert open_recommendation.approved_at >= before

    def test_approve_sets_approved_by(self, open_recommendation: LucasRecommendation) -> None:
        """approve() registra el user_id que aprobó."""
        user_id = uuid.uuid4()

        open_recommendation.approve(user_id=user_id)

        assert open_recommendation.approved_by_user_id == user_id

    def test_approve_raises_if_already_approved(self, open_recommendation: LucasRecommendation) -> None:
        """approve() falla con InvalidStateTransition si ya está aprobada."""
        from src.modules.vitalia.marketing.domain.exceptions import InvalidStateTransitionError

        user_id = uuid.uuid4()
        open_recommendation.approve(user_id=user_id)

        with pytest.raises(InvalidStateTransitionError):
            open_recommendation.approve(user_id=user_id)

    def test_approve_raises_if_rejected(self, open_recommendation: LucasRecommendation) -> None:
        """approve() falla con InvalidStateTransition si está rechazada."""
        from src.modules.vitalia.marketing.domain.exceptions import InvalidStateTransitionError

        user_id = uuid.uuid4()
        open_recommendation.reject(user_id=user_id, reason=RejectReason.NOT_PRIORITY)

        with pytest.raises(InvalidStateTransitionError):
            open_recommendation.approve(user_id=user_id)

    def test_approve_raises_if_expired(self, open_recommendation: LucasRecommendation) -> None:
        """approve() falla con ExpiredRecommendationError si la recomendación expiró."""
        from src.modules.vitalia.marketing.domain.exceptions import ExpiredRecommendationError

        open_recommendation.expires_at = datetime.now(UTC) - timedelta(seconds=1)
        user_id = uuid.uuid4()

        with pytest.raises(ExpiredRecommendationError):
            open_recommendation.approve(user_id=user_id)


class TestRejectTransitionsStatus:
    """reject() transitions status OPEN → REJECTED."""

    def test_reject_transitions_status(self, open_recommendation: LucasRecommendation) -> None:
        """reject() debe cambiar status de OPEN a REJECTED."""
        user_id = uuid.uuid4()

        open_recommendation.reject(user_id=user_id, reason=RejectReason.NOT_PRIORITY)

        assert open_recommendation.status == RecommendationStatus.REJECTED

    def test_reject_sets_reject_reason(self, open_recommendation: LucasRecommendation) -> None:
        """reject() guarda la razón de rechazo."""
        user_id = uuid.uuid4()

        open_recommendation.reject(user_id=user_id, reason=RejectReason.TOO_RISKY)

        assert open_recommendation.reject_reason == RejectReason.TOO_RISKY
        assert open_recommendation.rejected_by_user_id == user_id
        assert open_recommendation.rejected_at is not None


class TestUndoApproval:
    """undo() reverts APPROVED → OPEN within undo_until window."""

    def test_undo_within_window_transitions_to_open(self, open_recommendation: LucasRecommendation) -> None:
        """undo() dentro de la ventana de 5 min vuelve a OPEN."""
        user_id = uuid.uuid4()
        open_recommendation.approve(user_id=user_id)

        open_recommendation.undo()

        assert open_recommendation.status == RecommendationStatus.OPEN
        assert open_recommendation.approved_at is None
        assert open_recommendation.approved_by_user_id is None
        assert open_recommendation.undo_until is None

    def test_undo_outside_window_raises(self, open_recommendation: LucasRecommendation) -> None:
        """undo() fuera de la ventana falla con UndoWindowExpiredError."""
        from src.modules.vitalia.marketing.domain.exceptions import UndoWindowExpiredError

        user_id = uuid.uuid4()
        open_recommendation.approve(user_id=user_id)
        open_recommendation.undo_until = datetime.now(UTC) - timedelta(seconds=1)

        with pytest.raises(UndoWindowExpiredError):
            open_recommendation.undo()


class TestExpireRecommendation:
    """expire() transitions status OPEN → EXPIRED."""

    def test_expire_open_recommendation(self, open_recommendation: LucasRecommendation) -> None:
        """expire() sobre recomendación abierta la marca como EXPIRED."""
        open_recommendation.expire()

        assert open_recommendation.status == RecommendationStatus.EXPIRED

    def test_expire_approved_does_nothing(self, open_recommendation: LucasRecommendation) -> None:
        """expire() sobre recomendación aprobada no cambia el status."""
        user_id = uuid.uuid4()
        open_recommendation.approve(user_id=user_id)

        open_recommendation.expire()

        assert open_recommendation.status == RecommendationStatus.APPROVED
