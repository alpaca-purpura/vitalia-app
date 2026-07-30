// cap: clinics.lisa.doctores
// story-origin: vitalia-fase2-lisa-doctores
/**
 * staff.ts — React Query hooks for Lisa Staff sub-tab.
 *
 * Hooks:
 *   - useStaffList(filters) — paginated doctor list (masked PHI)
 *   - useCreateDoctor() — mutation: POST /doctors
 *
 * React Query key convention:
 *   ['lisa','staff','list',filters] — list
 *   ['lisa','staff',id]             — detail (T-FE-2)
 *   ['lisa','staff',id,'blocks']    — availability blocks (T-FE-3)
 *
 * Auth pattern: useAuth() → getToken() + orgId → fetchClient(token, tenantId, clinicId).
 * HIPAA-lite: clinicId injected via useClinicId() (X-Clinic-ID header).
 *
 * T-FE-1 vitalia-fase2-lisa-doctores
 * spec_anchor: 03-arch-fe.md § Data layer + § React Query keys
 * downstream-regression-na: brand-local vitalia FE API; no cross-brand consumers
 */

"use client";

import { useCallback, useRef } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "@clerk/nextjs";
import type {
  EntityPickerItem,
  EntitySearchFn,
  EntitySearchResult,
} from "@luana/ui-kit";
import { useTenantId } from "@/hooks/useTenantId";
import { fetchClient } from "@/lib/api/fetchClient";
import { useClinicId } from "@/hooks/useClinicId";
import { useActorHeaders } from "@/hooks/useActorHeaders";
import type {
  DoctorListItem,
  DoctorDetail,
  PaginatedDoctors,
  StaffFilters,
} from "../types/staff.types";
import type { DoctorCreateFormValues } from "../types/staff-schema";

// Client-side calls go SAME-ORIGIN relative (`/api/v1/vitalia/...`). The dev-app
// Cloudflare tunnel (deploy/cloudflared/dev-config.yml) routes `^/api/.*` to the
// backend; in prod the same-origin reverse-proxy does. Using the absolute
// `http://localhost:8002` here cross-origins the browser → CORS block on every
// client fetch (regression 2026-06-06: staff directory error-banner despite BE 200;
// only SSR initialData masked it). Server-side fetches live in staff-server.ts and
// keep the absolute NEXT_PUBLIC_API_URL (server-to-server, no CORS). Convention
// matches features/adrian + features/fidelizacion (relative client base).
const API_BASE = "";

/**
 * useStaffActorHeaders — thin wrapper over the shared `useActorHeaders` hook.
 *
 * ★ Lifted 2026-06-15 (vitalia-bugfix-agenda-actor-headers-422): the X-User-ID (DB UUID)
 *   + X-User-Role (per-tenant) resolution moved verbatim to `@/hooks/useActorHeaders` so
 *   features/mateo (agenda) can consume it WITHOUT a forbidden cross-feature import
 *   (FSD-Lite). Behaviour unchanged for the staff consumers below — this re-exports the
 *   shared hook under the original name to avoid touching the call sites.
 *
 * Origin (Bug #4, Chris decision 2026-06-06, option B):
 *   - X-User-Role = PER-TENANT role (active clinic) from the tenant store, NOT the GLOBAL
 *     `/me` role (a user can be `doctor` globally yet `owner` of a clinic → 403 otherwise).
 *   - X-User-ID = DB user UUID (users.id), NOT the Clerk id (`user_…` → 422 UUID).
 */
export function useStaffActorHeaders(): Record<string, string> {
  return useActorHeaders();
}

// ── Query key factory ──────────────────────────────────────────────────────────

export const staffKeys = {
  all: ["lisa", "staff"] as const,
  lists: () => [...staffKeys.all, "list"] as const,
  list: (filters: StaffFilters) => [...staffKeys.lists(), filters] as const,
  details: () => [...staffKeys.all, "detail"] as const,
  detail: (id: string) => [...staffKeys.details(), id] as const,
  blocks: (id: string) => [...staffKeys.detail(id), "blocks"] as const,
  /**
   * Prefix key for ALL occurrence windows of a doctor — partial matching target
   * for mutation invalidation (bug7 r3 D-3a: el calendario PINTA de occurrences;
   * invalidar solo `blocks` dejaba el calendario stale tras create/update/delete).
   */
  occurrencesAll: (id: string) =>
    [...staffKeys.detail(id), "occurrences"] as const,
  occurrences: (id: string, from: string, to: string) =>
    [...staffKeys.occurrencesAll(id), from, to] as const,
  bioFiles: (id: string) => [...staffKeys.detail(id), "bio-files"] as const,
};

// ── useStaffList ───────────────────────────────────────────────────────────────

export interface UseStaffListOptions {
  filters: StaffFilters;
  initialData?: PaginatedDoctors;
}

/**
 * useStaffList — fetches paginated staff directory.
 * Hydrated from SSR initialData (no refetch on mount when SSR data is fresh).
 */
