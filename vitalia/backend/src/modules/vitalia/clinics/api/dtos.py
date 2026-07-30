# cap: clinics.clinics-brand-extension
# story-origin: TBD
"""Vitalia Clinic API DTOs — Pydantic v2 request/response models.

PII rule: response_model= is MANDATORY on all routes (arch test enforces).
No PHI fields exposed. Clinic identity data (name, slug, country) is allowed.

All DTOs use ConfigDict(from_attributes=True) for SQLAlchemy model_validate.
"""

from __future__ import annotations

from datetime import date, datetime, time
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic.alias_generators import to_camel

# cap: clinics.lisa.doctores — doctor DTOs added in T-BE-1


class ClinicCreateRequest(BaseModel):
    """Request body for POST /api/v1/vitalia/clinics/."""

    name: str = Field(min_length=1, max_length=200, description="Clinic name")
    slug: str = Field(min_length=2, max_length=100, description="URL-safe slug (unique per tenant)")
    country: str = Field(min_length=2, max_length=2, description="ISO 3166-1 alpha-2")
    timezone: str = Field(default="UTC", description="IANA timezone string")
    plan_tier: str = Field(default="starter", description="starter | growth | scale")


class ClinicResponse(BaseModel):
    """Response body for Clinic endpoints.

    PII allowlist: id, tenant_id, name, slug, country, timezone, plan_tier,
    is_active, onboarding_completed, created_at — no PHI fields.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    name: str
    slug: str
    country: str
    timezone: str
    plan_tier: str
    is_active: bool
    onboarding_completed: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ClinicListResponse(BaseModel):
    """Response body for GET /api/v1/vitalia/clinics/ list endpoint."""

    model_config = ConfigDict(from_attributes=True)

    clinics: list[ClinicResponse]
    total: int


# ── Doctor DTOs (T-BE-1) ─────────────────────────────────────────────────────


class DoctorCreateRequest(BaseModel):
    """Request body for POST /api/v1/vitalia/clinics/doctors/.

    All PII fields are handled server-side (encrypted at rest via pgcrypto).
    Accepts both camelCase (from FE) and snake_case (API clients / tests) via populate_by_name=True.
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    first_name: str = Field(min_length=1, max_length=128)
    last_name: str = Field(min_length=1, max_length=128)
    dni: str = Field(min_length=1, max_length=32, description="DNI / document number (PHI)")
    email: str = Field(min_length=3, max_length=254, description="Professional email (PHI)")
    phone: str | None = Field(default=None, max_length=32, description="Mobile phone (PHI)")
    specialty: str | None = Field(default=None, max_length=128)
    credential: str = Field(min_length=1, max_length=64, description="Credential number (PHI)")
    credential_country: str = Field(min_length=2, max_length=2, description="PE|AR|MX|CL")
    years_experience: int | None = Field(default=None, ge=0, le=60)
    languages: list[str] = Field(default_factory=list)


class DoctorListItemDTO(BaseModel):
    """Response item for list endpoint — PHI fields are MASKED.

    Per hipaa-lite.md: list responses must mask DNI/email/phone.
    Use masked_dni/masked_email/masked_phone fields (never raw PHI).

    camelCase wire contract: alias_generator=to_camel + populate_by_name=True.
    Routes must set response_model_by_alias=True (or use model.model_dump(by_alias=True)).
    03-arch-fe § TypeScript Types mandates camelCase (firstName, lastName, avatarUrl, etc.).
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )

    id: UUID
    tenant_id: UUID
    clinic_id: UUID
    first_name: str = ""
    """Staff card: firstName required by FE StaffCard (03-arch-fe § TypeScript Types)."""
    last_name: str = ""
    """Staff card: lastName required by FE StaffCard."""
    display_name: str
    specialty: str | None
    active: bool
    visible_en_landing: bool
    years_experience: int | None = None
    languages: list[str] = Field(default_factory=list)
    avatar_key: str | None = None
    # FE StaffCard stats — nullable until appointments/analytics are wired (post-MVP)
    patients_count: int | None = None
    """Populated later by appointments module. FE null-guards this field."""
    nps_score: float | None = None
    """Populated later by analytics module. FE null-guards this field."""
    # PHI masked versions (never raw dni/email/phone)
    masked_dni: str | None = None
    masked_email: str | None = None
    masked_phone: str | None = None
    created_at: datetime | None = None


class DoctorListResponse(BaseModel):
    """Paginated list response for GET /doctors/.

    camelCase wire contract aligned with 03-arch-fe § TypeScript Types.
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )

    items: list[DoctorListItemDTO]
    total: int
    page: int
    page_size: int


