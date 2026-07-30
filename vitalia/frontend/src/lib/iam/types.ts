// cap: iam.luana-core-adoption
// story-origin: vitalia-fase1-s9-TBD
/**
 * lib/iam/types.ts — TypeScript types for IAM module (F1-S9 T-2).
 *
 * Mirror of luana_core_iam TenantSchema Pydantic DTO.
 * spec_anchor: 03-arch-fe.md § 2.1 NEW lib/iam/types.ts
 * anti-duplication: consumes core endpoint GET /api/v1/iam/users/me/tenants
 */

/**
 * TenantSchema — camelCase mirror of core TenantSchema Pydantic DTO.
 * Fields: id (UUID string), name, slug, role.
 * No PHI fields — endpoint returns identity + tenant list only (HIPAA-lite exempt).
 *
 * spec_anchor: 03-arch-fe.md § 2 + CONTEXT-BRIEF § 7 anti-duplication verdict
 */
export interface TenantSchema {
  /** Tenant UUID — used as [tenantId] path segment in routing tree. */
  id: string;
  /** Human-readable clinic/organization name. */
  name: string;
  /** URL-safe slug identifier. */
  slug: string;
  /** Role of current user within this tenant (e.g., "admin", "doctor", "staff"). */
  role: string;
}
