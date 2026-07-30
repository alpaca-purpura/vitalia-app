# cap: crm.crm-consent-optout
"""RED tests — T-BE-5: phone dedup (SC-paciente-duplicado / RN-9).

TDD: written BEFORE implementation.

find_by_phone() is used to offer the "use existing patient?" dialog in the
inline patient creation flow when a matching phone is already in the DB.

HIPAA-lite: result is masked (no raw PHI returned).
dual filter: tenant_id + clinic_id mandatory.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

TENANT_ID = uuid4()
CLINIC_ID = uuid4()
EXISTING_PATIENT_ID = uuid4()


class TestFindByPhoneMethodExists:
    """PatientRepository.find_by_phone() and PatientService.find_by_phone() must exist."""

    def test_find_by_phone_on_repo(self) -> None:
        from src.modules.vitalia.crm.infrastructure.persistence.patient_repository import (
            PatientRepository,
        )

        assert hasattr(PatientRepository, "find_by_phone")

    def test_find_by_phone_on_service(self) -> None:
        from src.modules.vitalia.crm.application.services.patient_service import (
            PatientService,
        )

        assert hasattr(PatientService, "find_by_phone")


class TestFindByPhoneDedup:
    """SC-paciente-duplicado / RN-9: detect existing patient by phone."""

    @pytest.mark.asyncio
    async def test_find_by_phone_returns_patient_dict_when_found(self) -> None:
        """find_by_phone() returns patient dict (masked) if phone matches existing row."""
        import datetime

        from src.modules.vitalia.crm.application.services.patient_service import (
            PatientService,
        )

        mock_patient_repo = MagicMock()
        mock_patient_repo.find_by_phone = AsyncMock(
            return_value={
                "patient_id": EXISTING_PATIENT_ID,
                "name_masked": "M. López",
                "phone_masked": "+51 9***",
                "created_at": datetime.datetime.now(tz=datetime.timezone.utc),
            }
        )
        mock_audit_repo = AsyncMock()
        mock_audit_repo.write = AsyncMock()

        service = PatientService(patient_repo=mock_patient_repo, audit_repo=mock_audit_repo)

        result = await service.find_by_phone(
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            user_id=uuid4(),
            phone="+51987654321",
        )

        assert result is not None
        assert result["patient_id"] == EXISTING_PATIENT_ID
        # Masked fields present
        assert "name_masked" in result
        assert "phone_masked" in result
        # Raw PHI must NOT be present
        assert "name" not in result
        assert "phone" not in result
        assert "email" not in result

    @pytest.mark.asyncio
    async def test_find_by_phone_returns_none_when_not_found(self) -> None:
        """find_by_phone() returns None when no patient matches the phone."""
        from src.modules.vitalia.crm.application.services.patient_service import (
            PatientService,
        )

        mock_patient_repo = MagicMock()
        mock_patient_repo.find_by_phone = AsyncMock(return_value=None)
        mock_audit_repo = AsyncMock()

        service = PatientService(patient_repo=mock_patient_repo, audit_repo=mock_audit_repo)

        result = await service.find_by_phone(
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            user_id=uuid4(),
            phone="+51999999999",
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_find_by_phone_enforces_dual_filter(self) -> None:
        """find_by_phone with clinic_id=None must raise MissingClinicFilterError."""
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
            await repo.find_by_phone(
                tenant_id=TENANT_ID,
                clinic_id=None,  # type: ignore[arg-type]
                phone="+51987654321",
            )

    @pytest.mark.asyncio
    async def test_find_by_phone_no_cross_tenant_leak(self) -> None:
        """Phone match from different tenant must NOT be returned."""
        from src.modules.vitalia.crm.application.services.patient_service import (
            PatientService,
        )

        # Repo returns None for this tenant+clinic (even though phone exists for other tenant)
        mock_patient_repo = MagicMock()
        mock_patient_repo.find_by_phone = AsyncMock(return_value=None)
        mock_audit_repo = AsyncMock()

        service = PatientService(patient_repo=mock_patient_repo, audit_repo=mock_audit_repo)

        # Call with OUR tenant — should get None (other tenant's row not returned)
        result = await service.find_by_phone(
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            user_id=uuid4(),
            phone="+51987654321",
        )
        assert result is None

        # Repo was called with correct tenant+clinic (dual filter)
        call_kwargs = mock_patient_repo.find_by_phone.call_args[1]
        assert str(call_kwargs["tenant_id"]) == str(TENANT_ID)
        assert str(call_kwargs["clinic_id"]) == str(CLINIC_ID)

    @pytest.mark.asyncio
    async def test_create_minimal_detects_duplicate_via_find_by_phone(self) -> None:
        """When phone already exists, create_minimal() sets is_duplicate=True (RN-9)."""
        import datetime

        from src.modules.vitalia.crm.application.services.patient_service import (
            PatientService,
        )

        existing = {
            "patient_id": EXISTING_PATIENT_ID,
            "name_masked": "M. López",
            "phone_masked": "+51 9***",
            "created_at": datetime.datetime.now(tz=datetime.timezone.utc),
        }

        mock_patient_repo = MagicMock()
        # find_by_phone detects existing patient
        mock_patient_repo.find_by_phone = AsyncMock(return_value=existing)
        # create_minimal would return the existing patient flagged as duplicate
        mock_patient_repo.create_minimal = AsyncMock(
            return_value={
                "patient_id": EXISTING_PATIENT_ID,
                "name_masked": "M. López",
                "phone_masked": "+51 9***",
                "is_duplicate": True,
                "created_at": datetime.datetime.now(tz=datetime.timezone.utc),
            }
        )
        mock_audit_repo = AsyncMock()
        mock_audit_repo.write = AsyncMock()

        service = PatientService(patient_repo=mock_patient_repo, audit_repo=mock_audit_repo)

        result = await service.create_minimal(
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            user_id=uuid4(),
            name="María López",
            phone="+51987654321",  # same phone as existing
            channel="whatsapp",
        )

        # Service must surface is_duplicate=True for RN-9 dialog
        assert result.is_duplicate is True
        assert result.patient_id == EXISTING_PATIENT_ID
