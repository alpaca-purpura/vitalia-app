// cap: clinics.lisa.doctores
// story-origin: vitalia-fase2-lisa-doctores
/**
 * staff.types.ts — TypeScript types for Lisa Staff sub-tab.
 *
 * Mirrors Pydantic DTOs from clinics API (camelCase, ISO 8601 datetimes as string).
 * PHI fields masked in list responses (maskedDni, maskedEmail, maskedPhone).
 *
 * Per ADR-vitalia-004 § 3: RQ + Zustand split.
 * Per vitalia/.claude/rules/hipaa-lite.md: PHI dual-filter tenant+clinic.
 *
 * F1 follow-through (audit fix): field names mirror real BE camelCase contract.
 * BE DoctorListItemDTO uses maskedDni (not dniMasked) per alias_generator=to_camel.
 *
 * T-FE-1 vitalia-fase2-lisa-doctores
 * spec_anchor: 03-arch-fe.md § TypeScript Types + 03-arch-be.md § DTOs
 * downstream-regression-na: brand-local vitalia FE types; no cross-brand consumers
 */

// ── List item (PHI masked for listing) ────────────────────────────────────────

export interface DoctorListItem {
  id: string;
  /** camelCase from BE alias_generator=to_camel */
  tenantId?: string;
  clinicId?: string;
  firstName: string;
  lastName: string;
  displayName?: string | null;
  specialty?: string | null;
  active: boolean;
  visibleEnLanding?: boolean;
  yearsExperience?: number | null;
  languages?: string[];
  /** Avatar storage key — no direct URL in list item */
  avatarKey?: string | null;
  /** Patient count — anonymous aggregate, no PHI */
  patientsCount?: number | null;
  /** NPS score — anonymous aggregate, no PHI */
  npsScore?: number | null;
  /**
   * Masked DNI — e.g. "***567".
   * F1 fix: BE returns maskedDni (to_camel of masked_dni), not dniMasked.
   */
  maskedDni?: string | null;
  maskedEmail?: string | null;
  maskedPhone?: string | null;
  createdAt?: string;
  /** avatarUrl is not in list response — only avatarKey. Derived client-side if needed. */
  avatarUrl?: string | null;
}

// ── Doctor detail (full profile, PHI fields shown only to admin_clinic role) ──

export interface DoctorDetail {
  id: string;
  firstName: string;
  lastName: string;
  /** Encrypted at rest — decrypted only for authorized roles */
  dni: string;
  email: string;
  phone?: string | null;
  specialty?: string | null;
  /** Credential code — e.g. CMP number for PE */
  credential: string;
  credentialCountry: CredentialCountry;
  yearsExperience?: number | null;
  languages: string[];
  bioInputsNotes?: string | null;
  bioLinks: string[];
  bioPublic?: BioPublic | null;
  /** Bio file attachments (D3-B, T-FE-bio-docs). Populated by GET /{id}/bio-files endpoint. */
  bioFiles?: BioFile[];
  avatarKey?: string | null;
  avatarUrl?: string | null;
  visibleEnLanding: boolean;
  active: boolean;
  createdAt: string;
  updatedAt: string;
  // ── D3-D public page fields (T-FE-pagina-publica) ────────────────────────
  /** URL-safe slug for public page (populated by BE after slug assigned) */
  publicSlug?: string | null;
  /** Controls visibility at /d/{clinica-slug}/{doctor-slug} */
  visiblePublic?: boolean;
  /** Structured public profile (populated by GET /{id} with public_profile=true) */
  publicProfile?: DoctorPublicProfile | null;
  clinicSlug?: string | null;
  /** Server-computed generation state (materialNew, generatedAt, materialNewCount) */
  profileState?: ProfileState | null;
}

// ── Bio public sections ────────────────────────────────────────────────────────

export interface BioPublic {
  resumen?: string | null;
  formacion?: string | null;
  enfoque?: string | null;
}

// ── Credential validation (country-specific per business rule) ─────────────────

export type CredentialCountry = "PE" | "AR" | "MX" | "CL";

export const CREDENTIAL_LABELS: Record<CredentialCountry, string> = {
  PE: "CMP",
  AR: "Matrícula nacional",
  MX: "Cédula profesional",
  CL: "Registro nacional",
};

// ── Availability blocks (discriminated union by kind) ──────────────────────────

export type EndConditionKind = "end_date" | "occurrences" | "open_ended";
export type RecurrenceFreq = "weekly" | "biweekly";

export interface RecurrentBlock {
  id: string;
  kind: "recurrent";
  /** D3-F PRIMARY: list of weekday indices, 0=Monday..6=Sunday */
  daysOfWeek: number[];
  /** D3-F PRIMARY: recurrence interval in weeks (1=weekly, 2=biweekly, etc.) */
  interval: number;
  /** LEGACY optional — single day. Populated by BE mapper for old blocks. */
  dayOfWeek?: number;
  /** LEGACY optional — freq shorthand. Populated by BE mapper for old blocks. */
  freq?: RecurrenceFreq;
  startTime: string; // HH:mm 24h
  endTime: string;
  endConditionKind: EndConditionKind;
  endDate?: string | null; // ISO 8601 date
  occurrences?: number | null;
}

