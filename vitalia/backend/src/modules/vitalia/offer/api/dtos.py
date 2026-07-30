# cap: lisa.servicios
# voseo-allowed: "vos" matched by hook is the value-objects module name (domain.vos), not voseo
"""Pydantic v2 DTOs for Lisa's service catalog API (T-2 § 3).

Request DTOs use ``extra="forbid"`` so unknown keys are rejected (defense-in-
depth). Response DTOs use ``ConfigDict(from_attributes=True)`` so they hydrate
straight from the service read models (ServiceView, SalesBrief, Case, …). They
whitelist exactly the fields that may leave the API — PII / PHI never in scope
for the catalog DTOs (catalog is NOT PHI, RN-13), and the Case DTO carries no
patient identifiers (only the before/after asset urls + consent flags). Monetary
fields use ``currency: str | None`` (never a hardcoded default). No ``Any``.

T-R1 (G reconcile): added VO DTOs (ValueWithUnitDTO, ServiceVariantDTO,
ThreeChargePricingDTO + ReservationConfigDTO/AdvanceConfigDTO/FinancingConfigDTO)
with ``.to_domain()`` that builds frozen domain VOs at the boundary (domain
invariants enforce → ValueError → 422 at router). ServicePatchRequest widened to
all rich OfferExt fields; ServiceDetailDTO widened to carry them on the read path.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from luana_core_offer_studio.domain.enums import OfferStatus
from pydantic import BaseModel, ConfigDict, Field

from src.modules.vitalia.offer.domain.enums import (
    InitialApptType,
    IntervalUnit,
    PriceMode,
    ReservationKind,
    ServiceModality,
)
from src.modules.vitalia.offer.domain.vos import (
    AdvanceConfig,
    FinancingConfig,
    ReservationConfig,
    ServiceVariant,
    ThreeChargePricing,
    ValueWithUnit,
)

# ============================================================
# VO DTOs — build frozen domain VOs at the API boundary (T-R1 § A.1)
# ============================================================


class ValueWithUnitDTO(BaseModel):
    """RN-31 — typed numeric interval with a unit. Mirrors domain ValueWithUnit.

    No Pydantic-level constraints on ``value`` — domain VO enforces ``value >= 1``
    in ``__post_init__`` (raises ValueError → caller maps to 422).
    """

    model_config = ConfigDict(from_attributes=True)

    value: int
    unit: IntervalUnit

    def to_domain(self) -> ValueWithUnit:
        """Build the frozen domain VO; invariants enforce (ValueError → 422 at router)."""
        return ValueWithUnit(value=self.value, unit=self.unit)


class ServiceVariantDTO(BaseModel):
    """RN-29 / RN-11 — named price variant. Mirrors domain ServiceVariant.

    No Pydantic-level constraints on ``name``/``price`` — domain VO enforces
    name non-blank and price >= 0 in ``__post_init__`` (raises ValueError → 422).
    """

    model_config = ConfigDict(from_attributes=True)

    name: str
    price: Decimal
    note: str | None = None

    def to_domain(self) -> ServiceVariant:
        """Build the frozen domain VO; invariants enforce (ValueError → 422 at router)."""
        return ServiceVariant(name=self.name, price=self.price, note=self.note)


class ReservationConfigDTO(BaseModel):
    """First charge — deposit to hold the appointment."""

    model_config = ConfigDict(from_attributes=True)

    enabled: bool
    amount: Decimal | None = None
    kind: ReservationKind

    def to_domain(self) -> ReservationConfig:
        """Build the frozen domain VO."""
        return ReservationConfig(enabled=self.enabled, amount=self.amount, kind=self.kind)


class AdvanceConfigDTO(BaseModel):
    """Second charge — advance payment before the procedure."""

    model_config = ConfigDict(from_attributes=True)

    enabled: bool
    amount: Decimal | None = None
    kind: ReservationKind

    def to_domain(self) -> AdvanceConfig:
        """Build the frozen domain VO."""
        return AdvanceConfig(enabled=self.enabled, amount=self.amount, kind=self.kind)


class FinancingConfigDTO(BaseModel):
    """Third charge — installment financing. installments >= 1 when offered."""

    model_config = ConfigDict(from_attributes=True)

    offered: bool
    installments: int | None = None
    interest_kind: str | None = None
    finance_partner: str | None = None

    def to_domain(self) -> FinancingConfig:
        """Build the frozen domain VO; invariants enforce (ValueError → 422 at router)."""
        return FinancingConfig(
            offered=self.offered,
            installments=self.installments,
            interest_kind=self.interest_kind,
            finance_partner=self.finance_partner,
        )


class ThreeChargePricingDTO(BaseModel):
    """RN-6 — headline price + 3 independent charges. Mirrors domain ThreeChargePricing."""

    model_config = ConfigDict(from_attributes=True)

    price: Decimal | None = None
    price_mode: PriceMode
    price_publishable: bool
    currency: str | None = None  # from tenant_locale — NEVER hardcode 'USD'
    reservation: ReservationConfigDTO | None = None
    advance: AdvanceConfigDTO | None = None
    financing: FinancingConfigDTO | None = None

    def to_domain(self) -> ThreeChargePricing:
        """Build the frozen domain VO; invariants enforce (ValueError → 422 at router)."""
        return ThreeChargePricing(
            price=self.price,
            price_mode=self.price_mode,
            price_publishable=self.price_publishable,
            currency=self.currency,
            reservation=self.reservation.to_domain() if self.reservation is not None else None,
            advance=self.advance.to_domain() if self.advance is not None else None,
            financing=self.financing.to_domain() if self.financing is not None else None,
        )


# ============================================================
# Catalog — list + detail
# ============================================================


class ServiceListItemDTO(BaseModel):
    """One catalog card (RN-15 list). Maps from ServiceView.

    T-BE-1 (mateo-nueva-cita): exposes ``initial_appt_duration_minutes`` so the
    "Nueva cita" form can prefill appointment duration from the selected service.
    ``None`` is valid — the FE defaults to 30 min (RN-5, FE concern).
    """

    model_config = ConfigDict(from_attributes=True)

    offer_id: UUID
    public_name: str
    category: str | None = None
    modality: ServiceModality
    is_active: bool
    status: OfferStatus
    canonical_service_ref: str | None = None  # → origin chip (biblioteca vs personalizado)
    price: Decimal | None = None
    currency: str | None = None
    initial_appt_duration_minutes: int | None = None  # T-BE-1: prefill duración cita (RN-5)


class ServiceListResponse(BaseModel):
    """Keyset-paginated catalog page (RN-15)."""

    model_config = ConfigDict(from_attributes=True)

    items: list[ServiceListItemDTO]
    next_cursor: str | None = None


class SpecialistLinkDTO(BaseModel):
    """A doctor linked to a service.

    ``display_name`` and ``specialty`` are populated when the detail endpoint
    receives ``X-Clinic-ID`` and the doctor is found in the roster (G2-F13-BE).
    Both are ``None`` when the header is absent or the doctor is no longer in
    the roster — backward-compatible, never breaks the detail response.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    offer_id: UUID
    doctor_id: UUID
    display_name: str | None = None
    specialty: str | None = None


