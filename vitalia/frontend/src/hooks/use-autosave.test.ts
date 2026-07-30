// cap: clinics.lisa.doctores
// story-origin: vitalia-fase2-lisa-doctores
/**
 * use-autosave.test.ts — Tests for autosave debounce hook.
 *
 * TDD RED-first per tdd-mandatory.md.
 *
 * Covers:
 *   - Debounces calls by 600ms
 *   - Calls saveFn after debounce period
 *   - Does NOT call saveFn before debounce period
 *   - Returns correct status (idle / saving / saved / error)
 *   - flush() forces immediate save
 *
 * V-FN-9 + V-ARCH-9 validator gates.
 * T-FE-2 vitalia-fase2-lisa-doctores
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useAutosave } from "./use-autosave";

beforeEach(() => {
  vi.useFakeTimers();
});

afterEach(() => {
  vi.useRealTimers();
});

describe("useAutosave", () => {
  it("starts in idle status", () => {
    const saveFn = vi.fn().mockResolvedValue(undefined);
    const { result } = renderHook(() =>
      useAutosave({ saveFn, debounceMs: 600 }),
    );
    expect(result.current.status).toBe("idle");
  });

  it("does NOT call saveFn before 600ms", async () => {
    const saveFn = vi.fn().mockResolvedValue(undefined);
    const { result } = renderHook(() =>
      useAutosave({ saveFn, debounceMs: 600 }),
    );

    act(() => {
      result.current.schedule({ field: "notes", value: "test" });
    });
    vi.advanceTimersByTime(400);

    expect(saveFn).not.toHaveBeenCalled();
  });

  it("calls saveFn after 600ms debounce", async () => {
    const saveFn = vi.fn().mockResolvedValue(undefined);
    const { result } = renderHook(() =>
      useAutosave({ saveFn, debounceMs: 600 }),
    );

    act(() => {
      result.current.schedule({ field: "notes", value: "test" });
    });

    await act(async () => {
      vi.advanceTimersByTime(600);
    });

    expect(saveFn).toHaveBeenCalledWith({ field: "notes", value: "test" });
  });

  it("resets debounce when schedule called again before timeout", async () => {
    const saveFn = vi.fn().mockResolvedValue(undefined);
    const { result } = renderHook(() =>
      useAutosave({ saveFn, debounceMs: 600 }),
    );

    act(() => {
      result.current.schedule({ field: "notes", value: "first" });
    });
    vi.advanceTimersByTime(400);

    act(() => {
      result.current.schedule({ field: "notes", value: "second" });
    });
    vi.advanceTimersByTime(400);
    expect(saveFn).not.toHaveBeenCalled();

    await act(async () => {
      vi.advanceTimersByTime(200);
    });
    expect(saveFn).toHaveBeenCalledTimes(1);
    expect(saveFn).toHaveBeenCalledWith({ field: "notes", value: "second" });
  });

  it("flush() calls saveFn immediately", async () => {
    const saveFn = vi.fn().mockResolvedValue(undefined);
    const { result } = renderHook(() =>
      useAutosave({ saveFn, debounceMs: 600 }),
    );

    act(() => {
      result.current.schedule({ field: "notes", value: "flushed" });
    });

    await act(async () => {
      await result.current.flush();
    });

    expect(saveFn).toHaveBeenCalledWith({ field: "notes", value: "flushed" });
  });

  it("sets status=saved after successful save", async () => {
    const saveFn = vi.fn().mockResolvedValue(undefined);
    const { result } = renderHook(() =>
      useAutosave({ saveFn, debounceMs: 600 }),
    );

    act(() => {
      result.current.schedule({ field: "notes", value: "test" });
    });

    await act(async () => {
      vi.advanceTimersByTime(600);
    });

    expect(result.current.status).toBe("saved");
  });

  it("sets status=error after failed save", async () => {
    const saveFn = vi
      .fn()
      .mockRejectedValue(new Error("Network error"));
    const { result } = renderHook(() =>
      useAutosave({ saveFn, debounceMs: 600 }),
    );

    act(() => {
      result.current.schedule({ field: "notes", value: "test" });
    });

    await act(async () => {
      vi.advanceTimersByTime(600);
    });

    expect(result.current.status).toBe("error");
  });

  // F3 fix: autosave coalescing — two rapid field edits within the debounce window
  // must produce a single merged PATCH containing both fields (not lose the first one).
  it("coalesces two rapid object field edits into a single merged PATCH", async () => {
    const saveFn = vi.fn().mockResolvedValue(undefined);
    const { result } = renderHook(() =>
      useAutosave<Record<string, unknown>>({ saveFn, debounceMs: 600 }),
    );

    // Field A edit at t=0
    act(() => {
      result.current.schedule({ specialty: "Odontología" });
    });

    // Field B edit at t=300ms (within the debounce window)
    vi.advanceTimersByTime(300);
    act(() => {
      result.current.schedule({ phone: "+51 999 000 111" });
    });

    // Debounce fires at t=300+600=900ms from start
    await act(async () => {
      vi.advanceTimersByTime(600);
    });

    // saveFn called exactly once with BOTH fields merged
    expect(saveFn).toHaveBeenCalledTimes(1);
    expect(saveFn).toHaveBeenCalledWith({
      specialty: "Odontología",
      phone: "+51 999 000 111",
    });
  });

  it("later field value wins when same field edited twice within window", async () => {
    const saveFn = vi.fn().mockResolvedValue(undefined);
    const { result } = renderHook(() =>
      useAutosave<Record<string, unknown>>({ saveFn, debounceMs: 600 }),
    );

    act(() => {
      result.current.schedule({ specialty: "Primera especialidad" });
    });
    vi.advanceTimersByTime(200);

    act(() => {
      result.current.schedule({ specialty: "Especialidad final" });
    });

    await act(async () => {
      vi.advanceTimersByTime(600);
    });

    expect(saveFn).toHaveBeenCalledTimes(1);
    expect(saveFn).toHaveBeenCalledWith({ specialty: "Especialidad final" });
  });
});
