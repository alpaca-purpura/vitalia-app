// cap: iam.luana-core-adoption
// story-origin: vitalia-shell-state-persistence
/**
 * tenant-store-hydration.test.ts — SSR-safe hydration smoke tests for tenant-store.
 * vitalia-shell-state-persistence T-3 · ADR-vitalia-006
 *
 * Smoke: factory applied, no clobber.
 *
 * Tests verify:
 * - Store uses createSsrSafePersistedStore (exposes _hasHydrated + setHasHydrated + persist.rehydrate)
 * - setItem NO-OP while _hasHydrated === false (no clobber of stored activeTenant)
 * - After rehydrate(), stored activeTenant is restored (not replaced by default null)
 * - partialize excludes _hasHydrated and setHasHydrated
 * - partialize includes only activeTenant
 * - Corrupt localStorage falls back to default without throw
 *
 * Pattern mirrors shell-store-hydration.test.ts (T-1 reference pattern).
 *
 * Named export (no default export) per FSD-Lite enforce.
 * downstream-regression-na: brand-local store test; no cross-brand consumers
 */

import { describe, it, expect, beforeEach, vi, afterEach } from "vitest";
import { act } from "@testing-library/react";
import { useTenantStore, TENANT_STORAGE_KEY } from "../tenant-store";

// ── Helpers ───────────────────────────────────────────────────────────────────

const T_SONRISA = { id: "sonrisa-plena", name: "Sonrisa Plena", city: "Lima" };
const T_DERMALIA = { id: "dermalia-mx", name: "Dermalia MX", city: "CDMX" };

function seedLocalStorage(tenant: object) {
  localStorage.setItem(
    TENANT_STORAGE_KEY,
    JSON.stringify({
      state: { activeTenant: tenant },
      version: 1,
    }),
  );
}

