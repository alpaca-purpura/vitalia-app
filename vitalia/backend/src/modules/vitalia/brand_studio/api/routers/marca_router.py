# cap: brand_studio.lisa-marca
# story-origin: vitalia-fase2-s7-TBD
"""Vitalia Brand Studio — Marca API Router (21 endpoints).

Endpoints served under /api/v1/lisa/marca/:
  GET  /initial-state/{subsubtab}      — SSR hydration per sub-sub-tab
  GET  /identity                       — Get brand identity
  PATCH /identity                      — Update identity (audit)
  GET  /visuals                        — Get brand visuals
  PATCH /visuals                       — Update visuals (audit)
  POST /logos                          — Upload logo (≤ 5 MB)
  DELETE /logos                        — Delete logo (soft · una marca = un logo)
  GET  /personality                    — Get personality compiler v2 blocks
  PATCH /personality                   — Update personality (audit + cache invalidate)
  GET  /contact                        — Get contact + social media
  PATCH /contact                       — Update contact (audit)
  GET  /team-preview                   — Read-only top-N team preview
  GET  /clinic-config                  — Read-only clinic_vertical + specialties
  GET  /voice-preview                  — Compile slot 5 BRAND_VOICE (cached)
  GET  /prohibited-phrases             — List seed defaults + tenant overrides
  POST /voice-warning-override         — Log override decision (audit row)
  GET  /trust-signals                  — List tenant trust signals
  POST /trust-signals                  — Add trust signal (audit)
  DELETE /trust-signals/{id}           — Soft-delete trust signal
  GET  /trust-catalog                  — Hybrid catalog per country

RBAC per 03-arch § 5.2:
  - GET endpoints: open to owner + admin_clinic (same as mutation roles — brand config)
  - PATCH/POST/DELETE: require_brand_owner_access() dependency (owner + admin_clinic)

Architecture per 03-arch § 5:
  - response_model= MANDATORY (arch test enforces + PII allowlist)
  - X-Tenant-ID header MANDATORY (tenant isolation raíz rule)
  - X-User-ID header MANDATORY (audit log writes)
  - X-User-Role header for RBAC (mutation endpoints)
  - clinic_id NOT required — brand config is owner-level (no PHI dual filter)
  - Audit log sync write BEFORE return on every mutation (defense-in-depth)
  - Fire-forget telemetry AFTER successful response (non-blocking)

Anti-creep guards:
  - NO health_voice_validator.py (arch test test_no_health_voice_validator.py)
  - NO brand_voice_summary mirror table (arch test test_no_brand_voice_summary_table.py)

downstream-regression-na: brand-local brand_studio router for vitalia
"""

from __future__ import annotations

from typing import Annotated, Any, Literal, NamedTuple
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, Header, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import get_async_session_committing
from src.modules.vitalia._shared.auth.rbac import require_brand_owner_access
from src.modules.vitalia._shared.telemetry.growth_studio_emitter import GrowthStudioEmitter
from src.modules.vitalia.audit.audit_writer import AsyncAuditWriter
from src.modules.vitalia.brand_studio.api.dtos.marca_dtos import (
    BrandContactDTO,
    BrandContactPatchDTO,
    BrandIdentityDTO,
    BrandIdentityPatchDTO,
    BrandPersonalityDTO,
    BrandPersonalityPatchDTO,
    BrandTeamPreviewDTO,
    BrandVisualsDTO,
    BrandVisualsPatchDTO,
    ClinicConfigDTO,
    LogoUploadResponseDTO,
    MarcaInitialStateDTO,
    ProhibitedPhrasesListDTO,
    TrustSignalCreateRequestDTO,
    TrustSignalDTO,
    TrustSignalsCatalogDTO,
    VoicePreviewDTO,
    VoiceWarningOverrideRequestDTO,
)
from src.modules.vitalia.brand_studio.application.services.marca_service import MarcaService
from src.modules.vitalia.brand_studio.application.services.trust_catalog_service import TrustCatalogService
from src.modules.vitalia.brand_studio.application.services.voice_blocklist_service import VoiceBlocklistService
from src.modules.vitalia.brand_studio.application.services.voice_preview_service import VoicePreviewService
from src.modules.vitalia.brand_studio.infrastructure.repositories.prohibited_phrase_repository_impl import (
    ProhibitedPhraseRepositoryImpl,
)
from src.modules.vitalia.brand_studio.infrastructure.repositories.trust_signal_repository_impl import (
    TrustSignalRepositoryImpl,
)
from src.modules.vitalia.iam.application.services.clinic_resolver import UserNotFoundError
from src.modules.vitalia.iam.application.services.user_resolver import resolve_user_uuid_from_clerk_id

