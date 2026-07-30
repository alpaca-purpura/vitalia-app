// cap: lisa.servicios
// story-origin: vitalia-fase2-lisa-servicios T-6
/**
 * servicios.ts — React Query hooks for Lisa Servicios (offer catalog + escalera).
 *
 * Hooks (T-6):
 *   - useServicios(filters)        — paginated catalog list (GET /offer/servicios)
 *   - useEscalera()                — full list grouped by value_level (escalera view)
 *   - useBiblioteca(q, clinicType) — standard-library search (empty-state invite)
 *   - useCreateServicioCustom()    — POST custom service (returns ServiceDetail)
 *   - useCreateServicioFromTemplate() — POST from biblioteca template (returns ServiceDetail)
 *   - useActivateServicio()        — POST activate (catalog Switch)
 *   - useSoftDeleteServicio()      — DELETE (soft, kebab ⋮)
 *   - useMoveRung()                — escalera drag → PATCH value_level
 *
 * ★ T-7 DRIFT FIX (path-drift finding — same class as the 2026-06-04 embudo
 *   imagined-contract trap): T-6 wired English paths `/offer/services` + params
 *   `q`/`is_active`/`page_size` + activate as PATCH + create→ListItem. The shipped
 *   BE (servicios_router.py) speaks SPANISH `/offer/servicios`, params
 *   `search`/`active`(bool)/`cursor`, activate is POST, create returns
 *   ServiceDetailDTO, and EVERY mutation needs X-User-ID (audit actor). next.config
 *   has a 1:1 `/api/*` rewrite (no English→Spanish map) → the T-6 hooks were 404-ing
 *   live. All corrected here so the catalog + workspace integrate live.
 *
 * ★ WIRE = snake_case (offer module — from_attributes, NO to_camel). See servicios.types.ts.
 *
 * ★ value_level GAP (useMoveRung): the SHIPPED ServicePatchRequest is `extra="forbid"`
 *   and exposes NO value_level → a PATCH({value_level}) returns 422. useMoveRung
 *   therefore DEGRADES to an optimistic-cache-only move with a toast warning + a
 *   documented no-op on the wire (the BE field is an Upstream deficiency, see
 *   T-6-impl-log.md). When the BE wires value_level, flip USE_VALUE_LEVEL_PATCH.
 *
 * React Query key convention ([module, subtab, action, ...filters], arch test
 * test_react_query_keys_convention):
 *   ['offer','servicios','list',filters]
 *   ['offer','servicios','escalera']
 *   ['offer','biblioteca','search',q]
 *   ['offer','servicios','detail',offerId]   (T-7 consumes detail)
 *
 * Auth: useAuth() → getToken() + useTenantId() (NEVER useAuth().orgId — arch test
 * test-no-clerk-organizations). Catalog is NOT PHI (RN-13) → no X-Clinic-ID on
 * list/escalera; only Case writes (T-7) carry it.
 *
 * T-6 vitalia-fase2-lisa-servicios
 * spec_anchor: 03-arch-fe.md § Data layer + § React Query keys
 * downstream-regression-na: brand-local vitalia FE API; no cross-brand consumers
 */

"use client";

import { useCallback, useRef } from "react";
import {
  useQuery,
  useMutation,
  useQueryClient,
} from "@tanstack/react-query";
import { useAuth } from "@clerk/nextjs";
import { toast } from "sonner";
import { useTenantId } from "@/hooks/useTenantId";
import { useActorHeaders } from "@/hooks/useActorHeaders";
import { useClinicId } from "@/hooks/useClinicId";
import type { EntitySearchFn } from "@luana/ui-kit";
import { fetchClient } from "@/lib/api/fetchClient";
import type {
  ServiceListResponse,
  ServiceListItem,
  ServiceDetail,
  BibliotecaSearchResponse,
  ServiceCreateCustomRequest,
  ServiceCreateFromTemplateRequest,
  ServiciosFilters,
  OfferValueLevel,
  ServicePatchRequest,
  SalesBriefPatchRequest,
  SpecialistLinkRequest,
  TestimonialCreateRequest,
  CaseCreateRequest,
  KnowledgeExtractRequest,
  KnowledgeExtractResponse,
  // Nested-resource responses — the BE returns the SUB-DTO (NOT the full
  // ServiceDetail). G2-F3 (lisa-servicios round 2): typing these as
  // ServiceDetail + setQueryData(detail) corrupted the cache (public_name lost)
  // → EntityPicker crash. We type honestly + invalidate detail to refetch.
  SalesBrief,
  SpecialistLink,
  ServiceTestimonial,
  ServiceCase,
} from "../types/servicios.types";

