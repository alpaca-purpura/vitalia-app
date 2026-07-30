// cap: shell-organism.shell-vitalia
// story-origin: platform-lift-shell-chrome-ui-kit T-V2
/**
 * shell-store.test.ts — Kit store state machine tests.
 * platform-lift-shell-chrome-ui-kit T-V2
 *
 * T-V2 removes the legacy useShellStore (valeriaOpen API) and exposes only
 * useShellStoreKit (kit API: supervisorOpen / splitPct). These tests migrate
 * from the old valeriaOpen/historyOpen API to the canonical kit API.
 *
 * Machine (generic kit, create-shell-store.ts):
 *   A=closed   : supervisorOpen 'closed' ⇒ historyOpen forced false (RN-5)
 *   B=chat     : supervisorOpen 'chat', NEVER restores history (RN-6)
 *   C=chat+hist: supervisorOpen 'chat' + historyOpen true (RN-7 additive)
 *
 * gherkin_coverage:
 * - SC-1 happy: default supervisorOpen/historyOpen defaults
 * - SC-5 RN-5/6: collapsing closes history; reopening NEVER restores history
 * - SC-8 RN-7: historyOpen additive (not conflated with supervisorOpen)
 *
 * Named export (no default export) per FSD-Lite enforce.
 * downstream-regression-na: brand-local store test; no cross-brand consumers
 */

import { describe, it, expect, beforeEach } from "vitest";
import { useShellStoreKit, SHELL_STORAGE_KEY } from "../shell-store";

