// cap: scheduling.mateo-agenda
// story-origin: vitalia-shell-state-persistence
/**
 * agenda-stores-hydration.test.ts — SSR-safe hydration smoke tests for
 * agenda-store (useDrawerStore) + agenda-filters-store (useFiltersStore).
 * vitalia-shell-state-persistence T-3 · ADR-vitalia-006
 *
 * Smoke: factory applied, no clobber.
 *
 * Tests verify:
 * - Both stores use createSsrSafePersistedStore (expose _hasHydrated + setHasHydrated + persist.rehydrate)
 * - setItem NO-OP while _hasHydrated === false
 * - After rehydrate(), stored values restored (drawerWidth, lastView)
 * - partialize excludes _hasHydrated / setHasHydrated / setters
 * - partialize includes only the persisted fields
 * - Corrupt localStorage falls back to defaults without throw
 *
 * Pattern mirrors shell-store-hydration.test.ts (T-1 reference pattern).
 *
 * Named export (no default export) per FSD-Lite enforce.
 * downstream-regression-na: brand-local store test; no cross-brand consumers
 */

import { describe, it, expect, beforeEach, vi, afterEach } from "vitest";
import { act } from "@testing-library/react";
import {
  useDrawerStore,
  DRAWER_WIDTH_DEFAULT,
  DRAWER_WIDTH_MIN,
  DRAWER_WIDTH_MAX,
} from "../agenda-store";
import { useFiltersStore } from "../agenda-filters-store";

// ── Constants (match internal storage keys) ────────────────────────────────────

const DRAWER_WIDTH_STORAGE_KEY = "vitalia.agenda.drawerWidth";
const LAST_VIEW_STORAGE_KEY = "vitalia.agenda.lastView";

// ── Helpers ───────────────────────────────────────────────────────────────────

function clearAllStorage() {
  localStorage.removeItem(DRAWER_WIDTH_STORAGE_KEY);
  localStorage.removeItem(LAST_VIEW_STORAGE_KEY);
}

// ── useDrawerStore hydration tests ────────────────────────────────────────────

