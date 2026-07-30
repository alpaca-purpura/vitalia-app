// cap: platform.design-tokens-theme
// story-origin: vitalia-fase1-s3-TBD
/**
 * /test-stack/tenant-switcher — Visual baseline page F1-S3
 * (vitalia-fase1-tenant-switcher)
 *
 * Serves the TenantSwitcher showcase fixture as a Next.js route.
 * Per F1-S1 lesson: test pages in e2e/__test-pages__/ need a Next.js route
 * wrapper otherwise Playwright 404s. Route lives here outside auth route groups.
 *
 * TopBarGlobal mounts TenantSwitcher internally (F1-S3 T-8).
 * Specs target /test-stack/tenant-switcher to avoid needing a real
 * /{tenantId}/dashboard route (which doesn't exist yet — Fase 2).
 *
 * Public dev-only page — no Clerk auth, no PHI (HIPAA-lite no-phi-scope).
 * See: 03-arch.md § 2.9 + vitalia/.claude/rules/hipaa-lite.md (no-phi-scope)
 */
import TenantSwitcherShowcasePage from "@/../e2e/__test-pages__/tenant-switcher/tenant-switcher-showcase";

export default TenantSwitcherShowcasePage;