export function useStaffList({ filters, initialData }: UseStaffListOptions) {
  const { getToken, isLoaded, isSignedIn } = useAuth();
  const tenantId = useTenantId();
  const clinicId = useClinicId();

  // SSR initialData seeds ONLY the default (unfiltered, page-1) view. Passing it for
  // every key meant a search/filter key was seeded with the full list AND marked fresh
  // (staleTime 30s) → React Query never fetched the filtered result → the search box
  // did nothing (bug 2026-06-07). Scope initialData to the default filter set so any
  // q/specialty/active/page change is a fresh key that actually hits the BE.
  const isDefaultFilters =
    !filters.q &&
    !filters.specialty &&
    !filters.active &&
    (filters.page ?? 1) === 1;

  return useQuery({
    queryKey: staffKeys.list(filters),
    queryFn: async () => {
      const token = await getToken();
      if (!token || !tenantId) throw new Error("Sin autenticación");

      const params = new URLSearchParams();
      params.set("page", String(filters.page ?? 1));
      params.set("page_size", "24");
      if (filters.q) params.set("q", filters.q);
      if (filters.specialty) params.set("specialty", filters.specialty);
      if (filters.active === "true" || filters.active === "false") {
        params.set("active", filters.active);
      }

      return fetchClient<PaginatedDoctors>(
        `${API_BASE}/api/v1/vitalia/clinics/doctors?${params.toString()}`,
        {
          token,
          tenantId,
          clinicId,
        },
      );
    },
    enabled: isLoaded && !!isSignedIn,
    initialData: isDefaultFilters ? initialData : undefined,
    staleTime: 30_000,
    retry: (failureCount, error) => {
      // SC-7: network failure — retry up to 2 times, surface error after
      const isNetworkError = error instanceof TypeError;
      return isNetworkError && failureCount < 2;
    },
  });
}

// ── useCreateDoctor ────────────────────────────────────────────────────────────

export interface CreateDoctorPayload {
  first_name: string;
  last_name: string;
  dni: string;
  email: string;
  phone?: string | null;
  specialty?: string | null;
  credential: string;
  credential_country: string;
  active: boolean;
}

/**
 * Maps RHF camelCase form values → snake_case API payload.
 */
export function mapDoctorCreateToPayload(
  values: DoctorCreateFormValues,
): CreateDoctorPayload {
  return {
    first_name: values.firstName,
    last_name: values.lastName,
    dni: values.dni,
    email: values.email,
    phone: values.phone || null,
    specialty: values.specialty || null,
    credential: values.credential,
    credential_country: values.credentialCountry,
    active: values.active,
  };
}

/**
 * useCreateDoctor — mutation: POST /api/v1/vitalia/clinics/doctors
 * On success: invalidates list queries so directory refreshes.
 * On 422: caller surfaces inline credential error.
 * On 409: caller surfaces "Ya existe un doctor con ese documento" toast.
 */
export function useCreateDoctor() {
  const { getToken } = useAuth();
  const tenantId = useTenantId();
  const clinicId = useClinicId();
  const mutationHeaders = useStaffActorHeaders();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: CreateDoctorPayload) => {
      const token = await getToken();
      if (!token || !tenantId) throw new Error("Sin autenticación");

      return fetchClient<DoctorDetail>(
        `${API_BASE}/api/v1/vitalia/clinics/doctors`,
        {
          method: "POST",
          token,
          tenantId,
          clinicId,
          headers: mutationHeaders,
          body: JSON.stringify(payload),
        },
      );
    },
    onSuccess: () => {
      // Invalidate all list queries so directory refreshes
      void queryClient.invalidateQueries({ queryKey: staffKeys.lists() });
    },
  });
}

// ── useDoctor ──────────────────────────────────────────────────────────────────

/**
 * useDoctor — fetches single doctor detail for workspace pages.
 * Hydrated from SSR initialData (layout passes getDoctorInitialState result).
 */
export function useDoctor(
  doctorId: string,
  initialData?: DoctorDetail,
) {
  const { getToken, isLoaded, isSignedIn } = useAuth();
  const tenantId = useTenantId();
  const clinicId = useClinicId();
  // GET /{id} (detail) REQUIRES X-User-ID (UUID) — audit-on-PHI-read. Without it the
  // BE 422s ("No se pudo cargar el perfil", regression 2026-06-06 bug #5). The list GET
  // does not require it (masked). Reuse the actor headers (X-User-ID DB-UUID + role).
  const actorHeaders = useStaffActorHeaders();

  return useQuery({
    queryKey: staffKeys.detail(doctorId),
    queryFn: async () => {
      const token = await getToken();
      if (!token || !tenantId) throw new Error("Sin autenticación");
      const detail = await fetchClient<DoctorDetail>(
        `${API_BASE}/api/v1/vitalia/clinics/doctors/${doctorId}`,
        { token, tenantId, clinicId, headers: actorHeaders },
      );
      // Frontera null→[]: el BE serializa secciones nullable del perfil (RN-D3D-6);
      // los consumers (editor/preview) asumen arrays. Normalizar ACÁ, una vez.
      if (detail.publicProfile) {
        const pp = detail.publicProfile;
        pp.formacion = pp.formacion ?? [];
        pp.experiencia = pp.experiencia ?? [];
        pp.tratamientos = pp.tratamientos ?? [];
        pp.certificaciones = pp.certificaciones ?? [];
        pp.idiomas = pp.idiomas ?? [];
      }
      return detail;
    },
    // Gate until X-User-ID (from /me) is ready — firing the detail GET before it
    // resolves sends X-User-ID:"" → 422 race ("No se pudo cargar el perfil", bug #5).
    enabled: isLoaded && !!isSignedIn && !!actorHeaders["X-User-ID"],
    initialData,
    staleTime: 30_000,
  });
}

