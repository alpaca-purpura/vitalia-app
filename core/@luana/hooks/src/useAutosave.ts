// cap: platform.autosave-primitive-platform
// story-origin: build-autosave-primitive-luana
"use client";

/**
 * useAutosave.ts — Primitiva de autoguardado compartida (@luana/hooks).
 *
 * Generaliza el patrón de los hooks vitalia use{Identity,Personality,Contact,Visuals}Autosave
 * + la robustez getTokenReady de VozTonoView.tsx.
 *
 * Características:
 *   - getTokenReady(): espera hasta authReadyAttempts × 200ms a que el token no sea null.
 *     (robustez ante la ventana de Clerk donde isSignedIn=true pero getToken()→null transitorio)
 *   - debounce default 2000ms; scheduleSave cancela el timer previo (last-wins).
 *   - Máquina de estados: idle → dirty → saving → saved | error.
 *   - savedAt se actualiza en cada guardado exitoso.
 *   - onSaved / onError callbacks opcionales.
 *   - telemetry opt-in: { type: "saved"|"error", durationMs }.
 *   - retry() re-dispara el último conjunto de valores fallido.
 *   - Cleanup en unmount: cancela timer + guard setState post-unmount.
 *
 * NO importa @clerk/* — auth desacoplado vía getToken inyectado.
 * NO usa @tanstack/react-query — estado manejado con useRef + useState (sin dep pesada).
 *
 * ADR-012 — build-autosave-primitive-luana T-1
 */

import { useCallback, useEffect, useRef, useState } from "react";

// ── Tipos exportados (re-exportados también desde @luana/schemas) ─────────────

/**
 * Estado observable del ciclo de autoguardado.
 * @public
 */
export type AutosaveStatus = "idle" | "dirty" | "saving" | "saved" | "error";

/**
 * Opciones de configuración para useAutosave<TValues>.
 * @public
 */
export interface UseAutosaveOptions<TValues> {
  /** Función de mutación real — inyectada por el consumer. */
  save: (values: TValues, ctx: { token: string }) => Promise<unknown>;
  /** Proveedor de token — inyectado (desacopla Clerk u otro auth provider). */
  getToken: () => Promise<string | null>;
  /** Callback on success — ej. invalidar una React Query key. */
  onSaved?: () => void;
  /** Callback on error. */
  onError?: (err: unknown) => void;
  /**
   * Ventana de debounce en ms.
   * @default 2000
   */
  debounceMs?: number;
  /**
   * Si `true`, las llamadas sucesivas a scheduleSave MEZCLAN sus payloads
   * (shallow merge sobre objetos) en lugar de descartar el anterior (last-wins).
   * Útil cuando cada edición envía un patch parcial distinto y todos deben
   * llegar al backend en un único guardado.
   *
   * Requiere que TValues sea un objeto plano para que el merge tenga sentido;
   * con primitivos el merge degrada a last-wins (el último valor gana).
   *
   * @default false
   */
  coalesce?: boolean;
  /** Telemetría opt-in. */
  telemetry?: (event: { type: "saved" | "error"; durationMs: number }) => void;
  /**
   * Máximo intentos esperando token no-null (× 200ms).
   * @default 10
   */
  authReadyAttempts?: number;
}

/**
 * Interfaz retornada por useAutosave<TValues>.
 * @public
 */
export interface UseAutosaveReturn<TValues> {
  status: AutosaveStatus;
  savedAt: Date | null;
  scheduleSave: (values: TValues) => void;
  cancel: () => void;
  retry: () => void;
  /**
   * Cancela el debounce pendiente y guarda inmediatamente los valores
   * acumulados (el merge si coalesce, o el último si last-wins).
   * No-op si no hay nada pendiente.
   * @returns Promesa que resuelve cuando el guardado termina.
   */
  flush: () => Promise<void>;
}

// ── Constantes ────────────────────────────────────────────────────────────────

const DEFAULT_DEBOUNCE_MS = 2000;
const DEFAULT_AUTH_READY_ATTEMPTS = 10;
const AUTH_RETRY_INTERVAL_MS = 200;

// ── Hook ──────────────────────────────────────────────────────────────────────

/**
 * Hook de autoguardado compartido.
 *
 * @example
 * ```ts
 * const { status, scheduleSave, savedAt } = useAutosave({
 *   save: (values, { token }) => api.patch('/resource', values, token),
 *   getToken: () => clerk.getToken(),
 *   onSaved: () => queryClient.invalidateQueries({ queryKey: ['resource'] }),
 * });
 * ```
 */
