// cap: iam.luana-core-adoption
// story-origin: vitalia-fase1-s3-TBD
/**
 * tenant-store.ts — Zustand SSR-safe store for tenant state with localStorage persistence.
 * F1-S3 vitalia-fase1-tenant-switcher — T-4
 * Migrated to createSsrSafePersistedStore (vitalia-shell-state-persistence T-3).
 *
 * WHY MIGRATED: The raw persist() middleware auto-writes the default value during
 * SSR/skeleton/pre-hydration, potentially clobbering the stored activeTenant on reload.
 * The factory wraps persist with skipHydration:true + setItem NO-OP until client rehydrate.
 * ADR-vitalia-006 documents the pattern (defense-in-depth transversal convention).
 *
 * Persists only `activeTenant` (via partialize) — NOT `availableTenants`.
 * `availableTenants` is refetched fresh on each session via useTenants hook.
 *
 * Storage key: 'vitalia-tenant-state' (TENANT_STORAGE_KEY).
 * Version: 1 (increment for future breaking migrations).
 *
 * partialize strategy:
 * - activeTenant → persisted (user's last selected clinic)
 * - availableTenants → NOT persisted (fetched fresh each session)
 * - _hasHydrated → NOT persisted (transient hydration flag)
 * - setHasHydrated → NOT persisted (recreated on hydration)
 * - setters → NOT persisted (recreated on hydration)
 *
 * Cross-user isolation: useSignOutCleanup watches Clerk isSignedIn flip
 * and calls clearStore() + localStorage.removeItem(TENANT_STORAGE_KEY).
 *
 * REHYDRATION: call useStoreHydration(useTenantStore) from the first client-side
 * component that consumes this store (within an ssr:false dynamic chunk).
 *
 * Named export (no default export) per FSD-Lite enforce.
 * HIPAA-lite: no-phi-scope — tenant name/city are business entities, not PHI.
 * No Clerk Organizations used — per MEMORY.md::no-clerk-organizations 2026-05-20.
 *
 * downstream-regression-na: brand-local store; no cross-brand consumers
 */

import {
  createSsrSafePersistedStore,
  type SsrSafeHydration,
} from "@luana/hooks/create-ssr-safe-persisted-store";
import type { TenantStore, Tenant } from "@/components/shared/shell-organism/types";

/** localStorage key for tenant state persistence */
export const TENANT_STORAGE_KEY = "vitalia-tenant-state" as const;

/** Persisted slice — only activeTenant */
type PersistedState = {
  activeTenant: Tenant | null;
};

/** Full store state — extends SsrSafeHydration for factory compliance */
type TenantStoreWithHydration = TenantStore & SsrSafeHydration;

export const useTenantStore = createSsrSafePersistedStore<TenantStoreWithHydration>(
  (set, get) => ({
    // ── SsrSafeHydration ────────────────────────────────────────────────────
    _hasHydrated: false,
    setHasHydrated: (v: boolean) => set({ _hasHydrated: v }),

    // ── State ─────────────────────────────────────────────────────────────
    activeTenant: null,
    availableTenants: [],

    // ── Actions ───────────────────────────────────────────────────────────

    setActiveTenant: (tenant: Tenant) => {
      set({ activeTenant: tenant });
    },

    setAvailableTenants: (tenants: ReadonlyArray<Tenant>) => {
      set({ availableTenants: tenants });
      // Auto-pick first tenant when no active tenant is set
      const current = get().activeTenant;
      if (!current && tenants.length > 0) {
        set({ activeTenant: tenants[0] });
      }
    },

    switchTenant: (id: string) => {
      const target = get().availableTenants.find((t) => t.id === id) ?? null;
      if (!target) return null;
      set({ activeTenant: target });
      return target;
    },

    clearStore: () => {
      set({ activeTenant: null, availableTenants: [] });
    },
  }),
  {
    name: TENANT_STORAGE_KEY,
    // Only persist activeTenant — availableTenants is fetched fresh each session
    // _hasHydrated and setters are intentionally excluded from persist
    partialize: (state): PersistedState => ({
      activeTenant: state.activeTenant,
    }),
    version: 1,
  },
);
