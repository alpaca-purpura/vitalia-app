# cap: clinics.lisa.doctores
"""Tests: availability-occurrences range endpoint (T-BE-occurrences-endpoint, D3-C).

TDD RED-first — battery SC-D3C-1..8 written BEFORE the implementation
(tdd-mandatory + hotfix-repro: the RED regression reproduces the indefinite-paint
bug server-side if the count-based series restarts at every queried window).

Root cause (repro Chris live 2026-06-11, trace_evidence in 06-tickets.yaml):
FE `recurrentBlockVisibleInWeek` ignores `occurrences` → paints forever. BE
`rrule(count)` is correct; this endpoint becomes the projection SSoT the FE
consumes (T-FE-occurrences-consume).

Validators: V-D3C-1..8 (04-validators.yaml)
Gherkin coverage: SC-D3C-1, SC-D3C-2, SC-D3C-3, SC-D3C-4, SC-D3C-5, SC-D3C-6,
                  SC-D3C-7, SC-D3C-8

Anchor invariant under test (impl-log § Plan):
  - the recurrence series anchors at block.created_at.date() (the reference_date
    used when slots were materialized on create) — NEVER at the query window
    start. Re-anchoring per window = N occurrences in EVERY window = the bug.
  - open_ended uses a rolling today+90d horizon (mirrors materialization).
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.modules.vitalia.clinics.domain.availability_block import AvailabilityBlock

# 2026-06-01 is a Monday (same fixed anchor as test_availability_projection.py)
MONDAY = date(2026, 6, 1)
MONDAY_CREATED_AT = datetime(2026, 6, 1, 8, 0, tzinfo=timezone.utc)

VALID_TENANT = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
VALID_CLINIC = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
VALID_DOCTOR = "cccccccc-cccc-cccc-cccc-cccccccccccc"
VALID_USER = "eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee"


# ── Factories ─────────────────────────────────────────────────────────────────


def _recurrent_block(
    *,
    created_at: datetime = MONDAY_CREATED_AT,
    day_of_week: int = 0,
    freq: str = "weekly",
    end_condition_kind: str = "occurrences",
    end_date: date | None = None,
    occurrences: int | None = 2,
    start_time: time = time(9, 0),
    end_time: time = time(12, 0),
    tenant_id: UUID | None = None,
    clinic_id: UUID | None = None,
    doctor_id: UUID | None = None,
    block_id: UUID | None = None,
) -> AvailabilityBlock:
    """Recurrent AvailabilityBlock with a controllable creation anchor."""
    return AvailabilityBlock(
        id=block_id or uuid4(),
        tenant_id=tenant_id or uuid4(),
        clinic_id=clinic_id or uuid4(),
        doctor_id=doctor_id or uuid4(),
        kind="recurrent",
        start_time=start_time,
        end_time=end_time,
        day_of_week=day_of_week,
        freq=freq,  # type: ignore[arg-type]
        end_condition_kind=end_condition_kind,  # type: ignore[arg-type]
        end_date=end_date,
        occurrences=occurrences,
        specific_date=None,
        created_at=created_at,
        updated_at=created_at,
    )


def _one_off_block(
    *,
    specific_date: date,
    start_time: time = time(10, 0),
    end_time: time = time(11, 0),
    tenant_id: UUID | None = None,
    clinic_id: UUID | None = None,
    doctor_id: UUID | None = None,
) -> AvailabilityBlock:
    """One-off AvailabilityBlock."""
    return AvailabilityBlock(
        id=uuid4(),
        tenant_id=tenant_id or uuid4(),
        clinic_id=clinic_id or uuid4(),
        doctor_id=doctor_id or uuid4(),
        kind="one_off",
        start_time=start_time,
        end_time=end_time,
        specific_date=specific_date,
    )


def _service_with_blocks(blocks: list[AvailabilityBlock]) -> tuple[object, AsyncMock]:
    """Real AvailabilityBlockService wired to a mocked repo returning `blocks`."""
    from src.modules.vitalia.clinics.application.availability_block_service import (
        AvailabilityBlockService,
    )

    mock_repo = AsyncMock()
    mock_repo.list_blocks.return_value = blocks
    svc = AvailabilityBlockService(block_repo=mock_repo, audit_repo=AsyncMock())
    return svc, mock_repo


async def _occurrences(svc: object, block: AvailabilityBlock, range_start: date, range_end: date) -> list[object]:
    """Shortcut: list occurrences for the block's own scope ids."""
    return await svc.list_occurrences(  # type: ignore[attr-defined]
        doctor_id=block.doctor_id,
        tenant_id=block.tenant_id,
        clinic_id=block.clinic_id,
        range_start=range_start,
        range_end=range_end,
    )