// ── usePatchDoctor ─────────────────────────────────────────────────────────────

export interface PatchDoctorPayload {
  specialty?: string | null;
  phone?: string | null;
  yearsExperience?: number | null;
  languages?: string[];
  visibleEnLanding?: boolean;
  bioInputsNotes?: string | null;
  bioLinks?: string[];
  bioPublic?: {
    resumen?: string | null;
    formacion?: string | null;
    enfoque?: string | null;
  } | null;
  avatarKey?: string | null;
}

/**
 * usePatchDoctor — mutation: PATCH /api/v1/vitalia/clinics/doctors/{id}
 * Used for autosave on-change.
 */
export function usePatchDoctor(doctorId: string) {
  const { getToken } = useAuth();
  const tenantId = useTenantId();
  const clinicId = useClinicId();
  const mutationHeaders = useStaffActorHeaders();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: PatchDoctorPayload) => {
      const token = await getToken();
      if (!token || !tenantId) throw new Error("Sin autenticación");
      return fetchClient<DoctorDetail>(
        `${API_BASE}/api/v1/vitalia/clinics/doctors/${doctorId}`,
        {
          method: "PATCH",
          token,
          tenantId,
          clinicId,
          headers: mutationHeaders,
          body: JSON.stringify(payload),
        },
      );
    },
    onSuccess: (updated) => {
      // Update the cache optimistically with the returned data
      queryClient.setQueryData(staffKeys.detail(doctorId), updated);
    },
  });
}

// ── useGenerateBio ─────────────────────────────────────────────────────────────

export interface GenerateBioResponse {
  resumen: string;
  formacion: string;
  enfoque: string;
}

/**
 * useGenerateBio — mutation: POST /api/v1/vitalia/clinics/doctors/{id}/generate-bio
 * Sends bio inputs to BE; returns generated 3-section bio.
 * No-invent guardrail handled by BE service (D-4).
 */
export function useGenerateBio(doctorId: string) {
  const { getToken } = useAuth();
  const tenantId = useTenantId();
  const clinicId = useClinicId();
  const mutationHeaders = useStaffActorHeaders();

  return useMutation({
    mutationFn: async () => {
      const token = await getToken();
      if (!token || !tenantId) throw new Error("Sin autenticación");
      return fetchClient<GenerateBioResponse>(
        `${API_BASE}/api/v1/vitalia/clinics/doctors/${doctorId}/generate-bio`,
        {
          method: "POST",
          token,
          tenantId,
          clinicId,
          headers: mutationHeaders,
          body: JSON.stringify({}),
        },
      );
    },
  });
}

// ── useAvatarUpload ────────────────────────────────────────────────────────────

/**
 * useAvatarUpload — mutation: POST /api/v1/vitalia/assets/upload (proxy)
 * Per D-3: proxy upload (presigned not implemented in engine).
 * After upload: PATCH doctor {avatarKey}.
 */
export function useAvatarUpload(doctorId: string) {
  const { getToken } = useAuth();
  const tenantId = useTenantId();
  const clinicId = useClinicId();
  const mutationHeaders = useStaffActorHeaders();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (file: File) => {
      const token = await getToken();
      if (!token || !tenantId) throw new Error("Sin autenticación");

      // Step 1: Upload file to assets proxy
      const formData = new FormData();
      formData.append("file", file);
      formData.append("kind", "avatar");

      const uploadUrl = `${API_BASE}/api/v1/vitalia/assets/upload`;
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 60_000);

      let uploadResponse: Response;
      try {
        uploadResponse = await fetch(uploadUrl, {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
            "X-Tenant-ID": tenantId,
            ...(clinicId ? { "X-Clinic-ID": clinicId } : {}),
            ...mutationHeaders,
          },
          body: formData,
          signal: controller.signal,
        });
      } finally {
        clearTimeout(timeoutId);
      }

      if (!uploadResponse.ok) {
        throw new Error(`Error al subir imagen: ${uploadResponse.status}`);
      }

      const { key, url } = (await uploadResponse.json()) as {
        key: string;
        url: string;
      };

      // Step 2: PATCH doctor with new avatar_key
      await fetchClient<DoctorDetail>(
        `${API_BASE}/api/v1/vitalia/clinics/doctors/${doctorId}`,
        {
          method: "PATCH",
          token,
          tenantId,
          clinicId,
          headers: mutationHeaders,
          body: JSON.stringify({ avatar_key: key }),
        },
      );

      return { key, url };
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: staffKeys.detail(doctorId),
      });
    },
  });
}

// ── Doctor picker searchFn (D3-A entity switcher) ──────────────────────────────

/**
 * pickerCursorToPage — pure page↔cursor adapter half (cursor → page).
 *
 * The EntityPicker (@luana/ui-kit, canon §2.4) speaks CURSOR pagination; the
 * doctors list endpoint speaks page/page_size. Convention: cursor = stringified
 * NEXT page number. null/undefined/garbage/<1 → first page (never a NaN fetch).
 *
 * T-FE-switcher-wire vitalia-fase2-lisa-doctores
 */
