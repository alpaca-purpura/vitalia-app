// cap: compliance.hipaa-lite-defensive-stack
// story-origin: vitalia-bugfix-agenda-actor-headers-422
"use client";

/**
 * useActorHeaders — shared HIPAA-lite actor headers for the BE RBAC + audit guard.
 *
 * Returns the two actor headers required by every PHI endpoint that audits the
 * acting user and gates on a per-tenant role:
 *   - X-User-ID   → audit actor; PHI endpoints type it as UUID (users.id). MUST be
 *                   the DB user UUID (users.id), NOT the Clerk id (`user_…` → 422
 *                   "Input should be a valid UUID").
 *   - X-User-Role → tenant-scoped RBAC. MUST be the PER-TENANT role (active clinic's
 *                   role from the tenant store), NOT the GLOBAL role from `GET /me`.
 *                   A user can be `doctor` globally yet `owner` of a specific clinic.
 *
 * ★ Lifted from features/lisa/api/staff.ts::useStaffActorHeaders (Bug #4, 2026-06-06)
 *   to src/hooks/ so other features (mateo/agenda) can consume it WITHOUT a forbidden
 *   cross-feature import (FSD-Lite). features/lisa now re-exports a thin wrapper over
 *   this hook (no behaviour change). The X-Clinic-ID header lives in the separate
 *   shared `useClinicId()` hook — caller merges both.
 *
 * Resolution detail:
 * 1) X-User-ID = the DB user UUID read from the `GET /api/v1/iam/users/me` query cache
 *    (same ME_QUERY_KEY → react-query dedupes, no extra request). The Clerk id exposed
 *    by useCurrentUser would 422 the UUID-typed header.
 * 2) X-User-Role = the per-tenant role from the tenant store (availableTenants entry for
 *    the active tenant, falling back to activeTenant.role). The global `/me` role sent
 *    "doctor" for an owner → 403 on tenant-scoped RBAC.
 *
 * Both are resolved here, scoped to PHI mutations/reads, WITHOUT touching the shared
 * useCurrentUser / hasPhiAccess gating. The systemic useCurrentUser per-tenant fix is
 * tracked in a separate carril.
 *
 * Per vitalia/.claude/rules/hipaa-lite.md: PHI endpoints require dual filter + audit actor.
 * Per MEMORY.md::no-clerk-organizations: tenant/role come from luana-core-iam, not Clerk org.
 */

import { useAuth } from "@clerk/nextjs";
import { useQuery } from "@tanstack/react-query";
import { fetchClient } from "@/lib/api/fetchClient";
import { useTenantId } from "@/hooks/useTenantId";
import { ME_QUERY_KEY } from "@/hooks/useCurrentUser";
import { useTenantStore } from "@/stores/tenant-store";

/**
 * Returns the X-User-ID (DB UUID) + X-User-Role (per-tenant) headers.
 *
 * X-User-ID is "" until `GET /me` resolves — callers MUST gate PHI queries on a
 * non-empty X-User-ID to avoid firing with an empty UUID (→ 422 race).
 */
export function useActorHeaders(): Record<string, string> {
  const { getToken, isLoaded, isSignedIn } = useAuth();
  const tenantId = useTenantId();
  const tenantRole = useTenantStore(
    (s) =>
      s.availableTenants.find((t) => t.id === tenantId)?.role ??
      s.activeTenant?.role ??
      null,
  );
  // Reuse the /me query cache (same key as useCurrentUser) to read the DB user UUID.
  const meQuery = useQuery<{ id: string }>({
    queryKey: [...ME_QUERY_KEY, tenantId],
    queryFn: async () => {
      const token = await getToken();
      if (!token || !tenantId) throw new Error("Sin autenticación");
      return fetchClient<{ id: string }>("/api/v1/iam/users/me", {
        token,
        tenantId,
      });
    },
    enabled: isLoaded && isSignedIn === true && Boolean(tenantId),
    staleTime: 5 * 60 * 1000,
  });
  return {
    "X-User-ID": meQuery.data?.id ?? "",
    "X-User-Role": tenantRole ?? "owner",
  };
}