describe("useShellStoreKit — kit state machine (closed|chat + historyOpen additive)", () => {
  beforeEach(() => {
    // Reset to factory default. Default supervisorOpen='chat' (B).
    useShellStoreKit.setState({
      supervisorOpen: "chat",
      historyOpen: false,
      splitPct: null,
      mobileDrawerOpen: false,
    });
  });

  // ── SC-1 happy: initial state ────────────────────────────────────────────

  describe("initial state", () => {
    it("supervisorOpen='chat' historyOpen=false splitPct=null mobileDrawerOpen=false", () => {
      const state = useShellStoreKit.getState();
      expect(state.supervisorOpen).toBe("chat");
      expect(state.historyOpen).toBe(false);
      expect(state.splitPct).toBeNull();
      expect(state.mobileDrawerOpen).toBe(false);
    });

    it("valeriaOpen / shellMode / valeriaState NOT present on kit store (AC-1 — eliminated)", () => {
      const state = useShellStoreKit.getState() as unknown as Record<string, unknown>;
      expect(state.valeriaOpen).toBeUndefined();
      expect(state.shellMode).toBeUndefined();
      expect(state.setShellMode).toBeUndefined();
      expect(state.cycleValeriaState).toBeUndefined();
      expect(state.valeriaState).toBeUndefined();
    });
  });

  // ── SHELL_STORAGE_KEY (conserved) ──────────────────────────────────────────

  describe("SHELL_STORAGE_KEY", () => {
    it("SHELL_STORAGE_KEY exported 'vitalia-shell-state' (conserved SC-6)", () => {
      expect(SHELL_STORAGE_KEY).toBe("vitalia-shell-state");
    });
  });

  // ── supervisorOpen: closed <-> chat ───────────────────────────────────────

  describe("setSupervisorOpen", () => {
    it("setSupervisorOpen('closed') sets state A", () => {
      useShellStoreKit.getState().setSupervisorOpen("closed");
      expect(useShellStoreKit.getState().supervisorOpen).toBe("closed");
    });

    it("setSupervisorOpen('chat') sets state B", () => {
      useShellStoreKit.getState().setSupervisorOpen("closed");
      useShellStoreKit.getState().setSupervisorOpen("chat");
      expect(useShellStoreKit.getState().supervisorOpen).toBe("chat");
    });
  });

  // ── RN-5 / RN-6 transitions: collapse closes history; reopen never restores ─

  describe("RN-5/6 transitions", () => {
    it("collapseSupervisor → A (supervisorOpen='closed') AND forces historyOpen=false (RN-6)", () => {
      // Start in C (chat + history)
      useShellStoreKit.getState().setSupervisorOpen("chat");
      useShellStoreKit.getState().setHistoryOpen(true);
      expect(useShellStoreKit.getState().historyOpen).toBe(true);

      useShellStoreKit.getState().collapseSupervisor();

      expect(useShellStoreKit.getState().supervisorOpen).toBe("closed");
      // colapsar cierra historial también (RN-6)
      expect(useShellStoreKit.getState().historyOpen).toBe(false);
    });

    it("openSupervisor (reopen) → B chat-only, NEVER restores history (RN-5)", () => {
      // Was in C before collapsing
      useShellStoreKit.getState().setSupervisorOpen("chat");
      useShellStoreKit.getState().setHistoryOpen(true);
      useShellStoreKit.getState().collapseSupervisor(); // → A, history false
      expect(useShellStoreKit.getState().supervisorOpen).toBe("closed");

      useShellStoreKit.getState().openSupervisor();

      expect(useShellStoreKit.getState().supervisorOpen).toBe("chat");
      // RN-5: reapertura NUNCA restaura el historial
      expect(useShellStoreKit.getState().historyOpen).toBe(false);
    });

    it("historyOpen forced false while supervisorOpen='closed' (RN-5 invariant)", () => {
      useShellStoreKit.getState().setSupervisorOpen("closed");
      // Attempt to open history while closed must NOT leave A
      useShellStoreKit.getState().setHistoryOpen(true);
      // RN-5: en A, historyOpen está forzado false
      expect(useShellStoreKit.getState().historyOpen).toBe(false);
    });
  });

  // ── SC-8 RN-7: historyOpen additive (opens supervisor too from A) ───────────

  describe("openHistory — additive (RN-7)", () => {
    it("setHistoryOpen(true) from chat → C (chat + history)", () => {
      useShellStoreKit.getState().setSupervisorOpen("chat");
      useShellStoreKit.getState().setHistoryOpen(true);
      expect(useShellStoreKit.getState().supervisorOpen).toBe("chat");
      expect(useShellStoreKit.getState().historyOpen).toBe(true);
    });

    it("openHistory from A opens supervisor too (A → B+C) (RN-7)", () => {
      useShellStoreKit.getState().setSupervisorOpen("closed");
      useShellStoreKit.getState().openHistory();
      // abrir historial desde A → B+C (abre supervisor también)
      expect(useShellStoreKit.getState().supervisorOpen).toBe("chat");
      expect(useShellStoreKit.getState().historyOpen).toBe(true);
    });

    it("closeHistory → B (chat, history closed)", () => {
      useShellStoreKit.getState().setSupervisorOpen("chat");
      useShellStoreKit.getState().setHistoryOpen(true);
      useShellStoreKit.getState().closeHistory();
      expect(useShellStoreKit.getState().supervisorOpen).toBe("chat");
      expect(useShellStoreKit.getState().historyOpen).toBe(false);
    });

    it("toggleHistory flips historyOpen (chat context)", () => {
      useShellStoreKit.getState().setSupervisorOpen("chat");
      useShellStoreKit.getState().setHistoryOpen(false);
      useShellStoreKit.getState().toggleHistory();
      expect(useShellStoreKit.getState().historyOpen).toBe(true);
      useShellStoreKit.getState().toggleHistory();
      expect(useShellStoreKit.getState().historyOpen).toBe(false);
    });
  });

  // ── splitPct (split %) ────────────────────────────────────────────────────

  describe("setSplitPct", () => {
    it("setSplitPct(45) updates split %", () => {
      useShellStoreKit.getState().setSplitPct(45);
      expect(useShellStoreKit.getState().splitPct).toBe(45);
    });

    it("setSplitPct(null) resets to default", () => {
      useShellStoreKit.getState().setSplitPct(45);
      useShellStoreKit.getState().setSplitPct(null);
      expect(useShellStoreKit.getState().splitPct).toBeNull();
    });
  });

  // ── mobileDrawerOpen slice independence (conserved) ────────────────────────

  describe("mobileDrawerOpen slice independence", () => {
    it("setMobileDrawerOpen(true) does not change supervisorOpen", () => {
      useShellStoreKit.getState().setSupervisorOpen("chat");
      useShellStoreKit.getState().setMobileDrawerOpen(true);
      expect(useShellStoreKit.getState().mobileDrawerOpen).toBe(true);
      expect(useShellStoreKit.getState().supervisorOpen).toBe("chat");
    });
  });

  // ── persist partialize ─────────────────────────────────────────────────────

  describe("persist partialize", () => {
    it("persist API defined", () => {
      expect(useShellStoreKit.persist).toBeDefined();
    });

    it("storage key is vitalia-shell-state (SC-6 canonical key)", () => {
      expect(useShellStoreKit.persist.getOptions().name).toBe("vitalia-shell-state");
    });

    it("partialize persists supervisorOpen, splitPct, mobileDrawerOpen — NOT historyOpen (RN-5/11)", () => {
      const partialize = useShellStoreKit.persist.getOptions().partialize;
      expect(partialize).toBeDefined();
      if (partialize) {
        const partial = partialize(useShellStoreKit.getState()) as Record<string, unknown>;
        expect(partial).toHaveProperty("supervisorOpen");
        expect(partial).toHaveProperty("splitPct");
        expect(partial).toHaveProperty("mobileDrawerOpen");
        // RN-5/RN-11: historial NUNCA persiste abierto
        expect(partial).not.toHaveProperty("historyOpen");
        // setters + transient excluded
        expect(partial).not.toHaveProperty("setSupervisorOpen");
        expect(partial).not.toHaveProperty("openSupervisor");
        expect(partial).not.toHaveProperty("collapseSupervisor");
        expect(partial).not.toHaveProperty("toggleHistory");
        expect(partial).not.toHaveProperty("_hasHydrated");
      }
    });
  });
});