# ──────────────────────────────────────────────────────────────────────────────
# SC-D3C-1 ★REGRESSION — weekly occurrences=2 → EXACTLY 2 dates, EVER
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_sc_d3c_1_weekly_occurrences_2_exactly_2_dates() -> None:
    """★REGRESSION (repro Chris): weekly × occurrences=2 → EXACTLY 2 occurrence dates.

    Wide window covering 8 weeks must yield ONLY {Jun 1, Jun 8} — the off-by-week
    guard: a 3rd+ date means the series leaked past its count.
    """
    block = _recurrent_block(occurrences=2)
    svc, _ = _service_with_blocks([block])

    result = await _occurrences(svc, block, MONDAY, MONDAY + timedelta(days=55))

    dates = [o.occurrence_date for o in result]
    assert dates == [date(2026, 6, 1), date(2026, 6, 8)], (
        f"weekly occurrences=2 must project EXACTLY [Jun 1, Jun 8], got {dates}"
    )


@pytest.mark.asyncio
async def test_sc_d3c_1_regression_later_window_is_empty() -> None:
    """★REGRESSION core: a window AFTER the 2 occurrences elapsed → ZERO occurrences.

    If the implementation re-anchors rrule(count=2) at the window start (the
    architect sketch's literal `reference_date=from`), every window returns 2
    dates → the indefinite-paint bug reproduced server-side. This test is the
    RED that pins the anchor at block creation.
    """
    block = _recurrent_block(occurrences=2)  # series: Jun 1 + Jun 8 only
    svc, _ = _service_with_blocks([block])

    result = await _occurrences(svc, block, date(2026, 7, 1), date(2026, 7, 31))

    assert result == [], (
        f"block exhausted its 2 occurrences in June — July window must be EMPTY, "
        f"got {[o.occurrence_date for o in result]} (count restarted per window = the FE bug, server-side)"
    )


# ──────────────────────────────────────────────────────────────────────────────
# SC-D3C-2 — biweekly occurrences=3 → 3 dates spaced 14d (span 6 weeks)
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_sc_d3c_2_biweekly_occurrences_3_spaced_14d() -> None:
    """biweekly × occurrences=3 → exactly 3 dates, 14 days apart (NOT weekly)."""
    block = _recurrent_block(freq="biweekly", occurrences=3)
    svc, _ = _service_with_blocks([block])

    result = await _occurrences(svc, block, MONDAY, MONDAY + timedelta(days=41))

    dates = [o.occurrence_date for o in result]
    assert dates == [date(2026, 6, 1), date(2026, 6, 15), date(2026, 6, 29)], (
        f"biweekly occurrences=3 anchored Jun 1 must be [Jun 1, Jun 15, Jun 29], got {dates}"
    )
    deltas = [(dates[i + 1] - dates[i]).days for i in range(len(dates) - 1)]
    assert deltas == [14, 14], f"biweekly spacing must be 14d, got {deltas}"


@pytest.mark.asyncio
async def test_sc_d3c_2_biweekly_off_parity_week_is_empty() -> None:
    """Biweekly parity anchors at creation: the in-between week has NO occurrence.

    Window [Jun 8, Jun 14] sits between Jun 1 and Jun 15 → empty. If dtstart
    re-derives from the window start, parity flips and Jun 8 appears (bug).
    """
    block = _recurrent_block(freq="biweekly", occurrences=3)
    svc, _ = _service_with_blocks([block])

    result = await _occurrences(svc, block, date(2026, 6, 8), date(2026, 6, 14))

    assert result == [], (
        f"off-parity week must be empty for biweekly series anchored Jun 1, got {[o.occurrence_date for o in result]}"
    )


# ──────────────────────────────────────────────────────────────────────────────
# SC-D3C-3 — end_date inclusive (TZ tenant)
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_sc_d3c_3_end_date_on_occurrence_day_is_inclusive() -> None:
    """end_date landing ON an occurrence day INCLUDES that final day."""
    block = _recurrent_block(end_condition_kind="end_date", end_date=date(2026, 6, 15), occurrences=None)
    svc, _ = _service_with_blocks([block])

    result = await _occurrences(svc, block, MONDAY, MONDAY + timedelta(days=27))

    dates = [o.occurrence_date for o in result]
    assert date(2026, 6, 15) in dates, f"end_date Jun 15 (a Monday) must be INCLUDED, got {dates}"
    assert dates == [date(2026, 6, 1), date(2026, 6, 8), date(2026, 6, 15)]


