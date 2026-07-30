// cap: compliance.hipaa-lite-defensive-stack
// story-origin: TBD
"use client";

/**
 * usePiiRoleGate — returns whether the current user can view PHI data.
 *
 * Per vitalia/.claude/rules/hipaa-lite.md:
 *   - Roles allowed PHI: doctor | nurse | admin_clinic
 *   - Other roles (marketing, sales, patient) NEVER see PHI
 *   - Patient role ONLY sees their own data (filtered at BE level)
 *
 * Usage:
 *   const { canViewPhi, role } = usePiiRoleGate();
 *   if (!canViewPhi) return <AccessDenied />;
 */

import { useCurrentUser } from "./useCurrentUser";
import type { VitaliaRole } from "./useCurrentUser";

export interface PiiRoleGate {
  /** Whether the user has PHI access (doctor | nurse | admin_clinic) */
  canViewPhi: boolean;
  /** Current user role */
  role: VitaliaRole | null;
  /** Whether auth has finished loading */
  isLoaded: boolean;
}

/**
 * Returns PHI access gate status for the current user.
 */
export function usePiiRoleGate(): PiiRoleGate {
  const { role, hasPhiAccess, isLoaded } = useCurrentUser();

  return {
    canViewPhi: hasPhiAccess,
    role,
    isLoaded,
  };
}