class DoctorDetailDTO(BaseModel):
    """Full doctor detail for admin workspace (admin_clinic role only).

    Exposes decrypted PII fields — only available to admin_clinic.

    camelCase wire contract: alias_generator=to_camel + populate_by_name=True.
    03-arch-fe § TypeScript Types: DoctorDetail interface uses camelCase keys.
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )

    id: UUID
    tenant_id: UUID
    clinic_id: UUID
    first_name: str
    last_name: str
    display_name: str
    dni: str
    email: str
    phone: str | None
    specialty: str | None
    credential: str
    credential_country: str
    years_experience: int | None
    languages: list[str]
    bio_inputs_notes: str | None
    bio_links: list[str]
    bio_public: "BioPublicDTO | None"
    avatar_key: str | None
    visible_en_landing: bool
    active: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None
    # Delta v3 D3-B (T-BE-bio-docs): bio material files folded into detail.
    # Populated on GET /{id} and PATCH /{id}; POST create returns [] (correct
    # by construction — a new doctor has no files yet).
    bio_files: list["BioFileDTO"] = Field(default_factory=list)

    # Delta v3 D3-D (T-BE-pagina-publica): public profile + slug + generation state (RN-D3D-4).
    # Populated by GET /{id} handler after querying bio_files for material_new computation.
    # public_profile: structured 6-section profile (None before first generate-profile call).
    # public_slug: URL-safe slug for DoctorPaginaView (None before first generate-profile call).
    # profile_state: generation state computed server-side; None when bio_generated_at is None.
    #
    # Limitation (RN-D3D-4 partial): material_new tracks file uploads only (uploaded_at comparison).
    # Changes to bio_inputs_notes or bio_links do NOT bump material_new (no dedicated timestamp).
    # Documented for auditor: files=yes, notes/links=best-effort (bio_generated_at heuristic).
    public_profile: "PublicDoctorProfileDTO | None" = None
    public_slug: str | None = None
    profile_state: "ProfileStateDTO | None" = None
    clinic_slug: str | None = None  # para construir URL pública /d/{clinic}/{doctor} en FE (D3-D)


class BioPublicDTO(BaseModel):
    """Public bio DTO — 3 editable sections."""

    model_config = ConfigDict(from_attributes=True)

    resumen: str | None = None
    formacion: str | None = None
    enfoque: str | None = None


# ── D3-D Public profile DTOs (T-BE-pagina-publica) ───────────────────────────
# cap: clinics.lisa.doctores


class FormacionItemDTO(BaseModel):
    """Formación académica item — para perfil público del doctor.

    Not PHI — academic credentials are professional public data.
    """

    model_config = ConfigDict(from_attributes=True, alias_generator=to_camel, populate_by_name=True)

    titulo: str
    institucion: str
    anio: int | None = None


class ExperienciaItemDTO(BaseModel):
    """Experiencia profesional item — para perfil público del doctor.

    Not PHI — professional experience is public data.
    """

    model_config = ConfigDict(from_attributes=True, alias_generator=to_camel, populate_by_name=True)

    puesto: str
    lugar: str
    anios: int | None = None


class PublicDoctorProfileDTO(BaseModel):
    """Allow-listed DTO for public /api/public/clinic/{slug}/doctors/{doctor_slug} endpoint.

    CHANNEL GUARD (hipaa-lite.md): zero PHI — only structured professional sections.
    Constructed by public_doctor_serializer.to_public_profile_dto() — never from ORM directly.
    Arch test test_public_doctor_profile_allowlist.py enforces this invariant.

    Per 03-arch-delta.md § 6.1 + RN-D3D-6: all sections nullable.
    Minimum identity guaranteed: display_name always present.

    OG-safe fields (RN-D3D-7): display_name, specialty, sobre_mi (first line),
    avatar_key — available for FE generateMetadata without PHI exposure.
    """

    model_config = ConfigDict(from_attributes=True, alias_generator=to_camel, populate_by_name=True)

    clinic_name: str | None = None  # Consultorio (mockup v3.2) — nombre clínica, no-PHI
    # badge "✓ {nro} ({país}) — verificado" — colegiatura = dato profesional público, no-PHI paciente
    credential_label: str | None = None

    # Minimum identity — always present (RN-D3D-6)
    display_name: str
    specialty: str | None = None
    avatar_key: str | None = None

    # Structured profile sections — nullable (RN-D3D-6)
    sobre_mi: str | None = None
    """Professional summary — first line used for OG description (RN-D3D-7)."""

    formacion: list[FormacionItemDTO] | None = None
    """Academic background — list of {titulo, institucion, anio}."""

    experiencia: list[ExperienciaItemDTO] | None = None
    """Work experience — list of {puesto, lugar, anios}."""

    tratamientos: list[str] | None = None
    """Treatment/procedure chips — public display strings."""

    certificaciones: list[str] | None = None
    """Professional certifications tick list."""

    idiomas: list[str] | None = None
    """Languages spoken. Exposed only if len > 1 (RN-D3D-5 — enforced by serializer)."""


class ProfileStateDTO(BaseModel):
    """Profile state for admin detail view — RN-D3D-4 material_new detection.

    Server-side computation (files-only — RN-D3D-4 PARCIAL, ver DoctorDetailDTO
    nota): any(bio_files.uploaded_at > bio_generated_at). Cambios en notas/links
    NO bumpean material_new (sin timestamp dedicado — limitación documentada).
    Exposed in DoctorDetailDTO (admin workspace, not public).
    Not PHI — timestamps only.
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )

    generated_at: datetime | None = None
    """Timestamp of last bio/profile generation. None if never generated."""

    material_new: bool = False
    """True when bio material (files or inputs) has changed since last generation."""

    material_new_count: int = 0
    """Count of bio files uploaded after bio_generated_at (approximate indicator)."""