@pytest.mark.asyncio
async def test_sc_d3c_3_end_date_before_next_occurrence_excludes_it() -> None:
    """end_date the day BEFORE an occurrence excludes it (no off-by-one overshoot)."""
    block = _recurrent_block(end_condition_kind="end_date", end_date=date(2026, 6, 14), occurrences=None)
    svc, _ = _service_with_blocks([block])

    result = await _occurrences(svc, block, MONDAY, MONDAY + timedelta(days=27))

    dates = [o.occurrence_date for o in result]
    assert dates == [date(2026, 6, 1), date(2026, 6, 8)], (
        f"end_date Jun 14 (Sunday) must NOT include Monday Jun 15, got {dates}"
    )


# ──────────────────────────────────────────────────────────────────────────────
# SC-D3C-4 — open_ended → rolling 90d horizon (ni corta ni infinita)
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_sc_d3c_4_open_ended_old_block_still_paints_today() -> None:
    """open_ended block created 100 days ago still paints the current window (ni corta).

    The horizon rolls from today (mirrors re-materialization), NOT from creation —
    otherwise old open-ended blocks would vanish from the calendar.
    """
    today = datetime.now(tz=timezone.utc).date()
    anchor = today - timedelta(days=100)
    block = _recurrent_block(
        created_at=datetime.combine(anchor, time(8, 0), tzinfo=timezone.utc),
        day_of_week=anchor.weekday(),
        end_condition_kind="open_ended",
        occurrences=None,
    )
    svc, _ = _service_with_blocks([block])

    result = await _occurrences(svc, block, today, today + timedelta(days=13))

    assert len(result) == 2, (
        f"weekly open_ended must have exactly 2 occurrences in any 14-day window, "
        f"got {len(result)}: {[o.occurrence_date for o in result]}"
    )


@pytest.mark.asyncio
async def test_sc_d3c_4_open_ended_respects_90d_horizon() -> None:
    """open_ended projects up to today+90d and NOT beyond (ni infinita)."""
    today = datetime.now(tz=timezone.utc).date()
    anchor = today - timedelta(days=100)
    block = _recurrent_block(
        created_at=datetime.combine(anchor, time(8, 0), tzinfo=timezone.utc),
        day_of_week=anchor.weekday(),
        end_condition_kind="open_ended",
        occurrences=None,
    )
    svc, _ = _service_with_blocks([block])

    horizon = today + timedelta(days=90)
    result = await _occurrences(svc, block, today + timedelta(days=34), today + timedelta(days=95))

    dates = [o.occurrence_date for o in result]
    assert dates, "open_ended must still paint inside the horizon (ni corta)"
    beyond = [d for d in dates if d > horizon]
    assert not beyond, f"occurrences beyond today+90d horizon: {beyond}"
    assert any(d >= horizon - timedelta(days=6) for d in dates), (
        f"weekly series must reach the final horizon week (ni corta), got max {max(dates)} vs horizon {horizon}"
    )


# ──────────────────────────────────────────────────────────────────────────────
# SC-D3C-5 — edit does NOT reset/duplicate the count
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_sc_d3c_5_edit_preserves_count_no_reset_no_duplicates() -> None:
    """Editing a recurrent block (same id/created_at, new times) keeps the SAME 2 dates.

    The series anchors at created_at (stable across edits) — updated_at moving
    forward must NOT re-anchor (reset) the count nor duplicate occurrences.
    """
    block_id = uuid4()
    tid, cid, did = uuid4(), uuid4(), uuid4()
    original = _recurrent_block(
        block_id=block_id,
        tenant_id=tid,
        clinic_id=cid,
        doctor_id=did,
        occurrences=2,
        start_time=time(9, 0),
        end_time=time(12, 0),
    )
    edited = _recurrent_block(
        block_id=block_id,
        tenant_id=tid,
        clinic_id=cid,
        doctor_id=did,
        occurrences=2,
        start_time=time(10, 0),
        end_time=time(13, 0),
    )
    edited.updated_at = MONDAY_CREATED_AT + timedelta(days=3)  # edit 3 days later

    svc_before, _ = _service_with_blocks([original])
    svc_after, _ = _service_with_blocks([edited])
    window_end = MONDAY + timedelta(days=55)

    before = await _occurrences(svc_before, original, MONDAY, window_end)
    after = await _occurrences(svc_after, edited, MONDAY, window_end)

    dates_before = [o.occurrence_date for o in before]
    dates_after = [o.occurrence_date for o in after]
    assert dates_after == dates_before == [date(2026, 6, 1), date(2026, 6, 8)], (
        f"edit must not reset the series: before={dates_before} after={dates_after}"
    )
    assert len(dates_after) == len(set(dates_after)), "edit must not duplicate occurrences"