class CaseDTO(BaseModel):
    """Before/after case. PHI asset urls only — NO patient identifiers."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    offer_id: UUID
    before_asset_url: str
    after_asset_url: str
    consent_signed: bool
    consent_ref: str | None = None


class TestimonialDTO(BaseModel):
    """Manual testimonial (NOT PHI)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    offer_id: UUID
    rating: int
    text: str
    author: str
    source: str


class FaqPairDTO(BaseModel):
    """A single FAQ question/answer pair inside the sales brief."""

    model_config = ConfigDict(from_attributes=True)

    question: str
    answer: str


class ObjectionPairDTO(BaseModel):
    """A single objection/response pair inside the sales brief."""

    model_config = ConfigDict(from_attributes=True)

    objection_type: str
    response: str


class SalesBriefDTO(BaseModel):
    """Adrián-facing sales material (1:1 per offer, NOT PHI)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    offer_id: UUID
    candidate_ideal: str | None = None
    contraindications: str | None = None
    qualification_questions: str | None = None
    escalation_conditions: str | None = None
    requires_evaluation: bool = False
    emotional_benefits: str | None = None
    pain_of_not_treating: str | None = None
    differentiators: str | None = None
    promos: str | None = None
    faq: list[FaqPairDTO] = Field(default_factory=list)
    objections: list[ObjectionPairDTO] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    problems_solved: str | None = None
    language_to_avoid: str | None = None
    updated_at: datetime | None = None


class ServiceDetailDTO(BaseModel):
    """Service workspace: catalog headline + linked sub-resources + rich ficha fields.

    Widened in T-R1 (G reconcile) to carry all rich OfferExt fields so the FE
    can hydrate the ResumenView from the GET response. Catalog is NOT PHI (RN-13)
    — no PII concern with these fields. currency: str | None (never hardcoded 'USD').
    """

    model_config = ConfigDict(from_attributes=True)

    offer_id: UUID
    public_name: str
    category: str | None = None
    modality: ServiceModality
    is_active: bool
    status: OfferStatus
    canonical_service_ref: str | None = None
    price: Decimal | None = None
    currency: str | None = None
    # — Rich ficha fields (T-R1 § A.4 — read-path widening) —
    description_long: str | None = None
    includes: str | None = None
    excludes: str | None = None
    warranty: str | None = None
    variants: list[ServiceVariantDTO] = Field(default_factory=list)  # RN-29
    procedure_steps: str | None = None
    anesthesia_pain: str | None = None
    prep: str | None = None
    aftercare: str | None = None
    downtime: str | None = None
    expected_result: str | None = None
    result_timing: str | None = None
    result_lifespan: str | None = None
    realistic_expectations: str | None = None
    risks: str | None = None
    red_flags: str | None = None
    session_interval: ValueWithUnitDTO | None = None
    recurrence_interval: ValueWithUnitDTO | None = None
    initial_appt_duration_minutes: int | None = None
    initial_appt_type: InitialApptType | None = None
    pricing: ThreeChargePricingDTO | None = None
    candidate_for_library: bool = False
    # — Sub-resources —
    sales_brief: SalesBriefDTO | None = None
    specialists: list[SpecialistLinkDTO] = Field(default_factory=list)
    cases: list[CaseDTO] = Field(default_factory=list)
    testimonials: list[TestimonialDTO] = Field(default_factory=list)


# ============================================================
# Biblioteca — typeahead
# ============================================================


class BibliotecaItemDTO(BaseModel):
    """A preset library entry surfaced by the typeahead (RN-25 / AC-18)."""

    model_config = ConfigDict(from_attributes=True)

    canonical_ref: str
    name: str
    clinic_type: str
    category: str | None = None
    modality: str
    synonyms: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)


class BibliotecaSearchResponse(BaseModel):
    """Typeahead result set."""

    model_config = ConfigDict(from_attributes=True)

    items: list[BibliotecaItemDTO]


# ============================================================
# Knowledge extract — document → autocomplete (AC-11, NOT RAG)
# ============================================================


class KnowledgeSourceDTO(BaseModel):
    """Reference to the recorded engine KnowledgeSource (None id → degraded)."""

    model_config = ConfigDict(from_attributes=True)

    knowledge_source_id: UUID | None = None


class ExtractionPrefillDTO(BaseModel):
    """Editable prefill suggested from an uploaded document/URL (all optional)."""

    model_config = ConfigDict(from_attributes=True)

    description_long: str | None = None
    includes: str | None = None
    excludes: str | None = None
    procedure_steps: str | None = None
    aftercare: str | None = None
    risks: str | None = None
    keywords: list[str] = Field(default_factory=list)
    source_label: str | None = None


class KnowledgeExtractResponse(BaseModel):
    """document→autocomplete: tracked source + editable prefill (AC-11)."""

    model_config = ConfigDict(from_attributes=True)

    source: KnowledgeSourceDTO
    prefill: ExtractionPrefillDTO


# ============================================================
# Request DTOs (extra="forbid")
# ============================================================


class ServiceCreateFromTemplateRequest(BaseModel):
    """ "Usar plantilla": draft an Offer pre-filled from a biblioteca preset (RN-16/25)."""

    model_config = ConfigDict(extra="forbid")

    canonical_service_ref: str
    clinic_type: str


class ServiceCreateCustomRequest(BaseModel):
    """ "Crear personalizado": canonical_ref=null."""

    model_config = ConfigDict(extra="forbid")

    public_name: str = Field(min_length=1)
    price: Decimal
    currency: str | None = None
    modality: ServiceModality
    category: str | None = None


class ServicePatchRequest(BaseModel):
    """Per-field autosave (RN-20). All optional — last-write-wins per field.

    Widened in T-R1 (G reconcile) to expose the full editable ficha (RN-26 §6).
    extra="forbid" preserved. VO fields passed as DTOs; `.to_domain()` builds
    the frozen domain VO at the service boundary (domain invariants → ValueError → 422).
    """

    model_config = ConfigDict(extra="forbid")

    # — existing (keep) —
    public_name: str | None = Field(default=None, min_length=1)
    price: Decimal | None = None
    category: str | None = None
    modality: ServiceModality | None = None
    # — Qué es —
    description_long: str | None = None
    includes: str | None = None
    excludes: str | None = None
    warranty: str | None = None
    variants: list[ServiceVariantDTO] | None = None  # RN-29
    # — Procedimiento (RN-26) —
    procedure_steps: str | None = None
    anesthesia_pain: str | None = None
    prep: str | None = None
    aftercare: str | None = None
    downtime: str | None = None
    # — Resultados —
    expected_result: str | None = None
    result_timing: str | None = None
    result_lifespan: str | None = None
    realistic_expectations: str | None = None
    # — Riesgos —
    risks: str | None = None
    red_flags: str | None = None
    # — Modalidad y agenda —
    session_interval: ValueWithUnitDTO | None = None  # if modality=sesiones
    recurrence_interval: ValueWithUnitDTO | None = None  # if modality=recurrente
    initial_appt_duration_minutes: int | None = Field(default=None, ge=1)
    initial_appt_type: InitialApptType | None = None  # F3 — RN-32
    pricing: ThreeChargePricingDTO | None = None  # RN-6
    candidate_for_library: bool | None = None  # RN-27


class ServiceActivateRequest(BaseModel):
    """Toggle Activo (RN-10)."""

    model_config = ConfigDict(extra="forbid")

    is_active: bool


class SpecialistLinkRequest(BaseModel):
    """Link a doctor (autosave · RN-20). Idempotent re-link."""

    model_config = ConfigDict(extra="forbid")

    doctor_id: UUID


class CaseCreateRequest(BaseModel):
    """Before/after case. consent_signed MUST be true (RN-33; repo gates it)."""

    model_config = ConfigDict(extra="forbid")

    before_asset_url: str = Field(min_length=1)
    after_asset_url: str = Field(min_length=1)
    consent_signed: bool
    consent_ref: str | None = None


class TestimonialCreateRequest(BaseModel):
    """Manual testimonial."""

    model_config = ConfigDict(extra="forbid")

    rating: int = Field(ge=1, le=5)
    text: str = Field(min_length=1)
    author: str = Field(min_length=1)
    source: str = Field(min_length=1)


class SalesBriefPatchRequest(BaseModel):
    """Sales-brief autosave (per-field). All optional; unknown keys forbidden."""

    model_config = ConfigDict(extra="forbid")

    candidate_ideal: str | None = None
    contraindications: str | None = None
    qualification_questions: str | None = None
    escalation_conditions: str | None = None
    requires_evaluation: bool | None = None
    emotional_benefits: str | None = None
    pain_of_not_treating: str | None = None
    differentiators: str | None = None
    promos: str | None = None
    faq: list[FaqPairDTO] | None = None
    objections: list[ObjectionPairDTO] | None = None
    keywords: list[str] | None = None
    problems_solved: str | None = None
    language_to_avoid: str | None = None


class KnowledgeExtractRequest(BaseModel):
    """document→autocomplete by URL (file upload uses multipart, not this body)."""

    model_config = ConfigDict(extra="forbid")

    url: str | None = None
    filename: str | None = None
