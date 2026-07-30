# cap: lisa.servicios
# voseo-allowed: "vos" matched by hook is the value-objects module name (domain.vos), not voseo
"""Vitalia Offer — Lisa's service catalog API router (T-2 § 4, 16 endpoints).

Endpoints served under /api/v1/offer/:
  GET    /servicios                                  — catalog list + filters (RN-15 cursor)
  GET    /servicios/{offer_id}                       — service workspace
  POST   /servicios/from-template                    — draft from biblioteca preset (RN-16/25)
  POST   /servicios/custom                           — custom service (canonical_ref=null)
  PATCH  /servicios/{offer_id}                       — per-field autosave (RN-20)
  POST   /servicios/{offer_id}/activate              — toggle Activo (RN-10)
  DELETE /servicios/{offer_id}                       — soft-delete
  GET    /biblioteca/search                          — typeahead name+synonyms (RN-25/AC-18)
  POST   /servicios/{offer_id}/specialists           — link doctor (autosave · RN-20)
  DELETE /servicios/{offer_id}/specialists/{doctor}  — unlink
  POST   /servicios/{offer_id}/cases                 — HIPAA-lite consent gate + audit row
  DELETE /servicios/{offer_id}/cases/{case_id}       — remove case (audited)
  POST   /servicios/{offer_id}/testimonials          — manual testimonial
  DELETE /servicios/{offer_id}/testimonials/{id}     — remove testimonial
  PATCH  /servicios/{offer_id}/sales-brief           — sales brief autosave + write-through
  POST   /servicios/{offer_id}/knowledge/extract     — document→autocomplete (AC-11, NOT RAG)

RBAC per 03-arch § 8 (RN-7):
  - GET endpoints: open to any authenticated tenant caller (catalog reads).
  - POST/PATCH/DELETE: require_brand_owner_access() (owner + admin_clinic) → 403 otherwise.

Isolation/HIPAA per 03-arch § 8:
  - X-Tenant-ID header mandatory (tenant filter); cross-tenant → service None → 404, no leak.
  - X-User-ID header on audited writes (resolved to IAM users.id via _resolve_audit_actor).
  - X-Clinic-ID header required ONLY on Case endpoints (PHI dual filter; catalog is NOT PHI).
  - Case create: consent gate RN-33 (consent=False → repo raises ConsentNotSignedError → 422)
    + audit_log SYNC write pre-response. PHI never in URL; audit payload carries no PHI.
  - response_model= on EVERY route (arch test test_response_model_required + PII allowlist).

The api layer is THIN: validate DTO → call service → map domain exception → HTTPException.

downstream-regression-na: brand-local offer router for vitalia
"""

from __future__ import annotations