@pytest.mark.asyncio
async def test_sc_d3c_5_listing_twice_is_idempotent() -> None:
    """The projection is a pure read — listing twice yields identical results."""
    block = _recurrent_block(occurrences=2)
    svc, _ = _service_with_blocks([block])

    first = await _occurrences(svc, block, MONDAY, MONDAY + timedelta(days=55))
    second = await _occurrences(svc, block, MONDAY, MONDAY + timedelta(days=55))

    assert [(o.block_id, o.occurrence_date) for o in first] == [(o.block_id, o.occurrence_date) for o in second]


# ──────────────────────────────────────────────────────────────────────────────
# SC-D3C-6 — one_off + recurrent overlapping the same day → both visible
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_sc_d3c_6_one_off_and_recurrent_overlap_same_day_both_returned() -> None:
    """A one_off on Jun 8 + recurrent hitting Jun 8 → BOTH occurrences on that date."""
    tid, cid, did = uuid4(), uuid4(), uuid4()
    recurrent = _recurrent_block(tenant_id=tid, clinic_id=cid, doctor_id=did, occurrences=2)
    one_off = _one_off_block(specific_date=date(2026, 6, 8), tenant_id=tid, clinic_id=cid, doctor_id=did)
    svc, _ = _service_with_blocks([recurrent, one_off])

    result = await _occurrences(svc, recurrent, MONDAY, MONDAY + timedelta(days=13))

    assert len(result) == 3, f"expected 3 occurrences (Jun 1 + 2× Jun 8), got {len(result)}"
    on_jun_8 = [o for o in result if o.occurrence_date == date(2026, 6, 8)]
    assert len(on_jun_8) == 2, f"Jun 8 must show BOTH blocks, got {len(on_jun_8)}"
    assert {o.block_id for o in on_jun_8} == {recurrent.id, one_off.id}
    kinds = {o.block_id: o.kind for o in on_jun_8}
    assert kinds[one_off.id] == "one_off"
    assert kinds[recurrent.id] == "recurrent"


# ──────────────────────────────────────────────────────────────────────────────
# SC-D3C-7 — deleted block → ALL its occurrences gone (active blocks only)
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_sc_d3c_7_occurrences_derive_only_from_active_blocks() -> None:
    """Occurrences come ONLY from active (non-deleted) blocks — post-delete → empty.

    The repo's list_blocks already excludes soft-deleted rows; the service must
    delegate with the dual filter and project nothing once the block is gone.
    """
    block = _recurrent_block(occurrences=2)
    svc, mock_repo = _service_with_blocks([])  # repo state AFTER delete

    result = await _occurrences(svc, block, MONDAY, MONDAY + timedelta(days=55))

    assert result == [], "deleted block must contribute ZERO occurrences"
    mock_repo.list_blocks.assert_awaited_once_with(
        tenant_id=block.tenant_id, clinic_id=block.clinic_id, doctor_id=block.doctor_id
    )


# ──────────────────────────────────────────────────────────────────────────────
# SC-D3C-8 — TZ midnight border → correct day
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_sc_d3c_8_midnight_block_lands_on_correct_day() -> None:
    """A block starting at 00:00 UTC projects on its own weekday — no day shift."""
    block = _recurrent_block(occurrences=1, start_time=time(0, 0), end_time=time(2, 0))
    svc, _ = _service_with_blocks([block])

    result = await _occurrences(svc, block, MONDAY, MONDAY + timedelta(days=6))

    assert len(result) == 1
    assert result[0].occurrence_date == date(2026, 6, 1), (
        f"midnight block anchored Monday must land on Jun 1, got {result[0].occurrence_date}"
    )
    assert result[0].occurrence_date.weekday() == 0


@pytest.mark.asyncio
async def test_sc_d3c_8_sunday_weekday_resolves_correct_date() -> None:
    """day_of_week=6 (Sunday) anchored on a Monday → first occurrence is NEXT Sunday."""
    block = _recurrent_block(occurrences=1, day_of_week=6)
    svc, _ = _service_with_blocks([block])

    result = await _occurrences(svc, block, MONDAY, MONDAY + timedelta(days=13))

    assert [o.occurrence_date for o in result] == [date(2026, 6, 7)]
    assert result[0].occurrence_date.weekday() == 6