class GenerateProfileResponse(BaseModel):
    """Response body for POST /{doctor_id}/generate-profile.

    Returns the newly generated structured public profile + timestamp.
    Accepts snake_case internally; exposes camelCase to FE via alias_generator.
    PII allowlist: only structured professional sections + timestamps.
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )

    profile: PublicDoctorProfileDTO
    """Structured 6-section public profile just generated."""

    generated_at: datetime
    """Timestamp when profile was generated (UTC). Used for material_new comparison."""

    public_slug: str | None = None
    """URL-safe slug for public doctor page. Generated on first call if not set."""


class PatchPublicProfileRequest(BaseModel):
    """Request body for PATCH /{doctor_id}/public-profile — structured sections update.

    All fields are optional (patch semantics). Accepts camelCase from FE via alias_generator.
    extra="forbid" rejects unknown keys loudly (audit fix — prevents silent field drops).

    RN-D3B-4: this DTO intentionally has NO bio_generated_at field — that is ONLY
    set by POST generate-profile. Shapes from 03-arch-delta.md § 6.1.

    Not PHI — professional public data only.
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="forbid",
    )

    sobre_mi: str | None = None
    """Professional summary text."""

    formacion: list[FormacionItemDTO] | None = None
    """Academic background — list of {titulo, institucion, anio}."""

    experiencia: list[ExperienciaItemDTO] | None = None
    """Work experience — list of {puesto, lugar, anios}."""

    tratamientos: list[str] | None = None
    """Treatment/procedure chips — public display strings."""

    certificaciones: list[str] | None = None
    """Professional certifications tick list."""

    idiomas: list[str] | None = None
    """Languages spoken."""


