/**
 * fidelizacion-store — TDD RED tests for Zustand-like store via React state.
 *
 * downstream-regression-na: brand-local FE store; no cross-brand consumers
 */

import { describe, it, expect, beforeEach } from "vitest";
import { createFidelizacionStore } from "../../store/fidelizacion-store";

describe("createFidelizacionStore", () => {
  let store: ReturnType<typeof createFidelizacionStore>;

  beforeEach(() => {
    store = createFidelizacionStore();
  });

  it("initializes with default values", () => {
    const state = store.getState();
    expect(state.selectedPatientId).toBeNull();
    expect(state.expandedCardId).toBeNull();
    expect(state.isPauseModalOpen).toBe(false);
    expect(state.isConfirmTemplateModalOpen).toBe(false);
    expect(state.isManualCallModalOpen).toBe(false);
    expect(state.isSuggestSlotsModalOpen).toBe(false);
    expect(state.agentThinkingEventId).toBeNull();
  });

  it("selectPatient sets selectedPatientId", () => {
    store.getState().selectPatient("pat-1");
    expect(store.getState().selectedPatientId).toBe("pat-1");
  });

  it("openPauseModal sets isPauseModalOpen + targetEventId", () => {
    store.getState().openPauseModal("evt-1");
    const state = store.getState();
    expect(state.isPauseModalOpen).toBe(true);
    expect(state.pauseModalTargetEventId).toBe("evt-1");
  });

  it("closePauseModal resets isPauseModalOpen + targetEventId", () => {
    store.getState().openPauseModal("evt-1");
    store.getState().closePauseModal();
    const state = store.getState();
    expect(state.isPauseModalOpen).toBe(false);
    expect(state.pauseModalTargetEventId).toBeNull();
  });

  it("openConfirmTemplateModal sets modal open + eventId", () => {
    store.getState().openConfirmTemplateModal("evt-2");
    const state = store.getState();
    expect(state.isConfirmTemplateModalOpen).toBe(true);
    expect(state.confirmTemplateEventId).toBe("evt-2");
  });

  it("setAgentThinking sets agentThinkingEventId", () => {
    store.getState().setAgentThinking("evt-3");
    expect(store.getState().agentThinkingEventId).toBe("evt-3");
  });

  it("clearAgentThinking resets agentThinkingEventId", () => {
    store.getState().setAgentThinking("evt-3");
    store.getState().clearAgentThinking();
    expect(store.getState().agentThinkingEventId).toBeNull();
  });
});
