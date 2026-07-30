// cap: patients.nps-tracking
// story-origin: TBD
"use client";

/**
 * use-fidelizacion-url-state — URL state management for fidelización feature.
 *
 * Uses native Next.js useSearchParams + useRouter (nuqs not installed).
 * Provides typed read + typed write helpers.
 *
 * downstream-regression-na: brand-local FE hook; no cross-brand consumers
 */

import { useCallback } from "react";
import { useRouter, useSearchParams, usePathname } from "next/navigation";
import {
  parseFidelizacionUrlState,
  serializeFidelizacionUrlState,
  DEFAULT_URL_STATE,
  type FidelizacionUrlState,
  type FidelizacionTab,
  type FidelizacionPeriod,
  type UrgencyFilter,
} from "../types/url-state";

export interface UseFidelizacionUrlStateReturn {
  /** Current parsed URL state */
  urlState: FidelizacionUrlState;
  /** Set the active tab (replace history) */
  setTab: (tab: FidelizacionTab) => void;
  /** Set the period filter (replace history) */
  setPeriod: (period: FidelizacionPeriod) => void;
  /** Set vertical filter */
  setVertical: (vertical: string | null) => void;
  /** Set doctor filter */
  setDoctor: (doctor: string | null) => void;
  /** Set urgency filters */
  setUrgency: (urgency: UrgencyFilter[]) => void;
  /** Open confirm template modal with event ID */
  openConfirmTemplateModal: (eventId: string) => void;
  /** Close confirm template modal */
  closeConfirmTemplateModal: () => void;
  /** Open pause modal with event ID */
  openPauseModal: (eventId: string) => void;
  /** Close pause modal */
  closePauseModal: () => void;
  /** Open manual call modal with event ID */
  openManualCallModal: (eventId: string) => void;
  /** Close manual call modal */
  closeManualCallModal: () => void;
  /** Open suggest slots modal with event ID */
  openSuggestSlotsModal: (eventId: string) => void;
  /** Close suggest slots modal */
  closeSuggestSlotsModal: () => void;
  /** Select a patient in sidebar */
  selectPatient: (patientId: string | null) => void;
}

/**
 * Hook for managing fidelización URL state.
 * All state changes use `router.replace` by default (modal states),
 * except tab navigation which uses `router.push`.
 */
export function useFidelizacionUrlState(): UseFidelizacionUrlStateReturn {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const urlState = parseFidelizacionUrlState(searchParams);

  const updateParams = useCallback(
    (
      updates: Partial<FidelizacionUrlState>,
      method: "push" | "replace" = "replace",
    ) => {
      const newState = { ...urlState, ...updates };
      const newParams = serializeFidelizacionUrlState(newState);
      const queryString = newParams.toString();
      const url = queryString ? `${pathname}?${queryString}` : pathname;

      if (method === "push") {
        router.push(url);
      } else {
        router.replace(url);
      }
    },
    [router, pathname, urlState],
  );

  const setTab = useCallback(
    (tab: FidelizacionTab) => updateParams({ tab }, "push"),
    [updateParams],
  );

  const setPeriod = useCallback(
    (period: FidelizacionPeriod) => updateParams({ period }),
    [updateParams],
  );

  const setVertical = useCallback(
    (vertical: string | null) => updateParams({ vertical }),
    [updateParams],
  );

  const setDoctor = useCallback(
    (doctor: string | null) => updateParams({ doctor }),
    [updateParams],
  );

  const setUrgency = useCallback(
    (urgency: UrgencyFilter[]) => updateParams({ urgency }),
    [updateParams],
  );

  const openConfirmTemplateModal = useCallback(
    (eventId: string) => updateParams({ confirmTemplateModal: eventId }),
    [updateParams],
  );

  const closeConfirmTemplateModal = useCallback(
    () => updateParams({ confirmTemplateModal: null }),
    [updateParams],
  );

  const openPauseModal = useCallback(
    (eventId: string) => updateParams({ pauseModal: eventId }),
    [updateParams],
  );

  const closePauseModal = useCallback(
    () => updateParams({ pauseModal: null }),
    [updateParams],
  );

  const openManualCallModal = useCallback(
    (eventId: string) => updateParams({ manualCallModal: eventId }),
    [updateParams],
  );

  const closeManualCallModal = useCallback(
    () => updateParams({ manualCallModal: null }),
    [updateParams],
  );

  const openSuggestSlotsModal = useCallback(
    (eventId: string) => updateParams({ suggestSlotsModal: eventId }),
    [updateParams],
  );

  const closeSuggestSlotsModal = useCallback(
    () => updateParams({ suggestSlotsModal: null }),
    [updateParams],
  );

  const selectPatient = useCallback(
    (patientId: string | null) => updateParams({ selectedPatient: patientId }),
    [updateParams],
  );

  return {
    urlState,
    setTab,
    setPeriod,
    setVertical,
    setDoctor,
    setUrgency,
    openConfirmTemplateModal,
    closeConfirmTemplateModal,
    openPauseModal,
    closePauseModal,
    openManualCallModal,
    closeManualCallModal,
    openSuggestSlotsModal,
    closeSuggestSlotsModal,
    selectPatient,
  };
}

// Re-export defaults for consumers
export { DEFAULT_URL_STATE };