class DoctorPatchRequest(BaseModel):
    """Request body for PATCH /doctors/{id} — partial update.

    All fields are optional (patch semantics: only send fields to update).
    Accepts camelCase from FE (yearsExperience, bioInputsNotes, etc.) via alias_generator.
    extra="forbid" ensures unknown keys are rejected loudly (audit fix — silent drops caught).
    phone added: FE can update phone via PATCH (was missing, causing silent drop on camelCase).
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="forbid",
    )

    phone: str | None = Field(default=None, max_length=32, description="Mobile phone (PHI)")
    bio_inputs_notes: str | None = None
    bio_links: list[str] | None = None
    bio_public: BioPublicDTO | None = None
    avatar_key: str | None = None
    visible_en_landing: bool | None = None
    active: bool | None = None
    specialty: str | None = None
    years_experience: int | None = Field(default=None, ge=0, le=60)
    languages: list[str] | None = None


class PublicDoctorDTO(BaseModel):
    """Allow-listed DTO for public /api/public/clinic/{slug}/doctors endpoint.

    CHANNEL GUARD: only 7 fields permitted — NO PHI (dni/email/phone/credential).
    Constructed by public_doctor_serializer.to_public_dto() — never from ORM directly.
    Arch test test_public_doctors_allowlist.py enforces this invariant.
    """

    model_config = ConfigDict(from_attributes=True)

    display_name: str
    specialty: str | None = None
    avatar_key: str | None = None
    years_experience: int | None = None
    languages: list[str] = Field(default_factory=list)
    bio_public: BioPublicDTO | None = None
    credential_label: str | None = None
    """Optional display label like 'CMP 12345' (hides full credential number)."""


class PublicDoctorsResponse(BaseModel):
    """Response for public doctors endpoint."""

    model_config = ConfigDict(from_attributes=True)

    doctors: list[PublicDoctorDTO]


# ── Availability Block DTOs (T-BE-3) ─────────────────────────────────────────


class RecurrentBlockCreateRequest(BaseModel):
    """Request body for recurrent availability block (discriminated union kind='recurrent').

    Domain validation (03-arch-be.md § 1):
    - end_condition_kind must be one of: end_date | occurrences | open_ended
    - if end_condition_kind == 'end_date', end_date is required
    - if end_condition_kind == 'occurrences', occurrences >= 1 is required

    D3-F extension (T-BE-create-patch):
    - days_of_week (primary): list of weekday ints 0=Mon..6=Sun, used by FE post-D3-F.
    - interval (primary): recurrence interval in weeks (≥1; 1=weekly, 2=biweekly, N custom).
    - day_of_week (legacy optional): single-day shorthand for backward compat.
    - freq (legacy optional): 'weekly' | 'biweekly' shorthand for backward compat.

    Precedence: if both forms present → days_of_week + interval win (primary).
    Validation: at least ONE of (days_of_week non-empty) OR (day_of_week present) required.

    Accepts camelCase from FE (startTime, endTime, daysOfWeek, interval, etc.) via alias_generator.
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    kind: str = Field(default="recurrent")
    start_time: "time"
    end_time: "time"
    # D3-F primary fields (FE post-D3-F sends these)
    days_of_week: list[int] = Field(
        default_factory=list,
        description="Primary D3-F: weekday list 0=Mon..6=Sun. Non-empty → primary path.",
    )
    interval: int = Field(
        default=1,
        ge=1,
        description="Recurrence interval in weeks (1=weekly, 2=biweekly, N custom).",
    )
    # Legacy fields (backward compat — optional post D3-F)
    day_of_week: int | None = Field(
        default=None,
        ge=0,
        le=6,
        description="Legacy: 0=Monday..6=Sunday. Optional when days_of_week provided.",
    )
    freq: str | None = Field(
        default=None,
        description="Legacy: weekly | biweekly. Optional when interval provided.",
    )
    end_condition_kind: str = Field(description="end_date | occurrences | open_ended")
    end_date: "date | None" = None
    occurrences: int | None = Field(default=None, ge=1)
    specific_date: "date | None" = None

    @model_validator(mode="after")
    def _validate_at_least_one_day_form(self) -> "RecurrentBlockCreateRequest":
        """Require at least one of: days_of_week (non-empty) OR day_of_week (not None).

        Error message in Spanish neutro as per UI contract.
        """
        has_primary = bool(self.days_of_week)
        has_legacy = self.day_of_week is not None
        if not has_primary and not has_legacy:
            raise ValueError(
                "Se requiere al menos un día de la semana. Proporciona 'days_of_week' (lista) o 'day_of_week' (legado)."
            )
        return self


class OneOffBlockCreateRequest(BaseModel):
    """Request body for one-off availability block (discriminated union kind='one_off').

    SC-1c: a single specific date — no recurrence.
    Accepts camelCase from FE (startTime, endTime, specificDate) via alias_generator.
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    kind: str = Field(default="one_off")
    start_time: "time"
    end_time: "time"
    specific_date: "date"


class AvailabilityBlockDTO(BaseModel):
    """Response DTO for a single availability block.

    Not PHI — availability blocks are scheduling metadata (not patient data).
    camelCase wire contract aligned with 03-arch-fe § TypeScript Types (AvailabilityBlock).

    D3-F extension: daysOfWeek + interval added alongside legacy dayOfWeek/freq for
    backward compat. FE consumers must migrate to daysOfWeek + interval (primary).
    Legacy single-day payloads are coerced to list in the service/mapper layer.
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )

    id: UUID
    tenant_id: UUID
    clinic_id: UUID
    doctor_id: UUID
    kind: str
    start_time: "time"
    end_time: "time"
    # D3-F primary recurrent fields
    days_of_week: list[int] = []
    """Multi-day weekday list (0=Mon..6=Sun) — primary D3-F field. Empty for one_off."""
    interval: int = 1
    """Recurrence interval in weeks (1=weekly, 2=biweekly, N=custom)."""
    # Legacy backward-compat recurrent fields (None for one_off)
    day_of_week: int | None = None
    freq: str | None = None
    end_condition_kind: str | None = None
    end_date: "date | None" = None
    occurrences: int | None = None
    # One-off field (None for recurrent)
    specific_date: "date | None" = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class AvailabilityBlocksResponse(BaseModel):
    """Response for GET /{doctor_id}/availability-blocks — list of blocks."""

    model_config = ConfigDict(from_attributes=True)

    blocks: list[AvailabilityBlockDTO]


