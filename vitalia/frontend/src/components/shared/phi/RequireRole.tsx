// cap: platform.shell-foundation-shadcn-tailwind-v4
// story-origin: TBD
/**
 * RequireRole — role-gated PHI content wrapper.
 *
 * Per vitalia/.claude/rules/hipaa-lite.md:
 *   - Roles allowed PHI: doctor | nurse | admin_clinic
 *   - Others (marketing, sales, patient) NEVER see PHI directly
 *
 * Usage:
 *   <RequireRole roles={["doctor", "nurse", "admin_clinic"]} userRole={user.role}>
 *     <PatientDiagnosisPanel />
 *   </RequireRole>
 *
 * Note: This is a SERVER-SAFE component (no hooks, pure props).
 * For hook-based usage, wrap with a Client Component that passes userRole.
 */

import type { ReactNode } from "react";

export type PhiRole =
  | "doctor"
  | "nurse"
  | "admin_clinic"
  | "patient"
  | "marketing"
  | "sales"
  | "superadmin";

export interface RequireRoleProps {
  /** Roles that are allowed to see the children */
  roles: PhiRole[];
  /** Current user's role */
  userRole: string | null | undefined;
  /** Content to show when role matches */
  children: ReactNode;
  /** Optional fallback content when access is denied */
  fallback?: ReactNode;
}

/**
 * Renders children only if userRole is in the allowed roles list.
 * Renders fallback (or nothing) if access is denied.
 */
export function RequireRole({
  roles,
  userRole,
  children,
  fallback = null,
}: RequireRoleProps) {
  if (!userRole || !roles.includes(userRole as PhiRole)) {
    return <>{fallback}</>;
  }

  return <>{children}</>;
}
