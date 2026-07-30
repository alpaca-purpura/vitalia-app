// cap: lisa.servicios
// story-origin: vitalia-fase2-lisa-servicios T-6
/**
 * servicios.types.ts — TypeScript mirror of the offer-module wire contract.
 *
 * ★ WIRE SHAPE = snake_case (CRITICAL, confirmed verbatim from
 *   vitalia/backend/src/modules/vitalia/offer/api/dtos.py).
 *   The offer DTOs use `model_config = ConfigDict(from_attributes=True)` WITHOUT
 *   `alias_generator=to_camel` → the JSON keys on the wire are snake_case
 *   (`offer_id`, `public_name`, `is_active`, `canonical_service_ref`, `next_cursor`).
 *   This INTENTIONALLY diverges from the clinics/staff DTOs (which DO camelize).
 *   Mirroring the real shape here prevents the "imagined contract" trap
 *   (learning 2026-06-04-embudo-imagined-contract-never-integrated): an FE that
 *   guesses camelCase against a snake_case BE renders empty/undefined live while
 *   each side is green in isolation.
 *
 * ★ value_level GAP (reconciliation note, see T-6-impl-log.md § Upstream deficiency):
 *   the escalera (value ladder) groups services by OfferValueLevel, but the SHIPPED
 *   contract exposes NO value_level on ServiceListItemDTO/ServiceDetailDTO and
 *   ServicePatchRequest is `extra="forbid"` → a move-rung PATCH(value_level) would
 *   422. value_level is modelled here (optional) so the escalera can render once the
 *   BE wires the field; useMoveRung degrades to a documented no-op until then.
 *
 * T-6 vitalia-fase2-lisa-servicios
 * spec_anchor: 03-arch-fe.md § Data layer + 03-arch-be.md § dtos.py
 * downstream-regression-na: brand-local vitalia FE types; no cross-brand consumers
 */

// ── Value-object mirrors (T-R3 — snake_case, mirror domain value objects) ─────────────────

/**
 * Mirror of the domain ValueWithUnit value object.
 * unit: IntervalUnit StrEnum = "dias"|"semanas"|"meses"|"anios"
 */
export interface ValueWithUnit {
  value: number;
  unit: "dias" | "semanas" | "meses" | "anios";
}

// ── Wire enums (lowercase, mirror StrEnum on the BE) ────────────────────────────

/** Mirror of offer.domain.enums.ServiceModality. */
export type ServiceModality = "unica" | "sesiones" | "recurrente";

/** Mirror of offer.domain.enums.OfferStatus (subset surfaced to the catalog). */
export type OfferStatus = "draft" | "active" | "inactive" | "archived";

/**
 * Mirror of offer.domain.OfferValueLevel — the 5 EXACT ladder rungs (wire = lowercase).
 * FE renders MEDICAL labels (RN-2 override) via RUNG_LABEL_ES below — the engine's
 * own label_es is NOT consumed blindly (M2).
 */
export type OfferValueLevel =
  | "lead_magnet"
  | "activacion"
  | "transformacion"
  | "maximizacion"
  | "corporativo";

/** Service origin in the catalog (derived FE-side from canonical_service_ref presence). */
export type ServiceOrigen = "estandar" | "personalizado";

// ── List endpoint ───────────────────────────────────────────────────────────────

/** Mirror of ServiceListItemDTO (snake_case wire). */
export interface ServiceListItem {
  offer_id: string;
  public_name: string;
  category: string | null;
  modality: ServiceModality;
  is_active: boolean;
  status: OfferStatus;
  canonical_service_ref: string | null;
  price: number | null;
  currency: string | null;
  /**
   * NOT on the shipped wire (see GAP note above). Present so escalera can group
   * once the BE adds it. Treated as undefined today.
   */
  value_level?: OfferValueLevel | null;
}

/** Mirror of ServiceListResponse. */
export interface ServiceListResponse {
  items: ServiceListItem[];
  next_cursor: string | null;
}

// ── Detail endpoint (T-7 consumes the nested blocks) ────────────────────────────
//
// ★ T-7 DRIFT FIX (path-drift finding, same class as 2026-06-04-embudo-imagined-contract):
//   the T-6 shapes below (SalesBrief.positioning/benefits/faqs, SpecialistLink.display_name,
//   ServiceCase.case_id, ServiceTestimonial.testimonial_id) were IMAGINED — they do NOT
//   match the shipped offer DTOs (dtos.py). Replaced with the verbatim wire shapes so the
//   workspace renders live instead of green-in-isolation-but-broken.

/** Mirror of FaqPairDTO (snake_case wire). */
export interface FaqPair {
  question: string;
  answer: string;
}

/** Mirror of ObjectionPairDTO. NOTE: `objection_type` (not `objection`). */
export interface ObjectionPair {
  objection_type: string;
  response: string;
}

