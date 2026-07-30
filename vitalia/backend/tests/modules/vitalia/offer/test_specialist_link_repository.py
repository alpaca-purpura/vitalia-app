"""Repo tests for ServiceSpecialistLinkRepository (real DB).

- link + list_by_offer round-trip
- list_by_offer is tenant-scoped (RN-12)
- unlink soft-deletes (excluded from list) and lets a re-link succeed
  (unique partial index only covers WHERE deleted_at IS NULL)
"""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.vitalia.offer.domain.specialist_link import ServiceSpecialistLink
from src.modules.vitalia.offer.infrastructure.repositories.specialist_link_repository import (
    ServiceSpecialistLinkRepository,
)

pytestmark = pytest.mark.integration


async def _seed_tenant(session: AsyncSession) -> UUID:
    tid = uuid4()
    await session.execute(
        text("INSERT INTO tenants (id, name, slug) VALUES (:id, :name, :slug)"),
        {"id": tid, "name": "Clínica Test", "slug": f"test-{tid.hex[:12]}"},
    )
    return tid


async def _seed_doctor(session: AsyncSession, tenant_id: UUID) -> UUID:
    did = uuid4()
    await session.execute(
        text(
            "INSERT INTO vitalia_doctors "
            "(id, tenant_id, clinic_id, first_name, last_name, credential_country) "
            "VALUES (:id, :tid, :cid, :fn, :ln, :cc)"
        ),
        {"id": did, "tid": tenant_id, "cid": uuid4(), "fn": "Ana", "ln": "Pérez", "cc": "PE"},
    )
    return did


async def test_link_and_list_by_offer(db_session: AsyncSession) -> None:
    tenant_id = await _seed_tenant(db_session)
    doctor_id = await _seed_doctor(db_session, tenant_id)
    offer_id = uuid4()
    repo = ServiceSpecialistLinkRepository(db_session)

    await repo.link(ServiceSpecialistLink(tenant_id=tenant_id, offer_id=offer_id, doctor_id=doctor_id))

    links = await repo.list_by_offer(offer_id, tenant_id=tenant_id)
    assert [link.doctor_id for link in links] == [doctor_id]


async def test_list_by_offer_cross_tenant_empty(db_session: AsyncSession) -> None:
    tenant_a = await _seed_tenant(db_session)
    other_tenant = await _seed_tenant(db_session)
    doctor_id = await _seed_doctor(db_session, tenant_a)
    offer_id = uuid4()
    repo = ServiceSpecialistLinkRepository(db_session)
    await repo.link(ServiceSpecialistLink(tenant_id=tenant_a, offer_id=offer_id, doctor_id=doctor_id))

    # RN-12 — another tenant sees no links
    assert await repo.list_by_offer(offer_id, tenant_id=other_tenant) == []


async def test_unlink_soft_deletes_and_allows_relink(db_session: AsyncSession) -> None:
    tenant_id = await _seed_tenant(db_session)
    doctor_id = await _seed_doctor(db_session, tenant_id)
    offer_id = uuid4()
    repo = ServiceSpecialistLinkRepository(db_session)
    await repo.link(ServiceSpecialistLink(tenant_id=tenant_id, offer_id=offer_id, doctor_id=doctor_id))

    await repo.unlink(offer_id, doctor_id, tenant_id=tenant_id)
    assert await repo.list_by_offer(offer_id, tenant_id=tenant_id) == []

    # unique partial index only covers live rows → re-link must succeed
    await repo.link(ServiceSpecialistLink(tenant_id=tenant_id, offer_id=offer_id, doctor_id=doctor_id))
    assert len(await repo.list_by_offer(offer_id, tenant_id=tenant_id)) == 1
