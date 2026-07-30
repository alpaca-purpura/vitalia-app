// cap: brand_studio.lisa-marca
// story-origin: vitalia-fase2-s7-TBD
/**
 * marca.ts — API client for Lisa Marca sub-tab (brand identity admin).
 *
 * Consumes:
 *   GET  /api/v1/lisa/marca/identity
 *   PUT  /api/v1/lisa/marca/identity
 *   GET  /api/v1/lisa/marca/visuals
 *   PUT  /api/v1/lisa/marca/visuals
 *   POST /api/v1/lisa/marca/logos
 *   DELETE /api/v1/lisa/marca/logos
 *
 * Auth pattern: fetchClient auto-injects X-Tenant-ID + X-Clinic-ID (HIPAA-lite).
 * React Query keys factory: marcaKeys.* (per 03-arch.md conventions).
 *
 * T-5 vitalia-fase2-lisa-marca
 * spec_anchor: 03-arch.md § 4 API endpoints + CONTEXT-BRIEF § 6
 * downstream-regression-na: brand-local vitalia FE API; no cross-brand consumers
 */

import { fetchClient } from "@/lib/api/fetchClient";
import type { IdentityFormValues } from "../types/marca/identity-schema";
import type { ClinicVisualsFormValues } from "../types/marca/visuals-schema";

// ── React Query Key Factory ────────────────────────────────────────────────────

export const marcaKeys = {
  all: ["lisa", "marca"] as const,
  identity: (tenantId: string) =>
    [...marcaKeys.all, "identity", tenantId] as const,
  visuals: (tenantId: string) =>
    [...marcaKeys.all, "visuals", tenantId] as const,
  logo: (tenantId: string) => [...marcaKeys.all, "logo", tenantId] as const,
  // T-6 Voz y tono
  personality: (tenantId: string) =>
    [...marcaKeys.all, "personality", tenantId] as const,
  voicePreview: (tenantId: string, blocksHash: string) =>
    [...marcaKeys.all, "voicePreview", tenantId, blocksHash] as const,
  prohibitedPhrases: (tenantId: string) =>
    [...marcaKeys.all, "prohibitedPhrases", tenantId] as const,
  // T-7 Presencia
  contact: (tenantId: string) =>
    [...marcaKeys.all, "contact", tenantId] as const,
  trustSignals: (tenantId: string) =>
    [...marcaKeys.all, "trustSignals", tenantId] as const,
  trustCatalog: (tenantId: string, countryCode: string) =>
    [...marcaKeys.all, "trustCatalog", tenantId, countryCode] as const,
  locations: (tenantId: string) =>
    [...marcaKeys.all, "locations", tenantId] as const,
} as const;

// ── Response types (camelCase mirrors of Pydantic DTOs per 03-arch.md) ────────

export interface IdentityResponse extends IdentityFormValues {
  tenantId: string;
  clinicId: string;
  updatedAt: string; // ISO 8601
  /** Read-only vertical captured in onboarding (mapped from BE clinic_vertical). */
  clinic_vertical?: string;
  /** Read-only specialties list (BE primary_specialties). */
  primary_specialties?: string[];
}

/**
 * Raw shape returned by the vitalia BE `BrandIdentityDTO` (snake_case).
 *
 * ⚠️ NO es la forma del form. El BE vitalia tiene una identidad MÁS chica que la
 * de nicolify (de donde se importó el schema verbatim): solo `name` + `tagline`
 * (+ `clinic_vertical` read-only). `tagline` puede ser `null`. Por eso el cast
 * ciego rompía el form (brand_name=undefined, tagline=null → zod inválido →
 * autosave muerto). Origen: estabilizar-harness-e2e-lisa-marca (de-mock keystone).
 */
interface BrandIdentityApi {
  tenant_id?: string;
  name: string | null;
  slug?: string | null;
  tagline: string | null;
  clinic_vertical?: string | null;
  primary_specialties?: string[] | null;
  updated_at?: string | null;
}

/** Mapea la respuesta del BE → forma del form (null-safe: nunca null/undefined). */
function mapIdentityFromApi(
  raw: BrandIdentityApi,
  opts: ApiOpts,
): IdentityResponse {
  return {
    brand_name: raw.name ?? "",
    tagline: raw.tagline ?? "",
    description: "",
    website: "",
    industry: raw.clinic_vertical ?? "",
    founding_year: "",
    language: "es",
    timezone: "America/Lima",
    clinic_vertical: raw.clinic_vertical ?? "",
    primary_specialties: raw.primary_specialties ?? [],
    tenantId: opts.tenantId,
    clinicId: opts.clinicId ?? "",
    updatedAt: raw.updated_at ?? "",
  };
}

export interface VisualsResponse extends ClinicVisualsFormValues {
  tenantId: string;
  clinicId: string;
  logoUrl: string | null;
  updatedAt: string; // ISO 8601
}

export interface LogoUploadResponse {
  logoUrl: string;
  updatedAt: string;
}

// ── API client options ─────────────────────────────────────────────────────────

interface ApiOpts {
  token: string;
  tenantId: string;
  clinicId?: string | null;
  /** Clerk userId real — se manda como X-User-ID (actor de audit) en mutaciones. */
  userId?: string | null;
  /** Rol vitalia — se manda como X-User-Role (RBAC) en mutaciones. */
  userRole?: string | null;
}

