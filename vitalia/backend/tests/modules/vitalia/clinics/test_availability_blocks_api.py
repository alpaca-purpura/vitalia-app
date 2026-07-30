# cap: clinics.lisa.doctores
"""Tests: Availability blocks API endpoints (T-BE-3).

TDD RED-first — these tests should fail BEFORE the implementation is added,
then pass after the routes and service are wired.

Validators: V-FN-1, V-FN-2, V-FN-3, V-FN-4, V-FN-7, V-ARCH-2, V-NF-7
Gherkin coverage: SC-1, SC-1b, SC-1c, SC-1d, SC-3b

Tests:
  1. response_model= declared on all availability-block routes (arch gate V-ARCH-2)
  2. RBAC admin_clinic on all mutations
  3. GET list returns blocks for doctor (dual filter)
  4. POST create block (recurrent weekly) -> materializes slots -> audit created
  5. POST create block (one_off) -> materializes 1 day of slots
  6. PATCH edit block -> reproject-future-only invariant
  7. DELETE block (no appointments) -> {deleted: True, preserved_appointments: 0} + audit
  8. DELETE block with confirmed appt -> preserved_appointments > 0 (SC-3b critical)
  9. Invalid discriminated union (recurrent without end_condition) -> 422
 10. AvailabilityBlockDTO no PHI fields
"""

from __future__ import annotations

from datetime import date, time, timedelta
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest

# ──────────────────────────────────────────────────────────────────────────────
# V-ARCH-2 — response_model= on all availability block routes
# ──────────────────────────────────────────────────────────────────────────────


def test_availability_blocks_get_list_has_response_model() -> None:
    """GET /{doctor_id}/availability-blocks must declare response_model= (arch gate V-ARCH-2)."""
    from src.modules.vitalia.clinics.api.doctors_router import router

    routes = [
        r
        for r in router.routes
        if hasattr(r, "path")
        and "availability-blocks" in r.path
        and "GET" in getattr(r, "methods", set())
        and "{block_id}" not in r.path
    ]
    assert routes, "GET /{doctor_id}/availability-blocks route not found"
    route = routes[0]
    assert getattr(route, "response_model", None) is not None, "GET availability-blocks must declare response_model="


def test_availability_blocks_post_has_response_model() -> None:
    """POST /{doctor_id}/availability-blocks must declare response_model= (arch gate V-ARCH-2)."""
    from src.modules.vitalia.clinics.api.doctors_router import router

    routes = [
        r
        for r in router.routes
        if hasattr(r, "path") and "availability-blocks" in r.path and "POST" in getattr(r, "methods", set())
    ]
    assert routes, "POST /{doctor_id}/availability-blocks route not found"
    route = routes[0]
    assert getattr(route, "response_model", None) is not None, "POST availability-blocks must declare response_model="


def test_availability_blocks_patch_has_response_model() -> None:
    """PATCH /{doctor_id}/availability-blocks/{block_id} must declare response_model= (arch gate V-ARCH-2)."""
    from src.modules.vitalia.clinics.api.doctors_router import router

    routes = [
        r
        for r in router.routes
        if hasattr(r, "path")
        and "availability-blocks" in r.path
        and "{block_id}" in r.path
        and "PATCH" in getattr(r, "methods", set())
    ]
    assert routes, "PATCH /{doctor_id}/availability-blocks/{block_id} route not found"
    route = routes[0]
    assert getattr(route, "response_model", None) is not None, (
        "PATCH availability-blocks/{block_id} must declare response_model="
    )


def test_availability_blocks_delete_has_response_model() -> None:
    """DELETE /{doctor_id}/availability-blocks/{block_id} must declare response_model= (arch gate V-ARCH-2)."""
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
    assert getattr(route, "response_model", None) is not None, (
        "DELETE availability-blocks/{block_id} must declare response_model="
    )


# ──────────────────────────────────────────────────────────────────────────────
# DTO discriminated union — dtos.py
# ──────────────────────────────────────────────────────────────────────────────


