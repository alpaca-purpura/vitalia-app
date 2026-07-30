# cap: lisa.servicios
"""CaseRepository — PHI (before/after patient photos). HIPAA-lite dual filter.

Inherits the engine ``CompoundScopeRepositoryBase`` (lifted from the brand-local
``PhiRepositoryBase`` on 2026-05-20 per promotion proposal
``2026-05-20-core-platform-extensions-slice-1``). The engine base enforces the
dual filter (tenant_id + scope_id) on every query; vitalia binds
``scope_field="clinic_id"`` for clinic isolation.

create() enforces the consent gate RN-33: a Case with consent_signed=False is
NEVER persisted (raises ConsentNotSignedError). clinic_id is mandatory for every
operation — a missing clinic_id raises MissingClinicFilterError (HIPAA-lite).
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from luana_core_platform.repositories.compound_scope_repository import CompoundScopeRepositoryBase
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.vitalia._shared.repositories.phi_repository import MissingClinicFilterError
from src.modules.vitalia.offer.domain.proof import Case
from src.modules.vitalia.offer.infrastructure.models.offer_service_case_model import OfferServiceCaseModel


class ConsentNotSignedError(Exception):
    """Raised when persisting a PHI Case without a signed consent (RN-33)."""

    def __init__(self, message: str | None = None) -> None:
        super().__init__(
            message
            or "Cannot persist a before/after Case without signed consent "
            "(RN-33 · vitalia/.claude/rules/hipaa-lite.md). consent_signed MUST be true."
        )


def _to_domain(model: OfferServiceCaseModel) -> Case:
    return Case(
        tenant_id=model.tenant_id,
        offer_id=model.offer_id,
        before_asset_url=model.before_asset_url,
        after_asset_url=model.after_asset_url,
        consent_signed=model.consent_signed,
        consent_ref=model.consent_ref,
        clinic_id=model.clinic_id,
        id=model.id,
        created_at=model.created_at,
        deleted_at=model.deleted_at,
    )


class CaseRepository(CompoundScopeRepositoryBase[OfferServiceCaseModel, UUID]):
    """Persistence for PHI before/after cases (engine dual filter + consent gate)."""

    MODEL = OfferServiceCaseModel

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session=session, scope_field="clinic_id")

    @staticmethod
    def _require_clinic(clinic_id: UUID | None) -> UUID:
        if clinic_id is None:
            raise MissingClinicFilterError()
        return clinic_id

    async def create(self, case: Case, *, clinic_id: UUID) -> Case:
        clinic_id = self._require_clinic(clinic_id)
        if not case.consent_signed:
            raise ConsentNotSignedError()
        model = OfferServiceCaseModel(
            id=case.id,
            tenant_id=case.tenant_id,
            offer_id=case.offer_id,
            clinic_id=clinic_id,
            before_asset_url=case.before_asset_url,
            after_asset_url=case.after_asset_url,
            consent_signed=case.consent_signed,
            consent_ref=case.consent_ref,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return _to_domain(model)

    async def get_by_id(self, entity_id: UUID, *, tenant_id: UUID, clinic_id: UUID) -> Case | None:
        clinic_id = self._require_clinic(clinic_id)
        model = await super().get_by_id(id=entity_id, tenant_id=tenant_id, scope_id=clinic_id)
        return _to_domain(model) if model is not None else None

    async def list_by_offer(self, offer_id: UUID, *, tenant_id: UUID, clinic_id: UUID) -> list[Case]:
        clinic_id = self._require_clinic(clinic_id)
        scope_attr = self._scope_attr()
        stmt = (
            select(OfferServiceCaseModel)
            .where(OfferServiceCaseModel.tenant_id == tenant_id)
            .where(scope_attr == clinic_id)
            .where(OfferServiceCaseModel.offer_id == offer_id)
            .where(OfferServiceCaseModel.deleted_at.is_(None))
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_domain(m) for m in rows]

    async def soft_delete(self, entity_id: UUID, *, tenant_id: UUID, clinic_id: UUID) -> None:
        clinic_id = self._require_clinic(clinic_id)
        stmt = (
            update(OfferServiceCaseModel)
            .where(
                OfferServiceCaseModel.id == entity_id,
                OfferServiceCaseModel.tenant_id == tenant_id,
                OfferServiceCaseModel.clinic_id == clinic_id,
                OfferServiceCaseModel.deleted_at.is_(None),
            )
            .values(deleted_at=datetime.now(UTC))
        )
        await self._session.execute(stmt)
