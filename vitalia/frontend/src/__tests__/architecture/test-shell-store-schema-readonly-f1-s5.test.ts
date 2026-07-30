// cap: shell-organism.shell-vitalia
// story-origin: platform-lift-shell-chrome-ui-kit T-V2
/**
 * Architecture test — Shell Store Schema Invariant (kit store enforce, T-V2).
 *
 * T-V2 (platform-lift-shell-chrome-ui-kit) removes the legacy useShellStore
 * (valeriaOpen API) and exposes only useShellStoreKit (kit API).
 *
 * This test enforces the kit-store invariants:
 *   - supervisorOpen: 'closed' | 'chat'  (A=closed tira-avatar · B=chat split)
 *   - historyOpen: boolean               (additive push — NOT a conflated third state)
 *   - splitPct: number | null            (split %)
 *   - mobileDrawerOpen: boolean          (independent slice)
 *   - valeriaOpen / shellMode / valeriaState / cycleValeriaState ELIMINATED.
 *
 * If a consumer re-introduces valeriaOpen/shellMode → FAIL.
 * Storage key 'vitalia-shell-state' MUST stay (E2E addInitScript + persisted migration, SC-6).
 *
 * downstream-regression-na: brand-local arch fitness test; no cross-brand consumers
 */

import { describe, it, expect } from "vitest";
import type { SsrSafeHydration } from "@luana/hooks/create-ssr-safe-persisted-store";
import {
  useShellStoreKit,
  SHELL_STORAGE_KEY,
} from "@/stores/shell-store";

describe("Architecture: shell-store schema invariant (T-V2 kit store readonly)", () => {
  it("SHELL_STORAGE_KEY is vitalia-shell-state (SC-6 — must never change)", () => {
    expect(SHELL_STORAGE_KEY).toBe("vitalia-shell-state");
  });

  it("kit store uses canonical key vitalia-shell-state", () => {
    expect(useShellStoreKit.persist.getOptions().name).toBe("vitalia-shell-state");
  });

  it("supervisorOpen valid states are closed | chat", () => {
    const validStates = ["closed", "chat"] as const;
    for (const s of validStates) {
      useShellStoreKit.getState().setSupervisorOpen(s);
      expect(useShellStoreKit.getState().supervisorOpen).toBe(s);
    }
  });

  it("historyOpen is a boolean slice (additive, not conflated with supervisorOpen)", () => {
    useShellStoreKit.getState().setSupervisorOpen("chat");
    useShellStoreKit.getState().setHistoryOpen(true);
    expect(useShellStoreKit.getState().historyOpen).toBe(true);
    expect(typeof useShellStoreKit.getState().historyOpen).toBe("boolean");
  });

  it("legacy fields valeriaOpen + shellMode + cycleValeriaState + valeriaState ELIMINATED (AC-1)", () => {
    const state = useShellStoreKit.getState() as unknown as Record<string, unknown>;
    expect(state.valeriaOpen).toBeUndefined();
    expect(state.shellMode).toBeUndefined();
    expect(state.setShellMode).toBeUndefined();
    expect(state.cycleValeriaState).toBeUndefined();
    expect(state.valeriaState).toBeUndefined();
    expect(state.setValeriaState).toBeUndefined();
    expect(state.setValeriaOpen).toBeUndefined();
    expect(state.openValeria).toBeUndefined();
    expect(state.collapseValeria).toBeUndefined();
    expect(state.valeriaPct).toBeUndefined();
    expect(state.setValeriaPct).toBeUndefined();
  });

  it("_hasHydrated exposed (SsrSafeHydration interface)", () => {
    // Type check: SsrSafeHydration interface is exported from shell-store
    const state = useShellStoreKit.getState();
    expect(typeof state._hasHydrated).toBe("boolean");
    const _typeCheck: SsrSafeHydration = state;
    expect(_typeCheck).toBeDefined();
  });
});
