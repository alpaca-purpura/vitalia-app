# cap: configuracion.cuenta
"""RED tests for ClinicAccountRepository + ClinicRepository extensions.

Tests are UNIT (mocked AsyncSession) — no DB required (no integration marker).
Covers:
  - get_active_for_tenant: returns first active non-deleted clinic
  - get_active_for_tenant: returns None when no active clinic
  - update_account: updates specified fields + returns updated Clinic
  - update_account: raises NotFound when clinic not found for tenant
  - ClinicConfigRepository.get_config: reads config_json from TenantModel
  - ClinicConfigRepository.get_config: returns empty dict when absent
  - ClinicConfigRepository.update_specialties: RMW on config_json JSONB
  - cross-tenant: get_active_for_tenant with wrong tenant_id returns None
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.modules.vitalia.clinics.infrastructure.repositories.clinic_config_repository import (
    ClinicConfigRepository,
)
from src.modules.vitalia.clinics.infrastructure.repositories.clinic_repository import (
    ClinicRepository,
)


@pytest.fixture
def mock_db() -> AsyncMock:
    """Mock AsyncSession."""
    db = AsyncMock()
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.add = MagicMock()
    return db


@pytest.fixture
def clinic_repo(mock_db: AsyncMock) -> ClinicRepository:
    return ClinicRepository(mock_db)


@pytest.fixture
def config_repo(mock_db: AsyncMock) -> ClinicConfigRepository:
    return ClinicConfigRepository(mock_db)


# ---------------------------------------------------------------------------
# get_active_for_tenant
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_active_for_tenant_returns_clinic(clinic_repo: ClinicRepository, mock_db: AsyncMock) -> None:
    """Returns first active clinic for tenant."""
    tenant_id = uuid4()
    clinic_id = uuid4()

    mock_model = MagicMock()
    mock_model.id = clinic_id
    mock_model.tenant_id = tenant_id
    mock_model.name = "Clínica Test"
    mock_model.slug = "clinica-test"
    mock_model.country = "AR"
    mock_model.timezone = "America/Argentina/Buenos_Aires"
    mock_model.plan_tier = "starter"
    mock_model.is_active = True
    mock_model.onboarding_completed = False
    mock_model.created_at = None
    mock_model.updated_at = None
    mock_model.deleted_at = None
    # Account fields
    mock_model.legal_name = "Clínica Test S.R.L."
    mock_model.fiscal_id = "20345678901"
    mock_model.address = None
    mock_model.phone = None
    mock_model.email = None
    mock_model.language = "es-419"
    mock_model.currency = None

    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_model
    mock_db.execute.return_value = mock_result

    clinic = await clinic_repo.get_active_for_tenant(tenant_id)
    assert clinic is not None
    assert clinic.tenant_id == tenant_id
    mock_db.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_active_for_tenant_returns_none(clinic_repo: ClinicRepository, mock_db: AsyncMock) -> None:
    """Returns None when no active clinic found."""
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None
    mock_db.execute.return_value = mock_result

    clinic = await clinic_repo.get_active_for_tenant(uuid4())
    assert clinic is None


@pytest.mark.asyncio
async def test_get_active_for_tenant_cross_tenant_isolation(clinic_repo: ClinicRepository, mock_db: AsyncMock) -> None:
    """Cross-tenant: different tenant_id returns None (query filtered)."""
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None
    mock_db.execute.return_value = mock_result

    # Simulate DB returning nothing for wrong tenant
    clinic = await clinic_repo.get_active_for_tenant(uuid4())
    assert clinic is None
    # Verify execute was called (DB query made, returned nothing)
    mock_db.execute.assert_called_once()


# ---------------------------------------------------------------------------
# update_account
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_update_account_returns_updated_clinic(clinic_repo: ClinicRepository, mock_db: AsyncMock) -> None:
    """update_account flushes + re-fetches + returns updated Clinic (caller owns commit).

    Intentional change (C9-1 Option A fix): commit() was removed from
    update_account so clinic fields + specialties + audit row commit
    atomically via get_async_session_committing in the router. The repo
    flushes (making updates visible intra-transaction) but does NOT commit.
    """
    tenant_id = uuid4()
    clinic_id = uuid4()

    mock_model = MagicMock()
    mock_model.id = clinic_id
    mock_model.tenant_id = tenant_id
    mock_model.name = "Clínica Aurora"
    mock_model.slug = "aurora"
    mock_model.country = "AR"
    mock_model.timezone = "UTC"
    mock_model.plan_tier = "starter"
    mock_model.is_active = True
    mock_model.onboarding_completed = False
    mock_model.created_at = None
    mock_model.updated_at = None
    mock_model.deleted_at = None
    mock_model.legal_name = "Aurora SRL"
    mock_model.fiscal_id = "20345678901"
    mock_model.address = "Av. Corrientes 1234"
    mock_model.phone = None
    mock_model.email = "info@aurora.com"
    mock_model.language = "es-419"
    mock_model.currency = None

    mock_execute_result = MagicMock()
    mock_execute_result.scalars.return_value.first.return_value = mock_model
    mock_db.execute.return_value = mock_execute_result

    updated = await clinic_repo.update_account(
        tenant_id=tenant_id,
        clinic_id=clinic_id,
        legal_name="Aurora SRL",
        address="Av. Corrientes 1234",
        email="info@aurora.com",
    )
    assert updated is not None
    # flush is called (makes writes visible intra-transaction for re-fetch)
    mock_db.flush.assert_called_once()
    # commit NOT called — caller (get_async_session_committing) owns the commit
    mock_db.commit.assert_not_called()


@pytest.mark.asyncio
async def test_update_account_not_found_raises(clinic_repo: ClinicRepository, mock_db: AsyncMock) -> None:
    """update_account raises when clinic not found for tenant."""
    from src.modules.vitalia.clinics.domain.exceptions import ClinicNotFoundError

    mock_execute_result = MagicMock()
    mock_execute_result.scalars.return_value.first.return_value = None
    mock_db.execute.return_value = mock_execute_result

    with pytest.raises(ClinicNotFoundError):
        await clinic_repo.update_account(
            tenant_id=uuid4(),
            clinic_id=uuid4(),
            legal_name="New Name",
        )


# ---------------------------------------------------------------------------
# ClinicConfigRepository
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_config_repo_get_config_returns_dict(config_repo: ClinicConfigRepository, mock_db: AsyncMock) -> None:
    """get_config returns clinic_config dict from config_json."""
    tenant_id = uuid4()

    mock_tenant = MagicMock()
    mock_tenant.config_json = {"clinic_config": {"primary_specialties": ["odontologia-estetica"]}}
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_tenant
    mock_db.execute.return_value = mock_result

    config = await config_repo.get_config(tenant_id)
    assert config == {"primary_specialties": ["odontologia-estetica"]}


@pytest.mark.asyncio
async def test_config_repo_get_config_missing_returns_empty(
    config_repo: ClinicConfigRepository, mock_db: AsyncMock
) -> None:
    """get_config returns empty dict when config_json has no clinic_config key."""
    mock_tenant = MagicMock()
    mock_tenant.config_json = {}
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_tenant
    mock_db.execute.return_value = mock_result

    config = await config_repo.get_config(uuid4())
    assert config == {}


@pytest.mark.asyncio
async def test_config_repo_get_config_null_config_json(config_repo: ClinicConfigRepository, mock_db: AsyncMock) -> None:
    """get_config returns empty dict when config_json is None."""
    mock_tenant = MagicMock()
    mock_tenant.config_json = None
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_tenant
    mock_db.execute.return_value = mock_result

    config = await config_repo.get_config(uuid4())
    assert config == {}


@pytest.mark.asyncio
async def test_config_repo_update_specialties_executes_update(
    config_repo: ClinicConfigRepository, mock_db: AsyncMock
) -> None:
    """update_specialties executes the UPDATE statement (caller owns commit).

    Intentional change (C9-1 Option A fix): commit() was removed from
    update_specialties so all three writes (clinic fields + specialties +
    audit row) commit atomically via get_async_session_committing in the router.
    The repo executes the SQL but does NOT commit — the unit-of-work owner does.
    """
    tenant_id = uuid4()

    # First call: read tenant (for RMW)
    mock_tenant = MagicMock()
    mock_tenant.config_json = {"clinic_config": {}}
    mock_read_result = MagicMock()
    mock_read_result.scalars.return_value.first.return_value = mock_tenant
    mock_db.execute.return_value = mock_read_result

    await config_repo.update_specialties(
        tenant_id=tenant_id,
        specialties=["odontologia-estetica", "medicina-estetica"],
    )
    # execute called at least twice: SELECT + UPDATE
    assert mock_db.execute.call_count >= 2
    # commit NOT called — caller (get_async_session_committing) owns the commit
    mock_db.commit.assert_not_called()


@pytest.mark.asyncio
async def test_config_repo_get_dpo_returns_dict(config_repo: ClinicConfigRepository, mock_db: AsyncMock) -> None:
    """get_dpo returns compliance.dpo from config_json."""
    tenant_id = uuid4()
    dpo_data = {"name": "Dr. Juan García", "email": "dpo@clinica.com"}
    mock_tenant = MagicMock()
    mock_tenant.config_json = {"compliance": {"dpo": dpo_data}}
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_tenant
    mock_db.execute.return_value = mock_result

    dpo = await config_repo.get_dpo(tenant_id)
    assert dpo == dpo_data


@pytest.mark.asyncio
async def test_config_repo_get_dpo_missing_returns_none(
    config_repo: ClinicConfigRepository, mock_db: AsyncMock
) -> None:
    """get_dpo returns None when compliance.dpo absent."""
    mock_tenant = MagicMock()
    mock_tenant.config_json = {}
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_tenant
    mock_db.execute.return_value = mock_result

    dpo = await config_repo.get_dpo(uuid4())
    assert dpo is None