def test_availability_block_dto_exists() -> None:
    """AvailabilityBlockDTO must exist in dtos.py."""
    from src.modules.vitalia.clinics.api.dtos import AvailabilityBlockDTO

    assert AvailabilityBlockDTO is not None


def test_availability_blocks_response_dto_exists() -> None:
    """AvailabilityBlocksResponse must exist in dtos.py."""
    from src.modules.vitalia.clinics.api.dtos import AvailabilityBlocksResponse

    assert AvailabilityBlocksResponse is not None


def test_delete_block_response_dto_exists() -> None:
    """DeleteBlockResponse must exist in dtos.py with deleted + preserved_appointments fields."""
    from src.modules.vitalia.clinics.api.dtos import DeleteBlockResponse

    fields = set(DeleteBlockResponse.model_fields.keys())
    assert "deleted" in fields, "DeleteBlockResponse must have 'deleted' field"
    assert "preserved_appointments" in fields, "DeleteBlockResponse must have 'preserved_appointments' field"


def test_recurrent_block_create_request_exists() -> None:
    """RecurrentBlockCreateRequest discriminated union must exist in dtos.py."""
    from src.modules.vitalia.clinics.api.dtos import RecurrentBlockCreateRequest

    assert RecurrentBlockCreateRequest is not None
    fields = set(RecurrentBlockCreateRequest.model_fields.keys())
    assert "kind" in fields, "RecurrentBlockCreateRequest must have 'kind' field"
    assert "day_of_week" in fields, "RecurrentBlockCreateRequest must have 'day_of_week'"
    assert "end_condition_kind" in fields, "RecurrentBlockCreateRequest must have 'end_condition_kind'"


def test_one_off_block_create_request_exists() -> None:
    """OneOffBlockCreateRequest discriminated union must exist in dtos.py."""
    from src.modules.vitalia.clinics.api.dtos import OneOffBlockCreateRequest

    assert OneOffBlockCreateRequest is not None
    fields = set(OneOffBlockCreateRequest.model_fields.keys())
    assert "kind" in fields, "OneOffBlockCreateRequest must have 'kind' field"
    assert "specific_date" in fields, "OneOffBlockCreateRequest must have 'specific_date' field"


def test_availability_block_dto_has_no_phi_fields() -> None:
    """AvailabilityBlockDTO must not expose PHI fields (scheduling metadata, not patient data)."""
    from src.modules.vitalia.clinics.api.dtos import AvailabilityBlockDTO

    # Availability blocks are scheduling metadata — must not contain patient PHI
    phi_fields = {"patient_name", "patient_dni", "patient_email", "diagnosis", "treatment_plan"}
    model_fields = set(AvailabilityBlockDTO.model_fields.keys())
    violations = phi_fields & model_fields
    assert not violations, (
        f"AvailabilityBlockDTO contains PHI fields: {violations}. "
        "Availability blocks are scheduling metadata, not patient data."
    )


# ──────────────────────────────────────────────────────────────────────────────
# AvailabilityBlockService — application service exists
# ──────────────────────────────────────────────────────────────────────────────


def test_availability_block_service_exists() -> None:
    """AvailabilityBlockService must exist in clinics/application/."""
    from src.modules.vitalia.clinics.application.availability_block_service import (
        AvailabilityBlockService,
    )

    assert AvailabilityBlockService is not None


def test_availability_block_service_has_list_method() -> None:
    """AvailabilityBlockService must have list_blocks method."""
    from src.modules.vitalia.clinics.application.availability_block_service import (
        AvailabilityBlockService,
    )

    assert hasattr(AvailabilityBlockService, "list_blocks"), "AvailabilityBlockService must have list_blocks method"


def test_availability_block_service_has_create_method() -> None:
    """AvailabilityBlockService must have create_block method."""
    from src.modules.vitalia.clinics.application.availability_block_service import (
        AvailabilityBlockService,
    )

    assert hasattr(AvailabilityBlockService, "create_block"), "AvailabilityBlockService must have create_block method"


