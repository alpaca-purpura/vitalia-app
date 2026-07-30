# cap: clinics.lisa.doctores
"""Doctors API router — FastAPI thin layer.

Routes (all under prefix /api/v1/vitalia/clinics/doctors):
  GET  /                         — list doctors (masked, paginated)
  POST /                         — create doctor (validate credential, 409 if DNI dup)
  GET  /{id}                     — get doctor detail (owner / admin_clinic)
  PATCH /{id}                    — patch doctor (bio/active/visible/avatar_key)

Architecture rules (03-arch-be.md § 4 + ADR-vitalia-004):
  - response_model= MANDATORY on all routes (arch test enforces)
  - X-Tenant-ID + X-User-ID + X-User-Role headers required
  - No business logic in router — delegate to DoctorService
  - Map domain exceptions: DniConflictError → 409, CredentialValidationError → 422
  - PHI never in URL params (hipaa-lite.md § Anti-patterns)
  - redirect_slashes=False enforced at app level in main.py
  - RBAC: staff mutations require {owner, admin_clinic} (_STAFF_MUTATION_ROLES via
    require_brand_owner_access) — owner manages the staff roster (Chris #3b 2026-06-06)
"""

from __future__ import annotations

from datetime import date
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.vitalia._shared.auth.rbac import require_brand_owner_access
from src.modules.vitalia._shared.phi_masking import mask_dni, mask_email, mask_phone
from src.modules.vitalia._shared.repositories.audit_log_repository import AuditLogRepository
from src.modules.vitalia._shared.telemetry.growth_studio_emitter import GrowthStudioEmitter
from src.modules.vitalia.clinics.api.dtos import (
    AvailabilityBlockDTO,
    AvailabilityBlocksResponse,
    AvailabilityOccurrenceDTO,
    AvailabilityOccurrencesResponse,
    BioFileDeleteResponse,
    BioFileDTO,
    BioFileRegisterRequest,
    BioFilesResponse,
    BioPublicDTO,
    DeleteBlockResponse,
    DoctorCreateRequest,
    DoctorDetailDTO,
    DoctorListItemDTO,
    DoctorListResponse,
    DoctorPatchRequest,
    ExperienciaItemDTO,
    FormacionItemDTO,
    GenerateBioRequest,
    GenerateBioResponse,
    GenerateProfileResponse,
    OneOffBlockCreateRequest,
    PatchPublicProfileRequest,
    ProfileStateDTO,
    PublicDoctorProfileDTO,
    RecurrentBlockCreateRequest,
)
from src.modules.vitalia.clinics.application.availability_block_service import (
    AvailabilityBlockService,
)
from src.modules.vitalia.clinics.application.bio_file_service import (
    BioFileService,
    BioFileStorageError,
)
from src.modules.vitalia.clinics.application.bio_generation_service import BioGenerationService
from src.modules.vitalia.clinics.application.credential_validator import CredentialValidationError
from src.modules.vitalia.clinics.application.doctor_service import (
    DniConflictError,
    DoctorService,
    _slugify,
)
from src.modules.vitalia.clinics.domain.availability_block import AvailabilityBlock
from src.modules.vitalia.clinics.domain.bio import BioPublic
from src.modules.vitalia.clinics.domain.bio_file import DoctorBioFile
from src.modules.vitalia.clinics.domain.doctor import Doctor
from src.modules.vitalia.clinics.infrastructure.repositories.availability_block_repository import (
    AvailabilityBlockRepository,
)
from src.modules.vitalia.clinics.infrastructure.repositories.doctor_bio_file_repository import (
    DoctorBioFileRepository,
)
from src.modules.vitalia.clinics.infrastructure.repositories.doctor_repository import (
    DoctorRepository,
)

logger = structlog.get_logger()

router = APIRouter(tags=["staff"])

# Allowed roles for staff (doctor) mutations: owner + admin_clinic.
# Decision Chris 2026-06-06 (#3b, story vitalia-fase2-lisa-doctores): the clinic
# OWNER manages the staff roster (business-roster data, not patient PHI), mirroring
# the marca/brand-config module ({owner, admin_clinic}). Widened from the previous
# admin_clinic-only set, which left the clinic owner unable to add staff + created a
# bootstrap chicken-egg (who creates the first admin_clinic?). See hipaa-lite.md § RBAC.
_STAFF_MUTATION_ROLES: frozenset[str] = frozenset(["owner", "admin_clinic"])


async def _get_db() -> AsyncSession:
    """Async DB session dependency."""
    from src.db import get_async_session  # noqa: PLC0415

    async for session in get_async_session():
        yield session


def _build_service(db: AsyncSession) -> DoctorService:
    """Build DoctorService with injected repos."""
    repo = DoctorRepository(session=db)
    audit = AuditLogRepository(session=db)
    emitter = GrowthStudioEmitter(session=db)
    return DoctorService(doctor_repo=repo, audit_repo=audit, emitter=emitter)


def _build_block_service(db: AsyncSession) -> AvailabilityBlockService:
    """Build AvailabilityBlockService with injected repos."""
    block_repo = AvailabilityBlockRepository(session=db)
    audit = AuditLogRepository(session=db)
    return AvailabilityBlockService(block_repo=block_repo, audit_repo=audit)


def _build_bio_file_service(db: AsyncSession) -> BioFileService:
    """Build BioFileService with injected repos (delta v3 D3-B)."""
    bio_file_repo = DoctorBioFileRepository(session=db)
    doctor_repo = DoctorRepository(session=db)
    audit = AuditLogRepository(session=db)
    return BioFileService(bio_file_repo=bio_file_repo, doctor_repo=doctor_repo, audit_repo=audit)