describe("useDrawerStore SSR-safe hydration (T-3 smoke)", () => {
  let setItemSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    clearAllStorage();
    // Reset store to initial state + disable hydration flag
    useDrawerStore.setState({
      selectedSlotId: null,
      drawerOpen: false,
      drawerWidth: DRAWER_WIDTH_DEFAULT,
      staleDetected: false,
      _hasHydrated: false,
    });
    setItemSpy = vi.spyOn(Storage.prototype, "setItem");
  });

  afterEach(() => {
    vi.restoreAllMocks();
    clearAllStorage();
  });

  // ── SsrSafeHydration interface compliance ──────────────────────────────────

  describe("SsrSafeHydration interface", () => {
    it("exposes _hasHydrated (false initially)", () => {
      expect(useDrawerStore.getState()._hasHydrated).toBe(false);
    });

    it("exposes setHasHydrated action", () => {
      expect(typeof useDrawerStore.getState().setHasHydrated).toBe("function");
    });

    it("exposes persist.rehydrate method", () => {
      expect(typeof useDrawerStore.persist.rehydrate).toBe("function");
    });
  });

  // ── setItem NO-OP pre-hydration ────────────────────────────────────────────

  describe("setItem NO-OP pre-hydration — factory applied", () => {
    it("does NOT write to storage while _hasHydrated=false", async () => {
      // Seed with non-default drawerWidth
      localStorage.setItem(
        DRAWER_WIDTH_STORAGE_KEY,
        JSON.stringify({ state: { drawerWidth: 600 }, version: 0 }),
      );
      setItemSpy.mockClear();

      expect(useDrawerStore.getState()._hasHydrated).toBe(false);

      // Simulate pre-hydration state change (like a component setting width)
      act(() => {
        useDrawerStore.getState().setDrawerWidth(500);
      });

      const writesForKey = setItemSpy.mock.calls.filter(
        ([k]) => k === DRAWER_WIDTH_STORAGE_KEY,
      );
      expect(writesForKey).toHaveLength(0);
    });

    it("after rehydrate, drawerWidth is restored from storage (not clobbered to default)", async () => {
      // Seed with a non-default width (600px)
      localStorage.setItem(
        DRAWER_WIDTH_STORAGE_KEY,
        JSON.stringify({ state: { drawerWidth: 600 }, version: 0 }),
      );

      await act(async () => {
        useDrawerStore.persist.rehydrate();
        await new Promise((r) => setTimeout(r, 0));
      });

      expect(useDrawerStore.getState()._hasHydrated).toBe(true);
      expect(useDrawerStore.getState().drawerWidth).toBe(600);
    });

    it("pre-hydration setDrawerWidth does NOT persist to storage", async () => {
      localStorage.setItem(
        DRAWER_WIDTH_STORAGE_KEY,
        JSON.stringify({ state: { drawerWidth: 600 }, version: 0 }),
      );
      setItemSpy.mockClear();

      // Pre-hydration mutation
      act(() => {
        useDrawerStore.getState().setDrawerWidth(DRAWER_WIDTH_MIN);
      });

      // Must NOT have written to storage (NO-OP)
      const writesForKey = setItemSpy.mock.calls.filter(
        ([k]) => k === DRAWER_WIDTH_STORAGE_KEY,
      );
      expect(writesForKey).toHaveLength(0);

      // After rehydrate, state comes from localStorage (600), not pre-hydration mutation
      await act(async () => {
        useDrawerStore.persist.rehydrate();
        await new Promise((r) => setTimeout(r, 0));
      });

      expect(useDrawerStore.getState().drawerWidth).toBe(600);
    });
  });

  // ── Post-hydration writes work ─────────────────────────────────────────────

  describe("post-hydration writes work normally", () => {
    it("after rehydrate, setDrawerWidth writes to storage", async () => {
      await act(async () => {
        useDrawerStore.persist.rehydrate();
        await new Promise((r) => setTimeout(r, 0));
      });

      setItemSpy.mockClear();

      act(() => {
        useDrawerStore.getState().setDrawerWidth(550);
      });

      const writesForKey = setItemSpy.mock.calls.filter(
        ([k]) => k === DRAWER_WIDTH_STORAGE_KEY,
      );
      expect(writesForKey.length).toBeGreaterThan(0);
    });

    it("_hasHydrated=true after rehydrate with empty storage", async () => {
      await act(async () => {
        useDrawerStore.persist.rehydrate();
        await new Promise((r) => setTimeout(r, 0));
      });

      expect(useDrawerStore.getState()._hasHydrated).toBe(true);
    });
  });

  // ── partialize compliance ──────────────────────────────────────────────────

  describe("partialize compliance", () => {
    it("partialize excludes _hasHydrated and setHasHydrated", () => {
      const partialize = useDrawerStore.persist.getOptions().partialize;
      if (partialize) {
        const partial = partialize(useDrawerStore.getState());
        expect(partial).not.toHaveProperty("_hasHydrated");
        expect(partial).not.toHaveProperty("setHasHydrated");
      }
    });

    it("partialize includes drawerWidth (the only persisted field)", () => {
      const partialize = useDrawerStore.persist.getOptions().partialize;
      if (partialize) {
        const partial = partialize(useDrawerStore.getState());
        expect(partial).toHaveProperty("drawerWidth");
      }
    });

    it("partialize excludes session-only fields (selectedSlotId, drawerOpen, staleDetected)", () => {
      const partialize = useDrawerStore.persist.getOptions().partialize;
      if (partialize) {
        const partial = partialize(useDrawerStore.getState());
        expect(partial).not.toHaveProperty("selectedSlotId");
        expect(partial).not.toHaveProperty("drawerOpen");
        expect(partial).not.toHaveProperty("staleDetected");
      }
    });

    it("partialize excludes setters", () => {
      const partialize = useDrawerStore.persist.getOptions().partialize;
      if (partialize) {
        const partial = partialize(useDrawerStore.getState());
        expect(partial).not.toHaveProperty("openDrawer");
        expect(partial).not.toHaveProperty("closeDrawer");
        expect(partial).not.toHaveProperty("toggleDrawer");
        expect(partial).not.toHaveProperty("setDrawerWidth");
        expect(partial).not.toHaveProperty("setStaleDetected");
      }
    });
  });

  // ── Corrupt localStorage fallback ──────────────────────────────────────────

  describe("corrupt localStorage fallback", () => {
    it("handles invalid JSON without throwing", async () => {
      localStorage.setItem(DRAWER_WIDTH_STORAGE_KEY, "not-valid-json");

      await expect(
        act(async () => {
          useDrawerStore.persist.rehydrate();
          await new Promise((r) => setTimeout(r, 0));
        }),
      ).resolves.not.toThrow();
    });

    it("falls back to default drawerWidth when localStorage is corrupt", async () => {
      localStorage.setItem(DRAWER_WIDTH_STORAGE_KEY, "{invalid}");

      await act(async () => {
        useDrawerStore.persist.rehydrate();
        await new Promise((r) => setTimeout(r, 0));
      });

      expect(useDrawerStore.getState().drawerWidth).toBe(DRAWER_WIDTH_DEFAULT);
    });

    it("_hasHydrated=true even after corrupt JSON", async () => {
      localStorage.setItem(DRAWER_WIDTH_STORAGE_KEY, "bad json");

      await act(async () => {
        useDrawerStore.persist.rehydrate();
        await new Promise((r) => setTimeout(r, 0));
      });

      expect(useDrawerStore.getState()._hasHydrated).toBe(true);
    });
  });

  // ── drawerWidth constraints preserved ────────────────────────────────────────

  describe("drawerWidth constraints preserved post-migration", () => {
    it("drawerWidth defaults to DRAWER_WIDTH_DEFAULT (520)", () => {
      expect(useDrawerStore.getState().drawerWidth).toBe(DRAWER_WIDTH_DEFAULT);
    });

    it("setDrawerWidth is clamped to [DRAWER_WIDTH_MIN, DRAWER_WIDTH_MAX]", async () => {
      // Hydrate first so writes work
      await act(async () => {
        useDrawerStore.persist.rehydrate();
        await new Promise((r) => setTimeout(r, 0));
      });

      act(() => { useDrawerStore.getState().setDrawerWidth(100); });
      expect(useDrawerStore.getState().drawerWidth).toBe(DRAWER_WIDTH_MIN);

      act(() => { useDrawerStore.getState().setDrawerWidth(9999); });
      expect(useDrawerStore.getState().drawerWidth).toBe(DRAWER_WIDTH_MAX);
    });
  });
});

