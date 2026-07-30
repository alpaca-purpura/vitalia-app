# cap: clinics.lisa.doctores
"""Tests for AvailabilityBlock domain validation + mutable invariants.

TDD RED-first — domain validation + service reproject-future-only.

Validators: V-FN-1, V-FN-2, V-FN-7, V-ARCH-1, V-ARCH-4
Gherkin coverage: SC-1, SC-1b, SC-1d, SC-3b
"""

from __future__ import annotations

from datetime import date, time, timedelta
from uuid import uuid4

import pytest

# ── Domain validation tests (pure Python — no service needed) ────────────────


def test_recurrent_block_requires_end_condition_kind() -> None:
    """recurrence-end-condition-required: ValueError when end_condition_kind is None.

    Business rule from 01-spec.md § Business rules:
    'A recurrent block without explicit end_condition → ValueError'.
    """
    from src.modules.vitalia.clinics.domain.availability_block import AvailabilityBlock

    with pytest.raises(ValueError, match="condicion de fin"):
        AvailabilityBlock(
            id=uuid4(),
            tenant_id=uuid4(),
            clinic_id=uuid4(),
            doctor_id=uuid4(),
            kind="recurrent",
            start_time=time(9, 0),
            end_time=time(17, 0),
            day_of_week=0,
            freq="weekly",
            end_condition_kind=None,  # MISSING — must raise ValueError
            end_date=None,
            occurrences=None,
            specific_date=None,
        )


def test_recurrent_end_date_requires_date_value() -> None:
    """end_condition_kind='end_date' with end_date=None → ValueError."""
    from src.modules.vitalia.clinics.domain.availability_block import AvailabilityBlock

    with pytest.raises(ValueError, match="end_date"):
        AvailabilityBlock(
            id=uuid4(),
            tenant_id=uuid4(),
            clinic_id=uuid4(),
            doctor_id=uuid4(),
            kind="recurrent",
            start_time=time(9, 0),
            end_time=time(17, 0),
            day_of_week=0,
            freq="weekly",
            end_condition_kind="end_date",
            end_date=None,  # MISSING — must raise ValueError
            occurrences=None,
            specific_date=None,
        )


def test_recurrent_occurrences_requires_positive_count() -> None:
    """end_condition_kind='occurrences' with occurrences=None or 0 → ValueError."""
    from src.modules.vitalia.clinics.domain.availability_block import AvailabilityBlock

    with pytest.raises(ValueError, match="occurrences"):
        AvailabilityBlock(
            id=uuid4(),
            tenant_id=uuid4(),
            clinic_id=uuid4(),
            doctor_id=uuid4(),
            kind="recurrent",
            start_time=time(9, 0),
            end_time=time(17, 0),
            day_of_week=0,
            freq="weekly",
            end_condition_kind="occurrences",
            end_date=None,
            occurrences=None,  # MISSING — must raise ValueError
            specific_date=None,
        )


def test_recurrent_occurrences_zero_raises() -> None:
    """occurrences=0 is not positive — must raise ValueError."""
    from src.modules.vitalia.clinics.domain.availability_block import AvailabilityBlock

    with pytest.raises(ValueError, match="occurrences"):
        AvailabilityBlock(
            id=uuid4(),
            tenant_id=uuid4(),
            clinic_id=uuid4(),
            doctor_id=uuid4(),
            kind="recurrent",
            start_time=time(9, 0),
            end_time=time(17, 0),
            day_of_week=0,
            freq="weekly",
            end_condition_kind="occurrences",
            end_date=None,
            occurrences=0,  # zero is not ≥1 — must raise
            specific_date=None,
        )


def test_recurrent_open_ended_valid() -> None:
    """end_condition_kind='open_ended' is valid — no error raised."""
    from src.modules.vitalia.clinics.domain.availability_block import AvailabilityBlock

    block = AvailabilityBlock(
        id=uuid4(),
        tenant_id=uuid4(),
        clinic_id=uuid4(),
        doctor_id=uuid4(),
        kind="recurrent",
        start_time=time(9, 0),
        end_time=time(17, 0),
        day_of_week=0,
        freq="weekly",
        end_condition_kind="open_ended",
        end_date=None,
        occurrences=None,
        specific_date=None,
    )
    assert block.end_condition_kind == "open_ended"


def test_one_off_requires_specific_date() -> None:
    """one_off block without specific_date → ValueError."""
    from src.modules.vitalia.clinics.domain.availability_block import AvailabilityBlock

    with pytest.raises(ValueError, match="one_off"):
        AvailabilityBlock(
            id=uuid4(),
            tenant_id=uuid4(),
            clinic_id=uuid4(),
            doctor_id=uuid4(),
            kind="one_off",
            start_time=time(9, 0),
            end_time=time(17, 0),
            day_of_week=None,
            freq=None,
            end_condition_kind=None,
            end_date=None,
            occurrences=None,
            specific_date=None,  # MISSING — must raise ValueError
        )


