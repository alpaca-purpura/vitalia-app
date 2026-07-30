/**
 * useContactAutosave.test.ts — Vitest unit tests para hook autosave contacto/presencia.
 *
 * T-9 vitalia-fase2-lisa-marca
 * spec_anchor: 06-tickets.yaml T-9 deliverables + 03-arch.md § 4.3
 *
 * Tests cubiertos:
 *   - Estado inicial (autosaveStatus='idle', savedAt=null)
 *   - scheduleAutosave: transición idle → dirty
 *   - Debounce 600ms: mutación NO dispara antes del timeout
 *   - Debounce 600ms: mutación SÍ dispara después del timeout
 *   - onSuccess: transición → saved
 *   - onError: transición → error
 *   - Rapid edits: solo el último scheduleAutosave dispara la mutación
 *   - cancelAutosave: evita la mutación
 *
 * downstream-regression-na: brand-local vitalia FE hook tests; no cross-brand consumers
 */

import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { renderHook, act, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import React from "react";
import { useContactAutosave } from "../useContactAutosave";

// ── Mocks ──────────────────────────────────────────────────────────────────────

const { mockUpdateContact } = vi.hoisted(() => ({
  mockUpdateContact: vi.fn(),
}));

vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({
    getToken: vi.fn().mockResolvedValue("mock-token-contact"),
    isLoaded: true,
    isSignedIn: true,
  }),
}));
vi.mock("@/hooks/useTenantId", () => ({ useTenantId: () => "mock-tenant-id" }));


vi.mock("../../api/marca-presence-api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../../api/marca-presence-api")>();
  return {
    ...actual,
    updateContact: mockUpdateContact,
  };
});

// ── Fixtures ───────────────────────────────────────────────────────────────────

// BrandContactPatchPayload campos camelCase (per 03-arch.md § 4.3)
const CONTACT_VALUES = {
  websiteUrl: "https://clinicasanpedro.pe",
  instagramHandle: "clinicasanpedro",
  facebookPage: "https://facebook.com/clinicasanpedro",
  googleBusinessUrl: "https://g.page/clinicasanpedro",
  whatsappBusiness: "+51912345678",
  yearsExperience: 12,
  patientsCount: "5000+",
  awards: "Premio Excelencia Médica 2023",
};

const CONTACT_RESPONSE = {
  tenantId: "t1",
  publicLandingUrl: null,
  websiteUrl: "https://clinicasanpedro.pe",
  instagramHandle: "clinicasanpedro",
  tiktokHandle: null,
  facebookPage: "https://facebook.com/clinicasanpedro",
  googleBusinessUrl: "https://g.page/clinicasanpedro",
  updatedAt: "2026-01-01T00:00:00Z",
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

describe("useContactAutosave — estado inicial", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    mockUpdateContact.mockResolvedValue(CONTACT_RESPONSE);
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.clearAllMocks();
  });

  it("autosaveStatus empieza en 'idle'", () => {
    const { result } = renderHook(
      () => useContactAutosave({ tenantId: "t1", clinicId: "c1" }),
      { wrapper: makeWrapper() },
    );
    expect(result.current.autosaveStatus).toBe("idle");
  });

  it("savedAt empieza en null", () => {
    const { result } = renderHook(
      () => useContactAutosave({ tenantId: "t1", clinicId: "c1" }),
      { wrapper: makeWrapper() },
    );
    expect(result.current.savedAt).toBeNull();
  });
});

describe("useContactAutosave — scheduleAutosave y debounce", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    mockUpdateContact.mockResolvedValue(CONTACT_RESPONSE);
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.clearAllMocks();
  });

  it("pasa a 'dirty' al llamar scheduleAutosave", () => {
    const { result } = renderHook(
      () => useContactAutosave({ tenantId: "t1", clinicId: "c1" }),
      { wrapper: makeWrapper() },
    );

    act(() => {
      result.current.scheduleAutosave(CONTACT_VALUES);
    });

    expect(result.current.autosaveStatus).toBe("dirty");
  });

  it("NO llama updateContact antes de 600ms", () => {
    const { result } = renderHook(
      () => useContactAutosave({ tenantId: "t1", clinicId: "c1" }),
      { wrapper: makeWrapper() },
    );

    act(() => {
      result.current.scheduleAutosave(CONTACT_VALUES);
    });

    act(() => {
      vi.advanceTimersByTime(300);
    });

    expect(mockUpdateContact).not.toHaveBeenCalled();
  });

  it("llama updateContact después de 600ms", async () => {
    const { result } = renderHook(
      () => useContactAutosave({ tenantId: "t1", clinicId: "c1" }),
      { wrapper: makeWrapper() },
    );

    act(() => {
      result.current.scheduleAutosave(CONTACT_VALUES);
    });

    await act(async () => {
      await vi.advanceTimersByTimeAsync(600);
    });

    expect(mockUpdateContact).toHaveBeenCalledTimes(1);
  });

  it("rapid edits: solo dispara una mutación", async () => {
    const { result } = renderHook(
      () => useContactAutosave({ tenantId: "t1", clinicId: "c1" }),
      { wrapper: makeWrapper() },
    );

    // 3 ediciones rápidas en menos de 600ms
    act(() => {
      result.current.scheduleAutosave({ ...CONTACT_VALUES, whatsappBusiness: "+51 1 111 1111" });
    });
    await act(async () => { await vi.advanceTimersByTimeAsync(200); });
    act(() => {
      result.current.scheduleAutosave({ ...CONTACT_VALUES, whatsappBusiness: "+51 1 222 2222" });
    });
    await act(async () => { await vi.advanceTimersByTimeAsync(200); });
    act(() => {
      result.current.scheduleAutosave({ ...CONTACT_VALUES, whatsappBusiness: "+51 1 333 3333" });
    });
    await act(async () => { await vi.advanceTimersByTimeAsync(600); });

    expect(mockUpdateContact).toHaveBeenCalledTimes(1);
  });
});

describe("useContactAutosave — transiciones por resultado de mutación", () => {
  afterEach(() => {
    vi.useRealTimers();
    vi.clearAllMocks();
  });

  it("pasa a 'saved' tras mutación exitosa", async () => {
    vi.useFakeTimers();
    mockUpdateContact.mockResolvedValue(CONTACT_RESPONSE);

    const { result } = renderHook(
      () => useContactAutosave({ tenantId: "t1", clinicId: "c1" }),
      { wrapper: makeWrapper() },
    );

    act(() => {
      result.current.scheduleAutosave(CONTACT_VALUES);
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
    mockUpdateContact.mockRejectedValue(new Error("500 Internal Server Error"));

    const { result } = renderHook(
      () => useContactAutosave({ tenantId: "t1", clinicId: "c1" }),
      { wrapper: makeWrapper() },
    );

    act(() => {
      result.current.scheduleAutosave(CONTACT_VALUES);
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

describe("useContactAutosave — cancelAutosave", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    mockUpdateContact.mockResolvedValue(CONTACT_RESPONSE);
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.clearAllMocks();
  });

  it("cancelAutosave impide la mutación", () => {
    const { result } = renderHook(
      () => useContactAutosave({ tenantId: "t1", clinicId: "c1" }),
      { wrapper: makeWrapper() },
    );

    act(() => {
      result.current.scheduleAutosave(CONTACT_VALUES);
    });
    act(() => {
      result.current.cancelAutosave();
    });
    act(() => {
      vi.advanceTimersByTime(700);
    });

    expect(mockUpdateContact).not.toHaveBeenCalled();
  });
});
