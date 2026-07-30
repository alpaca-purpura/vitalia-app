/**
 * BrandContext — per-tenant context passed to extension handlers.
 *
 * TypeScript mirror of Python BrandContext frozen dataclass (9 fields).
 * Per §7.5.2 D3 — frozen at v0.1.0. Future optional fields may be added
 * without breaking bump.
 *
 * NO PII fields — safe to include in trace logs.
 */

export type BrandSlug = "nicolify" | "vitalia" | "comunify" | "lupulo" | "test-brand";

export type VerticalKind = "marketing" | "medical" | "creator-economy" | "gastronomy";

export type PiiPolicy = "standard" | "medical" | "creator" | "gastronomy";

export interface BrandContext {
  /** Opaque tenant UUID (snake_case: tenant_id) */
  tenantId: string;
  /** Brand slug from allowlist (snake_case: brand_slug) */
  brandSlug: BrandSlug;
  /** Plan tier identifier (snake_case: plan_tier) */
  planTier: string;
  /** ISO 639-1 + region locale, e.g. "es-AR" | "es-MX" | "en-US" (snake_case: locale) */
  locale: string;
  /** Tenant-level feature flag map (snake_case: feature_flags) */
  featureFlags: Record<string, boolean>;
  /** Opaque tenant profile UUID (snake_case: tenant_profile_id) */
  tenantProfileId: string;
  /** Vertical domain kind (snake_case: vertical_kind) */
  verticalKind: VerticalKind;
  /** Compliance flags, e.g. { hipaa_required: true } (snake_case: compliance_flags) */
  complianceFlags: Record<string, boolean>;
  /** PII handling policy (snake_case: pii_policy) */
  piiPolicy: PiiPolicy;
}
