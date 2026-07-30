// cap: configuracion.cuenta
// story-origin: vitalia-fase2-config-cuenta
/**
 * cuenta.types.ts — TypeScript view-model types for config/cuenta (Mi cuenta).
 *
 * camelCase EXACT MIRROR of Pydantic DTOs (03-arch.md § 5).
 * NO imagined fields (HB-42 lesson from embudo board crash).
 * Registered in test_fe_be_contract_parity.py as ContractPair (fe_interface="ClinicAccountDTO").
 *
 * All ISO 8601 datetimes as `string`. Optional fields explicit with `?:`.
 *
 * T-1 vitalia-fase2-config-cuenta
 * spec_anchor: 03-arch.md § 5
 * downstream-regression-na: brand-local vitalia FE types; no cross-brand consumers
 */

// ── ClinicAccountResponse (GET + PATCH response) ─────────────────────────────

/**
 * ClinicAccountDTO — camelCase mirror of BE ClinicAccountResponse Pydantic DTO.
 * Used as the contract interface for test_fe_be_contract_parity.py.
 *
 * Read-only fields (defined at signup, NEVER in PATCH): country, language, clinicType.
 */
export interface ClinicAccountDTO {
  /** Clinic UUID — BE field: clinic_id → camelCase: clinicId */
  clinicId: string;
  /** Tenant UUID (luana-core-iam) */
  tenantId: string;
  /** Nombre comercial — editable */
  name: string;
  /** Razón social / nombre legal — editable, nullable */
  legalName: string | null;
  /** ID fiscal del tenant (CUIT/RUC/RFC/NIT/RUT) — editable, nullable */
  fiscalId: string | null;
  /** Dirección física — editable, nullable */
  address: string | null;
  /** Teléfono de contacto — editable, nullable */
  phone: string | null;
  /** Correo electrónico — editable, nullable */
  email: string | null;
  /** Moneda ISO 4217 — editable via CurrencySelector */
  currency: string | null;
  /** Zona horaria IANA — editable via TimezoneSelect */
  timezone: string;
  /** País ISO 3166-1 alpha-2 — READ-ONLY (defined at signup) */
  country: string;
  /** Idioma BCP 47 — READ-ONLY (derived from country) */
  language: string;
  /** Tipo de clínica — READ-ONLY (defined at signup) */
  clinicType: string;
  /** Especialidades primarias — editable multi-select */
  primarySpecialties: string[];
  /** Label del fiscal ID según país (e.g. "CUIT", "RUC", "RFC") */
  fiscalIdLabel: string;
}

// ── PATCH request payload (FE → BE) ──────────────────────────────────────────

/**
 * ClinicAccountPatchDTO — partial payload for PATCH /api/v1/clinics/account/.
 * Only editable fields. READ-ONLY fields (country/language/clinicType) MUST NOT
 * be included (BE will reject with 422 if sent).
 */
export interface ClinicAccountPatchDTO {
  name?: string;
  legalName?: string;
  fiscalId?: string;
  address?: string;
  phone?: string;
  email?: string;
  currency?: string;
  timezone?: string;
  primarySpecialties?: string[];
}

// ── Specialty catalog ─────────────────────────────────────────────────────────

/** Entrada del catálogo de especialidades — mirror del BE SpecialtyEntry. */
export interface SpecialtyEntryDTO {
  /** URL-safe slug (lo que persiste config_json.primary_specialties) */
  id: string;
  /** Display name (Spanish neutro LatAm) */
  name: string;
  /** Vitalia tier (1=MVP, 2, 3) */
  tier: number;
}

export interface SpecialtyCatalogDTO {
  /** ISO 3166-1 alpha-2 country code */
  country: string;
  /** Ordered catalog entries for the country ({id, name, tier} — NO string[]) */
  specialties: SpecialtyEntryDTO[];
}

// ── DPO reference ─────────────────────────────────────────────────────────────

export interface DpoReferenceDTO {
  /** DPO full name, or null if not configured */
  name: string | null;
  /** DPO contact email, or null if not configured */
  email: string | null;
  /** Localized role label (e.g. "Responsable de tratamiento de datos") */
  roleLabel: string;
  /** Sub-path to the security/DPO management section */
  manageUrlSubpath: string;
}
