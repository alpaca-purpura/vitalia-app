# cap: crm.crm-consent-optout
"""RED tests — T-BE-5: typeahead patient search (SC-empty-pacientes, SC-pacientes-grandes).

TDD: written BEFORE implementation.

HIPAA-lite required:
- Search results masked (name_masked, phone_masked only — never raw PHI)
- dual filter tenant_id + clinic_id on search()
- cursor pagination (next_cursor)
- PHI NEVER in URL params (q= is generic, not name/dni/phone)
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

TENANT_ID = uuid4()
CLINIC_ID = uuid4()
USER_ID = uuid4()


class TestPatientSearchMethodExists:
    """PatientRepository.search() and PatientService.search() must exist."""

    def test_search_method_exists_on_repo(self) -> None:
        from src.modules.vitalia.crm.infrastructure.persistence.patient_repository import (
            PatientRepository,
        )

        assert hasattr(PatientRepository, "search")

    def test_search_method_exists_on_service(self) -> None:
        from src.modules.vitalia.crm.application.services.patient_service import (
            PatientService,
        )

        assert hasattr(PatientService, "search")


class TestPatientSearchResponse:
    """PatientSearchResponse DTO structure."""

    def test_search_response_dto_has_items(self) -> None:
        from src.modules.vitalia.crm.application.dto.patient_dto import (
            PatientSearchResponse,
        )

        fields = PatientSearchResponse.model_fields
        assert "items" in fields

    def test_search_response_dto_has_next_cursor(self) -> None:
        from src.modules.vitalia.crm.application.dto.patient_dto import (
            PatientSearchResponse,
        )

        fields = PatientSearchResponse.model_fields
        assert "next_cursor" in fields

    def test_search_response_dto_has_total_approx(self) -> None:
        from src.modules.vitalia.crm.application.dto.patient_dto import (
            PatientSearchResponse,
        )

        fields = PatientSearchResponse.model_fields
        assert "total_approx" in fields


class TestPatientSearchItemMasked:
    """PatientSearchItem must expose masked fields only — no raw PHI."""

    def test_search_item_has_name_masked_not_name(self) -> None:
        from src.modules.vitalia.crm.application.dto.patient_dto import (
            PatientSearchItem,
        )

        fields = PatientSearchItem.model_fields
        assert "name_masked" in fields
        assert "name" not in fields

    def test_search_item_has_phone_masked_not_phone(self) -> None:
        from src.modules.vitalia.crm.application.dto.patient_dto import (
            PatientSearchItem,
        )

        fields = PatientSearchItem.model_fields
        assert "phone_masked" in fields
        assert "phone" not in fields

    def test_search_item_has_no_email(self) -> None:
        """email is PHI — must not appear in search results."""
        from src.modules.vitalia.crm.application.dto.patient_dto import (
            PatientSearchItem,
        )

        fields = PatientSearchItem.model_fields
        assert "email" not in fields

    def test_search_item_has_patient_id(self) -> None:
        from src.modules.vitalia.crm.application.dto.patient_dto import (
            PatientSearchItem,
        )

        fields = PatientSearchItem.model_fields
        assert "patient_id" in fields


class TestPatientSearchServiceBehavior:
    """SC-empty-pacientes: empty results when no match."""

    @pytest.mark.asyncio
    async def test_search_empty_returns_empty_items(self) -> None:
        from src.modules.vitalia.crm.application.services.patient_service import (
            PatientService,
        )

        mock_patient_repo = MagicMock()
        mock_patient_repo.search = AsyncMock(
            return_value={
                "items": [],
                "next_cursor": None,
                "total_approx": 0,
            }
        )
        mock_audit_repo = AsyncMock()
        mock_audit_repo.write = AsyncMock()

        service = PatientService(patient_repo=mock_patient_repo, audit_repo=mock_audit_repo)

        result = await service.search(
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            user_id=USER_ID,
            q="nomatch_xyz_123",
        )

        assert result.items == []
        assert result.next_cursor is None
        assert result.total_approx == 0

    @pytest.mark.asyncio
    async def test_search_returns_masked_items(self) -> None:
        """SC-pacientes-grandes: items have masked fields only."""
        import datetime

        from src.modules.vitalia.crm.application.dto.patient_dto import (
            PatientSearchItem,
        )
        from src.modules.vitalia.crm.application.services.patient_service import (
            PatientService,
        )

        patient_id = uuid4()
        now = datetime.datetime.now(tz=datetime.timezone.utc)

        mock_patient_repo = MagicMock()
        mock_patient_repo.search = AsyncMock(
            return_value={
                "items": [
                    {
                        "patient_id": patient_id,
                        "name_masked": "M. López",
                        "phone_masked": "+51 9***",
                        "channel_first": "whatsapp",
                        "created_at": now,
                    }
                ],
                "next_cursor": None,
                "total_approx": 1,
            }
        )
        mock_audit_repo = AsyncMock()
        mock_audit_repo.write = AsyncMock()

        service = PatientService(patient_repo=mock_patient_repo, audit_repo=mock_audit_repo)

        result = await service.search(
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            user_id=USER_ID,
            q="Ló",
        )

        assert len(result.items) == 1
        item = result.items[0]
        assert isinstance(item, PatientSearchItem)
        assert item.patient_id == patient_id
        assert item.name_masked == "M. López"
        assert item.phone_masked == "+51 9***"
        assert not hasattr(item, "name") or "name_masked" in item.model_fields

    @pytest.mark.asyncio
    async def test_search_writes_audit_log(self) -> None:
        """Search must write audit log entry (sync, HIPAA-lite)."""
        from src.modules.vitalia.crm.application.services.patient_service import (
            PatientService,
        )

        mock_patient_repo = MagicMock()
        mock_patient_repo.search = AsyncMock(return_value={"items": [], "next_cursor": None, "total_approx": 0})
        mock_audit_repo = AsyncMock()
        mock_audit_repo.write = AsyncMock()

        service = PatientService(patient_repo=mock_patient_repo, audit_repo=mock_audit_repo)

        await service.search(
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            user_id=USER_ID,
            q="test",
        )

        mock_audit_repo.write.assert_awaited_once()
        audit_entry = mock_audit_repo.write.call_args[0][0]
        assert audit_entry.action in ("patient_search", "search_patients")
        assert audit_entry.resource_type == "patient"

    @pytest.mark.asyncio
    async def test_search_enforces_dual_filter(self) -> None:
        """search() with clinic_id=None must raise MissingClinicFilterError."""
        from src.modules.vitalia._shared.repositories.phi_repository import (
            MissingClinicFilterError,
        )
        from src.modules.vitalia.crm.infrastructure.persistence.patient_repository import (
            PatientRepository,
        )

        mock_session = AsyncMock()
        mock_audit_repo = AsyncMock()

        repo = PatientRepository(session=mock_session, audit_repo=mock_audit_repo, kek=None)

        with pytest.raises(MissingClinicFilterError):
            await repo.search(
                tenant_id=TENANT_ID,
                clinic_id=None,  # type: ignore[arg-type]
                q="test",
            )

    @pytest.mark.asyncio
    async def test_search_cursor_pagination(self) -> None:
        """SC-pacientes-grandes: next_cursor returned when more pages exist."""
        import datetime

        from src.modules.vitalia.crm.application.services.patient_service import (
            PatientService,
        )

        cursor_id = uuid4()
        now = datetime.datetime.now(tz=datetime.timezone.utc)

        items_batch = [
            {
                "patient_id": uuid4(),
                "name_masked": f"P{i}. Test",
                "phone_masked": "+51 9***",
                "channel_first": "web",
                "created_at": now,
            }
            for i in range(20)
        ]

        mock_patient_repo = MagicMock()
        mock_patient_repo.search = AsyncMock(
            return_value={
                "items": items_batch,
                "next_cursor": cursor_id,
                "total_approx": 50,
            }
        )
        mock_audit_repo = AsyncMock()
        mock_audit_repo.write = AsyncMock()

        service = PatientService(patient_repo=mock_patient_repo, audit_repo=mock_audit_repo)

        result = await service.search(
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            user_id=USER_ID,
            q="Test",
        )

        assert len(result.items) == 20
        assert result.next_cursor is not None
        assert result.total_approx == 50
