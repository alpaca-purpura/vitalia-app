// cap: configuracion.cuenta
// story-origin: vitalia-fase2-config-cuenta
/**
 * config/index.ts — Feature public API (FSD-Lite boundary matrix).
 *
 * T-1 vitalia-fase2-config-cuenta:
 *   - Exports AccountDataView, PreferencesView, ResponsibleView (real views).
 *   - Removes CuentaPlaceholder (replaced by real views).
 *
 * downstream-regression-na: brand-local FE barrel; no cross-brand consumers
 */

// ── Real Mi Cuenta views (T-1 vitalia-fase2-config-cuenta) ──────────────────
export { AccountDataView } from "./components/cuenta/AccountDataView";
export { PreferencesView } from "./components/cuenta/PreferencesView";
export { ResponsibleView } from "./components/cuenta/ResponsibleView";

// ── Types (consumed by pages + tests) ────────────────────────────────────────
export type {
  ClinicAccountDTO,
  ClinicAccountPatchDTO,
  SpecialtyCatalogDTO,
  DpoReferenceDTO,
} from "./types/cuenta.types";

// ── Placeholder components (still active — conexiones + avanzado not yet shipped) ─
// CuentaPlaceholder removed — replaced by AccountDataView + PreferencesView + ResponsibleView
export { AvanzadoPlaceholder } from "./components/placeholders/AvanzadoPlaceholder";

// ── Special placeholders ─────────────────────────────────────────────────────
export { ConexionesPlaceholder } from "./components/placeholders/ConexionesPlaceholder";
