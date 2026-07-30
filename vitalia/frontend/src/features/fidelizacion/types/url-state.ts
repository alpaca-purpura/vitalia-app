// cap: patients.nps-tracking
// story-origin: TBD
/**
 * url-state.ts — URL state types for fidelizacion feature.
 *
 * nuqs is NOT installed — using native Next.js useSearchParams + useRouter.
 * Types define the shape; parsing done via URLSearchParams in the hook.
 *
 * downstream-regression-na: brand-local FE types; no cross-brand consumers
 */

export type FidelizacionTab =
  | "multisession"
  | "followup"
  | "maintenance"
  | "absence"
  | "nps";

export type FidelizacionPeriod = "7d" | "30d" | "90d";

export type UrgencyFilter =
  | "critical"
  | "alert"
  | "near"
  | "waiting"
  | "up_to_date";

export interface FidelizacionUrlState {
  tab: FidelizacionTab;
  period: FidelizacionPeriod;
  vertical: string | null;
  doctor: string | null;
  urgency: UrgencyFilter[];
  selectedPatient: string | null;
  pauseModal: string | null;
  confirmTemplateModal: string | null;
  manualCallModal: string | null;
  suggestSlotsModal: string | null;
}

export const DEFAULT_URL_STATE: FidelizacionUrlState = {
  tab: "multisession",
  period: "30d",
  vertical: null,
  doctor: null,
  urgency: [],
  selectedPatient: null,
  pauseModal: null,
  confirmTemplateModal: null,
  manualCallModal: null,
  suggestSlotsModal: null,
};

const VALID_TABS: FidelizacionTab[] = [
  "multisession",
  "followup",
  "maintenance",
  "absence",
  "nps",
];
const VALID_PERIODS: FidelizacionPeriod[] = ["7d", "30d", "90d"];
const VALID_URGENCY: UrgencyFilter[] = [
  "critical",
  "alert",
  "near",
  "waiting",
  "up_to_date",
];

/**
 * Parse URL search params into typed FidelizacionUrlState.
 * Provides safe defaults for missing/invalid values.
 */
export function parseFidelizacionUrlState(
  params: URLSearchParams,
): FidelizacionUrlState {
  const rawTab = params.get("tab");
  const tab: FidelizacionTab =
    rawTab && VALID_TABS.includes(rawTab as FidelizacionTab)
      ? (rawTab as FidelizacionTab)
      : DEFAULT_URL_STATE.tab;

  const rawPeriod = params.get("period");
  const period: FidelizacionPeriod =
    rawPeriod && VALID_PERIODS.includes(rawPeriod as FidelizacionPeriod)
      ? (rawPeriod as FidelizacionPeriod)
      : DEFAULT_URL_STATE.period;

  const rawUrgency = params.getAll("urgency");
  const urgency = rawUrgency.filter((u): u is UrgencyFilter =>
    VALID_URGENCY.includes(u as UrgencyFilter),
  );

  return {
    tab,
    period,
    vertical: params.get("vertical"),
    doctor: params.get("doctor"),
    urgency,
    selectedPatient: params.get("selectedPatient"),
    pauseModal: params.get("pauseModal"),
    confirmTemplateModal: params.get("confirmTemplateModal"),
    manualCallModal: params.get("manualCallModal"),
    suggestSlotsModal: params.get("suggestSlotsModal"),
  };
}

/**
 * Serialize FidelizacionUrlState to URLSearchParams.
 */
export function serializeFidelizacionUrlState(
  state: Partial<FidelizacionUrlState>,
): URLSearchParams {
  const params = new URLSearchParams();

  if (state.tab && state.tab !== DEFAULT_URL_STATE.tab) {
    params.set("tab", state.tab);
  }
  if (state.period && state.period !== DEFAULT_URL_STATE.period) {
    params.set("period", state.period);
  }
  if (state.vertical) params.set("vertical", state.vertical);
  if (state.doctor) params.set("doctor", state.doctor);
  if (state.urgency) {
    state.urgency.forEach((u) => params.append("urgency", u));
  }
  if (state.selectedPatient)
    params.set("selectedPatient", state.selectedPatient);
  if (state.pauseModal) params.set("pauseModal", state.pauseModal);
  if (state.confirmTemplateModal)
    params.set("confirmTemplateModal", state.confirmTemplateModal);
  if (state.manualCallModal)
    params.set("manualCallModal", state.manualCallModal);
  if (state.suggestSlotsModal)
    params.set("suggestSlotsModal", state.suggestSlotsModal);

  return params;
}
