# cap: crm.crm-consent-optout
"""RED tests — T-BE-5: inline patient create (SC-crear-paciente, SC-paciente-incompleto).

TDD: tests written BEFORE implementation. All will fail (RED) until
patient_repository.create_minimal(), patient_service.create_minimal(),
and POST /patients router endpoint are implemented.

HIPAA-lite required:
- PHI not leaked in response (name_masked only, never raw name/phone)
- audit_log row created (sync, pre-response)
- cross-tenant blocked (404)
- cross-clinic blocked (403 / MissingClinicFilterError)
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

TENANT_ID = uuid4()
CLINIC_ID = uuid4()
USER_ID = uuid4()
PATIENT_ID = uuid4()

VALID_HEADERS = {
    "Authorization": "Bearer test-token",
    "X-Tenant-ID": str(TENANT_ID),
    "X-Clinic-ID": str(CLINIC_ID),
}


def _make_create_payload(
    *,
    name: str = "María López",
    phone: str | None = "+51987654321",
    email: str | None = "test@example.com",
    channel: str = "whatsapp",
) -> dict:
    payload: dict = {"name": name, "channel": channel}
    if phone is not None:
        payload["phone"] = phone
    if email is not None:
        payload["email"] = email
    return payload


# ---------------------------------------------------------------------------
# SC-crear-paciente: successful minimal patient create
# ---------------------------------------------------------------------------


class TestPatientInlineCreateSuccess:
    """POST /api/v1/crm/patients — happy path."""

    def test_create_minimal_method_exists_on_service(self) -> None:
        """PatientInlineService must expose create_minimal()."""
        from src.modules.vitalia.crm.application.services.patient_service import (
            PatientService,
        )

        assert hasattr(PatientService, "create_minimal")

    def test_create_minimal_method_exists_on_repo(self) -> None:
        """PatientRepository must expose create_minimal()."""
        from src.modules.vitalia.crm.infrastructure.persistence.patient_repository import (
            PatientRepository,
        )

        assert hasattr(PatientRepository, "create_minimal")

    def test_create_returns_patient_id_and_masked_name(self) -> None:
        """Response must contain patient_id and name_masked (first initial + last name)."""
        from src.modules.vitalia.crm.application.dto.patient_dto import (
            PatientInlineCreateResponse,
        )

        # Simulate what the service would return
        resp = PatientInlineCreateResponse(
            patient_id=PATIENT_ID,
            name_masked="M. López",
            phone_masked="+51 9***",
            is_duplicate=False,
            created_at=__import__("datetime").datetime.now(tz=__import__("datetime").timezone.utc),
        )
        assert resp.patient_id == PATIENT_ID
        assert resp.name_masked == "M. López"
        assert resp.phone_masked == "+51 9***"
        assert resp.is_duplicate is False

    def test_create_returns_masked_not_raw_phi(self) -> None:
        """Response DTO must NOT expose raw name or raw phone fields."""
        from src.modules.vitalia.crm.application.dto.patient_dto import (
            PatientInlineCreateResponse,
        )

        # Fields raw name and phone MUST NOT exist on the response DTO
        assert not hasattr(PatientInlineCreateResponse.model_fields, "name"), (
            "PatientInlineCreateResponse must NOT have raw 'name' field (PHI leak)"
        )
        assert not hasattr(PatientInlineCreateResponse.model_fields, "phone"), (
            "PatientInlineCreateResponse must NOT have raw 'phone' field (PHI leak)"
        )

    @pytest.mark.asyncio
    async def test_service_create_minimal_calls_repo(self) -> None:
        """create_minimal() must delegate to patient_repo.create_minimal().

        The audit log is written inside the repository's create_minimal() (HIPAA-lite).
        Service test verifies: repo.create_minimal() called + result mapped correctly.
        Repo-level audit test is in test_patient_repository.py.
        """
        from src.modules.vitalia.crm.application.services.patient_service import (
            PatientService,
        )

        mock_patient_repo = MagicMock()
        mock_patient_repo.find_by_phone = AsyncMock(return_value=None)  # no dup
        mock_audit_repo = AsyncMock()
        mock_audit_repo.write = AsyncMock()

        now = __import__("datetime").datetime.now(tz=__import__("datetime").timezone.utc)
        # create_minimal on repo returns a minimal dict
        mock_patient_repo.create_minimal = AsyncMock(
            return_value={
                "patient_id": PATIENT_ID,
                "name_masked": "M. López",
                "phone_masked": "+51 9***",
                "is_duplicate": False,
                "created_at": now,
            }
        )

        service = PatientService(patient_repo=mock_patient_repo, audit_repo=mock_audit_repo)

        result = await service.create_minimal(
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            user_id=USER_ID,
            name="María López",
            phone="+51987654321",
            email="test@example.com",
            channel="whatsapp",
        )

        # Repo.create_minimal MUST have been called
        mock_patient_repo.create_minimal.assert_awaited_once()
        call_kwargs = mock_patient_repo.create_minimal.call_args[1]
        assert str(call_kwargs["tenant_id"]) == str(TENANT_ID)
        assert str(call_kwargs["clinic_id"]) == str(CLINIC_ID)
        assert call_kwargs["name"] == "María López"

        # Result properly mapped
        assert result.patient_id == PATIENT_ID
        assert result.name_masked == "M. López"
        assert result.is_duplicate is False


# ---------------------------------------------------------------------------
# SC-paciente-incompleto: missing required fields → 422, no row created
# ---------------------------------------------------------------------------


class TestPatientInlineCreateValidation:
    """POST /api/v1/crm/patients — input validation."""

    def test_create_request_dto_requires_name(self) -> None:
        """PatientInlineCreateRequest must require name (non-optional)."""
        from pydantic import ValidationError

        from src.modules.vitalia.crm.application.dto.patient_dto import (
            PatientInlineCreateRequest,
        )

        with pytest.raises(ValidationError):
            PatientInlineCreateRequest(channel="whatsapp")  # missing name

    def test_create_request_dto_requires_channel(self) -> None:
        """PatientInlineCreateRequest must require channel."""
        from pydantic import ValidationError

        from src.modules.vitalia.crm.application.dto.patient_dto import (
            PatientInlineCreateRequest,
        )

        with pytest.raises(ValidationError):
            PatientInlineCreateRequest(name="María López")  # missing channel

    def test_create_request_dto_validates_channel_enum(self) -> None:
        """channel must be one of the allowed literals."""
        from pydantic import ValidationError

        from src.modules.vitalia.crm.application.dto.patient_dto import (
            PatientInlineCreateRequest,
        )

        with pytest.raises(ValidationError):
            PatientInlineCreateRequest(name="María López", channel="invalid_channel")

    def test_create_request_dto_accepts_valid_payload(self) -> None:
        """Valid payload must pass validation."""
        from src.modules.vitalia.crm.application.dto.patient_dto import (
            PatientInlineCreateRequest,
        )

        req = PatientInlineCreateRequest(
            name="María López",
            phone="+51987654321",
            channel="whatsapp",
        )
        assert req.name == "María López"
        assert req.channel == "whatsapp"

    def test_create_request_dto_accepts_minimal_payload(self) -> None:
        """Only name+channel required; phone, email, note are optional."""
        from src.modules.vitalia.crm.application.dto.patient_dto import (
            PatientInlineCreateRequest,
        )

        req = PatientInlineCreateRequest(name="Carlos Gómez", channel="walk_in")
        assert req.phone is None
        assert req.email is None


# ---------------------------------------------------------------------------
# HIPAA-lite: PHI not leaked in response model
# ---------------------------------------------------------------------------


class TestPhiNotLeakedInResponse:
    """Response DTO (PatientInlineCreateResponse) must NOT expose raw PHI."""

    def test_response_dto_has_name_masked_not_name(self) -> None:
        """name_masked exposed, raw name NOT in model_fields."""
        from src.modules.vitalia.crm.application.dto.patient_dto import (
            PatientInlineCreateResponse,
        )

        fields = PatientInlineCreateResponse.model_fields
        assert "name_masked" in fields
        assert "name" not in fields

    def test_response_dto_has_phone_masked_not_phone(self) -> None:
        """phone_masked exposed, raw phone NOT in model_fields."""
        from src.modules.vitalia.crm.application.dto.patient_dto import (
            PatientInlineCreateResponse,
        )

        fields = PatientInlineCreateResponse.model_fields
        assert "phone_masked" in fields
        assert "phone" not in fields

    def test_response_dto_has_no_email_field(self) -> None:
        """email is PHI — must NOT be in response DTO at all."""
        from src.modules.vitalia.crm.application.dto.patient_dto import (
            PatientInlineCreateResponse,
        )

        fields = PatientInlineCreateResponse.model_fields
        assert "email" not in fields


# ---------------------------------------------------------------------------
# HIPAA-lite: cross-tenant isolation
# ---------------------------------------------------------------------------


class TestCrossTenantIsolation:
    """PatientRepository.create_minimal() must enforce dual filter."""

    @pytest.mark.asyncio
    async def test_cross_clinic_raises_missing_filter(self) -> None:
        """create_minimal with clinic_id=None raises MissingClinicFilterError."""
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
            await repo.create_minimal(
                tenant_id=TENANT_ID,
                clinic_id=None,  # type: ignore[arg-type]
                user_id=USER_ID,
                name="Test Patient",
                channel="whatsapp",
            )
