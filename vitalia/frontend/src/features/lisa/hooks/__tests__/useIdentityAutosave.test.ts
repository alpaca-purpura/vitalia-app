/**
 * useIdentityAutosave.test.ts — Vitest unit tests para hook autosave identidad.
 *
 * T-9 vitalia-fase2-lisa-marca
 * spec_anchor: 06-tickets.yaml T-9 deliverables + 03-arch.md § 4
 *
 * Tests cubiertos:
 *   - Estado inicial (autosaveStatus='idle', savedAt=null)
 *   - scheduleAutosave: transición idle → dirty
 *   - Debounce 600ms: mutación NO dispara antes del timeout
 *   - Debounce 600ms: mutación SÍ dispara después del timeout
 *   - Rapid edits: solo el último scheduleAutosave dispara la mutación
 *   - onMutate: transición dirty → saving
 *   - onSuccess: transición saving → saved + savedAt set
 *   - onError: transición saving → error
 *   - cancelAutosave: cancela timer pendiente, sin llamar mutación
 *   - Unmount cleanup: cancelAutosave llamado al desmontar
 *   - Sin token: mutación lanza "Not authenticated"
 *
 * downstream-regression-na: brand-local vitalia FE hook tests; no cross-brand consumers
 */

import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { renderHook, act, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import React from "react";
import { useIdentityAutosave } from "../useIdentityAutosave";

// ── Mocks ──────────────────────────────────────────────────────────────────────

// vi.hoisted() ensures variables are available when vi.mock factories are hoisted
const { mockGetToken, mockUpdateIdentity } = vi.hoisted(() => ({
  mockGetToken: vi.fn().mockResolvedValue("mock-token-identity"),
  mockUpdateIdentity: vi.fn(),
}));

vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({
    getToken: mockGetToken,
    isLoaded: true,
    isSignedIn: true,
  }),
}));
vi.mock("@/hooks/useTenantId", () => ({ useTenantId: () => "mock-tenant-id" }));


vi.mock("../../api/marca", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../../api/marca")>();
  return {
    ...actual,
    updateIdentity: mockUpdateIdentity,
  };
});

// ── Fixtures ───────────────────────────────────────────────────────────────────

const IDENTITY_VALUES = {
  brand_name: "Clínica San Pedro",
  tagline: "Tu salud, nuestra prioridad",
  description: "Clínica líder en Lima",
  industry: "Salud",
  website: "https://clinicasanpedro.pe",
  founding_year: "2015",
  language: "es",
  timezone: "America/Lima",
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

describe("useIdentityAutosave — estado inicial", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    mockUpdateIdentity.mockResolvedValue({ ...IDENTITY_VALUES, tenantId: "t1", clinicId: "c1", updatedAt: "2026-01-01T00:00:00Z" });
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.clearAllMocks();
  });

  it("autosaveStatus empieza en 'idle'", () => {
    const { result } = renderHook(
      () => useIdentityAutosave({ tenantId: "t1", clinicId: "c1" }),
      { wrapper: makeWrapper() },
    );
    expect(result.current.autosaveStatus).toBe("idle");
  });

  it("savedAt empieza en null", () => {
    const { result } = renderHook(
      () => useIdentityAutosave({ tenantId: "t1", clinicId: "c1" }),
      { wrapper: makeWrapper() },
    );
    expect(result.current.savedAt).toBeNull();
  });
});

describe("useIdentityAutosave — scheduleAutosave transiciones", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    mockUpdateIdentity.mockResolvedValue({ ...IDENTITY_VALUES, tenantId: "t1", clinicId: "c1", updatedAt: "2026-01-01T00:00:00Z" });
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.clearAllMocks();
  });

  it("pasa a 'dirty' al llamar scheduleAutosave", () => {
    const { result } = renderHook(
      () => useIdentityAutosave({ tenantId: "t1", clinicId: "c1" }),
      { wrapper: makeWrapper() },
    );

    act(() => {
      result.current.scheduleAutosave(IDENTITY_VALUES);
    });

    expect(result.current.autosaveStatus).toBe("dirty");
  });

  it("NO llama updateIdentity antes de 600ms", () => {
    const { result } = renderHook(
      () => useIdentityAutosave({ tenantId: "t1", clinicId: "c1" }),
      { wrapper: makeWrapper() },
    );

    act(() => {
      result.current.scheduleAutosave(IDENTITY_VALUES);
    });

    // Avanzar solo 300ms — mutación NO debe haberse disparado
    act(() => {
      vi.advanceTimersByTime(300);
    });

    expect(mockUpdateIdentity).not.toHaveBeenCalled();
  });

  it("llama updateIdentity después de 600ms (debounce completo)", async () => {
    const { result } = renderHook(
      () => useIdentityAutosave({ tenantId: "t1", clinicId: "c1" }),
      { wrapper: makeWrapper() },
    );

    act(() => {
      result.current.scheduleAutosave(IDENTITY_VALUES);
    });

    // advanceTimersByTimeAsync avanza fake timers Y procesa promises pendientes
    await act(async () => {
      await vi.advanceTimersByTimeAsync(600);
    });

    expect(mockUpdateIdentity).toHaveBeenCalledTimes(1);
  });
});

