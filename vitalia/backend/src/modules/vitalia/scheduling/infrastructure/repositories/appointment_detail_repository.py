# cap: scheduling.mateo-agenda
# story-origin: TBD
"""AppointmentDetailRepository — appointment detail view with PHI masking.

Returns full detail projection for the appointment drawer (right panel):
  - PHI-masked patient name + DNI
  - Service label from clinic_map
  - Payment history (list of payments)
  - Doctor + slot + status

Dual filter HIPAA: EVERY query filters tenant_id + clinic_id.
PHI masking: patient_name_masked + dni_masked (server-side).

Per 03-arch § 3.2 + vitalia/.claude/rules/hipaa-lite.md
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

import structlog
from luana_core_platform.repositories.compound_scope_repository import (
    CompoundScopeRepositoryBase,
)
from sqlalchemy import bindparam, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.vitalia._shared.encryption.kek_client import KEKClient
from src.modules.vitalia.scheduling.infrastructure.repositories._phi_mask import apply_name_mask
from src.modules.vitalia.scheduling.persistence.models.appointment_clinic_map_model import (
    AppointmentClinicMapModel,
)
from src.modules.vitalia.scheduling.persistence.models.appointment_payment_model import (
    AppointmentPaymentModel,
)

logger = structlog.get_logger()

# SQLAlchemy 2.0 note (bug fix vitalia-bugfix-agenda-actor-headers-422 T-2):
# this detail query had the same TextClause crash as agenda_grid_repository_impl
# (select(...).select_from(text(...)).outerjoin(ORMModel, ...) → ORM compile path
# reads `.selectable` on a TextClause → AttributeError / HTTP 500). It is rewritten
# as a single parameterized text() statement: dual filter (tenant_id + clinic_id)
# as bound params, only real-schema columns projected. PHI name/DNI are masked
# placeholders (vitalia_appointments has no name column; patient name is encrypted
# bytea in vitalia_patients) — real masked-name resolution is an architect follow-up.
_DETAIL_PROJECTION = """
    va.id AS appointment_id,
    va.patient_id AS patient_id,
    pgp_sym_decrypt(p.name, :kek)::text AS raw_patient_name,
    '—' AS dni_masked,
    COALESCE(map.service_label, 'Consulta') AS service_label,
    va.doctor_id AS doctor_id,
    COALESCE(NULLIF(TRIM(CONCAT(doc.first_name, ' ', doc.last_name)), ''), 'Sin asignar') AS doctor_label,
    va.slot_iso AS start_time,
    va.slot_iso + (va.duration_minutes * INTERVAL '1 minute') AS end_time,
    va.duration_minutes AS duration_minutes,
    va.status AS appointment_status,
    CASE
        WHEN va.status = 'NO_SHOW' THEN 'no_show'
        WHEN COALESCE(va.amount_pending, 0) <= 0 AND COALESCE(va.amount_paid, 0) > 0 THEN 'pagado'
        WHEN COALESCE(va.amount_paid, 0) > 0 THEN 'deposito'
        ELSE 'sin_pago'
    END AS payment_status,
    COALESCE(map.origin, va.origin) AS origin,
    ROUND(COALESCE(va.amount_pending, 0) * 100)::bigint AS balance_due_cents,
    ROUND(COALESCE(va.amount_paid, 0) * 100)::bigint AS balance_paid_cents,
    COALESCE(map.currency_override, va.currency) AS currency,
    va.booking_metadata AS booking_metadata,
    va.created_at AS created_at,
    va.updated_at AS updated_at