def test_start_time_before_end_time_enforced() -> None:
    """start_time >= end_time → ValueError."""
    from src.modules.vitalia.clinics.domain.availability_block import AvailabilityBlock

    with pytest.raises(ValueError, match="start_time"):
        AvailabilityBlock(
            id=uuid4(),
            tenant_id=uuid4(),
            clinic_id=uuid4(),
            doctor_id=uuid4(),
            kind="one_off",
            start_time=time(17, 0),
            end_time=time(9, 0),  # end BEFORE start — must raise
            day_of_week=None,
            freq=None,
            end_condition_kind=None,
            end_date=None,
            occurrences=None,
            specific_date=date.today() + timedelta(days=3),
        )


def test_valid_recurrent_weekly_end_date() -> None:
    """Happy path: recurrent weekly + end_date succeeds."""
    from src.modules.vitalia.clinics.domain.availability_block import AvailabilityBlock

    block = AvailabilityBlock(
        id=uuid4(),
        tenant_id=uuid4(),
        clinic_id=uuid4(),
        doctor_id=uuid4(),
        kind="recurrent",
        start_time=time(9, 0),
        end_time=time(17, 0),
        day_of_week=0,
        freq="weekly",
        end_condition_kind="end_date",
        end_date=date(2026, 12, 31),
        occurrences=None,
        specific_date=None,
    )
    assert block.kind == "recurrent"
    assert block.end_condition_kind == "end_date"
    assert block.end_date == date(2026, 12, 31)


def test_valid_biweekly_occurrences() -> None:
    """Happy path: biweekly + occurrences=6 succeeds."""
    from src.modules.vitalia.clinics.domain.availability_block import AvailabilityBlock

    block = AvailabilityBlock(
        id=uuid4(),
        tenant_id=uuid4(),
        clinic_id=uuid4(),
        doctor_id=uuid4(),
        kind="recurrent",
        start_time=time(10, 0),
        end_time=time(12, 0),
        day_of_week=2,
        freq="biweekly",
        end_condition_kind="occurrences",
        end_date=None,
        occurrences=6,
        specific_date=None,
    )
    assert block.occurrences == 6


def test_valid_one_off_block() -> None:
    """Happy path: one_off with specific_date succeeds."""
    from src.modules.vitalia.clinics.domain.availability_block import AvailabilityBlock

    target = date(2026, 7, 15)
    block = AvailabilityBlock(
        id=uuid4(),
        tenant_id=uuid4(),
        clinic_id=uuid4(),
        doctor_id=uuid4(),
        kind="one_off",
        start_time=time(14, 0),
        end_time=time(16, 0),
        day_of_week=None,
        freq=None,
        end_condition_kind=None,
        end_date=None,
        occurrences=None,
        specific_date=target,
    )
    assert block.specific_date == target


# ── Repository inheritance (V-ARCH-1) ────────────────────────────────────────


def test_availability_block_repository_inherits_compound_scope_repository_base() -> None:
    """AvailabilityBlockRepository must inherit CompoundScopeRepositoryBase.

    Arch gate: test_compound_scope_repository_used.py enforces engine base
    for all PHI repos (HIPAA dual-filter contract).
    """
    from luana_core_platform.repositories.compound_scope_repository import (
        CompoundScopeRepositoryBase,
    )

    from src.modules.vitalia.clinics.infrastructure.repositories.availability_block_repository import (
        AvailabilityBlockRepository,
    )

    assert issubclass(AvailabilityBlockRepository, CompoundScopeRepositoryBase), (
        "AvailabilityBlockRepository must inherit CompoundScopeRepositoryBase for HIPAA dual-filter compliance."
    )


def test_availability_block_repository_validates_dual_filter() -> None:
    """validate_dual_filter raises MissingClinicFilterError when clinic_id is None."""
    from unittest.mock import MagicMock

    from src.modules.vitalia._shared.repositories.phi_repository import (
        MissingClinicFilterError,
    )
    from src.modules.vitalia.clinics.infrastructure.repositories.availability_block_repository import (
        AvailabilityBlockRepository,
    )

    mock_session = MagicMock()
    repo = AvailabilityBlockRepository(session=mock_session)

    with pytest.raises(MissingClinicFilterError):
        repo.validate_dual_filter(tenant_id=uuid4(), clinic_id=None)


def test_availability_block_repository_requires_tenant_id() -> None:
    """validate_dual_filter raises ValueError when tenant_id is None."""
    from unittest.mock import MagicMock

    from src.modules.vitalia.clinics.infrastructure.repositories.availability_block_repository import (
        AvailabilityBlockRepository,
    )

    mock_session = MagicMock()
    repo = AvailabilityBlockRepository(session=mock_session)

    with pytest.raises(ValueError, match="tenant_id"):
        repo.validate_dual_filter(tenant_id=None, clinic_id=uuid4())


