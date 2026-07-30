// cap: platform.design-tokens-theme
// story-origin: vitalia-fase1-s4-TBD
/**
 * /test-stack/shell-layout — Visual baseline page F1-S4
 * (vitalia-fase1-shell-layout-5050)
 *
 * Serves the ShellOrganismLayout showcase fixture as a Next.js route.
 * Pattern parity con F1-S0..S3 test-stack showcases.
 *
 * Specs e2e/regression/vitalia-fase1-shell-layout-5050/*.spec.ts apuntan
 * via POM ShellLayoutPage.gotoShell() a este route para evitar requerir
 * un real /{tenantId}/lisa/marca route (no existe hasta Fase 2).
 *
 * Public dev-only page — no Clerk auth, no PHI (HIPAA-lite no-phi-scope).
 */
import ShellLayoutShowcasePage from "@/../e2e/__test-pages__/shell-layout/shell-layout-showcase";

export default ShellLayoutShowcasePage;
