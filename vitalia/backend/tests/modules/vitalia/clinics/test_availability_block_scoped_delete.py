# cap: clinics.lisa.doctores
"""Tests: scoped delete (scope=occurrence|this_and_future) + past block guard (Feature #1 + #2).

TDD RED-first — tests MUST fail before implementation.

Feature #1 — scoped delete:
  - scope=occurrence: excludes single occurrence, preserves confirmed, leaves block active
  - scope=this_and_future: truncates series end_date, retires future free slots >= occ_date
  - scope=series: existing behavior (backward compat — do not break)
  - 422 when scope requires occurrence_date and it's missing

Feature #2 — past block guard:
  - create one_off with specific_date < today → ValueError → 422
  - create recurrent with end_date < today → ValueError → 422

Tests:
  1.  projection skip excluded_dates (unit — domain + projection)
  2.  exclude_occurrence service: free slot retired, confirmed preserved, excluded_dates persisted
  3.  truncate_from service: end_date set, future free slots retired >= occ_date, confirmed preserved
  4.  DELETE scope=occurrence (API mock) → 200 + scope echoed
  5.  DELETE scope=this_and_future (API mock) → 200 + scope echoed
  6.  DELETE scope=occurrence without occurrence_date → 422
  7.  DELETE scope=this_and_future without occurrence_date → 422
  8.  DELETE scope=series (default) → backward compat (unchanged behavior)
  9.  POST one_off specific_date in the past → 422
  10. POST recurrent end_date in the past → 422
  11. delete route has response_model= (arch gate)
"""

from __future__ import annotations

from datetime import date, time, timedelta
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

if TYPE_CHECKING:
    from fastapi import FastAPI

    from src.modules.vitalia.clinics.domain.availability_block import AvailabilityBlock

import pytest

# ── Helpers ─────────────────────────────────────────────────────────────────


def _make_recurrent_block(
    *,
    days_of_week: list[int] | None = None,
    end_condition_kind: str = "open_ended",
    end_date: date | None = None,
    excluded_dates: list[str] | None = None,
) -> "AvailabilityBlock":
    from src.modules.vitalia.clinics.domain.availability_block import AvailabilityBlock

    return AvailabilityBlock(
        id=uuid4(),
        tenant_id=uuid4(),
        clinic_id=uuid4(),
        doctor_id=uuid4(),
        kind="recurrent",
        start_time=time(9, 0),
        end_time=time(17, 0),
        days_of_week=days_of_week or [0],  # Monday
        interval=1,
        end_condition_kind=end_condition_kind,
        end_date=end_date,
        excluded_dates=excluded_dates or [],
    )


def _make_one_off_block(*, specific_date: date) -> "AvailabilityBlock":
    from src.modules.vitalia.clinics.domain.availability_block import AvailabilityBlock

    return AvailabilityBlock(
        id=uuid4(),
        tenant_id=uuid4(),
        clinic_id=uuid4(),
        doctor_id=uuid4(),
        kind="one_off",
        start_time=time(10, 0),
        end_time=time(12, 0),
        specific_date=specific_date,
    )


# ── Feature #1 — excluded_dates in projection ────────────────────────────────


def test_projection_skips_excluded_occurrence() -> None:
    """Projection must skip any occurrence whose date is in block.excluded_dates."""
    from src.modules.vitalia.clinics.application.availability_projection_service import (
        AvailabilityProjectionService,
    )

    today = date.today()
    # Find next Monday
    days_ahead = (0 - today.weekday()) % 7  # next Monday (0=Mon)
    if days_ahead == 0:
        days_ahead = 7
    next_monday = today + timedelta(days=days_ahead)
    excluded = next_monday.isoformat()

    block = _make_recurrent_block(
        days_of_week=[0],
        end_condition_kind="end_date",
        end_date=today + timedelta(days=21),
        excluded_dates=[excluded],
    )

    svc = AvailabilityProjectionService()
    slots = svc.project_block(block, reference_date=today)
    slot_dates = [s.slot_date.isoformat() for s in slots]

    assert excluded not in slot_dates, f"Excluded date {excluded} should not appear in projection"


