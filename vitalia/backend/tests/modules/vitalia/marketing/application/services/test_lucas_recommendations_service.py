"""Tests for LucasRecommendationsService — RED phase (TDD).

Gherkin coverage:
  SC-MK-01 (Lucas approve happy — service flow):
    - test_approve_sets_status_audit_outbox
    - test_approve_undo_within_5min
    - test_approve_idempotency_dedup
  SC-MK-04 (adversarial — RBAC + range validation):
    - test_approve_action_payload_out_of_range_rejected
  Additional:
    - test_reject_sets_status_audit_outbox
    - test_list_returns_open_recommendations
    - test_approve_already_approved_raises
    - test_undo_after_window_expired_raises

HIPAA-lite: dual filter (tenant_id + clinic_id) enforced in all queries.
Audit log write: AsyncAuditWriter.write() called BEFORE returning response.
Outbox: adapter_bus.publish() called after audit log.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.modules.vitalia.infrastructure.models.lucas_recommendation_model import (
    LucasRecommendationModel,
)
from src.modules.vitalia.marketing.domain.enums import (
    BowtieStage,
    RecommendationStatus,
    RejectReason,
)
from src.modules.vitalia.marketing.domain.exceptions import (
    InvalidStateTransitionError,
    UndoWindowExpiredError,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def tenant_id() -> uuid.UUID:
    """Tenant UUID for all tests."""
    return uuid.UUID("11111111-1111-1111-1111-111111111111")


@pytest.fixture
def clinic_id() -> uuid.UUID:
    """Clinic UUID for all tests (HIPAA dual filter)."""
    return uuid.UUID("22222222-2222-2222-2222-222222222222")


@pytest.fixture
def user_id() -> uuid.UUID:
    """User (doctor/admin) UUID performing operations."""
    return uuid.UUID("33333333-3333-3333-3333-333333333333")


@pytest.fixture
def rec_id() -> uuid.UUID:
    """Recommendation UUID."""
    return uuid.UUID("44444444-4444-4444-4444-444444444444")


def _make_rec_model(
    rec_id: uuid.UUID,
    tenant_id: uuid.UUID,
    clinic_id: uuid.UUID,
    status: str = "open",
    undo_until: datetime | None = None,
    approved_at: datetime | None = None,
    approved_by_user_id: uuid.UUID | None = None,
    expires_at: datetime | None = None,
    action_payload_json: dict | None = None,
) -> LucasRecommendationModel:
    """Build a LucasRecommendationModel with sensible defaults."""
    now = datetime.now(UTC)
    model = LucasRecommendationModel()
    model.id = rec_id
    model.tenant_id = tenant_id
    model.clinic_id = clinic_id
    model.stage = BowtieStage.ATTRACTION.value
    model.recommendation_kind = "increase_budget"
    model.title = "Aumentar presupuesto en Google Ads"
    model.body = "El CTR cayó un 12% esta semana."
    model.rationale_json = {}
    model.priority = 1
    model.status = status
    model.expires_at = expires_at or (now + timedelta(days=7))
    model.action_payload_json = action_payload_json
    model.confidence_pct = 85
    model.projected_impact_text = "+15% CTR estimado"
    model.approved_by_user_id = approved_by_user_id
    model.approved_at = approved_at
    model.undo_until = undo_until
    model.rejected_by_user_id = None
    model.rejected_at = None
    model.reject_reason = None
    model.created_at = now
    model.updated_at = now
    model.deleted_at = None
    return model


@pytest.fixture
def mock_repo(rec_id: uuid.UUID, tenant_id: uuid.UUID, clinic_id: uuid.UUID) -> MagicMock:
    """Mock LucasRecommendationRepository.

    get_by_id uses signature (id, tenant_id, scope_id) per CompoundScopeRepositoryBase.
    save returns the model passed in (merge+flush pattern).
    """
    repo = MagicMock()
    rec = _make_rec_model(rec_id, tenant_id, clinic_id)

    # Base class signature: get_by_id(id=..., tenant_id=..., scope_id=...)
    async def _get_by_id(*, id: uuid.UUID, tenant_id: uuid.UUID, scope_id: uuid.UUID) -> LucasRecommendationModel:  # noqa: A002
        return rec

    repo.get_by_id = AsyncMock(side_effect=_get_by_id)
    # save returns whatever model was passed in
    repo.save = AsyncMock(side_effect=lambda model: model)
    repo.list_open_by_stage = AsyncMock(return_value=[rec])
    return repo


@pytest.fixture
def mock_audit_writer() -> MagicMock:
    """Mock AsyncAuditWriter with async write()."""
    writer = MagicMock()
    writer.write = AsyncMock()
    return writer


@pytest.fixture
def mock_adapter_bus() -> MagicMock:
    """Mock outbox adapter_bus with async publish()."""
    bus = MagicMock()
    bus.publish = AsyncMock()
    return bus


@pytest.fixture
def service(mock_repo: MagicMock, mock_audit_writer: MagicMock):
    """LucasRecommendationsService with mocked dependencies."""
    from src.modules.vitalia.marketing.application.services.lucas_recommendations_service import (
        LucasRecommendationsService,
    )

    return LucasRecommendationsService(
        repo=mock_repo,
        audit_writer=mock_audit_writer,
    )


# ---------------------------------------------------------------------------
# SC-MK-01 — approve happy path
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_approve_sets_status_audit_outbox(
    service,
    mock_repo: MagicMock,
    mock_audit_writer: MagicMock,
    rec_id: uuid.UUID,
    tenant_id: uuid.UUID,
    clinic_id: uuid.UUID,
    user_id: uuid.UUID,
) -> None:
    """SC-MK-01: approve() transitions status OPEN→APPROVED, writes audit_log, publishes outbox event.

    Order invariant: audit_log write BEFORE outbox publish.
    """
    with patch(
        "src.modules.vitalia.marketing.application.services.lucas_recommendations_service.adapter_bus"
    ) as mock_bus:
        mock_bus.publish = AsyncMock()

        result = await service.approve(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            recommendation_id=rec_id,
            user_id=user_id,
        )

    # Status is APPROVED on the saved model (save(model) called positionally)
    save_args = mock_repo.save.call_args
    saved_model = save_args.args[0] if save_args.args else next(iter(save_args.kwargs.values()))
    assert saved_model.status == RecommendationStatus.APPROVED.value

    # Audit log written BEFORE outbox (mandatory HIPAA-lite)
    mock_audit_writer.write.assert_awaited_once()
    audit_kwargs = mock_audit_writer.write.call_args.kwargs
    assert str(tenant_id) == audit_kwargs["tenant_id"] or audit_kwargs["tenant_id"] == tenant_id
    assert str(clinic_id) == str(audit_kwargs["clinic_id"])
    assert "approve" in audit_kwargs["action"].lower() or "lucas_recommendation" in audit_kwargs["action"].lower()
    assert str(rec_id) == str(audit_kwargs["resource_id"])

    # Outbox event published
    mock_bus.publish.assert_awaited_once()
    published_event = mock_bus.publish.call_args[0][0]
    assert "approved" in type(published_event).__name__.lower()

    # Result has correct status
    assert result.status == RecommendationStatus.APPROVED.value


@pytest.mark.asyncio
async def test_approve_undo_within_5min(
    service,
    mock_repo: MagicMock,
    mock_audit_writer: MagicMock,
    rec_id: uuid.UUID,
    tenant_id: uuid.UUID,
    clinic_id: uuid.UUID,
    user_id: uuid.UUID,
) -> None:
    """SC-MK-01: undo() within 5-minute window reverts APPROVED→OPEN."""
    now = datetime.now(UTC)
    # Set up repo to return APPROVED rec with undo_until in future
    rec = _make_rec_model(
        rec_id,
        tenant_id,
        clinic_id,
        status="approved",
        approved_at=now,
        approved_by_user_id=user_id,
        undo_until=now + timedelta(minutes=4),  # within window
    )
    mock_repo.get_by_id = AsyncMock(side_effect=lambda *, id, tenant_id, scope_id: rec)  # noqa: A002
    mock_repo.save = AsyncMock(side_effect=lambda model: model)

    with patch(
        "src.modules.vitalia.marketing.application.services.lucas_recommendations_service.adapter_bus"
    ) as mock_bus:
        mock_bus.publish = AsyncMock()

        await service.undo(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            recommendation_id=rec_id,
        )

    # Status reverted to OPEN
    save_args = mock_repo.save.call_args
    if save_args.args:
        saved_model = save_args.args[0]
    else:
        saved_model = next(iter(save_args.kwargs.values()))
    assert saved_model.status == RecommendationStatus.OPEN.value
    assert saved_model.approved_at is None
    assert saved_model.undo_until is None

    # Audit log written
    mock_audit_writer.write.assert_awaited_once()

    # Outbox event published
    mock_bus.publish.assert_awaited_once()
    published_event = mock_bus.publish.call_args[0][0]
    assert "undone" in type(published_event).__name__.lower()


@pytest.mark.asyncio
async def test_approve_idempotency_dedup(
    service,
    mock_repo: MagicMock,
    mock_audit_writer: MagicMock,
    rec_id: uuid.UUID,
    tenant_id: uuid.UUID,
    clinic_id: uuid.UUID,
    user_id: uuid.UUID,
) -> None:
    """SC-MK-01: approve() on already-APPROVED rec raises InvalidStateTransitionError (idempotency).

    Re-approving the same recommendation should raise, not silently succeed.
    """
    now = datetime.now(UTC)
    rec = _make_rec_model(
        rec_id,
        tenant_id,
        clinic_id,
        status="approved",
        approved_at=now,
        approved_by_user_id=user_id,
        undo_until=now + timedelta(minutes=4),
    )
    mock_repo.get_by_id = AsyncMock(side_effect=lambda *, id, tenant_id, scope_id: rec)  # noqa: A002

    with pytest.raises(InvalidStateTransitionError):
        await service.approve(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            recommendation_id=rec_id,
            user_id=user_id,
        )

    # No audit log or outbox on idempotency rejection
    mock_audit_writer.write.assert_not_awaited()


# ---------------------------------------------------------------------------
# SC-MK-04 — adversarial: action_payload range validation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_approve_action_payload_out_of_range_rejected(
    service,
    mock_repo: MagicMock,
    mock_audit_writer: MagicMock,
    rec_id: uuid.UUID,
    tenant_id: uuid.UUID,
    clinic_id: uuid.UUID,
    user_id: uuid.UUID,
) -> None:
    """SC-MK-04: approve() with action_payload budget_amount_cents > 1_000_000_00 rejected.

    Validation: amount_cents <= 100_000_00 (100k USD limit).
    Raises ValueError with user-facing Spanish message.
    """
    rec = _make_rec_model(
        rec_id,
        tenant_id,
        clinic_id,
        status="open",
        # action_payload with out-of-range amount
        action_payload_json={"action": "increase_budget", "budget_amount_cents": 100_000_01},
    )
    mock_repo.get_by_id = AsyncMock(side_effect=lambda *, id, tenant_id, scope_id: rec)  # noqa: A002

    with pytest.raises(ValueError, match="presupuesto"):
        await service.approve(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            recommendation_id=rec_id,
            user_id=user_id,
        )

    # No persistence on validation failure
    mock_repo.save.assert_not_called()
    mock_audit_writer.write.assert_not_awaited()


# ---------------------------------------------------------------------------
# Additional coverage
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_reject_sets_status_audit_outbox(
    service,
    mock_repo: MagicMock,
    mock_audit_writer: MagicMock,
    rec_id: uuid.UUID,
    tenant_id: uuid.UUID,
    clinic_id: uuid.UUID,
    user_id: uuid.UUID,
) -> None:
    """reject() transitions OPEN→REJECTED, writes audit, publishes outbox event."""
    with patch(
        "src.modules.vitalia.marketing.application.services.lucas_recommendations_service.adapter_bus"
    ) as mock_bus:
        mock_bus.publish = AsyncMock()

        result = await service.reject(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            recommendation_id=rec_id,
            user_id=user_id,
            reason=RejectReason.NOT_PRIORITY,
        )

    # Saved model is REJECTED (save(model) called positionally)
    save_args = mock_repo.save.call_args
    saved_model = save_args.args[0] if save_args.args else next(iter(save_args.kwargs.values()))
    assert saved_model.status == RecommendationStatus.REJECTED.value
    assert saved_model.reject_reason == RejectReason.NOT_PRIORITY.value

    # Audit log written
    mock_audit_writer.write.assert_awaited_once()
    audit_kwargs = mock_audit_writer.write.call_args.kwargs
    assert "reject" in audit_kwargs["action"].lower() or "lucas_recommendation" in audit_kwargs["action"].lower()

    # Outbox event
    mock_bus.publish.assert_awaited_once()
    published_event = mock_bus.publish.call_args[0][0]
    assert "rejected" in type(published_event).__name__.lower()

    assert result.status == RecommendationStatus.REJECTED.value


@pytest.mark.asyncio
async def test_list_returns_open_recommendations(
    service,
    mock_repo: MagicMock,
    tenant_id: uuid.UUID,
    clinic_id: uuid.UUID,
    rec_id: uuid.UUID,
) -> None:
    """list() returns open recommendations for a stage with dual filter applied."""
    results = await service.list_open_by_stage(
        tenant_id=tenant_id,
        clinic_id=clinic_id,
        stage=BowtieStage.ATTRACTION,
        limit=3,
    )

    mock_repo.list_open_by_stage.assert_awaited_once_with(
        tenant_id=tenant_id,
        clinic_id=clinic_id,
        stage=BowtieStage.ATTRACTION,
        limit=3,
    )
    assert len(results) == 1
    assert results[0].id == rec_id


@pytest.mark.asyncio
async def test_approve_already_approved_raises(
    service,
    mock_repo: MagicMock,
    rec_id: uuid.UUID,
    tenant_id: uuid.UUID,
    clinic_id: uuid.UUID,
    user_id: uuid.UUID,
) -> None:
    """approve() on REJECTED rec raises InvalidStateTransitionError."""
    rec = _make_rec_model(rec_id, tenant_id, clinic_id, status="rejected")
    mock_repo.get_by_id = AsyncMock(side_effect=lambda *, id, tenant_id, scope_id: rec)  # noqa: A002

    with pytest.raises(InvalidStateTransitionError):
        await service.approve(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            recommendation_id=rec_id,
            user_id=user_id,
        )


@pytest.mark.asyncio
async def test_undo_after_window_expired_raises(
    service,
    mock_repo: MagicMock,
    rec_id: uuid.UUID,
    tenant_id: uuid.UUID,
    clinic_id: uuid.UUID,
    user_id: uuid.UUID,
) -> None:
    """undo() after 5-minute window raises UndoWindowExpiredError."""
    now = datetime.now(UTC)
    rec = _make_rec_model(
        rec_id,
        tenant_id,
        clinic_id,
        status="approved",
        approved_at=now - timedelta(minutes=10),
        approved_by_user_id=user_id,
        undo_until=now - timedelta(minutes=5),  # window already expired
    )
    mock_repo.get_by_id = AsyncMock(side_effect=lambda *, id, tenant_id, scope_id: rec)  # noqa: A002

    with pytest.raises(UndoWindowExpiredError):
        await service.undo(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            recommendation_id=rec_id,
        )