def _compute_profile_state(
    doctor: Doctor,
    bio_files: list,
) -> "ProfileStateDTO | None":
    """Compute ProfileStateDTO from doctor bio_generated_at and bio_files.

    Returns None when bio_generated_at is None (profile never generated).
    material_new: True when any bio_file was uploaded AFTER bio_generated_at.
    material_new_count: count of such files.

    Limitation (RN-D3D-4 partial): notes/links changes do NOT bump material_new
    (no dedicated timestamp for those fields). Files only. Docstring reflects this.
    """
    if doctor.bio_generated_at is None:
        return None

    new_files = [f for f in bio_files if f.uploaded_at > doctor.bio_generated_at]
    count = len(new_files)
    return ProfileStateDTO(
        generated_at=doctor.bio_generated_at,
        material_new=count > 0,
        material_new_count=count,
    )


def _build_clinic_repository(db):  # noqa: ANN001, ANN202
    """Builder patcheable (patrón _build_* del router) — clinic slug para URL pública D3-D."""
    from src.modules.vitalia.clinics.infrastructure.repositories.clinic_repository import (  # noqa: PLC0415
        ClinicRepository,
    )

    return ClinicRepository(db)


def _to_detail_dto(doctor: Doctor, bio_files: list | None = None, clinic_slug: str | None = None) -> DoctorDetailDTO:
    """Map Doctor domain entity → DoctorDetailDTO.

    Args:
        doctor: Domain entity with decrypted PHI fields.
        bio_files: List of DoctorBioFile entities for profile_state computation.
            If None (e.g., POST create), bio_files defaults to [] and profile_state
            is computed from doctor.bio_generated_at alone (no file comparison).
    """
    if bio_files is None:
        bio_files = []

    bio_dto = None
    if doctor.bio_public is not None:
        bio_dto = BioPublicDTO(
            resumen=doctor.bio_public.resumen,
            formacion=doctor.bio_public.formacion,
            enfoque=doctor.bio_public.enfoque,
        )

    public_profile_dto = _to_public_profile_dto(doctor)
    profile_state_dto = _compute_profile_state(doctor, bio_files)

    return DoctorDetailDTO(
        id=doctor.id,
        tenant_id=doctor.tenant_id,
        clinic_id=doctor.clinic_id,
        first_name=doctor.first_name,
        last_name=doctor.last_name,
        display_name=doctor.display_name,
        dni=doctor.dni,
        email=doctor.email,
        phone=doctor.phone,
        specialty=doctor.specialty,
        credential=doctor.credential,
        credential_country=doctor.credential_country,
        years_experience=doctor.years_experience,
        languages=doctor.languages,
        bio_inputs_notes=doctor.bio_inputs_notes,
        bio_links=doctor.bio_links,
        bio_public=bio_dto,
        avatar_key=doctor.avatar_key,
        visible_en_landing=doctor.visible_en_landing,
        active=doctor.active,
        created_at=doctor.created_at,
        updated_at=doctor.updated_at,
        public_profile=public_profile_dto,
        public_slug=doctor.public_slug,
        profile_state=profile_state_dto,
        clinic_slug=clinic_slug,
    )


def _to_list_item(doctor: Doctor) -> DoctorListItemDTO:
    """Map Doctor domain entity → DoctorListItemDTO (PHI masked).

    first_name/last_name included for FE StaffCard (03-arch-fe § TypeScript Types).
    patients_count/nps_score: None until appointments/analytics wired (post-MVP).
    """
    return DoctorListItemDTO(
        id=doctor.id,
        tenant_id=doctor.tenant_id,
        clinic_id=doctor.clinic_id,
        first_name=doctor.first_name,
        last_name=doctor.last_name,
        display_name=doctor.display_name,
        specialty=doctor.specialty,
        active=doctor.active,
        visible_en_landing=doctor.visible_en_landing,
        years_experience=doctor.years_experience,
        languages=doctor.languages,
        avatar_key=doctor.avatar_key,
        patients_count=None,  # populated by appointments module (post-MVP)
        nps_score=None,  # populated by analytics module (post-MVP)
        masked_dni=mask_dni(doctor.dni) if doctor.dni else None,
        masked_email=mask_email(doctor.email) if doctor.email else None,
        masked_phone=mask_phone(doctor.phone) if doctor.phone else None,
        created_at=doctor.created_at,
    )


@router.get("", response_model=DoctorListResponse, response_model_by_alias=True, include_in_schema=False)
@router.get("/", response_model=DoctorListResponse, response_model_by_alias=True)
async def list_doctors(
    tenant_id: UUID = Header(alias="X-Tenant-ID"),
    clinic_id: UUID = Header(alias="X-Clinic-ID"),
    q: str | None = Query(default=None),
    specialty: str | None = Query(default=None),
    active: bool | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=24, ge=1, le=100),
    db: AsyncSession = Depends(_get_db),
) -> DoctorListResponse:
    """List all doctors for a clinic — paginated, PHI masked.

    SC-6: list scoped to tenant+clinic (dual filter).
    SC-9: large dataset — server-side pagination.
    `q`: free-text search over name + specialty (directory search box).
    Headers typed as UUID — FastAPI validates and returns 422 for invalid values.
    """
    service = _build_service(db)
    doctors, total = await service.list_doctors(
        tenant_id=tenant_id,
        clinic_id=clinic_id,
        q=q,
        specialty=specialty,
        active=active,
        page=page,
        page_size=page_size,
    )
    items = [_to_list_item(d) for d in doctors]
    return DoctorListResponse(items=items, total=total, page=page, page_size=page_size)