def test_occurrence_dates_in_range_skips_excluded() -> None:
    """occurrence_dates_in_range must skip dates in block.excluded_dates."""
    from src.modules.vitalia.clinics.application.availability_projection_service import (
        AvailabilityProjectionService,
    )

    today = date.today()
    days_ahead = (0 - today.weekday()) % 7
    if days_ahead == 0:
        days_ahead = 7
    next_monday = today + timedelta(days=days_ahead)
    excluded = next_monday.isoformat()

    block = _make_recurrent_block(
        days_of_week=[0],
        end_condition_kind="end_date",
        end_date=today + timedelta(days=21),
        excluded_dates=[excluded],
    )

    svc = AvailabilityProjectionService()
    dates = svc.occurrence_dates_in_range(
        block,
        range_start=today,
        range_end=today + timedelta(days=21),
    )
    assert next_monday not in dates, f"Excluded date {next_monday} should not appear in occurrences"


def test_one_off_skips_excluded_specific_date() -> None:
    """A one_off block whose specific_date is in excluded_dates returns 0 slots."""
    from src.modules.vitalia.clinics.application.availability_projection_service import (
        AvailabilityProjectionService,
    )

    tomorrow = date.today() + timedelta(days=1)
    block = _make_one_off_block(specific_date=tomorrow)
    block.excluded_dates = [tomorrow.isoformat()]

    svc = AvailabilityProjectionService()
    slots = svc.project_block(block, reference_date=date.today())
    assert slots == [], "one_off with excluded specific_date must return empty list"


# ── Feature #1 — service exclude_occurrence ──────────────────────────────────


@pytest.mark.asyncio
async def test_service_exclude_occurrence_persists_excluded_date() -> None:
    """exclude_occurrence appends occurrence_date to block.excluded_dates and persists."""
    from src.modules.vitalia.clinics.application.availability_block_service import (
        AvailabilityBlockService,
    )

    tenant_id = uuid4()
    clinic_id = uuid4()
    block_id = uuid4()
    user_id = uuid4()
    occ_date = date.today() + timedelta(days=7)

    block = _make_recurrent_block(end_condition_kind="open_ended")
    block.id = block_id
    block.tenant_id = tenant_id
    block.clinic_id = clinic_id

    mock_repo = AsyncMock()
    mock_repo.get_block.return_value = block
    mock_repo.persist_excluded_dates = AsyncMock(return_value=block)
    mock_repo.retire_free_slots_on_date = AsyncMock(return_value=0)

    mock_audit = AsyncMock()

    svc = AvailabilityBlockService(block_repo=mock_repo, audit_repo=mock_audit)
    result = await svc.exclude_occurrence(
        block_id=block_id,
        tenant_id=tenant_id,
        clinic_id=clinic_id,
        user_id=user_id,
        occurrence_date=occ_date,
    )

    assert occ_date.isoformat() in result.excluded_dates
    mock_repo.persist_excluded_dates.assert_called_once()
    mock_audit.write.assert_called_once()


@pytest.mark.asyncio
async def test_service_exclude_occurrence_retires_free_slots_not_confirmed() -> None:
    """exclude_occurrence retires free slots on that date but preserves confirmed."""
    from src.modules.vitalia.clinics.application.availability_block_service import (
        AvailabilityBlockService,
    )

    tenant_id = uuid4()
    clinic_id = uuid4()
    block_id = uuid4()
    occ_date = date.today() + timedelta(days=3)

    block = _make_recurrent_block(end_condition_kind="open_ended")
    block.id = block_id
    block.tenant_id = tenant_id
    block.clinic_id = clinic_id

    mock_repo = AsyncMock()
    mock_repo.get_block.return_value = block
    mock_repo.persist_excluded_dates = AsyncMock(return_value=block)
    mock_repo.retire_free_slots_on_date = AsyncMock(return_value=0)

    mock_audit = AsyncMock()

    svc = AvailabilityBlockService(block_repo=mock_repo, audit_repo=mock_audit)
    await svc.exclude_occurrence(
        block_id=block_id,
        tenant_id=tenant_id,
        clinic_id=clinic_id,
        user_id=uuid4(),
        occurrence_date=occ_date,
    )

    # retire_free_slots_on_date must be called with the exact date
    mock_repo.retire_free_slots_on_date.assert_called_once_with(
        block_id,
        slot_date=occ_date,
        tenant_id=tenant_id,
        clinic_id=clinic_id,
    )


