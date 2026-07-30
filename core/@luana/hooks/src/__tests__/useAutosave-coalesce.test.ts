// canon: design-system-canon.md §2.6 · story-origin: core-ds-foundation
/**
 * useAutosave-coalesce.test.ts — TDD para la EXTENSIÓN T-7 de useAutosave.
 *
 * Cubre las dos capacidades nuevas (sin tocar el comportamiento histórico):
 *   A. coalesce=true  → ediciones sucesivas con claves distintas MEZCLAN en
 *      un único payload (merge), en vez de last-wins.
 *   B. coalesce=true con la MISMA clave → la última gana (overwrite normal).
 *   C. flush()        → cancela el debounce y guarda inmediato lo acumulado.
 *   D. flush() sin nada pendiente → no-op (no llama save).
 *   E. BACK-COMPAT: defaults (coalesce ausente, debounceMs 2000) → last-wins,
 *      idéntico al hook original.
 *
 * Herramientas: Vitest fake timers + @testing-library/react renderHook.
 *
 * core-ds-foundation T-7
 */

import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useAutosave } from "../useAutosave";
import type { UseAutosaveOptions } from "../useAutosave";

// ── Helpers ───────────────────────────────────────────────────────────────────

type PatchValues = Record<string, unknown>;

function makeMocks() {
  const save = vi.fn(
    (_values: PatchValues, _ctx: { token: string }): Promise<void> =>
      Promise.resolve(),
  );
  const getToken = vi.fn((): Promise<string | null> => Promise.resolve(null));
  const onSaved = vi.fn((): void => undefined);
  const onError = vi.fn((_err: unknown): void => undefined);
  return { save, getToken, onSaved, onError };
}

function opts(
  overrides: Partial<UseAutosaveOptions<PatchValues>> = {},
  mocks = makeMocks(),
): UseAutosaveOptions<PatchValues> {
  mocks.save.mockResolvedValue(undefined);
  mocks.getToken.mockResolvedValue("tok-abc");
  return {
    save: mocks.save,
    getToken: mocks.getToken,
    onSaved: mocks.onSaved,
    onError: mocks.onError,
    debounceMs: 600,
    authReadyAttempts: 10,
    ...overrides,
  };
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe("useAutosave — coalesce + flush (T-7)", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.clearAllMocks();
  });

  // ─── A. coalesce merge (distinct keys) ─────────────────────────────────────

  it("coalesce=true: successive patches with distinct keys MERGE into one payload", async () => {
    const mocks = makeMocks();
    const { result } = renderHook(() =>
      useAutosave<PatchValues>(opts({ coalesce: true }, mocks)),
    );

    act(() => {
      result.current.scheduleSave({ voz: "cercana" });
      result.current.scheduleSave({ arquetipo: "experto" });
      result.current.scheduleSave({ tono: "calido" });
    });

    expect(result.current.status).toBe("dirty");

    await act(async () => {
      await vi.advanceTimersByTimeAsync(600);
    });

    expect(mocks.save).toHaveBeenCalledTimes(1);
    expect(mocks.save).toHaveBeenCalledWith(
      { voz: "cercana", arquetipo: "experto", tono: "calido" },
      { token: "tok-abc" },
    );
  });

  // ─── B. coalesce same key → last wins ──────────────────────────────────────

  it("coalesce=true: same key overwrites (last value wins for that key)", async () => {
    const mocks = makeMocks();
    const { result } = renderHook(() =>
      useAutosave<PatchValues>(opts({ coalesce: true }, mocks)),
    );

    act(() => {
      result.current.scheduleSave({ voz: "cercana", tono: "calido" });
      result.current.scheduleSave({ voz: "directa" });
    });

    await act(async () => {
      await vi.advanceTimersByTimeAsync(600);
    });

    expect(mocks.save).toHaveBeenCalledTimes(1);
    expect(mocks.save).toHaveBeenCalledWith(
      { voz: "directa", tono: "calido" },
      { token: "tok-abc" },
    );
  });

  // ─── C. flush() saves immediately ──────────────────────────────────────────

  it("flush(): cancels debounce and saves the accumulated merge right away", async () => {
    const mocks = makeMocks();
    const { result } = renderHook(() =>
      useAutosave<PatchValues>(opts({ coalesce: true }, mocks)),
    );

    act(() => {
      result.current.scheduleSave({ voz: "cercana" });
      result.current.scheduleSave({ arquetipo: "experto" });
    });

    // No esperamos el debounce: forzamos flush.
    await act(async () => {
      await result.current.flush();
    });

    expect(mocks.save).toHaveBeenCalledTimes(1);
    expect(mocks.save).toHaveBeenCalledWith(
      { voz: "cercana", arquetipo: "experto" },
      { token: "tok-abc" },
    );
    expect(result.current.status).toBe("saved");

    // El debounce ya estaba cancelado: avanzar el tiempo NO re-guarda.
    await act(async () => {
      await vi.advanceTimersByTimeAsync(600);
    });
    expect(mocks.save).toHaveBeenCalledTimes(1);
  });

  // ─── D. flush() with nothing pending is a no-op ────────────────────────────

  it("flush(): no-op when nothing was scheduled", async () => {
    const mocks = makeMocks();
    const { result } = renderHook(() =>
      useAutosave<PatchValues>(opts({ coalesce: true }, mocks)),
    );

    await act(async () => {
      await result.current.flush();
    });

    expect(mocks.save).not.toHaveBeenCalled();
  });

  // ─── E. BACK-COMPAT: defaults keep last-wins ───────────────────────────────

  it("back-compat: with defaults (no coalesce) distinct-key patches LAST-WIN, not merge", async () => {
    const mocks = makeMocks();
    // Default debounce 2000, coalesce absent → false.
    const { result } = renderHook(() =>
      useAutosave<PatchValues>({
        save: mocks.save,
        getToken: mocks.getToken,
        onSaved: mocks.onSaved,
        onError: mocks.onError,
      }),
    );
    mocks.save.mockResolvedValue(undefined);
    mocks.getToken.mockResolvedValue("tok-abc");

    act(() => {
      result.current.scheduleSave({ voz: "cercana" });
      result.current.scheduleSave({ arquetipo: "experto" });
    });

    await act(async () => {
      await vi.advanceTimersByTimeAsync(2000);
    });

    expect(mocks.save).toHaveBeenCalledTimes(1);
    // Sin coalesce el segundo payload pisa entero: NO contiene `voz`.
    expect(mocks.save).toHaveBeenCalledWith(
      { arquetipo: "experto" },
      { token: "tok-abc" },
    );
  });

  // ─── F. flush() works in last-wins mode too ────────────────────────────────

  it("flush(): also works without coalesce (saves the last value)", async () => {
    const mocks = makeMocks();
    const { result } = renderHook(() =>
      useAutosave<PatchValues>(opts({ coalesce: false }, mocks)),
    );

    act(() => {
      result.current.scheduleSave({ voz: "cercana" });
      result.current.scheduleSave({ voz: "directa" });
    });

    await act(async () => {
      await result.current.flush();
    });

    expect(mocks.save).toHaveBeenCalledTimes(1);
    expect(mocks.save).toHaveBeenCalledWith(
      { voz: "directa" },
      { token: "tok-abc" },
    );
  });
});