from decimal import Decimal
from typing import Annotated, NamedTuple
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import get_async_session_committing
from src.modules.vitalia._shared.auth.rbac import require_brand_owner_access
from src.modules.vitalia._shared.telemetry.growth_studio_emitter import GrowthStudioEmitter
from src.modules.vitalia.audit.audit_writer import AsyncAuditWriter
from src.modules.vitalia.iam.application.services.clinic_resolver import UserNotFoundError
from src.modules.vitalia.iam.application.services.user_resolver import resolve_user_uuid_from_clerk_id
from src.modules.vitalia.offer.api.dtos import (
    BibliotecaItemDTO,
    BibliotecaSearchResponse,
    CaseCreateRequest,
    CaseDTO,
    ExtractionPrefillDTO,
    KnowledgeExtractRequest,
    KnowledgeExtractResponse,
    KnowledgeSourceDTO,
    SalesBriefDTO,
    SalesBriefPatchRequest,
    ServiceActivateRequest,
    ServiceCreateCustomRequest,
    ServiceCreateFromTemplateRequest,
    ServiceDetailDTO,
    ServiceListItemDTO,
    ServiceListResponse,
    ServicePatchRequest,
    ServiceVariantDTO,
    SpecialistLinkDTO,
    SpecialistLinkRequest,
    TestimonialCreateRequest,
    TestimonialDTO,
    ThreeChargePricingDTO,
    ValueWithUnitDTO,
)
from src.modules.vitalia.offer.application.services.biblioteca_service import BibliotecaService
from src.modules.vitalia.offer.application.services.catalog_service import ServiceCatalogService, ServiceView
from src.modules.vitalia.offer.application.services.document_autocomplete_service import DocumentAutocompleteService
from src.modules.vitalia.offer.application.services.proof_service import ProofService
from src.modules.vitalia.offer.application.services.sales_brief_service import SalesBriefService
from src.modules.vitalia.offer.application.services.specialist_link_service import (
    DoctorNotInRosterError,
    SpecialistLinkService,
)
from src.modules.vitalia.offer.domain.enums import ServiceModality
from src.modules.vitalia.offer.infrastructure.adapters.doc_extract_adapter import DocExtractAdapter
from src.modules.vitalia.offer.infrastructure.adapters.doctor_roster_adapter import DoctorRosterAdapter
from src.modules.vitalia.offer.infrastructure.adapters.knowledge_source_adapter import KnowledgeSourceAdapter
from src.modules.vitalia.offer.infrastructure.adapters.offer_engine_adapter import OfferEngineAdapter
from src.modules.vitalia.offer.infrastructure.repositories.case_repository import CaseRepository, ConsentNotSignedError
from src.modules.vitalia.offer.infrastructure.repositories.offer_ext_repository import OfferServiceExtRepository
from src.modules.vitalia.offer.infrastructure.repositories.sales_brief_repository import SalesBriefRepository
from src.modules.vitalia.offer.infrastructure.repositories.specialist_link_repository import (
    ServiceSpecialistLinkRepository,
)
from src.modules.vitalia.offer.infrastructure.repositories.testimonial_repository import TestimonialRepository

logger = structlog.get_logger()

# Mutation guard: owner + admin_clinic only (RN-7).
_brand_owner_required = Depends(require_brand_owner_access())

router = APIRouter(tags=["offer"])


# ============================================================
# Header / actor helpers
# ============================================================