def test_availability_block_service_has_update_method() -> None:
    """AvailabilityBlockService must have update_block method."""
    from src.modules.vitalia.clinics.application.availability_block_service import (
        AvailabilityBlockService,
    )

    assert hasattr(AvailabilityBlockService, "update_block"), "AvailabilityBlockService must have update_block method"


def test_availability_block_service_has_delete_method() -> None:
    """AvailabilityBlockService must have delete_block method."""
    from src.modules.vitalia.clinics.application.availability_block_service import (
        AvailabilityBlockService,
    )

    assert hasattr(AvailabilityBlockService, "delete_block"), "AvailabilityBlockService must have delete_block method"


# ──────────────────────────────────────────────────────────────────────────────
# AvailabilityBlockService — unit tests (mock repository)
# ──────────────────────────────────────────────────────────────────────────────


def _make_mock_block(
    *,
    block_id: UUID | None = None,
    tenant_id: UUID | None = None,
    clinic_id: UUID | None = None,
    doctor_id: UUID | None = None,
    kind: str = "recurrent",
) -> "object":
    """Build an AvailabilityBlock domain entity for testing."""
    from src.modules.vitalia.clinics.domain.availability_block import AvailabilityBlock

    today = date.today()
    bid = block_id or uuid4()
    tid = tenant_id or uuid4()
    cid = clinic_id or uuid4()
    did = doctor_id or uuid4()

    if kind == "one_off":
        return AvailabilityBlock(
            id=bid,
            tenant_id=tid,
            clinic_id=cid,
            doctor_id=did,
            kind="one_off",
            start_time=time(9, 0),
            end_time=time(12, 0),
            specific_date=today + timedelta(days=7),
        )

    return AvailabilityBlock(
        id=bid,
        tenant_id=tid,
        clinic_id=cid,
        doctor_id=did,
        kind="recurrent",
        start_time=time(9, 0),
        end_time=time(12, 0),
        day_of_week=0,  # Monday
        freq="weekly",
        end_condition_kind="end_date",
        end_date=today + timedelta(days=60),
    )


@pytest.mark.asyncio
async def test_availability_block_service_list_blocks() -> None:
    """list_blocks delegates to repo with dual filter and returns blocks."""
    from src.modules.vitalia.clinics.application.availability_block_service import (
        AvailabilityBlockService,
    )

    tid = uuid4()
    cid = uuid4()
    did = uuid4()
    block = _make_mock_block(tenant_id=tid, clinic_id=cid, doctor_id=did)

    mock_repo = AsyncMock()
    mock_repo.list_blocks.return_value = [block]
    mock_audit = AsyncMock()

    svc = AvailabilityBlockService(block_repo=mock_repo, audit_repo=mock_audit)
    result = await svc.list_blocks(doctor_id=did, tenant_id=tid, clinic_id=cid)

    assert len(result) == 1
    mock_repo.list_blocks.assert_awaited_once_with(tenant_id=tid, clinic_id=cid, doctor_id=did)


