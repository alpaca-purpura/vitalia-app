// cap: platform.autosave-primitive-platform
// story-origin: build-autosave-primitive-luana
/**
 * useAutosave.test.ts — TDD (RED → GREEN) para la primitiva de autoguardado.
 *
 * Scenarios (build-autosave-primitive-luana 01-spec.md § Gherkin):
 *   1. debounce-coalesce        — 5 cambios en <2000ms → 1 sola llamada
 *   2. save-success             — status idle→dirty→saving→saved + savedAt + onSaved
 *   3. auth-ready               — getToken null transitorio → espera, NO error permanente
 *   4. error-recovery-retry     — save rechaza → status error → retry()/scheduleSave → saved
 *   5. concurrent-edits-last-wins — scheduleSave A + B rápido → solo B dispara save
 *   6. network-failure          — save lanza → status error, sin excepción no capturada
 *   7. unmount-cancels          — debounce pendiente → unmount → sin save ni setState
 *   8. telemetry-opt-in         — telemetry({ type, durationMs }) llamado; opt-in no rompe
 *
 * Herramientas: Vitest fake timers + @testing-library/react renderHook + mocks vi.fn().
 *
 * ADR-012 — build-autosave-primitive-luana T-1
 */

import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useAutosave } from "../useAutosave";
import type { UseAutosaveOptions } from "../useAutosave";

// ── Helpers ───────────────────────────────────────────────────────────────────

type SimpleValues = { name: string };

function makeMocks() {
  const save = vi.fn(
    (_values: SimpleValues, _ctx: { token: string }): Promise<void> =>
      Promise.resolve(),
  );
  const getToken = vi.fn((): Promise<string | null> => Promise.resolve(null));
  const onSaved = vi.fn((): void => undefined);
  const onError = vi.fn((_err: unknown): void => undefined);
  const telemetry = vi.fn(
    (_event: { type: "saved" | "error"; durationMs: number }): void =>
      undefined,
  );
  return { save, getToken, onSaved, onError, telemetry };
}

/**
 * Build default options.
 * When `preMocked` is false (default), sets up save→resolve, getToken→"tok-abc".
 * Pass `preMocked: true` when you've already set up custom mock behavior on `mocks`.
 */