// Client-side calls go SAME-ORIGIN relative (`/api/v1/offer/...`). See staff.ts
// for the CORS rationale (absolute base cross-origins the browser). Server-side
// fetches live in servicios-server.ts with the absolute NEXT_PUBLIC_API_URL.
const API_BASE = "";

/**
 * value_level move PATCH is NOT wired on the BE yet (ServicePatchRequest extra="forbid").
 * Keep this OFF until the BE adds the field; the escalera move then becomes a real PATCH.
 */
const USE_VALUE_LEVEL_PATCH = false;


// ── Query key factory ──────────────────────────────────────────────────────────

export const serviciosKeys = {
  all: ["offer", "servicios"] as const,
  lists: () => [...serviciosKeys.all, "list"] as const,
  list: (filters: ServiciosFilters) =>
    [...serviciosKeys.lists(), filters] as const,
  escalera: () => [...serviciosKeys.all, "escalera"] as const,
  details: () => [...serviciosKeys.all, "detail"] as const,
  detail: (offerId: string) => [...serviciosKeys.details(), offerId] as const,
  biblioteca: (q: string) => ["offer", "biblioteca", "search", q] as const,
};

// ── Request helpers ──────────────────────────────────────────────────────────────

function buildListParams(filters: ServiciosFilters): URLSearchParams {
  // BE list params (servicios_router.list_services): search / category / active(bool) /
  // origin / cursor. NO page_size — the endpoint paginates by cursor.
  const params = new URLSearchParams();
  if (filters.search) params.set("search", filters.search);
  if (filters.category) params.set("category", filters.category);
  if (filters.active !== "all") {
    params.set("active", filters.active === "active" ? "true" : "false");
  }
  return params;
}

// ── useServicios (catalog list) ──────────────────────────────────────────────────

export interface UseServiciosOptions {
  filters: ServiciosFilters;
  initialData?: ServiceListResponse;
}

/**
 * useServicios — paginated catalog list. SSR initialData seeds ONLY the default
 * (unfiltered) view so any search/filter change is a fresh key that hits the BE
 * (mirrors the staff.ts bug-2026-06-07 fix).
 */
export function useServicios({ filters, initialData }: UseServiciosOptions) {
  const { getToken, isLoaded, isSignedIn } = useAuth();
  const tenantId = useTenantId();

  const isDefaultFilters =
    !filters.search && !filters.category && filters.active === "all";

  return useQuery({
    queryKey: serviciosKeys.list(filters),
    queryFn: async () => {
      const token = await getToken();
      if (!token || !tenantId) throw new Error("Sin autenticación");
      const params = buildListParams(filters);
      return fetchClient<ServiceListResponse>(
        `${API_BASE}/api/v1/offer/servicios?${params.toString()}`,
        { token, tenantId },
      );
    },
    enabled: isLoaded && isSignedIn && !!tenantId,
    initialData: isDefaultFilters ? initialData : undefined,
    staleTime: 30_000,
  });
}

// ── useEscalera (full list for the ladder grouping) ──────────────────────────────

export interface UseEscaleraOptions {
  initialData?: ServiceListResponse;
}

/**
 * useEscalera — fetches the catalog (first cursor page) so the escalera can group
 * services by value_level client-side. The BE paginates by cursor (no page_size);
 * the catalog is small enough that the first page covers the ladder today. Until
 * the BE wires value_level, grouping falls back to "unassigned" (EscaleraView).
 */
export function useEscalera({ initialData }: UseEscaleraOptions = {}) {
  const { getToken, isLoaded, isSignedIn } = useAuth();
  const tenantId = useTenantId();

  return useQuery({
    queryKey: serviciosKeys.escalera(),
    queryFn: async () => {
      const token = await getToken();
      if (!token || !tenantId) throw new Error("Sin autenticación");
      return fetchClient<ServiceListResponse>(
        `${API_BASE}/api/v1/offer/servicios`,
        { token, tenantId },
      );
    },
    enabled: isLoaded && isSignedIn && !!tenantId,
    initialData,
    staleTime: 30_000,
  });
}