@router.post(
    "",
    response_model=DoctorDetailDTO,
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
    dependencies=[Depends(require_brand_owner_access(roles=_STAFF_MUTATION_ROLES))],
)
@router.post(
    "/",
    response_model=DoctorDetailDTO,
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_brand_owner_access(roles=_STAFF_MUTATION_ROLES))],
)
async def create_doctor(
    request: DoctorCreateRequest,
    tenant_id: UUID = Header(alias="X-Tenant-ID"),
    clinic_id: UUID = Header(alias="X-Clinic-ID"),
    user_id: UUID = Header(alias="X-User-ID"),
    db: AsyncSession = Depends(_get_db),
) -> DoctorDetailDTO:
    """Create a new doctor in the clinic staff directory.

    SC-2: invalid credential → 422 with Spanish neutro error message.
    SC-5: duplicate DNI → 409 Conflict.
    Headers typed as UUID — FastAPI validates and returns 422 for invalid values.
    """
    service = _build_service(db)
    try:
        doctor = await service.create_doctor(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            user_id=user_id,
            first_name=request.first_name,
            last_name=request.last_name,
            dni=request.dni,
            email=request.email,
            phone=request.phone,
            specialty=request.specialty,
            credential=request.credential,
            credential_country=request.credential_country,
            years_experience=request.years_experience,
            languages=request.languages,
        )
    except CredentialValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error": "credential_invalid", "field": exc.field, "message": exc.message},
        ) from exc
    except DniConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": "dni_conflict", "message": exc.message},
        ) from exc

    await db.commit()
    return _to_detail_dto(doctor)


@router.get("/{doctor_id}", response_model=DoctorDetailDTO, response_model_by_alias=True)
async def get_doctor(
    doctor_id: UUID,
    tenant_id: UUID = Header(alias="X-Tenant-ID"),
    clinic_id: UUID = Header(alias="X-Clinic-ID"),
    user_id: UUID = Header(alias="X-User-ID"),
    db: AsyncSession = Depends(_get_db),
) -> DoctorDetailDTO:
    """Get doctor detail (admin_clinic role required).

    SC-4: cross-tenant access → 404 generic (audit written internally).
    Loads bio_files for profile_state computation (material_new detection RN-D3D-4).
    Headers typed as UUID — FastAPI validates and returns 422 for invalid values.
    """
    service = _build_service(db)
    doctor = await service.get_doctor(
        doctor_id=doctor_id,
        tenant_id=tenant_id,
        clinic_id=clinic_id,
        user_id=user_id,
    )
    if doctor is None:
        await db.commit()  # flush audit log entry
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "doctor_not_found", "message": "Médico no encontrado."},
        )
    # Load bio_files for profile_state.material_new computation (RN-D3D-4).
    # Files are promotional material (CV/diploma), not PHI — no audit log for this read.
    bio_file_svc = _build_bio_file_service(db)
    bio_files = await bio_file_svc.list_files(
        tenant_id=tenant_id,
        clinic_id=clinic_id,
        doctor_id=doctor_id,
    )
    # clinic_slug para que el FE construya la URL pública /d/{clinic}/{doctor} (D3-D)
    clinic = await _build_clinic_repository(db).get_by_id(tenant_id=tenant_id, clinic_id=clinic_id)
    await db.commit()
    return _to_detail_dto(doctor, bio_files=bio_files, clinic_slug=clinic.slug if clinic else None)


def _to_block_dto(block: AvailabilityBlock) -> AvailabilityBlockDTO:
    """Map AvailabilityBlock domain entity -> AvailabilityBlockDTO."""
    return AvailabilityBlockDTO(
        id=block.id,
        tenant_id=block.tenant_id,
        clinic_id=block.clinic_id,
        doctor_id=block.doctor_id,
        kind=block.kind,
        start_time=block.start_time,
        end_time=block.end_time,
        day_of_week=block.day_of_week,
        freq=block.freq,
        end_condition_kind=block.end_condition_kind,
        end_date=block.end_date,
        occurrences=block.occurrences,
        specific_date=block.specific_date,
        created_at=block.created_at,
        updated_at=block.updated_at,
    )


@router.patch(
    "/{doctor_id}",
    response_model=DoctorDetailDTO,
    response_model_by_alias=True,
    dependencies=[Depends(require_brand_owner_access(roles=_STAFF_MUTATION_ROLES))],
)
async def patch_doctor(
    doctor_id: UUID,
    request: DoctorPatchRequest,
    tenant_id: UUID = Header(alias="X-Tenant-ID"),
    clinic_id: UUID = Header(alias="X-Clinic-ID"),
    user_id: UUID = Header(alias="X-User-ID"),
    db: AsyncSession = Depends(_get_db),
) -> DoctorDetailDTO:
    """Patch doctor mutable fields (bio, active, visible, avatar_key).

    Autosave-friendly: accepts partial payload.
    Audit: doctor.updated or doctor.deactivated.
    Headers typed as UUID — FastAPI validates and returns 422 for invalid values.
    """
    # Map DTO bio to domain BioPublic if provided
    bio_public: BioPublic | None = None
    if request.bio_public is not None:
        bio_public = BioPublic(
            resumen=request.bio_public.resumen,
            formacion=request.bio_public.formacion,
            enfoque=request.bio_public.enfoque,
        )

    service = _build_service(db)
    doctor = await service.update_doctor(
        doctor_id=doctor_id,
        tenant_id=tenant_id,
        clinic_id=clinic_id,
        user_id=user_id,
        phone=request.phone,
        bio_inputs_notes=request.bio_inputs_notes,
        bio_links=request.bio_links,
        bio_public=bio_public,
        avatar_key=request.avatar_key,
        visible_en_landing=request.visible_en_landing,
        active=request.active,
        specialty=request.specialty,
        years_experience=request.years_experience,
        languages=request.languages,
    )
    if doctor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "doctor_not_found", "message": "Médico no encontrado."},
        )
    await db.commit()
    return _to_detail_dto(doctor)


# ── Bio generation endpoint (T-BE-4) ─────────────────────────────────────────