/** Mirror of SalesBriefDTO — the full 18-field "Para Adrián" brief. */
export interface SalesBrief {
  id: string;
  offer_id: string;
  candidate_ideal: string | null;
  contraindications: string | null;
  qualification_questions: string | null;
  escalation_conditions: string | null;
  requires_evaluation: boolean;
  emotional_benefits: string | null;
  pain_of_not_treating: string | null;
  differentiators: string | null;
  promos: string | null;
  faq: FaqPair[];
  objections: ObjectionPair[];
  keywords: string[];
  problems_solved: string | null;
  language_to_avoid: string | null;
  updated_at: string | null;
}

/**
 * Mirror of SpecialistLinkDTO. G2-F13: BE now enriches with display_name +
 * specialty when the request carries X-Clinic-ID (dual-scoped roster join).
 * Fields are optional to remain backwards-compatible with older BE responses.
 */
export interface SpecialistLink {
  id: string;
  offer_id: string;
  doctor_id: string;
  /** Resolved from the clinic roster when X-Clinic-ID is present. */
  display_name?: string | null;
  /** Specialty label resolved from the clinic roster. */
  specialty?: string | null;
}

/** Mirror of CaseDTO (PHI). NOTE: never returned by the detail endpoint (always []). */
export interface ServiceCase {
  id: string;
  offer_id: string;
  before_asset_url: string;
  after_asset_url: string;
  consent_signed: boolean;
  consent_ref: string | null;
}

/** Mirror of TestimonialDTO. */
export interface ServiceTestimonial {
  id: string;
  offer_id: string;
  rating: number;
  text: string;
  author: string;
  source: string;
}

/**
 * Mirror of ServiceDetailDTO — widened (T-R3 / G reconcile) to carry the rich
 * ficha fields that OfferExt/OfferServiceExtModel store. Snake_case: the offer
 * DTOs don't alias to camelCase (see file header note). Fields match the
 * widened ServiceDetailDTO in offer/api/dtos.py post T-R1.
 */
export interface ServiceDetail extends ServiceListItem {
  sales_brief: SalesBrief | null;
  specialists: SpecialistLink[];
  cases: ServiceCase[];
  testimonials: ServiceTestimonial[];

  // ── Rich ficha fields (T-R3 — optional until all existing test fixtures updated)
  // All are nullable at the BE (OfferExt defaults to None). Optional here so legacy
  // test fixtures (other leaves) don't need to supply every field immediately.

  // Qué es
  description_long?: string | null;
  includes?: string | null;
  excludes?: string | null;
  warranty?: string | null;
  variants?: import("../components/servicios/VariantsRepeater").ServiceVariant[] | null;

  // El procedimiento
  procedure_steps?: string | null;
  anesthesia_pain?: string | null;
  prep?: string | null;
  aftercare?: string | null;
  downtime?: string | null;

  // Resultados
  expected_result?: string | null;
  result_timing?: string | null;
  result_lifespan?: string | null;
  realistic_expectations?: string | null;

  // Riesgos
  risks?: string | null;
  red_flags?: string | null;

  // Modalidad y agenda
  session_interval?: ValueWithUnit | null;        // revealed when modality=sesiones
  recurrence_interval?: ValueWithUnit | null;     // revealed when modality=recurrente
  initial_appt_duration_minutes?: number | null;
  initial_appt_type?: string | null;

  // ── Pricing (T-R-planpago — 3-charge model wired to BE) ─────────────────────
  /** ThreeChargePricingDTO — null on older services that haven't configured pricing. */
  pricing?: ThreeChargePricing | null;
}

// ── 3-charge pricing types (T-R-planpago) ────────────────────────────────────
//
// Mirror of ThreeChargePricingDTO in offer/api/dtos.py (snake_case, from_attributes).
// The BE stores pricing as a JSONB blob on the offer row.

/** "monto" = fixed amount · "porcentaje" = % of total price. */
export type ChargeKind = "monto" | "porcentaje";

/** "fijo" = fixed price · "rango" = "desde X" display. */
export type PriceMode = "fijo" | "rango";

/** Mirror of ReservationConfigDTO. */
export interface ReservationConfig {
  enabled: boolean;
  amount: number | null;
  kind: ChargeKind;
}

/** Mirror of AdvanceConfigDTO. */
export interface AdvanceConfig {
  enabled: boolean;
  amount: number | null;
  kind: ChargeKind;
}

/** Mirror of FinancingConfigDTO. */
export interface FinancingConfig {
  offered: boolean;
  installments: number | null;
  interest_kind: string | null;
  finance_partner: string | null;
}

/**
 * Mirror of ThreeChargePricingDTO — the 3-cobro model.
 *
 * RN-23: currency is read-only on this screen (comes from tenant/offer config).
 * The FE sends servicio.currency as-is in every pricing patch — NEVER edits it.
 */
export interface ThreeChargePricing {
  price: number | null;
  price_mode: PriceMode;
  price_publishable: boolean;
  currency: string | null;
  reservation: ReservationConfig | null;
  advance: AdvanceConfig | null;
  financing: FinancingConfig | null;
}

// ── Knowledge extraction (Sub-phase A: extract-only) ────────────────────────────

