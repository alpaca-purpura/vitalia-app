# cap: scheduling.mateo-agenda
# story-origin: TBD
"""AgendaGridRepositoryImpl — SQLAlchemy 2.0 async implementation.

JOINs:
  vitalia_appointments (base)
  vitalia_appointment_clinic_map (service_label, origin, currency_override)
  vitalia_appointment_payments (balance aggregation)

PHI masking contract (HIPAA-lite, 03-arch § 2.2):
  patient_name_masked / dni_masked — projected as masked placeholders ('—').
  The patient name lives encrypted (bytea) in vitalia_patients; vitalia_appointments
  has no name column. FE NEVER receives raw PHI.

Dual filter: EVERY query WHERE tenant_id = :tenant_id AND clinic_id = :clinic_id
(bound params — never f-string interpolation).

Per 03-arch § 3.1 + vitalia/.claude/rules/hipaa-lite.md
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

import structlog
from luana_core_platform.repositories.compound_scope_repository import (
    CompoundScopeRepositoryBase,
)
from sqlalchemy import bindparam, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.vitalia._shared.encryption.kek_client import KEKClient
from src.modules.vitalia.scheduling.domain.agenda_filter import AgendaPresetFilter
from src.modules.vitalia.scheduling.infrastructure.repositories._phi_mask import (
    apply_name_mask as _apply_name_mask,
)
from src.modules.vitalia.scheduling.infrastructure.repositories._phi_mask import (
    mask_name as _mask_name,
)
from src.modules.vitalia.scheduling.persistence.models.appointment_clinic_map_model import (
    AppointmentClinicMapModel,
)

logger = structlog.get_logger()

__all__ = ["AgendaGridRepositoryImpl", "_apply_name_mask", "_mask_name"]

# ---------------------------------------------------------------------------
# Raw-SQL projection over vitalia_appointments (no ORM model — the table is
# created by migration 002_vitalia_appointments_columns.py without a Python
# Mapped class). The grid query JOINs the brand-local extension tables
# vitalia_appointment_clinic_map + vitalia_appointment_payments.
#
# SQLAlchemy 2.0 note (bug fix vitalia-bugfix-agenda-actor-headers-422 T-2):
#   the previous implementation used
#     select(...).select_from(text("vitalia_appointments va")).outerjoin(ORMModel, ...)
#   Mixing a text() FROM with ORM-model join targets routes compilation through the
#   ORM context (`_normalize_froms`), which reads `info.selectable` on every entry in
#   `_from_obj` — a TextClause has no `.selectable` → AttributeError at COMPILE time
#   (HTTP 500 before reaching the DB). It also interpolated UUIDs via f-strings
#   (SQL-injection surface). The fix below uses a single parameterized text() statement:
#   it compiles + executes, keeps the HIPAA-lite dual filter (tenant_id + clinic_id) as
#   bound params, and references only columns that exist in the real schema.
# ---------------------------------------------------------------------------

# Projection column list shared by list_slots + get_by_id (router-aligned aliases).
# PHI name/DNI are projected as masked placeholders: vitalia_appointments has no name
# column and the patient name lives encrypted (bytea) in vitalia_patients, so the grid
# never carries raw PHI. Real masked-name resolution from the encrypted source is an
# architect-level follow-up (see T-2 result § Upstream deficiency).
_GRID_PROJECTION = """
    va.id AS appointment_id,
    va.patient_id AS patient_id,
    -- raw decrypted name (masked in Python via _mask_name, never returned raw — D5)
    MAX(pgp_sym_decrypt(p.name, :kek)::text) AS raw_patient_name,
    '—' AS dni_masked,
    -- service name from the brand-local clinic_map extension (populated on create) (D4)
    COALESCE(map.service_label, 'Consulta') AS service_label,
    va.doctor_id AS doctor_id,
    -- doctor display name from vitalia_doctors (D3)
    MAX(COALESCE(NULLIF(TRIM(CONCAT(doc.first_name, ' ', doc.last_name)), ''), 'Sin asignar')) AS doctor_label,
    va.slot_iso AS start_time,
    va.slot_iso + (va.duration_minutes * INTERVAL '1 minute') AS end_time,
    va.status AS appointment_status,
    -- SlotPaymentStatus derived server-side (domain: pagado|deposito|sin_pago|no_show) — D2
    CASE
        WHEN va.status = 'NO_SHOW' THEN 'no_show'
        WHEN COALESCE(va.amount_pending, 0) <= 0 AND COALESCE(va.amount_paid, 0) > 0 THEN 'pagado'
        WHEN COALESCE(va.amount_paid, 0) > 0 THEN 'deposito'
        ELSE 'sin_pago'
    END AS payment_status,
    COALESCE(map.origin, va.origin) AS origin,
    -- real balances from the appointment ledger (cents) — D6
    ROUND(COALESCE(va.amount_pending, 0) * 100)::bigint AS balance_due_cents,
    ROUND(COALESCE(va.amount_paid, 0) * 100)::bigint AS balance_paid_cents,
    COALESCE(map.currency_override, va.currency) AS currency