@router.post(
    "/{doctor_id}/generate-bio",
    response_model=GenerateBioResponse,
    dependencies=[Depends(require_brand_owner_access(roles=_STAFF_MUTATION_ROLES))],
)
async def generate_doctor_bio(
    doctor_id: UUID,
    request: GenerateBioRequest,  # noqa: ARG001 — empty body, kept for explicit schema
    tenant_id: UUID = Header(alias="X-Tenant-ID"),
    clinic_id: UUID = Header(alias="X-Clinic-ID"),
    user_id: UUID = Header(alias="X-User-ID"),  # noqa: ARG001 — kept for RBAC audit trace
    db: AsyncSession = Depends(_get_db),
) -> GenerateBioResponse:
    """Generate public bio from stored inputs (single-shot extractive, NOT agentic).

    03-arch D-4: deterministic single-shot LLM call — uses ONLY provided material
    (bio_inputs_notes + bio_links). Does NOT invent content.

    Anti-invent guardrail: if info missing → section is empty, never hallucinated.
    Output: 3 editable sections (resumen, formacion, enfoque) stored in bio_public.

    Graceful fallback (tessl__graceful-degradation):
      - LLM fail or timeout → returns empty sections + error_message (HTTP 200)
      - Does NOT break autosave of rest of doctor profile
      - FE shows error_message as toast notification

    PHI note: bio_inputs_notes/bio_links are promotional material (CV/diploma),
    NOT clinical patient PHI. Audit log NOT written (non-PHI endpoint).

    V-FN-9: bio-gen produces sections ONLY from provided material; fallback on fail.
    """
    service = _build_service(db)
    doctor = await service.get_doctor(
        doctor_id=doctor_id,
        tenant_id=tenant_id,
        clinic_id=clinic_id,
        user_id=user_id,
    )
    if doctor is None:
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "doctor_not_found", "message": "Médico no encontrado."},
        )

    # BioGenerationService: deterministic extractive (D-4) — NOT copilot/sales_agent
    bio_svc = BioGenerationService()
    bio, error_message = bio_svc.generate_with_error(doctor)

    if error_message is None:
        logger.info(
            "bio_generated",
            doctor_id=str(doctor_id),
            tenant_id=tenant_id,
            sections_filled=sum(1 for s in [bio.resumen, bio.formacion, bio.enfoque] if s),
        )
    else:
        logger.warning(
            "bio_generation_fallback",
            doctor_id=str(doctor_id),
            tenant_id=tenant_id,
        )

    bio_dto = BioPublicDTO(
        resumen=bio.resumen,
        formacion=bio.formacion,
        enfoque=bio.enfoque,
    )
    await db.commit()
    return GenerateBioResponse(bio=bio_dto, error_message=error_message)


# ── Structured profile generation endpoint (T-BE-generate-profile) ───────────


def _to_public_profile_dto(doctor: "Doctor") -> "PublicDoctorProfileDTO | None":
    """Map Doctor.public_profile (DoctorPublicProfile) → PublicDoctorProfileDTO.

    Returns None if doctor has no public_profile set yet.
    """
    pp = doctor.public_profile
    if pp is None:
        return None

    formacion = [
        FormacionItemDTO(
            titulo=item.get("titulo", "") if isinstance(item, dict) else "",
            institucion=item.get("institucion", "") if isinstance(item, dict) else "",
            anio=item.get("anio") if isinstance(item, dict) else None,
        )
        for item in (pp.formacion or [])
    ]
    experiencia = [
        ExperienciaItemDTO(
            puesto=item.get("puesto", "") if isinstance(item, dict) else "",
            lugar=item.get("lugar", "") if isinstance(item, dict) else "",
            anios=item.get("anios") if isinstance(item, dict) else None,
        )
        for item in (pp.experiencia or [])
    ]

    return PublicDoctorProfileDTO(
        display_name=doctor.display_name,
        specialty=doctor.specialty,
        avatar_key=doctor.avatar_key,
        sobre_mi=pp.sobre_mi,
        formacion=formacion or None,
        experiencia=experiencia or None,
        tratamientos=pp.tratamientos or None,
        certificaciones=pp.certificaciones or None,
        idiomas=pp.idiomas or None,
    )


@router.post(
    "/{doctor_id}/generate-profile",
    response_model=GenerateProfileResponse,
    response_model_by_alias=True,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_brand_owner_access(roles=_STAFF_MUTATION_ROLES))],
)
async def generate_doctor_profile(
    doctor_id: UUID,
    tenant_id: UUID = Header(alias="X-Tenant-ID"),
    clinic_id: UUID = Header(alias="X-Clinic-ID"),
    user_id: UUID = Header(alias="X-User-ID"),
    db: AsyncSession = Depends(_get_db),
) -> GenerateProfileResponse:
    """Generate structured 6-section public profile from stored bio material.

    T-BE-generate-profile (vitalia-fase2-lisa-doctores story).

    Loads doctor + bio material (bio_inputs_notes + bio_links + bio_files filenames),
    calls BioGenerationService.generate_structured() to produce DoctorPublicProfile,
    persists public_profile JSONB + bio_generated_at + public_slug (if not set),
    writes audit log (doctor.profile_generated) SYNC, returns profile + generated_at.

    Deterministic extractive (D-4): same no-invent style as generate-bio.
    Empty sections (no material) → None/[] per RN-D3D-6 — no error.

    RBAC: {owner, admin_clinic} (staff mutation roles).
    Audit: doctor.profile_generated (HIPAA-lite sync write).
    DO NOT touch generate-bio legacy endpoint (backward compat).
    """
    service = _build_service(db)

    # 1. Load doctor (dual filter: tenant+clinic)
    doctor = await service.get_doctor(
        doctor_id=doctor_id,
        tenant_id=tenant_id,
        clinic_id=clinic_id,
        user_id=user_id,
    )
    if doctor is None:
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "doctor_not_found", "message": "Médico no encontrado."},
        )

    # 2. Load bio file filenames (filenames only — not URLs, not PHI)
    bio_file_svc = _build_bio_file_service(db)
    bio_files = await bio_file_svc.list_files(
        doctor_id=doctor_id,
        tenant_id=tenant_id,
        clinic_id=clinic_id,
    )
    bio_file_filenames = [f.filename for f in bio_files if f.filename]

    # 3. Generate structured profile (graceful degradation: never raises)
    bio_svc = BioGenerationService()
    profile = bio_svc.generate_structured(
        doctor=doctor,
        bio_file_filenames=bio_file_filenames,
    )

    # 4. Compute public_slug if doctor doesn't have one yet
    slug = doctor.public_slug
    if slug is None:
        slug = _slugify(doctor.display_name)

    # 5. Persist profile + bio_generated_at + slug (audit written sync in service)
    updated = await service.generate_public_profile(
        doctor_id=doctor_id,
        tenant_id=tenant_id,
        clinic_id=clinic_id,
        user_id=user_id,
        profile=profile,
        public_slug=slug,
    )

    await db.commit()

    # 6. Determine generated_at (from updated entity or fallback)
    from datetime import datetime, timezone  # noqa: PLC0415

    generated_at = updated.bio_generated_at if updated is not None else datetime.now(tz=timezone.utc)

    # 7. Build profile DTO
    profile_dto = _to_public_profile_dto(updated or doctor)
    if profile_dto is None:
        # Shouldn't happen (we just wrote it), but graceful fallback
        profile_dto = PublicDoctorProfileDTO(
            display_name=doctor.display_name,
            specialty=doctor.specialty,
        )

    logger.info(
        "doctor_profile_generated",
        doctor_id=str(doctor_id),
        tenant_id=str(tenant_id),
        clinic_id=str(clinic_id),
        slug=slug,
    )

    return GenerateProfileResponse(
        profile=profile_dto,
        generated_at=generated_at,
        public_slug=slug,
    )


