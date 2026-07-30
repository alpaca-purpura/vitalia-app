// cap: patients.nps-tracking
// story-origin: TBD
/**
 * fidelizacion/index.ts — Feature public API (FSD-Lite boundary matrix).
 *
 * Exposes only what external consumers (app/ routes, other feature imports if allowed)
 * need from this feature. Internal-only modules are NOT re-exported here.
 *
 * downstream-regression-na: brand-local FE barrel; no cross-brand consumers
 */

// ── Components ────────────────────────────────────────────────────────────────
export { FidelizacionLayout } from "./components/FidelizacionLayout";

// ── Copy constants (used by page.tsx metadata etc.) ───────────────────────────
export { FIDELIZACION_COPY } from "./copy";

// ── Types (exported for page-level usage if needed) ───────────────────────────
export type {
  FidelizacionTab,
  FidelizacionPeriod,
  UrgencyFilter,
  FidelizacionUrlState,
} from "./types/url-state";

export type { FidelizacionSummaryResponse } from "./types/fidelizacion-summary";
export type { NPSSummaryResponse, NPSRowDTO, NPSBand } from "./types/nps";
export type { PatternRow, ReEngagementPattern } from "./types/re-engagement";
