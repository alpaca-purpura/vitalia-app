// cap: patients.nps-tracking
// story-origin: TBD
"use client";

/**
 * use-fidelizacion-store — React hook for fidelización ephemeral UI state.
 *
 * Wraps vanilla store with React useSyncExternalStore for reactive updates.
 *
 * downstream-regression-na: brand-local FE hook; no cross-brand consumers
 */

import { useSyncExternalStore, useRef } from "react";
import {
  createFidelizacionStore,
  type FidelizacionStoreState,
  type FidelizacionStoreActions,
} from "../store/fidelizacion-store";

/**
 * Module-level store instance (singleton per app).
 * Lazily initialized.
 */
let storeInstance: ReturnType<typeof createFidelizacionStore> | null = null;

function getStoreInstance() {
  if (!storeInstance) {
    storeInstance = createFidelizacionStore();
  }
  return storeInstance;
}

/**
 * React hook to access fidelización UI state.
 *
 * @returns Full store state + actions
 */
export function useFidelizacionStore(): FidelizacionStoreState &
  FidelizacionStoreActions {
  const store = useRef(getStoreInstance());

  return useSyncExternalStore(
    store.current.subscribe,
    store.current.getState,
    store.current.getState,
  );
}
