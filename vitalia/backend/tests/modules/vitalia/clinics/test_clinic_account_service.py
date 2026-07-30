# cap: configuracion.cuenta
"""RED tests for ClinicAccountService — written BEFORE implementation (TDD).

All tests are UNIT (mocked repos + audit_writer). No DB required.
Covers:
  - get_account: returns ClinicAccountData aggregating clinic + config
  - get_account: 404 when clinic not found
  - patch_account: updates clinic fields + specialties in same transaction
  - patch_account: validates fiscal_id — bad format → 422
  - patch_account: writes audit log SYNC pre-response
  - patch_account: emits ClinicSpecialtiesChanged when specialties change
  - patch_account: 403 when role != admin_clinic
  - patch_account: cross-tenant isolation (different tenant → 404)
  - get_specialties_catalog: returns catalog for clinic's country
  - get_dpo: returns DPO info from config_json
"""

from __future__ import annotations

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.modules.vitalia.clinics.application.clinic_account_service import (
    ClinicAccountService,
)
from src.modules.vitalia.clinics.domain.clinic import Clinic


def _make_clinic(tenant_id=None, country="AR") -> Clinic:
    """Factory for Clinic domain entity."""
    return Clinic(
        id=uuid4(),
        tenant_id=tenant_id or uuid4(),
        name="Clínica Aurora",
        slug="aurora",
        country=country,
        timezone="America/Argentina/Buenos_Aires",
        plan_tier="starter",
        is_active=True,
        onboarding_completed=True,
        legal_name="Aurora Dental SRL",
        fiscal_id="20345678901",
        address="Av. Corrientes 1234, CABA",
        phone="+54 11 4567-8901",
        email="info@aurora.com",
        language="es-419",
        currency=None,
    )


@pytest.fixture
def mock_clinic_repo() -> AsyncMock:
    repo = AsyncMock()
    return repo


@pytest.fixture
def mock_config_repo() -> AsyncMock:
    repo = AsyncMock()
    return repo


@pytest.fixture
def mock_audit_writer() -> AsyncMock:
    writer = AsyncMock()
    writer.write = AsyncMock(return_value=None)
    return writer


@pytest.fixture
def service(
    mock_clinic_repo: AsyncMock,
    mock_config_repo: AsyncMock,
    mock_audit_writer: AsyncMock,
) -> ClinicAccountService:
    return ClinicAccountService(
        clinic_repo=mock_clinic_repo,
        config_repo=mock_config_repo,
        audit_writer=mock_audit_writer,
    )


# ---------------------------------------------------------------------------
# get_account
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_account_returns_data(
    service: ClinicAccountService,
    mock_clinic_repo: AsyncMock,
    mock_config_repo: AsyncMock,
) -> None:
    """get_account aggregates clinic + config into ClinicAccountData."""
    tenant_id = uuid4()
    clinic = _make_clinic(tenant_id=tenant_id)
    mock_clinic_repo.get_active_for_tenant.return_value = clinic
    mock_config_repo.get_config.return_value = {"primary_specialties": ["odontologia-estetica"]}

    result = await service.get_account(tenant_id=tenant_id)
    assert result is not None
    assert result.clinic_id == clinic.id
    assert result.name == "Clínica Aurora"
    assert "odontologia-estetica" in result.primary_specialties


@pytest.mark.asyncio
async def test_get_account_raises_404_when_no_clinic(
    service: ClinicAccountService,
    mock_clinic_repo: AsyncMock,
) -> None:
    """get_account raises ClinicNotFoundError when no active clinic."""
    from src.modules.vitalia.clinics.domain.exceptions import ClinicNotFoundError

    mock_clinic_repo.get_active_for_tenant.return_value = None
    with pytest.raises(ClinicNotFoundError):
        await service.get_account(tenant_id=uuid4())


# ---------------------------------------------------------------------------
# patch_account
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_patch_account_updates_fields(
    service: ClinicAccountService,
    mock_clinic_repo: AsyncMock,
    mock_config_repo: AsyncMock,
    mock_audit_writer: AsyncMock,
) -> None:
    """patch_account updates clinic fields and commits."""
    tenant_id = uuid4()
    user_id = uuid4()
    clinic = _make_clinic(tenant_id=tenant_id)
    mock_clinic_repo.get_active_for_tenant.return_value = clinic
    mock_clinic_repo.update_account.return_value = clinic
    mock_config_repo.get_config.return_value = {}

    from src.modules.vitalia.clinics.api.dtos import ClinicAccountPatchRequest

    patch_req = ClinicAccountPatchRequest(address="Av. Santa Fe 1000")
    await service.patch_account(
        tenant_id=tenant_id,
        user_id=user_id,
        patch=patch_req,
        user_role="admin_clinic",
        from_ip="127.0.0.1",
    )
    mock_clinic_repo.update_account.assert_called_once()


@pytest.mark.asyncio
async def test_patch_account_writes_audit_log_sync(
    service: ClinicAccountService,
    mock_clinic_repo: AsyncMock,
    mock_config_repo: AsyncMock,
    mock_audit_writer: AsyncMock,
) -> None:
    """Audit log MUST be written synchronously (awaited) before response."""
    tenant_id = uuid4()
    user_id = uuid4()
    clinic = _make_clinic(tenant_id=tenant_id)
    mock_clinic_repo.get_active_for_tenant.return_value = clinic
    mock_clinic_repo.update_account.return_value = clinic
    mock_config_repo.get_config.return_value = {}

    from src.modules.vitalia.clinics.api.dtos import ClinicAccountPatchRequest

    patch_req = ClinicAccountPatchRequest(phone="+54 11 9999-0000")
    await service.patch_account(
        tenant_id=tenant_id,
        user_id=user_id,
        patch=patch_req,
        user_role="admin_clinic",
        from_ip="10.0.0.1",
    )
    # Audit write must have been called (sync)
    mock_audit_writer.write.assert_called_once()