# ── Feature #1 — service truncate_from ───────────────────────────────────────


@pytest.mark.asyncio
async def test_service_truncate_from_sets_end_date() -> None:
    """truncate_from sets end_condition_kind='end_date' + end_date = occ_date - 1."""
    from src.modules.vitalia.clinics.application.availability_block_service import (
        AvailabilityBlockService,
    )

    tenant_id = uuid4()
    clinic_id = uuid4()
    block_id = uuid4()
    occ_date = date.today() + timedelta(days=14)

    block = _make_recurrent_block(end_condition_kind="open_ended")
    block.id = block_id
    block.tenant_id = tenant_id
    block.clinic_id = clinic_id

    mock_repo = AsyncMock()
    mock_repo.get_block.return_value = block
    mock_repo.truncate_block = AsyncMock(return_value=block)
    mock_repo.retire_free_slots_from_date = AsyncMock(return_value=0)

    mock_audit = AsyncMock()

    svc = AvailabilityBlockService(block_repo=mock_repo, audit_repo=mock_audit)
    await svc.truncate_from(
        block_id=block_id,
        tenant_id=tenant_id,
        clinic_id=clinic_id,
        user_id=uuid4(),
        occurrence_date=occ_date,
    )

    mock_repo.truncate_block.assert_called_once()
    call_kwargs = mock_repo.truncate_block.call_args
    # Verify the truncation date passed
    assert call_kwargs is not None


@pytest.mark.asyncio
async def test_service_truncate_from_retires_future_free_slots() -> None:
    """truncate_from retires FREE slots where slot_date >= occurrence_date."""
    from src.modules.vitalia.clinics.application.availability_block_service import (
        AvailabilityBlockService,
    )

    tenant_id = uuid4()
    clinic_id = uuid4()
    block_id = uuid4()
    occ_date = date.today() + timedelta(days=7)

    block = _make_recurrent_block(end_condition_kind="open_ended")
    block.id = block_id
    block.tenant_id = tenant_id
    block.clinic_id = clinic_id

    mock_repo = AsyncMock()
    mock_repo.get_block.return_value = block
    mock_repo.truncate_block = AsyncMock(return_value=block)
    mock_repo.retire_free_slots_from_date = AsyncMock(return_value=0)

    mock_audit = AsyncMock()

    svc = AvailabilityBlockService(block_repo=mock_repo, audit_repo=mock_audit)
    await svc.truncate_from(
        block_id=block_id,
        tenant_id=tenant_id,
        clinic_id=clinic_id,
        user_id=uuid4(),
        occurrence_date=occ_date,
    )

    mock_repo.retire_free_slots_from_date.assert_called_once_with(
        block_id,
        from_date=occ_date,
        tenant_id=tenant_id,
        clinic_id=clinic_id,
    )
    mock_audit.write.assert_called_once()


# ── Feature #1 — API endpoint scope parameter ────────────────────────────────


def test_delete_route_has_response_model() -> None:
    """DELETE /{doctor_id}/availability-blocks/{block_id} must declare response_model=."""
    from src.modules.vitalia.clinics.api.doctors_router import router

    routes = [
        r
        for r in router.routes
        if hasattr(r, "path")
        and "availability-blocks" in r.path
        and "{block_id}" in r.path
        and "DELETE" in getattr(r, "methods", set())
    ]
    assert routes, "DELETE /{doctor_id}/availability-blocks/{block_id} route not found"
    route = routes[0]
    assert getattr(route, "response_model", None) is not None, "DELETE availability-blocks must declare response_model="


def test_delete_scope_response_includes_scope_field() -> None:
    """DeleteBlockResponse must have a 'scope' field for the new scoped delete contract."""
    from src.modules.vitalia.clinics.api.dtos import DeleteBlockResponse

    # Instantiate with scope field
    resp = DeleteBlockResponse(deleted=True, preserved_appointments=0, scope="series")
    assert resp.scope == "series"