// ── useBiblioteca (standard-library search) ──────────────────────────────────────

/**
 * useBiblioteca — standard-library typeahead. BE GET /biblioteca/search requires
 * BOTH `q` (default "") AND `clinic_type` (REQUIRED query param). The clinic_type
 * scopes the canonical library to the tenant's specialty; the query is disabled
 * until a clinicType is known so we never fire a 422 (missing required param).
 */
export function useBiblioteca(q: string, clinicType: string | null | undefined) {
  const { getToken, isLoaded, isSignedIn } = useAuth();
  const tenantId = useTenantId();

  return useQuery({
    queryKey: [...serviciosKeys.biblioteca(q), clinicType ?? ""] as const,
    queryFn: async () => {
      const token = await getToken();
      if (!token || !tenantId) throw new Error("Sin autenticación");
      if (!clinicType) throw new Error("Falta el tipo de clínica");
      const params = new URLSearchParams();
      params.set("q", q);
      params.set("clinic_type", clinicType);
      return fetchClient<BibliotecaSearchResponse>(
        `${API_BASE}/api/v1/offer/biblioteca/search?${params.toString()}`,
        { token, tenantId },
      );
    },
    enabled: isLoaded && isSignedIn && !!tenantId && !!clinicType,
    staleTime: 60_000,
  });
}

// ── Mutations ────────────────────────────────────────────────────────────────────

/**
 * Shared auth resolver for mutations.
 *
 * ★ Every offer-module write needs the audit actor header X-User-ID (the DB user
 *   UUID resolved from /iam/users/me — see useActorHeaders). The resolver returns
 *   that header so callers can spread it into `headers`. The actor header is read
 *   at call time so it reflects the resolved /me cache. specialist-link + case
 *   writes additionally carry X-Clinic-ID (passed via fetchClient `clinicId`).
 */
function useMutationAuth() {
  const { getToken } = useAuth();
  const tenantId = useTenantId();
  const actorHeaders = useActorHeaders();
  return useCallback(async () => {
    const token = await getToken();
    if (!token || !tenantId) throw new Error("Sin autenticación");
    if (!actorHeaders["X-User-ID"]) throw new Error("Actor no resuelto");
    return { token, tenantId, actorHeaders };
  }, [getToken, tenantId, actorHeaders]);
}

export function useCreateServicioCustom() {
  const queryClient = useQueryClient();
  const resolveAuth = useMutationAuth();
  return useMutation({
    mutationFn: async (payload: ServiceCreateCustomRequest) => {
      const { token, tenantId, actorHeaders } = await resolveAuth();
      // BE returns ServiceDetailDTO (NOT a list item) so the workspace can navigate
      // straight into [offer-id] with the draft already hydrated.
      return fetchClient<ServiceDetail>(
        `${API_BASE}/api/v1/offer/servicios/custom`,
        {
          token,
          tenantId,
          method: "POST",
          headers: actorHeaders,
          body: JSON.stringify(payload),
        },
      );
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: serviciosKeys.lists() });
      void queryClient.invalidateQueries({ queryKey: serviciosKeys.escalera() });
    },
  });
}

export function useCreateServicioFromTemplate() {
  const queryClient = useQueryClient();
  const resolveAuth = useMutationAuth();
  return useMutation({
    mutationFn: async (payload: ServiceCreateFromTemplateRequest) => {
      const { token, tenantId, actorHeaders } = await resolveAuth();
      return fetchClient<ServiceDetail>(
        `${API_BASE}/api/v1/offer/servicios/from-template`,
        {
          token,
          tenantId,
          method: "POST",
          headers: actorHeaders,
          body: JSON.stringify(payload),
        },
      );
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: serviciosKeys.lists() });
      void queryClient.invalidateQueries({ queryKey: serviciosKeys.escalera() });
    },
  });
}