export function pickerCursorToPage(cursor?: string | null): number {
  if (!cursor) return 1;
  const page = Number(cursor);
  return Number.isFinite(page) && page >= 1 ? Math.floor(page) : 1;
}

/**
 * mapDoctorsPageToPickerResult — pure page↔cursor adapter half (page → result).
 *
 * Maps one `PaginatedDoctors` page to the `EntitySearchResult` the EntityPicker
 * consumes: `nextCursor` is the stringified next page while pages remain
 * (null on the last page), `total` feeds the "Mostrando N de M" footer, and
 * each item's `name` prefers `displayName` falling back to "firstName lastName".
 */
export function mapDoctorsPageToPickerResult(
  res: PaginatedDoctors,
  page: number,
): EntitySearchResult<EntityPickerItem> {
  const pageSize = res.pageSize > 0 ? res.pageSize : 1;
  const lastPage = Math.max(1, Math.ceil(res.total / pageSize));
  return {
    items: res.items.map((d) => ({
      id: d.id,
      name: d.displayName?.trim()
        ? d.displayName
        : `${d.firstName} ${d.lastName}`,
    })),
    nextCursor: page < lastPage ? String(page + 1) : null,
    total: res.total,
  };
}

/**
 * useDoctorPickerSearchFn — query-lib-agnostic `searchFn` for the EntityPicker
 * wired into the staff workspace N3 bar (D3-A switcher).
 *
 * Request contract:
 *   - `active=true` ALWAYS (RN-D3A-2: inactive staff never appears)
 *   - `q` server-side when non-empty (RN-D3A-1: never client-side filtering
 *     of the full collection — canon §2.4)
 *   - `page_size=limit` hard page size (cursor = stringified page number)
 *
 * The list GET requires NO actor headers (masked listing — same contract as
 * `useStaffList`; X-User-ID is a detail/mutation requirement only, bug #5).
 *
 * IDENTITY-STABLE across re-renders (latest-ref pattern): the EntityPicker's
 * fetch effect depends on `searchFn` — an unstable identity would re-fire the
 * first-page fetch on every parent render while the popover is open. The ref
 * always holds the freshest auth/tenant context (read at CALL time → no stale
 * closure), while the returned function identity never changes.
 */
export function useDoctorPickerSearchFn(): EntitySearchFn<EntityPickerItem> {
  const { getToken } = useAuth();
  const tenantId = useTenantId();
  const clinicId = useClinicId();

  const ctxRef = useRef({ getToken, tenantId, clinicId });
  ctxRef.current = { getToken, tenantId, clinicId };

  return useCallback(async ({ q, cursor, limit }) => {
    const ctx = ctxRef.current;
    const token = await ctx.getToken();
    if (!token || !ctx.tenantId) throw new Error("Sin autenticación");

    const page = pickerCursorToPage(cursor);
    const params = new URLSearchParams();
    params.set("page", String(page));
    params.set("page_size", String(limit));
    params.set("active", "true");
    if (q) params.set("q", q);

    const res = await fetchClient<PaginatedDoctors>(
      `${API_BASE}/api/v1/vitalia/clinics/doctors?${params.toString()}`,
      { token, tenantId: ctx.tenantId, clinicId: ctx.clinicId },
    );
    return mapDoctorsPageToPickerResult(res, page);
  }, []);
}

// ── useAvailabilityBlocks ──────────────────────────────────────────────────────

/**
 * useAvailabilityBlocks — fetches availability blocks for a doctor.
 * Key: ['lisa','staff',id,'blocks']
 * Includes all block kinds (recurrent + one_off).
 * T-FE-3 vitalia-fase2-lisa-doctores
 */
export function useAvailabilityBlocks(doctorId: string) {
  const { getToken, isLoaded, isSignedIn } = useAuth();
  const tenantId = useTenantId();
  const clinicId = useClinicId();

  return useQuery({
    queryKey: staffKeys.blocks(doctorId),
    queryFn: async (): Promise<import("../types/staff.types").AvailabilityBlock[]> => {
      const token = await getToken();
      if (!token || !tenantId) throw new Error("Sin autenticación");
      // BE returns the envelope { blocks: [...] } (AvailabilityBlocksResponse), NOT a
      // bare array — returning it raw made AvailabilityCalendar do `(blocks).filter` on
      // an object → "filter is not a function" crash on the horarios tab (bug #6,
      // 2026-06-06). Unwrap `.blocks`.
      const res = await fetchClient<{
        blocks: import("../types/staff.types").AvailabilityBlock[];
      }>(
        `${API_BASE}/api/v1/vitalia/clinics/doctors/${doctorId}/availability-blocks`,
        { token, tenantId, clinicId },
      );
      return res.blocks ?? [];
    },
    enabled: isLoaded && !!isSignedIn && !!doctorId,
    staleTime: 30_000,
  });
}

// ── useAvailabilityOccurrences ────────────────────────────────────────────────