export function useAutosave<TValues>(
  options: UseAutosaveOptions<TValues>,
): UseAutosaveReturn<TValues> {
  const {
    save,
    getToken,
    onSaved,
    onError,
    debounceMs = DEFAULT_DEBOUNCE_MS,
    coalesce = false,
    telemetry,
    authReadyAttempts = DEFAULT_AUTH_READY_ATTEMPTS,
  } = options;

  // ── Refs ────────────────────────────────────────────────────────────────────
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const isMountedRef = useRef(true);
  // lastValuesRef: snapshot que se va a guardar cuando dispara el debounce.
  //   - coalesce=false → último valor (last-wins, comportamiento histórico).
  //   - coalesce=true  → merge acumulado de todos los scheduleSave pendientes.
  const lastValuesRef = useRef<TValues | null>(null);
  const isSavingRef = useRef(false);
  const coalesceRef = useRef(coalesce);
  coalesceRef.current = coalesce;

  // Stable refs for callbacks to avoid stale-closure issues in the debounced fn
  const saveRef = useRef(save);
  const getTokenRef = useRef(getToken);
  const onSavedRef = useRef(onSaved);
  const onErrorRef = useRef(onError);
  const telemetryRef = useRef(telemetry);
  const authReadyAttemptsRef = useRef(authReadyAttempts);

  // Keep refs fresh on every render
  saveRef.current = save;
  getTokenRef.current = getToken;
  onSavedRef.current = onSaved;
  onErrorRef.current = onError;
  telemetryRef.current = telemetry;
  authReadyAttemptsRef.current = authReadyAttempts;

  // ── State ────────────────────────────────────────────────────────────────────
  const [status, setStatus] = useState<AutosaveStatus>("idle");
  const [savedAt, setSavedAt] = useState<Date | null>(null);

  // ── Unmount guard ────────────────────────────────────────────────────────────
  useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
    };
  }, []);

  // ── getTokenReady ─────────────────────────────────────────────────────────
  // Waits up to authReadyAttempts × 200ms for a non-null token.
  // Prevents permanent "Not authenticated" when Clerk resolves the token
  // with a brief delay after isSignedIn becomes true.
  const getTokenReady = useCallback(async (): Promise<string> => {
    const attempts = authReadyAttemptsRef.current;
    for (let i = 0; i < attempts; i += 1) {
      const token = await getTokenRef.current();
      if (token) return token;
      await new Promise<void>((resolve) =>
        setTimeout(resolve, AUTH_RETRY_INTERVAL_MS),
      );
    }
    throw new Error("Not authenticated");
  }, []); // deps intentionally empty — uses stable refs

  // ── executeSave ───────────────────────────────────────────────────────────
  const executeSave = useCallback(
    async (values: TValues): Promise<void> => {
      if (!isMountedRef.current) return;
      if (isSavingRef.current) return; // guard concurrent saves

      isSavingRef.current = true;

      if (isMountedRef.current) {
        setStatus("saving");
      }

      const startMs = Date.now();
      try {
        const token = await getTokenReady();
        if (!isMountedRef.current) return;

        await saveRef.current(values, { token });

        if (isMountedRef.current) {
          setStatus("saved");
          setSavedAt(new Date());
          onSavedRef.current?.();
          telemetryRef.current?.({
            type: "saved",
            durationMs: Date.now() - startMs,
          });
        }
      } catch (err: unknown) {
        if (isMountedRef.current) {
          setStatus("error");
          onErrorRef.current?.(err);
          telemetryRef.current?.({
            type: "error",
            durationMs: Date.now() - startMs,
          });
        }
      } finally {
        isSavingRef.current = false;
      }
    },
    [getTokenReady],
  );

  // ── cancel ────────────────────────────────────────────────────────────────
  const cancel = useCallback((): void => {
    if (timerRef.current !== null) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  // ── scheduleSave ─────────────────────────────────────────────────────────
  const scheduleSave = useCallback(
    (values: TValues): void => {
      const prev = lastValuesRef.current;
      if (
        coalesceRef.current &&
        prev !== null &&
        isPlainObject(prev) &&
        isPlainObject(values)
      ) {
        // Merge: las claves nuevas pisan, las anteriores no-pisadas sobreviven.
        lastValuesRef.current = {
          ...(prev as Record<string, unknown>),
          ...(values as Record<string, unknown>),
        } as TValues;
      } else {
        // last-wins (default histórico, o coalesce con primitivos/null).
        lastValuesRef.current = values;
      }
      cancel(); // cancel prior timer — el merge ya vive en lastValuesRef

      if (isMountedRef.current) {
        setStatus("dirty");
      }

      timerRef.current = setTimeout(() => {
        timerRef.current = null;
        if (isMountedRef.current && lastValuesRef.current !== null) {
          void executeSave(lastValuesRef.current);
        }
      }, debounceMs);
    },
    [cancel, executeSave, debounceMs],
  );

  // ── retry ─────────────────────────────────────────────────────────────────
  const retry = useCallback((): void => {
    if (lastValuesRef.current !== null) {
      void executeSave(lastValuesRef.current);
    }
  }, [executeSave]);

  // ── flush ─────────────────────────────────────────────────────────────────
  // Cancela el debounce y guarda ya los valores acumulados (merge o último).
  // Mantiene lastValuesRef poblado: si el guardado falla, retry() lo reusa;
  // si llega un scheduleSave posterior con coalesce, mergea sobre este lote
  // (las mismas claves se sobrescriben, así que re-guardar es idempotente).
  const flush = useCallback(async (): Promise<void> => {
    cancel();
    if (lastValuesRef.current === null) return;
    await executeSave(lastValuesRef.current);
  }, [cancel, executeSave]);

  // ── Cleanup on unmount ────────────────────────────────────────────────────
  useEffect(() => {
    return () => {
      cancel();
    };
  }, [cancel]);

  return { status, savedAt, scheduleSave, cancel, retry, flush };
}

// ── helpers ────────────────────────────────────────────────────────────────

/**
 * True si el valor es un objeto plano mergeable (no null, no array, no Date,
 * no instancia de clase con prototipo no-Object). Conservador: solo objetos
 * literales / Record planos entran al merge de coalesce.
 */
function isPlainObject(value: unknown): value is Record<string, unknown> {
  if (typeof value !== "object" || value === null) return false;
  if (Array.isArray(value)) return false;
  const proto = Object.getPrototypeOf(value) as object | null;
  return proto === Object.prototype || proto === null;
}
