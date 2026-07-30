// cap: shell-organism.shell-vitalia
// story-origin: platform-lift-shell-chrome-ui-kit T-V2
/**
 * shell-store-hydration.test.ts — Kit store SSR-safe hydration + legacy migration tests.
 * platform-lift-shell-chrome-ui-kit T-V2
 *
 * T-V2 removes the legacy useShellStore. All tests now use useShellStoreKit
 * (kit API: supervisorOpen / splitPct) against the canonical key 'vitalia-shell-state'.
 *
 * Covers:
 *
 * SC-1/SC-5 SSR-safe (no-clobber — ADR-vitalia-006):
 *   - Seed localStorage with a NEW-shape preference (supervisorOpen)
 *   - Pre-hydration window: store created, mutations happen, NO setItem to the key
 *   - Post-rehydrate: value comes from storage (not the default)
 *
 * SC-18 legacy migration (no-crash):
 *   - Old shape {valeriaState:'collapsed'|'rail'|'full', shellMode} migrates:
 *       collapsed → supervisorOpen='closed'
 *       rail      → supervisorOpen='chat', historyOpen=false
 *       full      → supervisorOpen='chat', historyOpen=false (NO restore history — RN-5)
 *   - v1 shape {valeriaOpen: ...} migrates → supervisorOpen (field rename compat)
 *   - corrupt / unknown → fallback {supervisorOpen:'chat', historyOpen:false} + console.warn
 *   - NO clobber during SSR/skeleton (factory setItem NO-OP pre-hydration)
 *
 * Named export (no default export) per FSD-Lite enforce.
 * downstream-regression-na: brand-local store test; no cross-brand consumers
 */

import { describe, it, expect, beforeEach, vi, afterEach } from "vitest";
import { act } from "@testing-library/react";
import { useShellStoreKit, SHELL_STORAGE_KEY } from "../shell-store";

// ── Helpers ───────────────────────────────────────────────────────────────────

/** Seed localStorage with current kit shape (supervisorOpen). */
function seedNew(
  supervisorOpen: string,
  splitPct: number | null = null,
  mobileDrawerOpen = false,
) {
  localStorage.setItem(
    SHELL_STORAGE_KEY,
    JSON.stringify({
      state: { supervisorOpen, splitPct, mobileDrawerOpen },
      version: 1,
    }),
  );
}

/** Seed localStorage with v1 vitalia-specific shape (valeriaOpen) for compat migration tests. */
function seedV1Vitalia(
  valeriaOpen: string,
  valeriaPct: number | null = null,
  mobileDrawerOpen = false,
) {
  localStorage.setItem(
    SHELL_STORAGE_KEY,
    JSON.stringify({
      state: { valeriaOpen, valeriaPct, mobileDrawerOpen },
      version: 1,
    }),
  );
}

/** Seed localStorage with the LEGACY shape (version 0) for migration tests. */
function seedLegacy(
  valeriaState: string,
  shellMode = "agentic",
  mobileDrawerOpen = false,
) {
  localStorage.setItem(
    SHELL_STORAGE_KEY,
    JSON.stringify({
      state: { valeriaState, shellMode, mobileDrawerOpen },
      version: 0,
    }),
  );
}

function clearStorage() {
  localStorage.removeItem(SHELL_STORAGE_KEY);
}