/**
 * useAvailabilityOccurrences — fetches BE-projected occurrences for a week window.
 *
 * This is the PAINT source for AvailabilityCalendar. It replaces the buggy
 * client-side recurrentBlockVisibleInWeek() that ignored occurrences/open_ended
 * end conditions → infinite paint.
 *
 * Endpoint: GET /api/v1/vitalia/clinics/doctors/{id}/availability-occurrences?from=&to=
 * Response: { occurrences: AvailabilityOccurrenceDTO[] } (camelCase via alias_generator=to_camel)
 *
 * BE anchors series in block.created_at.date() (not query window) → consistent
 * series numbering across page-loads (no infinite paint even for open_ended).
 *
 * T-FE-occurrences-consume vitalia-fase2-lisa-doctores
 * spec_anchor: 01-spec.md § D3-C.1
 */
export function useAvailabilityOccurrences(
  doctorId: string,
  fromIso: string,
  toIso: string,
) {
  const { getToken, isLoaded, isSignedIn } = useAuth();
  const tenantId = useTenantId();
  const clinicId = useClinicId();
  // X-User-ID required by the endpoint for actor-header consistency (per doctors_router.py)
  const actorHeaders = useStaffActorHeaders();

  return useQuery({
    queryKey: staffKeys.occurrences(doctorId, fromIso, toIso),
    queryFn: async (): Promise<
      import("../types/staff.types").AvailabilityOccurrence[]
    > => {
      const token = await getToken();
      if (!token || !tenantId) throw new Error("Sin autenticación");
      const params = new URLSearchParams({ from: fromIso, to: toIso });
      const res = await fetchClient<{
        occurrences: import("../types/staff.types").AvailabilityOccurrence[];
      }>(
        `${API_BASE}/api/v1/vitalia/clinics/doctors/${doctorId}/availability-occurrences?${params.toString()}`,
        { token, tenantId, clinicId, headers: actorHeaders },
      );
      return res.occurrences ?? [];
    },
    // bug7 r3: el endpoint exige X-User-ID y X-Clinic-ID como UUID Header
    // REQUERIDOS — disparar la query antes de que /iam/users/me resuelva
    // mandaba X-User-ID:"" → 422 → la query quedaba en error y el calendario
    // pintaba VACÍO para siempre (race de page-load).
    enabled:
      isLoaded &&
      !!isSignedIn &&
      !!doctorId &&
      !!fromIso &&
      !!toIso &&
      !!clinicId &&
      !!actorHeaders["X-User-ID"],
    staleTime: 30_000,
  });
}

// ── useCreateBlock ─────────────────────────────────────────────────────────────

export interface CreateBlockPayload {
  kind: "recurrent" | "one_off";
  day_of_week?: number | null;
  start_time: string;
  end_time: string;
  freq?: "weekly" | "biweekly" | null;
  end_condition_kind?: "end_date" | "occurrences" | "open_ended" | null;
  end_date?: string | null;
  occurrences?: number | null;
  specific_date?: string | null;
  /** D3-F PRIMARY: weekday ints 0=Mon..6=Sun (BE accepts snake via populate_by_name) */
  days_of_week?: number[];
  /** D3-F PRIMARY: recurrence interval in weeks (1=weekly, 2=biweekly, N=custom) */
  interval?: number;
}

/**
 * useCreateBlock — mutation: POST /api/v1/vitalia/clinics/doctors/{id}/availability-blocks
 * On success: invalidates blocks query so calendar refreshes.
 * Recurrence is resolved by backend via dateutil.rrule (D-2).
 * T-FE-3 vitalia-fase2-lisa-doctores
 */
export function useCreateBlock(doctorId: string) {
  const { getToken } = useAuth();
  const tenantId = useTenantId();
  const clinicId = useClinicId();
  const mutationHeaders = useStaffActorHeaders();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: CreateBlockPayload) => {
      const token = await getToken();
      if (!token || !tenantId) throw new Error("Sin autenticación");
      return fetchClient<import("../types/staff.types").AvailabilityBlock>(
        `${API_BASE}/api/v1/vitalia/clinics/doctors/${doctorId}/availability-blocks`,
        {
          method: "POST",
          token,
          tenantId,
          clinicId,
          headers: mutationHeaders,
          body: JSON.stringify(payload),
        },
      );
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: staffKeys.blocks(doctorId),
      });
      // bug7 r3 D-3a: occurrences es la fuente de PINTADO del calendario —
      // sin esta invalidación el bloque guardado no aparece hasta un reload.
      void queryClient.invalidateQueries({
        queryKey: staffKeys.occurrencesAll(doctorId),
      });
    },
  });
}

// ── useUpdateBlock ─────────────────────────────────────────────────────────────

export interface UpdateBlockPayload {
  /** bug7 r3 D-3b: el PATCH BE discrimina recurrent|one_off por `kind` */
  kind?: "recurrent" | "one_off";
  /** bug7 r3 D-3b: fecha puntual al editar un bloque one_off */
  specific_date?: string | null;
  freq?: "weekly" | "biweekly";
  end_condition_kind?: "end_date" | "occurrences" | "open_ended";
  end_date?: string | null;
  occurrences?: number | null;
  start_time?: string;
  end_time?: string;
  /** D3-F PRIMARY: weekday ints 0=Mon..6=Sun (BE accepts snake via populate_by_name) */
  days_of_week?: number[];
  /** D3-F PRIMARY: recurrence interval in weeks (1=weekly, 2=biweekly, N=custom) */
  interval?: number;
}