class AvailabilityOccurrenceDTO(BaseModel):
    """One block-level occurrence within the queried range (D3-C paint SSoT).

    The calendar paints blocks, not 30-min slots — the BE collapses slots to
    one occurrence per (block, date). camelCase wire contract consumed by
    useAvailabilityOccurrences (T-FE-occurrences-consume).

    Not PHI — availability occurrences are scheduling metadata.
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )

    block_id: UUID
    occurrence_date: date
    start_time: time
    end_time: time
    kind: str
    """'recurrent' | 'one_off'."""
    freq: str | None = None
    """'weekly' | 'biweekly' — None for one_off."""
    pattern_summary: str
    """Human pattern (SSoT: format_recurrence_summary, RN-D3F-1)."""


class AvailabilityOccurrencesResponse(BaseModel):
    """Response for GET /{doctor_id}/availability-occurrences?from=&to=."""

    model_config = ConfigDict(from_attributes=True)

    occurrences: list[AvailabilityOccurrenceDTO]


class DeleteBlockResponse(BaseModel):
    """Response for DELETE /{doctor_id}/availability-blocks/{block_id}.

    SC-1d / SC-3b: delete retires future free slots; confirms preserved count.
    CRITICAL: preserved_appointments indicates confirmed appointments NOT cancelled.

    scope: echoed from the request query param (series | occurrence | this_and_future).
    """

    model_config = ConfigDict(from_attributes=True)

    deleted: bool
    preserved_appointments: int
    """Count of future slots preserved because they have confirmed appointments."""
    scope: str = "series"
    """Delete scope echoed: 'series' | 'occurrence' | 'this_and_future'."""


# ── Bio generation DTOs (T-BE-4) ─────────────────────────────────────────────


class GenerateBioRequest(BaseModel):
    """Request body for POST /doctors/{id}/generate-bio.

    Body is empty — service uses the doctor's stored bio_inputs_notes + bio_links.
    Defined as explicit DTO (not empty dict) to comply with response_model= mandate.

    D-4 (03-arch): deterministic extractive service, NOT agentic.
    Voice anchor is resolved server-side from PersonalityProfile (read-only).
    """

    model_config = ConfigDict(from_attributes=True)


class GenerateBioResponse(BaseModel):
    """Response for POST /doctors/{id}/generate-bio.

    Returns 3 editable sections + optional error_message.

    On LLM success: bio contains sections, error_message is None.
    On LLM failure (timeout/error): bio is empty BioPublicDTO, error_message is set.
    FE: shows error_message as toast; does NOT block autosave of rest of profile.

    V-FN-9: bio-gen fallback on LLM fail -> empty sections + message.
    """

    model_config = ConfigDict(from_attributes=True)

    bio: BioPublicDTO
    """3 editable sections: resumen, formacion, enfoque (may be None if no material)."""

    error_message: str | None = None
    """Spanish neutro error message shown to user on LLM failure. None = success."""


# ── Bio-files DTOs (T-BE-bio-docs, delta v3 D3-B) ────────────────────────────
# cap: clinics.lisa.doctores


class BioFileDTO(BaseModel):
    """Response DTO for a single doctor bio-file record.

    camelCase wire contract (alias_generator=to_camel): sizeBytes, contentType,
    uploadedAt match 03-arch-delta § 3.1 FE TypeScript interface.

    Not PHI — bio-files are promotional material (CV/diploma).
    response_model= mandatory (PII gate / arch test).
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )

    id: UUID
    filename: str
    size_bytes: int
    content_type: str
    uploaded_at: datetime


