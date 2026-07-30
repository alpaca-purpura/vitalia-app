// @luana/hooks — engine-shared. Origin: vitalia-shell-state-persistence / ADR-vitalia-006 (lift 2026-05-29).
/**
 * create-ssr-safe-persisted-store.ts — Factory for SSR-safe Zustand persisted stores.
 * vitalia-shell-state-persistence T-1 · ADR-vitalia-006
 *
 * WHY THIS EXISTS: Zustand persist middleware auto-writes the default value to
 * localStorage during SSR/skeleton/pre-hydration cycles in Next.js App Router,
 * clobbering any previously saved preference on each reload.
 *
 * HOW IT FIXES IT:
 * 1. skipHydration:true — no auto-hydrate on module-eval (server or client).
 * 2. ssrSafeStorage — setItem is a NO-OP while _hasHydrated === false.
 *    getItem/removeItem passthrough so reading from storage still works.
 *    This cuts the spurious write at the root, independent of timing.
 * 3. onRehydrateStorage — flips _hasHydrated = true after client rehydrate.
 *    useStoreHydration(store) triggers rehydrate() once client-side.
 *
 * 4 techniques that FAILED (00-research.md — do NOT repeat):
 * - skipHydration + rehydrate() at module-level (async → reads already-clobbered storage)
 * - skipHydration + rehydrate() in useEffect only (write precedes it; StrictMode 2x)
 * - Guard in ValeriaSidebar D2 effect only (necessary but not sufficient)
 * - Combinations of above + container restart
 *
 * Named exports only — NO default exports (FSD-Lite boundary enforcement).
 * FSD boundary: lib layer — importable by stores/ and features/*\/store/.
 *   NEVER import from components/ or features directly.
 * HIPAA-lite: no-phi-scope — factory handles UI preferences, no PHI.
 * downstream-regression-na: brand-local factory; no cross-brand consumers
 *
 * Promotion candidate: /pm-luana lift to core/@luana/hooks (Next 16 + Zustand 5
 *   persist pattern applies to all future brand frontends — see ADR-vitalia-006 § 5).
 */

// `create` desde zustand/react (no el index `zustand`): turbopack no resuelve el `export *`
// del index (re-export transitivo de named exports) → `create` undefined. El subpath directo
// (con el patch zustand que vuelve relativos sus self-refs) sí resuelve. (HB-78)
import { create } from "zustand/react";
import type { StateCreator } from "zustand";
import {
  persist,
  createJSONStorage,
  type PersistOptions,
  type PersistStorage,
  type StorageValue,
} from "zustand/middleware";

// ── SsrSafeHydration interface ────────────────────────────────────────────────

/**
 * Marker interface added to all SSR-safe persisted stores.
 * - `_hasHydrated`: false until client-side rehydrate completes.
 * - `setHasHydrated`: action called by onRehydrateStorage callback.
 *
 * Every store created with createSsrSafePersistedStore MUST include
 * these fields in its state initializer.
 */
export interface SsrSafeHydration {
  _hasHydrated: boolean;
  setHasHydrated: (v: boolean) => void;
}

// ── Minimal persist API surface exposed by the factory ────────────────────────

interface StorePersistApi<T> {
  rehydrate: () => Promise<void> | void;
  getOptions: () => PersistOptions<T, Partial<T>>;
}

/**
 * A Zustand store created by createSsrSafePersistedStore.
 * Extends the standard hook with .persist for rehydration and .getState/.setState.
 */
export interface SsrSafePersistedStore<T extends SsrSafeHydration> {
  (): T;
  (selector: (state: T) => T): T;
  <U>(selector: (state: T) => U): U;
  getState: () => T;
  setState: (
    stateOrUpdater: Partial<T> | T | ((state: T) => Partial<T> | T),
    replace?: boolean,
  ) => void;
  subscribe: (listener: (state: T, prevState: T) => void) => () => void;
  persist: StorePersistApi<T>;
}

// ── ssrSafeStorage — the key mechanism ───────────────────────────────────────

/**
 * Wraps localStorage (via createJSONStorage) with a setItem NO-OP guard.
 *
 * While getHydrated() === false:
 *   - setItem → NO-OP (spurious default writes are silently dropped)
 *   - getItem → passthrough (reads still work for rehydration)
 *   - removeItem → passthrough (cleanup still works)
 *
 * After getHydrated() === true (i.e. after rehydrate() + onRehydrateStorage):
 *   - All operations passthrough normally.
 *
 * This is the critical piece the 4 failed techniques lacked:
 * they all left setItem active, so the default was written BEFORE
 * rehydrate() could run, regardless of timing or StrictMode.
 */