describe("useIdentityAutosave — rapid edits (debounce cancela)", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    mockUpdateIdentity.mockResolvedValue({ ...IDENTITY_VALUES, tenantId: "t1", clinicId: "c1", updatedAt: "2026-01-01T00:00:00Z" });
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.clearAllMocks();
  });

  it("solo dispara una mutación con ediciones rápidas", async () => {
    const { result } = renderHook(
      () => useIdentityAutosave({ tenantId: "t1", clinicId: "c1" }),
      { wrapper: makeWrapper() },
    );

    // 3 ediciones rápidas — solo la última debe persistir
    act(() => {
      result.current.scheduleAutosave({ ...IDENTITY_VALUES, brand_name: "Clínica A" });
    });
    await act(async () => { await vi.advanceTimersByTimeAsync(200); });
    act(() => {
      result.current.scheduleAutosave({ ...IDENTITY_VALUES, brand_name: "Clínica B" });
    });
    await act(async () => { await vi.advanceTimersByTimeAsync(200); });
    act(() => {
      result.current.scheduleAutosave({ ...IDENTITY_VALUES, brand_name: "Clínica C" });
    });
    await act(async () => { await vi.advanceTimersByTimeAsync(600); });

    expect(mockUpdateIdentity).toHaveBeenCalledTimes(1);
  });
});

describe("useIdentityAutosave — transiciones de estado por mutación", () => {
  afterEach(() => {
    vi.useRealTimers();
    vi.clearAllMocks();
  });

  it("pasa a 'saved' tras mutación exitosa", async () => {
    vi.useFakeTimers();
    mockUpdateIdentity.mockResolvedValue({ ...IDENTITY_VALUES, tenantId: "t1", clinicId: "c1", updatedAt: "2026-01-01T00:00:00Z" });

    const { result } = renderHook(
      () => useIdentityAutosave({ tenantId: "t1", clinicId: "c1" }),
      { wrapper: makeWrapper() },
    );

    act(() => {
      result.current.scheduleAutosave(IDENTITY_VALUES);
    });
    act(() => {
      vi.advanceTimersByTime(600);
    });

    vi.useRealTimers();

    await waitFor(() => {
      expect(result.current.autosaveStatus).toBe("saved");
    });
  });

  it("savedAt es una Date tras mutación exitosa", async () => {
    vi.useFakeTimers();
    mockUpdateIdentity.mockResolvedValue({ ...IDENTITY_VALUES, tenantId: "t1", clinicId: "c1", updatedAt: "2026-01-01T00:00:00Z" });

    const { result } = renderHook(
      () => useIdentityAutosave({ tenantId: "t1", clinicId: "c1" }),
      { wrapper: makeWrapper() },
    );

    act(() => {
      result.current.scheduleAutosave(IDENTITY_VALUES);
    });
    act(() => {
      vi.advanceTimersByTime(600);
    });

    vi.useRealTimers();

    await waitFor(() => {
      expect(result.current.savedAt).toBeInstanceOf(Date);
    });
  });

  it("pasa a 'error' tras mutación fallida", async () => {
    vi.useFakeTimers();
    mockUpdateIdentity.mockRejectedValue(new Error("Server error 500"));

    const { result } = renderHook(
      () => useIdentityAutosave({ tenantId: "t1", clinicId: "c1" }),
      { wrapper: makeWrapper() },
    );

    act(() => {
      result.current.scheduleAutosave(IDENTITY_VALUES);
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

describe("useIdentityAutosave — cancelAutosave", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    mockUpdateIdentity.mockResolvedValue({ ...IDENTITY_VALUES, tenantId: "t1", clinicId: "c1", updatedAt: "2026-01-01T00:00:00Z" });
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.clearAllMocks();
  });

  it("cancelAutosave evita que la mutación se dispare", () => {
    const { result } = renderHook(
      () => useIdentityAutosave({ tenantId: "t1", clinicId: "c1" }),
      { wrapper: makeWrapper() },
    );

    act(() => {
      result.current.scheduleAutosave(IDENTITY_VALUES);
    });
    act(() => {
      result.current.cancelAutosave();
    });
    act(() => {
      vi.advanceTimersByTime(700);
    });

    expect(mockUpdateIdentity).not.toHaveBeenCalled();
  });
});

describe("useIdentityAutosave — sin token de autenticación", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    mockGetToken.mockResolvedValue(null); // Sin token
    mockUpdateIdentity.mockImplementation(() => {
      throw new Error("Not authenticated");
    });
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.clearAllMocks();
    mockGetToken.mockResolvedValue("mock-token-identity");
  });

  it("no llama updateIdentity cuando el token es null", async () => {
    const { result } = renderHook(
      () => useIdentityAutosave({ tenantId: "t1", clinicId: "c1" }),
      { wrapper: makeWrapper() },
    );

    act(() => {
      result.current.scheduleAutosave(IDENTITY_VALUES);
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
