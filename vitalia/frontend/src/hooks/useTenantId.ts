// cap: iam.luana-core-adoption
// story-origin: vitalia-fe-tenant-resolution-no-clerk-org
"use client";

/**
 * useTenantId — returns the current tenant ID for all API requests.
 *
 * Per MEMORY.md::no-clerk-organizations (2026-05-20 + 2026-06-01):
 *   Luana does NOT use Clerk Organizations. tenant_id is OUR data
 *   (luana-core-iam), written by us into Clerk user.publicMetadata
 *   for convenient FE access. It is NOT the Clerk Organization id
 *   (format: org_3DzUI3...) — that is NOT a UUID and will cause
 *   backend UUID() parse errors (500 on all PHI endpoints).
 *
 * Source of truth: user.publicMetadata.tenant_id (UUID string)
 *   Set by luana-core-iam when user is provisioned.
 *   Example: "e69a691d-070e-5caf-a053-6e74642ec100"
 *
 * NEVER use:
 *   - useAuth().orgId  → format org_xxx, NOT a UUID, breaks backend
 *   - useOrganization  → Clerk Orgs not used in Luana
 *   - auth().orgId     → same issue
 *
 * Mirrors the pattern of useClinicId.ts (clinic_id from publicMetadata.clinicId).
 */

import { useUser } from "@clerk/nextjs";

/**
 * Returns the current user's tenant ID for X-Tenant-ID header injection.
 *
 * Reads exclusively from user.publicMetadata.tenant_id (our claim, written by
 * luana-core-iam). Returns null if not yet loaded or claim is absent.
 *
 * Does NOT fall back to Clerk organization metadata — Luana does not use
 * Clerk Organizations (see MEMORY.md::no-clerk-organizations).
 */
export function useTenantId(): string | null {
  const { user, isLoaded } = useUser();

  if (!isLoaded) return null;

  if (user) {
    const meta = user.publicMetadata as Record<string, unknown>;
    if (typeof meta.tenant_id === "string" && meta.tenant_id.length > 0) {
      return meta.tenant_id;
    }
  }

  return null;
}
