"""Repo tests for CaseRepository — PHI · HIPAA-lite dual filter + consent gate.

Validators RN-33 (consent gate) + dual filter (tenant + clinic):
- create with consent_signed=False → ConsentNotSignedError (RN-33)
- create without clinic_id → MissingClinicFilterError (dual filter)
- create + get_by_id round-trip with both filters
- get_by_id cross-clinic returns None (clinic dual filter blocks)
- get_by_id cross-tenant returns None (RN-12)
- CaseRepository inherits PhiRepositoryBase (contract)
"""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest
from luana_core_platform.repositories.compound_scope_repository import CompoundScopeRepositoryBase
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.vitalia._shared.repositories.phi_repository import MissingClinicFilterError
from src.modules.vitalia.offer.domain.proof import Case
from src.modules.vitalia.offer.infrastructure.repositories.case_repository import (
    CaseRepository,
    ConsentNotSignedError,
)

pytestmark = pytest.mark.integration


def test_case_repository_inherits_engine_compound_scope() -> None:
    """Contract: Case is PHI → repo MUST inherit engine CompoundScopeRepositoryBase.

    Post engine-lift (2026-05-20) new PHI repos use the lifted engine base, not the
    brand-local PhiRepositoryBase. Arch gate test_compound_scope_repository_used.py.
    """
    assert issubclass(CaseRepository, CompoundScopeRepositoryBase)


async def _seed_tenant(session: AsyncSession) -> UUID:
    tid = uuid4()
    await session.execute(
        text("INSERT INTO tenants (id, name, slug) VALUES (:id, :name, :slug)"),
        {"id": tid, "name": "Clínica Test", "slug": f"test-{tid.hex[:12]}"},
    )
    return tid


def _make_case(tenant_id: UUID, *, consent: bool) -> Case:
    return Case(
        tenant_id=tenant_id,
        offer_id=uuid4(),
        before_asset_url="https://assets.example.com/before.jpg",
        after_asset_url="https://assets.example.com/after.jpg",
        consent_signed=consent,
        consent_ref="CONSENT-001" if consent else None,
    )


async def test_create_without_consent_raises(db_session: AsyncSession) -> None:
    tenant_id = await _seed_tenant(db_session)
    repo = CaseRepository(db_session)

    # RN-33 — a Case without signed consent is NEVER persisted
    with pytest.raises(ConsentNotSignedError):
        await repo.create(_make_case(tenant_id, consent=False), clinic_id=uuid4())


async def test_create_without_clinic_raises(db_session: AsyncSession) -> None:
    tenant_id = await _seed_tenant(db_session)
    repo = CaseRepository(db_session)

    # dual filter — clinic_id mandatory for PHI
    with pytest.raises(MissingClinicFilterError):
        await repo.create(_make_case(tenant_id, consent=True), clinic_id=None)  # type: ignore[arg-type]


async def test_create_and_get_by_id_dual_filter(db_session: AsyncSession) -> None:
    tenant_id = await _seed_tenant(db_session)
    clinic_id = uuid4()
    repo = CaseRepository(db_session)

    created = await repo.create(_make_case(tenant_id, consent=True), clinic_id=clinic_id)
    fetched = await repo.get_by_id(created.id, tenant_id=tenant_id, clinic_id=clinic_id)

    assert fetched is not None
    assert fetched.consent_signed is True
    assert fetched.clinic_id == clinic_id


async def test_get_by_id_cross_clinic_returns_none(db_session: AsyncSession) -> None:
    tenant_id = await _seed_tenant(db_session)
    clinic_id = uuid4()
    other_clinic = uuid4()
    repo = CaseRepository(db_session)
    created = await repo.create(_make_case(tenant_id, consent=True), clinic_id=clinic_id)

    # dual filter — same tenant, wrong clinic → no PHI leak
    assert await repo.get_by_id(created.id, tenant_id=tenant_id, clinic_id=other_clinic) is None


async def test_get_by_id_cross_tenant_returns_none(db_session: AsyncSession) -> None:
    tenant_id = await _seed_tenant(db_session)
    other_tenant = await _seed_tenant(db_session)
    clinic_id = uuid4()
    repo = CaseRepository(db_session)
    created = await repo.create(_make_case(tenant_id, consent=True), clinic_id=clinic_id)

    # RN-12 — cross-tenant query returns None
    assert await repo.get_by_id(created.id, tenant_id=other_tenant, clinic_id=clinic_id) is None
