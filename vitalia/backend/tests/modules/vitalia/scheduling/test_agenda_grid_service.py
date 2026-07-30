"""RED tests — AgendaGridService: PHI mask + audit log + cross-clinic 404.

TDD: tests define expected interface BEFORE implementation.
All tests use in-memory mocks — no Postgres required (pure unit tests).

Contract (03-arch § 5 + hipaa-lite.md):
- PHI masking applied to all slot projections (never raw patient.name)
- Audit log sync write before returning response
- Cross-clinic query returns empty list (dual filter enforced at repo layer)

Per 05-guidelines TDD-mandatory + vitalia/.claude/rules/hipaa-lite.md
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest

# ---------------------------------------------------------------------------
# Import helpers (lazy — fail RED until files exist)
# ---------------------------------------------------------------------------


def _import_service():
    from src.modules.vitalia.scheduling.application.services.agenda_grid_service import (  # noqa: PLC0415
        AgendaGridService,
    )

    return AgendaGridService


def _import_phi_masking():
    from src.modules.vitalia._shared.phi_masking import (  # noqa: PLC0415
        mask_dni,
        mask_name,
    )

    return mask_name, mask_dni


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

TENANT_ID = uuid4()
CLINIC_ID = uuid4()
OTHER_CLINIC_ID = uuid4()
APPT_ID = uuid4()
USER_ID = uuid4()


def _make_slot_dict(
    clinic_id: UUID = CLINIC_ID,
    *,
    patient_name_masked: str = "P. Hernández",
    dni_masked: str = "12.***.***",
) -> dict:
    return {
        "slot_id": str(APPT_ID),
        "appointment_id": str(APPT_ID),
        "tenant_id": str(TENANT_ID),
        "clinic_id": str(clinic_id),
        "patient_name_masked": patient_name_masked,
        "dni_masked": dni_masked,
        "service": "Limpieza dental",
        "doctor": "Dra. García",
        "start_at": datetime(2026, 5, 27, 9, 0, tzinfo=timezone.utc),
        "end_at": datetime(2026, 5, 27, 10, 0, tzinfo=timezone.utc),
        "payment_status": "sin_pago",
        "origin": "walk_in",
        "balance_amount_cents": 15000,
        "currency": "PEN",
    }


def _make_mock_repo(slots: list[dict] | None = None) -> MagicMock:
    repo = MagicMock()
    # Use 'is None' check so empty list [] is respected (not treated as falsy)
    default_slots = [_make_slot_dict()] if slots is None else slots
    repo.list_slots = AsyncMock(return_value=default_slots)
    return repo


def _make_mock_audit_writer() -> MagicMock:
    writer = MagicMock()
    writer.write = AsyncMock(return_value=None)
    return writer


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestAgendaGridServicePhiMask:
    """A1: PHI masking applied to response projections."""

    @pytest.mark.asyncio
    async def test_phi_mask_applied_to_response(self):
        """AgendaGridService.list_slots must return slots with masked PHI fields.

        The service layer must call mask_name/mask_dni on raw patient data
        or verify that the repository already returns masked values.
        The response must never expose a raw patient.name or raw DNI.
        """
        AgendaGridService = _import_service()
        repo = _make_mock_repo([_make_slot_dict(patient_name_masked="P. Hernández", dni_masked="12.***.***")])
        audit_writer = _make_mock_audit_writer()
        service = AgendaGridService(repo=repo, audit_writer=audit_writer)

        result = await service.list_slots(
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            date_from=datetime(2026, 5, 27, tzinfo=timezone.utc),
            date_to=datetime(2026, 5, 27, 23, 59, tzinfo=timezone.utc),
            user_id=USER_ID,
        )

        assert len(result) >= 1
        for slot in result:
            # PHI must be masked — no raw full name pattern
            name = slot.get("patient_name_masked") or slot.get("patient_name", "")
            assert "." in name or len(name.split()) <= 2, (
                f"patient_name_masked should be in masked format, got: {name!r}"
            )
            # DNI must be masked
            dni = slot.get("dni_masked") or slot.get("dni", "")
            if dni:
                assert "***" in dni or "*" in dni, f"dni_masked should be masked, got: {dni!r}"

    @pytest.mark.asyncio
    async def test_phi_mask_function_name_format(self):
        """mask_name() must return 'P. Apellido' format from full name."""
        mask_name, mask_dni = _import_phi_masking()

        assert mask_name("Pedro Hernández") == "P. Hernández"
        assert mask_name("Ana María González") == "A. González"
        assert mask_name("Juan") == "J."
        assert mask_name("") == "P."  # fallback for empty

    @pytest.mark.asyncio
    async def test_phi_mask_function_dni_format(self):
        """mask_dni() must return '12.***' format."""
        mask_name, mask_dni = _import_phi_masking()

        result = mask_dni("12345678")
        assert result.startswith("12")
        assert "***" in result

        result_short = mask_dni("1234")
        assert "***" in result_short or result_short == "12**"


class TestAgendaGridServiceAuditLog:
    """A2: Audit log sync write before response."""

    @pytest.mark.asyncio
    async def test_audit_log_sync_write(self):
        """list_slots() must write audit log row before returning.

        HIPAA-lite mandate: every PHI read must log a row synchronously.
        The audit_writer.write() must be called BEFORE the method returns.
        """
        AgendaGridService = _import_service()
        repo = _make_mock_repo()
        audit_writer = _make_mock_audit_writer()
        service = AgendaGridService(repo=repo, audit_writer=audit_writer)

        await service.list_slots(
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            date_from=datetime(2026, 5, 27, tzinfo=timezone.utc),
            date_to=datetime(2026, 5, 27, 23, 59, tzinfo=timezone.utc),
            user_id=USER_ID,
        )

        audit_writer.write.assert_called_once()
        call_kwargs = audit_writer.write.call_args.kwargs
        assert call_kwargs.get("tenant_id") == TENANT_ID
        assert call_kwargs.get("clinic_id") == CLINIC_ID
        assert "agenda" in call_kwargs.get("action", "").lower() or "read" in call_kwargs.get("action", "").lower()

    @pytest.mark.asyncio
    async def test_audit_log_contains_required_fields(self):
        """Audit log row must contain action, resource_type, resource_id fields."""
        AgendaGridService = _import_service()
        repo = _make_mock_repo()
        audit_writer = _make_mock_audit_writer()
        service = AgendaGridService(repo=repo, audit_writer=audit_writer)

        await service.list_slots(
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            date_from=datetime(2026, 5, 27, tzinfo=timezone.utc),
            date_to=datetime(2026, 5, 27, 23, 59, tzinfo=timezone.utc),
            user_id=USER_ID,
        )

        call_kwargs = audit_writer.write.call_args.kwargs
        assert "action" in call_kwargs
        assert "resource_type" in call_kwargs


class TestAgendaGridServiceCrossClinic:
    """A3: Cross-clinic query returns empty list (not 404 for grid)."""

    @pytest.mark.asyncio
    async def test_cross_clinic_returns_empty(self):
        """Grid with wrong clinic_id returns empty slots (dual filter at repo layer).

        The repo mock returns [] for mismatched clinic_id.
        Service must pass clinic_id through and return empty, not raise 404.
        (Grid list → 200 empty. Drawer detail → 404. Different behavior.)
        """
        AgendaGridService = _import_service()
        # Repo returns empty list for cross-clinic (simulates dual filter rejection)
        repo = _make_mock_repo(slots=[])
        audit_writer = _make_mock_audit_writer()
        service = AgendaGridService(repo=repo, audit_writer=audit_writer)

        result = await service.list_slots(
            tenant_id=TENANT_ID,
            clinic_id=OTHER_CLINIC_ID,
            date_from=datetime(2026, 5, 27, tzinfo=timezone.utc),
            date_to=datetime(2026, 5, 27, 23, 59, tzinfo=timezone.utc),
            user_id=USER_ID,
        )

        assert result == []
        # repo must have been called with the mismatched clinic_id
        repo.list_slots.assert_called_once()
        call_kwargs = repo.list_slots.call_args.kwargs
        assert call_kwargs.get("clinic_id") == OTHER_CLINIC_ID