"""

_GRID_FROM_JOINS = """
    FROM vitalia_appointments va
    LEFT OUTER JOIN vitalia_appointment_clinic_map map
        ON map.appointment_id = va.id AND map.deleted_at IS NULL
    LEFT OUTER JOIN vitalia_doctors doc
        ON doc.id = va.doctor_id AND doc.tenant_id = va.tenant_id AND doc.deleted_at IS NULL
    LEFT OUTER JOIN vitalia_patients p
        ON p.id = va.patient_id AND p.tenant_id = va.tenant_id AND p.deleted_at IS NULL
"""

_GRID_GROUP_BY = """
    GROUP BY va.id, va.slot_iso, va.duration_minutes, va.status,
             va.origin, va.doctor_id, va.patient_id,
             va.amount_paid, va.amount_pending, va.currency,
             map.service_label, map.origin, map.currency_override
"""

# Preset → appointment status filter mapping
_PRESET_STATUS_MAP: dict[str, str] = {
    AgendaPresetFilter.POR_CONFIRMAR_MANANA: "SCHEDULED",
    AgendaPresetFilter.REAGENDAR_PENDIENTES: "RESCHEDULED",
    AgendaPresetFilter.NO_SHOWS_DIA: "NO_SHOW",
}


class AgendaGridRepositoryImpl(CompoundScopeRepositoryBase):  # type: ignore[type-arg]
    """SQLA 2.0 async implementation of AgendaGridRepository.

    Inherits CompoundScopeRepositoryBase (engine) for HIPAA-lite dual-scope
    isolation contract (tenant_id + clinic_id on EVERY query).

    MODEL is set to None because this repo issues complex JOIN queries against
    vitalia_appointments (no Python SA model) + ORM joins. All query methods
    are fully overridden — the base class get_by_id/list_for_scope are never
    called. scope_field="clinic_id" per vitalia HIPAA-lite overlay.

    Query strategy (SQLA 2.0, bug fix T-2):
    - Single parameterized text() statement over vitalia_appointments + JOINs to the
      brand-local extension tables (clinic_map, payments).
    - Dual filter (tenant_id + clinic_id) bound as params on EVERY query.
    - PHI name/DNI projected as masked placeholders ('—') — vitalia_appointments has
      no name column and the patient name is encrypted (bytea) in vitalia_patients,
      so the grid never carries raw PHI. Real masked-name resolution from the
      encrypted source is an architect follow-up (T-2 § Upstream deficiency).
    """

    MODEL = None  # Complex JOIN repo — overrides all query methods, never calls super().get_by_id()

    def __init__(self, session: AsyncSession, kek: KEKClient | None = None) -> None:
        super().__init__(session=session, scope_field="clinic_id")
        # KEK for decrypting the patient name (masked server-side). Lazy: from_env() does
        # not read the env until get_key() is called (safe to construct without env).
        self._kek: KEKClient = kek if kek is not None else KEKClient.from_env()

    def _check_dual_filter(self, *, tenant_id: UUID, clinic_id: UUID | None) -> None:
        """Inline dual-filter guard (HIPAA-lite — tenant_id + clinic_id mandatory).

        Called at the top of every query method to enforce both filters.
        Raises if clinic_id is missing (cross-clinic leak risk).
        """
        if clinic_id is None:
            raise ValueError(
                "AgendaGridRepositoryImpl: clinic_id is required on all PHI queries "
                "(vitalia/.claude/rules/hipaa-lite.md § Tenant isolation refuerzo)"
            )

    async def get_by_id(
        self,
        entity_id: UUID,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
    ) -> dict[str, Any] | None:
        """Get single slot by appointment_id with dual filter.

        Parameterized text() statement (SQLA 2.0). Dual filter tenant_id + clinic_id
        bound as params (HIPAA-lite). Returns None if not found / cross-clinic.
        """
        self._check_dual_filter(tenant_id=tenant_id, clinic_id=clinic_id)

        stmt = text(
            f"SELECT {_GRID_PROJECTION}"  # noqa: S608 — static projection, no user input
            f"{_GRID_FROM_JOINS}"
            " WHERE va.tenant_id = :tenant_id"
            "   AND va.clinic_id = :clinic_id"
            "   AND va.id = :appointment_id"
            "   AND va.deleted_at IS NULL"
            f"{_GRID_GROUP_BY}"
        ).bindparams(
            bindparam("tenant_id", value=tenant_id),
            bindparam("clinic_id", value=clinic_id),
            bindparam("appointment_id", value=entity_id),
            bindparam("kek", value=self._kek.get_key()),
        )
        result = await self._session.execute(stmt)
        row = result.mappings().first()
        return _apply_name_mask(dict(row)) if row else None

    async def list_by_filter(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        **filters: object,
    ) -> list[dict[str, Any]]:
        """List slots using generic filter kwargs (delegates to list_slots)."""
        self._check_dual_filter(tenant_id=tenant_id, clinic_id=clinic_id)
        date_from = filters.get("date_from")
        date_to = filters.get("date_to")
        if not isinstance(date_from, datetime) or not isinstance(date_to, datetime):
            raise ValueError("list_by_filter requires date_from + date_to as datetime")
        return await self.list_slots(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            date_from=date_from,
            date_to=date_to,
            preset_filter=filters.get("preset_filter"),  # type: ignore[arg-type]
        )

    async def list_slots(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        date_from: datetime,
        date_to: datetime,
        preset_filter: AgendaPresetFilter | None = None,
        doctor_id: UUID | None = None,
        limit: int = 500,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """List appointment slots — PHI-masked projection with JOIN clinic_map + payments.

        Dual filter applied: tenant_id + clinic_id in every WHERE clause.
        patient_name_masked column expected from vitalia_appointments
        (set by AgendaSlotService before persisting or via trigger/view).
        """
        self._check_dual_filter(tenant_id=tenant_id, clinic_id=clinic_id)

        logger.debug(
            "agenda_grid_list_slots",
            tenant_id=str(tenant_id),
            clinic_id=str(clinic_id),
            date_from=date_from.isoformat(),
            date_to=date_to.isoformat(),
            preset_filter=str(preset_filter) if preset_filter else None,
        )

        # WHERE clauses + bound params (dual filter + date range — HIPAA-lite).
        where_sql = [
            "va.tenant_id = :tenant_id",
            "va.clinic_id = :clinic_id",
            "va.slot_iso >= :date_from",
            "va.slot_iso <= :date_to",
            "va.deleted_at IS NULL",
            # A cancelled appointment freed its slot — it is not an active turn on the agenda (D7).
            # The slot disappears from the grid; the detail endpoint still serves it by id.
            "va.status <> 'CANCELLED'",
        ]
        params: list[Any] = [
            bindparam("tenant_id", value=tenant_id),
            bindparam("clinic_id", value=clinic_id),
            bindparam("date_from", value=date_from),
            bindparam("date_to", value=date_to),
            bindparam("kek", value=self._kek.get_key()),  # decrypt patient name (D5)
        ]

        # Preset filter → additional status conditions (static SQL — no user input).
        if preset_filter == AgendaPresetFilter.HOY:
            where_sql.append("DATE(va.slot_iso) = CURRENT_DATE")
        elif preset_filter == AgendaPresetFilter.NO_SHOWS_DIA:
            where_sql.append("va.status = 'NO_SHOW'")
            where_sql.append("DATE(va.slot_iso) = CURRENT_DATE")
        elif preset_filter == AgendaPresetFilter.POR_CONFIRMAR_MANANA:
            where_sql.append("va.status = 'SCHEDULED'")
            where_sql.append("DATE(va.slot_iso) = CURRENT_DATE + INTERVAL '1 day'")
        elif preset_filter == AgendaPresetFilter.REAGENDAR_PENDIENTES:
            where_sql.append("va.status = 'RESCHEDULED'")
        elif preset_filter == AgendaPresetFilter.SALDOS_PENDIENTES:
            where_sql.append("(va.balance_status = 'pending' OR va.balance_status = 'deposit_paid')")

        # Doctor filter (bound param)
        if doctor_id is not None:
            where_sql.append("va.doctor_id = :doctor_id")
            params.append(bindparam("doctor_id", value=doctor_id))

        params.append(bindparam("row_limit", value=limit))
        params.append(bindparam("row_offset", value=offset))

        where_clause = " AND ".join(where_sql)
        stmt = text(
            f"SELECT {_GRID_PROJECTION}"  # noqa: S608 — static projection + bound params, no user input
            f"{_GRID_FROM_JOINS}"
            f" WHERE {where_clause}"
            f"{_GRID_GROUP_BY}"
            " ORDER BY va.slot_iso ASC"
            " LIMIT :row_limit OFFSET :row_offset"
        ).bindparams(*params)

        result = await self._session.execute(stmt)
        rows = result.mappings().all()

        logger.debug(
            "agenda_grid_list_slots_done",
            tenant_id=str(tenant_id),
            clinic_id=str(clinic_id),
            count=len(rows),
        )

        return [_apply_name_mask(dict(row)) for row in rows]

    # ---------------------------------------------------------------------------
    # Write methods (T-BE-4): create appointment + clinic_map with mirror cols
    # ---------------------------------------------------------------------------

    async def create(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        offer_id: UUID,
        patient_id: UUID,
        doctor_id: UUID,
        service_label: str,
        start_time: datetime,
        end_time: datetime,
        origin: str,
        notes_internal: str | None = None,
        currency_override: str | None = None,
    ) -> UUID:
        """Insert engine appointment row into vitalia_appointments.

        vitalia_appointments has no Python model (created via raw migration).
        Returns the new appointment_id UUID.

        T-BE-4 bugfix: clinic_id and offer_id are NOT NULL in vitalia_appointments
        (schema from mig 002) — they MUST be included in the INSERT.
        clinic_id: comes from X-Clinic-ID header (dual filter — hipaa-lite.md).
        offer_id: comes from the catalog offer selected by the user (FK, required).
        """
        appointment_id = uuid4()
        duration_minutes = int((end_time - start_time).total_seconds() // 60)
        stmt = text(
            "INSERT INTO vitalia_appointments "
            "(id, tenant_id, clinic_id, offer_id, patient_id, doctor_id, slot_iso, duration_minutes, "
            " status, origin, notes_internal, currency, created_at) "
            "VALUES (:id, :tenant_id, :clinic_id, :offer_id, :patient_id, :doctor_id, :slot_iso, :dur, "
            "        'SCHEDULED', :origin, :notes, :currency, NOW())"
        ).bindparams(
            bindparam("id", value=appointment_id),
            bindparam("tenant_id", value=tenant_id),
            bindparam("clinic_id", value=clinic_id),
            bindparam("offer_id", value=offer_id),
            bindparam("patient_id", value=patient_id),
            bindparam("doctor_id", value=doctor_id),
            bindparam("slot_iso", value=start_time),
            bindparam("dur", value=duration_minutes),
            bindparam("origin", value=origin),
            bindparam("notes", value=notes_internal),
            bindparam("currency", value=currency_override),
        )
        await self._session.execute(stmt)
        logger.info(
            "appointment_created",
            appointment_id=str(appointment_id),
            tenant_id=str(tenant_id),
            clinic_id=str(clinic_id),
            offer_id=str(offer_id),
        )
        return appointment_id

    async def create_clinic_map(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        appointment_id: UUID,
        patient_id: UUID,
        doctor_id: UUID,
        service_label: str,
        origin: str,
        currency_override: str | None = None,
        # T-BE-4 mirror columns (feed the EXCLUDE constraint from migration 050)
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        status: str = "SCHEDULED",
    ) -> None:
        """Insert brand-local clinic_map row with mirror cols for EXCLUDE constraint.

        start_time/end_time/status are the mirror columns added by migration 050.
        They feed: EXCLUDE USING gist(tstzrange(start_time, end_time, '[)') WITH &&, ...)
        WHERE (status <> 'CANCELLED').
        SQLSTATE 23P01 on this insert → AppointmentOverlapError.
        """
        row = AppointmentClinicMapModel(
            appointment_id=appointment_id,
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            patient_id=patient_id,
            doctor_id=doctor_id,
            service_label=service_label,
            origin=origin,
            currency_override=currency_override,
            start_time=start_time,
            end_time=end_time,
            status=status,
        )
        self._session.add(row)
        await self._session.flush()  # raise IntegrityError here if EXCLUDE fires

        logger.info(
            "clinic_map_created",
            appointment_id=str(appointment_id),
            tenant_id=str(tenant_id),
            clinic_id=str(clinic_id),
        )

    async def update_clinic_map_status(
        self,
        appointment_id: UUID,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        new_status: str,
    ) -> None:
        """Propagate status change to clinic_map mirror column.

        Called by AppointmentStatusService after update_status().
        CANCELLED frees the slot for EXCLUDE (WHERE status <> 'CANCELLED').
        """
        stmt = (
            update(AppointmentClinicMapModel)
            .where(
                AppointmentClinicMapModel.appointment_id == appointment_id,
                AppointmentClinicMapModel.tenant_id == tenant_id,
                AppointmentClinicMapModel.clinic_id == clinic_id,
                AppointmentClinicMapModel.deleted_at.is_(None),
            )
            .values(status=new_status)
        )
        await self._session.execute(stmt)
        logger.info(
            "clinic_map_status_updated",
            appointment_id=str(appointment_id),
            tenant_id=str(tenant_id),
            new_status=new_status,
        )