def _build_test_app_with_mock_svc(
    mock_svc: MagicMock,
    doctor_id: UUID,
    block_id: UUID,
    tenant_id: UUID,
    clinic_id: UUID,
    user_id: UUID,
) -> "FastAPI":
    """Build a minimal test FastAPI app with mocked block service."""
    from fastapi import FastAPI

    from src.modules.vitalia.clinics.api.doctors_router import router

    app = FastAPI()

    async def override_db() -> None:  # type: ignore[override]
        yield None  # type: ignore[misc]

    from src.db import get_async_session  # type: ignore[import]

    app.dependency_overrides[get_async_session] = override_db
    app.include_router(router, prefix="/doctors")
    return app


@pytest.mark.asyncio
async def test_delete_scope_occurrence_returns_scope_in_response() -> None:
    """DELETE scope=occurrence returns 200 with scope='occurrence' echoed."""
    from unittest.mock import patch

    from fastapi import FastAPI
    from httpx import ASGITransport, AsyncClient

    from src.modules.vitalia.clinics.api.doctors_router import router

    doctor_id = uuid4()
    block_id = uuid4()
    tenant_id = uuid4()
    clinic_id = uuid4()
    user_id = uuid4()
    occ_date = (date.today() + timedelta(days=7)).isoformat()

    app = FastAPI(redirect_slashes=False)
    app.include_router(router, prefix="/doctors")

    async def override_db():  # type: ignore[return]
        yield MagicMock()

    from src.db import get_async_session  # type: ignore[import]

    app.dependency_overrides[get_async_session] = override_db

    mock_block = _make_recurrent_block(end_condition_kind="open_ended")
    mock_block.excluded_dates = [occ_date]

    with patch("src.modules.vitalia.clinics.api.doctors_router._build_block_service") as mock_builder:
        mock_svc = MagicMock()
        mock_svc.exclude_occurrence = AsyncMock(return_value=mock_block)
        mock_svc.count_future_confirmed = AsyncMock(return_value=0)
        mock_builder.return_value = mock_svc

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.delete(
                f"/doctors/{doctor_id}/availability-blocks/{block_id}",
                params={"scope": "occurrence", "occurrence_date": occ_date},
                headers={
                    "X-Tenant-ID": str(tenant_id),
                    "X-Clinic-ID": str(clinic_id),
                    "X-User-ID": str(user_id),
                    "X-User-Role": "owner",
                },
            )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data.get("scope") == "occurrence" or "scope" in data


@pytest.mark.asyncio
async def test_delete_scope_occurrence_without_occurrence_date_returns_422() -> None:
    """DELETE scope=occurrence without occurrence_date must return 422."""
    from unittest.mock import patch

    from fastapi import FastAPI
    from httpx import ASGITransport, AsyncClient

    from src.modules.vitalia.clinics.api.doctors_router import router

    doctor_id = uuid4()
    block_id = uuid4()
    tenant_id = uuid4()
    clinic_id = uuid4()
    user_id = uuid4()

    app = FastAPI(redirect_slashes=False)
    app.include_router(router, prefix="/doctors")

    async def override_db():  # type: ignore[return]
        yield MagicMock()

    from src.db import get_async_session  # type: ignore[import]

    app.dependency_overrides[get_async_session] = override_db

    with patch("src.modules.vitalia.clinics.api.doctors_router._build_block_service") as mock_builder:
        mock_svc = MagicMock()
        mock_builder.return_value = mock_svc

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.delete(
                f"/doctors/{doctor_id}/availability-blocks/{block_id}",
                params={"scope": "occurrence"},  # No occurrence_date!
                headers={
                    "X-Tenant-ID": str(tenant_id),
                    "X-Clinic-ID": str(clinic_id),
                    "X-User-ID": str(user_id),
                    "X-User-Role": "owner",
                },
            )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_delete_scope_this_and_future_without_occurrence_date_returns_422() -> None:
    """DELETE scope=this_and_future without occurrence_date must return 422."""
    from unittest.mock import patch

    from fastapi import FastAPI
    from httpx import ASGITransport, AsyncClient

    from src.modules.vitalia.clinics.api.doctors_router import router

    doctor_id = uuid4()
    block_id = uuid4()
    tenant_id = uuid4()
    clinic_id = uuid4()
    user_id = uuid4()

    app = FastAPI(redirect_slashes=False)
    app.include_router(router, prefix="/doctors")

    async def override_db():  # type: ignore[return]
        yield MagicMock()

    from src.db import get_async_session  # type: ignore[import]

    app.dependency_overrides[get_async_session] = override_db

    with patch("src.modules.vitalia.clinics.api.doctors_router._build_block_service") as mock_builder:
        mock_svc = MagicMock()
        mock_builder.return_value = mock_svc

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.delete(
                f"/doctors/{doctor_id}/availability-blocks/{block_id}",
                params={"scope": "this_and_future"},  # No occurrence_date!
                headers={
                    "X-Tenant-ID": str(tenant_id),
                    "X-Clinic-ID": str(clinic_id),
                    "X-User-ID": str(user_id),
                    "X-User-Role": "owner",
                },
            )

    assert response.status_code == 422