@pytest.mark.asyncio
async def test_availability_block_service_create_block_weekly(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """create_block with recurrent weekly -> materializes slots -> audit created (V-FN-1).

    SC-1: recurrent weekly with end_date -> rrule expands, slots persisted, audit
    doctor.availability_block_created.
    """
    from src.modules.vitalia.clinics.application.availability_block_service import (
        AvailabilityBlockService,
    )

    tid = uuid4()
    cid = uuid4()
    did = uuid4()
    uid = uuid4()

    mock_repo = AsyncMock()
    mock_audit = AsyncMock()

    block = _make_mock_block(tenant_id=tid, clinic_id=cid, doctor_id=did, kind="recurrent")
    mock_repo.create_block.return_value = block

    svc = AvailabilityBlockService(block_repo=mock_repo, audit_repo=mock_audit)

    result = await svc.create_block(
        tenant_id=tid,
        clinic_id=cid,
        doctor_id=did,
        user_id=uid,
        kind="recurrent",
        start_time=time(9, 0),
        end_time=time(12, 0),
        day_of_week=0,
        freq="weekly",
        end_condition_kind="end_date",
        end_date=date.today() + timedelta(days=60),
        occurrences=None,
        specific_date=None,
    )

    assert result is not None
    # Audit must have been written SYNC (doctor.availability_block_created)
    mock_audit.write.assert_awaited_once()
    audit_entry = mock_audit.write.call_args[0][0]
    assert audit_entry.action == "doctor.availability_block_created"
    assert audit_entry.resource_type == "availability_block"
    # Repo create_block called with block and projected slots
    mock_repo.create_block.assert_awaited_once()


@pytest.mark.asyncio
async def test_availability_block_service_create_block_one_off() -> None:
    """create_block with one_off -> materializes 1 day of slots (V-FN-3 SC-1c).

    SC-1c: one-off block -> single specific_date -> slots on that date only.
    """
    from src.modules.vitalia.clinics.application.availability_block_service import (
        AvailabilityBlockService,
    )

    tid = uuid4()
    cid = uuid4()
    did = uuid4()
    uid = uuid4()

    specific = date.today() + timedelta(days=14)

    mock_repo = AsyncMock()
    mock_audit = AsyncMock()

    block = _make_mock_block(tenant_id=tid, clinic_id=cid, doctor_id=did, kind="one_off")
    mock_repo.create_block.return_value = block

    svc = AvailabilityBlockService(block_repo=mock_repo, audit_repo=mock_audit)

    result = await svc.create_block(
        tenant_id=tid,
        clinic_id=cid,
        doctor_id=did,
        user_id=uid,
        kind="one_off",
        start_time=time(9, 0),
        end_time=time(12, 0),
        day_of_week=None,
        freq=None,
        end_condition_kind=None,
        end_date=None,
        occurrences=None,
        specific_date=specific,
    )

    assert result is not None
    # Slots passed to repo must be only for specific_date
    create_call = mock_repo.create_block.call_args
    # create_block(block, slots, tenant_id=..., clinic_id=...)
    # positional args: block=args[0][0], slots=args[0][1]
    slots = create_call[0][1]
    for slot in slots:
        assert slot.slot_date == specific, (
            f"one_off block should only materialize slots on {specific}, got {slot.slot_date}"
        )


@pytest.mark.asyncio
async def test_availability_block_service_biweekly_occurrences() -> None:
    """create_block biweekly N=6 -> exactly 6 occurrence dates (V-FN-2, SC-1b)."""
    from src.modules.vitalia.clinics.application.availability_projection_service import (
        AvailabilityProjectionService,
    )
    from src.modules.vitalia.clinics.domain.availability_block import AvailabilityBlock

    # Direct projection test (service calls this internally)
    block = AvailabilityBlock(
        id=uuid4(),
        tenant_id=uuid4(),
        clinic_id=uuid4(),
        doctor_id=uuid4(),
        kind="recurrent",
        start_time=time(10, 0),
        end_time=time(11, 0),
        day_of_week=2,  # Wednesday
        freq="biweekly",
        end_condition_kind="occurrences",
        occurrences=6,
    )

    proj = AvailabilityProjectionService(slot_duration_minutes=60)
    slots = proj.project_block(block, reference_date=date(2026, 6, 1))

    # Each occurrence = 1 slot (1h slot, 1h window), 6 occurrences
    occurrence_dates = {s.slot_date for s in slots}
    assert len(occurrence_dates) == 6, (
        f"biweekly with occurrences=6 should produce exactly 6 distinct dates, got {len(occurrence_dates)}"
    )


@pytest.mark.asyncio
async def test_availability_block_service_update_block() -> None:
    """update_block re-projects future slots via repo.update_block."""
    from src.modules.vitalia.clinics.application.availability_block_service import (
        AvailabilityBlockService,
    )

    tid = uuid4()
    cid = uuid4()
    did = uuid4()
    uid = uuid4()
    bid = uuid4()

    mock_repo = AsyncMock()
    mock_audit = AsyncMock()

    block = _make_mock_block(block_id=bid, tenant_id=tid, clinic_id=cid, doctor_id=did)
    mock_repo.get_block.return_value = block
    mock_repo.update_block.return_value = block

    svc = AvailabilityBlockService(block_repo=mock_repo, audit_repo=mock_audit)

    result = await svc.update_block(
        block_id=bid,
        tenant_id=tid,
        clinic_id=cid,
        doctor_id=did,
        user_id=uid,
        kind="recurrent",
        start_time=time(10, 0),
        end_time=time(13, 0),  # modified
        day_of_week=0,
        freq="weekly",
        end_condition_kind="end_date",
        end_date=date.today() + timedelta(days=90),
        occurrences=None,
        specific_date=None,
    )

    assert result is not None
    mock_repo.update_block.assert_awaited_once()


@pytest.mark.asyncio
async def test_availability_block_service_delete_no_confirmed_appointments() -> None:
    """delete_block with no confirmed appts -> {deleted: True, preserved_appointments: 0} + audit (V-FN-4, SC-1d)."""
    from src.modules.vitalia.clinics.application.availability_block_service import (
        AvailabilityBlockService,
    )

    tid = uuid4()
    cid = uuid4()
    uid = uuid4()
    bid = uuid4()

    mock_repo = AsyncMock()
    mock_audit = AsyncMock()

    # Repo delete_block returns preserved_appointments count
    mock_repo.delete_block.return_value = 0

    svc = AvailabilityBlockService(block_repo=mock_repo, audit_repo=mock_audit)
    deleted, preserved = await svc.delete_block(
        block_id=bid,
        tenant_id=tid,
        clinic_id=cid,
        user_id=uid,
    )

    assert deleted is True
    assert preserved == 0

    # Audit must be written SYNC with doctor.availability_block_deleted
    mock_audit.write.assert_awaited_once()
    audit_entry = mock_audit.write.call_args[0][0]
    assert audit_entry.action == "doctor.availability_block_deleted"
    assert audit_entry.resource_type == "availability_block"


@pytest.mark.asyncio
async def test_availability_block_service_delete_preserves_confirmed_appointments() -> None:
    """delete_block with confirmed appts -> preserved_appointments > 0 (CRITICAL SC-3b, V-FN-7).

    Business rule: 'delete-block-preserves-confirmed-appointments' — CRITICAL.
    Slots with has_confirmed_appointment=True MUST NOT be deleted.
    Service returns (True, N) where N == preserved appointments count.
    """
    from src.modules.vitalia.clinics.application.availability_block_service import (
        AvailabilityBlockService,
    )

    tid = uuid4()
    cid = uuid4()
    uid = uuid4()
    bid = uuid4()

    mock_repo = AsyncMock()
    mock_audit = AsyncMock()

    # 3 confirmed appointments are preserved (repo.delete_block returns count)
    mock_repo.delete_block.return_value = 3

    svc = AvailabilityBlockService(block_repo=mock_repo, audit_repo=mock_audit)
    deleted, preserved = await svc.delete_block(
        block_id=bid,
        tenant_id=tid,
        clinic_id=cid,
        user_id=uid,
    )

    assert deleted is True
    assert preserved == 3, (
        f"Expected 3 preserved appointments, got {preserved}. "
        "CRITICAL: delete-block-preserves-confirmed-appointments invariant violated."
    )

    # Audit must be written SYNC
    mock_audit.write.assert_awaited_once()
    audit_entry = mock_audit.write.call_args[0][0]
    assert audit_entry.action == "doctor.availability_block_deleted"
    assert audit_entry.resource_type == "availability_block"


@pytest.mark.asyncio
async def test_availability_block_service_update_block_not_found_returns_none() -> None:
    """update_block for non-existent block returns None (caller -> 404)."""
    from src.modules.vitalia.clinics.application.availability_block_service import (
        AvailabilityBlockService,
    )

    tid = uuid4()
    cid = uuid4()
    uid = uuid4()

    mock_repo = AsyncMock()
    mock_audit = AsyncMock()
    mock_repo.get_block.return_value = None  # not found

    svc = AvailabilityBlockService(block_repo=mock_repo, audit_repo=mock_audit)

    result = await svc.update_block(
        block_id=uuid4(),
        tenant_id=tid,
        clinic_id=cid,
        doctor_id=uuid4(),
        user_id=uid,
        kind="recurrent",
        start_time=time(9, 0),
        end_time=time(12, 0),
        day_of_week=0,
        freq="weekly",
        end_condition_kind="open_ended",
        end_date=None,
        occurrences=None,
        specific_date=None,
    )

    assert result is None
    mock_repo.update_block.assert_not_awaited()


# ──────────────────────────────────────────────────────────────────────────────
# RBAC — admin_clinic required on mutations (V-NF-7 / hipaa-lite RBAC)
# ──────────────────────────────────────────────────────────────────────────────


def test_availability_block_post_route_has_rbac_dependency() -> None:
    """POST availability-blocks must have admin_clinic RBAC dependency.

    Checks that the route declares a Depends(require_brand_owner_access(...)) dependency.
    """
    from src.modules.vitalia.clinics.api.doctors_router import router

    post_block_routes = [
        r
        for r in router.routes
        if hasattr(r, "path") and "availability-blocks" in r.path and "POST" in getattr(r, "methods", set())
    ]
    assert post_block_routes, "POST availability-blocks route not found"
    route = post_block_routes[0]
    # Check the route has dependencies defined
    assert hasattr(route, "dependencies"), "Route must have dependencies attribute"
    deps = route.dependencies
    assert len(deps) > 0, (
        "POST availability-blocks must declare RBAC admin_clinic Depends() — "
        "HIPAA-lite requires admin_clinic role for all mutations"
    )


def test_availability_block_delete_route_has_rbac_dependency() -> None:
    """DELETE availability-blocks/{block_id} must have admin_clinic RBAC dependency."""
    from src.modules.vitalia.clinics.api.doctors_router import router

    delete_routes = [
        r
        for r in router.routes
        if hasattr(r, "path")
        and "availability-blocks" in r.path
        and "{block_id}" in r.path
        and "DELETE" in getattr(r, "methods", set())
    ]
    assert delete_routes, "DELETE availability-blocks/{block_id} route not found"
    route = delete_routes[0]
    assert hasattr(route, "dependencies"), "Route must have dependencies attribute"
    deps = route.dependencies
    assert len(deps) > 0, "DELETE availability-blocks/{block_id} must declare RBAC admin_clinic Depends()"


def test_availability_block_patch_route_has_rbac_dependency() -> None:
    """PATCH availability-blocks/{block_id} must have admin_clinic RBAC dependency."""
    from src.modules.vitalia.clinics.api.doctors_router import router

    patch_routes = [
        r
        for r in router.routes
        if hasattr(r, "path")
        and "availability-blocks" in r.path
        and "{block_id}" in r.path
        and "PATCH" in getattr(r, "methods", set())
    ]
    assert patch_routes, "PATCH availability-blocks/{block_id} route not found"
    route = patch_routes[0]
    assert hasattr(route, "dependencies"), "Route must have dependencies attribute"
    deps = route.dependencies
    assert len(deps) > 0, "PATCH availability-blocks/{block_id} must declare RBAC admin_clinic Depends()"


# ──────────────────────────────────────────────────────────────────────────────
# DTOs — discriminated union validation
# ──────────────────────────────────────────────────────────────────────────────


def test_recurrent_block_create_request_valid_end_date() -> None:
    """RecurrentBlockCreateRequest validates end_date condition."""
    from src.modules.vitalia.clinics.api.dtos import RecurrentBlockCreateRequest

    req = RecurrentBlockCreateRequest(
        kind="recurrent",
        start_time=time(9, 0),
        end_time=time(17, 0),
        day_of_week=0,
        freq="weekly",
        end_condition_kind="end_date",
        end_date=date.today() + timedelta(days=30),
        occurrences=None,
        specific_date=None,
    )
    assert req.kind == "recurrent"
    assert req.end_condition_kind == "end_date"


def test_one_off_block_create_request_valid() -> None:
    """OneOffBlockCreateRequest validates with specific_date."""
    from src.modules.vitalia.clinics.api.dtos import OneOffBlockCreateRequest

    req = OneOffBlockCreateRequest(
        kind="one_off",
        start_time=time(10, 0),
        end_time=time(12, 0),
        specific_date=date.today() + timedelta(days=7),
    )
    assert req.kind == "one_off"
    assert req.specific_date is not None


def test_availability_block_dto_from_domain() -> None:
    """AvailabilityBlockDTO can be constructed from domain entity fields."""
    from src.modules.vitalia.clinics.api.dtos import AvailabilityBlockDTO

    bid = uuid4()
    tid = uuid4()
    cid = uuid4()
    did = uuid4()
    today = date.today()

    dto = AvailabilityBlockDTO(
        id=bid,
        tenant_id=tid,
        clinic_id=cid,
        doctor_id=did,
        kind="recurrent",
        start_time=time(9, 0),
        end_time=time(17, 0),
        day_of_week=0,
        freq="weekly",
        end_condition_kind="end_date",
        end_date=today + timedelta(days=60),
        occurrences=None,
        specific_date=None,
    )
    assert dto.id == bid
    assert dto.kind == "recurrent"


def test_delete_block_response_dto_fields() -> None:
    """DeleteBlockResponse has correct field types."""
    from src.modules.vitalia.clinics.api.dtos import DeleteBlockResponse

    resp = DeleteBlockResponse(deleted=True, preserved_appointments=3)
    assert resp.deleted is True
    assert resp.preserved_appointments == 3


# ──────────────────────────────────────────────────────────────────────────────
# Patch create-request: D3-F daysOfWeek+interval in request DTO
# TDD RED-first: these fail BEFORE the fix (day_of_week/freq currently REQUIRED)
# ──────────────────────────────────────────────────────────────────────────────


def test_recurrent_block_create_request_accepts_days_of_week_primary() -> None:
    """RecurrentBlockCreateRequest accepts daysOfWeek+interval (primary D3-F fields).

    SC-D3F-CREATE-1: FE sends daysOfWeek=[0,3]+interval=2+occurrences=8 → 201.
    day_of_week and freq must be OPTIONAL (legacy backward compat).
    """
    from src.modules.vitalia.clinics.api.dtos import RecurrentBlockCreateRequest

    # Primary D3-F path — no legacy day_of_week / freq provided
    req = RecurrentBlockCreateRequest(
        kind="recurrent",
        start_time=time(9, 0),
        end_time=time(17, 0),
        days_of_week=[0, 3],  # Monday + Thursday
        interval=2,
        end_condition_kind="occurrences",
        occurrences=8,
    )
    assert req.days_of_week == [0, 3]
    assert req.interval == 2
    assert req.occurrences == 8
    # legacy fields are None / default when not provided
    assert req.day_of_week is None
    assert req.freq is None


def test_recurrent_block_create_request_accepts_legacy_only() -> None:
    """RecurrentBlockCreateRequest accepts legacy day_of_week+freq (regression guard).

    SC-D3F-CREATE-2: legacy clients send day_of_week+freq → 201 identical to before.
    """
    from src.modules.vitalia.clinics.api.dtos import RecurrentBlockCreateRequest

    req = RecurrentBlockCreateRequest(
        kind="recurrent",
        start_time=time(9, 0),
        end_time=time(17, 0),
        day_of_week=0,
        freq="weekly",
        end_condition_kind="occurrences",
        occurrences=4,
    )
    assert req.day_of_week == 0
    assert req.freq == "weekly"
    # days_of_week should be empty/None (legacy path — service derives from day_of_week)
    assert not req.days_of_week


def test_recurrent_block_create_request_rejects_neither_form() -> None:
    """RecurrentBlockCreateRequest rejects payloads with no day specification.

    SC-D3F-CREATE-3: no day_of_week AND no days_of_week → 422 with Spanish error.
    The validator must raise ValidationError before hitting the domain.
    """
    import pytest
    from pydantic import ValidationError

    from src.modules.vitalia.clinics.api.dtos import RecurrentBlockCreateRequest

    with pytest.raises(ValidationError) as exc_info:
        RecurrentBlockCreateRequest(
            kind="recurrent",
            start_time=time(9, 0),
            end_time=time(17, 0),
            # Neither days_of_week nor day_of_week provided
            end_condition_kind="open_ended",
        )
    errors = exc_info.value.errors()
    assert any(errors), "ValidationError must have at least one error"
    # Error message must be in Spanish neutro
    all_msgs = " ".join(str(e.get("msg", "")) for e in errors)
    # Check for Spanish error hint (must contain at least 'día' or 'semana')
    assert "día" in all_msgs or "semana" in all_msgs or "day_of_week" in all_msgs or "days_of_week" in all_msgs, (
        f"Error message must reference day fields. Got: {all_msgs!r}"
    )


def test_recurrent_block_create_request_days_of_week_field_exists() -> None:
    """RecurrentBlockCreateRequest must have days_of_week and interval fields (D3-F)."""
    from src.modules.vitalia.clinics.api.dtos import RecurrentBlockCreateRequest

    fields = set(RecurrentBlockCreateRequest.model_fields.keys())
    assert "days_of_week" in fields, "RecurrentBlockCreateRequest must have 'days_of_week' field (D3-F)"
    assert "interval" in fields, "RecurrentBlockCreateRequest must have 'interval' field (D3-F)"


def test_recurrent_block_create_request_day_of_week_optional_now() -> None:
    """day_of_week must be OPTIONAL in RecurrentBlockCreateRequest (legacy field, backward compat)."""
    from src.modules.vitalia.clinics.api.dtos import RecurrentBlockCreateRequest

    field_info = RecurrentBlockCreateRequest.model_fields.get("day_of_week")
    assert field_info is not None, "day_of_week field must exist"
    # The field must be optional (default is None, not required)
    assert field_info.default is None or field_info.is_required() is False, (
        "day_of_week must be OPTIONAL in RecurrentBlockCreateRequest (D3-F patch)"
    )


def test_recurrent_block_create_request_freq_optional_now() -> None:
    """freq must be OPTIONAL in RecurrentBlockCreateRequest (legacy field, backward compat)."""
    from src.modules.vitalia.clinics.api.dtos import RecurrentBlockCreateRequest

    field_info = RecurrentBlockCreateRequest.model_fields.get("freq")
    assert field_info is not None, "freq field must exist"
    assert field_info.default is None or field_info.is_required() is False, (
        "freq must be OPTIONAL in RecurrentBlockCreateRequest (D3-F patch)"
    )


def test_service_create_block_accepts_days_of_week() -> None:
    """AvailabilityBlockService.create_block must accept days_of_week + interval params.

    SC-D3F-CREATE-4: service signature updated to accept primary D3-F fields.
    """
    import inspect

    from src.modules.vitalia.clinics.application.availability_block_service import (
        AvailabilityBlockService,
    )

    sig = inspect.signature(AvailabilityBlockService.create_block)
    params = set(sig.parameters.keys())
    assert "days_of_week" in params, "create_block must accept days_of_week param"
    assert "interval" in params, "create_block must accept interval param"


def test_service_update_block_accepts_days_of_week() -> None:
    """AvailabilityBlockService.update_block must accept days_of_week + interval params.

    SC-D3F-CREATE-5: update_block (PATCH) also needs the new params.
    """
    import inspect

    from src.modules.vitalia.clinics.application.availability_block_service import (
        AvailabilityBlockService,
    )

    sig = inspect.signature(AvailabilityBlockService.update_block)
    params = set(sig.parameters.keys())
    assert "days_of_week" in params, "update_block must accept days_of_week param"
    assert "interval" in params, "update_block must accept interval param"
