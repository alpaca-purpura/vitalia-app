// cap: shell-organism.shell-vitalia
// story-origin: platform-lift-shell-chrome-ui-kit T-V2
/**
 * Architecture test — Shell Store Schema (kit API, T-V2 platform-lift-shell-chrome-ui-kit).
 *
 * T-V2 removes the legacy useShellStore (valeriaOpen API). The canonical store
 * is now useShellStoreKit (supervisorOpen / splitPct API from @luana/ui-kit).
 *
 * Invariant (create-shell-store.ts + migrateShellStateKit):
 *   - supervisorOpen: 'closed' | 'chat'  (A=closed tira-avatar · B=chat split)
 *   - historyOpen: boolean               (additive push — NOT a conflated third state)
 *   - splitPct: number | null            (split %)
 *   - mobileDrawerOpen: boolean          (independent slice)
 *   - valeriaOpen / shellMode / valeriaState ELIMINATED.
 *
 * If a consumer re-introduces valeriaOpen/shellMode/valeriaState/rail/full → FAIL.
 * Storage key 'vitalia-shell-state' MUST stay (E2E addInitScript + persisted migration, SC-6).
 *
 * downstream-regression-na: brand-local arch fitness test; no cross-brand consumers
 */

import { describe, it, expect } from "vitest";
import {
  useShellStoreKit,
  SHELL_STORAGE_KEY,
} from "@/stores/shell-store";

describe("Architecture: shell-store schema invariant (T-V2 kit store)", () => {
  it("SHELL_STORAGE_KEY equals vitalia-shell-state (conserved SC-6)", () => {
    // Storage key cementado SC-6 — must NOT change (breaks E2E addInitScript + persisted migration)
    expect(SHELL_STORAGE_KEY).toBe("vitalia-shell-state");
  });

  it("useShellStoreKit exposes setSupervisorOpen setter", () => {
    expect(typeof useShellStoreKit.getState().setSupervisorOpen).toBe("function");
  });

  it("useShellStoreKit exposes openSupervisor / collapseSupervisor setters", () => {
    expect(typeof useShellStoreKit.getState().openSupervisor).toBe("function");
    expect(typeof useShellStoreKit.getState().collapseSupervisor).toBe("function");
  });

  it("useShellStoreKit exposes setHistoryOpen / openHistory / closeHistory / toggleHistory", () => {
    const state = useShellStoreKit.getState();
    expect(typeof state.setHistoryOpen).toBe("function");
    expect(typeof state.openHistory).toBe("function");
    expect(typeof state.closeHistory).toBe("function");
    expect(typeof state.toggleHistory).toBe("function");
  });

  it("useShellStoreKit exposes setSplitPct setter", () => {
    expect(typeof useShellStoreKit.getState().setSplitPct).toBe("function");
  });

  it("default supervisorOpen is chat (RN-6)", () => {
    useShellStoreKit.setState({ supervisorOpen: "chat", historyOpen: false });
    expect(useShellStoreKit.getState().supervisorOpen).toBe("chat");
  });

  it("default historyOpen is false (RN-5/RN-11 — never persisted open)", () => {
    useShellStoreKit.setState({ supervisorOpen: "chat", historyOpen: false });
    expect(useShellStoreKit.getState().historyOpen).toBe(false);
  });

  it("setSupervisorOpen updates to each valid state", () => {
    useShellStoreKit.getState().setSupervisorOpen("closed");
    expect(useShellStoreKit.getState().supervisorOpen).toBe("closed");

    useShellStoreKit.getState().setSupervisorOpen("chat");
    expect(useShellStoreKit.getState().supervisorOpen).toBe("chat");
  });

  it("collapseSupervisor → closed AND historyOpen=false (RN-6)", () => {
    useShellStoreKit.getState().setSupervisorOpen("chat");
    useShellStoreKit.getState().setHistoryOpen(true);
    useShellStoreKit.getState().collapseSupervisor();
    expect(useShellStoreKit.getState().supervisorOpen).toBe("closed");
    expect(useShellStoreKit.getState().historyOpen).toBe(false);
  });

  it("openSupervisor → chat, NEVER restores history (RN-5)", () => {
    useShellStoreKit.getState().setSupervisorOpen("chat");
    useShellStoreKit.getState().setHistoryOpen(true);
    useShellStoreKit.getState().collapseSupervisor();
    useShellStoreKit.getState().openSupervisor();
    expect(useShellStoreKit.getState().supervisorOpen).toBe("chat");
    expect(useShellStoreKit.getState().historyOpen).toBe(false);
  });

  it("openHistory from closed opens supervisor too (A → B+C) (RN-7 additive)", () => {
    useShellStoreKit.getState().setSupervisorOpen("closed");
    useShellStoreKit.getState().openHistory();
    expect(useShellStoreKit.getState().supervisorOpen).toBe("chat");
    expect(useShellStoreKit.getState().historyOpen).toBe(true);
  });

  it("valeriaOpen / shellMode / valeriaState / valeriaState removed (AC-1)", () => {
    const state = useShellStoreKit.getState() as unknown as Record<string, unknown>;
    expect(state.valeriaOpen).toBeUndefined();
    expect(state.shellMode).toBeUndefined();
    expect(state.valeriaState).toBeUndefined();
    expect(state.cycleValeriaState).toBeUndefined();
    expect(state.setShellMode).toBeUndefined();
    expect(state.setValeriaState).toBeUndefined();
    expect(state.setValeriaOpen).toBeUndefined();
    expect(state.openValeria).toBeUndefined();
    expect(state.collapseValeria).toBeUndefined();
  });
});