/**
 * useUpdateBlock — mutation: PATCH /api/v1/vitalia/clinics/doctors/{doctorId}/availability-blocks/{blockId}
 * T-FE-3 vitalia-fase2-lisa-doctores
 */
export function useUpdateBlock(doctorId: string) {
  const { getToken } = useAuth();
  const tenantId = useTenantId();
  const clinicId = useClinicId();
  const mutationHeaders = useStaffActorHeaders();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      blockId,
      payload,
    }: {
      blockId: string;
      payload: UpdateBlockPayload;
    }) => {
      const token = await getToken();
      if (!token || !tenantId) throw new Error("Sin autenticación");
      return fetchClient<import("../types/staff.types").AvailabilityBlock>(
        `${API_BASE}/api/v1/vitalia/clinics/doctors/${doctorId}/availability-blocks/${blockId}`,
        {
          method: "PATCH",
          token,
          tenantId,
          clinicId,
          headers: mutationHeaders,
          body: JSON.stringify(payload),
        },
      );
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: staffKeys.blocks(doctorId),
      });
      // bug7 r3 D-3a: occurrences es la fuente de PINTADO del calendario —
      // sin esta invalidación el bloque guardado no aparece hasta un reload.
      void queryClient.invalidateQueries({
        queryKey: staffKeys.occurrencesAll(doctorId),
      });
    },
  });
}

// ── useDeleteBlock ─────────────────────────────────────────────────────────────

export interface DeleteBlockResponse {
  /** Whether the block (or occurrence) was deleted */
  deleted: boolean;
  /** Number of confirmed appointments preserved (SC-3b) */
  preservedAppointments: number;
  /** Scope that was applied by the backend */
  scope: string;
}

export interface DeleteBlockParams {
  blockId: string;
  /** Omit for full-series delete (back-compat default = "series") */
  scope?: "series" | "occurrence" | "this_and_future";
  /** Required when scope = "occurrence" | "this_and_future" — ISO date YYYY-MM-DD */
  occurrenceDate?: string;
}

/**
 * useDeleteBlock — mutation: DELETE /api/v1/vitalia/clinics/doctors/{doctorId}/availability-blocks/{blockId}
 * Supports recurrent-series scoped deletes via query params (round-5 bug7).
 * scope=series (default): deletes the whole series
 * scope=occurrence: deletes only the specific occurrence identified by occurrence_date
 * scope=this_and_future: deletes from occurrence_date onwards
 * Returns deletion confirmation + preserved appointments count.
 * T-FE-3 vitalia-fase2-lisa-doctores
 */
export function useDeleteBlock(doctorId: string) {
  const { getToken } = useAuth();
  const tenantId = useTenantId();
  const clinicId = useClinicId();
  const mutationHeaders = useStaffActorHeaders();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ blockId, scope, occurrenceDate }: DeleteBlockParams) => {
      const token = await getToken();
      if (!token || !tenantId) throw new Error("Sin autenticación");
      const params = new URLSearchParams();
      if (scope) params.set("scope", scope);
      if (occurrenceDate) params.set("occurrence_date", occurrenceDate);
      const qs = params.toString() ? `?${params.toString()}` : "";
      return fetchClient<DeleteBlockResponse>(
        `${API_BASE}/api/v1/vitalia/clinics/doctors/${doctorId}/availability-blocks/${blockId}${qs}`,
        {
          method: "DELETE",
          token,
          tenantId,
          clinicId,
          headers: mutationHeaders,
        },
      );
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: staffKeys.blocks(doctorId),
      });
      // bug7 r3 D-3a: occurrences es la fuente de PINTADO del calendario —
      // sin esta invalidación el bloque guardado no aparece hasta un reload.
      void queryClient.invalidateQueries({
        queryKey: staffKeys.occurrencesAll(doctorId),
      });
    },
  });
}

// ── useBioFiles ───────────────────────────────────────────────────────────────

/**
 * useBioFiles — fetches bio document list for a doctor.
 * Key: ['lisa','staff',id,'detail',id,'bio-files']
 * Endpoint: GET /api/v1/vitalia/clinics/doctors/{id}/bio-files
 * HIPAA-lite: X-Tenant-ID + X-Clinic-ID required.
 * T-FE-bio-docs vitalia-fase2-lisa-doctores
 * spec_anchor: 01-spec.md § D3-B
 */
export function useBioFiles(doctorId: string) {
  const { getToken, isLoaded, isSignedIn } = useAuth();
  const tenantId = useTenantId();
  const clinicId = useClinicId();
  const mutationHeaders = useStaffActorHeaders();

  return useQuery({
    queryKey: staffKeys.bioFiles(doctorId),
    queryFn: async (): Promise<import("../types/staff.types").BioFile[]> => {
      const token = await getToken();
      if (!token || !tenantId) throw new Error("Sin autenticación");
      const res = await fetchClient<{
        bioFiles: import("../types/staff.types").BioFile[];
      }>(
        `${API_BASE}/api/v1/vitalia/clinics/doctors/${doctorId}/bio-files`,
        { token, tenantId, clinicId, headers: mutationHeaders },
      );
      return res.bioFiles ?? [];
    },
    enabled: isLoaded && !!isSignedIn && !!doctorId,
    staleTime: 30_000,
  });
}

// ── useBioFileUpload ──────────────────────────────────────────────────────────