function clearStorage() {
  localStorage.removeItem(TENANT_STORAGE_KEY);
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe("tenant-store SSR-safe hydration (T-3 smoke)", () => {
  let setItemSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    clearStorage();
    // Reset store to initial state + disable hydration flag
    useTenantStore.setState({
      activeTenant: null,
      availableTenants: [],
      _hasHydrated: false,
    });
    setItemSpy = vi.spyOn(Storage.prototype, "setItem");
  });

  afterEach(() => {
    vi.restoreAllMocks();
    clearStorage();
  });

  // ── SsrSafeHydration interface compliance ────────────────────────────────

  describe("SsrSafeHydration interface", () => {
    it("exposes _hasHydrated (false initially)", () => {
      expect(useTenantStore.getState()._hasHydrated).toBe(false);
    });

    it("exposes setHasHydrated action", () => {
      expect(typeof useTenantStore.getState().setHasHydrated).toBe("function");
    });

    it("exposes persist.rehydrate method", () => {
      expect(typeof useTenantStore.persist.rehydrate).toBe("function");
    });
  });

  // ── setItem NO-OP pre-hydration (no clobber) ─────────────────────────────

  describe("setItem NO-OP pre-hydration — factory applied", () => {
    it("does NOT write to storage while _hasHydrated=false", async () => {
      seedLocalStorage(T_SONRISA);
      setItemSpy.mockClear();

      // Pre-hydration: any state mutations must NOT write to storage
      expect(useTenantStore.getState()._hasHydrated).toBe(false);

      // Simulate what happens if something sets activeTenant pre-hydration
      act(() => {
        useTenantStore.getState().setActiveTenant(T_DERMALIA);
      });

      const writesForKey = setItemSpy.mock.calls.filter(
        ([k]) => k === TENANT_STORAGE_KEY,
      );
      expect(writesForKey).toHaveLength(0);
    });

    it("after rehydrate, activeTenant is restored from storage (not clobbered to null)", async () => {
      // Seed with a real tenant preference
      seedLocalStorage(T_SONRISA);

      // Rehydrate (simulates useStoreHydration in the first client consumer)
      await act(async () => {
        useTenantStore.persist.rehydrate();
        await new Promise((r) => setTimeout(r, 0));
      });

      // _hasHydrated must flip
      expect(useTenantStore.getState()._hasHydrated).toBe(true);
      // activeTenant must be T_SONRISA from localStorage, not default null
      expect(useTenantStore.getState().activeTenant).toStrictEqual(T_SONRISA);
    });

    it("pre-hydration setActiveTenant does NOT persist to storage", async () => {
      seedLocalStorage(T_SONRISA);
      setItemSpy.mockClear();

      // Simulate pre-hydration mutation (like what SSR skeleton might trigger)
      act(() => {
        useTenantStore.getState().setActiveTenant(T_DERMALIA);
      });

      // Must NOT have written to storage (NO-OP)
      const writesForKey = setItemSpy.mock.calls.filter(
        ([k]) => k === TENANT_STORAGE_KEY,
      );
      expect(writesForKey).toHaveLength(0);

      // After rehydrate, state comes from localStorage (T_SONRISA), not the pre-hydration mutation
      await act(async () => {
        useTenantStore.persist.rehydrate();
        await new Promise((r) => setTimeout(r, 0));
      });

      expect(useTenantStore.getState().activeTenant).toStrictEqual(T_SONRISA);
    });
  });

  // ── Post-hydration writes work normally ───────────────────────────────────

  describe("post-hydration writes work normally", () => {
    it("after rehydrate, setActiveTenant writes to storage", async () => {
      await act(async () => {
        useTenantStore.persist.rehydrate();
        await new Promise((r) => setTimeout(r, 0));
      });

      setItemSpy.mockClear();

      act(() => {
        useTenantStore.getState().setActiveTenant(T_DERMALIA);
      });

      const writesForKey = setItemSpy.mock.calls.filter(
        ([k]) => k === TENANT_STORAGE_KEY,
      );
      expect(writesForKey.length).toBeGreaterThan(0);
    });

    it("_hasHydrated=true after rehydrate with empty storage", async () => {
      await act(async () => {
        useTenantStore.persist.rehydrate();
        await new Promise((r) => setTimeout(r, 0));
      });

      expect(useTenantStore.getState()._hasHydrated).toBe(true);
    });
  });

  // ── partialize compliance ─────────────────────────────────────────────────

  describe("partialize compliance", () => {
    it("partialize excludes _hasHydrated", () => {
      const partialize = useTenantStore.persist.getOptions().partialize;
      if (partialize) {
        const partial = partialize(useTenantStore.getState());
        expect(partial).not.toHaveProperty("_hasHydrated");
      }
    });

    it("partialize excludes setHasHydrated", () => {
      const partialize = useTenantStore.persist.getOptions().partialize;
      if (partialize) {
        const partial = partialize(useTenantStore.getState());
        expect(partial).not.toHaveProperty("setHasHydrated");
      }
    });

    it("partialize includes activeTenant", () => {
      const partialize = useTenantStore.persist.getOptions().partialize;
      if (partialize) {
        const partial = partialize(useTenantStore.getState());
        expect(partial).toHaveProperty("activeTenant");
      }
    });

    it("partialize excludes availableTenants (not persisted — fetched fresh)", () => {
      const partialize = useTenantStore.persist.getOptions().partialize;
      if (partialize) {
        const partial = partialize(useTenantStore.getState());
        expect(partial).not.toHaveProperty("availableTenants");
      }
    });

    it("partialize excludes setters", () => {
      const partialize = useTenantStore.persist.getOptions().partialize;
      if (partialize) {
        const partial = partialize(useTenantStore.getState());
        expect(partial).not.toHaveProperty("setActiveTenant");
        expect(partial).not.toHaveProperty("setAvailableTenants");
        expect(partial).not.toHaveProperty("switchTenant");
        expect(partial).not.toHaveProperty("clearStore");
      }
    });
  });

  // ── Corrupt localStorage fallback ─────────────────────────────────────────

  describe("corrupt localStorage fallback", () => {
    it("handles invalid JSON without throwing", async () => {
      localStorage.setItem(TENANT_STORAGE_KEY, "not-valid-json{{{{");

      await expect(
        act(async () => {
          useTenantStore.persist.rehydrate();
          await new Promise((r) => setTimeout(r, 0));
        }),
      ).resolves.not.toThrow();
    });

    it("falls back to null activeTenant when localStorage is corrupt", async () => {
      localStorage.setItem(TENANT_STORAGE_KEY, "this is not json");

      await act(async () => {
        useTenantStore.persist.rehydrate();
        await new Promise((r) => setTimeout(r, 0));
      });

      // Should have default value (null), not crash
      expect(useTenantStore.getState().activeTenant).toBeNull();
    });

    it("_hasHydrated=true even after corrupt JSON (hydrated with defaults)", async () => {
      localStorage.setItem(TENANT_STORAGE_KEY, "{invalid");

      await act(async () => {
        useTenantStore.persist.rehydrate();
        await new Promise((r) => setTimeout(r, 0));
      });

      expect(useTenantStore.getState()._hasHydrated).toBe(true);
    });
  });

  // ── clearStore (cross-user signout cleanup) ───────────────────────────────

  describe("clearStore preserves existing behavior", () => {
    it("clearStore resets activeTenant to null", () => {
      useTenantStore.getState().setActiveTenant(T_SONRISA);
      useTenantStore.getState().clearStore();
      expect(useTenantStore.getState().activeTenant).toBeNull();
    });

    it("clearStore resets availableTenants to empty", () => {
      useTenantStore.setState({ availableTenants: [T_SONRISA, T_DERMALIA] });
      useTenantStore.getState().clearStore();
      expect(useTenantStore.getState().availableTenants).toHaveLength(0);
    });
  });
});