# ── Structured profile manual edit endpoint (AUDITOR_AUTO_FIX_LOOP iter 1) ────


@router.patch(
    "/{doctor_id}/public-profile",
    response_model=DoctorDetailDTO,
    response_model_by_alias=True,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_brand_owner_access(roles=_STAFF_MUTATION_ROLES))],
)
async def patch_doctor_public_profile(
    doctor_id: UUID,
    request: PatchPublicProfileRequest,
    tenant_id: UUID = Header(alias="X-Tenant-ID"),
    clinic_id: UUID = Header(alias="X-Clinic-ID"),
    user_id: UUID = Header(alias="X-User-ID"),
    db: AsyncSession = Depends(_get_db),
) -> DoctorDetailDTO:
    """Persist manually-edited structured public profile sections.

    StructuredProfileEditor autosaves to this endpoint via usePatchPublicProfile hook.

    RN-D3B-4: does NOT touch bio_generated_at — that is ONLY set by generate-profile.
    Updates public_profile JSONB with provided sections (partial: None fields preserved
    as-is in the DoctorPublicProfile domain object).

    RBAC: {owner, admin_clinic} (staff mutation roles).
    Audit: doctor.public_profile_updated (HIPAA-lite sync write).
    Response: DoctorDetailDTO with clinic_slug populated (mirrors GET /{id}).
    """
    service = _build_service(db)

    # Build DoctorPublicProfile from request (all-optional patch fields)
    from src.modules.vitalia.clinics.domain.public_profile import (  # noqa: PLC0415
        DoctorPublicProfile,
    )

    # Load current doctor to merge (None request fields keep current values)
    doctor = await service.get_doctor(
        doctor_id=doctor_id,
        tenant_id=tenant_id,
        clinic_id=clinic_id,
        user_id=user_id,
    )
    if doctor is None:
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "doctor_not_found", "message": "Médico no encontrado."},
        )

    # Merge: use existing profile as base, apply non-None fields from request
    existing = doctor.public_profile or DoctorPublicProfile()

    def _items_to_dicts(items: list | None) -> list[dict]:
        """Convert DTO list items to raw dict for DoctorPublicProfile storage."""
        if items is None:
            return []
        return [item.model_dump() for item in items]

    merged_profile = DoctorPublicProfile(
        sobre_mi=request.sobre_mi if request.sobre_mi is not None else existing.sobre_mi,
        formacion=_items_to_dicts(request.formacion) if request.formacion is not None else existing.formacion,
        experiencia=_items_to_dicts(request.experiencia) if request.experiencia is not None else existing.experiencia,
        tratamientos=request.tratamientos if request.tratamientos is not None else existing.tratamientos,
        certificaciones=request.certificaciones if request.certificaciones is not None else existing.certificaciones,
        idiomas=request.idiomas if request.idiomas is not None else existing.idiomas,
    )

    # Persist — service calls repo.update_public_profile_sections (NO bio_generated_at)
    updated = await service.patch_public_profile(
        doctor_id=doctor_id,
        tenant_id=tenant_id,
        clinic_id=clinic_id,
        user_id=user_id,
        profile=merged_profile,
    )

    await db.commit()

    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "doctor_not_found", "message": "Médico no encontrado."},
        )

    # Populate clinic_slug (mirrors GET /{id} handler: get_by_id → .slug)
    clinic = await _build_clinic_repository(db).get_by_id(
        tenant_id=tenant_id,
        clinic_id=clinic_id,
    )

    logger.info(
        "doctor_public_profile_patched",
        doctor_id=str(doctor_id),
        tenant_id=str(tenant_id),
        clinic_id=str(clinic_id),
    )

    return _to_detail_dto(updated, clinic_slug=clinic.slug if clinic else None)


# ── Availability blocks sub-routes (T-BE-3) ──────────────────────────────────


@router.get("/{doctor_id}/availability-blocks", response_model=AvailabilityBlocksResponse, response_model_by_alias=True)
async def list_availability_blocks(
    doctor_id: UUID,
    tenant_id: UUID = Header(alias="X-Tenant-ID"),
    clinic_id: UUID = Header(alias="X-Clinic-ID"),
    db: AsyncSession = Depends(_get_db),
) -> AvailabilityBlocksResponse:
    """List availability blocks for a doctor (dual filter).

    Returns all active (non-deleted) blocks for the specified doctor,
    scoped to the tenant+clinic (dual filter per hipaa-lite.md).
    Headers typed as UUID — FastAPI validates and returns 422 for invalid values.
    """
    svc = _build_block_service(db)
    blocks = await svc.list_blocks(
        doctor_id=doctor_id,
        tenant_id=tenant_id,
        clinic_id=clinic_id,
    )
    return AvailabilityBlocksResponse(blocks=[_to_block_dto(b) for b in blocks])


