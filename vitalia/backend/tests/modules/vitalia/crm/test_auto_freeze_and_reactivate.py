# cap: crm.adrian-embudo
# story-origin: vitalia-fase2-adrian-embudo
"""Tests for auto-freeze logic and reactivation (SC-freeze, RN-13).

Tests FunnelService.check_and_apply_freeze() and reactivate() with the
deterministic freeze rules from funnel_machine.py.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.modules.vitalia.crm.domain.lead import Lead
from src.modules.vitalia.crm.domain.lead_activity import LeadActivity

TENANT_ID = uuid4()
LEAD_ID = uuid4()


def _utc_now() -> datetime:
    return datetime.now(tz=timezone.utc)


def _make_lead_with_age(days_in_stage: int, days_since_response: int) -> Lead:
    stage_entered = _utc_now() - timedelta(days=days_in_stage)
    updated = _utc_now() - timedelta(days=days_since_response)
    return Lead(
        id=LEAD_ID,
        tenant_id=TENANT_ID,
        name="Paciente Test",
        stage="interesado",
        score=0,
        version=1,
        stage_entered_at=stage_entered,
        is_frozen=False,
        updated_at=updated,
    )


def _make_activity() -> LeadActivity:
    return LeadActivity(
        id=uuid4(),
        tenant_id=TENANT_ID,
        lead_id=LEAD_ID,
        actor="system",
        kind="stage_move",
        description_es="Se congeló el prospecto por inactividad.",
        occurred_at=_utc_now(),
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
# RN-13: Auto-freeze rules
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_check_freeze_no_response_14d_freezes() -> None:
    """RN-13: no response for 14d → should_freeze=True, reason=inactividad_lead."""
    from src.modules.vitalia.crm.domain.funnel_machine import should_freeze

    should, reason = should_freeze(
        stage="interesado",
        days_in_stage=10,
        days_since_last_response=14,
    )
    assert should is True
    assert reason == "inactividad_lead"


@pytest.mark.asyncio
async def test_check_freeze_30d_hard_cap_freezes() -> None:
    """RN-13: 30d in stage regardless of SLA → should_freeze=True."""
    from src.modules.vitalia.crm.domain.funnel_machine import should_freeze

    should, reason = should_freeze(
        stage="interesado",
        days_in_stage=30,
        days_since_last_response=5,
    )
    assert should is True
    assert reason == "sin_respuesta_presupuesto"


@pytest.mark.asyncio
async def test_check_freeze_2x_sla_freezes() -> None:
    """RN-13: >2× SLA for stage → should_freeze=True."""
    from src.modules.vitalia.crm.domain.funnel_machine import should_freeze

    # interesado SLA amber=7, threshold=14
    should, reason = should_freeze(
        stage="interesado",
        days_in_stage=15,  # >14 = 2×7
        days_since_last_response=5,
    )
    assert should is True
    assert reason == "agente_trabado"


@pytest.mark.asyncio
async def test_check_no_freeze_within_sla() -> None:
    """Within normal SLA — no freeze."""
    from src.modules.vitalia.crm.domain.funnel_machine import should_freeze

    should, reason = should_freeze(
        stage="interesado",
        days_in_stage=5,
        days_since_last_response=3,
    )
    assert should is False
    assert reason is None


# ---------------------------------------------------------------------------
# FunnelService.reactivate: clears frozen state
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_reactivate_clears_frozen() -> None:
    """reactivate() calls lead_repo.reactivate and records activity."""
    service, lead_repo, transition_repo, activity_repo, emitter, event_bus = _make_service()

    frozen_lead = _make_lead_with_age(20, 15)
    frozen_lead.is_frozen = True
    frozen_lead.frozen_reason = "inactividad_lead"

    reactivated = _make_lead_with_age(20, 15)
    reactivated.is_frozen = False

    lead_repo.get_by_id = AsyncMock(return_value=frozen_lead)
    lead_repo.reactivate = AsyncMock(return_value=reactivated)
    activity_repo.record = AsyncMock(return_value=_make_activity())

    result = await service.reactivate(
        lead_id=LEAD_ID,
        tenant_id=TENANT_ID,
        objective=None,
    )

    assert result.is_frozen is False
    lead_repo.reactivate.assert_awaited_once_with(LEAD_ID, tenant_id=TENANT_ID)
    activity_repo.record.assert_awaited_once()