class BioFileRegisterRequest(BaseModel):
    """Request body for POST /{doctor_id}/bio-files.

    FE sends camelCase (storageKey, sizeBytes, contentType) after uploading
    to the asset proxy (POST /assets/upload?kind=bio_doc).
    extra="forbid": unknown keys rejected loudly (audit fix pattern).
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="forbid",
    )

    storage_key: str = Field(min_length=1, description="Clave R2 devuelta por /assets/upload")
    filename: str = Field(min_length=1, max_length=255, description="Nombre original del archivo")
    size_bytes: int = Field(ge=1, description="Tamaño en bytes (validado por el backend)")
    content_type: str = Field(min_length=1, description="MIME type del archivo")


class BioFilesResponse(BaseModel):
    """Response for GET /{doctor_id}/bio-files — list of bio-files."""

    model_config = ConfigDict(from_attributes=True, alias_generator=to_camel, populate_by_name=True)

    bio_files: list[BioFileDTO]


class BioFileDeleteResponse(BaseModel):
    """Response for DELETE /{doctor_id}/bio-files/{file_id}."""

    model_config = ConfigDict(from_attributes=True, alias_generator=to_camel, populate_by_name=True)

    deleted: bool


# ── Assets proxy DTOs (T-BE-6) ───────────────────────────────────────────────


class AssetUploadResponse(BaseModel):
    """Response for POST /api/v1/vitalia/assets/upload.

    Returns R2 storage key (tenant-scoped path) and the public URL.

    key:  Tenant-scoped path in R2 — {tenant_id}/{kind}/{uuid}-{filename}.
          Frontend uses this key to PATCH avatar_key on the doctor record.
    url:  Public URL (local path in dev/test; R2 public URL in prod).

    D-3 (03-arch): presigned upload does NOT exist in luana-core-assets.
    Consume AssetsService.upload_asset proxy. Live R2 = T-BE-7 Chris manual.
    V-FN-10: returns {key, url} on valid upload.
    """

    model_config = ConfigDict(from_attributes=True)

    key: str
    """Tenant-scoped R2 storage key. Frontend PATCHes doctor.avatar_key with this."""

    url: str
    """Public URL for the uploaded file."""


# ---------------------------------------------------------------------------
# Account DTOs (vitalia-fase2-config-cuenta T-2)
# cap: configuracion.cuenta
# ---------------------------------------------------------------------------


class ClinicAccountResponse(BaseModel):
    """Response body for GET /api/v1/clinics/account/ and PATCH /api/v1/clinics/account/.

    Aggregates clinic identity + locale preferences + specialties.
    Non-PHI: clinic-level identity fields (not patient data).
    """

    model_config = ConfigDict(from_attributes=True)

    clinic_id: UUID
    tenant_id: UUID
    name: str
    slug: str
    country: str = Field(description="ISO 3166-1 alpha-2")
    timezone: str
    plan_tier: str
    is_active: bool
    # Account fields
    legal_name: str | None = None
    fiscal_id: str | None = None
    address: str | None = None
    phone: str | None = None
    email: str | None = None
    language: str = "es-419"
    currency: str | None = None
    # Config from tenant.config_json["clinic_config"]
    primary_specialties: list[str] = Field(default_factory=list)


class ClinicAccountPatchRequest(BaseModel):
    """Request body for PATCH /api/v1/clinics/account/.

    All fields optional — only provided fields are updated (partial update).
    primary_specialties triggers RMW on tenant.config_json JSONB.
    """

    name: str | None = None
    legal_name: str | None = None
    fiscal_id: str | None = None
    address: str | None = None
    phone: str | None = None
    email: str | None = None
    language: str | None = None
    currency: str | None = None
    primary_specialties: list[str] | None = None


class SpecialtyCatalogResponse(BaseModel):
    """Response body for GET /api/v1/clinics/account/specialties-catalog.

    Returns available specialty options for the clinic's country.
    """

    model_config = ConfigDict(from_attributes=True)

    country: str
    specialties: list[dict]  # [{id, name, tier}] — serialized SpecialtyEntry


class DpoReferenceResponse(BaseModel):
    """Response body for GET /api/v1/clinics/account/dpo.

    Returns the DPO (Data Protection Officer / Responsable de tratamiento)
    reference for the tenant. Empty state (configured=False) when absent.
    Per hipaa-lite.md § DPO/Responsable tratamiento per tenant.
    """

    model_config = ConfigDict(from_attributes=True)

    configured: bool = False
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    role: str | None = None
    jurisdiction: str | None = None