# ── Availability occurrences range projection (T-BE-occurrences-endpoint, D3-C) ──


@router.get(
    "/{doctor_id}/availability-occurrences",
    response_model=AvailabilityOccurrencesResponse,
    response_model_by_alias=True,
)
async def list_availability_occurrences(
    doctor_id: UUID,
    from_date: date = Query(alias="from", description="Inicio del rango (YYYY-MM-DD, inclusivo)"),
    to_date: date = Query(alias="to", description="Fin del rango (YYYY-MM-DD, inclusivo)"),
    tenant_id: UUID = Header(alias="X-Tenant-ID"),
    clinic_id: UUID = Header(alias="X-Clinic-ID"),
    user_id: UUID = Header(alias="X-User-ID"),  # noqa: ARG001 — actor-header consistency (useStaffActorHeaders)
    db: AsyncSession = Depends(_get_db),
) -> AvailabilityOccurrencesResponse:
    """Project active blocks into block-level occurrences within [from, to].

    D3-C fix (03-arch-delta § 4.3): this endpoint is the paint SSoT — the FE
    week/month views consume it and client-side expansion dies (V-D3C-NODUP).
    Collapses slots to ONE occurrence per (block, date); reuses
    AvailabilityProjectionService (no new expansion logic).

    Range bounded to 62 days (unbounded projection guard) — violations → 422.
    Dual filter tenant+clinic enforced by the repository (hipaa-lite).
    Headers typed as UUID — FastAPI validates and returns 422 for invalid values.
    X-User-ID required for detail-endpoint consistency (useStaffActorHeaders).
    """
    svc = _build_block_service(db)
    try:
        occurrences = await svc.list_occurrences(
            doctor_id=doctor_id,
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            range_start=from_date,
            range_end=to_date,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error": "invalid_range", "message": str(exc)},
        ) from exc

    return AvailabilityOccurrencesResponse(
        occurrences=[AvailabilityOccurrenceDTO.model_validate(o) for o in occurrences]
    )


@router.post(
    "/{doctor_id}/availability-blocks",
    response_model=AvailabilityBlockDTO,
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_brand_owner_access(roles=_STAFF_MUTATION_ROLES))],
)
async def create_availability_block(
    doctor_id: UUID,
    request: RecurrentBlockCreateRequest | OneOffBlockCreateRequest,
    tenant_id: UUID = Header(alias="X-Tenant-ID"),
    clinic_id: UUID = Header(alias="X-Clinic-ID"),
    user_id: UUID = Header(alias="X-User-ID"),
    db: AsyncSession = Depends(_get_db),
) -> AvailabilityBlockDTO:
    """Create a new availability block (recurrent or one-off) + materialize slots.

    SC-1: recurrent weekly/biweekly + end condition -> expand via rrule -> vitalia_availability_slots.
    SC-1b: biweekly occurrences=N -> exactly N occurrence dates.
    SC-1c: one-off (specific_date) -> single day of slots.

    Scheduling module reads vitalia_availability_slots to display available appointments.
    No scheduling module edit required — slots table is brand-local, scheduling reads it.

    Audit: doctor.availability_block_created (sync write pre-response, HIPAA-lite).
    Headers typed as UUID — FastAPI validates and returns 422 for invalid values.
    """
    svc = _build_block_service(db)
    try:
        block = await svc.create_block(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            doctor_id=doctor_id,
            user_id=user_id,
            kind=request.kind,
            start_time=request.start_time,
            end_time=request.end_time,
            # D3-F primary fields (only present on RecurrentBlockCreateRequest)
            days_of_week=getattr(request, "days_of_week", None),
            interval=getattr(request, "interval", 1),
            # Legacy fields (backward compat)
            day_of_week=getattr(request, "day_of_week", None),
            freq=getattr(request, "freq", None),
            end_condition_kind=getattr(request, "end_condition_kind", None),
            end_date=getattr(request, "end_date", None),
            occurrences=getattr(request, "occurrences", None),
            specific_date=getattr(request, "specific_date", None),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error": "invalid_block", "message": str(exc)},
        ) from exc

    await db.commit()
    return _to_block_dto(block)


@router.patch(
    "/{doctor_id}/availability-blocks/{block_id}",
    response_model=AvailabilityBlockDTO,
    response_model_by_alias=True,
    dependencies=[Depends(require_brand_owner_access(roles=_STAFF_MUTATION_ROLES))],
)
async def patch_availability_block(
    doctor_id: UUID,
    block_id: UUID,
    request: RecurrentBlockCreateRequest | OneOffBlockCreateRequest,
    tenant_id: UUID = Header(alias="X-Tenant-ID"),
    clinic_id: UUID = Header(alias="X-Clinic-ID"),
    user_id: UUID = Header(alias="X-User-ID"),
    db: AsyncSession = Depends(_get_db),
) -> AvailabilityBlockDTO:
    """Edit a block (reproject-future-only invariant).

    Only slots on or after today are re-projected. Past slots are never touched.
    Confirmed future slots (has_confirmed_appointment=True) are preserved.
    Headers typed as UUID — FastAPI validates and returns 422 for invalid values.
    """
    svc = _build_block_service(db)
    try:
        block = await svc.update_block(
            block_id=block_id,
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            doctor_id=doctor_id,
            user_id=user_id,
            kind=request.kind,
            start_time=request.start_time,
            end_time=request.end_time,
            # D3-F primary fields (only present on RecurrentBlockCreateRequest)
            days_of_week=getattr(request, "days_of_week", None),
            interval=getattr(request, "interval", 1),
            # Legacy fields (backward compat)
            day_of_week=getattr(request, "day_of_week", None),
            freq=getattr(request, "freq", None),
            end_condition_kind=getattr(request, "end_condition_kind", None),
            end_date=getattr(request, "end_date", None),
            occurrences=getattr(request, "occurrences", None),
            specific_date=getattr(request, "specific_date", None),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error": "invalid_block", "message": str(exc)},
        ) from exc

    if block is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "availability_block_not_found",
                "message": "Bloque de disponibilidad no encontrado.",
            },
        )
    await db.commit()
    return _to_block_dto(block)


