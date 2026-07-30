// cap: patients.nps-tracking
// story-origin: TBD
/**
 * fidelizacion-store.ts — Ephemeral UI state for fidelización feature.
 *
 * Vanilla JS store (Zustand not installed — using subscribe/notify pattern).
 * Ephemeral state: modals open/close, selected card, agent status.
 * Persisted URL state lives in url-state.ts (via useSearchParams).
 *
 * downstream-regression-na: brand-local FE store; no cross-brand consumers
 */

export interface FidelizacionStoreState {
  /** Currently focused patient (for contact sidebar) */
  selectedPatientId: string | null;
  /** Currently expanded card (for detail expansion) */
  expandedCardId: string | null;
  /** Pause patient modal */
  isPauseModalOpen: boolean;
  pauseModalTargetEventId: string | null;
  /** Confirm template (Adrián recordatorio) modal */
  isConfirmTemplateModalOpen: boolean;
  confirmTemplateEventId: string | null;
  /** Manual call log modal */
  isManualCallModalOpen: boolean;
  manualCallTargetEventId: string | null;
  /** Suggest slots modal */
  isSuggestSlotsModalOpen: boolean;
  suggestSlotsTargetEventId: string | null;
  /** Agent thinking state (cron mid-run) */
  agentThinkingEventId: string | null;
  /** Agent failed state */
  agentFailedEventId: string | null;
}

export interface FidelizacionStoreActions {
  selectPatient: (patientId: string | null) => void;
  setExpandedCard: (cardId: string | null) => void;
  openPauseModal: (eventId: string) => void;
  closePauseModal: () => void;
  openConfirmTemplateModal: (eventId: string) => void;
  closeConfirmTemplateModal: () => void;
  openManualCallModal: (eventId: string) => void;
  closeManualCallModal: () => void;
  openSuggestSlotsModal: (eventId: string) => void;
  closeSuggestSlotsModal: () => void;
  setAgentThinking: (eventId: string) => void;
  clearAgentThinking: () => void;
  setAgentFailed: (eventId: string) => void;
  clearAgentFailed: () => void;
  reset: () => void;
}

export type FidelizacionStore = {
  getState: () => FidelizacionStoreState & FidelizacionStoreActions;
  subscribe: (listener: () => void) => () => void;
};

const INITIAL_STATE: FidelizacionStoreState = {
  selectedPatientId: null,
  expandedCardId: null,
  isPauseModalOpen: false,
  pauseModalTargetEventId: null,
  isConfirmTemplateModalOpen: false,
  confirmTemplateEventId: null,
  isManualCallModalOpen: false,
  manualCallTargetEventId: null,
  isSuggestSlotsModalOpen: false,
  suggestSlotsTargetEventId: null,
  agentThinkingEventId: null,
  agentFailedEventId: null,
};

/**
 * Create a fidelización store instance.
 * Returns a store object with getState() and subscribe().
 *
 * Usage in components: use useFidelizacionStore() hook which wraps this.
 */
export function createFidelizacionStore(): FidelizacionStore {
  let state: FidelizacionStoreState & FidelizacionStoreActions;
  const listeners = new Set<() => void>();

  function notify() {
    listeners.forEach((l) => l());
  }

  function setState(partial: Partial<FidelizacionStoreState>) {
    state = { ...state, ...partial };
    notify();
  }

  const actions: FidelizacionStoreActions = {
    selectPatient: (patientId) => setState({ selectedPatientId: patientId }),

    setExpandedCard: (cardId) => setState({ expandedCardId: cardId }),

    openPauseModal: (eventId) =>
      setState({ isPauseModalOpen: true, pauseModalTargetEventId: eventId }),

    closePauseModal: () =>
      setState({ isPauseModalOpen: false, pauseModalTargetEventId: null }),

    openConfirmTemplateModal: (eventId) =>
      setState({
        isConfirmTemplateModalOpen: true,
        confirmTemplateEventId: eventId,
      }),

    closeConfirmTemplateModal: () =>
      setState({
        isConfirmTemplateModalOpen: false,
        confirmTemplateEventId: null,
      }),

    openManualCallModal: (eventId) =>
      setState({
        isManualCallModalOpen: true,
        manualCallTargetEventId: eventId,
      }),

    closeManualCallModal: () =>
      setState({ isManualCallModalOpen: false, manualCallTargetEventId: null }),

    openSuggestSlotsModal: (eventId) =>
      setState({
        isSuggestSlotsModalOpen: true,
        suggestSlotsTargetEventId: eventId,
      }),

    closeSuggestSlotsModal: () =>
      setState({
        isSuggestSlotsModalOpen: false,
        suggestSlotsTargetEventId: null,
      }),

    setAgentThinking: (eventId) => setState({ agentThinkingEventId: eventId }),

    clearAgentThinking: () => setState({ agentThinkingEventId: null }),

    setAgentFailed: (eventId) => setState({ agentFailedEventId: eventId }),

    clearAgentFailed: () => setState({ agentFailedEventId: null }),

    reset: () => {
      state = { ...INITIAL_STATE, ...actions };
      notify();
    },
  };

  state = { ...INITIAL_STATE, ...actions };

  return {
    getState: () => state,
    subscribe: (listener) => {
      listeners.add(listener);
      return () => listeners.delete(listener);
    },
  };
}
