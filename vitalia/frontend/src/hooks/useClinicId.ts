// cap: compliance.hipaa-lite-defensive-stack
// story-origin: TBD
"use client";

/**
 * useClinicId — returns the current clinic ID for HIPAA-lite dual filter.
 *
 * Per vitalia/.claude/rules/hipaa-lite.md:
 *   - Vitalia adds clinic_id as second required filter on all PHI queries
 *   - X-Clinic-ID header must be sent alongside X-Tenant-ID
 *
 * Source of truth: Clerk user.publicMetadata.clinicId
 *   This is OUR data (luana-core-iam), written by us into Clerk user public
 *   metadata for convenience. It is NOT sourced from Clerk Organizations.
 *
 * Per MEMORY.md::no-clerk-organizations (2026-05-20):
 *   Luana does NOT use Clerk Organizations. tenant_id and clinic_id are
 *   resolved from our own luana-core-iam data, NOT from Clerk org APIs.
 *   The publicMetadata fields are written by our IAM module.
 */

import { useUser } from "@clerk/nextjs";

/**
 * Returns the current user's clinic ID for HIPAA-lite PHI filtering.
 *
 * Reads exclusively from user.publicMetadata.clinicId (our claim, written by
 * luana-core-iam). Returns null if not yet loaded or user has no clinic assigned.
 *
 * Does NOT fall back to Clerk organization metadata — Luana does not use
 * Clerk Organizations (see MEMORY.md::no-clerk-organizations).
 */
export function useClinicId(): string | null {
  const { user, isLoaded } = useUser();

  if (!isLoaded) return null;

  if (user) {
    const meta = user.publicMetadata as Record<string, unknown>;
    if (typeof meta.clinicId === "string" && meta.clinicId.length > 0) {
      return meta.clinicId;
    }
  }

  return null;
}