export interface OneOffBlock {
  id: string;
  kind: "one_off";
  specificDate: string; // ISO 8601 date
  startTime: string;
  endTime: string;
}

export type AvailabilityBlock = RecurrentBlock | OneOffBlock;

// ── Availability occurrences (BE projection SSoT — T-FE-occurrences-consume) ──

/**
 * AvailabilityOccurrence — mirrors BE AvailabilityOccurrenceDTO (camelCase via alias_generator=to_camel).
 * Paint source: occurrences from BE projection endpoint, NOT client-side recurrence expansion.
 * spec_anchor: 01-spec.md § D3-C.1 | 03-arch-be.md § AvailabilityOccurrenceDTO
 */
export interface AvailabilityOccurrence {
  /** UUID of the parent AvailabilityBlock */
  blockId: string;
  /** ISO 8601 date string — the actual calendar date of this occurrence */
  occurrenceDate: string;
  /** HH:mm 24h */
  startTime: string;
  /** HH:mm 24h */
  endTime: string;
  /** 'recurrent' | 'one_off' */
  kind: "recurrent" | "one_off";
  /** 'weekly' | 'biweekly' — null for one_off */
  freq: "weekly" | "biweekly" | null;
  /** Human-readable summary from BE — e.g. "Cada semana · Lunes 09:00–13:00 · 2 repeticiones" */
  patternSummary: string;
}

// ── Bio documents (T-FE-bio-docs, D3-B) ───────────────────────────────────────

/**
 * BioFile — mirrors BE BioFileDTO (camelCase via alias_generator=to_camel).
 * spec_anchor: 01-spec.md § D3-B | 03-arch-be.md § BioFileDTO
 */
export interface BioFile {
  id: string;
  filename: string;
  sizeBytes: number;
  contentType: string;
  /** ISO 8601 datetime */
  uploadedAt: string;
}

// ── Asset upload response ──────────────────────────────────────────────────────

export interface AssetUploadResponse {
  key: string;
  url: string;
}

// ── API pagination ─────────────────────────────────────────────────────────────

export interface PaginatedDoctors {
  items: DoctorListItem[];
  total: number;
  page: number;
  pageSize: number;
}

// ── Staff filters (URL searchParams) ──────────────────────────────────────────

export interface StaffFilters {
  q?: string;
  specialty?: string;
  active?: "true" | "false" | "";
  page?: number;
}

// ── Structured public profile types (D3-D, T-FE-pagina-publica) ───────────────

/** Formación académica estructurada (mirrors BE StructuredFormacionDTO) */
export interface StructuredFormacion {
  titulo: string;
  institucion?: string | null;
  anio?: number | null;
}

/**
 * Experiencia profesional estructurada (mirrors BE StructuredExperienciaDTO commit 275d5d7e).
 * Real wire shape: {puesto, lugar, anios} — previous {cargo,institucion,desde,hasta,descripcion}
 * was an imagined contract; deleted per auditor finding F2.
 */
export interface StructuredExperiencia {
  puesto: string;
  lugar?: string | null;
  anios?: number | null;
}

// StructuredCertificacion DELETED — BE sends certificaciones as string[] (finding F3)
// StructuredIdioma DELETED — BE sends idiomas as string[] (finding F3)

/**
 * DoctorPublicProfile — structured public profile.
 * Mirrors BE DoctorPublicProfileDTO (camelCase via alias_generator=to_camel).
 * spec_anchor: 01-spec.md § D3-D | 03-arch-be.md § DoctorPublicProfileDTO
 * Anti-enumeration: publicSlug / visiblePublic only on detail (not list).
 */
export interface DoctorPublicProfile {
  sobreMi?: string | null;
  formacion: StructuredFormacion[];
  experiencia: StructuredExperiencia[];
  tratamientos: string[];
  certificaciones: string[];
  idiomas: string[];
}

/**
 * ProfileState — server-computed state for AI generation.
 * Mirrors BE ProfileStateDTO.
 * materialNew: max(bio_files.uploaded_at, inputs/links change) > bio_generated_at
 */
export interface ProfileState {
  /** ISO 8601 datetime of last generation, null if never generated */
  generatedAt: string | null;
  /** True when new material uploaded since last generation */
  materialNew: boolean;
  /** Count of new files/links since last generation */
  materialNewCount: number;
}

/**
 * PublicDoctorPageData — public page response (no auth).
 * Mirrors BE PublicDoctorPageDTO (camelCase).
 * Anti-enumeration: visible: false → BE returns 404 (not this type).
 */
export interface PublicDoctorPageData {
  /** OG-safe display name — never full DNI/email */
  displayName: string;
  specialty?: string | null;
  avatarKey?: string | null;
  clinicName?: string | null;
  credentialLabel?: string | null;
  sobreMi?: string | null;
  formacion?: StructuredFormacion[] | null;
  experiencia?: StructuredExperiencia[] | null;
  tratamientos?: string[] | null;
  certificaciones?: string[] | null;
  idiomas?: string[] | null;
}
