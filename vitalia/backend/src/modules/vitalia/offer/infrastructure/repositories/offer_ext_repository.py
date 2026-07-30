# cap: lisa.servicios
"""OfferServiceExtRepository — async, tenant-scoped, soft-delete.

Every query filters tenant_id (incl. get_by_id). NOT PHI (RN-13) → plain
AsyncSession (no dual filter). VO bundles round-trip via serializers.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.vitalia.offer.domain.enums import InitialApptType, ServiceModality
from src.modules.vitalia.offer.domain.offer_ext import OfferExt
from src.modules.vitalia.offer.infrastructure.models.offer_service_ext_model import OfferServiceExtModel
from src.modules.vitalia.offer.infrastructure.serializers import (
    interval_from_dict,
    interval_to_dict,
    pricing_from_dict,
    pricing_to_dict,
    variants_from_list,
    variants_to_list,
)


class OfferExtNotFoundError(Exception):
    """Raised when updating an OfferExt that does not exist in the tenant scope."""

    def __init__(self, ext_id: UUID) -> None:
        super().__init__(f"OfferExt {ext_id} not found (or soft-deleted) in tenant scope.")


_SCALAR_TEXT = (
    "description_long",
    "includes",
    "excludes",
    "warranty",
    "procedure_steps",
    "anesthesia_pain",
    "prep",
    "aftercare",
    "downtime",
    "expected_result",
    "result_timing",
    "result_lifespan",
    "realistic_expectations",
    "risks",
    "red_flags",
    "canonical_service_ref",
    "category",
)


def _to_model(ext: OfferExt) -> OfferServiceExtModel:
    model = OfferServiceExtModel(
        id=ext.id,
        tenant_id=ext.tenant_id,
        offer_id=ext.offer_id,
        modality=ext.modality.value,
        is_active=ext.is_active,
        clinic_scope=ext.clinic_scope,
        variants=variants_to_list(ext.variants),
        session_interval=interval_to_dict(ext.session_interval),
        recurrence_interval=interval_to_dict(ext.recurrence_interval),
        initial_appt_duration_minutes=ext.initial_appt_duration_minutes,
        initial_appt_type=ext.initial_appt_type.value if ext.initial_appt_type is not None else None,
        pricing=pricing_to_dict(ext.pricing),
        candidate_for_library=ext.candidate_for_library,
    )
    for attr in _SCALAR_TEXT:
        setattr(model, attr, getattr(ext, attr))
    return model


def _to_domain(model: OfferServiceExtModel) -> OfferExt:
    ext = OfferExt(
        tenant_id=model.tenant_id,
        offer_id=model.offer_id,
        modality=ServiceModality(model.modality),
        is_active=model.is_active,
        clinic_scope=model.clinic_scope,
        variants=variants_from_list(model.variants),
        session_interval=interval_from_dict(model.session_interval),
        recurrence_interval=interval_from_dict(model.recurrence_interval),
        initial_appt_duration_minutes=model.initial_appt_duration_minutes,
        initial_appt_type=InitialApptType(model.initial_appt_type) if model.initial_appt_type is not None else None,
        pricing=pricing_from_dict(model.pricing),
        candidate_for_library=model.candidate_for_library,
        id=model.id,
        created_at=model.created_at,
        updated_at=model.updated_at,
        deleted_at=model.deleted_at,
    )
    for attr in _SCALAR_TEXT:
        setattr(ext, attr, getattr(model, attr))
    return ext


class OfferServiceExtRepository:
    """Persistence for OfferExt (brand projection)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, ext: OfferExt) -> OfferExt:
        model = _to_model(ext)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return _to_domain(model)

    async def get_by_id(self, entity_id: UUID, *, tenant_id: UUID) -> OfferExt | None:
        stmt = select(OfferServiceExtModel).where(
            OfferServiceExtModel.id == entity_id,
            OfferServiceExtModel.tenant_id == tenant_id,
            OfferServiceExtModel.deleted_at.is_(None),
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_domain(model) if model is not None else None

    async def get_by_offer(self, offer_id: UUID, *, tenant_id: UUID) -> OfferExt | None:
        stmt = select(OfferServiceExtModel).where(
            OfferServiceExtModel.offer_id == offer_id,
            OfferServiceExtModel.tenant_id == tenant_id,
            OfferServiceExtModel.deleted_at.is_(None),
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_domain(model) if model is not None else None

    async def update(self, ext: OfferExt) -> OfferExt:
        """Patch an existing OfferExt by (id, tenant_id). Touches updated_at.

        Used by autosave-per-field (RN-16) — every PATCH re-persists the whole
        aggregate (idempotent). Soft-deleted rows are not updated.
        """
        values: dict[str, object] = {
            "modality": ext.modality.value,
            "is_active": ext.is_active,
            "canonical_service_ref": ext.canonical_service_ref,
            "category": ext.category,
            "clinic_scope": ext.clinic_scope,
            "variants": variants_to_list(ext.variants),
            "session_interval": interval_to_dict(ext.session_interval),
            "recurrence_interval": interval_to_dict(ext.recurrence_interval),
            "initial_appt_duration_minutes": ext.initial_appt_duration_minutes,
            "initial_appt_type": ext.initial_appt_type.value if ext.initial_appt_type is not None else None,
            "pricing": pricing_to_dict(ext.pricing),
            "candidate_for_library": ext.candidate_for_library,
            "updated_at": datetime.now(UTC),
        }
        for attr in _SCALAR_TEXT:
            values[attr] = getattr(ext, attr)
        stmt = (
            update(OfferServiceExtModel)
            .where(
                OfferServiceExtModel.id == ext.id,
                OfferServiceExtModel.tenant_id == ext.tenant_id,
                OfferServiceExtModel.deleted_at.is_(None),
            )
            .values(**values)
            .returning(OfferServiceExtModel)
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        if model is None:
            raise OfferExtNotFoundError(ext.id)
        await self._session.refresh(model)
        return _to_domain(model)

    async def list_by_tenant(
        self,
        *,
        tenant_id: UUID,
        category: str | None = None,
        active: bool | None = None,
        origin: str | None = None,
        cursor: datetime | None = None,
        limit: int = 24,
    ) -> tuple[list[OfferExt], datetime | None]:
        """Server-side filtered + keyset-paginated list (RN-15).

        Filters (all optional, AND-combined): category exact, active flag, origin
        (``"biblioteca"`` = has canonical_service_ref · ``"personalizado"`` = null).
        Keyset pagination on created_at DESC: pass the previous page's last
        created_at as ``cursor`` to fetch the next page. Returns (rows, next_cursor)
        where next_cursor is None when the page is the last. NEVER loads-all.
        """
        clamped = max(1, min(limit, 100))
        stmt = select(OfferServiceExtModel).where(
            OfferServiceExtModel.tenant_id == tenant_id,
            OfferServiceExtModel.deleted_at.is_(None),
        )
        if category is not None:
            stmt = stmt.where(OfferServiceExtModel.category == category)
        if active is not None:
            stmt = stmt.where(OfferServiceExtModel.is_active.is_(active))
        if origin == "biblioteca":
            stmt = stmt.where(OfferServiceExtModel.canonical_service_ref.is_not(None))
        elif origin == "personalizado":
            stmt = stmt.where(OfferServiceExtModel.canonical_service_ref.is_(None))
        if cursor is not None:
            stmt = stmt.where(OfferServiceExtModel.created_at < cursor)
        stmt = stmt.order_by(OfferServiceExtModel.created_at.desc()).limit(clamped + 1)
        rows = list((await self._session.execute(stmt)).scalars().all())
        next_cursor = rows[clamped].created_at if len(rows) > clamped else None
        page = [_to_domain(m) for m in rows[:clamped]]
        return page, next_cursor

    async def soft_delete(self, entity_id: UUID, *, tenant_id: UUID) -> None:
        stmt = (
            update(OfferServiceExtModel)
            .where(
                OfferServiceExtModel.id == entity_id,
                OfferServiceExtModel.tenant_id == tenant_id,
                OfferServiceExtModel.deleted_at.is_(None),
            )
            .values(deleted_at=datetime.now(UTC))
        )
        await self._session.execute(stmt)