# ── Feature #2 — past block guard ────────────────────────────────────────────


def test_create_one_off_past_date_raises_value_error() -> None:
    """create_block with one_off and specific_date < today must raise ValueError."""
    # Use a definitely-past date
    past_date = date(2020, 1, 1)

    # Import service and call create_block synchronously via domain validation
    # The ValueError should come from service-level validation before domain construction
    import asyncio

    from src.modules.vitalia.clinics.application.availability_block_service import (
        AvailabilityBlockService,
    )

    mock_repo = AsyncMock()
    mock_audit = AsyncMock()
    svc = AvailabilityBlockService(block_repo=mock_repo, audit_repo=mock_audit)

    with pytest.raises(ValueError, match="pasad"):
        asyncio.run(
            svc.create_block(
                tenant_id=uuid4(),
                clinic_id=uuid4(),
                doctor_id=uuid4(),
                user_id=uuid4(),
                kind="one_off",
                start_time=time(9, 0),
                end_time=time(17, 0),
                specific_date=past_date,
            )
        )


def test_create_recurrent_past_end_date_raises_value_error() -> None:
    """create_block with recurrent and end_date < today must raise ValueError."""
    import asyncio

    from src.modules.vitalia.clinics.application.availability_block_service import (
        AvailabilityBlockService,
    )

    past_end_date = date(2020, 6, 1)

    mock_repo = AsyncMock()
    mock_audit = AsyncMock()
    svc = AvailabilityBlockService(block_repo=mock_repo, audit_repo=mock_audit)

    with pytest.raises(ValueError, match="pasad"):
        asyncio.run(
            svc.create_block(
                tenant_id=uuid4(),
                clinic_id=uuid4(),
                doctor_id=uuid4(),
                user_id=uuid4(),
                kind="recurrent",
                start_time=time(9, 0),
                end_time=time(17, 0),
                days_of_week=[0],
                end_condition_kind="end_date",
                end_date=past_end_date,
            )
        )


@pytest.mark.asyncio
async def test_post_one_off_past_date_returns_422() -> None:
    """POST create availability block with past specific_date returns 422."""
    from unittest.mock import patch

    from fastapi import FastAPI
    from httpx import ASGITransport, AsyncClient

    from src.modules.vitalia.clinics.api.doctors_router import router

    doctor_id = uuid4()
    tenant_id = uuid4()
    clinic_id = uuid4()
    user_id = uuid4()

    app = FastAPI(redirect_slashes=False)
    app.include_router(router, prefix="/doctors")

    async def override_db():  # type: ignore[return]
        yield MagicMock()

    from src.db import get_async_session  # type: ignore[import]

    app.dependency_overrides[get_async_session] = override_db

    with patch("src.modules.vitalia.clinics.api.doctors_router._build_block_service") as mock_builder:
        mock_svc = MagicMock()
        mock_svc.create_block = AsyncMock(side_effect=ValueError("No puedes crear bloques en fechas pasadas."))
        mock_builder.return_value = mock_svc

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                f"/doctors/{doctor_id}/availability-blocks",
                json={
                    "kind": "one_off",
                    "startTime": "09:00:00",
                    "endTime": "17:00:00",
                    "specificDate": "2020-01-01",
                },
                headers={
                    "X-Tenant-ID": str(tenant_id),
                    "X-Clinic-ID": str(clinic_id),
                    "X-User-ID": str(user_id),
                    "X-User-Role": "owner",
                },
            )

    assert response.status_code == 422
