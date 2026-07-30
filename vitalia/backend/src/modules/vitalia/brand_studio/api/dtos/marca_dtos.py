# cap: brand_studio.lisa-marca
# story-origin: vitalia-fase2-s7-TBD
"""Marca DTOs — 18 Pydantic v2 DTOs for brand_studio API endpoints.

PII policy: response_model= mandatory on every endpoint (arch test enforces).
Spanish neutro LatAm: user-facing strings use tuteo (no voseo).

downstream-regression-na: brand-local DTOs vitalia
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

# ---------------------------------------------------------------------------
# § 4.1 Identity DTOs (sub-sub-tab Identidad)
# ---------------------------------------------------------------------------


class BrandIdentityDTO(BaseModel):
    """GET /lisa/marca/identity response."""

    model_config = ConfigDict(from_attributes=True)

    tenant_id: UUID
    name: str
    slug: str  # read-only (from tenant.subdomain)
    tagline: str | None
    clinic_vertical: str  # read-only — captured in onboarding-clinica
    primary_specialties: list[str]  # read-only — idem
    updated_at: datetime | None


class BrandIdentityPatchDTO(BaseModel):
    """PATCH /lisa/marca/identity request — partial update."""

    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(None, min_length=2, max_length=100)
    tagline: str | None = Field(None, max_length=150)


class BrandVisualsDTO(BaseModel):
    """GET /lisa/marca/visuals response."""

    model_config = ConfigDict(from_attributes=True)

    tenant_id: UUID
    primary_color: str | None  # hex "#RRGGBB"
    accent_color: str | None
    background_color: str | None
    text_primary_color: str | None
    font_heading: str | None
    font_body: str | None
    logo_url: str | None
    updated_at: datetime | None


class BrandVisualsPatchDTO(BaseModel):
    """PATCH /lisa/marca/visuals request — partial update."""

    model_config = ConfigDict(extra="forbid")

    primary_color: str | None = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    accent_color: str | None = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    background_color: str | None = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    text_primary_color: str | None = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    font_heading: str | None = Field(None, max_length=64)
    font_body: str | None = Field(None, max_length=64)


class LogoUploadResponseDTO(BaseModel):
    """POST /lisa/marca/logos response."""

    model_config = ConfigDict(from_attributes=True)

    logo_id: UUID
    logo_url: str
    size_bytes: int
    format: Literal["png", "jpg", "jpeg", "webp"]


# ---------------------------------------------------------------------------
# § 4.2 Personality + Voice DTOs (sub-sub-tab Voz)
# ---------------------------------------------------------------------------


class BrandPersonalityDTO(BaseModel):
    """GET /lisa/marca/personality response.

    alias_generator=to_camel: response serializes with camelCase keys (soISpeak,
    identityAnchor, etc.) so the FE fetchClient (no case-transform) reads them
    correctly. populate_by_name=True keeps internal snake_case construction working
    (from_attributes + keyword args in tests).

    Fix: arreglar-guardado-voz-y-tono / T-2 — BE-2 camelCase contract.
    """

    model_config = ConfigDict(from_attributes=True, populate_by_name=True, alias_generator=to_camel)

    tenant_id: UUID
    personality_profile_id: UUID
    archetype: Literal["caregiver", "sage", "healer", "hero"]
    so_i_speak: str  # block "ASÍ HABLO" (compiler v2 block 3)
    so_i_dont_speak: str  # block "ASÍ NO HABLO" (compiler v2 block 4)
    technical_context: str  # block 5
    format_instructions: str  # block 6
    identity_anchor: str  # block 1
    domain_context: str  # block 2
    compiled_at: datetime | None
    compiler_version: str


class BrandPersonalityPatchDTO(BaseModel):
    """PATCH /lisa/marca/personality — partial update of compiler v2 6 blocks.

    alias_generator=to_camel: FE sends camelCase (soISpeak, identityAnchor, etc.).
    populate_by_name=True: internal code and tests can still use snake_case.
    extra="forbid": genuinely-unknown fields are still rejected (only known
    snake/camel pairs are valid — they share the same field).

    Fix: arreglar-guardado-voz-y-tono / T-2 — BE-2 camelCase contract.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True, alias_generator=to_camel)

    archetype: Literal["caregiver", "sage", "healer", "hero"] | None = None
    so_i_speak: str | None = Field(None, max_length=4000)
    so_i_dont_speak: str | None = Field(None, max_length=4000)
    technical_context: str | None = Field(None, max_length=2000)
    format_instructions: str | None = Field(None, max_length=2000)
    identity_anchor: str | None = Field(None, max_length=2000)
    domain_context: str | None = Field(None, max_length=2000)