# ── Port contract (V-ARCH-4) ─────────────────────────────────────────────────


def test_availability_repo_port_is_abc() -> None:
    """AvailabilityRepoPort must be an abstract base class (ABC)."""
    import inspect

    from src.modules.vitalia.clinics.application.ports.availability_repo_port import (
        AvailabilityRepoPort,
    )

    assert inspect.isabstract(AvailabilityRepoPort), (
        "AvailabilityRepoPort must be abstract (ABC) — application layer depends on port, not impl"
    )


def test_availability_repo_port_has_required_methods() -> None:
    """Port must declare all required abstract methods."""
    from src.modules.vitalia.clinics.application.ports.availability_repo_port import (
        AvailabilityRepoPort,
    )

    required = {"list_blocks", "get_block", "create_block", "update_block", "delete_block", "count_future_confirmed"}
    abstract = set(AvailabilityRepoPort.__abstractmethods__)
    missing = required - abstract
    assert not missing, f"AvailabilityRepoPort missing abstract methods: {missing}"


# ── Service: reproject_future only modifies future slots ─────────────────────


def test_reproject_future_does_not_touch_past_slots() -> None:
    """reproject_future only touches slot_date >= today.

    Past slots (including those with confirmed appointments) must not be
    touched by the reproject logic.
    """
    from src.modules.vitalia.clinics.application.availability_projection_service import (
        AvailabilityProjectionService,
    )
    from src.modules.vitalia.clinics.domain.availability_block import AvailabilityBlock

    today = date.today()
    block = AvailabilityBlock(
        id=uuid4(),
        tenant_id=uuid4(),
        clinic_id=uuid4(),
        doctor_id=uuid4(),
        kind="recurrent",
        start_time=time(9, 0),
        end_time=time(10, 0),
        day_of_week=0,
        freq="weekly",
        end_condition_kind="end_date",
        end_date=today + timedelta(days=60),
        occurrences=None,
        specific_date=None,
    )
    service = AvailabilityProjectionService(slot_duration_minutes=30)
    # All projected slots should be >= today
    slots = service.project_block(block, reference_date=today)
    for s in slots:
        assert s.slot_date >= today, f"Slot on {s.slot_date} predates reference {today} — reproject must be future-only"


# ── delete_block preserves confirmed appointments (SC-1d, SC-3b) ─────────────


def test_retire_future_logic_preserves_confirmed_slots() -> None:
    """Delete block must preserve slots with has_confirmed_appointment=True.

    Validates business rule: 'delete-block-preserves-confirmed-appointments'.
    Service retire_future() must count confirmed slots and leave them untouched.
    """
    from src.modules.vitalia.clinics.application.availability_projection_service import (
        AvailabilityProjectionService,
        ProjectedSlot,
    )

    today = date.today()
    block_id = uuid4()
    tenant_id = uuid4()
    clinic_id = uuid4()
    doctor_id = uuid4()

    # Build existing slots: some confirmed, some free
    existing = [
        ProjectedSlot(
            id=uuid4(),
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            doctor_id=doctor_id,
            block_id=block_id,
            slot_date=today + timedelta(days=7),
            start_ts=__import__("datetime").datetime(2026, 7, 7, 9, 0, tzinfo=__import__("datetime").timezone.utc),
            end_ts=__import__("datetime").datetime(2026, 7, 7, 9, 30, tzinfo=__import__("datetime").timezone.utc),
            has_confirmed_appointment=True,  # CONFIRMED — must NOT be deleted
        ),
        ProjectedSlot(
            id=uuid4(),
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            doctor_id=doctor_id,
            block_id=block_id,
            slot_date=today + timedelta(days=14),
            start_ts=__import__("datetime").datetime(2026, 7, 14, 9, 0, tzinfo=__import__("datetime").timezone.utc),
            end_ts=__import__("datetime").datetime(2026, 7, 14, 9, 30, tzinfo=__import__("datetime").timezone.utc),
            has_confirmed_appointment=False,  # FREE — can be deleted
        ),
    ]

    service = AvailabilityProjectionService(slot_duration_minutes=30)
    to_delete, preserved_count = service.classify_future_slots_for_deletion(
        existing_slots=existing,
        reference_date=today,
    )

    # Free slots go to deletion list, confirmed are preserved
    assert preserved_count == 1, f"Expected 1 confirmed slot preserved, got {preserved_count}"
    assert len(to_delete) == 1, f"Expected 1 slot in deletion list, got {len(to_delete)}"
    # The deletable slot has no confirmed appointment
    assert not to_delete[0].has_confirmed_appointment
