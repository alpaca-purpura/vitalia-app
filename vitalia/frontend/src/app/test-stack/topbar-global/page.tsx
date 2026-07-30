// cap: platform.design-tokens-theme
// story-origin: TBD
/**
 * /test-stack/topbar-global — Visual baseline page F1-S2
 * (vitalia-fase1-topbar-global)
 *
 * Serves the TopBarGlobal showcase fixture as a Next.js route.
 * Per F1-S1 lesson: test pages in e2e/__test-pages__/ need a Next.js route
 * wrapper otherwise Playwright 404s. Route lives here outside auth route groups.
 *
 * Public dev-only page — no Clerk auth, no PHI (HIPAA-lite no-phi-scope).
 * See: 03-arch.md § 2.9 + vitalia/.claude/rules/hipaa-lite.md (no-phi-scope)
 */
import TopBarShowcasePage from "@/../e2e/__test-pages__/topbar-global/topbar-showcase";

export default TopBarShowcasePage;