/**
 * useBioFileUpload — 2-step mutation: POST /assets/upload (proxy, kind=bio_doc)
 * then POST /{doctor_id}/bio-files (register metadata).
 *
 * Mirror of useAvatarUpload (D-3 pattern). Step 2 sends BioFileRegisterRequest
 * (camelCase): { storageKey, filename, sizeBytes, contentType }.
 *
 * On success: invalidates bio-files query.
 * HIPAA-lite: all headers required (X-Tenant-ID, X-Clinic-ID, X-User-ID/Role).
 * T-FE-bio-docs vitalia-fase2-lisa-doctores
 * spec_anchor: 01-spec.md § D3-B.1
 */
export function useBioFileUpload(doctorId: string) {
  const { getToken } = useAuth();
  const tenantId = useTenantId();
  const clinicId = useClinicId();
  const mutationHeaders = useStaffActorHeaders();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (file: File) => {
      const token = await getToken();
      if (!token || !tenantId) throw new Error("Sin autenticación");

      // Step 1 — upload bytes to assets proxy
      const formData = new FormData();
      formData.append("file", file);
      formData.append("kind", "bio_doc");

      const uploadUrl = `${API_BASE}/api/v1/vitalia/assets/upload`;
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 60_000);

      let uploadResponse: Response;
      try {
        uploadResponse = await fetch(uploadUrl, {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
            "X-Tenant-ID": tenantId,
            ...(clinicId ? { "X-Clinic-ID": clinicId } : {}),
            ...mutationHeaders,
          },
          body: formData,
          signal: controller.signal,
        });
      } finally {
        clearTimeout(timeoutId);
      }

      if (!uploadResponse.ok) {
        const status = uploadResponse.status;
        if (status === 503) {
          throw new Error("STORAGE_UNAVAILABLE");
        }
        throw new Error(`Error al subir archivo: ${status}`);
      }

      const { key } = (await uploadResponse.json()) as { key: string; url: string };

      // Step 2 — register bio file metadata
      const registered = await fetchClient<{
        bioFiles: import("../types/staff.types").BioFile[];
      }>(
        `${API_BASE}/api/v1/vitalia/clinics/doctors/${doctorId}/bio-files`,
        {
          method: "POST",
          token,
          tenantId,
          clinicId,
          headers: mutationHeaders,
          body: JSON.stringify({
            storageKey: key,
            filename: file.name,
            sizeBytes: file.size,
            contentType: file.type,
          }),
        },
      );

      return registered.bioFiles ?? [];
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: staffKeys.bioFiles(doctorId),
      });
    },
  });
}

// ── useDeleteBioFile ──────────────────────────────────────────────────────────

/**
 * useDeleteBioFile — mutation: DELETE /{doctor_id}/bio-files/{file_id}
 * Requires explicit user confirmation before calling mutate().
 * On success: invalidates bio-files query.
 * HIPAA-lite: audit log written sync pre-response by BE.
 * T-FE-bio-docs vitalia-fase2-lisa-doctores
 */
export function useDeleteBioFile(doctorId: string) {
  const { getToken } = useAuth();
  const tenantId = useTenantId();
  const clinicId = useClinicId();
  const mutationHeaders = useStaffActorHeaders();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (fileId: string) => {
      const token = await getToken();
      if (!token || !tenantId) throw new Error("Sin autenticación");
      return fetchClient<{ deleted: boolean }>(
        `${API_BASE}/api/v1/vitalia/clinics/doctors/${doctorId}/bio-files/${fileId}`,
        {
          method: "DELETE",
          token,
          tenantId,
          clinicId,
          headers: mutationHeaders,
        },
      );
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: staffKeys.bioFiles(doctorId),
      });
    },
  });
}

// ── useBioFileDownload ────────────────────────────────────────────────────────

/**
 * useBioFileDownload — mutation: GET /{doctor_id}/bio-files/{file_id}/download
 *
 * D-1 decision: backend streams bytes via StorageStrategy.get_file_bytes()
 * (presigned URL not implemented in engine). FE fetches raw, converts to blob,
 * triggers programmatic download via anchor click.
 *
 * HIPAA-lite: X-Tenant-ID + X-Clinic-ID + X-User-ID required (audit log on BE).
 * T-FE-bio-docs vitalia-fase2-lisa-doctores
 */
export function useBioFileDownload(doctorId: string) {
  const { getToken } = useAuth();
  const tenantId = useTenantId();
  const clinicId = useClinicId();
  const mutationHeaders = useStaffActorHeaders();

  return useMutation({
    mutationFn: async ({
      fileId,
      filename,
    }: {
      fileId: string;
      filename: string;
    }) => {
      const token = await getToken();
      if (!token || !tenantId) throw new Error("Sin autenticación");

      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 60_000);

      let response: Response;
      try {
        response = await fetch(
          `${API_BASE}/api/v1/vitalia/clinics/doctors/${doctorId}/bio-files/${fileId}/download`,
          {
            headers: {
              Authorization: `Bearer ${token}`,
              "X-Tenant-ID": tenantId,
              ...(clinicId ? { "X-Clinic-ID": clinicId } : {}),
              ...mutationHeaders,
            },
            signal: controller.signal,
          },
        );
      } finally {
        clearTimeout(timeoutId);
      }

      if (!response.ok) {
        throw new Error(`Error al descargar archivo: ${response.status}`);
      }

      const blob = await response.blob();
      const objectUrl = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = objectUrl;
      anchor.download = filename;
      anchor.style.display = "none";
      document.body.appendChild(anchor);
      anchor.click();
      document.body.removeChild(anchor);
      URL.revokeObjectURL(objectUrl);
    },
  });
}

