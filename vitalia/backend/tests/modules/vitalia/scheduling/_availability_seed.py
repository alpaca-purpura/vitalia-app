# cap: scheduling.mateo-agenda
"""Shared real-DB seed helpers for availability service-day tests (T-D1).

Not a test module (no `test_` prefix → pytest does not collect it).
Synthetic data only — no real PHI (patient_id is a random UUID, never a name).

Reused by:
  - test_service_day_strips_realdb.py  (repo seam)
  - test_service_day_router_phi.py     (router seam)
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def insert_doctor(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    clinic_id: UUID,
    first_name: str,
    last_name: str,
) -> UUID:
    """Insert a minimal vitalia_doctors row, return its id."""
    doctor_id = uuid4()
    await session.execute(
        text(
            """
            INSERT INTO vitalia_doctors
                (id, tenant_id, clinic_id, first_name, last_name,
                 credential_country, languages, active, visible_en_landing, created_at)
            VALUES
                (:id, :tenant_id, :clinic_id, :first_name, :last_name,
                 'MX', '[]'::jsonb, true, false, NOW())
            """
        ),
        {
            "id": doctor_id,
            "tenant_id": tenant_id,
            "clinic_id": clinic_id,
            "first_name": first_name,
            "last_name": last_name,
        },
    )
    await session.flush()
    return doctor_id


async def insert_slot(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    clinic_id: UUID,
    doctor_id: UUID,
    slot_date: date,
    start_hour: int = 9,
    end_hour: int = 17,
) -> None:
    """Insert one working-hours slot (vitalia_availability_slots)."""
    start_ts = datetime(slot_date.year, slot_date.month, slot_date.day, start_hour, 0, tzinfo=timezone.utc)
    end_ts = start_ts.replace(hour=end_hour)
    await session.execute(
        text(
            """
            INSERT INTO vitalia_availability_slots
                (id, tenant_id, clinic_id, doctor_id, slot_date,
                 start_ts, end_ts, has_confirmed_appointment, created_at)
            VALUES
                (:id, :tenant_id, :clinic_id, :doctor_id, :slot_date,
                 :start_ts, :end_ts, false, NOW())
            """
        ),
        {
            "id": uuid4(),
            "tenant_id": tenant_id,
            "clinic_id": clinic_id,
            "doctor_id": doctor_id,
            "slot_date": slot_date,
            "start_ts": start_ts,
            "end_ts": end_ts,
        },
    )
    await session.flush()


async def ensure_tenant(session: AsyncSession, tenant_id: UUID) -> None:
    """Idempotently seed a tenants row (offer_service_specialist_links FK requires it)."""
    await session.execute(
        text("INSERT INTO tenants (id, name, slug) VALUES (:id, :name, :slug) ON CONFLICT (id) DO NOTHING"),
        {"id": tenant_id, "name": "Clínica Test", "slug": f"svc-day-{tenant_id.hex[:12]}"},
    )
    await session.flush()


async def insert_link(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    offer_id: UUID,
    doctor_id: UUID,
) -> None:
    """Link an offer (service) to a specialist doctor (offer_service_specialist_links)."""
    await ensure_tenant(session, tenant_id)
    await session.execute(
        text(
            """
            INSERT INTO offer_service_specialist_links
                (id, tenant_id, offer_id, doctor_id, created_at)
            VALUES
                (:id, :tenant_id, :offer_id, :doctor_id, NOW())
            """
        ),
        {"id": uuid4(), "tenant_id": tenant_id, "offer_id": offer_id, "doctor_id": doctor_id},
    )
    await session.flush()


async def insert_busy(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    clinic_id: UUID,
    doctor_id: UUID,
    day: date,
    start_hour: int,
    end_hour: int,
    status: str = "CONFIRMED",
) -> None:
    """Insert a booked appointment (vitalia_appointment_clinic_map mirror cols).

    status='CANCELLED' is used to assert RN-6 exclusion.
    """
    start_time = datetime(day.year, day.month, day.day, start_hour, 0, tzinfo=timezone.utc)
    end_time = start_time.replace(hour=end_hour)
    appointment_id = uuid4()
    patient_id = uuid4()  # synthetic — never a real patient
    dur = int((end_time - start_time).total_seconds() // 60) or 30
    # FK parent: vitalia_appointment_clinic_map.appointment_id → vitalia_appointments(id).
    await session.execute(
        text(
            """
            INSERT INTO vitalia_appointments
                (id, tenant_id, clinic_id, offer_id, patient_id, doctor_id,
                 slot_iso, duration_minutes, status, origin, notes_internal,
                 currency, created_at)
            VALUES
                (:id, :tenant_id, :clinic_id, :offer_id, :patient_id, :doctor_id,
                 :slot_iso, :dur, :status, 'walk_in', NULL, 'USD', NOW())
            """
        ),
        {
            "id": appointment_id,
            "tenant_id": tenant_id,
            "clinic_id": clinic_id,
            "offer_id": uuid4(),
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "slot_iso": start_time,
            "dur": dur,
            "status": status,
        },
    )
    await session.flush()
    await session.execute(
        text(
            """
            INSERT INTO vitalia_appointment_clinic_map
                (appointment_id, tenant_id, clinic_id, patient_id, doctor_id,
                 service_label, origin, start_time, end_time, status, created_at)
            VALUES
                (:aid, :tenant_id, :clinic_id, :patient_id, :doctor_id,
                 'Consulta', 'walk_in', :start_time, :end_time, :status, NOW())
            """
        ),
        {
            "aid": appointment_id,
            "tenant_id": tenant_id,
            "clinic_id": clinic_id,
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "start_time": start_time,
            "end_time": end_time,
            "status": status,
        },
    )
    await session.flush()
