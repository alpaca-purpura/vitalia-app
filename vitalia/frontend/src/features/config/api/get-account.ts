// cap: configuracion.cuenta
// story-origin: vitalia-fase2-config-cuenta
/**
 * get-account.ts — GET /api/v1/clinics/account/ (trailing slash mandatory).
 *
 * Camelize boundary: snake_case BE response → camelCase FE view-model (ClinicAccountDTO).
 * fetchClient auto-injects X-Tenant-ID + X-Clinic-ID (HIPAA-lite dual filter).
 *
 * T-1 vitalia-fase2-config-cuenta
 * spec_anchor: 03-arch.md § 4 (API routes) + § 5 (types)
 * downstream-regression-na: brand-local vitalia FE API; no cross-brand consumers
 */

import { fetchClient } from "@/lib/api/fetchClient";
import { keysToCamel } from "@/lib/api/keys-to-camel";
import type { ClinicAccountDTO, SpecialtyCatalogDTO, DpoReferenceDTO } from "../types/cuenta.types";

export interface AccountFetchOptions {
  token: string;
  tenantId: string;
  clinicId?: string | null;
  /** Clerk userId real — el account_router exige X-User-ID en TODAS las routes (422 si falta). */
  userId: string;
}

// ── React Query key factory ───────────────────────────────────────────────────

export const cuentaKeys = {
  all: (tenantId: string) => ["cuenta", tenantId] as const,
  account: (tenantId: string) => ["cuenta", tenantId, "account"] as const,
  specialtyCatalog: (tenantId: string) => ["cuenta", tenantId, "specialty-catalog"] as const,
  dpo: (tenantId: string) => ["cuenta", tenantId, "dpo"] as const,
} as const;

// ── GET /api/v1/clinics/account/ ─────────────────────────────────────────────

/**
 * Fetches the tenant's clinic account data.
 * Applies camelize boundary: snake_case JSON → ClinicAccountDTO (camelCase).
 */
export async function getAccount(opts: AccountFetchOptions): Promise<ClinicAccountDTO> {
  // NOTE: trailing slash is MANDATORY (redirect_slashes=False on BE).
  const raw = await fetchClient<unknown>("/api/v1/clinics/account/", {
    token: opts.token,
    tenantId: opts.tenantId,
    clinicId: opts.clinicId,
    headers: { "X-User-ID": opts.userId },
  });
  return keysToCamel<ClinicAccountDTO>(raw);
}

// ── GET /api/v1/clinics/account/specialties-catalog ──────────────────────────

/**
 * Fetches the specialty catalog for the tenant's country.
 * No trailing slash (path has a suffix segment, no ambiguity).
 */
export async function getSpecialtyCatalog(opts: AccountFetchOptions): Promise<SpecialtyCatalogDTO> {
  const raw = await fetchClient<unknown>("/api/v1/clinics/account/specialties-catalog", {
    token: opts.token,
    tenantId: opts.tenantId,
    clinicId: opts.clinicId,
    headers: { "X-User-ID": opts.userId },
  });
  return keysToCamel<SpecialtyCatalogDTO>(raw);
}

// ── GET /api/v1/clinics/account/dpo ──────────────────────────────────────────

/**
 * Fetches the DPO (responsible party) reference for the tenant.
 */
export async function getDpoReference(opts: AccountFetchOptions): Promise<DpoReferenceDTO> {
  const raw = await fetchClient<unknown>("/api/v1/clinics/account/dpo", {
    token: opts.token,
    tenantId: opts.tenantId,
    clinicId: opts.clinicId,
    headers: { "X-User-ID": opts.userId },
  });
  return keysToCamel<DpoReferenceDTO>(raw);
}
