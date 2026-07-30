// cap: iam.iam-scaffold-slice-1
// story-origin: vitalia-iam-slice2-phi-real-auth
"use client";

/**
 * useCurrentUser — returns current authenticated user with role from DB.
 *
 * ★ Slice 2 (vitalia-iam-slice2-phi-real-auth T-3):
 * Role source migrated from Clerk publicMetadata.role → GET /api/v1/iam/users/me.
 *
 * Rationale: 1 fuente de verdad (DB via user_tenants.role).
 * Clerk publicMetadata.role era Slice-1 deuda (doble fuente, drift posible).
 * El engine GET /me devuelve role resuelto desde user_tenants por X-Tenant-ID.
 *
 * Roles per hipaa-lite.md: doctor | nurse | admin_clinic | patient | marketing | sales | superadmin
 *
 * Shape CurrentUser INTACTO (consumers RequireRole / usePiiRoleGate sin cambios).
 *
 * OQ-2 confirmado: engine GET /api/v1/iam/users/me retorna User con campos:
 *   id (UUID), full_name, email, role (str), tenant_id, is_active
 * — suficiente para el hook. No se necesita endpoint brand-local.
 * hasPhiAccess se calcula FE-side (conjunto PHI_ROLES constante).
 *
 * useClinicId queda fuera de scope (clinic_id sigue por header X-Clinic-ID
 * que AuditedSection.tsx ya manda — no migra en esta story).
 */

import { useAuth, useUser } from "@clerk/nextjs";
import { useQuery } from "@tanstack/react-query";
import { fetchClient } from "@/lib/api/fetchClient";
import { useTenantId } from "@/hooks/useTenantId";

export type VitaliaRole =
  | "doctor"
  | "nurse"
  | "admin_clinic"
  | "patient"
  | "marketing"
  | "sales"
  | "superadmin";

export interface CurrentUser {
  id: string;
  firstName: string | null;
  lastName: string | null;
  email: string | null;
  role: VitaliaRole | null;
  /** Whether user has PHI access (doctor | nurse | admin_clinic) */
  hasPhiAccess: boolean;
  isLoaded: boolean;
}

/** Engine GET /api/v1/iam/users/me response shape (read-only, no new endpoint) */
interface MeResponse {
  id: string;
  full_name: string | null;
  email: string;
  role: string;
  tenant_id: string | null;
  is_active: boolean;
}

const PHI_ROLES: ReadonlySet<string> = new Set([
  "doctor",
  "nurse",
  "admin_clinic",
]);

/** Stable empty result for loading/error/unauthenticated states */
function emptyUser(isLoaded: boolean): CurrentUser {
  return {
    id: "",
    firstName: null,
    lastName: null,
    email: null,
    role: null,
    hasPhiAccess: false,
    isLoaded,
  };
}

/**
 * React Query key for the /me endpoint.
 * Scoped to the tenant org so re-fetch on tenant switch is automatic.
 */
export const ME_QUERY_KEY = ["iam", "me"] as const;

/**
 * Returns current authenticated user with role resolved from DB via /me.
 *
 * Loading state: isLoaded = false while query is pending.
 * Error state: role = null, hasPhiAccess = false.
 * Success state: role from user_tenants.role (1 fuente de verdad DB).
 */
export function useCurrentUser(): CurrentUser {
  const { getToken, isLoaded: authLoaded, isSignedIn } = useAuth();
  const { user, isLoaded: userLoaded } = useUser();
  const tenantId = useTenantId();

  const query = useQuery<MeResponse, Error>({
    queryKey: [...ME_QUERY_KEY, tenantId],
    queryFn: async () => {
      const token = await getToken();
      if (!token || !tenantId) throw new Error("Not authenticated");
      return fetchClient<MeResponse>("/api/v1/iam/users/me", {
        token,
        tenantId,
      });
    },
    enabled: authLoaded && isSignedIn === true && Boolean(tenantId),
    staleTime: 5 * 60 * 1000,   // 5 min — rol no cambia frecuentemente
    gcTime: 10 * 60 * 1000,
    retry: 2,
    refetchOnWindowFocus: false,
  });

  // Auth or user not loaded yet
  if (!authLoaded || !userLoaded) {
    return emptyUser(false);
  }

  // Not signed in
  if (!isSignedIn || !user) {
    return emptyUser(true);
  }

  // Query error or no data after load — still show isLoaded true so UI can react
  if (query.isError || (!query.data && query.status !== "pending")) {
    return { ...emptyUser(false), isLoaded: true };
  }

  // Query pending (no data yet)
  if (!query.data) {
    return emptyUser(false);
  }

  // Query succeeded: use DB role
  const meData = query.data;
  const role =
    typeof meData.role === "string" && meData.role.length > 0
      ? (meData.role as VitaliaRole)
      : null;

  return {
    // Identity fields from Clerk user object (firstName/lastName not in /me response)
    id: user.id,
    firstName: user.firstName,
    lastName: user.lastName,
    email: user.primaryEmailAddress?.emailAddress ?? meData.email ?? null,
    // ★ Role desde DB via /me (fuente de verdad única)
    role,
    hasPhiAccess: role !== null && PHI_ROLES.has(role),
    isLoaded: true,
  };
}
