# cap: crm.adrian-embudo
# story-origin: vitalia-fase2-adrian-embudo
"""Tests for FunnelService — unit tests using AsyncMock repos.

TDD order: RED first, then GREEN in funnel_service.py.

Covers:
  SC-1: happy-path adjacent stage transition
  SC-1c: reason persisted in transition record
  SC-2: invalid transition → InvalidTransitionError (422 at API)
  SC-4: cross-tenant lead → 404 (tested via repo returning None)
  SC-freeze: freeze + reactivate flow
  SC-board: board assembly with HOT_BOARD_STAGES filter
  SC-reservado_manual: ManualReservadoForbiddenError (403 at API)
  SC-5: optimistic lock conflict → StaleStateError
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.modules.vitalia.crm.domain.exceptions import (
    InvalidTransitionError,
    ManualReservadoForbiddenError,
    StaleStateError,
)
from src.modules.vitalia.crm.domain.lead import Lead
from src.modules.vitalia.crm.domain.lead_activity import LeadActivity
from src.modules.vitalia.crm.domain.lead_stage_transition import LeadStageTransition

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

TENANT_ID = uuid4()
LEAD_ID = uuid4()
USER_ID = uuid4()


def _make_lead(
    stage: str = "interesado",
    version: int = 1,
    is_frozen: bool = False,
    score: int = 0,
    buying_signals: list[str] | None = None,
    stage_entered_at: datetime | None = None,
) -> Lead:
    return Lead(
        id=LEAD_ID,
        tenant_id=TENANT_ID,
        name="María García",
        email="maria@example.com",
        phone="+525512345678",
        stage=stage,
        score=score,
        version=version,
        is_frozen=is_frozen,
        stage_entered_at=stage_entered_at or datetime.now(tz=timezone.utc),
        buying_signals=buying_signals or [],
    )


def _make_transition(from_stage: str, to_stage: str) -> LeadStageTransition:
    return LeadStageTransition(
        id=uuid4(),
        tenant_id=TENANT_ID,
        lead_id=LEAD_ID,
        from_stage=from_stage,
        to_stage=to_stage,
        triggered_by="manual_override",
        reason=None,
        score_at_transition=50,
        actor_user_id=USER_ID,
        occurred_at=datetime.now(tz=timezone.utc),
        deleted_at=None,
    )


def _make_activity() -> LeadActivity:
    return LeadActivity(
        id=uuid4(),
        tenant_id=TENANT_ID,
        lead_id=LEAD_ID,
        actor="human",
        kind="stage_move",
        description_es="La etapa cambió a Calificando.",
        occurred_at=datetime.now(tz=timezone.utc),
        deleted_at=None,
    )


def _make_service() -> tuple[object, AsyncMock, AsyncMock, AsyncMock, AsyncMock, AsyncMock]:
    from src.modules.vitalia.crm.application.services.funnel_service import FunnelService

    lead_repo = AsyncMock()
    transition_repo = AsyncMock()
    activity_repo = AsyncMock()
    emitter = AsyncMock()
    event_bus = AsyncMock()

    service = FunnelService(
        lead_repo=lead_repo,
        transition_repo=transition_repo,
        activity_repo=activity_repo,
        emitter=emitter,
        event_bus=event_bus,
    )
    return service, lead_repo, transition_repo, activity_repo, emitter, event_bus


# ---------------------------------------------------------------------------
# SC-1: Happy-path adjacent stage transition
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_transition_stage_adjacent_forward_ok() -> None:
    """SC-1: adjacent forward transition interesado → calificando succeeds."""
    service, lead_repo, transition_repo, activity_repo, emitter, event_bus = _make_service()

    lead_before = _make_lead(stage="interesado", version=1)
    lead_after = _make_lead(stage="calificando", version=2)

    lead_repo.get_by_id = AsyncMock(return_value=lead_before)
    lead_repo.update_stage = AsyncMock(return_value=lead_after)
    transition_repo.record = AsyncMock(return_value=_make_transition("interesado", "calificando"))
    activity_repo.record = AsyncMock(return_value=_make_activity())

    result = await service.transition_stage(
        lead_id=LEAD_ID,
        tenant_id=TENANT_ID,
        to_stage="calificando",
        version=1,
        reason=None,
        triggered_by="manual_override",
        actor_user_id=USER_ID,
    )

    assert result.lead.stage == "calificando"
    assert result.lead.version == 2
    lead_repo.update_stage.assert_awaited_once()
    transition_repo.record.assert_awaited_once()
    activity_repo.record.assert_awaited_once()


# ---------------------------------------------------------------------------
# SC-1c: reason stored in transition record
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_transition_stage_reason_persisted() -> None:
    """SC-1c: reason text is passed to transition_repo.record (RN-4.1)."""
    service, lead_repo, transition_repo, activity_repo, emitter, event_bus = _make_service()

    lead_before = _make_lead(stage="interesado", version=1)
    lead_after = _make_lead(stage="calificando", version=2)

    lead_repo.get_by_id = AsyncMock(return_value=lead_before)
    lead_repo.update_stage = AsyncMock(return_value=lead_after)
    t = _make_transition("interesado", "calificando")
    t.reason = "El contacto solicitó información de precios."
    transition_repo.record = AsyncMock(return_value=t)
    activity_repo.record = AsyncMock(return_value=_make_activity())

    await service.transition_stage(
        lead_id=LEAD_ID,
        tenant_id=TENANT_ID,
        to_stage="calificando",
        version=1,
        reason="El contacto solicitó información de precios.",
        triggered_by="manual_override",
        actor_user_id=USER_ID,
    )

    call_kwargs = transition_repo.record.call_args.kwargs
    assert call_kwargs["reason"] == "El contacto solicitó información de precios."


# ---------------------------------------------------------------------------
# SC-2: Invalid stage transition (impossible jump)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_transition_invalid_stage_raises_error() -> None:
    """SC-2: jump from interesado → plan_presentado raises InvalidTransitionError."""
    service, lead_repo, transition_repo, activity_repo, emitter, event_bus = _make_service()

    lead_repo.get_by_id = AsyncMock(return_value=_make_lead(stage="interesado"))

    with pytest.raises(InvalidTransitionError) as exc_info:
        await service.transition_stage(
            lead_id=LEAD_ID,
            tenant_id=TENANT_ID,
            to_stage="plan_presentado",
            version=1,
            reason=None,
            triggered_by="manual_override",
            actor_user_id=USER_ID,
        )

    assert "calificando" in exc_info.value.allowed_next


# ---------------------------------------------------------------------------
# SC-reservado_manual: manual reservado forbidden (RN-4)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_transition_manual_reservado_forbidden() -> None:
    """RN-4: manual stage → reservado raises ManualReservadoForbiddenError (403)."""
    service, lead_repo, transition_repo, activity_repo, emitter, event_bus = _make_service()

    lead_repo.get_by_id = AsyncMock(return_value=_make_lead(stage="plan_presentado"))

    with pytest.raises(ManualReservadoForbiddenError):
        await service.transition_stage(
            lead_id=LEAD_ID,
            tenant_id=TENANT_ID,
            to_stage="reservado",
            version=1,
            reason=None,
            triggered_by="manual_override",
            actor_user_id=USER_ID,
        )


# ---------------------------------------------------------------------------
# SC-reason_required: backward transitions blocked by machine
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_transition_backward_blocked_by_machine() -> None:
    """Backward transition (calificando → interesado) blocked by STAGE_MACHINE (InvalidTransitionError).

    The machine only allows forward transitions. Backward moves raise InvalidTransitionError.
    ReasonRequiredError only applies for forward jumps when machine allows but it's non-adjacent.
    Per STAGE_MACHINE, all invalid moves hit InvalidTransitionError first.
    """
    service, lead_repo, transition_repo, activity_repo, emitter, event_bus = _make_service()

    lead_repo.get_by_id = AsyncMock(return_value=_make_lead(stage="calificando"))

    with pytest.raises(InvalidTransitionError) as exc_info:
        await service.transition_stage(
            lead_id=LEAD_ID,
            tenant_id=TENANT_ID,
            to_stage="interesado",  # not in allowed_next("calificando")
            version=1,
            reason=None,
            triggered_by="manual_override",
            actor_user_id=USER_ID,
        )
    assert "consulta_agendada" in exc_info.value.allowed_next


# ---------------------------------------------------------------------------
# SC-4: Lead not found for tenant
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_lead_detail_not_found_returns_none() -> None:
    """SC-4: cross-tenant lead returns None."""
    service, lead_repo, transition_repo, activity_repo, emitter, event_bus = _make_service()
    lead_repo.get_by_id = AsyncMock(return_value=None)
    activity_repo.list_for_lead = AsyncMock(return_value=[])

    result = await service.get_lead_detail(
        lead_id=LEAD_ID,
        tenant_id=TENANT_ID,
    )
    assert result is None


# ---------------------------------------------------------------------------
# SC-freeze: reactivate a frozen lead
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_reactivate_frozen_lead() -> None:
    """SC-freeze: reactivate clears is_frozen."""
    service, lead_repo, transition_repo, activity_repo, emitter, event_bus = _make_service()

    frozen_lead = _make_lead(stage="interesado", is_frozen=True)
    reactivated_lead = _make_lead(stage="interesado", is_frozen=False)

    lead_repo.get_by_id = AsyncMock(return_value=frozen_lead)
    lead_repo.reactivate = AsyncMock(return_value=reactivated_lead)
    activity_repo.record = AsyncMock(return_value=_make_activity())

    result = await service.reactivate(
        lead_id=LEAD_ID,
        tenant_id=TENANT_ID,
        objective="Nuevo blanqueamiento.",
    )

    assert result.is_frozen is False
    lead_repo.reactivate.assert_awaited_once()


# ---------------------------------------------------------------------------
# SC-board: board assembly
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_board_assembles_columns() -> None:
    """SC-board: get_board returns BoardResponse with stage columns."""
    service, lead_repo, transition_repo, activity_repo, emitter, event_bus = _make_service()

    lead_a = _make_lead(stage="interesado", score=30)
    lead_b_id = uuid4()
    lead_b = Lead(
        id=lead_b_id,
        tenant_id=TENANT_ID,
        name="Juan López",
        stage="calificando",
        score=50,
        version=1,
    )

    lead_repo.list_for_board = AsyncMock(return_value=[lead_a, lead_b])
    activity_repo.last_for_lead = AsyncMock(return_value=None)

    result = await service.get_board(
        tenant_id=TENANT_ID,
        stage_filter=None,
        sort="stage_age_desc",
    )

    column_stages = {col.stage for col in result.columns}
    assert "interesado" in column_stages
    assert "calificando" in column_stages


# ---------------------------------------------------------------------------
# SC-board-contract: board card exposes full FE contract (T-FE2bis)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_board_card_exposes_full_fe_contract() -> None:
    """T-FE2bis: every LeadCardDTO field the FE LeadCardDTO declares must be present.

    Critical fields tested:
    - version (non-optional, required for optimistic-concurrency drag-transition mutation)
    - tenant_id
    - is_frozen, frozen_reason, closure_reason, reactivation_cohort_at
    - service_interest, assigned_doctor_id, is_blacklisted
    - last_activity_description (mapped from activity description_es text)
    - last_activity_at (from activity.occurred_at, ISO 8601 string)

    RED before T-FE2bis fix: LeadCardDTO missing these fields.
    GREEN after: board card serialises full FE-required contract.
    """
    from decimal import Decimal
    from uuid import uuid4 as _uuid4

    service, lead_repo, transition_repo, activity_repo, emitter, event_bus = _make_service()

    doctor_id = _uuid4()
    reactivation_dt = datetime(2026, 7, 1, tzinfo=timezone.utc)
    stage_entered = datetime(2026, 5, 10, tzinfo=timezone.utc)

    lead = Lead(
        id=LEAD_ID,
        tenant_id=TENANT_ID,
        name="Ana Torres",
        stage="calificando",
        score=72,
        version=3,
        temperature="warm",
        operated_by="agent",
        channel="wa",
        estimated_value=Decimal("4500"),
        currency="MXN",
        buying_signals=["pregunta_precio", "solicita_cita"],
        is_frozen=False,
        frozen_reason=None,
        closure_reason=None,
        reactivation_cohort_at=reactivation_dt,
        deposit_status="pending",
        service_interest="implante_dental",
        assigned_doctor_id=doctor_id,
        is_blacklisted=False,
        stage_entered_at=stage_entered,
    )

    activity = _make_activity()
    activity.description_es = "Adrián envió el catálogo de implantes."
    activity.occurred_at = datetime(2026, 6, 1, 12, 0, 0, tzinfo=timezone.utc)

    lead_repo.list_for_board = AsyncMock(return_value=[lead])
    activity_repo.last_for_lead = AsyncMock(return_value=activity)

    result = await service.get_board(tenant_id=TENANT_ID)

    calificando_col = next((c for c in result.columns if c.stage == "calificando"), None)
    assert calificando_col is not None, "calificando column missing"
    assert len(calificando_col.leads) == 1
    card = calificando_col.leads[0]

    # version — CRITICAL for drag-transition mutation (SC-5)
    assert card.version == 3, "version missing from board card breaks drag-transition mutation"

    # tenant_id
    assert card.tenant_id == TENANT_ID

    # freeze / terminal state
    assert card.is_frozen is False
    assert card.frozen_reason is None
    assert card.closure_reason is None
    assert card.reactivation_cohort_at is not None  # ISO 8601 string

    # commercial metadata
    assert card.service_interest == "implante_dental"
    assert card.assigned_doctor_id == doctor_id
    assert card.is_blacklisted is False

    # last_activity mapped
    assert card.last_activity_description == "Adrián envió el catálogo de implantes."
    assert card.last_activity_at == "2026-06-01T12:00:00+00:00"


# ---------------------------------------------------------------------------
# SC-5: Optimistic lock conflict
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_transition_stale_version_raises_error() -> None:
    """SC-5: concurrent edit → StaleStateError from repo propagates."""
    service, lead_repo, transition_repo, activity_repo, emitter, event_bus = _make_service()

    lead_repo.get_by_id = AsyncMock(return_value=_make_lead(stage="interesado", version=1))
    lead_repo.update_stage = AsyncMock(side_effect=StaleStateError(LEAD_ID, 1))

    with pytest.raises(StaleStateError):
        await service.transition_stage(
            lead_id=LEAD_ID,
            tenant_id=TENANT_ID,
            to_stage="calificando",
            version=1,
            reason=None,
            triggered_by="manual_override",
            actor_user_id=USER_ID,
        )


# ---------------------------------------------------------------------------
# B2: get_lead_detail returns COMPUTED score, not STORED score
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_lead_detail_score_is_computed_not_stored() -> None:
    """B2: LeadDetailResponse.lead.score must reflect the computed score.

    Lead has score=0 stored (new lead, no transitions yet) but scorer.compute
    returns (10, [ScoreFactor(label='Etapa: interesado', delta=10)]) because
    the base for 'interesado' stage is 10 points.
    Expect: result.lead.score == 10 (computed), NOT 0 (stored).
    Expect: sum(f.delta for f in result.score_breakdown) == result.lead.score.

    RED before fix: _lead_to_response(lead) serialises lead.score (0 stored).
    GREEN after: detail response overrides .score with the computed value.
    """
    service, lead_repo, transition_repo, activity_repo, emitter, event_bus = _make_service()

    # Lead with score=0 STORED (new lead, never transitioned)
    lead = _make_lead(stage="interesado", score=0, buying_signals=[])
    lead_repo.get_by_id = AsyncMock(return_value=lead)

    result = await service.get_lead_detail(
        lead_id=LEAD_ID,
        tenant_id=TENANT_ID,
    )

    assert result is not None
    # Computed score must be > 0 (base for "interesado" = 10, not stored 0)
    assert result.lead.score != 0, "B2: detail.lead.score still 0 (stored) — must use computed value"
    # The score breakdown must be non-empty and sum to the reported score
    assert len(result.score_breakdown) > 0, "score_breakdown must not be empty"
    total = sum(f.delta for f in result.score_breakdown)
    assert result.lead.score == total, f"B2: detail.lead.score ({result.lead.score}) != sum(breakdown) ({total})"


# ---------------------------------------------------------------------------
# U2-BE: LeadResponse exposes assigned_doctor_id
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_lead_detail_exposes_assigned_doctor_id() -> None:
    """U2-BE: LeadDetailResponse.lead.assigned_doctor_id must be populated.

    Lead has assigned_doctor_id set.  The detail endpoint must forward it so
    the FE Resumen view can show the Doctor row (currently always blank).

    RED before fix: LeadResponse.assigned_doctor_id field missing.
    GREEN after: field present and matches lead's value.
    """
    from uuid import uuid4 as _uuid4

    service, lead_repo, transition_repo, activity_repo, emitter, event_bus = _make_service()

    doctor_id = _uuid4()
    lead = Lead(
        id=LEAD_ID,
        tenant_id=TENANT_ID,
        name="Carlos Ruiz",
        stage="interesado",
        score=0,
        version=1,
        assigned_doctor_id=doctor_id,
    )
    lead_repo.get_by_id = AsyncMock(return_value=lead)

    result = await service.get_lead_detail(
        lead_id=LEAD_ID,
        tenant_id=TENANT_ID,
    )

    assert result is not None
    assert result.lead.assigned_doctor_id == doctor_id, (
        "U2-BE: assigned_doctor_id not forwarded in LeadDetailResponse.lead"
    )
