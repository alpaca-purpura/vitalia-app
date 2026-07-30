// cap: configuracion.cuenta
// story-origin: vitalia-fase2-config-cuenta
"use client";
/**
 * use-account-form.ts — RHF+Zod form state + use-autosave 600ms for config/cuenta.
 *
 * Autosave lifecycle:
 *   - onChange → scheduleAutosave({ ...changedField }) — debounced 600ms
 *   - coalesces rapid multi-field edits into single PATCH
 *   - NO "Guardar" button (autosave non-negotiable per form-runtime-array.md)
 *
 * Status exposed to views for FloatingAutosaveIndicator.
 *
 * T-1 vitalia-fase2-config-cuenta
 * spec_anchor: 03-arch.md § 5 (client-side forms) + ADR-vitalia-004 § 3.5
 * downstream-regression-na: brand-local vitalia FE hook; no cross-brand consumers
 */

import { useCallback } from "react";
import { useAutosave } from "@/hooks/use-autosave";
import type { ClinicAccountDTO, ClinicAccountPatchDTO } from "../types/cuenta.types";

export interface UseAccountFormOptions {
  /** Initial data from React Query (SSR hydration or first load). */
  initialData: ClinicAccountDTO | null | undefined;
  /** Save function — receives partial patch payload, returns updated account. */
  saveFn: (payload: ClinicAccountPatchDTO) => Promise<ClinicAccountDTO>;
  /** Tenant ID for React Query key scoping. */
  tenantId: string;
  /** Debounce delay (default 600ms per spec). */
  debounceMs?: number;
}

export interface UseAccountFormReturn {
  /** Schedule a debounced autosave with given partial payload. */
  scheduleAutosave: (payload: ClinicAccountPatchDTO) => void;
  /** Flush pending autosave immediately (e.g., on blur / tab switch). */
  flushAutosave: () => Promise<void>;
  /** Current autosave status for FloatingAutosaveIndicator. */
  autosaveStatus: "idle" | "saving" | "saved" | "error";
}

/**
 * useAccountForm — RHF-compatible autosave hook for config/cuenta.
 *
 * Note: intentionally NOT wrapping useForm (views manage their own RHF instance).
 * This hook is responsible for the save lifecycle only (debounce + status).
 * Views receive `scheduleAutosave` as an onChange callback.
 */
export function useAccountForm({
  saveFn,
  debounceMs = 600,
}: UseAccountFormOptions): UseAccountFormReturn {
  const {
    schedule,
    flush,
    status: autosaveStatus,
  } = useAutosave<ClinicAccountPatchDTO>({ saveFn, debounceMs });

  const scheduleAutosave = useCallback(
    (payload: ClinicAccountPatchDTO) => {
      schedule(payload);
    },
    [schedule],
  );

  const flushAutosave = useCallback(async () => {
    await flush();
  }, [flush]);

  return {
    scheduleAutosave,
    flushAutosave,
    autosaveStatus,
  };
}
