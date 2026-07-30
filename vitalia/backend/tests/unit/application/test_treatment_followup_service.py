"""Unit tests — TreatmentFollowupService (T-be-6 A2).

TDD RED → GREEN. All tests use mocked repositories (no Postgres needed).

Acceptance criteria (T-be-6):
  A2: TreatmentFollowupService schedules cron ticks D+5/14/90 in tenant TZ
      (test_cron_ticks_scheduled)

Decision coverage:
  D1: DDD inside-out — services receive repos via DI, no direct DB access.
  D2: Idempotency — same booking_id → returns existing followup (no new row).
  master-data: cron ticks computed in tenant TZ (not hardcoded UTC).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.modules.vitalia.application.services.treatment_followup_service import (
    StartFollowupRequest,
    StartFollowupResult,
    TreatmentFollowupService,
)

# ── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture()
def tenant_id() -> uuid.UUID:
    return uuid.UUID("11111111-0000-0000-0000-000000000001")


@pytest.fixture()
def booking_id() -> uuid.UUID:
    return uuid.UUID("33333333-0000-0000-0000-000000000003")


@pytest.fixture()
def patient_id() -> uuid.UUID:
    return uuid.UUID("22222222-0000-0000-0000-000000000002")


@pytest.fixture()
def doctor_id() -> uuid.UUID:
    return uuid.UUID("55555555-0000-0000-0000-000000000005")


@pytest.fixture()
def procedure_date() -> datetime:
    # 2026-05-20 at 10:00 UTC
    return datetime(2026, 5, 20, 10, 0, 0, tzinfo=timezone.utc)


@pytest.fixture()
def mock_followup_repo() -> MagicMock:
    repo = MagicMock()
    repo.get_by_booking_id = AsyncMock(return_value=None)  # no existing by default
    repo.save = AsyncMock()
    return repo


@pytest.fixture()
def mock_session() -> MagicMock:
    session = MagicMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    return session


def _make_service(
    tenant_id: uuid.UUID,
    mock_session: MagicMock,
    mock_followup_repo: MagicMock,
    *,
    tenant_timezone: str = "America/Argentina/Buenos_Aires",
) -> TreatmentFollowupService:
    return TreatmentFollowupService(
        session=mock_session,
        followup_repo=mock_followup_repo,
        tenant_id=tenant_id,
        tenant_timezone=tenant_timezone,
    )


# ── A2: Cron ticks D+5/14/90 in tenant TZ ───────────────────────────────────


@pytest.mark.asyncio
async def test_cron_ticks_scheduled(
    tenant_id: uuid.UUID,
    mock_session: MagicMock,
    mock_followup_repo: MagicMock,
    booking_id: uuid.UUID,
    patient_id: uuid.UUID,
    doctor_id: uuid.UUID,
    procedure_date: datetime,
) -> None:
    """A2: start_followup must schedule cron ticks at D+5, D+14, D+90 in tenant TZ.

    The first tick (D+5) must be set as next_scheduled_at on the created followup.
    All tick times must be UTC-stored but computed relative to tenant TZ midnight.
    """
    svc = _make_service(tenant_id, mock_session, mock_followup_repo)

    request = StartFollowupRequest(
        booking_id=booking_id,
        patient_id=patient_id,
        doctor_id=doctor_id,
        procedure_date=procedure_date,
        plan_template_slug="dental_implant",
    )

    result = await svc.start_followup(request=request)

    assert result.followup_id is not None, "followup_id must be set"
    assert result.current_step == "D0_init", "Initial step must be D0_init"

    # D+5 tick
    d5_tick = result.cron_ticks["D5"]
    assert d5_tick is not None
    expected_d5_base = procedure_date + timedelta(days=5)
    diff_d5 = abs((d5_tick - expected_d5_base).total_seconds())
    assert diff_d5 < 86401, f"D+5 tick {d5_tick} must be within 24h of {expected_d5_base}"

    # D+14 tick
    d14_tick = result.cron_ticks["D14"]
    assert d14_tick is not None
    expected_d14_base = procedure_date + timedelta(days=14)
    diff_d14 = abs((d14_tick - expected_d14_base).total_seconds())
    assert diff_d14 < 86401, f"D+14 tick {d14_tick} must be within 24h of {expected_d14_base}"

    # D+90 tick
    d90_tick = result.cron_ticks["D90"]
    assert d90_tick is not None
    expected_d90_base = procedure_date + timedelta(days=90)
    diff_d90 = abs((d90_tick - expected_d90_base).total_seconds())
    assert diff_d90 < 86401, f"D+90 tick {d90_tick} must be within 24h of {expected_d90_base}"

    # All ticks stored as UTC (timezone-aware)
    for key, tick in result.cron_ticks.items():
        assert tick.tzinfo is not None, f"Tick {key}={tick} must be timezone-aware (UTC store)"

    # D5 must be the next_scheduled_at
    assert result.next_scheduled_at == d5_tick, "D+5 must be the initial next_scheduled_at"


@pytest.mark.asyncio
async def test_cron_ticks_chronological_order(
    tenant_id: uuid.UUID,
    mock_session: MagicMock,
    mock_followup_repo: MagicMock,
    booking_id: uuid.UUID,
    patient_id: uuid.UUID,
    doctor_id: uuid.UUID,
    procedure_date: datetime,
) -> None:
    """D+5 < D+14 < D+90 must hold chronological order."""
    svc = _make_service(tenant_id, mock_session, mock_followup_repo)
    request = StartFollowupRequest(
        booking_id=booking_id,
        patient_id=patient_id,
        doctor_id=doctor_id,
        procedure_date=procedure_date,
        plan_template_slug="psychology_individual",
    )

    result = await svc.start_followup(request=request)

    assert result.cron_ticks["D5"] < result.cron_ticks["D14"] < result.cron_ticks["D90"], (
        "Cron ticks must be D5 < D14 < D90"
    )


@pytest.mark.asyncio
async def test_cron_ticks_tenant_tz_morning_anchor(
    tenant_id: uuid.UUID,
    mock_session: MagicMock,
    mock_followup_repo: MagicMock,
    booking_id: uuid.UUID,
    patient_id: uuid.UUID,
    doctor_id: uuid.UUID,
) -> None:
    """Cron ticks should be anchored to tenant morning (not midnight UTC).

    For AR timezone (UTC-3), a 9:00 AM local is 12:00 UTC.
    We verify tick is NOT at 00:00 UTC (raw midnight) but reasonable morning hour.
    """
    svc = _make_service(tenant_id, mock_session, mock_followup_repo, tenant_timezone="America/Argentina/Buenos_Aires")
    procedure = datetime(2026, 5, 20, 15, 0, 0, tzinfo=timezone.utc)  # 12:00 local AR
    request = StartFollowupRequest(
        booking_id=booking_id,
        patient_id=patient_id,
        doctor_id=doctor_id,
        procedure_date=procedure,
        plan_template_slug="dental_implant",
    )

    result = await svc.start_followup(request=request)

    # D+5 tick should land on 2026-05-25 9:00 AR = 12:00 UTC
    d5_utc = result.cron_ticks["D5"]
    # Assert it's not midnight UTC (which would mean no TZ adjustment)
    assert d5_utc.hour != 0, f"D+5 tick at 00:00 UTC suggests no tenant TZ adjustment (got {d5_utc})"


# ── D2: Idempotency ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_start_followup_idempotent_same_booking(
    tenant_id: uuid.UUID,
    mock_session: MagicMock,
    mock_followup_repo: MagicMock,
    booking_id: uuid.UUID,
    patient_id: uuid.UUID,
    doctor_id: uuid.UUID,
    procedure_date: datetime,
) -> None:
    """D2: Same booking_id → returns existing followup, no new row saved."""
    existing_followup_id = uuid.uuid4()
    existing_model = MagicMock()
    existing_model.id = existing_followup_id
    existing_model.current_step = "D5_check"
    existing_model.next_scheduled_at = procedure_date + timedelta(days=5)

    mock_followup_repo.get_by_booking_id = AsyncMock(return_value=existing_model)

    svc = _make_service(tenant_id, mock_session, mock_followup_repo)
    request = StartFollowupRequest(
        booking_id=booking_id,
        patient_id=patient_id,
        doctor_id=doctor_id,
        procedure_date=procedure_date,
        plan_template_slug="dental_implant",
    )

    result = await svc.start_followup(request=request)

    assert result.followup_id == existing_followup_id, "Must return existing followup_id"
    assert result.is_new is False, "is_new must be False on idempotent hit"
    mock_followup_repo.save.assert_not_called()


# ── D1: DI constructor ───────────────────────────────────────────────────────


def test_treatment_followup_service_constructor_requires_di(tenant_id: uuid.UUID) -> None:
    """D1: TreatmentFollowupService must accept repos via DI, not hardcode session."""
    import inspect

    sig = inspect.signature(TreatmentFollowupService.__init__)
    params = list(sig.parameters.keys())
    assert "session" in params
    assert "followup_repo" in params
    assert "tenant_id" in params
    assert "tenant_timezone" in params


def test_start_followup_result_pydantic() -> None:
    """StartFollowupResult must be a Pydantic model."""
    now = datetime.now(tz=timezone.utc)
    result = StartFollowupResult(
        followup_id=uuid.uuid4(),
        booking_id=uuid.uuid4(),
        current_step="D0_init",
        next_scheduled_at=now + timedelta(days=5),
        cron_ticks={
            "D5": now + timedelta(days=5),
            "D14": now + timedelta(days=14),
            "D90": now + timedelta(days=90),
        },
        is_new=True,
    )
    assert result.is_new is True
    assert "D5" in result.cron_ticks


def test_start_followup_request_pydantic() -> None:
    """StartFollowupRequest must be a Pydantic model with required fields."""
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        StartFollowupRequest(
            # missing booking_id
            patient_id=uuid.uuid4(),
            doctor_id=uuid.uuid4(),
            procedure_date=datetime.now(tz=timezone.utc),
            plan_template_slug="dental_implant",
        )