export function useActivateServicio() {
  const queryClient = useQueryClient();
  const resolveAuth = useMutationAuth();
  return useMutation({
    mutationFn: async ({
      offerId,
      isActive,
    }: {
      offerId: string;
      isActive: boolean;
    }) => {
      const { token, tenantId, actorHeaders } = await resolveAuth();
      // BE activate is a POST (state transition), NOT a PATCH.
      return fetchClient<ServiceDetail>(
        `${API_BASE}/api/v1/offer/servicios/${offerId}/activate`,
        {
          token,
          tenantId,
          method: "POST",
          headers: actorHeaders,
          body: JSON.stringify({ is_active: isActive }),
        },
      );
    },
    onSuccess: (detail, { offerId }) => {
      // G2-F2b: activate returns the full ServiceDetailDTO → seed the workspace
      // detail cache so the StatusBar switch reflects the new state WITHOUT a
      // full refresh (it previously only invalidated lists/escalera).
      queryClient.setQueryData(serviciosKeys.detail(offerId), detail);
      void queryClient.invalidateQueries({ queryKey: serviciosKeys.lists() });
      void queryClient.invalidateQueries({ queryKey: serviciosKeys.escalera() });
    },
  });
}

export function useSoftDeleteServicio() {
  const queryClient = useQueryClient();
  const resolveAuth = useMutationAuth();
  return useMutation({
    mutationFn: async (offerId: string) => {
      const { token, tenantId, actorHeaders } = await resolveAuth();
      return fetchClient<void>(
        `${API_BASE}/api/v1/offer/servicios/${offerId}`,
        { token, tenantId, method: "DELETE", headers: actorHeaders },
      );
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: serviciosKeys.lists() });
      void queryClient.invalidateQueries({ queryKey: serviciosKeys.escalera() });
    },
  });
}

/**
 * useMoveRung — escalera drag moves a service to a different rung (value_level).
 *
 * ★ DEGRADED: the BE has no value_level field on ServicePatchRequest (extra="forbid")
 *   → a real PATCH would 422. While USE_VALUE_LEVEL_PATCH is false this performs an
 *   optimistic cache move + an informative toast, and does NOT hit the wire.
 *   The structural gap is an Upstream deficiency (architect wrote a contract the
 *   shipped BE doesn't honour) — see T-6-impl-log.md § Upstream deficiency.
 */
export function useMoveRung() {
  const queryClient = useQueryClient();
  const resolveAuth = useMutationAuth();
  return useMutation({
    mutationFn: async ({
      offerId,
      toRung,
    }: {
      offerId: string;
      toRung: OfferValueLevel;
    }) => {
      if (!USE_VALUE_LEVEL_PATCH) {
        // Documented no-op: the BE rejects value_level today.
        return { offerId, toRung, persisted: false } as const;
      }
      const { token, tenantId, actorHeaders } = await resolveAuth();
      await fetchClient<ServiceDetail>(
        `${API_BASE}/api/v1/offer/servicios/${offerId}`,
        {
          token,
          tenantId,
          method: "PATCH",
          headers: actorHeaders,
          body: JSON.stringify({ value_level: toRung }),
        },
      );
      return { offerId, toRung, persisted: true } as const;
    },
    onMutate: async ({ offerId, toRung }) => {
      // Optimistic move so the card lands in the target rung immediately.
      await queryClient.cancelQueries({ queryKey: serviciosKeys.escalera() });
      const prev = queryClient.getQueryData<ServiceListResponse>(
        serviciosKeys.escalera(),
      );
      if (prev) {
        queryClient.setQueryData<ServiceListResponse>(serviciosKeys.escalera(), {
          ...prev,
          items: prev.items.map((it) =>
            it.offer_id === offerId ? { ...it, value_level: toRung } : it,
          ),
        });
      }
      return { prev };
    },
    onError: (_err, _vars, ctx) => {
      if (ctx?.prev) {
        queryClient.setQueryData(serviciosKeys.escalera(), ctx.prev);
      }
    },
    onSuccess: (result) => {
      if (!result.persisted) {
        toast.info("La escalera todavía no guarda el peldaño", {
          description:
            "El movimiento se verá en pantalla, pero aún no se persiste (pendiente del backend).",
        });
      }
    },
  });
}