# ──────────────────────────────────────────────────────────────────────────────
# Range validation — cap 62 days, to >= from (service-level business rule)
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_range_longer_than_62_days_raises_value_error() -> None:
    """Range > 62 days → ValueError (unbounded projection guard, arch § 4.3)."""
    block = _recurrent_block()
    svc, _ = _service_with_blocks([block])

    with pytest.raises(ValueError, match="62"):
        await _occurrences(svc, block, MONDAY, MONDAY + timedelta(days=63))


@pytest.mark.asyncio
async def test_range_end_before_start_raises_value_error() -> None:
    """to < from → ValueError."""
    block = _recurrent_block()
    svc, _ = _service_with_blocks([block])

    with pytest.raises(ValueError):
        await _occurrences(svc, block, MONDAY, MONDAY - timedelta(days=1))


# ──────────────────────────────────────────────────────────────────────────────
# format_recurrence_summary — SSoT human pattern (RN-D3F-1, pre-D3-F wording)
# ──────────────────────────────────────────────────────────────────────────────


def test_format_recurrence_summary_one_off() -> None:
    """one_off → 'Único'."""
    from src.modules.vitalia.clinics.application.recurrence_summary import (
        format_recurrence_summary,
    )

    assert format_recurrence_summary(_one_off_block(specific_date=date(2026, 6, 8))) == "Único"


def test_format_recurrence_summary_weekly() -> None:
    """recurrent weekly → 'Semanal'."""
    from src.modules.vitalia.clinics.application.recurrence_summary import (
        format_recurrence_summary,
    )

    assert format_recurrence_summary(_recurrent_block(freq="weekly")) == "Semanal"


def test_format_recurrence_summary_biweekly() -> None:
    """recurrent biweekly → 'Quincenal'."""
    from src.modules.vitalia.clinics.application.recurrence_summary import (
        format_recurrence_summary,
    )

    assert format_recurrence_summary(_recurrent_block(freq="biweekly")) == "Quincenal"


@pytest.mark.asyncio
async def test_occurrence_pattern_summary_uses_shared_formatter() -> None:
    """BlockOccurrence.pattern_summary comes from the shared SSoT formatter."""
    block = _recurrent_block(freq="biweekly", occurrences=3)
    svc, _ = _service_with_blocks([block])

    result = await _occurrences(svc, block, MONDAY, MONDAY + timedelta(days=41))

    assert all(o.pattern_summary == "Quincenal" for o in result)
    assert all(o.freq == "biweekly" for o in result)


# ──────────────────────────────────────────────────────────────────────────────
# Endpoint — GET /{doctor_id}/availability-occurrences (router thin layer)
# ──────────────────────────────────────────────────────────────────────────────


def _make_client(monkeypatch: pytest.MonkeyPatch, blocks: list[AvailabilityBlock]) -> TestClient:
    """Minimal app with doctors_router; real service + mocked repo (no DB)."""
    import src.modules.vitalia.clinics.api.doctors_router as doctors_router_module
    from src.modules.vitalia.clinics.api.doctors_router import _get_db, router
    from src.modules.vitalia.clinics.application.availability_block_service import (
        AvailabilityBlockService,
    )

    def _fake_build_block_service(db: object) -> AvailabilityBlockService:  # noqa: ARG001
        mock_repo = AsyncMock()
        mock_repo.list_blocks.return_value = blocks
        return AvailabilityBlockService(block_repo=mock_repo, audit_repo=AsyncMock())

    monkeypatch.setattr(doctors_router_module, "_build_block_service", _fake_build_block_service)

    test_app = FastAPI(redirect_slashes=False)
    test_app.include_router(router, prefix="/api/v1/vitalia/clinics/doctors")

    async def _fake_db():  # noqa: ANN202
        yield None  # type: ignore[misc]

    test_app.dependency_overrides[_get_db] = _fake_db
    return TestClient(test_app, raise_server_exceptions=False)


def _occ_headers() -> dict[str, str]:
    return {
        "X-Tenant-ID": VALID_TENANT,
        "X-Clinic-ID": VALID_CLINIC,
        "X-User-ID": VALID_USER,
    }


def test_availability_occurrences_route_has_response_model() -> None:
    """GET /{doctor_id}/availability-occurrences must declare response_model= (arch gate)."""
    from src.modules.vitalia.clinics.api.doctors_router import router

    routes = [
        r
        for r in router.routes
        if hasattr(r, "path") and "availability-occurrences" in r.path and "GET" in getattr(r, "methods", set())
    ]
    assert routes, "GET /{doctor_id}/availability-occurrences route not found"
    assert getattr(routes[0], "response_model", None) is not None