// ── useFiltersStore hydration tests ───────────────────────────────────────────

describe("useFiltersStore SSR-safe hydration (T-3 smoke)", () => {
  let setItemSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    clearAllStorage();
    // Reset store to initial state + disable hydration flag
    useFiltersStore.setState({
      activePreset: null,
      lastView: "semana",
      _hasHydrated: false,
    });
    setItemSpy = vi.spyOn(Storage.prototype, "setItem");
  });

  afterEach(() => {
    vi.restoreAllMocks();
    clearAllStorage();
  });

  // ── SsrSafeHydration interface compliance ──────────────────────────────────

  describe("SsrSafeHydration interface", () => {
    it("exposes _hasHydrated (false initially)", () => {
      expect(useFiltersStore.getState()._hasHydrated).toBe(false);
    });

    it("exposes setHasHydrated action", () => {
      expect(typeof useFiltersStore.getState().setHasHydrated).toBe("function");
    });

    it("exposes persist.rehydrate method", () => {
      expect(typeof useFiltersStore.persist.rehydrate).toBe("function");
    });
  });

  // ── setItem NO-OP pre-hydration ────────────────────────────────────────────

  describe("setItem NO-OP pre-hydration — factory applied", () => {
    it("does NOT write to storage while _hasHydrated=false", async () => {
      // Seed with non-default lastView
      localStorage.setItem(
        LAST_VIEW_STORAGE_KEY,
        JSON.stringify({ state: { lastView: "dia" }, version: 0 }),
      );
      setItemSpy.mockClear();

      expect(useFiltersStore.getState()._hasHydrated).toBe(false);

      // Simulate pre-hydration state change
      act(() => {
        useFiltersStore.getState().setLastView("mes");
      });

      const writesForKey = setItemSpy.mock.calls.filter(
        ([k]) => k === LAST_VIEW_STORAGE_KEY,
      );
      expect(writesForKey).toHaveLength(0);
    });

    it("after rehydrate, lastView is restored from storage (not clobbered to default)", async () => {
      // Seed with non-default lastView ('dia')
      localStorage.setItem(
        LAST_VIEW_STORAGE_KEY,
        JSON.stringify({ state: { lastView: "dia" }, version: 0 }),
      );

      await act(async () => {
        useFiltersStore.persist.rehydrate();
        await new Promise((r) => setTimeout(r, 0));
      });

      expect(useFiltersStore.getState()._hasHydrated).toBe(true);
      expect(useFiltersStore.getState().lastView).toBe("dia");
    });

    it("pre-hydration setLastView does NOT persist to storage", async () => {
      localStorage.setItem(
        LAST_VIEW_STORAGE_KEY,
        JSON.stringify({ state: { lastView: "dia" }, version: 0 }),
      );
      setItemSpy.mockClear();

      // Pre-hydration mutation
      act(() => {
        useFiltersStore.getState().setLastView("mes");
      });

      // Must NOT have written to storage (NO-OP)
      const writesForKey = setItemSpy.mock.calls.filter(
        ([k]) => k === LAST_VIEW_STORAGE_KEY,
      );
      expect(writesForKey).toHaveLength(0);

      // After rehydrate, state comes from localStorage ('dia'), not pre-hydration mutation
      await act(async () => {
        useFiltersStore.persist.rehydrate();
        await new Promise((r) => setTimeout(r, 0));
      });

      expect(useFiltersStore.getState().lastView).toBe("dia");
    });
  });

  // ── Post-hydration writes work ─────────────────────────────────────────────

  describe("post-hydration writes work normally", () => {
    it("after rehydrate, setLastView writes to storage", async () => {
      await act(async () => {
        useFiltersStore.persist.rehydrate();
        await new Promise((r) => setTimeout(r, 0));
      });

      setItemSpy.mockClear();

      act(() => {
        useFiltersStore.getState().setLastView("mes");
      });

      const writesForKey = setItemSpy.mock.calls.filter(
        ([k]) => k === LAST_VIEW_STORAGE_KEY,
      );
      expect(writesForKey.length).toBeGreaterThan(0);
    });

    it("_hasHydrated=true after rehydrate with empty storage", async () => {
      await act(async () => {
        useFiltersStore.persist.rehydrate();
        await new Promise((r) => setTimeout(r, 0));
      });

      expect(useFiltersStore.getState()._hasHydrated).toBe(true);
    });
  });

  // ── partialize compliance ──────────────────────────────────────────────────

  describe("partialize compliance", () => {
    it("partialize excludes _hasHydrated and setHasHydrated", () => {
      const partialize = useFiltersStore.persist.getOptions().partialize;
      if (partialize) {
        const partial = partialize(useFiltersStore.getState());
        expect(partial).not.toHaveProperty("_hasHydrated");
        expect(partial).not.toHaveProperty("setHasHydrated");
      }
    });

    it("partialize includes lastView (the only persisted field)", () => {
      const partialize = useFiltersStore.persist.getOptions().partialize;
      if (partialize) {
        const partial = partialize(useFiltersStore.getState());
        expect(partial).toHaveProperty("lastView");
      }
    });

    it("partialize excludes session-only activePreset", () => {
      const partialize = useFiltersStore.persist.getOptions().partialize;
      if (partialize) {
        const partial = partialize(useFiltersStore.getState());
        expect(partial).not.toHaveProperty("activePreset");
      }
    });

    it("partialize excludes setters", () => {
      const partialize = useFiltersStore.persist.getOptions().partialize;
      if (partialize) {
        const partial = partialize(useFiltersStore.getState());
        expect(partial).not.toHaveProperty("setActivePreset");
        expect(partial).not.toHaveProperty("setLastView");
        expect(partial).not.toHaveProperty("clearFilters");
      }
    });
  });

  // ── Corrupt localStorage fallback ──────────────────────────────────────────

  describe("corrupt localStorage fallback", () => {
    it("handles invalid JSON without throwing", async () => {
      localStorage.setItem(LAST_VIEW_STORAGE_KEY, "not-valid-json");

      await expect(
        act(async () => {
          useFiltersStore.persist.rehydrate();
          await new Promise((r) => setTimeout(r, 0));
        }),
      ).resolves.not.toThrow();
    });

    it("falls back to default lastView='semana' when localStorage is corrupt", async () => {
      localStorage.setItem(LAST_VIEW_STORAGE_KEY, "{bad json}");

      await act(async () => {
        useFiltersStore.persist.rehydrate();
        await new Promise((r) => setTimeout(r, 0));
      });

      expect(useFiltersStore.getState().lastView).toBe("semana");
    });

    it("_hasHydrated=true even after corrupt JSON", async () => {
      localStorage.setItem(LAST_VIEW_STORAGE_KEY, "nope");

      await act(async () => {
        useFiltersStore.persist.rehydrate();
        await new Promise((r) => setTimeout(r, 0));
      });

      expect(useFiltersStore.getState()._hasHydrated).toBe(true);
    });
  });

  // ── Existing behavior preserved ────────────────────────────────────────────

  describe("existing filters behavior preserved post-migration", () => {
    it("lastView defaults to 'semana'", () => {
      expect(useFiltersStore.getState().lastView).toBe("semana");
    });

    it("activePreset defaults to null", () => {
      expect(useFiltersStore.getState().activePreset).toBeNull();
    });

    it("clearFilters sets activePreset=null, preserves lastView", async () => {
      // Hydrate so writes work
      await act(async () => {
        useFiltersStore.persist.rehydrate();
        await new Promise((r) => setTimeout(r, 0));
      });

      act(() => {
        useFiltersStore.getState().setLastView("mes");
        useFiltersStore.getState().setActivePreset("today");
      });

      act(() => {
        useFiltersStore.getState().clearFilters();
      });

      expect(useFiltersStore.getState().activePreset).toBeNull();
      expect(useFiltersStore.getState().lastView).toBe("mes");
    });
  });
});