// ════════════════════════════════════════════════════════════════════════════════
//  T-7 WORKSPACE HOOKS — the servicio detail surface (5 leaves + autosave + roster)
//
//  Header matrix (verbatim from servicios_router.py):
//    GET detail                         → X-Tenant-ID only (catalog is NOT PHI, RN-13)
//    PATCH /servicios/{id}              → X-Tenant-ID + X-User-ID
//    PATCH /servicios/{id}/sales-brief  → X-Tenant-ID + X-User-ID
//    POST  /servicios/{id}/knowledge/extract → X-Tenant-ID + X-User-ID
//    POST/DELETE testimonials           → X-Tenant-ID + X-User-ID
//    POST  /servicios/{id}/specialists  → X-Tenant-ID + X-User-ID + X-Clinic-ID
//    DELETE /servicios/{id}/specialists/{doctor_id} → X-Tenant-ID + X-User-ID (no clinic)
//    POST/DELETE cases (PHI)            → X-Tenant-ID + X-User-ID + X-Clinic-ID
// ════════════════════════════════════════════════════════════════════════════════

// ── useServicioDetail (workspace detail) ─────────────────────────────────────────

export interface UseServicioDetailOptions {
  offerId: string;
  initialData?: ServiceDetail;
}

/**
 * useServicioDetail — the full workspace detail (sales_brief + specialists + cases
 * + testimonials nested). G2-F13: passes X-Clinic-ID so the BE can enrich
 * SpecialistLinkDTO with display_name + specialty (dual-scoped roster join).
 * clinicId may be null for tenants without a resolved clinic; the BE degrades
 * gracefully (display_name = null) when the header is absent.
 * SSR seeds initialData so the workspace renders without a fetch flash on first paint.
 */
export function useServicioDetail({
  offerId,
  initialData,
}: UseServicioDetailOptions) {
  const { getToken, isLoaded, isSignedIn } = useAuth();
  const tenantId = useTenantId();
  const clinicId = useClinicId();

  return useQuery({
    queryKey: serviciosKeys.detail(offerId),
    queryFn: async () => {
      const token = await getToken();
      if (!token || !tenantId) throw new Error("Sin autenticación");
      return fetchClient<ServiceDetail>(
        `${API_BASE}/api/v1/offer/servicios/${offerId}`,
        { token, tenantId, clinicId },
      );
    },
    enabled: isLoaded && isSignedIn && !!tenantId && !!offerId,
    initialData,
    staleTime: 30_000,
  });
}

// ── usePatchField (per-field autosave) ───────────────────────────────────────────

/**
 * usePatchField — PATCH a single core field of a servicio (public_name / price /
 * category / modality). Wired to the autosave indicator at the page level. Only
 * the `extra="forbid"` ServicePatchRequest fields are accepted; value_level is
 * NOT a patchable field (see GAP note).
 */
export function usePatchField(offerId: string) {
  const queryClient = useQueryClient();
  const resolveAuth = useMutationAuth();
  return useMutation({
    mutationFn: async (patch: ServicePatchRequest) => {
      const { token, tenantId, actorHeaders } = await resolveAuth();
      return fetchClient<ServiceDetail>(
        `${API_BASE}/api/v1/offer/servicios/${offerId}`,
        {
          token,
          tenantId,
          method: "PATCH",
          headers: actorHeaders,
          body: JSON.stringify(patch),
        },
      );
    },
    onSuccess: (detail) => {
      queryClient.setQueryData(serviciosKeys.detail(offerId), detail);
      void queryClient.invalidateQueries({ queryKey: serviciosKeys.lists() });
    },
  });
}

// ── useSalesBriefPatch ("Para Adrián" autosave) ──────────────────────────────────

/**
 * useSalesBriefPatch — PATCH the sales brief ("Para Adrián" leaf). All fields
 * optional; sent per-field by the autosave coalescer. The BE returns the
 * SalesBrief sub-DTO (NOT the full ServiceDetail) → we invalidate the detail
 * query to refetch the authoritative workspace state (G2-F3 cache-corruption fix).
 */
export function useSalesBriefPatch(offerId: string) {
  const queryClient = useQueryClient();
  const resolveAuth = useMutationAuth();
  return useMutation({
    mutationFn: async (patch: SalesBriefPatchRequest) => {
      const { token, tenantId, actorHeaders } = await resolveAuth();
      return fetchClient<SalesBrief>(
        `${API_BASE}/api/v1/offer/servicios/${offerId}/sales-brief`,
        {
          token,
          tenantId,
          method: "PATCH",
          headers: actorHeaders,
          body: JSON.stringify(patch),
        },
      );
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: serviciosKeys.detail(offerId) });
    },
  });
}

