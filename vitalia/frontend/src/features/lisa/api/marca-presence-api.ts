// cap: brand_studio.lisa-marca
// story-origin: vitalia-fase2-s7-TBD
/**
 * marca-presence-api.ts — API client for Lisa Marca Presencia sub-sub-tab.
 *
 * Consumes:
 *   GET  /api/v1/lisa/marca/contact
 *   PUT  /api/v1/lisa/marca/contact
 *   GET  /api/v1/lisa/marca/trust-signals
 *   POST /api/v1/lisa/marca/trust-signals
 *   DELETE /api/v1/lisa/marca/trust-signals/{id}
 *   GET  /api/v1/lisa/marca/trust-catalog/{country_code}
 *   GET  /api/v1/lisa/marca/locations
 *
 * Auth pattern: fetchClient auto-injects X-Tenant-ID + X-Clinic-ID (HIPAA-lite).
 * React Query keys factory: marcaKeys.* (per 03-arch.md conventions).
 *
 * T-7 vitalia-fase2-lisa-marca
 * spec_anchor: 03-arch.md § 4.3 + CONTEXT-BRIEF § 6
 * downstream-regression-na: brand-local vitalia FE API; no cross-brand consumers
 */

import { fetchClient } from "@/lib/api/fetchClient";
import type { TrustSignalsFormValues } from "../types/marca/trust-signals-schema";

/**
 * camelCase patch payload for PUT /lisa/marca/contact.
 * Mirrors BrandContactPatchDTO from 03-arch.md § 4.3.
 */
export interface BrandContactPatchPayload {
  websiteUrl?: string;
  instagramHandle?: string;
  tiktokHandle?: string;
  facebookPage?: string;
  googleBusinessUrl?: string;
  whatsappBusiness?: string;
  yearsExperience?: number;
  patientsCount?: string;
  awards?: string;
}

// ── Response types (camelCase mirrors of Pydantic DTOs per 03-arch.md § 4.3) ─

export interface BrandContactResponse {
  tenantId: string;
  publicLandingUrl: string | null;
  websiteUrl: string | null;
  instagramHandle: string | null;
  tiktokHandle: string | null;
  facebookPage: string | null;
  googleBusinessUrl: string | null;
  updatedAt: string | null; // ISO 8601
}

export interface TrustSignalItem {
  id: string;
  label: string;
  catalogCode: string | null;
  logoUrl: string | null;
  issuedYear: number | null;
  isSeed: boolean;
}

export interface TrustSignalsResponse {
  items: TrustSignalItem[];
}

export interface TrustCatalogItem {
  code: string;
  label: string;
  hint?: string;
}

export interface TrustCatalogResponse {
  country: string;
  items: TrustCatalogItem[];
}

export interface LocationItem {
  id: string;
  name: string;
  address: string;
}

export interface LocationsResponse {
  items: LocationItem[];
}

export interface TrustSignalCreateRequest {
  label: string;
  catalogCode?: string | null;
  issuedYear?: number | null;
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
 * Headers de mutación marca (audit actor + RBAC) — mismo contrato honesto que
 * marca-voice-api::updatePersonality (origin estabilizar-harness-e2e-lisa-marca).
 * X-User-ID = Clerk userId REAL (el BE lo resuelve a users.id); NO el tenantId.
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

// ── Contact endpoints ──────────────────────────────────────────────────────────

export async function getContact(opts: ApiOpts): Promise<BrandContactResponse> {
  return fetchClient<BrandContactResponse>(`/api/v1/lisa/marca/contact`, opts);
}

export async function updateContact(
  opts: ApiOpts,
  payload: BrandContactPatchPayload,
): Promise<BrandContactResponse> {
  return fetchClient<BrandContactResponse>(`/api/v1/lisa/marca/contact`, {
    ...opts,
    method: "PATCH",
    headers: buildMutationHeaders(opts),
    body: JSON.stringify(payload),
  });
}

// ── Trust signals endpoints ────────────────────────────────────────────────────

export async function getTrustSignals(opts: ApiOpts): Promise<TrustSignalsResponse> {
  return fetchClient<TrustSignalsResponse>(`/api/v1/lisa/marca/trust-signals`, opts);
}

export async function createTrustSignal(
  opts: ApiOpts,
  payload: TrustSignalCreateRequest,
): Promise<TrustSignalItem> {
  return fetchClient<TrustSignalItem>(`/api/v1/lisa/marca/trust-signals`, {
    ...opts,
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function deleteTrustSignal(opts: ApiOpts, signalId: string): Promise<void> {
  await fetchClient<void>(`/api/v1/lisa/marca/trust-signals/${signalId}`, {
    ...opts,
    method: "DELETE",
  });
}

export async function updateTrustSignals(
  opts: ApiOpts,
  payload: TrustSignalsFormValues,
): Promise<TrustSignalsResponse> {
  return fetchClient<TrustSignalsResponse>(`/api/v1/lisa/marca/trust-signals`, {
    ...opts,
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

// ── Trust catalog endpoint (OQ-D hybrid) ──────────────────────────────────────

export async function getTrustCatalog(
  opts: ApiOpts,
  countryCode: string,
): Promise<TrustCatalogResponse> {
  return fetchClient<TrustCatalogResponse>(
    `/api/v1/lisa/marca/trust-catalog/${countryCode}`,
    opts,
  );
}

// ── Locations endpoint (read-only from clinics module) ────────────────────────

export async function getLocations(opts: ApiOpts): Promise<LocationsResponse> {
  return fetchClient<LocationsResponse>(`/api/v1/lisa/marca/locations`, opts);
}
