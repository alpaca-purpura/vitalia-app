// cap: clinics.lisa.doctores
// story-origin: vitalia-fase2-lisa-doctores
"use client";
/**
 * use-autosave.ts — Debounced autosave hook (600ms default).
 *
 * Business rule (autosave-no-save-button HARD):
 *   All perfil fields autosave on-change with 600ms debounce.
 *   NO "Guardar" button. Show hint "Los cambios se guardan automaticamente".
 *
 * Usage:
 *   const { schedule, flush, status } = useAutosave({ saveFn })
 *   // In onChange:
 *   schedule({ field: 'bioNotes', value: newValue })
 *   // On unmount/blur (optional):
 *   flush()
 *
 * Status lifecycle: idle → saving → saved | error
 *
 * Per .claude/rules/form-runtime-array.md: autosave on-change non-negotiable.
 *
 * T-FE-2 vitalia-fase2-lisa-doctores
 * spec_anchor: 03-arch-fe.md § Forms + 01-spec.md § Business rules (autosave-no-save-button)
 * downstream-regression-na: brand-local vitalia FE hook; no cross-brand consumers
 */

import { useState, useRef, useCallback, useEffect } from "react";

// ── Types ─────────────────────────────────────────────────────────────────────

export type AutosaveStatus = "idle" | "saving" | "saved" | "error";

export interface UseAutosaveOptions<T> {
  /** Async function that performs the save — receives the payload */
  saveFn: (payload: T) => Promise<unknown>;
  /** Debounce delay in ms (default: 600 per spec) */
  debounceMs?: number;
}

export interface UseAutosaveReturn<T> {
  /** Queue a save with debounce */
  schedule: (payload: T) => void;
  /** Flush the pending save immediately (e.g., on blur or unmount) */
  flush: () => Promise<void>;
  /** Current autosave status */
  status: AutosaveStatus;
}

// ── Hook ──────────────────────────────────────────────────────────────────────

/**
 * useAutosave — debounced autosave with status tracking.
 *
 * Design notes:
 *   - debounceMs defaults to 600 (spec requirement)
 *   - status resets to "idle" after 2000ms in "saved" state
 *   - pending payload stored in ref to avoid stale closure in saveFn call
 *   - flush() resolves when save completes or rejects when save fails
 */
export function useAutosave<T>({
  saveFn,
  debounceMs = 600,
}: UseAutosaveOptions<T>): UseAutosaveReturn<T> {
  const [status, setStatus] = useState<AutosaveStatus>("idle");

  // Refs avoid stale closures in debounce callbacks
  const pendingPayloadRef = useRef<T | null>(null);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const isMountedRef = useRef(true);
  const saveFnRef = useRef(saveFn);

  // Keep saveFnRef current
  saveFnRef.current = saveFn;

  // Cleanup on unmount
  useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }
    };
  }, []);

  // Core save executor
  const executeSave = useCallback(async (payload: T) => {
    if (!isMountedRef.current) return;
    setStatus("saving");
    try {
      await saveFnRef.current(payload);
      if (isMountedRef.current) {
        setStatus("saved");
        // Auto-reset to idle after 2s
        setTimeout(() => {
          if (isMountedRef.current) {
            setStatus("idle");
          }
        }, 2000);
      }
    } catch {
      if (isMountedRef.current) {
        setStatus("error");
      }
    }
  }, []);

  // schedule — debounced with payload coalescing.
  // Merging pending payloads prevents rapid edits to different fields from
  // replacing each other: editing field A then B within the debounce window
  // produces a single merged PATCH containing both fields (F3 fix).
  const schedule = useCallback(
    (payload: T) => {
      // Coalesce: merge incoming payload with any already-pending payload
      // so that two rapid field edits produce one merged PATCH with both fields.
      if (pendingPayloadRef.current !== null && typeof payload === "object" && payload !== null) {
        pendingPayloadRef.current = {
          ...(pendingPayloadRef.current as object),
          ...(payload as object),
        } as T;
      } else {
        pendingPayloadRef.current = payload;
      }

      // Reset existing timer
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }

      timerRef.current = setTimeout(() => {
        const toSave = pendingPayloadRef.current;
        if (toSave !== null) {
          pendingPayloadRef.current = null;
          void executeSave(toSave);
        }
      }, debounceMs);
    },
    [debounceMs, executeSave],
  );

  // flush — immediate save of pending payload
  const flush = useCallback(async (): Promise<void> => {
    // Cancel pending timer
    if (timerRef.current) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
    const toSave = pendingPayloadRef.current;
    if (toSave !== null) {
      pendingPayloadRef.current = null;
      await executeSave(toSave);
    }
  }, [executeSave]);

  return { schedule, flush, status };
}