logger = structlog.get_logger()

# ---- Sentinel clinic_id for brand_studio (owner-level config, no clinic context) ----
_NULL_CLINIC_ID = UUID(int=0)


async def _resolve_audit_actor(session: AsyncSession, user_id_header: str) -> UUID:
    """Resolve the X-User-ID header value to an IAM users.id UUID for the audit actor.

    Header-trust path (no JWT — this router auths via X-User-ID + X-User-Role headers):
      - If the value parses as a UUID → use it as-is (back-compat: internal callers /
        legacy tests that already send users.id).
      - Otherwise (= a Clerk userId string like "user_2abc...") → resolve clerk_id →
        users.id via the public iam resolver. No match → 422.

    Centralizes the if-UUID-else-resolve so every auditing endpoint uses one path
    (DRY — origin estabilizar-harness-e2e-lisa-marca / T-3 sub-bug #2b).

    Args:
        session: AsyncSession for the iam lookup.
        user_id_header: Raw X-User-ID header value (users.id UUID or Clerk userId).

    Returns:
        The IAM users.id UUID to record as the audit actor.

    Raises:
        HTTPException: 422 if the value is neither a valid UUID nor a known Clerk id.
    """
    try:
        return UUID(user_id_header)
    except ValueError:
        pass

    try:
        return await resolve_user_uuid_from_clerk_id(session, user_id_header)
    except UserNotFoundError as exc:
        raise HTTPException(status_code=422, detail="Invalid user_id") from exc


# ---- RBAC dependencies ----
# Mutation guard: owner + admin_clinic only
_brand_owner_required = Depends(require_brand_owner_access())

router = APIRouter(tags=["brand_studio"])


# ============================================================
# Dependency injection factories
# ============================================================


async def _get_db(
    session: Annotated[AsyncSession, Depends(get_async_session_committing)],
) -> AsyncSession:
    """Pass-through DI for AsyncSession.

    Uses get_async_session_committing so mutations (PATCH/POST/DELETE) are
    committed at the end of each request. GET routes write nothing so committing
    an empty transaction is a no-op.
    Fix: arreglar-guardado-voz-y-tono T-3.bis — personality PATCH was not committed.
    """
    return session


class _ServiceBundle(NamedTuple):
    """Named bundle of DI-constructed services for a single request."""

    marca: MarcaService
    voice_blocklist: VoiceBlocklistService
    trust_catalog: TrustCatalogService


def _build_service(session: AsyncSession) -> _ServiceBundle:
    """Build MarcaService and its collaborators from an async session.

    Constructs the full dependency tree for a single request:
      - AsyncAuditWriter (shared session)
      - GrowthStudioEmitter (shared session)
      - VoicePreviewService (stateless in-process cache)
      - VoiceBlocklistService + repo (F6 fix: returned publicly via NamedTuple)
      - TrustSignalRepository + service
      - MarcaService (orchestrator)

    Returns _ServiceBundle(marca, voice_blocklist, trust_catalog) — no private
    attribute access required at router layer (fixes auditor finding F6).
    """
    audit = AsyncAuditWriter(session=session)
    telemetry = GrowthStudioEmitter(session=session)
    voice_preview_svc = VoicePreviewService()
    phrase_repo = ProhibitedPhraseRepositoryImpl(session=session)
    voice_blocklist_svc = VoiceBlocklistService(repo=phrase_repo, audit=audit)
    trust_signal_repo = TrustSignalRepositoryImpl(session=session)
    trust_catalog_svc = TrustCatalogService()

    marca_svc = MarcaService(
        session=session,
        audit=audit,
        telemetry=telemetry,
        voice_preview_service=voice_preview_svc,
        voice_blocklist_service=voice_blocklist_svc,
        trust_signal_repo=trust_signal_repo,
        trust_catalog_service=trust_catalog_svc,
    )
    return _ServiceBundle(
        marca=marca_svc,
        voice_blocklist=voice_blocklist_svc,
        trust_catalog=trust_catalog_svc,
    )