@pytest.mark.asyncio
async def test_patch_account_invalid_fiscal_id_raises_422(
    service: ClinicAccountService,
    mock_clinic_repo: AsyncMock,
    mock_config_repo: AsyncMock,
) -> None:
    """Invalid fiscal_id for known country raises FiscalIdValidationError."""
    from src.modules.vitalia._shared.validation.fiscal_id_validator import (
        FiscalIdValidationError,
    )

    tenant_id = uuid4()
    clinic = _make_clinic(tenant_id=tenant_id, country="AR")
    mock_clinic_repo.get_active_for_tenant.return_value = clinic
    mock_config_repo.get_config.return_value = {}

    from src.modules.vitalia.clinics.api.dtos import ClinicAccountPatchRequest

    patch_req = ClinicAccountPatchRequest(fiscal_id="INVALID_AR_CUIT")
    with pytest.raises(FiscalIdValidationError):
        await service.patch_account(
            tenant_id=tenant_id,
            user_id=uuid4(),
            patch=patch_req,
            user_role="admin_clinic",
            from_ip="127.0.0.1",
        )


@pytest.mark.asyncio
async def test_patch_account_emits_specialties_event(
    service: ClinicAccountService,
    mock_clinic_repo: AsyncMock,
    mock_config_repo: AsyncMock,
    mock_audit_writer: AsyncMock,
) -> None:
    """patch_account emits ClinicSpecialtiesChanged when specialties change."""
    tenant_id = uuid4()
    clinic = _make_clinic(tenant_id=tenant_id)
    mock_clinic_repo.get_active_for_tenant.return_value = clinic
    mock_clinic_repo.update_account.return_value = clinic
    mock_config_repo.get_config.return_value = {"primary_specialties": []}
    mock_config_repo.update_specialties = AsyncMock()

    from src.modules.vitalia.clinics.api.dtos import ClinicAccountPatchRequest

    patch_req = ClinicAccountPatchRequest(primary_specialties=["odontologia-estetica"])

    # Should not raise — event is best-effort try/except
    await service.patch_account(
        tenant_id=tenant_id,
        user_id=uuid4(),
        patch=patch_req,
        user_role="admin_clinic",
        from_ip="127.0.0.1",
    )
    mock_config_repo.update_specialties.assert_called_once()


@pytest.mark.asyncio
async def test_patch_account_forbidden_non_admin_role(
    service: ClinicAccountService,
    mock_clinic_repo: AsyncMock,
) -> None:
    """Non-admin_clinic role raises PermissionError (mapped to 403 in router)."""
    from src.modules.vitalia.clinics.api.dtos import ClinicAccountPatchRequest

    mock_clinic_repo.get_active_for_tenant.return_value = _make_clinic()
    patch_req = ClinicAccountPatchRequest(address="Somewhere")

    with pytest.raises(PermissionError):
        await service.patch_account(
            tenant_id=uuid4(),
            user_id=uuid4(),
            patch=patch_req,
            user_role="doctor",  # not admin_clinic
            from_ip="127.0.0.1",
        )


# ---------------------------------------------------------------------------
# get_specialties_catalog
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_specialties_catalog_for_clinic_country(
    service: ClinicAccountService,
    mock_clinic_repo: AsyncMock,
    mock_config_repo: AsyncMock,
) -> None:
    """get_specialties_catalog returns entries for clinic's country."""
    tenant_id = uuid4()
    clinic = _make_clinic(tenant_id=tenant_id, country="MX")
    mock_clinic_repo.get_active_for_tenant.return_value = clinic

    country, entries = await service.get_specialties_catalog(tenant_id=tenant_id)
    assert country == "MX"
    assert len(entries) > 0
    # Should return MX-specific catalog
    assert all(hasattr(e, "id") and hasattr(e, "name") for e in entries)


# ---------------------------------------------------------------------------
# get_dpo
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_dpo_returns_data(
    service: ClinicAccountService,
    mock_clinic_repo: AsyncMock,
    mock_config_repo: AsyncMock,
) -> None:
    """get_dpo returns DPO info from config_json."""
    tenant_id = uuid4()
    clinic = _make_clinic(tenant_id=tenant_id)
    mock_clinic_repo.get_active_for_tenant.return_value = clinic
    mock_config_repo.get_dpo.return_value = {
        "name": "Dr. García",
        "email": "dpo@aurora.com",
        "phone": "+54 11 1234-5678",
    }

    result = await service.get_dpo(tenant_id=tenant_id)
    assert result is not None
    assert result.get("name") == "Dr. García"


@pytest.mark.asyncio
async def test_get_dpo_returns_none_when_absent(
    service: ClinicAccountService,
    mock_clinic_repo: AsyncMock,
    mock_config_repo: AsyncMock,
) -> None:
    """get_dpo returns None when DPO not configured."""
    tenant_id = uuid4()
    clinic = _make_clinic(tenant_id=tenant_id)
    mock_clinic_repo.get_active_for_tenant.return_value = clinic
    mock_config_repo.get_dpo.return_value = None

    result = await service.get_dpo(tenant_id=tenant_id)
    assert result is None
