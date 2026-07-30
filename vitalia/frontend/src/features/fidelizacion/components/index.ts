// cap: patients.nps-tracking
// story-origin: TBD
/**
 * fidelizacion/components/index.ts — Components barrel (FSD-Lite public API).
 *
 * Only export components used outside this feature (via feature/index.ts).
 * Internal-only components may also appear here for intra-feature convenience.
 *
 * downstream-regression-na: brand-local FE barrel; no cross-brand consumers
 */

export { FidelizacionLayout } from "./FidelizacionLayout";
export { FidelizacionKPIsHero } from "./FidelizacionKPIsHero";
export { FidelizacionTabsBar } from "./FidelizacionTabsBar";
export { FidelizacionActivityFooter } from "./FidelizacionActivityFooter";
export { ReEngagementCard } from "./ReEngagementCard";
export type { ReEngagementCardHandlers } from "./ReEngagementCard";
export { NPSRowCompact } from "./NPSRowCompact";
export { ReEngagementContactSidebar } from "./ReEngagementContactSidebar";
export { ConfirmTemplateModal } from "./ConfirmTemplateModal";
export { PausePatientModal } from "./PausePatientModal";
export { ManualCallLoggedModal } from "./ManualCallLoggedModal";
export { SuggestSlotsModal } from "./SuggestSlotsModal";
export { MultiSessionTab } from "./tabs/MultiSessionTab";
export { FollowUpTab } from "./tabs/FollowUpTab";
export { MaintenanceTab } from "./tabs/MaintenanceTab";
export { AbsenceTab } from "./tabs/AbsenceTab";
export { NPSResumenTab } from "./tabs/NPSResumenTab";