class ProhibitedPhraseDTO(BaseModel):
    """GET /lisa/marca/prohibited-phrases response item."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    phrase: str
    suggested_alternative: str
    severity: Literal["low", "medium", "high"]
    country_scope: str | None
    is_seed: bool  # tenant_id IS NULL → True


class ProhibitedPhrasesListDTO(BaseModel):
    """GET /lisa/marca/prohibited-phrases response."""

    model_config = ConfigDict(from_attributes=True)

    items: list[ProhibitedPhraseDTO]
    total: int


class VoiceWarningOverrideRequestDTO(BaseModel):
    """POST /lisa/marca/voice-warning-override request."""

    model_config = ConfigDict(extra="forbid")

    phrase_id: UUID  # which prohibited phrase was triggered
    section: Literal["so_i_speak", "so_i_dont_speak"]
    user_text_excerpt: str = Field(..., max_length=500)  # NO PHI (microcopy fragment)


class VoicePreviewDTO(BaseModel):
    """GET /lisa/marca/voice-preview response."""

    model_config = ConfigDict(from_attributes=True)

    personality_profile_id: UUID
    sample_whatsapp: str  # short greeting
    sample_email_reactivation: str  # longer email body
    compiled_at: datetime
    compiler_version: str
    cache_hit: bool  # debug indicator (server cache by hash)


# ---------------------------------------------------------------------------
# § 4.3 Contact + Presence + Trust DTOs (sub-sub-tab Presencia)
# ---------------------------------------------------------------------------


class BrandContactDTO(BaseModel):
    """GET /lisa/marca/contact response."""

    model_config = ConfigDict(from_attributes=True)

    tenant_id: UUID
    public_landing_url: str | None  # read-only — auto-generated from tenant.subdomain
    website_url: str | None
    instagram_handle: str | None
    tiktok_handle: str | None
    facebook_page: str | None
    google_business_url: str | None
    updated_at: datetime | None


class BrandContactPatchDTO(BaseModel):
    """PATCH /lisa/marca/contact request — partial update."""

    model_config = ConfigDict(extra="forbid")

    website_url: str | None = Field(None, max_length=300)
    instagram_handle: str | None = Field(None, max_length=64)
    tiktok_handle: str | None = Field(None, max_length=64)
    facebook_page: str | None = Field(None, max_length=128)
    google_business_url: str | None = Field(None, max_length=300)


class TrustSignalDTO(BaseModel):
    """Trust signal — certification/authority listed via hybrid catalog."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    label: str  # "DIGESA" or free-text "Otra: ..."
    catalog_code: str | None  # None if free-text
    logo_url: str | None
    issued_year: int | None
    is_seed: bool


class TrustSignalsCatalogDTO(BaseModel):
    """Hybrid catalog per country — OQ-D resolution 2026-05-27."""

    model_config = ConfigDict(from_attributes=True)

    country: str  # ISO 3166-1 alpha-2
    items: list[dict[str, str]]  # [{code, label, hint}]


class TrustSignalCreateRequestDTO(BaseModel):
    """POST /lisa/marca/trust-signals request."""

    model_config = ConfigDict(extra="forbid")

    label: str = Field(..., min_length=2, max_length=128)
    catalog_code: str | None = Field(None, max_length=64)
    issued_year: int | None = Field(None, ge=1900, le=2100)


class TeamMemberPreviewItemDTO(BaseModel):
    """Individual team member in read-only preview."""

    model_config = ConfigDict(from_attributes=True)

    member_id: UUID
    display_name: str  # "Dr. Pérez" — no PHI (staff label, not patient)
    role: str  # "Odontólogo"
    avatar_url: str | None


class BrandTeamPreviewDTO(BaseModel):
    """Read-only top-N team preview consumed in sub-sub-tab Identidad."""

    model_config = ConfigDict(from_attributes=True)

    tenant_id: UUID
    total_count: int
    preview_count: int  # min(total_count, 3)
    members: list[TeamMemberPreviewItemDTO]


class ClinicConfigDTO(BaseModel):
    """Read-only display of clinic_vertical + primary_specialties.

    Captured in onboarding-clinica story (parallel). Lisa-marca shows read-only + edit-link.
    """

    model_config = ConfigDict(from_attributes=True)

    tenant_id: UUID
    clinic_vertical: str  # "dental_clinic" | "psychology_clinic" | ...
    primary_specialties: list[str]  # ["Odontología general", ...]


# ---------------------------------------------------------------------------
# § 4.4 Initial state DTO (SSR consumption per subsubtab)
# ---------------------------------------------------------------------------


class MarcaInitialStateDTO(BaseModel):
    """SSR initial state per subsubtab — Server Component fetches and hydrates React Query cache."""

    model_config = ConfigDict(from_attributes=True)

    subsubtab: Literal["identidad", "voz-y-tono", "presencia"]
    identity: BrandIdentityDTO | None = None
    visuals: BrandVisualsDTO | None = None
    personality: BrandPersonalityDTO | None = None
    contact: BrandContactDTO | None = None
    team_preview: BrandTeamPreviewDTO | None = None
    clinic_config: ClinicConfigDTO | None = None
    voice_preview: VoicePreviewDTO | None = None  # only for subsubtab=voz-y-tono
    prohibited_phrases: ProhibitedPhrasesListDTO | None = None  # idem
    trust_signals: list[TrustSignalDTO] | None = None
    trust_catalog: TrustSignalsCatalogDTO | None = None  # only for subsubtab=presencia
