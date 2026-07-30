/**
 * useVisualsAutosave.test.ts — Vitest unit tests para hook autosave visuales.
 *
 * T-9 vitalia-fase2-lisa-marca
 * spec_anchor: 06-tickets.yaml T-9 deliverables + 03-arch.md § 4
 *
 * Tests cubiertos:
 *   - Estado inicial (autosaveStatus='idle', savedAt=null)
 *   - scheduleAutosave: transición idle → dirty
 *   - Debounce 600ms: mutación NO dispara antes del timeout
 *   - Debounce 600ms: mutación SÍ dispara después del timeout
 *   - onSuccess: transición saving → saved + savedAt set
 *   - onError: transición saving → error
 *   - Rapid edits: solo el último scheduleAutosave dispara la mutación
 *
 * downstream-regression-na: brand-local vitalia FE hook tests; no cross-brand consumers
 */

import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { renderHook, act, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import React from "react";
import { useVisualsAutosave } from "../useVisualsAutosave";

// ── Mocks ──────────────────────────────────────────────────────────────────────

const { mockUpdateVisuals } = vi.hoisted(() => ({
  mockUpdateVisuals: vi.fn(),
}));

vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({
    getToken: vi.fn().mockResolvedValue("mock-token-visuals"),
    isLoaded: true,
    isSignedIn: true,
  }),
}));
vi.mock("@/hooks/useTenantId", () => ({ useTenantId: () => "mock-tenant-id" }));


vi.mock("../../api/marca", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../../api/marca")>();
  return {
    ...actual,
    updateVisuals: mockUpdateVisuals,
  };
});

// ── Fixtures ───────────────────────────────────────────────────────────────────

const VISUALS_VALUES = {
  primary_color: "#2563EB",
  accent_color: "#10B981",
  background_color: "#FFFFFF",
  font_heading: "Inter",
  font_body: "Inter",
  design_style: "Minimalista médico",
};

function makeWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return React.createElement(QueryClientProvider, { client: queryClient }, children);
  };
}

// ── Tests ──────────────────────────────────────────────────────────────────────

describe("useVisualsAutosave — estado inicial", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    mockUpdateVisuals.mockResolvedValue({
      ...VISUALS_VALUES,
      tenantId: "t1",
      clinicId: "c1",
      logoUrl: null,
      updatedAt: "2026-01-01T00:00:00Z",
    });
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.clearAllMocks();
  });

  it("autosaveStatus empieza en 'idle'", () => {
    const { result } = renderHook(
      () => useVisualsAutosave({ tenantId: "t1", clinicId: "c1" }),
      { wrapper: makeWrapper() },
    );
    expect(result.current.autosaveStatus).toBe("idle");
  });

  it("savedAt empieza en null", () => {
    const { result } = renderHook(
      () => useVisualsAutosave({ tenantId: "t1", clinicId: "c1" }),
      { wrapper: makeWrapper() },
    );
    expect(result.current.savedAt).toBeNull();
  });
});

describe("useVisualsAutosave — scheduleAutosave y debounce", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    mockUpdateVisuals.mockResolvedValue({
      ...VISUALS_VALUES,
      tenantId: "t1",
      clinicId: "c1",
      logoUrl: null,
      updatedAt: "2026-01-01T00:00:00Z",
    });
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.clearAllMocks();
  });

  it("pasa a 'dirty' al llamar scheduleAutosave", () => {
    const { result } = renderHook(
      () => useVisualsAutosave({ tenantId: "t1", clinicId: "c1" }),
      { wrapper: makeWrapper() },
    );

    act(() => {
      result.current.scheduleAutosave(VISUALS_VALUES);
    });

    expect(result.current.autosaveStatus).toBe("dirty");
  });

  it("NO llama updateVisuals antes de 600ms", () => {
    const { result } = renderHook(
      () => useVisualsAutosave({ tenantId: "t1", clinicId: "c1" }),
      { wrapper: makeWrapper() },
    );

    act(() => {
      result.current.scheduleAutosave(VISUALS_VALUES);
    });

    act(() => {
      vi.advanceTimersByTime(300);
    });

    expect(mockUpdateVisuals).not.toHaveBeenCalled();
  });

  it("llama updateVisuals después de 600ms", async () => {
    const { result } = renderHook(
      () => useVisualsAutosave({ tenantId: "t1", clinicId: "c1" }),
      { wrapper: makeWrapper() },
    );

    act(() => {
      result.current.scheduleAutosave(VISUALS_VALUES);
    });

    await act(async () => {
      await vi.advanceTimersByTimeAsync(600);
    });

    expect(mockUpdateVisuals).toHaveBeenCalledTimes(1);
  });

  it("rapid edits: solo una mutación al hacer ediciones rápidas", async () => {
    const { result } = renderHook(
      () => useVisualsAutosave({ tenantId: "t1", clinicId: "c1" }),
      { wrapper: makeWrapper() },
    );

    act(() => {
      result.current.scheduleAutosave({ ...VISUALS_VALUES, primary_color: "#000000" });
    });
    await act(async () => { await vi.advanceTimersByTimeAsync(200); });
    act(() => {
      result.current.scheduleAutosave({ ...VISUALS_VALUES, primary_color: "#111111" });
    });
    await act(async () => { await vi.advanceTimersByTimeAsync(600); });

    expect(mockUpdateVisuals).toHaveBeenCalledTimes(1);
  });
});

describe("useVisualsAutosave — transiciones por resultado de mutación", () => {
  afterEach(() => {
    vi.useRealTimers();
    vi.clearAllMocks();
  });

  it("pasa a 'saved' tras mutación exitosa", async () => {
    vi.useFakeTimers();
    mockUpdateVisuals.mockResolvedValue({
      ...VISUALS_VALUES,
      tenantId: "t1",
      clinicId: "c1",
      logoUrl: null,
      updatedAt: "2026-01-01T00:00:00Z",
    });

    const { result } = renderHook(
      () => useVisualsAutosave({ tenantId: "t1", clinicId: "c1" }),
      { wrapper: makeWrapper() },
    );

    act(() => {
      result.current.scheduleAutosave(VISUALS_VALUES);
    });
    act(() => {
      vi.advanceTimersByTime(600);
    });

    vi.useRealTimers();

    await waitFor(() => {
      expect(result.current.autosaveStatus).toBe("saved");
    });
  });

  it("pasa a 'error' tras mutación fallida", async () => {
    vi.useFakeTimers();
    mockUpdateVisuals.mockRejectedValue(new Error("Network error"));

    const { result } = renderHook(
      () => useVisualsAutosave({ tenantId: "t1", clinicId: "c1" }),
      { wrapper: makeWrapper() },
    );

    act(() => {
      result.current.scheduleAutosave(VISUALS_VALUES);
    });
    act(() => {
      vi.advanceTimersByTime(600);
    });

    vi.useRealTimers();

    await waitFor(() => {
      expect(result.current.autosaveStatus).toBe("error");
    });
  });
});