/**
 * Headers de mutación marca (audit actor + RBAC). Mismo contrato honesto que
 * marca-voice-api::updatePersonality (origin estabilizar-harness-e2e-lisa-marca:
 * el de-mock reveló que identity/visuals/contact mandaban PUT sin actor → 405/403).
 * X-User-ID = Clerk userId REAL (lo resuelve el BE a users.id); NO el tenantId.
 */
function buildMutationHeaders(opts: ApiOpts): Record<string, string> {
  if (!opts.userId) {
    throw new Error(
      "marca mutation requires an authenticated Clerk userId (X-User-ID audit actor)",
    );
  }
  return {
    "X-User-ID": opts.userId,
    "X-User-Role": opts.userRole ?? "owner",
  };
}

// ── Identity endpoints ─────────────────────────────────────────────────────────

export async function getIdentity(opts: ApiOpts): Promise<IdentityResponse> {
  const raw = await fetchClient<BrandIdentityApi>(
    `/api/v1/lisa/marca/identity`,
    opts,
  );
  return mapIdentityFromApi(raw, opts);
}

export async function updateIdentity(
  opts: ApiOpts,
  payload: Partial<IdentityFormValues>,
): Promise<IdentityResponse> {
  // Mapea form→BE: el BE solo acepta `name` + `tagline` (BrandIdentityPatchDTO).
  // - name: se OMITE si está vacío (el BE exige min_length=2 → mandar "" = 422).
  // - tagline: "" del form → null en BE (limpia el campo); undefined → no se toca.
  const body: { name?: string; tagline?: string | null } = {};
  if (payload.brand_name) body.name = payload.brand_name;
  if (payload.tagline !== undefined) {
    body.tagline = payload.tagline ? payload.tagline : null;
  }

  const raw = await fetchClient<BrandIdentityApi>(`/api/v1/lisa/marca/identity`, {
    ...opts,
    method: "PATCH",
    headers: buildMutationHeaders(opts),
    body: JSON.stringify(body),
  });
  return mapIdentityFromApi(raw, opts);
}

// ── Visuals endpoints ──────────────────────────────────────────────────────────

export async function getVisuals(opts: ApiOpts): Promise<VisualsResponse> {
  return fetchClient<VisualsResponse>(
    `/api/v1/lisa/marca/visuals`,
    opts,
  );
}

/**
 * Campos que el BE `BrandVisualsPatchDTO` acepta (extra="forbid"). El form FE
 * tiene MUCHOS más (importados de nicolify) + el response trae
 * tenantId/clinicId/logoUrl/updatedAt → mandar el objeto completo daba 422.
 */
const ALLOWED_VISUALS_FIELDS = [
  "primary_color",
  "accent_color",
  "background_color",
  "text_primary_color",
  "font_heading",
  "font_body",
] as const;

export async function updateVisuals(
  opts: ApiOpts,
  payload: Partial<ClinicVisualsFormValues>,
): Promise<VisualsResponse> {
  // Whitelist a los 6 campos del BE + omitir vacíos: los colores deben matchear
  // ^#RRGGBB (mandar "" daría 422); los fonts vacíos tampoco se mandan.
  const body: Record<string, string> = {};
  for (const key of ALLOWED_VISUALS_FIELDS) {
    const value = (payload as Record<string, unknown>)[key];
    if (typeof value === "string" && value !== "") body[key] = value;
  }

  return fetchClient<VisualsResponse>(`/api/v1/lisa/marca/visuals`, {
    ...opts,
    method: "PATCH",
    headers: buildMutationHeaders(opts),
    body: JSON.stringify(body),
  });
}

// ── Logo endpoints ─────────────────────────────────────────────────────────────

export async function uploadLogo(
  opts: ApiOpts,
  file: File,
): Promise<LogoUploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  // fetchClient sets Content-Type JSON by default; for FormData we override
  const { token, tenantId, clinicId, userId, userRole } = opts;
  // El BE POST /logos exige X-User-ID (Header sin default) + rol brand_owner
  // (_brand_owner_required) → sin estos headers daba 403/422. Mismo contrato de
  // actor honesto que las mutaciones PATCH (X-User-ID = Clerk userId real).
  if (!userId) {
    throw new Error(
      "logo upload requires an authenticated Clerk userId (X-User-ID audit actor)",
    );
  }
  const headers: Record<string, string> = {
    Authorization: `Bearer ${token}`,
    "X-Tenant-ID": tenantId,
    "X-User-ID": userId,
    "X-User-Role": userRole ?? "owner",
  };
  if (clinicId) headers["X-Clinic-ID"] = clinicId;

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 60_000); // 60s for uploads

  let response: Response;
  try {
    response = await fetch(`/api/v1/lisa/marca/logos`, {
      method: "POST",
      headers,
      body: formData,
      signal: controller.signal,
    });
  } finally {
    clearTimeout(timeoutId);
  }

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(`Logo upload failed: ${response.status} ${JSON.stringify(body)}`);
  }

  return response.json() as Promise<LogoUploadResponse>;
}

export async function deleteLogo(opts: ApiOpts): Promise<void> {
  // El BE DELETE /logos exige X-User-ID (actor del audit) + rol brand_owner
  // (_brand_owner_required) → sin estos headers daba 403/422. Mismo contrato de
  // actor honesto que upload + las mutaciones PATCH. Una sola marca = un solo logo
  // (visuals.logo_url), por eso la ruta NO lleva {logo_id} en el path.
  await fetchClient<void>(`/api/v1/lisa/marca/logos`, {
    ...opts,
    method: "DELETE",
    headers: buildMutationHeaders(opts),
  });
}
