"""Repo tests for OfferServiceExtRepository (TDD RED → GREEN · real DB).

Validates the REAL tenant-filter SQL (per learning mocked-service-tests-hide-repo-contract):
- create + get_by_id round-trip (VO bundles survive JSONB)
- get_by_id is tenant-scoped → wrong tenant returns None (RN-12)
- soft_delete excludes the row from get/list (soft delete only)
- get_by_offer round-trip
NOT PHI (RN-13) → plain AsyncSession, no clinic dual filter.
"""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.vitalia.offer.domain.enums import (
    InitialApptType,
    IntervalUnit,
    PriceMode,
    ServiceModality,
)
from src.modules.vitalia.offer.domain.offer_ext import OfferExt
from src.modules.vitalia.offer.domain.vos import ServiceVariant, ThreeChargePricing, ValueWithUnit
from src.modules.vitalia.offer.infrastructure.repositories.offer_ext_repository import OfferServiceExtRepository

pytestmark = pytest.mark.integration


async def _seed_tenant(session: AsyncSession) -> UUID:
    tid = uuid4()
    await session.execute(
        text("INSERT INTO tenants (id, name, slug) VALUES (:id, :name, :slug)"),
        {"id": tid, "name": "Clínica Test", "slug": f"test-{tid.hex[:12]}"},
    )
    return tid


def _make_ext(tenant_id: UUID, offer_id: UUID) -> OfferExt:
    return OfferExt(
        tenant_id=tenant_id,
        offer_id=offer_id,
        modality=ServiceModality.SESIONES,
        description_long="Tratamiento facial con resultados graduales.",
        variants=[ServiceVariant(name="Zona frente", price=Decimal("1500"))],
        session_interval=ValueWithUnit(value=2, unit=IntervalUnit.SEMANAS),
        initial_appt_duration_minutes=30,
        initial_appt_type=InitialApptType.VALORACION_DIAGNOSTICO,
        pricing=ThreeChargePricing(
            price=Decimal("4500"),
            price_mode=PriceMode.FIJO,
            price_publishable=True,
            currency="PEN",
            reservation=None,
            advance=None,
            financing=None,
        ),
    )


async def test_create_and_get_by_id_round_trip(db_session: AsyncSession) -> None:
    tenant_id = await _seed_tenant(db_session)
    repo = OfferServiceExtRepository(db_session)
    ext = _make_ext(tenant_id, uuid4())

    created = await repo.create(ext)
    fetched = await repo.get_by_id(created.id, tenant_id=tenant_id)

    assert fetched is not None
    assert fetched.modality is ServiceModality.SESIONES
    assert fetched.description_long == "Tratamiento facial con resultados graduales."
    assert fetched.variants[0].name == "Zona frente"
    assert fetched.variants[0].price == Decimal("1500")
    assert fetched.session_interval == ValueWithUnit(value=2, unit=IntervalUnit.SEMANAS)
    assert fetched.pricing is not None
    assert fetched.pricing.price == Decimal("4500")
    assert fetched.pricing.currency == "PEN"
    assert fetched.initial_appt_type is InitialApptType.VALORACION_DIAGNOSTICO


async def test_get_by_id_cross_tenant_returns_none(db_session: AsyncSession) -> None:
    tenant_a = await _seed_tenant(db_session)
    other_tenant = await _seed_tenant(db_session)
    repo = OfferServiceExtRepository(db_session)
    created = await repo.create(_make_ext(tenant_a, uuid4()))

    # RN-12 — querying with another tenant's id must not leak the row
    leaked = await repo.get_by_id(created.id, tenant_id=other_tenant)
    assert leaked is None


async def test_soft_delete_excludes_from_get_and_list(db_session: AsyncSession) -> None:
    tenant_id = await _seed_tenant(db_session)
    repo = OfferServiceExtRepository(db_session)
    created = await repo.create(_make_ext(tenant_id, uuid4()))

    await repo.soft_delete(created.id, tenant_id=tenant_id)

    assert await repo.get_by_id(created.id, tenant_id=tenant_id) is None
    # list_by_tenant returns (rows, next_cursor) since T-2 (RN-15 keyset pagination).
    rows, _ = await repo.list_by_tenant(tenant_id=tenant_id)
    assert created.id not in {e.id for e in rows}


async def test_get_by_offer_round_trip(db_session: AsyncSession) -> None:
    tenant_id = await _seed_tenant(db_session)
    offer_id = uuid4()
    repo = OfferServiceExtRepository(db_session)
    await repo.create(_make_ext(tenant_id, offer_id))

    fetched = await repo.get_by_offer(offer_id, tenant_id=tenant_id)
    assert fetched is not None
    assert fetched.offer_id == offer_id