# ============================================================
# Routes — SSR hydration
# ============================================================


@router.get(
    "/initial-state/{subsubtab}",
    response_model=MarcaInitialStateDTO,
    summary="SSR initial state per sub-sub-tab",
)
async def get_initial_state(
    subsubtab: Literal["identidad", "voz-y-tono", "presencia"],
    tenant_id: str = Header(alias="X-Tenant-ID"),
    user_id: str = Header(alias="X-User-ID"),
    user_role: str = Header(alias="X-User-Role", default=""),
    session: AsyncSession = Depends(_get_db),
) -> MarcaInitialStateDTO:
    """Return full hydration payload for a sub-sub-tab page (Server Component SSR).

    Per 03-arch § 5.1: SSR initial state is read-only and allows owner + admin_clinic.

    user_id is resolved via _resolve_audit_actor so SSR tolerates the real Clerk
    userId (T-2) the same way the auditing PATCH/POST/DELETE endpoints do — keeps the
    actor contract uniform even though this read writes no audit row.
    """
    try:
        tenant_uuid = UUID(tenant_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Invalid tenant_id") from exc
    user_uuid = await _resolve_audit_actor(session, user_id)

    bundle = _build_service(session)
    return await bundle.marca.get_initial_state(
        tenant_id=tenant_uuid,
        user_id=user_uuid,
        subsubtab=subsubtab,
    )


# ============================================================
# Routes — Identity
# ============================================================


@router.get(
    "/identity",
    response_model=BrandIdentityDTO,
    summary="Get brand identity (name, tagline, clinic_vertical)",
)
async def get_identity(
    tenant_id: str = Header(alias="X-Tenant-ID"),
    session: AsyncSession = Depends(_get_db),
) -> BrandIdentityDTO:
    """Return current brand identity for the tenant."""
    try:
        tenant_uuid = UUID(tenant_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Invalid tenant_id") from exc

    bundle = _build_service(session)
    return await bundle.marca.get_identity(tenant_id=tenant_uuid)


@router.patch(
    "/identity",
    response_model=BrandIdentityDTO,
    summary="Update brand identity (audit log)",
)
async def patch_identity(
    request: BrandIdentityPatchDTO,
    tenant_id: str = Header(alias="X-Tenant-ID"),
    user_id: str = Header(alias="X-User-ID"),
    _role: str = _brand_owner_required,
    session: AsyncSession = Depends(_get_db),
) -> BrandIdentityDTO:
    """Update brand name or tagline. Writes audit log row pre-response."""
    try:
        tenant_uuid = UUID(tenant_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Invalid tenant_id") from exc
    user_uuid = await _resolve_audit_actor(session, user_id)

    bundle = _build_service(session)
    return await bundle.marca.patch_identity(
        tenant_id=tenant_uuid,
        user_id=user_uuid,
        patch=request,
    )


# ============================================================
# Routes — Visuals
# ============================================================


@router.get(
    "/visuals",
    response_model=BrandVisualsDTO,
    summary="Get brand visuals (colors, fonts, logo)",
)
async def get_visuals(
    tenant_id: str = Header(alias="X-Tenant-ID"),
    session: AsyncSession = Depends(_get_db),
) -> BrandVisualsDTO:
    """Return brand visuals (primary/accent colors, fonts, logo URL)."""
    try:
        tenant_uuid = UUID(tenant_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Invalid tenant_id") from exc

    bundle = _build_service(session)
    return await bundle.marca.get_visuals(tenant_id=tenant_uuid)


@router.patch(
    "/visuals",
    response_model=BrandVisualsDTO,
    summary="Update brand visuals (audit log)",
)
async def patch_visuals(
    request: BrandVisualsPatchDTO,
    tenant_id: str = Header(alias="X-Tenant-ID"),
    user_id: str = Header(alias="X-User-ID"),
    _role: str = _brand_owner_required,
    session: AsyncSession = Depends(_get_db),
) -> BrandVisualsDTO:
    """Update brand colors or fonts. Writes audit log row pre-response."""
    try:
        tenant_uuid = UUID(tenant_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Invalid tenant_id") from exc
    user_uuid = await _resolve_audit_actor(session, user_id)

    bundle = _build_service(session)
    return await bundle.marca.patch_visuals(
        tenant_id=tenant_uuid,
        user_id=user_uuid,
        patch=request,
    )


@router.post(
    "/logos",
    response_model=LogoUploadResponseDTO,
    summary="Upload brand logo (≤ 5 MB)",
    status_code=status.HTTP_201_CREATED,
)
async def upload_logo(
    file: UploadFile,
    tenant_id: str = Header(alias="X-Tenant-ID"),
    user_id: str = Header(alias="X-User-ID"),
    _role: str = _brand_owner_required,
    session: AsyncSession = Depends(_get_db),
) -> LogoUploadResponseDTO:
    """Upload logo image (PNG/JPG/JPEG/WEBP, ≤ 5 MB).

    Server-side validation: format + size. Returns logo_url stored in brand config.
    """
    _MAX_LOGO_BYTES = 5 * 1024 * 1024  # 5 MB

    try:
        tenant_uuid = UUID(tenant_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Invalid tenant_id") from exc
    user_uuid = await _resolve_audit_actor(session, user_id)

    if file.content_type not in ("image/png", "image/jpeg", "image/jpg", "image/webp"):
        raise HTTPException(
            status_code=422,
            detail={"error_code": "LOGO_FORMAT_INVALID", "allowed": ["png", "jpg", "jpeg", "webp"]},
        )

    content = await file.read()
    if len(content) > _MAX_LOGO_BYTES:
        raise HTTPException(
            status_code=413,
            detail={"error_code": "LOGO_TOO_LARGE", "max_bytes": _MAX_LOGO_BYTES},
        )

    # Infer extension from content-type
    _ext_map: dict[str, str] = {
        "image/png": "png",
        "image/jpeg": "jpg",
        "image/jpg": "jpg",
        "image/webp": "webp",
    }
    ext = _ext_map.get(file.content_type or "", "jpg")

    bundle = _build_service(session)
    return await bundle.marca.upload_logo(
        tenant_id=tenant_uuid,
        user_id=user_uuid,
        content=content,
        ext=ext,
        size_bytes=len(content),
    )


@router.delete(
    "/logos",
    response_model=None,
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete brand logo (soft delete)",
)
async def delete_logo(
    tenant_id: str = Header(alias="X-Tenant-ID"),
    user_id: str = Header(alias="X-User-ID"),
    _role: str = _brand_owner_required,
    session: AsyncSession = Depends(_get_db),
) -> None:
    """Soft-delete the brand logo. Clears logo_url from brand config.

    Una marca tiene UN solo logo (visuals.logo_url) → la ruta no necesita {logo_id}
    en el path; el servicio lo desreferencia + lo borra del object storage por tenant.
    """
    try:
        tenant_uuid = UUID(tenant_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Invalid tenant_id") from exc
    user_uuid = await _resolve_audit_actor(session, user_id)

    bundle = _build_service(session)
    await bundle.marca.delete_logo(
        tenant_id=tenant_uuid,
        user_id=user_uuid,
    )


# ============================================================
# Routes — Personality (compiler v2 blocks)
# ============================================================


@router.get(
    "/personality",
    response_model=BrandPersonalityDTO,
    summary="Get brand personality compiler v2 blocks",
)
async def get_personality(
    tenant_id: str = Header(alias="X-Tenant-ID"),
    session: AsyncSession = Depends(_get_db),
) -> BrandPersonalityDTO:
    """Return brand personality (archetype + 6 compiler v2 blocks)."""
    try:
        tenant_uuid = UUID(tenant_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Invalid tenant_id") from exc

    bundle = _build_service(session)
    return await bundle.marca.get_personality(tenant_id=tenant_uuid)


@router.patch(
    "/personality",
    response_model=BrandPersonalityDTO,
    summary="Update personality blocks (audit + invalidate voice-preview cache)",
)
async def patch_personality(
    request: BrandPersonalityPatchDTO,
    tenant_id: str = Header(alias="X-Tenant-ID"),
    user_id: str = Header(alias="X-User-ID"),
    _role: str = _brand_owner_required,
    session: AsyncSession = Depends(_get_db),
) -> BrandPersonalityDTO:
    """Update one or more compiler v2 blocks. Writes audit log + invalidates voice preview cache."""
    try:
        tenant_uuid = UUID(tenant_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Invalid tenant_id") from exc
    user_uuid = await _resolve_audit_actor(session, user_id)

    bundle = _build_service(session)
    return await bundle.marca.patch_personality(
        tenant_id=tenant_uuid,
        user_id=user_uuid,
        patch=request,
    )


# ============================================================
# Routes — Contact + Social media
# ============================================================


@router.get(
    "/contact",
    response_model=BrandContactDTO,
    summary="Get brand contact and social media links",
)
async def get_contact(
    tenant_id: str = Header(alias="X-Tenant-ID"),
    session: AsyncSession = Depends(_get_db),
) -> BrandContactDTO:
    """Return brand contact info (website, social handles, Google Business URL)."""
    try:
        tenant_uuid = UUID(tenant_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Invalid tenant_id") from exc

    bundle = _build_service(session)
    return await bundle.marca.get_contact(tenant_id=tenant_uuid)


@router.patch(
    "/contact",
    response_model=BrandContactDTO,
    summary="Update contact and social media links (audit log)",
)
async def patch_contact(
    request: BrandContactPatchDTO,
    tenant_id: str = Header(alias="X-Tenant-ID"),
    user_id: str = Header(alias="X-User-ID"),
    _role: str = _brand_owner_required,
    session: AsyncSession = Depends(_get_db),
) -> BrandContactDTO:
    """Update website URL or social handles. Writes audit log row pre-response."""
    try:
        tenant_uuid = UUID(tenant_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Invalid tenant_id") from exc
    user_uuid = await _resolve_audit_actor(session, user_id)

    bundle = _build_service(session)
    return await bundle.marca.patch_contact(
        tenant_id=tenant_uuid,
        user_id=user_uuid,
        patch=request,
    )


# ============================================================
# Routes — Team preview (read-only)
# ============================================================


@router.get(
    "/team-preview",
    response_model=BrandTeamPreviewDTO,
    summary="Read-only top-N team preview (sub-sub-tab Identidad)",
)
async def get_team_preview(
    tenant_id: str = Header(alias="X-Tenant-ID"),
    limit: int = Query(default=3, ge=1, le=10),
    session: AsyncSession = Depends(_get_db),
) -> BrandTeamPreviewDTO:
    """Return top-N team member preview. CRUD lives in lisa-doctores story (future)."""
    try:
        tenant_uuid = UUID(tenant_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Invalid tenant_id") from exc

    bundle = _build_service(session)
    return await bundle.marca.get_team_preview(
        tenant_id=tenant_uuid,
        limit=limit,
    )


# ============================================================
# Routes — Clinic config (read-only)
# ============================================================


@router.get(
    "/clinic-config",
    response_model=ClinicConfigDTO,
    summary="Read-only clinic_vertical + primary_specialties (captured in onboarding)",
)
async def get_clinic_config(
    tenant_id: str = Header(alias="X-Tenant-ID"),
    session: AsyncSession = Depends(_get_db),
) -> ClinicConfigDTO:
    """Return clinic_vertical and primary_specialties configured during onboarding."""
    try:
        tenant_uuid = UUID(tenant_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Invalid tenant_id") from exc

    bundle = _build_service(session)
    return await bundle.marca.get_clinic_config(tenant_id=tenant_uuid)


# ============================================================
# Routes — Voice preview (sub-sub-tab Voz)
# ============================================================


@router.get(
    "/voice-preview",
    response_model=VoicePreviewDTO,
    summary="Compile slot 5 BRAND_VOICE preview (server-side LRU cache)",
)
async def get_voice_preview(
    tenant_id: str = Header(alias="X-Tenant-ID"),
    session: AsyncSession = Depends(_get_db),
) -> VoicePreviewDTO:
    """Compile BRAND_VOICE slot 5 deterministically.

    Uses PersonalityCompiler.compile() from engine (zero LLM dispatch).
    Response cached in-process LRU bounded 1000 entries.
    Cache invalidated on PATCH /personality.
    """
    try:
        tenant_uuid = UUID(tenant_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Invalid tenant_id") from exc

    bundle = _build_service(session)
    return await bundle.marca.get_voice_preview(tenant_id=tenant_uuid)


# ============================================================
# Routes — Prohibited phrases (voice blocklist)
# ============================================================


@router.get(
    "/prohibited-phrases",
    response_model=ProhibitedPhrasesListDTO,
    summary="List seed defaults + tenant overrides (soft warning UI)",
)
async def get_prohibited_phrases(
    tenant_id: str = Header(alias="X-Tenant-ID"),
    user_id: str | None = Header(alias="X-User-ID", default=None),
    country: str | None = Query(default=None, max_length=2, description="ISO 3166-1 alpha-2 (e.g. PE)"),
    session: AsyncSession = Depends(_get_db),
) -> ProhibitedPhrasesListDTO:
    """Return configurable voice blocklist (seed defaults + tenant overrides).

    Per anti-creep rule: NO LLM validator — soft warning only.
    UI shows warning + suggested_alternative + allows override with audit log.

    X-User-ID is OPTIONAL here (sub-bug #1, T-3): this is a read keyed by tenant +
    country, it writes no audit row, so no actor is needed. The browser's fetchClient
    never injects X-User-ID → it must not 422. X-Tenant-ID stays required
    (tenant-isolation). `user_id` is intentionally not parsed nor used.
    """
    del user_id  # accepted-but-unused: read keyed by tenant + country (no audit, no actor)
    try:
        tenant_uuid = UUID(tenant_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Invalid tenant_id") from exc

    bundle = _build_service(session)
    return await bundle.voice_blocklist.list_for_tenant(
        tenant_id=tenant_uuid,
        country=country,
    )


@router.post(
    "/voice-warning-override",
    response_model=dict[str, Any],
    summary="Log override decision when user proceeds despite voice warning",
)
async def post_voice_warning_override(
    request: VoiceWarningOverrideRequestDTO,
    tenant_id: str = Header(alias="X-Tenant-ID"),
    user_id: str = Header(alias="X-User-ID"),
    _role: str = _brand_owner_required,
    session: AsyncSession = Depends(_get_db),
) -> dict[str, Any]:
    """Write audit_log row action='voice_warning_overridden'.

    Returns {audit_id: UUID}. Override is always permitted — soft warning policy.
    """
    try:
        tenant_uuid = UUID(tenant_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Invalid tenant_id") from exc
    user_uuid = await _resolve_audit_actor(session, user_id)

    bundle = _build_service(session)
    audit_id = await bundle.voice_blocklist.log_warning_override(
        tenant_id=tenant_uuid,
        user_id=user_uuid,
        request=request,
    )

    # Fire-forget telemetry (non-blocking)
    try:
        telemetry = GrowthStudioEmitter(session=session)
        await telemetry.emit_event(
            event_type="lisa_marca_voice_warning_overridden",
            tenant_id=tenant_uuid,
            user_id=user_uuid,
            props={"section": request.section},
        )
    except Exception:  # noqa: BLE001
        logger.warning("telemetry_emit_failed_voice_override", tenant_id=str(tenant_uuid))

    return {"audit_id": str(audit_id)}


# ============================================================
# Routes — Trust signals
# ============================================================


@router.get(
    "/trust-signals",
    response_model=list[TrustSignalDTO],
    summary="List tenant trust signals (certifications, authorities)",
)
async def get_trust_signals(
    tenant_id: str = Header(alias="X-Tenant-ID"),
    user_id: str | None = Header(alias="X-User-ID", default=None),
    session: AsyncSession = Depends(_get_db),
) -> list[TrustSignalDTO]:
    """Return all non-deleted trust signals for the tenant.

    Read endpoint — X-User-ID optional (fetchClient no lo inyecta en GETs). Resuelve
    el actor sólo si viene; el read es tenant-scoped (origin sub-bug #1 extendido,
    estabilizar-harness-e2e-lisa-marca: el de-mock reveló el 422 en browser real).
    """
    try:
        tenant_uuid = UUID(tenant_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Invalid tenant_id") from exc
    user_uuid = await _resolve_audit_actor(session, user_id) if user_id else None

    bundle = _build_service(session)
    return await bundle.marca.get_trust_signals(tenant_id=tenant_uuid, user_id=user_uuid)  # type: ignore[return-value]


@router.post(
    "/trust-signals",
    response_model=TrustSignalDTO,
    summary="Add trust signal (audit log)",
    status_code=status.HTTP_201_CREATED,
)
async def create_trust_signal(
    request: TrustSignalCreateRequestDTO,
    tenant_id: str = Header(alias="X-Tenant-ID"),
    user_id: str = Header(alias="X-User-ID"),
    _role: str = _brand_owner_required,
    session: AsyncSession = Depends(_get_db),
) -> TrustSignalDTO:
    """Add a new trust signal (from hybrid catalog or free-text). Writes audit log."""
    try:
        tenant_uuid = UUID(tenant_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Invalid tenant_id") from exc
    user_uuid = await _resolve_audit_actor(session, user_id)

    bundle = _build_service(session)
    return await bundle.marca.create_trust_signal(
        tenant_id=tenant_uuid,
        user_id=user_uuid,
        request=request,
    )


@router.delete(
    "/trust-signals/{signal_id}",
    response_model=None,
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-delete trust signal",
)
async def delete_trust_signal(
    signal_id: UUID,
    tenant_id: str = Header(alias="X-Tenant-ID"),
    user_id: str = Header(alias="X-User-ID"),
    _role: str = _brand_owner_required,
    session: AsyncSession = Depends(_get_db),
) -> None:
    """Soft-delete (set deleted_at) a trust signal. Writes audit log."""
    try:
        tenant_uuid = UUID(tenant_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Invalid tenant_id") from exc
    user_uuid = await _resolve_audit_actor(session, user_id)

    bundle = _build_service(session)
    await bundle.marca.delete_trust_signal(
        tenant_id=tenant_uuid,
        user_id=user_uuid,
        signal_id=signal_id,
    )


# ============================================================
# Routes — Trust catalog (hybrid catalog per country)
# ============================================================


@router.get(
    "/trust-catalog",
    response_model=TrustSignalsCatalogDTO,
    summary="Hybrid catalog of known authorities per country (OQ-D resolution)",
)
async def get_trust_catalog(
    tenant_id: str = Header(alias="X-Tenant-ID"),
    user_id: str | None = Header(alias="X-User-ID", default=None),  # noqa: ARG001 — read, X-User-ID opcional (no se usa)
    country: str = Query(default="PE", max_length=2, description="ISO 3166-1 alpha-2 (e.g. PE)"),
    session: AsyncSession = Depends(_get_db),
) -> TrustSignalsCatalogDTO:
    """Return hybrid catalog (closed set + free-text) for a country.

    PE: 8 entries (DIGESA, MINSA, SUSALUD, COP_ODONTO, CMP, SUNAT, ISO_9001, ESSALUD).
    AR/CL/CO/MX/BR: empty (populated in future stories).

    Read endpoint — X-User-ID opcional e ignorado (origin sub-bug #1 extendido,
    estabilizar-harness-e2e-lisa-marca: el de-mock reveló el 422 en browser real).
    """
    try:
        UUID(tenant_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Invalid tenant_id") from exc

    trust_catalog_svc = TrustCatalogService()
    return await trust_catalog_svc.get_catalog(country=country)