def test_get_occurrences_happy_path_camelcase_contract(monkeypatch: pytest.MonkeyPatch) -> None:
    """200 + camelCase wire contract (blockId/occurrenceDate/startTime/endTime/kind/freq/patternSummary).

    Real-contract guard: the FE hook (T-FE-occurrences-consume) consumes camelCase —
    4th imagined-contract instance must not recur (learning 2026-06-04).
    """
    block = _recurrent_block(occurrences=2)
    client = _make_client(monkeypatch, [block])

    resp = client.get(
        f"/api/v1/vitalia/clinics/doctors/{VALID_DOCTOR}/availability-occurrences",
        params={"from": "2026-06-01", "to": "2026-06-28"},
        headers=_occ_headers(),
    )

    assert resp.status_code == 200, f"expected 200, got {resp.status_code}: {resp.text[:300]}"
    body = resp.json()
    assert "occurrences" in body
    assert len(body["occurrences"]) == 2
    first = body["occurrences"][0]
    for key in ("blockId", "occurrenceDate", "startTime", "endTime", "kind", "freq", "patternSummary"):
        assert key in first, f"camelCase key '{key}' missing in occurrence payload: {sorted(first)}"
    assert first["occurrenceDate"] == "2026-06-01"
    assert first["patternSummary"] == "Semanal"
    assert first["blockId"] == str(block.id)


def test_get_occurrences_range_over_62_days_returns_422(monkeypatch: pytest.MonkeyPatch) -> None:
    """from/to spanning > 62 days → 422 invalid_range (unbounded projection guard)."""
    client = _make_client(monkeypatch, [])

    resp = client.get(
        f"/api/v1/vitalia/clinics/doctors/{VALID_DOCTOR}/availability-occurrences",
        params={"from": "2026-06-01", "to": "2026-08-15"},
        headers=_occ_headers(),
    )

    assert resp.status_code == 422, f"expected 422 for 75-day range, got {resp.status_code}"


def test_get_occurrences_to_before_from_returns_422(monkeypatch: pytest.MonkeyPatch) -> None:
    """to < from → 422."""
    client = _make_client(monkeypatch, [])

    resp = client.get(
        f"/api/v1/vitalia/clinics/doctors/{VALID_DOCTOR}/availability-occurrences",
        params={"from": "2026-06-15", "to": "2026-06-01"},
        headers=_occ_headers(),
    )

    assert resp.status_code == 422


def test_get_occurrences_missing_user_id_header_returns_422(monkeypatch: pytest.MonkeyPatch) -> None:
    """X-User-ID required (detail-endpoint consistency — useStaffActorHeaders)."""
    client = _make_client(monkeypatch, [])

    resp = client.get(
        f"/api/v1/vitalia/clinics/doctors/{VALID_DOCTOR}/availability-occurrences",
        params={"from": "2026-06-01", "to": "2026-06-28"},
        headers={"X-Tenant-ID": VALID_TENANT, "X-Clinic-ID": VALID_CLINIC},
    )

    assert resp.status_code == 422, f"missing X-User-ID must 422, got {resp.status_code}"


def test_get_occurrences_malformed_tenant_header_returns_422(monkeypatch: pytest.MonkeyPatch) -> None:
    """Malformed X-Tenant-ID → 422 (UUID-typed header, T-FIX-1-BE convention)."""
    client = _make_client(monkeypatch, [])

    resp = client.get(
        f"/api/v1/vitalia/clinics/doctors/{VALID_DOCTOR}/availability-occurrences",
        params={"from": "2026-06-01", "to": "2026-06-28"},
        headers={"X-Tenant-ID": "not-a-uuid", "X-Clinic-ID": VALID_CLINIC, "X-User-ID": VALID_USER},
    )

    assert resp.status_code == 422


# ──────────────────────────────────────────────────────────────────────────────
# D3-F: Multi-day + interval recurrence (T-BE-recurrencia-domain)
# ──────────────────────────────────────────────────────────────────────────────
# RED tests written BEFORE the domain entity extension (TDD mandatory).
# These fail until availability_block.py gains days_of_week + interval fields
# and projection/summary are extended.
#
# Factory helper for D3-F blocks — passes days_of_week + interval directly.


