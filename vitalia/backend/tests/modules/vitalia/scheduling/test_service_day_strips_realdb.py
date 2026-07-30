# cap: scheduling.mateo-agenda
"""Repo seam (real DB) for get_service_day_strips — T-D1 delta mateo nueva-cita.

Seam = integration-realdb (mock-only does NOT count). Auto-skips if Postgres down.

Covers:
  - service WITH links → only linked doctors (clinic-active) appear
  - service WITHOUT links → fallback to all clinic-active doctors
  - service/clinic with no doctors → []
  - doctor with no working hours → blocks come back empty (working=[], busy=[])
  - busy excludes CANCELLED (RN-6)
  - cross-clinic doctor excluded (dual filter, no leak)
  - cross-tenant doctor excluded (no leak)
"""

from __future__ import annotations

from datetime import date
from uuid import uuid4

import pytest

from src.modules.vitalia.scheduling.infrastructure.repositories.availability_query_repository import (
    AvailabilityQueryRepository,
)

from ._availability_seed import insert_busy, insert_doctor, insert_link, insert_slot

TENANT_A = uuid4()
TENANT_B = uuid4()
CLINIC_A = uuid4()
CLINIC_B = uuid4()
DAY = date(2026, 7, 1)


@pytest.mark.integration
class TestGetServiceDayStrips:
    async def test_service_with_links_returns_only_linked_active_doctors(self, db_session) -> None:
        offer_id = uuid4()
        linked = await insert_doctor(
            db_session, tenant_id=TENANT_A, clinic_id=CLINIC_A, first_name="Ana", last_name="Linked"
        )
        unlinked = await insert_doctor(
            db_session, tenant_id=TENANT_A, clinic_id=CLINIC_A, first_name="Beto", last_name="Unlinked"
        )
        await insert_slot(db_session, tenant_id=TENANT_A, clinic_id=CLINIC_A, doctor_id=linked, slot_date=DAY)
        await insert_slot(db_session, tenant_id=TENANT_A, clinic_id=CLINIC_A, doctor_id=unlinked, slot_date=DAY)
        await insert_link(db_session, tenant_id=TENANT_A, offer_id=offer_id, doctor_id=linked)

        repo = AvailabilityQueryRepository(session=db_session)
        rows = await repo.get_service_day_strips(tenant_id=TENANT_A, clinic_id=CLINIC_A, offer_id=offer_id, day=DAY)

        ids = {r[0] for r in rows}
        assert linked in ids
        assert unlinked not in ids

    async def test_service_without_links_falls_back_to_all_clinic_doctors(self, db_session) -> None:
        offer_id = uuid4()  # never linked
        d1 = await insert_doctor(db_session, tenant_id=TENANT_A, clinic_id=CLINIC_A, first_name="Caro", last_name="One")
        d2 = await insert_doctor(db_session, tenant_id=TENANT_A, clinic_id=CLINIC_A, first_name="Dora", last_name="Two")
        await insert_slot(db_session, tenant_id=TENANT_A, clinic_id=CLINIC_A, doctor_id=d1, slot_date=DAY)
        await insert_slot(db_session, tenant_id=TENANT_A, clinic_id=CLINIC_A, doctor_id=d2, slot_date=DAY)

        repo = AvailabilityQueryRepository(session=db_session)
        rows = await repo.get_service_day_strips(tenant_id=TENANT_A, clinic_id=CLINIC_A, offer_id=offer_id, day=DAY)

        ids = {r[0] for r in rows}
        assert {d1, d2} <= ids

    async def test_clinic_with_no_doctors_returns_empty(self, db_session) -> None:
        repo = AvailabilityQueryRepository(session=db_session)
        rows = await repo.get_service_day_strips(tenant_id=TENANT_A, clinic_id=uuid4(), offer_id=uuid4(), day=DAY)
        assert rows == []

    async def test_doctor_without_working_hours_has_empty_strips(self, db_session) -> None:
        offer_id = uuid4()
        doc = await insert_doctor(
            db_session, tenant_id=TENANT_A, clinic_id=CLINIC_A, first_name="Eva", last_name="NoHours"
        )
        # slot present (so doctor is clinic-active) but on a DIFFERENT day → no working hours for DAY
        await insert_slot(db_session, tenant_id=TENANT_A, clinic_id=CLINIC_A, doctor_id=doc, slot_date=date(2026, 7, 2))
        await insert_link(db_session, tenant_id=TENANT_A, offer_id=offer_id, doctor_id=doc)

        repo = AvailabilityQueryRepository(session=db_session)
        rows = await repo.get_service_day_strips(tenant_id=TENANT_A, clinic_id=CLINIC_A, offer_id=offer_id, day=DAY)

        mine = [r for r in rows if r[0] == doc]
        assert len(mine) == 1
        _, _, working, busy = mine[0]
        assert working == []
        assert busy == []

    async def test_busy_excludes_cancelled_rn6(self, db_session) -> None:
        offer_id = uuid4()
        doc = await insert_doctor(
            db_session, tenant_id=TENANT_A, clinic_id=CLINIC_A, first_name="Fito", last_name="Busy"
        )
        await insert_slot(db_session, tenant_id=TENANT_A, clinic_id=CLINIC_A, doctor_id=doc, slot_date=DAY)
        await insert_link(db_session, tenant_id=TENANT_A, offer_id=offer_id, doctor_id=doc)
        await insert_busy(
            db_session,
            tenant_id=TENANT_A,
            clinic_id=CLINIC_A,
            doctor_id=doc,
            day=DAY,
            start_hour=10,
            end_hour=11,
            status="CONFIRMED",
        )
        await insert_busy(
            db_session,
            tenant_id=TENANT_A,
            clinic_id=CLINIC_A,
            doctor_id=doc,
            day=DAY,
            start_hour=12,
            end_hour=13,
            status="CANCELLED",
        )

        repo = AvailabilityQueryRepository(session=db_session)
        rows = await repo.get_service_day_strips(tenant_id=TENANT_A, clinic_id=CLINIC_A, offer_id=offer_id, day=DAY)

        _, _, _working, busy = next(r for r in rows if r[0] == doc)
        busy_starts = {b.start.hour for b in busy}
        assert 10 in busy_starts  # CONFIRMED kept
        assert 12 not in busy_starts  # CANCELLED dropped (RN-6)

    async def test_cross_clinic_doctor_excluded(self, db_session) -> None:
        offer_id = uuid4()
        # doctor lives in CLINIC_B but is linked to the service → must NOT leak into CLINIC_A
        other = await insert_doctor(
            db_session, tenant_id=TENANT_A, clinic_id=CLINIC_B, first_name="Gus", last_name="OtherClinic"
        )
        await insert_slot(db_session, tenant_id=TENANT_A, clinic_id=CLINIC_B, doctor_id=other, slot_date=DAY)
        await insert_link(db_session, tenant_id=TENANT_A, offer_id=offer_id, doctor_id=other)

        repo = AvailabilityQueryRepository(session=db_session)
        rows = await repo.get_service_day_strips(tenant_id=TENANT_A, clinic_id=CLINIC_A, offer_id=offer_id, day=DAY)
        assert other not in {r[0] for r in rows}

    async def test_cross_tenant_doctor_excluded(self, db_session) -> None:
        offer_id = uuid4()
        foreign = await insert_doctor(
            db_session, tenant_id=TENANT_B, clinic_id=CLINIC_A, first_name="Hugo", last_name="OtherTenant"
        )
        await insert_slot(db_session, tenant_id=TENANT_B, clinic_id=CLINIC_A, doctor_id=foreign, slot_date=DAY)
        await insert_link(db_session, tenant_id=TENANT_B, offer_id=offer_id, doctor_id=foreign)

        repo = AvailabilityQueryRepository(session=db_session)
        rows = await repo.get_service_day_strips(tenant_id=TENANT_A, clinic_id=CLINIC_A, offer_id=offer_id, day=DAY)
        assert foreign not in {r[0] for r in rows}