// ── Specialists (link / unlink) ──────────────────────────────────────────────────

/**
 * useLinkSpecialist — POST a doctor onto the servicio. Carries X-Clinic-ID
 * (specialist link is clinic-scoped). doctor_id in the body.
 */
export function useLinkSpecialist(offerId: string) {
  const queryClient = useQueryClient();
  const resolveAuth = useMutationAuth();
  const clinicId = useClinicId();
  return useMutation({
    mutationFn: async (doctorId: string) => {
      const { token, tenantId, actorHeaders } = await resolveAuth();
      if (!clinicId) throw new Error("Falta la clínica activa");
      const payload: SpecialistLinkRequest = { doctor_id: doctorId };
      return fetchClient<SpecialistLink>(
        `${API_BASE}/api/v1/offer/servicios/${offerId}/specialists`,
        {
          token,
          tenantId,
          clinicId,
          method: "POST",
          headers: actorHeaders,
          body: JSON.stringify(payload),
        },
      );
    },
    // BE returns SpecialistLinkDTO (NOT ServiceDetail) → refetch the authoritative
    // detail instead of overwriting it with a partial (G2-F3 root cause).
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: serviciosKeys.detail(offerId) });
    },
  });
}

/**
 * useUnlinkSpecialist — DELETE a doctor from the servicio. doctor_id is IN THE
 * PATH (not the body); unlink does NOT carry X-Clinic-ID.
 */
export function useUnlinkSpecialist(offerId: string) {
  const queryClient = useQueryClient();
  const resolveAuth = useMutationAuth();
  return useMutation({
    mutationFn: async (doctorId: string) => {
      const { token, tenantId, actorHeaders } = await resolveAuth();
      return fetchClient<void>(
        `${API_BASE}/api/v1/offer/servicios/${offerId}/specialists/${doctorId}`,
        { token, tenantId, method: "DELETE", headers: actorHeaders },
      );
    },
    // BE returns 204 No Content → invalidate detail (overwriting with the empty
    // body wiped the cache → EntityPicker crash, G2-F3).
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: serviciosKeys.detail(offerId) });
    },
  });
}

// ── Prueba social: testimonials + cases ──────────────────────────────────────────

/** useAddTestimonial — POST a testimonial (NOT PHI). */
export function useAddTestimonial(offerId: string) {
  const queryClient = useQueryClient();
  const resolveAuth = useMutationAuth();
  return useMutation({
    mutationFn: async (payload: TestimonialCreateRequest) => {
      const { token, tenantId, actorHeaders } = await resolveAuth();
      return fetchClient<ServiceTestimonial>(
        `${API_BASE}/api/v1/offer/servicios/${offerId}/testimonials`,
        {
          token,
          tenantId,
          method: "POST",
          headers: actorHeaders,
          body: JSON.stringify(payload),
        },
      );
    },
    // BE returns TestimonialDTO (NOT ServiceDetail) → invalidate detail (G2-F3).
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: serviciosKeys.detail(offerId) });
    },
  });
}

/** useRemoveTestimonial — DELETE a testimonial by id (in path). */
export function useRemoveTestimonial(offerId: string) {
  const queryClient = useQueryClient();
  const resolveAuth = useMutationAuth();
  return useMutation({
    mutationFn: async (testimonialId: string) => {
      const { token, tenantId, actorHeaders } = await resolveAuth();
      return fetchClient<void>(
        `${API_BASE}/api/v1/offer/servicios/${offerId}/testimonials/${testimonialId}`,
        { token, tenantId, method: "DELETE", headers: actorHeaders },
      );
    },
    // BE returns 204 No Content → invalidate detail (G2-F3).
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: serviciosKeys.detail(offerId) });
    },
  });
}

/**
 * useAddCase — POST a before/after case. This is PHI → carries X-Clinic-ID. The
 * BE gates on consent (consent_signed=false → 422 RN-33); the caller surfaces the
 * consent error to the user.
 */