def _multi_day_block(
    *,
    created_at: datetime = MONDAY_CREATED_AT,
    days_of_week: list[int],
    interval: int = 1,
    end_condition_kind: str = "occurrences",
    end_date: date | None = None,
    occurrences: int | None = None,
    start_time: time = time(9, 0),
    end_time: time = time(12, 0),
    tenant_id: UUID | None = None,
    clinic_id: UUID | None = None,
    doctor_id: UUID | None = None,
    block_id: UUID | None = None,
) -> AvailabilityBlock:
    """Factory for D3-F multi-day recurrent blocks (days_of_week list + interval)."""
    return AvailabilityBlock(
        id=block_id or uuid4(),
        tenant_id=tenant_id or uuid4(),
        clinic_id=clinic_id or uuid4(),
        doctor_id=doctor_id or uuid4(),
        kind="recurrent",
        start_time=start_time,
        end_time=end_time,
        days_of_week=days_of_week,
        interval=interval,
        end_condition_kind=end_condition_kind,  # type: ignore[arg-type]
        end_date=end_date,
        occurrences=occurrences,
        specific_date=None,
        created_at=created_at,
        updated_at=created_at,
    )


# SC-D3F-1: Mon+Thu every 2 weeks × 8 total occurrences → exactly 8 dates
@pytest.mark.asyncio
async def test_sc_d3f_1_mon_thu_biweekly_occurrences_8_complete_cycles() -> None:
    """SC-D3F-1 (bug7 round-6): Mon+Thu every 2 weeks × 8 repeticiones → 8 CICLOS
    completos = 16 ocurrencias (8 Mon + 8 Thu).

    'N repeticiones' = N ciclos del patrón (cada repetición incluye TODOS los días),
    ratificado Chris 2026-06-15. Antes count=8 daba 8 totales (Mon,Thu,Mon,...) y
    dejaba el último ciclo a medias. Mutation guard: count = N × len(days).
    Se valida sobre project_block (materialización completa, sin cap de ventana).
    """
    from src.modules.vitalia.clinics.application.availability_projection_service import (
        AvailabilityProjectionService,
    )

    block = _multi_day_block(
        days_of_week=[0, 3],  # Monday + Thursday
        interval=2,
        occurrences=8,
        end_condition_kind="occurrences",
    )
    slots = AvailabilityProjectionService(slot_duration_minutes=30).project_block(block, reference_date=MONDAY)
    dates = sorted({s.slot_date for s in slots})
    assert len(dates) == 16, f"8 repeticiones × [Mon,Thu] = 16 ocurrencias, got {len(dates)}: {dates}"
    for d in dates:
        assert d.weekday() in (0, 3), f"Date {d} is not Mon or Thu (weekday={d.weekday()})"
    assert len([d for d in dates if d.weekday() == 0]) == 8, "8 lunes (8 ciclos)"
    assert len([d for d in dates if d.weekday() == 3]) == 8, "8 jueves (8 ciclos)"


# SC-D3F-2: All 7 weekdays × N repeticiones → N semanas completas
@pytest.mark.asyncio
async def test_sc_d3f_2_all_7_days_7_occurrences_complete_weeks() -> None:
    """SC-D3F-2 (bug7 round-6): 7 weekdays × 7 repeticiones → 7 SEMANAS completas
    = 49 ocurrencias (7 de cada día).

    'N repeticiones' = N ciclos del patrón (Chris 2026-06-15). Antes count=7 daba
    7 dias consecutivos (1 semana); ahora 7 repeticiones = 7 semanas completas.
    """
    from src.modules.vitalia.clinics.application.availability_projection_service import (
        AvailabilityProjectionService,
    )

    block = _multi_day_block(
        days_of_week=[0, 1, 2, 3, 4, 5, 6],  # all weekdays
        interval=1,
        occurrences=7,
        end_condition_kind="occurrences",
    )
    slots = AvailabilityProjectionService(slot_duration_minutes=30).project_block(block, reference_date=MONDAY)
    dates = sorted({s.slot_date for s in slots})
    assert len(dates) == 49, f"7 repeticiones × 7 días = 49 ocurrencias, got {len(dates)}: {dates}"
    for wd in range(7):
        assert len([d for d in dates if d.weekday() == wd]) == 7, f"7 ocurrencias del weekday {wd}"