function ssrSafeStorage<S>(getHydrated: () => boolean): PersistStorage<S> {
  const jsonStorage = createJSONStorage<S>(() => {
    // Safe check for SSR environment where localStorage is not available
    if (typeof window === "undefined") {
      return {
        getItem: (_name: string) => null,
        setItem: (_name: string, _value: string) => undefined,
        removeItem: (_name: string) => undefined,
      } as unknown as Storage;
    }
    return localStorage;
  });

  if (!jsonStorage) {
    // Fallback: no-op storage (safe for SSR build)
    return {
      getItem: () => null,
      setItem: () => undefined,
      removeItem: () => undefined,
    };
  }

  return {
    getItem: (name: string): StorageValue<S> | null | Promise<StorageValue<S> | null> => {
      // Passthrough — reads always work (needed for rehydration)
      const result = jsonStorage.getItem(name);
      if (result instanceof Promise) {
        return result as Promise<StorageValue<S> | null>;
      }
      return result as StorageValue<S> | null;
    },

    setItem: (name: string, value: StorageValue<S>): void => {
      // NO-OP while not hydrated — drops the spurious default write
      if (!getHydrated()) {
        return;
      }
      jsonStorage.setItem(name, value);
    },

    removeItem: (name: string): void => {
      // Passthrough — cleanup should always work
      jsonStorage.removeItem(name);
    },
  };
}

// ── createSsrSafePersistedStore ───────────────────────────────────────────────

/**
 * Factory for SSR-safe Zustand persisted stores.
 *
 * The returned store has the full Zustand API including .persist.rehydrate().
 * Use it exactly like a standard Zustand hook: `const value = useMyStore(s => s.value)`
 *
 * Usage:
 * ```ts
 * export const useMyStore = createSsrSafePersistedStore<MyState>(
 *   (set) => ({
 *     _hasHydrated: false,
 *     setHasHydrated: (v) => set({ _hasHydrated: v }),
 *     value: 'default',
 *     setValue: (v) => set({ value: v }),
 *   }),
 *   {
 *     name: 'my-storage-key',
 *     partialize: (s) => ({ value: s.value }),
 *   },
 * );
 * ```
 *
 * Then call useStoreHydration(useMyStore) from the first client-side component
 * within an ssr:false dynamic chunk.
 *
 * @param initializer - Zustand StateCreator. MUST include _hasHydrated + setHasHydrated.
 * @param options - Zustand PersistOptions (name, partialize, version, etc.).
 *                  Do NOT include `storage` or `skipHydration` — factory handles those.
 */
export function createSsrSafePersistedStore<T extends SsrSafeHydration>(
  initializer: StateCreator<T>,
  options: Omit<PersistOptions<T, Partial<T>>, "storage" | "skipHydration">,
): SsrSafePersistedStore<T> {
  // Stable ref: the storage wrapper reads this on every setItem call.
  const hydrationRef = { hydrated: false };

  const safeStorage = ssrSafeStorage<Partial<T>>(() => hydrationRef.hydrated);

  // Create the store with persist middleware
  // Using `as any` for the persist options because PersistOptions generic constraints
  // on `storage` don't perfectly line up with our wrapper's generic, but the runtime
  // behavior is correct.
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const rawStore = create<T>()(persist(initializer as any, {
    ...options,
    // skipHydration: true — no auto-hydrate on module-eval.
    skipHydration: true,
    // ssrSafeStorage — setItem NO-OP until hydrated
    storage: safeStorage as PersistStorage<Partial<T>>,
    // onRehydrateStorage — flip hydrated flag AFTER rehydrate completes.
    onRehydrateStorage: (state: T) => {
      return (_rehydratedState: T | undefined, error: unknown) => {
        // Flip the local ref so storage writes become active
        hydrationRef.hydrated = true;
        // Update Zustand state flag for consumers and tests
        if (error) {
          state?.setHasHydrated(true);
        } else {
          state?.setHasHydrated(true);
        }
      };
    },
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
  } as any));

  // Cast to our interface type — .persist is added by Zustand's persist middleware at runtime
  const store = rawStore as unknown as SsrSafePersistedStore<T>;

  // Wrap setState to sync the hydrationRef when _hasHydrated is reset to false.
  // This enables test isolation: store.setState({ _hasHydrated: false }) resets both.
  const originalSetState = store.setState.bind(store);
  store.setState = (
    stateOrUpdater: Partial<T> | T | ((state: T) => Partial<T> | T),
    replace?: boolean,
  ): void => {
    originalSetState(stateOrUpdater, replace);
    // Sync hydrationRef when _hasHydrated is explicitly reset to false
    if (
      typeof stateOrUpdater === "object" &&
      stateOrUpdater !== null &&
      "_hasHydrated" in stateOrUpdater &&
      (stateOrUpdater as Partial<T>)._hasHydrated === false
    ) {
      hydrationRef.hydrated = false;
    }
  };

  return store;
}