/** Mirror of KnowledgeSourceDTO. */
export interface KnowledgeSource {
  knowledge_source_id: string | null;
}

/** Mirror of ExtractionPrefillDTO — fields Lisa prefills from a processed document. */
export interface ExtractionPrefill {
  description_long: string | null;
  includes: string | null;
  excludes: string | null;
  procedure_steps: string | null;
  aftercare: string | null;
  risks: string | null;
  keywords: string[];
  source_label: string | null;
}

/** Mirror of KnowledgeExtractResponse. */
export interface KnowledgeExtractResponse {
  source: KnowledgeSource;
  prefill: ExtractionPrefill;
}

// ── T-7 mutation request payloads (mirror the `extra="forbid"` request DTOs) ─────

/** Mirror of SpecialistLinkRequest. */
export interface SpecialistLinkRequest {
  doctor_id: string;
}

/** Mirror of CaseCreateRequest (PHI). */
export interface CaseCreateRequest {
  before_asset_url: string;
  after_asset_url: string;
  consent_signed: boolean;
  consent_ref?: string | null;
}

/** Mirror of TestimonialCreateRequest. */
export interface TestimonialCreateRequest {
  rating: number;
  text: string;
  author: string;
  source: string;
}

/** Mirror of SalesBriefPatchRequest (all optional). */
export interface SalesBriefPatchRequest {
  candidate_ideal?: string | null;
  contraindications?: string | null;
  qualification_questions?: string | null;
  escalation_conditions?: string | null;
  requires_evaluation?: boolean | null;
  emotional_benefits?: string | null;
  pain_of_not_treating?: string | null;
  differentiators?: string | null;
  promos?: string | null;
  faq?: FaqPair[] | null;
  objections?: ObjectionPair[] | null;
  keywords?: string[] | null;
  problems_solved?: string | null;
  language_to_avoid?: string | null;
}

/** Mirror of KnowledgeExtractRequest. */
export interface KnowledgeExtractRequest {
  url?: string | null;
  filename?: string | null;
}

// ── Biblioteca (standard library) search ────────────────────────────────────────

/** Mirror of BibliotecaItemDTO. */
export interface BibliotecaItem {
  canonical_ref: string;
  name: string;
  clinic_type: string;
  category: string | null;
  modality: string;
  synonyms: string[];
  keywords: string[];
}

/** Mirror of BibliotecaSearchResponse. */
export interface BibliotecaSearchResponse {
  items: BibliotecaItem[];
}

// ── Request payloads (mirror the `extra="forbid"` request DTOs) ─────────────────

export interface ServiceCreateFromTemplateRequest {
  canonical_service_ref: string;
  clinic_type: string;
}

export interface ServiceCreateCustomRequest {
  public_name: string;
  price: number;
  currency?: string | null;
  modality: ServiceModality;
  category?: string | null;
}

/**
 * Mirror of ServicePatchRequest — widened (T-R3 / G reconcile) to all patchable
 * OfferExt fields. Per-field autosave: the FE sends a single-key patch per change.
 * NOTE: NO value_level (extra="forbid" on BE; escalera surface).
 */
export interface ServicePatchRequest {
  // existing
  public_name?: string;
  price?: number;
  category?: string | null;
  modality?: ServiceModality;
  // Qué es
  description_long?: string | null;
  includes?: string | null;
  excludes?: string | null;
  warranty?: string | null;
  variants?: import("../components/servicios/VariantsRepeater").ServiceVariant[] | null;
  // El procedimiento
  procedure_steps?: string | null;
  anesthesia_pain?: string | null;
  prep?: string | null;
  aftercare?: string | null;
  downtime?: string | null;
  // Resultados
  expected_result?: string | null;
  result_timing?: string | null;
  result_lifespan?: string | null;
  realistic_expectations?: string | null;
  // Riesgos
  risks?: string | null;
  red_flags?: string | null;
  // Modalidad y agenda
  session_interval?: ValueWithUnit | null;
  recurrence_interval?: ValueWithUnit | null;
  initial_appt_duration_minutes?: number | null;
  initial_appt_type?: string | null;
  // Pricing (T-R-planpago)
  /**
   * Full ThreeChargePricingDTO — must be the COMPLETE object on every patch.
   * price_mode + price_publishable are required by the BE (no defaults).
   */
  pricing?: ThreeChargePricing | null;
}

export interface ServiceActivateRequest {
  is_active: boolean;
}

// ── FE-side filters (URL-driven, nuqs) ──────────────────────────────────────────

export interface ServiciosFilters {
  /** Free-text search (debounced 300ms). */
  search: string;
  /** Specialty / category filter (maps to wire `category`). */
  category: string | null;
  /** Ladder rung filter (FE-side; no-op until BE wires value_level). */
  rung: OfferValueLevel | null;
  /** Active/inactive filter (maps to wire `is_active`). */
  active: "all" | "active" | "inactive";
}

// ── Catalogo | escalera view discriminator (URL subsubtab = SSoT) ──────────────

export type ServiciosView = "catalogo" | "escalera";