@router.delete(
    "/{doctor_id}/availability-blocks/{block_id}",
    response_model=DeleteBlockResponse,
    dependencies=[Depends(require_brand_owner_access(roles=_STAFF_MUTATION_ROLES))],
)
async def delete_availability_block(
    doctor_id: UUID,
    block_id: UUID,
    scope: str = Query(default="series", description="series | occurrence | this_and_future"),
    occurrence_date: date | None = Query(
        default=None,
        alias="occurrence_date",
        description="YYYY-MM-DD (required for scope=occurrence|this_and_future)",
    ),
    tenant_id: UUID = Header(alias="X-Tenant-ID"),
    clinic_id: UUID = Header(alias="X-Clinic-ID"),
    user_id: UUID = Header(alias="X-User-ID"),
    db: AsyncSession = Depends(_get_db),
) -> DeleteBlockResponse:
    """Retire future slots + soft-delete block (with optional scoped delete).

    CRITICAL INVARIANT (delete-block-preserves-confirmed-appointments):
    Slots with has_confirmed_appointment=True are NEVER deleted in any scope.

    scope=series (DEFAULT, backward-compat):
        Full soft-delete of block + retire all future free slots.
        Returns {deleted: True, preserved_appointments: N, scope: 'series'}.

    scope=occurrence (requires occurrence_date):
        Appends occurrence_date to block.excluded_dates; retires free slots on that
        exact date; block remains active.
        Returns {deleted: False, preserved_appointments: N, scope: 'occurrence'}.

    scope=this_and_future (requires occurrence_date):
        Truncates series: sets end_date = occurrence_date - 1 day; retires free slots
        with slot_date >= occurrence_date; block remains active.
        Returns {deleted: False, preserved_appointments: N, scope: 'this_and_future'}.

    422 if scope requires occurrence_date and it is missing/invalid.
    Audit: doctor.availability_block_deleted | occurrence_excluded | truncated (sync, HIPAA-lite).
    Headers typed as UUID — FastAPI validates and returns 422 for invalid values.
    """
    valid_scopes = {"series", "occurrence", "this_and_future"}
    if scope not in valid_scopes:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "invalid_scope",
                "message": f"El parámetro 'scope' debe ser uno de: {', '.join(sorted(valid_scopes))}.",
            },
        )

    if scope in ("occurrence", "this_and_future") and occurrence_date is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "missing_occurrence_date",
                "message": "Se requiere el parámetro 'occurrence_date' (YYYY-MM-DD) para este tipo de eliminación.",
            },
        )

    svc = _build_block_service(db)

    try:
        if scope == "occurrence":
            assert occurrence_date is not None  # guarded above
            await svc.exclude_occurrence(
                block_id=block_id,
                tenant_id=tenant_id,
                clinic_id=clinic_id,
                user_id=user_id,
                occurrence_date=occurrence_date,
            )
            preserved = await svc.count_future_confirmed(block_id=block_id, tenant_id=tenant_id, clinic_id=clinic_id)
            await db.commit()
            return DeleteBlockResponse(deleted=False, preserved_appointments=preserved, scope=scope)

        elif scope == "this_and_future":
            assert occurrence_date is not None  # guarded above
            await svc.truncate_from(
                block_id=block_id,
                tenant_id=tenant_id,
                clinic_id=clinic_id,
                user_id=user_id,
                occurrence_date=occurrence_date,
            )
            preserved = await svc.count_future_confirmed(block_id=block_id, tenant_id=tenant_id, clinic_id=clinic_id)
            await db.commit()
            return DeleteBlockResponse(deleted=False, preserved_appointments=preserved, scope=scope)

        else:
            # scope=series — default backward-compat behavior
            deleted, preserved = await svc.delete_block(
                block_id=block_id,
                tenant_id=tenant_id,
                clinic_id=clinic_id,
                user_id=user_id,
            )
            await db.commit()
            return DeleteBlockResponse(deleted=deleted, preserved_appointments=preserved, scope=scope)

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error": "invalid_operation", "message": str(exc)},
        ) from exc


# ── Bio-files sub-routes (T-BE-bio-docs, delta v3 D3-B) ─────────────────────


def _to_bio_file_dto(bio_file: DoctorBioFile) -> BioFileDTO:
    """Map DoctorBioFile domain entity → BioFileDTO."""
    return BioFileDTO(
        id=bio_file.id,
        filename=bio_file.filename,
        size_bytes=bio_file.size_bytes,
        content_type=bio_file.content_type,
        uploaded_at=bio_file.uploaded_at,
    )