# SC-D3F-4 ★ REGRESSION: legacy single-day blocks project identically pre/post migration
@pytest.mark.asyncio
async def test_sc_d3f_4_legacy_single_day_block_projects_identically_post_migration() -> None:
    """SC-D3F-4 ★REGRESSION: a block with days_of_week=[0] interval=1 (migrated legacy)
    produces IDENTICAL occurrence dates as the old day_of_week=0 freq='weekly' block.

    This is the RN-D3F-3 invariant: migration must not change projection results.
    RED until: (a) domain entity accepts days_of_week + interval,
               (b) projection reads days_of_week + interval (not freq/day_of_week).
    """
    # Simulate migrated legacy block (days_of_week=[0], interval=1 = weekly Monday)
    migrated = _multi_day_block(
        days_of_week=[0],  # Monday only — migrated from day_of_week=0
        interval=1,  # weekly — migrated from freq='weekly'
        occurrences=2,
        end_condition_kind="occurrences",
    )
    # Legacy block using old interface (day_of_week=0, freq='weekly')
    legacy = _recurrent_block(
        day_of_week=0,
        freq="weekly",
        occurrences=2,
    )

    svc_migrated, _ = _service_with_blocks([migrated])
    svc_legacy, _ = _service_with_blocks([legacy])

    migrated_result = await _occurrences(svc_migrated, migrated, MONDAY, MONDAY + timedelta(days=55))
    legacy_result = await _occurrences(svc_legacy, legacy, MONDAY, MONDAY + timedelta(days=55))

    migrated_dates = [o.occurrence_date for o in migrated_result]
    legacy_dates = [o.occurrence_date for o in legacy_result]

    assert migrated_dates == legacy_dates, (
        f"Migrated block must project IDENTICAL to legacy: migrated={migrated_dates} legacy={legacy_dates}"
    )
    assert migrated_dates == [date(2026, 6, 1), date(2026, 6, 8)], f"Expected [Jun 1, Jun 8], got {migrated_dates}"


# D3-F: format_recurrence_summary extensions
def test_format_recurrence_summary_multi_day_biweekly_with_occurrences() -> None:
    """Multi-day Mon+Thu every 2 weeks × 8 → full Google-style summary."""
    from src.modules.vitalia.clinics.application.recurrence_summary import (
        format_recurrence_summary,
    )

    block = _multi_day_block(
        days_of_week=[0, 3],  # Monday + Thursday
        interval=2,
        occurrences=8,
        end_condition_kind="occurrences",
    )
    summary = format_recurrence_summary(block)
    assert "2" in summary, f"Interval 2 must appear in summary: {summary!r}"
    assert "lunes" in summary.lower() and "jueves" in summary.lower(), (
        f"Day names 'lunes' and 'jueves' must appear in summary: {summary!r}"
    )
    assert "8" in summary, f"Count 8 must appear in summary: {summary!r}"


def test_format_recurrence_summary_multi_day_weekly_with_end_date() -> None:
    """Multi-day Mon+Wed every week with end_date → summary mentions days."""
    from src.modules.vitalia.clinics.application.recurrence_summary import (
        format_recurrence_summary,
    )

    block = _multi_day_block(
        days_of_week=[0, 2],  # Monday + Wednesday
        interval=1,
        end_date=date(2026, 8, 31),
        end_condition_kind="end_date",
    )
    summary = format_recurrence_summary(block)
    assert "lunes" in summary.lower(), f"'lunes' must appear in summary: {summary!r}"
    assert "miércoles" in summary.lower(), f"'miércoles' must appear in summary: {summary!r}"


def test_format_recurrence_summary_single_day_interval_3_custom() -> None:
    """Single day custom interval=3 → NOT 'Semanal'/'Quincenal' (new format)."""
    from src.modules.vitalia.clinics.application.recurrence_summary import (
        format_recurrence_summary,
    )

    block = _multi_day_block(
        days_of_week=[1],  # Tuesday only, every 3 weeks
        interval=3,
        occurrences=4,
        end_condition_kind="occurrences",
    )
    summary = format_recurrence_summary(block)
    assert "3" in summary, f"Interval 3 must appear in summary: {summary!r}"
    assert summary not in ("Semanal", "Quincenal"), (
        f"Custom interval=3 must NOT produce legacy shorthand, got {summary!r}"
    )


# D3-F: Domain validation — days_of_week invariants
def test_domain_days_of_week_empty_raises() -> None:
    """days_of_week=[] must raise ValueError (len >= 1 required)."""
    with pytest.raises(ValueError, match=r"(?i)(d[íi]a|semana|d[ae]y)"):
        _multi_day_block(
            days_of_week=[],  # empty — invalid
            interval=1,
            occurrences=2,
        )


def test_domain_interval_zero_raises() -> None:
    """interval=0 must raise ValueError (interval >= 1 required)."""
    with pytest.raises(ValueError, match=r"(?i)(intervalo|interval)"):
        _multi_day_block(
            days_of_week=[0],
            interval=0,  # invalid
            occurrences=2,
        )


def test_domain_days_of_week_out_of_range_raises() -> None:
    """days_of_week containing 7 must raise ValueError (0–6 only)."""
    with pytest.raises(ValueError):
        _multi_day_block(
            days_of_week=[0, 7],  # 7 is out of range (0=Mon..6=Sun)
            interval=1,
            occurrences=2,
        )
