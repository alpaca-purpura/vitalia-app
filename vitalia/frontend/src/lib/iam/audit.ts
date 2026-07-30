// cap: compliance.hipaa-lite-defensive-stack
// story-origin: vitalia-fase1-s9-TBD
/**
 * lib/iam/audit.ts — HIPAA-lite audit logging helpers for IAM events (F1-S9 T-2).
 *
 * F1-S9 transport: console.warn (structured JSON payload).
 * Fase 2 scope: replace with POST to /api/v1/audit/iam-events (backend endpoint).
 *
 * HIPAA-lite compliance:
 *   - Payload includes ONLY: action, userId, attemptedTenant, timestamp
 *   - NO PHI (no diagnosis, no treatment, no patient name, no medical data)
 *   - userId is a Clerk opaque ID — not a PII identifier in isolation
 *   - Format: console.warn('[audit]', { action, userId, ..., timestamp })
 *
 * spec_anchor: 03-arch-fe.md § 4 + 06-tickets.yaml T-2 + vitalia/.claude/rules/hipaa-lite.md
 */

/**
 * Payload for cross-tenant access attempt audit event.
 * SC-4: user authenticated to tenant A but navigating to tenant B.
 */
export interface CrossTenantAttemptPayload {
  /** Clerk user ID (opaque string — not PII in isolation per HIPAA-lite). */
  userId: string;
  /** Tenant ID the user attempted to access (not their assigned tenant). */
  attemptedTenant: string;
}

/**
 * Payload for no-tenants-assigned audit event.
 * SC-8: authenticated user has zero tenants assigned in the platform.
 */
export interface NoTenantsAssignedPayload {
  /** Clerk user ID (opaque string — not PII in isolation per HIPAA-lite). */
  userId: string;
}

/**
 * Log a cross-tenant access attempt.
 * Called in (shell-organism)/layout.tsx when tenantId from URL is NOT in user's tenant list.
 *
 * Transport (F1-S9): console.warn — backend endpoint is Fase 2 scope.
 * Action value: "cross_tenant_attempt" (consumed by E2E spy in SC-4 spec).
 */
export function logCrossTenantAttempt(
  payload: CrossTenantAttemptPayload,
): void {
  console.warn("[audit]", {
    action: "cross_tenant_attempt",
    userId: payload.userId,
    attemptedTenant: payload.attemptedTenant,
    timestamp: new Date().toISOString(),
  });
}

/**
 * Log a no-tenants-assigned event.
 * Called in (shell-organism)/layout.tsx when fetchUserTenants returns [].
 * Triggers sign-out flow and redirect to /sign-in?error=no_tenants_assigned.
 *
 * Transport (F1-S9): console.warn — backend endpoint is Fase 2 scope.
 * Action value: "no_tenants_assigned" (consumed by E2E spy in SC-8 spec).
 */
export function logNoTenantsAssigned(payload: NoTenantsAssignedPayload): void {
  console.warn("[audit]", {
    action: "no_tenants_assigned",
    userId: payload.userId,
    timestamp: new Date().toISOString(),
  });
}
