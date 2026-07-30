// cap: platform.autosave-primitive-platform
// story-origin: build-autosave-primitive-luana

/**
 * AutosaveContract — tipos compartidos para la primitiva de autoguardado.
 *
 * Exportados desde @luana/schemas (sin dependencia de Clerk ni de brand).
 * El consumer inyecta `save` + `getToken` desacoplando auth y mutación.
 *
 * ADR-012 — build-autosave-primitive-luana T-1
 */

/** Estado observable del ciclo de autoguardado. */
export type AutosaveStatus = "idle" | "dirty" | "saving" | "saved" | "error";

/**
 * Opciones de configuración para useAutosave<TValues>.
 *
 * @template TValues Tipo del payload que se enviará al servidor.
 */
export interface UseAutosaveOptions<TValues> {
  /**
   * Función de mutación real — inyectada por el consumer.
   * Recibe los valores del formulario + el token de autenticación ya resuelto.
   */
  save: (values: TValues, ctx: { token: string }) => Promise<unknown>;

  /**
   * Proveedor de token — inyectado (desacopla Clerk u otro auth provider).
   * Puede devolver null transitoriamente (el hook espera hasta authReadyAttempts × 200ms).
   */
  getToken: () => Promise<string | null>;

  /** Callback on success — ej. invalidar una React Query key. Opcional. */
  onSaved?: () => void;

  /** Callback on error — ej. mostrar toast. Opcional. */
  onError?: (err: unknown) => void;

  /**
   * Ventana de debounce en milisegundos.
   * @default 2000
   */
  debounceMs?: number;

  /**
   * Callback de telemetría opt-in.
   * Llamado con { type, durationMs } al terminar cada intento (éxito o error).
   * Si no se provee no rompe.
   */
  telemetry?: (event: { type: "saved" | "error"; durationMs: number }) => void;

  /**
   * Máximo número de intentos esperando un token no-null (× 200ms cada uno).
   * @default 10  (≈ 2 segundos)
   */
  authReadyAttempts?: number;
}

/**
 * Interfaz retornada por useAutosave<TValues>.
 *
 * @template TValues Tipo del payload que se enviará al servidor.
 */
export interface UseAutosaveReturn<TValues> {
  /** Estado actual del ciclo de guardado. */
  status: AutosaveStatus;

  /** Fecha/hora del último guardado exitoso, o null si nunca se guardó. */
  savedAt: Date | null;

  /**
   * Agenda un guardado debounced.
   * Cancela cualquier timer previo (last-wins).
   * Transiciona el estado a "dirty" de inmediato.
   */
  scheduleSave: (values: TValues) => void;

  /** Cancela el timer debounced pendiente sin disparar el save. */
  cancel: () => void;

  /**
   * Re-dispara el último conjunto de valores fallido.
   * No hace nada si no hubo un intento previo fallido.
   */
  retry: () => void;
}