export function useAddCase(offerId: string) {
  const queryClient = useQueryClient();
  const resolveAuth = useMutationAuth();
  const clinicId = useClinicId();
  return useMutation({
    mutationFn: async (payload: CaseCreateRequest) => {
      const { token, tenantId, actorHeaders } = await resolveAuth();
      if (!clinicId) throw new Error("Falta la clínica activa");
      return fetchClient<ServiceCase>(
        `${API_BASE}/api/v1/offer/servicios/${offerId}/cases`,
        {
          token,
          tenantId,
          clinicId,
          method: "POST",
          headers: actorHeaders,
          body: JSON.stringify(payload),
        },
      );
    },
    // BE returns CaseDTO (NOT ServiceDetail) → invalidate detail (G2-F3).
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: serviciosKeys.detail(offerId) });
    },
  });
}

/** useRemoveCase — DELETE a case by id (PHI → X-Clinic-ID). */
export function useRemoveCase(offerId: string) {
  const queryClient = useQueryClient();
  const resolveAuth = useMutationAuth();
  const clinicId = useClinicId();
  return useMutation({
    mutationFn: async (caseId: string) => {
      const { token, tenantId, actorHeaders } = await resolveAuth();
      if (!clinicId) throw new Error("Falta la clínica activa");
      return fetchClient<void>(
        `${API_BASE}/api/v1/offer/servicios/${offerId}/cases/${caseId}`,
        { token, tenantId, clinicId, method: "DELETE", headers: actorHeaders },
      );
    },
    // BE returns 204 No Content → invalidate detail (G2-F3).
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: serviciosKeys.detail(offerId) });
    },
  });
}

// ── Knowledge extraction (Sub-phase A: extract-only) ─────────────────────────────

/**
 * useProcessDocument — POST a document URL/filename to Lisa for field extraction
 * ("Procesar con Lisa"). Returns the prefill payload the workspace uses to ✨
 * pre-fill the Resumen fields. RAG ingest is OUT of scope (Sub-phase A).
 */
export function useProcessDocument(offerId: string) {
  const resolveAuth = useMutationAuth();
  return useMutation({
    mutationFn: async (payload: KnowledgeExtractRequest) => {
      const { token, tenantId, actorHeaders } = await resolveAuth();
      return fetchClient<KnowledgeExtractResponse>(
        `${API_BASE}/api/v1/offer/servicios/${offerId}/knowledge/extract`,
        {
          token,
          tenantId,
          method: "POST",
          headers: actorHeaders,
          body: JSON.stringify(payload),
        },
      );
    },
  });
}

// ── useServicioPickerSearchFn (EntityPicker ▾ switcher) ──────────────────────────

/** EntityPicker item shape for the servicio switcher. */
export interface ServicioPickerItem {
  id: string;
  name: string;
}

function pickerCursorToCursor(cursor?: string): string | undefined {
  // The EntityPicker cursor is opaque; we pass it straight through to the BE
  // `cursor` query param (BE paginates the catalog by cursor).
  return cursor && cursor.length > 0 ? cursor : undefined;
}

function mapServiceListToPickerResult(
  res: ServiceListResponse,
): { items: ServicioPickerItem[]; nextCursor?: string } {
  return {
    items: res.items.map((it: ServiceListItem) => ({
      id: it.offer_id,
      name: it.public_name,
    })),
    nextCursor: res.next_cursor ?? undefined,
  };
}

/**
 * useServicioPickerSearchFn — backs the EntityPicker ▾ switcher in the workspace
 * franja. Searches the catalog (GET /servicios?search=&cursor=) and maps the
 * snake_case list items to picker items. Latest-ref so the returned fn is stable
 * (useCallback deps empty) while still reading the current token/tenant.
 */
export function useServicioPickerSearchFn(): EntitySearchFn<ServicioPickerItem> {
  const { getToken } = useAuth();
  const tenantId = useTenantId();

  const ctxRef = useRef({ getToken, tenantId });
  ctxRef.current = { getToken, tenantId };

  return useCallback<EntitySearchFn<ServicioPickerItem>>(async ({ q, cursor }) => {
    const { getToken: gt, tenantId: tid } = ctxRef.current;
    const token = await gt();
    if (!token || !tid) return { items: [] };
    const params = new URLSearchParams();
    if (q) params.set("search", q);
    const c = pickerCursorToCursor(cursor ?? undefined);
    if (c) params.set("cursor", c);
    const res = await fetchClient<ServiceListResponse>(
      `${API_BASE}/api/v1/offer/servicios?${params.toString()}`,
      { token, tenantId: tid },
    );
    return mapServiceListToPickerResult(res);
  }, []);
}
