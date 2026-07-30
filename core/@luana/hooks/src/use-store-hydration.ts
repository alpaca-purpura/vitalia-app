"use client";
// @luana/hooks — engine-shared. Origin: vitalia-shell-state-persistence / ADR-vitalia-006 (lift 2026-05-29).
/**
 * use-store-hydration.ts — Idempotent client-side rehydration hook.
 * vitalia-shell-state-persistence T-1 · ADR-vitalia-006
 *
 * Triggers store.persist.rehydrate() exactly ONCE per component mount,
 * guarded by a ref to prevent StrictMode double-invoke side effects.
 *
 * Must be called from within an `ssr:false` dynamic chunk (e.g. ShellOrganismLayoutClient),
 * NEVER at module-level and NEVER in the SSR skeleton path.
 *
 * Usage:
 * ```tsx
 * "use client";
 * import { useStoreHydration } from '@luana/hooks';
 * import { useShellStore } from '@/stores/shell-store';
 *
 * export function ShellOrganismLayoutClient() {
 *   useStoreHydration(useShellStore);
 *   // ...
 * }
 * ```
 *
 * StrictMode safety: React 18+ StrictMode double-invokes effects in dev.
 * The ref guard (`hasRehydrated.current`) ensures rehydrate() is called
 * at most once per component instance, regardless of double-invoke.
 *
 * Named export (no default export) per FSD-Lite boundary enforcement.
 * FSD boundary: lib layer — importable by stores/ and features/*\/store/ and components/.
 * HIPAA-lite: no-phi-scope — hook handles UI store rehydration, no PHI.
 * downstream-regression-na: brand-local hook; no cross-brand consumers
 */

import { useEffect, useRef } from "react";

/** Minimal interface for a Zustand persisted store with rehydrate capability. */
export interface RehydratableStore {
  persist: {
    rehydrate: () => void;
  };
}

/**
 * Triggers `store.persist.rehydrate()` exactly once on client mount.
 * Idempotent — safe to call multiple times (ref-guarded).
 * StrictMode-safe — double-invoke does not trigger double rehydrate.
 *
 * @param store - A Zustand persisted store created with createSsrSafePersistedStore.
 */
export function useStoreHydration(store: RehydratableStore): void {
  const hasRehydrated = useRef(false);

  useEffect(() => {
    if (!hasRehydrated.current) {
      hasRehydrated.current = true;
      store.persist.rehydrate();
    }
  }, [store]);
}