@router.post(
    "/{doctor_id}/bio-files",
    response_model=BioFilesResponse,
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_brand_owner_access(roles=_STAFF_MUTATION_ROLES))],
)
async def register_bio_file(
    doctor_id: UUID,
    request: BioFileRegisterRequest,
    tenant_id: UUID = Header(alias="X-Tenant-ID"),
    clinic_id: UUID = Header(alias="X-Clinic-ID"),
    user_id: UUID = Header(alias="X-User-ID"),
    db: AsyncSession = Depends(_get_db),
) -> BioFilesResponse:
    """Register a bio-file record for a doctor after FE upload to /assets/upload.

    Flow (03-arch-delta § 3.1):
      1. FE uploads file via POST /assets/upload?kind=bio_doc → gets {key, url}.
      2. FE calls this endpoint with {storageKey, filename, sizeBytes, contentType}.
      3. BE validates metadata + creates DoctorBioFile record + writes audit.
      4. Returns updated bio_files list.

    RBAC: {owner, admin_clinic} only.
    Audit: doctor.bio_file_added (sync write, HIPAA-lite).
    Cross-tenant: doctor not found → 404 generic (no existence leak).
    Headers typed as UUID — FastAPI validates and returns 422 for invalid values.
    """
    svc = _build_bio_file_service(db)
    try:
        bio_file = await svc.register_file(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            doctor_id=doctor_id,
            user_id=user_id,
            storage_key=request.storage_key,
            filename=request.filename,
            size_bytes=request.size_bytes,
            content_type=request.content_type,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error": "invalid_bio_file", "message": str(exc)},
        ) from exc

    if bio_file is None:
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "doctor_not_found", "message": "Médico no encontrado."},
        )

    await db.commit()
    # Return updated list (re-fetch after commit for consistency)
    bio_files = await svc.list_files(tenant_id=tenant_id, clinic_id=clinic_id, doctor_id=doctor_id)
    return BioFilesResponse(bio_files=[_to_bio_file_dto(f) for f in bio_files])


@router.get(
    "/{doctor_id}/bio-files",
    response_model=BioFilesResponse,
    response_model_by_alias=True,
    dependencies=[Depends(require_brand_owner_access(roles=_STAFF_MUTATION_ROLES))],
)
async def list_bio_files(
    doctor_id: UUID,
    tenant_id: UUID = Header(alias="X-Tenant-ID"),
    clinic_id: UUID = Header(alias="X-Clinic-ID"),
    user_id: UUID = Header(alias="X-User-ID"),  # noqa: ARG001 — actor-header consistency
    db: AsyncSession = Depends(_get_db),
) -> BioFilesResponse:
    """List bio-files for a doctor (dual filter, ordered by upload date DESC).

    RBAC: {owner, admin_clinic}.
    Not PHI — bio-files are promotional material (CV/diploma).
    Headers typed as UUID — FastAPI validates and returns 422 for invalid values.
    """
    svc = _build_bio_file_service(db)
    bio_files = await svc.list_files(tenant_id=tenant_id, clinic_id=clinic_id, doctor_id=doctor_id)
    return BioFilesResponse(bio_files=[_to_bio_file_dto(f) for f in bio_files])


@router.delete(
    "/{doctor_id}/bio-files/{file_id}",
    response_model=BioFileDeleteResponse,
    dependencies=[Depends(require_brand_owner_access(roles=_STAFF_MUTATION_ROLES))],
)
async def delete_bio_file(
    doctor_id: UUID,
    file_id: UUID,
    tenant_id: UUID = Header(alias="X-Tenant-ID"),
    clinic_id: UUID = Header(alias="X-Clinic-ID"),
    user_id: UUID = Header(alias="X-User-ID"),
    db: AsyncSession = Depends(_get_db),
) -> BioFileDeleteResponse:
    """Soft-delete a bio-file (RN-D3B-1: bio_public snapshot untouched).

    The bio_public/public_profile section is NOT touched by this deletion —
    the public profile snapshot is managed separately via PATCH /{doctor_id}.

    RBAC: {owner, admin_clinic}.
    Audit: doctor.bio_file_deleted (sync write, HIPAA-lite).
    Not found / cross-tenant → 404 generic.
    Headers typed as UUID — FastAPI validates and returns 422 for invalid values.
    """
    svc = _build_bio_file_service(db)
    deleted = await svc.delete_file(
        tenant_id=tenant_id,
        clinic_id=clinic_id,
        doctor_id=doctor_id,
        file_id=file_id,
        user_id=user_id,
    )
    if not deleted:
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "bio_file_not_found", "message": "Archivo no encontrado."},
        )
    await db.commit()
    return BioFileDeleteResponse(deleted=True)


@router.get(
    "/{doctor_id}/bio-files/{file_id}/download",
    dependencies=[Depends(require_brand_owner_access(roles=_STAFF_MUTATION_ROLES))],
)
async def download_bio_file(
    doctor_id: UUID,
    file_id: UUID,
    tenant_id: UUID = Header(alias="X-Tenant-ID"),
    clinic_id: UUID = Header(alias="X-Clinic-ID"),
    user_id: UUID = Header(alias="X-User-ID"),
    db: AsyncSession = Depends(_get_db),
) -> Response:
    """Stream bio-file bytes (D-1: stream proxy via StorageStrategy.get_file_bytes).

    Works with BOTH storage backends (local + R2) via engine StorageStrategy.
    response_model= exemption: annotated -> Response (stream, not JSON).

    RBAC: {owner, admin_clinic}.
    Audit: doctor.bio_file_downloaded (sync write, HIPAA-lite).
    Not found / cross-tenant → 404 generic.
    Storage failure → 503 (BioFileStorageError — graceful-degradation).
    Headers typed as UUID — FastAPI validates and returns 422 for invalid values.
    """
    svc = _build_bio_file_service(db)
    try:
        result = await svc.download_file(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            doctor_id=doctor_id,
            file_id=file_id,
            user_id=user_id,
        )
    except BioFileStorageError as exc:
        logger.warning(
            "bio_file_download_storage_error",
            file_id=str(file_id),
            doctor_id=str(doctor_id),
            tenant_id=str(tenant_id),
            error=str(exc),
        )
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "storage_unavailable", "message": "El archivo no está disponible en este momento."},
        ) from exc

    if result is None:
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "bio_file_not_found", "message": "Archivo no encontrado."},
        )

    bio_file, content = result
    await db.commit()

    logger.info(
        "bio_file_downloaded",
        file_id=str(file_id),
        doctor_id=str(doctor_id),
        tenant_id=str(tenant_id),
        size_bytes=len(content),
    )

    return Response(
        content=content,
        media_type=bio_file.content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{bio_file.filename}"',
            "Content-Length": str(len(content)),
        },
    )
