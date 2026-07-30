# cap: lisa.servicios
"""ProofService — social proof: Case (PHI) + Testimonial (not PHI) (T-2 § 6).

Case is PHI (before/after patient photo): the consent gate RN-33 lives at the
repository (a Case with consent_signed=False is never persisted, raising
``ConsentNotSignedError``), and every successful persist/delete writes a HIPAA-
lite ``audit_log`` row SYNCHRONOUSLY before the service returns (never fire-and-
forget). The audit payload carries NO PHI (no photo URLs, no consent text) — only
the action + resource ids. Dual-scoped tenant_id + clinic_id throughout.

Testimonial is manual marketing copy (NOT PHI): plain tenant-scoped CRUD with no
consent gate and no audit row.
"""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

import structlog

from src.modules.vitalia._shared.repositories.audit_log_repository import AuditLogEntry
from src.modules.vitalia.offer.domain.proof import Case, Testimonial

logger = structlog.get_logger()


class _CaseRepo(Protocol):
    async def create(self, case: Case, *, clinic_id: UUID) -> Case: ...
    async def list_by_offer(self, offer_id: UUID, *, tenant_id: UUID, clinic_id: UUID) -> list[Case]: ...
    async def soft_delete(self, entity_id: UUID, *, tenant_id: UUID, clinic_id: UUID) -> None: ...


class _TestimonialRepo(Protocol):
    async def create(self, testimonial: Testimonial) -> Testimonial: ...
    async def list_by_offer(self, offer_id: UUID, *, tenant_id: UUID) -> list[Testimonial]: ...
    async def soft_delete(self, entity_id: UUID, *, tenant_id: UUID) -> None: ...


class _Audit(Protocol):
    async def write(self, entry: AuditLogEntry) -> None: ...


class ProofService:
    """Cases (PHI, consent-gated + audited) + testimonials (plain CRUD)."""

    def __init__(self, *, case_repo: _CaseRepo, testimonial_repo: _TestimonialRepo, audit: _Audit) -> None:
        self._cases = case_repo
        self._testimonials = testimonial_repo
        self._audit = audit

    # ---- Case (PHI) ------------------------------------------------------

    async def create_case(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        user_id: UUID,
        offer_id: UUID,
        before_asset_url: str,
        after_asset_url: str,
        consent_signed: bool,
        consent_ref: str | None = None,
    ) -> Case:
        case = Case(
            tenant_id=tenant_id,
            offer_id=offer_id,
            before_asset_url=before_asset_url,
            after_asset_url=after_asset_url,
            consent_signed=consent_signed,
            consent_ref=consent_ref,
            clinic_id=clinic_id,
        )
        # Consent gate (RN-33) raises here when consent_signed is False — nothing
        # is persisted and NO audit row is written for a rejected access.
        saved = await self._cases.create(case, clinic_id=clinic_id)
        await self._write_audit(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            user_id=user_id,
            action="create_service_case",
            resource_id=saved.id,
        )
        return saved

    async def list_cases(self, *, tenant_id: UUID, clinic_id: UUID, offer_id: UUID) -> list[Case]:
        return await self._cases.list_by_offer(offer_id, tenant_id=tenant_id, clinic_id=clinic_id)

    async def delete_case(self, *, tenant_id: UUID, clinic_id: UUID, user_id: UUID, case_id: UUID) -> None:
        await self._cases.soft_delete(case_id, tenant_id=tenant_id, clinic_id=clinic_id)
        await self._write_audit(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            user_id=user_id,
            action="delete_service_case",
            resource_id=case_id,
        )

    # ---- Testimonial (NOT PHI) -------------------------------------------

    async def create_testimonial(
        self,
        *,
        tenant_id: UUID,
        offer_id: UUID,
        rating: int,
        text: str,
        author: str,
        source: str,
    ) -> Testimonial:
        testimonial = Testimonial(
            tenant_id=tenant_id,
            offer_id=offer_id,
            rating=rating,
            text=text,
            author=author,
            source=source,
        )
        return await self._testimonials.create(testimonial)

    async def list_testimonials(self, *, tenant_id: UUID, offer_id: UUID) -> list[Testimonial]:
        return await self._testimonials.list_by_offer(offer_id, tenant_id=tenant_id)

    async def delete_testimonial(self, *, tenant_id: UUID, testimonial_id: UUID) -> None:
        await self._testimonials.soft_delete(testimonial_id, tenant_id=tenant_id)

    # ---- HIPAA-lite audit (sync, no PHI in payload) ----------------------

    async def _write_audit(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        user_id: UUID,
        action: str,
        resource_id: UUID,
    ) -> None:
        entry = AuditLogEntry(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            user_id=user_id,
            action=action,
            resource_type="service_case",
            resource_id=resource_id,
            # payload_redacted intentionally empty: no photo URL / consent text (PHI).
        )
        await self._audit.write(entry)