function defaultOpts(
  overrides: Partial<UseAutosaveOptions<SimpleValues>> = {},
  mocks = makeMocks(),
  preMocked = false,
): UseAutosaveOptions<SimpleValues> {
  if (!preMocked) {
    mocks.save.mockResolvedValue(undefined);
    mocks.getToken.mockResolvedValue("tok-abc");
  }
  return {
    save: mocks.save,
    getToken: mocks.getToken,
    onSaved: mocks.onSaved,
    onError: mocks.onError,
    debounceMs: 2000,
    authReadyAttempts: 10,
    ...overrides,
  };
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe("useAutosave", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.clearAllMocks();
  });

  // ─── 1. debounce-coalesce ──────────────────────────────────────────────────

  it("debounce-coalesce: 5 changes <2000ms → 1 single save call (last-wins)", async () => {
    const mocks = makeMocks();
    mocks.save.mockResolvedValue(undefined);
    mocks.getToken.mockResolvedValue("tok-abc");

    const { result } = renderHook(() =>
      useAutosave<SimpleValues>(defaultOpts({}, mocks)),
    );

    // Dispatch 5 changes rapidly
    act(() => {
      result.current.scheduleSave({ name: "a" });
      result.current.scheduleSave({ name: "b" });
      result.current.scheduleSave({ name: "c" });
      result.current.scheduleSave({ name: "d" });
      result.current.scheduleSave({ name: "e" });
    });

    expect(result.current.status).toBe("dirty");

    // Advance past debounce window
    await act(async () => {
      await vi.advanceTimersByTimeAsync(2000);
    });

    expect(mocks.save).toHaveBeenCalledTimes(1);
    expect(mocks.save).toHaveBeenCalledWith(
      { name: "e" },
      { token: "tok-abc" },
    );
  });

  // ─── 2. save-success ──────────────────────────────────────────────────────

  it("save-success: status transitions idle→dirty→saving→saved + savedAt set + onSaved called", async () => {
    const mocks = makeMocks();
    mocks.save.mockResolvedValue(undefined);
    mocks.getToken.mockResolvedValue("tok-abc");

    const { result } = renderHook(() =>
      useAutosave<SimpleValues>(defaultOpts({}, mocks)),
    );

    expect(result.current.status).toBe("idle");
    expect(result.current.savedAt).toBeNull();

    act(() => {
      result.current.scheduleSave({ name: "test" });
    });

    expect(result.current.status).toBe("dirty");

    await act(async () => {
      await vi.advanceTimersByTimeAsync(2000);
    });

    expect(result.current.status).toBe("saved");
    expect(result.current.savedAt).toBeInstanceOf(Date);
    expect(mocks.onSaved).toHaveBeenCalledTimes(1);
    expect(mocks.save).toHaveBeenCalledWith(
      { name: "test" },
      { token: "tok-abc" },
    );
  });

  // ─── 3. auth-ready: transient null token ──────────────────────────────────

  it("auth-ready: getToken returns null then valid token → waits, saves, NOT permanent error", async () => {
    const mocks = makeMocks();
    mocks.save.mockResolvedValue(undefined);
    // First 2 calls return null, 3rd returns a valid token
    mocks.getToken
      .mockResolvedValueOnce(null)
      .mockResolvedValueOnce(null)
      .mockResolvedValue("tok-ready");

    const { result } = renderHook(() =>
      useAutosave<SimpleValues>({
        save: mocks.save,
        getToken: mocks.getToken,
        onSaved: mocks.onSaved,
        debounceMs: 2000,
        authReadyAttempts: 10,
      }),
    );

    act(() => {
      result.current.scheduleSave({ name: "auth-test" });
    });

    // Advance past debounce + wait cycles for getTokenReady
    await act(async () => {
      await vi.advanceTimersByTimeAsync(3000);
    });

    // Should NOT be in error — must have saved successfully
    expect(result.current.status).toBe("saved");
    expect(mocks.save).toHaveBeenCalledWith(
      { name: "auth-test" },
      { token: "tok-ready" },
    );
  });

  // ─── 4. error-recovery-retry ──────────────────────────────────────────────

  it("error-recovery-retry: save rejects → status error → retry() re-fires → saved", async () => {
    const mocks = makeMocks();
    // First call fails, second succeeds
    mocks.save
      .mockRejectedValueOnce(new Error("5xx"))
      .mockResolvedValue(undefined);
    mocks.getToken.mockResolvedValue("tok-abc");

    const { result } = renderHook(() =>
      useAutosave<SimpleValues>(defaultOpts({}, mocks)),
    );

    act(() => {
      result.current.scheduleSave({ name: "retry-test" });
    });

    await act(async () => {
      await vi.advanceTimersByTimeAsync(2000);
    });

    expect(result.current.status).toBe("error");
    expect(mocks.onError).toHaveBeenCalledWith(expect.any(Error));

    // Now retry
    await act(async () => {
      result.current.retry();
      await vi.advanceTimersByTimeAsync(100);
    });

    expect(result.current.status).toBe("saved");
    expect(mocks.save).toHaveBeenCalledTimes(2);
    expect(mocks.onSaved).toHaveBeenCalledTimes(1);
  });

  it("error-recovery-retry: next scheduleSave after error also re-fires", async () => {
    const mocks = makeMocks();
    mocks.save
      .mockRejectedValueOnce(new Error("5xx"))
      .mockResolvedValue(undefined);
    mocks.getToken.mockResolvedValue("tok-abc");

    const { result } = renderHook(() =>
      useAutosave<SimpleValues>(defaultOpts({}, mocks)),
    );

    act(() => {
      result.current.scheduleSave({ name: "retry-via-schedule" });
    });

    await act(async () => {
      await vi.advanceTimersByTimeAsync(2000);
    });

    expect(result.current.status).toBe("error");

    // New schedule should work
    act(() => {
      result.current.scheduleSave({ name: "retry-via-schedule-2" });
    });

    await act(async () => {
      await vi.advanceTimersByTimeAsync(2000);
    });

    expect(result.current.status).toBe("saved");
  });

  // ─── 5. concurrent-edits-last-wins ────────────────────────────────────────

  it("concurrent-edits-last-wins: cancel prior timer, only last values sent", async () => {
    const mocks = makeMocks();
    mocks.save.mockResolvedValue(undefined);
    mocks.getToken.mockResolvedValue("tok-abc");

    const { result } = renderHook(() =>
      useAutosave<SimpleValues>(defaultOpts({}, mocks)),
    );

    // Schedule A, then immediately B (within debounce window)
    act(() => {
      result.current.scheduleSave({ name: "A" });
    });

    // Still within debounce — schedule B cancels A
    act(() => {
      result.current.scheduleSave({ name: "B" });
    });

    await act(async () => {
      await vi.advanceTimersByTimeAsync(2000);
    });

    expect(mocks.save).toHaveBeenCalledTimes(1);
    expect(mocks.save).toHaveBeenCalledWith({ name: "B" }, { token: "tok-abc" });
  });

  // ─── 6. network-failure ───────────────────────────────────────────────────

  it("network-failure: save throws → status error, no uncaught exception", async () => {
    const mocks = makeMocks();
    mocks.save.mockRejectedValue(new Error("Network timeout"));
    mocks.getToken.mockResolvedValue("tok-abc");

    const { result } = renderHook(() =>
      useAutosave<SimpleValues>(defaultOpts({}, mocks, true)),
    );

    act(() => {
      result.current.scheduleSave({ name: "network-test" });
    });

    // Should not throw
    await act(async () => {
      await vi.advanceTimersByTimeAsync(2000);
    });

    expect(result.current.status).toBe("error");
    expect(mocks.onError).toHaveBeenCalledWith(expect.any(Error));
    expect(mocks.onSaved).not.toHaveBeenCalled();
  });

  // ─── 7. unmount-cancels ───────────────────────────────────────────────────

  it("unmount-cancels: pending debounce cleared on unmount → no save or setState", async () => {
    const mocks = makeMocks();
    mocks.save.mockResolvedValue(undefined);
    mocks.getToken.mockResolvedValue("tok-abc");

    const { result, unmount } = renderHook(() =>
      useAutosave<SimpleValues>(defaultOpts({}, mocks)),
    );

    act(() => {
      result.current.scheduleSave({ name: "unmount-test" });
    });

    expect(result.current.status).toBe("dirty");

    // Unmount BEFORE the debounce fires
    unmount();

    // Advance timers — save must NOT be called after unmount
    await act(async () => {
      await vi.advanceTimersByTimeAsync(3000);
    });

    expect(mocks.save).not.toHaveBeenCalled();
  });

  // ─── 8. telemetry-opt-in ──────────────────────────────────────────────────

  it("telemetry-opt-in: called with {type:'saved', durationMs} on success", async () => {
    const mocks = makeMocks();
    mocks.save.mockResolvedValue(undefined);
    mocks.getToken.mockResolvedValue("tok-abc");

    const { result } = renderHook(() =>
      useAutosave<SimpleValues>(defaultOpts({ telemetry: mocks.telemetry }, mocks)),
    );

    act(() => {
      result.current.scheduleSave({ name: "telemetry-test" });
    });

    await act(async () => {
      await vi.advanceTimersByTimeAsync(2000);
    });

    expect(mocks.telemetry).toHaveBeenCalledTimes(1);
    expect(mocks.telemetry).toHaveBeenCalledWith(
      expect.objectContaining({
        type: "saved",
        durationMs: expect.any(Number),
      }),
    );
  });

  it("telemetry-opt-in: called with {type:'error'} on failure", async () => {
    const mocks = makeMocks();
    mocks.save.mockRejectedValue(new Error("oops"));
    mocks.getToken.mockResolvedValue("tok-abc");

    const { result } = renderHook(() =>
      useAutosave<SimpleValues>(defaultOpts({ telemetry: mocks.telemetry }, mocks, true)),
    );

    act(() => {
      result.current.scheduleSave({ name: "telemetry-error" });
    });

    await act(async () => {
      await vi.advanceTimersByTimeAsync(2000);
    });

    expect(mocks.telemetry).toHaveBeenCalledTimes(1);
    expect(mocks.telemetry).toHaveBeenCalledWith(
      expect.objectContaining({ type: "error" }),
    );
  });

  it("telemetry-opt-in: absent telemetry option does NOT break save", async () => {
    const mocks = makeMocks();
    mocks.save.mockResolvedValue(undefined);
    mocks.getToken.mockResolvedValue("tok-abc");

    const { result } = renderHook(() =>
      useAutosave<SimpleValues>({
        save: mocks.save,
        getToken: mocks.getToken,
        debounceMs: 2000,
        // NO telemetry provided
      }),
    );

    act(() => {
      result.current.scheduleSave({ name: "no-telemetry" });
    });

    // Should not throw
    await act(async () => {
      await vi.advanceTimersByTimeAsync(2000);
    });

    expect(result.current.status).toBe("saved");
  });
});
