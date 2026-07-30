// cap: patients.nps-tracking
// story-origin: TBD
/**
 * fidelizacion/api — Public API barrel.
 *
 * No default exports per FSD-Lite + arch fitness gate.
 *
 * downstream-regression-na: brand-local FE api barrel; no cross-brand consumers
 */

export { useFidelizacionSummary } from "./use-fidelizacion-summary";
export { useReEngagementPatterns } from "./use-re-engagement-patterns";
export { useNpsResponses } from "./use-nps-responses";
export { useActivityStream } from "./use-activity-stream";
export type {
  ActivityEvent,
  ActivityStreamResponse,
} from "./use-activity-stream";
export { useSendProactiveTemplate } from "./use-send-proactive-template";
export { usePausePatient } from "./use-pause-patient";
export { useMarkExternal } from "./use-mark-external";
export { useMarkNoContinue } from "./use-mark-no-continue";
export { useLogManualCall } from "./use-log-manual-call";
export { useAvailabilitySlots } from "./use-availability-slots";
export type {
  AvailabilitySlot,
  AvailabilitySlotsResponse,
} from "./use-availability-slots";