// ── Type re-exports for consumers ──────────────────────────────────────────────

export type { DoctorListItem, DoctorDetail, PaginatedDoctors };

// ── useGenerateProfile (D3-D, T-FE-pagina-publica) ───────────────────────────

/**
 * useGenerateProfile — mutation: POST /api/v1/vitalia/clinics/doctors/{id}/generate-profile
 * Triggers BE LLM generation of structured public profile (DoctorPublicProfile).
 * On success: invalidates doctor detail (profileState.generatedAt updates).
 * spec_anchor: 01-spec.md § D3-D.2
 */
export function useGenerateProfile(doctorId: string) {
  const { getToken } = useAuth();
  const tenantId = useTenantId();
  const clinicId = useClinicId();
  const mutationHeaders = useStaffActorHeaders();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async () => {
      const token = await getToken();
      if (!token || !tenantId) throw new Error("Sin autenticación");
      return fetchClient<import("../types/staff.types").DoctorPublicProfile>(
        `${API_BASE}/api/v1/vitalia/clinics/doctors/${doctorId}/generate-profile`,
        {
          method: "POST",
          token,
          tenantId,
          clinicId,
          headers: mutationHeaders,
          body: JSON.stringify({}),
        },
      );
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: staffKeys.detail(doctorId) });
    },
  });
}

// ── useSavePublicProfile (D3-D, T-FE-pagina-publica) ─────────────────────────

/**
 * SavePublicProfilePayload — mirrors BE SavePublicProfileDTO (commit 275d5d7e).
 * - experiencia: [{puesto, lugar, anios}] (NOT cargo/institucion/desde/hasta)
 * - certificaciones: string[] (NOT object array — finding F3)
 * - idiomas: string[] (NOT object array — finding F3)
 */
export interface SavePublicProfilePayload {
  sobreMi?: string | null;
  formacion?: import("../types/staff.types").StructuredFormacion[];
  experiencia?: import("../types/staff.types").StructuredExperiencia[];
  tratamientos?: string[];
  certificaciones?: string[];
  idiomas?: string[];
}

/**
 * useSavePublicProfile — mutation: PATCH /api/v1/vitalia/clinics/doctors/{id}/public-profile
 * Saves edits to structured profile fields (autosave 600ms).
 * On success: optimistically updates detail cache.
 * spec_anchor: 01-spec.md § D3-D.3
 */
export function useSavePublicProfile(doctorId: string) {
  const { getToken } = useAuth();
  const tenantId = useTenantId();
  const clinicId = useClinicId();
  const mutationHeaders = useStaffActorHeaders();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: SavePublicProfilePayload) => {
      const token = await getToken();
      if (!token || !tenantId) throw new Error("Sin autenticación");
      return fetchClient<import("../types/staff.types").DoctorDetail>(
        `${API_BASE}/api/v1/vitalia/clinics/doctors/${doctorId}/public-profile`,
        {
          method: "PATCH",
          token,
          tenantId,
          clinicId,
          headers: mutationHeaders,
          body: JSON.stringify(payload),
        },
      );
    },
    onSuccess: (updated) => {
      queryClient.setQueryData(staffKeys.detail(doctorId), updated);
    },
  });
}

// ── useTogglePublicVisible (D3-D, T-FE-pagina-publica) ───────────────────────

/**
 * useTogglePublicVisible — mutation: PATCH /api/v1/vitalia/clinics/doctors/{id}
 * (body {visibleEnLanding} — NO existe ruta /public-visible; 7ª lección contrato).
 * Toggles visibility at the public /d/{clinica-slug}/{doctor-slug} route.
 * Anti-enumeration (RN-D3D-9): BE sends identical "perfil no disponible" for OFF/unknown/cross-tenant.
 * On success: invalidates detail (visiblePublic updates).
 * spec_anchor: 01-spec.md § D3-D.4
 */
export function useTogglePublicVisible(doctorId: string) {
  const { getToken } = useAuth();
  const tenantId = useTenantId();
  const clinicId = useClinicId();
  const mutationHeaders = useStaffActorHeaders();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (visiblePublic: boolean) => {
      const token = await getToken();
      if (!token || !tenantId) throw new Error("Sin autenticación");
      // Reusa el PATCH general /{doctor_id} (no existe /public-visible — 7ª lección contrato).
      return fetchClient<import("../types/staff.types").DoctorDetail>(
        `${API_BASE}/api/v1/vitalia/clinics/doctors/${doctorId}`,
        {
          method: "PATCH",
          token,
          tenantId,
          clinicId,
          headers: mutationHeaders,
          body: JSON.stringify({ visibleEnLanding: visiblePublic }),
        },
      );
    },
    onSuccess: () => {
      // invalidate (NO setQueryData): el PATCH response no incluye clinicSlug (solo el GET lo arma)
      void queryClient.invalidateQueries({ queryKey: staffKeys.detail(doctorId) });
    },
  });
}