def _tenant_uuid(tenant_id: str) -> UUID:
    try:
        return UUID(tenant_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Invalid tenant_id") from exc


def _clinic_uuid(clinic_id: str) -> UUID:
    try:
        return UUID(clinic_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Invalid clinic_id") from exc


async def _resolve_audit_actor(session: AsyncSession, user_id_header: str) -> UUID:
    """Resolve X-User-ID (users.id UUID or Clerk userId) to an IAM users.id UUID.

    Mirrors brand_studio marca_router._resolve_audit_actor: a UUID is used as-is;
    a Clerk userId string is resolved via the iam resolver; anything else → 422.
    """
    try:
        return UUID(user_id_header)
    except ValueError:
        pass
    try:
        return await resolve_user_uuid_from_clerk_id(session, user_id_header)
    except UserNotFoundError as exc:
        raise HTTPException(status_code=422, detail="Invalid user_id") from exc


# ============================================================
# Dependency injection factories
# ============================================================


async def _get_db(
    session: Annotated[AsyncSession, Depends(get_async_session_committing)],
) -> AsyncSession:
    """Pass-through DI for AsyncSession (committing so mutations persist)."""
    return session


class _ServiceBundle(NamedTuple):
    """Named bundle of DI-constructed services for a single request."""

    catalog: ServiceCatalogService
    biblioteca: BibliotecaService
    specialists: SpecialistLinkService
    proof: ProofService
    sales_brief: SalesBriefService
    autocomplete: DocumentAutocompleteService


def _build_service(session: AsyncSession) -> _ServiceBundle:
    """Build the offer service tree from an async session (patchable in tests)."""
    audit = AsyncAuditWriter(session=session)
    emitter = GrowthStudioEmitter(session=session)

    catalog = ServiceCatalogService(
        engine=OfferEngineAdapter(session),
        ext_repo=OfferServiceExtRepository(session),
        emitter=emitter,
    )
    biblioteca = BibliotecaService()
    specialists = SpecialistLinkService(
        roster=DoctorRosterAdapter(session),
        link_repo=ServiceSpecialistLinkRepository(session),
    )
    proof = ProofService(
        case_repo=CaseRepository(session),
        testimonial_repo=TestimonialRepository(session),
        audit=audit,
    )
    sales_brief = SalesBriefService(brief_repo=SalesBriefRepository(session))
    autocomplete = DocumentAutocompleteService(
        extractor=DocExtractAdapter(),
        knowledge=KnowledgeSourceAdapter(session),
    )
    return _ServiceBundle(
        catalog=catalog,
        biblioteca=biblioteca,
        specialists=specialists,
        proof=proof,
        sales_brief=sales_brief,
        autocomplete=autocomplete,
    )


# ============================================================
# Detail composition helper
# ============================================================


async def _detail_dto(
    bundle: _ServiceBundle,
    *,
    tenant_id: UUID,
    view: ServiceView,
    clinic_id: UUID | None = None,
) -> ServiceDetailDTO:
    """Compose the workspace DTO: catalog headline + sub-resources (tenant-scoped).

    *clinic_id* is optional (G2-F13-BE): when present, specialist links are
    enriched with ``display_name`` + ``specialty`` from the doctor roster.
    When absent the enrichment is skipped and those fields are ``None``.
    """
    brief = await bundle.sales_brief.get(tenant_id=tenant_id, offer_id=view.offer_id)
    enriched_links = await bundle.specialists.list_for_offer(
        tenant_id=tenant_id, offer_id=view.offer_id, clinic_id=clinic_id
    )
    testimonials = await bundle.proof.list_testimonials(tenant_id=tenant_id, offer_id=view.offer_id)
    return ServiceDetailDTO(
        offer_id=view.offer_id,
        public_name=view.public_name,
        category=view.category,
        modality=view.modality,
        is_active=view.is_active,
        status=view.status,
        canonical_service_ref=view.canonical_service_ref,
        price=view.price,
        currency=view.currency,
        # — Rich ficha fields (T-R1 § A.4 read-path widening) —
        description_long=view.description_long,
        includes=view.includes,
        excludes=view.excludes,
        warranty=view.warranty,
        variants=[ServiceVariantDTO.model_validate(v) for v in view.variants],
        procedure_steps=view.procedure_steps,
        anesthesia_pain=view.anesthesia_pain,
        prep=view.prep,
        aftercare=view.aftercare,
        downtime=view.downtime,
        expected_result=view.expected_result,
        result_timing=view.result_timing,
        result_lifespan=view.result_lifespan,
        realistic_expectations=view.realistic_expectations,
        risks=view.risks,
        red_flags=view.red_flags,
        session_interval=(
            ValueWithUnitDTO.model_validate(view.session_interval) if view.session_interval is not None else None
        ),
        recurrence_interval=(
            ValueWithUnitDTO.model_validate(view.recurrence_interval) if view.recurrence_interval is not None else None
        ),
        initial_appt_duration_minutes=view.initial_appt_duration_minutes,
        initial_appt_type=view.initial_appt_type,
        pricing=ThreeChargePricingDTO.model_validate(view.pricing) if view.pricing is not None else None,
        candidate_for_library=view.candidate_for_library,
        sales_brief=SalesBriefDTO.model_validate(brief) if brief is not None else None,
        # Build SpecialistLinkDTO explicitly to carry display_name + specialty
        # from the enriched read model (G2-F13-BE).
        specialists=[
            SpecialistLinkDTO(
                id=link.id,
                offer_id=link.offer_id,
                doctor_id=link.doctor_id,
                display_name=link.display_name,
                specialty=link.specialty,
            )
            for link in enriched_links
        ],
        # cases are PHI (need clinic_id) — omitted from the generic workspace payload.
        cases=[],
        testimonials=[TestimonialDTO.model_validate(t) for t in testimonials],
    )


# ============================================================
# Catalog — list + detail
# ============================================================


@router.get("/servicios", response_model=ServiceListResponse, summary="Catalog list + filters (RN-15)")
async def list_services(
    tenant_id: str = Header(alias="X-Tenant-ID"),
    search: str | None = Query(default=None),
    category: str | None = Query(default=None),
    active: bool | None = Query(default=None),
    origin: str | None = Query(default=None),
    cursor: str | None = Query(default=None),
    session: AsyncSession = Depends(_get_db),
) -> ServiceListResponse:
    """Return a keyset-paginated catalog page with optional filters."""
    tenant = _tenant_uuid(tenant_id)
    bundle = _build_service(session)
    views, next_cursor = await bundle.catalog.list_services(
        tenant_id=tenant,
        name_query=search,
        category=category,
        active=active,
        origin=origin,
        cursor=cursor,
    )
    return ServiceListResponse(
        items=[ServiceListItemDTO.model_validate(v) for v in views],
        next_cursor=str(next_cursor) if next_cursor is not None else None,
    )


@router.get("/servicios/{offer_id}", response_model=ServiceDetailDTO, summary="Service workspace")
async def get_service(
    offer_id: UUID,
    tenant_id: str = Header(alias="X-Tenant-ID"),
    clinic_id_header: str | None = Header(default=None, alias="X-Clinic-ID"),
    session: AsyncSession = Depends(_get_db),
) -> ServiceDetailDTO:
    """Return the workspace for a service. Cross-tenant / missing → 404 (no leak).

    When ``X-Clinic-ID`` is provided (G2-F13-BE) the response includes
    ``display_name`` and ``specialty`` for each linked specialist.  The header
    is **optional** — the endpoint remains fully functional without it.
    """
    tenant = _tenant_uuid(tenant_id)
    clinic: UUID | None = None
    if clinic_id_header is not None:
        try:
            clinic = UUID(clinic_id_header)
        except ValueError:
            clinic = None  # invalid UUID → degrade gracefully, do not 422
    bundle = _build_service(session)
    view = await bundle.catalog.get_service(tenant_id=tenant, offer_id=offer_id)
    if view is None:
        raise HTTPException(status_code=404, detail="Service not found")
    return await _detail_dto(bundle, tenant_id=tenant, view=view, clinic_id=clinic)


@router.post(
    "/servicios/from-template",
    response_model=ServiceDetailDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Draft an Offer from a biblioteca preset (RN-16/25)",
)
async def create_from_template(
    request: ServiceCreateFromTemplateRequest,
    tenant_id: str = Header(alias="X-Tenant-ID"),
    user_id: str = Header(alias="X-User-ID"),
    _role: str = _brand_owner_required,
    session: AsyncSession = Depends(_get_db),
) -> ServiceDetailDTO:
    """Create a service pre-filled from a library preset (canonical_ref set)."""
    tenant = _tenant_uuid(tenant_id)
    await _resolve_audit_actor(session, user_id)
    bundle = _build_service(session)
    preset = bundle.biblioteca.get_template(canonical_ref=request.canonical_service_ref)
    if preset is None:
        raise HTTPException(status_code=404, detail="Template not found")
    view = await bundle.catalog.create_service(
        tenant_id=tenant,
        public_name=preset.name,
        price=Decimal("0"),
        currency=None,
        canonical_ref=preset.canonical_ref,
        modality=ServiceModality(preset.modality),
        category=preset.category,
    )
    return await _detail_dto(bundle, tenant_id=tenant, view=view)


@router.post(
    "/servicios/custom",
    response_model=ServiceDetailDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Create a custom service (canonical_ref=null)",
)
async def create_custom(
    request: ServiceCreateCustomRequest,
    tenant_id: str = Header(alias="X-Tenant-ID"),
    user_id: str = Header(alias="X-User-ID"),
    _role: str = _brand_owner_required,
    session: AsyncSession = Depends(_get_db),
) -> ServiceDetailDTO:
    """Create a custom service from scratch."""
    tenant = _tenant_uuid(tenant_id)
    await _resolve_audit_actor(session, user_id)
    bundle = _build_service(session)
    view = await bundle.catalog.create_service(
        tenant_id=tenant,
        public_name=request.public_name,
        price=request.price,
        currency=request.currency,
        canonical_ref=None,
        modality=request.modality,
        category=request.category,
    )
    return await _detail_dto(bundle, tenant_id=tenant, view=view)


@router.patch("/servicios/{offer_id}", response_model=ServiceDetailDTO, summary="Per-field autosave (RN-20)")
async def patch_service(
    offer_id: UUID,
    request: ServicePatchRequest,
    tenant_id: str = Header(alias="X-Tenant-ID"),
    user_id: str = Header(alias="X-User-ID"),
    _role: str = _brand_owner_required,
    session: AsyncSession = Depends(_get_db),
) -> ServiceDetailDTO:
    """Patch one or more service fields. Cross-tenant / missing → 404.

    Only fields present in the request body are applied (exclude_unset=True →
    last-write-wins autosave semantics, RN-20). VO DTOs are converted to domain
    VOs at the service boundary; invariant violations become 422.
    """
    tenant = _tenant_uuid(tenant_id)
    await _resolve_audit_actor(session, user_id)
    bundle = _build_service(session)
    fields = request.model_dump(exclude_unset=True)
    # Convert VO DTO → domain VO at API boundary (invariants enforce here).
    try:
        if "session_interval" in fields and fields["session_interval"] is not None:
            fields["session_interval"] = request.session_interval.to_domain()  # type: ignore[union-attr]
        if "recurrence_interval" in fields and fields["recurrence_interval"] is not None:
            fields["recurrence_interval"] = request.recurrence_interval.to_domain()  # type: ignore[union-attr]
        if "variants" in fields and fields["variants"] is not None:
            fields["variants"] = [v.to_domain() for v in request.variants]  # type: ignore[union-attr]
        if "pricing" in fields and fields["pricing"] is not None:
            fields["pricing"] = request.pricing.to_domain()  # type: ignore[union-attr]
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    view = await bundle.catalog.patch_service(
        tenant_id=tenant,
        offer_id=offer_id,
        **fields,
    )
    if view is None:
        raise HTTPException(status_code=404, detail="Service not found")
    return await _detail_dto(bundle, tenant_id=tenant, view=view)


@router.post("/servicios/{offer_id}/activate", response_model=ServiceDetailDTO, summary="Toggle Activo (RN-10)")
async def activate_service(
    offer_id: UUID,
    request: ServiceActivateRequest,
    tenant_id: str = Header(alias="X-Tenant-ID"),
    user_id: str = Header(alias="X-User-ID"),
    _role: str = _brand_owner_required,
    session: AsyncSession = Depends(_get_db),
) -> ServiceDetailDTO:
    """Activate or pause a service. Cross-tenant / missing → 404."""
    tenant = _tenant_uuid(tenant_id)
    await _resolve_audit_actor(session, user_id)
    bundle = _build_service(session)
    view = await bundle.catalog.set_active(tenant_id=tenant, offer_id=offer_id, active=request.is_active)
    if view is None:
        raise HTTPException(status_code=404, detail="Service not found")
    return await _detail_dto(bundle, tenant_id=tenant, view=view)


@router.delete(
    "/servicios/{offer_id}",
    response_model=None,
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-delete a service",
)
async def delete_service(
    offer_id: UUID,
    tenant_id: str = Header(alias="X-Tenant-ID"),
    user_id: str = Header(alias="X-User-ID"),
    _role: str = _brand_owner_required,
    session: AsyncSession = Depends(_get_db),
) -> None:
    """Soft-delete a service. Missing/cross-tenant is a no-op (idempotent)."""
    tenant = _tenant_uuid(tenant_id)
    await _resolve_audit_actor(session, user_id)
    bundle = _build_service(session)
    existing = await bundle.catalog.get_service(tenant_id=tenant, offer_id=offer_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Service not found")
    await bundle.catalog.soft_delete(tenant_id=tenant, offer_id=offer_id)


# ============================================================
# Biblioteca — typeahead
# ============================================================


@router.get("/biblioteca/search", response_model=BibliotecaSearchResponse, summary="Typeahead (RN-25/AC-18)")
async def biblioteca_search(
    tenant_id: str = Header(alias="X-Tenant-ID"),
    q: str = Query(default=""),
    clinic_type: str = Query(...),
    session: AsyncSession = Depends(_get_db),
) -> BibliotecaSearchResponse:
    """Name+synonym typeahead over the preset library, scoped to the clinic type."""
    _tenant_uuid(tenant_id)
    bundle = _build_service(session)
    suggestions = bundle.biblioteca.search(query=q, clinic_type=clinic_type)
    return BibliotecaSearchResponse(items=[BibliotecaItemDTO.model_validate(s) for s in suggestions])


# ============================================================
# Specialists
# ============================================================


@router.post(
    "/servicios/{offer_id}/specialists",
    response_model=SpecialistLinkDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Link a doctor (autosave · RN-20)",
)
async def link_specialist(
    offer_id: UUID,
    request: SpecialistLinkRequest,
    tenant_id: str = Header(alias="X-Tenant-ID"),
    user_id: str = Header(alias="X-User-ID"),
    clinic_id: str = Header(alias="X-Clinic-ID"),
    _role: str = _brand_owner_required,
    session: AsyncSession = Depends(_get_db),
) -> SpecialistLinkDTO:
    """Link a doctor from the roster. Doctor not in roster → 404."""
    tenant = _tenant_uuid(tenant_id)
    clinic = _clinic_uuid(clinic_id)
    await _resolve_audit_actor(session, user_id)
    bundle = _build_service(session)
    try:
        link = await bundle.specialists.link(
            tenant_id=tenant,
            clinic_id=clinic,
            offer_id=offer_id,
            doctor_id=request.doctor_id,
        )
    except DoctorNotInRosterError as exc:
        raise HTTPException(status_code=404, detail="Doctor not in roster") from exc
    return SpecialistLinkDTO.model_validate(link)


@router.delete(
    "/servicios/{offer_id}/specialists/{doctor_id}",
    response_model=None,
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Unlink a doctor",
)
async def unlink_specialist(
    offer_id: UUID,
    doctor_id: UUID,
    tenant_id: str = Header(alias="X-Tenant-ID"),
    user_id: str = Header(alias="X-User-ID"),
    _role: str = _brand_owner_required,
    session: AsyncSession = Depends(_get_db),
) -> None:
    """Unlink a doctor (idempotent)."""
    tenant = _tenant_uuid(tenant_id)
    await _resolve_audit_actor(session, user_id)
    bundle = _build_service(session)
    await bundle.specialists.unlink(tenant_id=tenant, offer_id=offer_id, doctor_id=doctor_id)


# ============================================================
# Cases (PHI — consent gate + audit, X-Clinic-ID required)
# ============================================================


@router.post(
    "/servicios/{offer_id}/cases",
    response_model=CaseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Add a before/after case (HIPAA-lite consent gate + audit)",
)
async def create_case(
    offer_id: UUID,
    request: CaseCreateRequest,
    tenant_id: str = Header(alias="X-Tenant-ID"),
    user_id: str = Header(alias="X-User-ID"),
    clinic_id: str = Header(alias="X-Clinic-ID"),
    _role: str = _brand_owner_required,
    session: AsyncSession = Depends(_get_db),
) -> CaseDTO:
    """Create a case. consent_signed=False → 422 (RN-33); success writes audit row."""
    tenant = _tenant_uuid(tenant_id)
    clinic = _clinic_uuid(clinic_id)
    actor = await _resolve_audit_actor(session, user_id)
    bundle = _build_service(session)
    try:
        case = await bundle.proof.create_case(
            tenant_id=tenant,
            clinic_id=clinic,
            user_id=actor,
            offer_id=offer_id,
            before_asset_url=request.before_asset_url,
            after_asset_url=request.after_asset_url,
            consent_signed=request.consent_signed,
            consent_ref=request.consent_ref,
        )
    except ConsentNotSignedError as exc:
        raise HTTPException(status_code=422, detail="Consent not signed") from exc
    return CaseDTO.model_validate(case)


@router.delete(
    "/servicios/{offer_id}/cases/{case_id}",
    response_model=None,
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a case (audited)",
)
async def delete_case(
    offer_id: UUID,
    case_id: UUID,
    tenant_id: str = Header(alias="X-Tenant-ID"),
    user_id: str = Header(alias="X-User-ID"),
    clinic_id: str = Header(alias="X-Clinic-ID"),
    _role: str = _brand_owner_required,
    session: AsyncSession = Depends(_get_db),
) -> None:
    """Soft-delete a case + write an audit row."""
    tenant = _tenant_uuid(tenant_id)
    clinic = _clinic_uuid(clinic_id)
    actor = await _resolve_audit_actor(session, user_id)
    bundle = _build_service(session)
    await bundle.proof.delete_case(tenant_id=tenant, clinic_id=clinic, user_id=actor, case_id=case_id)


# ============================================================
# Testimonials (NOT PHI)
# ============================================================


@router.post(
    "/servicios/{offer_id}/testimonials",
    response_model=TestimonialDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Add a manual testimonial",
)
async def create_testimonial(
    offer_id: UUID,
    request: TestimonialCreateRequest,
    tenant_id: str = Header(alias="X-Tenant-ID"),
    user_id: str = Header(alias="X-User-ID"),
    _role: str = _brand_owner_required,
    session: AsyncSession = Depends(_get_db),
) -> TestimonialDTO:
    """Create a manual testimonial."""
    tenant = _tenant_uuid(tenant_id)
    await _resolve_audit_actor(session, user_id)
    bundle = _build_service(session)
    testimonial = await bundle.proof.create_testimonial(
        tenant_id=tenant,
        offer_id=offer_id,
        rating=request.rating,
        text=request.text,
        author=request.author,
        source=request.source,
    )
    return TestimonialDTO.model_validate(testimonial)


@router.delete(
    "/servicios/{offer_id}/testimonials/{testimonial_id}",
    response_model=None,
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a testimonial",
)
async def delete_testimonial(
    offer_id: UUID,
    testimonial_id: UUID,
    tenant_id: str = Header(alias="X-Tenant-ID"),
    user_id: str = Header(alias="X-User-ID"),
    _role: str = _brand_owner_required,
    session: AsyncSession = Depends(_get_db),
) -> None:
    """Soft-delete a testimonial (idempotent)."""
    tenant = _tenant_uuid(tenant_id)
    await _resolve_audit_actor(session, user_id)
    bundle = _build_service(session)
    await bundle.proof.delete_testimonial(tenant_id=tenant, testimonial_id=testimonial_id)


# ============================================================
# Sales brief (autosave + write-through)
# ============================================================


@router.patch(
    "/servicios/{offer_id}/sales-brief",
    response_model=SalesBriefDTO,
    summary="Sales-brief autosave + engine write-through",
)
async def patch_sales_brief(
    offer_id: UUID,
    request: SalesBriefPatchRequest,
    tenant_id: str = Header(alias="X-Tenant-ID"),
    user_id: str = Header(alias="X-User-ID"),
    _role: str = _brand_owner_required,
    session: AsyncSession = Depends(_get_db),
) -> SalesBriefDTO:
    """Patch the sales brief (per-field, idempotent autosave)."""
    tenant = _tenant_uuid(tenant_id)
    await _resolve_audit_actor(session, user_id)
    bundle = _build_service(session)
    fields = request.model_dump(exclude_unset=True)
    saved = await bundle.sales_brief.save(tenant_id=tenant, offer_id=offer_id, fields=fields)
    return SalesBriefDTO.model_validate(saved)


# ============================================================
# Knowledge extract — document → autocomplete (AC-11, NOT RAG)
# ============================================================


@router.post(
    "/servicios/{offer_id}/knowledge/extract",
    response_model=KnowledgeExtractResponse,
    summary="document→autocomplete (AC-11, NOT RAG)",
)
async def knowledge_extract(
    offer_id: UUID,
    request: KnowledgeExtractRequest,
    tenant_id: str = Header(alias="X-Tenant-ID"),
    user_id: str = Header(alias="X-User-ID"),
    _role: str = _brand_owner_required,
    session: AsyncSession = Depends(_get_db),
) -> KnowledgeExtractResponse:
    """Extract editable prefill from a document/URL + record the knowledge source."""
    tenant = _tenant_uuid(tenant_id)
    await _resolve_audit_actor(session, user_id)
    bundle = _build_service(session)
    try:
        result = await bundle.autocomplete.autocomplete(
            tenant_id=tenant,
            offer_id=offer_id,
            filename=request.filename,
            url=request.url,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return KnowledgeExtractResponse(
        source=KnowledgeSourceDTO(knowledge_source_id=result.knowledge_source_id),
        prefill=ExtractionPrefillDTO.model_validate(result.prefill),
    )