"""


class AppointmentDetailRepository(CompoundScopeRepositoryBase):  # type: ignore[type-arg]
    """Async repository for appointment detail views.

    Inherits CompoundScopeRepositoryBase (engine) for HIPAA-lite dual-scope
    isolation (tenant_id + clinic_id). MODEL is None because this repo issues
    JOIN queries across vitalia_appointments (no Python SA model) + ORM models.
    All query methods are fully overridden. scope_field="clinic_id".

    Detail view = appointment + clinic_map (service + origin) + payment history.
    """

    MODEL = None  # Complex JOIN repo — all query methods overridden, never calls super().get_by_id()

    def __init__(self, session: AsyncSession, kek: KEKClient | None = None) -> None:
        super().__init__(session=session, scope_field="clinic_id")
        self._kek: KEKClient = kek if kek is not None else KEKClient.from_env()

    async def get_by_id(
        self,
        entity_id: UUID,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
    ) -> dict[str, Any] | None:
        """Get appointment detail by ID with dual filter + PHI masking.

        Args:
            entity_id: Appointment UUID.
            tenant_id: Tenant UUID (dual filter key 1).
            clinic_id: Clinic UUID (HIPAA-lite dual filter key 2).

        Returns:
            Appointment detail dict with PHI-masked fields, or None if not found.
        """
        if clinic_id is None:
            raise ValueError("AppointmentDetailRepository: clinic_id required (HIPAA-lite dual filter)")

        logger.info(
            "appointment_detail_get",
            appointment_id=str(entity_id),
            tenant_id=str(tenant_id),
            clinic_id=str(clinic_id),
        )

        stmt = text(
            f"SELECT {_DETAIL_PROJECTION}"  # noqa: S608 — static projection + bound params, no user input
            " FROM vitalia_appointments va"
            " LEFT OUTER JOIN vitalia_appointment_clinic_map map"
            "   ON map.appointment_id = va.id AND map.deleted_at IS NULL"
            " LEFT OUTER JOIN vitalia_doctors doc"
            "   ON doc.id = va.doctor_id AND doc.tenant_id = va.tenant_id AND doc.deleted_at IS NULL"
            " LEFT OUTER JOIN vitalia_patients p"
            "   ON p.id = va.patient_id AND p.tenant_id = va.tenant_id AND p.deleted_at IS NULL"
            " WHERE va.tenant_id = :tenant_id"
            "   AND va.clinic_id = :clinic_id"
            "   AND va.id = :appointment_id"
            "   AND va.deleted_at IS NULL"
        ).bindparams(
            bindparam("tenant_id", value=tenant_id),
            bindparam("clinic_id", value=clinic_id),
            bindparam("appointment_id", value=entity_id),
            bindparam("kek", value=self._kek.get_key()),
        )

        result = await self._session.execute(stmt)
        row = result.mappings().first()
        if row is None:
            return None
        # Mask the decrypted patient name + strip the raw key before it leaves the repo (D5).
        detail = apply_name_mask(dict(row))

        # Fetch payment history
        payments = await self._get_payments(
            appointment_id=entity_id,
            tenant_id=tenant_id,
            clinic_id=clinic_id,
        )
        detail["payments"] = payments

        return detail

    async def list_by_filter(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        **filters: object,
    ) -> list[dict[str, Any]]:
        """List appointments by filter (stub — use AgendaGridRepository for grid queries)."""
        if clinic_id is None:
            raise ValueError("AppointmentDetailRepository: clinic_id required (HIPAA-lite dual filter)")
        return []

    async def update_status(
        self,
        appointment_id: UUID,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        new_status: str,
        reason: str | None = None,
    ) -> dict[str, Any]:
        """Update appointment status in vitalia_appointments.

        Dual filter: tenant_id + clinic_id (via clinic_map FK join — HIPAA-lite).
        Returns updated detail dict after persisting.
        """
        # Update base appointments table (status field)
        stmt = text(
            "UPDATE vitalia_appointments "
            "SET status = :new_status, updated_at = NOW() "
            "WHERE id = :appt_id AND tenant_id = :tenant_id AND deleted_at IS NULL"
        ).bindparams(
            bindparam("new_status", value=new_status),
            bindparam("appt_id", value=appointment_id),
            bindparam("tenant_id", value=tenant_id),
        )
        await self._session.execute(stmt)

        logger.info(
            "appointment_status_updated",
            appointment_id=str(appointment_id),
            tenant_id=str(tenant_id),
            new_status=new_status,
        )

        # Return fresh detail
        result = await self.get_by_id(appointment_id, tenant_id=tenant_id, clinic_id=clinic_id)
        if result is None:
            # Shouldn't happen if caller verified existence first, return minimal dict
            return {"appointment_id": str(appointment_id), "status": new_status}
        return result

    async def update_clinic_map_status(
        self,
        appointment_id: UUID,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        new_status: str,
    ) -> None:
        """Propagate status change to clinic_map mirror column (T-BE-4).

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

    async def _get_payments(
        self,
        appointment_id: UUID,
        tenant_id: UUID,
        clinic_id: UUID,
    ) -> list[dict[str, Any]]:
        """Fetch payment records for an appointment (dual filter applied)."""
        stmt = (
            select(AppointmentPaymentModel)
            .where(
                AppointmentPaymentModel.appointment_id == appointment_id,
                AppointmentPaymentModel.tenant_id == tenant_id,
                AppointmentPaymentModel.clinic_id == clinic_id,
                AppointmentPaymentModel.deleted_at.is_(None),
            )
            .order_by(AppointmentPaymentModel.created_at.asc())
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [
            {
                # DTO field names (AppointmentPaymentDTO) — NOT the model's id/amount.
                # The id/amount mismatch 500'd the detail drawer (D9, story vitalia-scheduling-mateo-review).
                "payment_id": str(m.id),
                "amount_cents": m.amount,
                "currency": m.currency,
                "method": m.method,
                "fiscal_doc_url": None,  # fiscal doc URL not resolved here (DTO-optional)
                "fiscal_doc_type": None,
                "created_by_label": None,  # staff label not resolved here (DTO-optional)
                "external_payment_id": m.external_payment_id,
                "fiscal_doc_id": str(m.fiscal_doc_id) if m.fiscal_doc_id else None,
                "notes": m.notes,
                "balance_version": m.balance_version,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in models
        ]