async function rehydrate() {
  await act(async () => {
    await useShellStoreKit.persist.rehydrate();
    await new Promise((r) => setTimeout(r, 0));
  });
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe("shell-store SSR-safe hydration + legacy migration (kit store)", () => {
  let setItemSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    clearStorage();
    useShellStoreKit.setState({
      supervisorOpen: "chat",
      historyOpen: false,
      splitPct: null,
      mobileDrawerOpen: false,
      _hasHydrated: false,
    });
    setItemSpy = vi.spyOn(Storage.prototype, "setItem");
  });

  afterEach(() => {
    vi.restoreAllMocks();
    clearStorage();
  });

  // ── SC-1/SC-5 no-clobber during SSR/pre-hydration ─────────────────────────

  describe("SC-1/SC-5 no-clobber — NO write espurio del default during pre-hydration", () => {
    it("does NOT write to storage while _hasHydrated=false", () => {
      seedNew("closed");
      setItemSpy.mockClear();

      expect(useShellStoreKit.getState()._hasHydrated).toBe(false);

      const writesForKey = setItemSpy.mock.calls.filter(
        ([k]) => k === SHELL_STORAGE_KEY,
      );
      expect(writesForKey).toHaveLength(0);
    });

    it("after rehydrate, supervisorOpen comes from storage (not clobbered to default)", async () => {
      seedNew("closed");

      await rehydrate();

      expect(useShellStoreKit.getState()._hasHydrated).toBe(true);
      expect(useShellStoreKit.getState().supervisorOpen).toBe("closed");
    });

    it("mutations before rehydrate don't persist to storage (NO-OP)", async () => {
      seedNew("closed");
      setItemSpy.mockClear();

      act(() => {
        useShellStoreKit.getState().setSupervisorOpen("chat");
      });

      const writesForKey = setItemSpy.mock.calls.filter(
        ([k]) => k === SHELL_STORAGE_KEY,
      );
      expect(writesForKey).toHaveLength(0);

      // After rehydrate, state comes from localStorage (closed), not the mutation
      await rehydrate();
      expect(useShellStoreKit.getState().supervisorOpen).toBe("closed");
    });

    it("post-hydrate mutation writes to storage (single clean write)", async () => {
      await rehydrate();
      setItemSpy.mockClear();

      act(() => {
        useShellStoreKit.getState().setSupervisorOpen("closed");
      });

      const writesForKey = setItemSpy.mock.calls.filter(
        ([k]) => k === SHELL_STORAGE_KEY,
      );
      expect(writesForKey.length).toBeGreaterThan(0);
    });
  });

  // ── SC-18 legacy migration (v0 → kit) ────────────────────────────────────

  describe("SC-18 legacy migration — old shape maps to new machine", () => {
    it("legacy 'collapsed' → supervisorOpen='closed'", async () => {
      seedLegacy("collapsed");
      await rehydrate();
      expect(useShellStoreKit.getState().supervisorOpen).toBe("closed");
    });

    it("legacy 'rail' → supervisorOpen='chat', historyOpen=false", async () => {
      seedLegacy("rail");
      await rehydrate();
      expect(useShellStoreKit.getState().supervisorOpen).toBe("chat");
      expect(useShellStoreKit.getState().historyOpen).toBe(false);
    });

    it("legacy 'full' → supervisorOpen='chat', historyOpen=false (NO restore history — RN-5)", async () => {
      seedLegacy("full");
      await rehydrate();
      expect(useShellStoreKit.getState().supervisorOpen).toBe("chat");
      // RN-5: NO restaura el historial al migrar de 'full'
      expect(useShellStoreKit.getState().historyOpen).toBe(false);
    });

    it("legacy shellMode is dropped (not present on migrated state)", async () => {
      seedLegacy("full", "web");
      await rehydrate();
      const state = useShellStoreKit.getState() as unknown as Record<string, unknown>;
      expect(state.shellMode).toBeUndefined();
    });

    it("legacy mobileDrawerOpen preserved", async () => {
      seedLegacy("rail", "agentic", true);
      await rehydrate();
      expect(useShellStoreKit.getState().mobileDrawerOpen).toBe(true);
    });
  });

  // ── v1 valeriaOpen field compat migration ─────────────────────────────────

  describe("v1 vitalia field name compat — valeriaOpen maps to supervisorOpen", () => {
    it("v1 valeriaOpen='chat' → supervisorOpen='chat'", async () => {
      seedV1Vitalia("chat");
      await rehydrate();
      expect(useShellStoreKit.getState().supervisorOpen).toBe("chat");
    });

    it("v1 valeriaOpen='closed' → supervisorOpen='closed'", async () => {
      seedV1Vitalia("closed");
      await rehydrate();
      expect(useShellStoreKit.getState().supervisorOpen).toBe("closed");
    });
  });

  // ── SC-18 corrupt / unknown → fallback + console.warn ─────────────────────

  describe("SC-18 corrupt/unknown → fallback {supervisorOpen:'chat', historyOpen:false} + console.warn", () => {
    it("invalid JSON does not throw, falls back to default", async () => {
      localStorage.setItem(SHELL_STORAGE_KEY, "not-valid-json{{{{");
      await expect(rehydrate()).resolves.not.toThrow();
      expect(useShellStoreKit.getState().supervisorOpen).toBe("chat");
      expect(useShellStoreKit.getState().historyOpen).toBe(false);
      expect(useShellStoreKit.getState()._hasHydrated).toBe(true);
    });

    it("unknown legacy valeriaState → fallback chat + console.warn (SC-18)", async () => {
      const warnSpy = vi.spyOn(console, "warn").mockImplementation(() => undefined);
      localStorage.setItem(
        SHELL_STORAGE_KEY,
        JSON.stringify({
          state: { valeriaState: "unknown-state", shellMode: "agentic" },
          version: 0,
        }),
      );

      await rehydrate();

      expect(useShellStoreKit.getState().supervisorOpen).toBe("chat");
      expect(useShellStoreKit.getState().historyOpen).toBe(false);
      expect(warnSpy).toHaveBeenCalled();
    });

    it("unknown new-shape supervisorOpen → fallback chat + console.warn", async () => {
      const warnSpy = vi.spyOn(console, "warn").mockImplementation(() => undefined);
      localStorage.setItem(
        SHELL_STORAGE_KEY,
        JSON.stringify({
          state: { supervisorOpen: "bogus", splitPct: null, mobileDrawerOpen: false },
          version: 1,
        }),
      );

      await rehydrate();

      expect(useShellStoreKit.getState().supervisorOpen).toBe("chat");
      expect(warnSpy).toHaveBeenCalled();
    });
  });

  // ── SC-6 empty_state — first visit ────────────────────────────────────────

  describe("empty_state — first visit without stored preference", () => {
    it("defaults to supervisorOpen='chat' historyOpen=false when no storage entry", async () => {
      await rehydrate();
      const state = useShellStoreKit.getState();
      expect(state.supervisorOpen).toBe("chat");
      expect(state.historyOpen).toBe(false);
    });

    it("_hasHydrated is true after rehydrate with empty storage", async () => {
      await rehydrate();
      expect(useShellStoreKit.getState()._hasHydrated).toBe(true);
    });

    it("mobileDrawerOpen defaults to false (fresh user)", async () => {
      await rehydrate();
      expect(useShellStoreKit.getState().mobileDrawerOpen).toBe(false);
    });
  });

  // ── SsrSafeHydration interface ────────────────────────────────────────────

  describe("SsrSafeHydration interface on shell-store", () => {
    it("exposes _hasHydrated (false initially)", () => {
      expect(useShellStoreKit.getState()._hasHydrated).toBe(false);
    });

    it("exposes setHasHydrated action", () => {
      expect(typeof useShellStoreKit.getState().setHasHydrated).toBe("function");
    });

    it("exposes persist.rehydrate method", () => {
      expect(typeof useShellStoreKit.persist.rehydrate).toBe("function");
    });

    it("partialize excludes _hasHydrated, setters, and historyOpen", () => {
      const partialize = useShellStoreKit.persist.getOptions().partialize;
      if (partialize) {
        const partial = partialize(useShellStoreKit.getState()) as Record<string, unknown>;
        expect(partial).not.toHaveProperty("_hasHydrated");
        expect(partial).not.toHaveProperty("setHasHydrated");
        expect(partial).not.toHaveProperty("setSupervisorOpen");
        expect(partial).not.toHaveProperty("setMobileDrawerOpen");
        // RN-5/RN-11: historyOpen never persisted
        expect(partial).not.toHaveProperty("historyOpen");
      }
    });
  });
});
