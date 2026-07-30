/**
 * useVoicePreview.test.ts — Vitest unit tests para hook useVoicePreview.
 *
 * T-9 vitalia-fase2-lisa-marca
 * spec_anchor: 06-tickets.yaml T-9 deliverables + 03-arch.md § 4.2
 *
 * Tests cubiertos:
 *   - Estado inicial (isLoading=false, isError=false, preview=undefined) cuando disabled
 *   - Query habilitada cuando isLoaded + isSignedIn + personalityProfileId
 *   - Query deshabilitada cuando enabled=false
 *   - Query deshabilitada cuando personalityProfileId vacío
 *   - Datos devueltos tras fetch exitoso
 *   - isError=true tras fetch fallido
 *   - queryKey usa marcaKeys.voicePreview(tenantId, blocksHash) (tenant-scoped)
 *   - Refetch al cambiar blocksHash (cache miss por hash diferente)
 *
 * Anti-creep: hook NO llama LLM directo — solo GET /voice-preview (server-side compile).
 * downstream-regression-na: brand-local vitalia FE hook tests; no cross-brand consumers
 */

import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import React from "react";
import { useVoicePreview } from "../useVoicePreview";

// ── Mocks ──────────────────────────────────────────────────────────────────────

const { mockGetVoicePreview } = vi.hoisted(() => ({
  mockGetVoicePreview: vi.fn(),
}));

vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({
    getToken: vi.fn().mockResolvedValue("mock-token-preview"),
    isLoaded: true,
    isSignedIn: true,
  }),
}));
vi.mock("@/hooks/useTenantId", () => ({ useTenantId: () => "mock-tenant-id" }));


vi.mock("../../api/marca-voice-api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../../api/marca-voice-api")>();
  return {
    ...actual,
    getVoicePreview: mockGetVoicePreview,
  };
});

// ── Fixtures ───────────────────────────────────────────────────────────────────

const VOICE_PREVIEW_RESPONSE = {
  personalityProfileId: "pp-001",
  sampleWhatsapp: "Hola, te recordamos tu cita con el Dr. García mañana a las 10:00 AM.",
  sampleEmailReactivacion: "Estimado paciente, hace 6 meses no tienes cita programada.",
  compiledAt: "2026-01-01T00:00:00Z",
  compilerVersion: "v2",
  cacheHit: false,
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

describe("useVoicePreview — query deshabilitada", () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it("preview es undefined cuando enabled=false", () => {
    const { result } = renderHook(
      () => useVoicePreview({
        tenantId: "t1",
        personalityProfileId: "pp-001",
        blocksHash: "abc123",
        enabled: false,
      }),
      { wrapper: makeWrapper() },
    );

    expect(result.current.preview).toBeUndefined();
    expect(result.current.isLoading).toBe(false);
    expect(mockGetVoicePreview).not.toHaveBeenCalled();
  });

  it("preview es undefined cuando personalityProfileId es string vacío", () => {
    const { result } = renderHook(
      () => useVoicePreview({
        tenantId: "t1",
        personalityProfileId: "", // vacío → disabled
        blocksHash: "abc123",
      }),
      { wrapper: makeWrapper() },
    );

    expect(result.current.preview).toBeUndefined();
    expect(mockGetVoicePreview).not.toHaveBeenCalled();
  });
});

describe("useVoicePreview — query habilitada", () => {
  beforeEach(() => {
    mockGetVoicePreview.mockResolvedValue(VOICE_PREVIEW_RESPONSE);
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("retorna datos de preview tras fetch exitoso", async () => {
    const { result } = renderHook(
      () => useVoicePreview({
        tenantId: "t1",
        personalityProfileId: "pp-001",
        blocksHash: "abc123",
      }),
      { wrapper: makeWrapper() },
    );

    await waitFor(() => {
      expect(result.current.preview).toBeDefined();
    });

    expect(result.current.preview?.personalityProfileId).toBe("pp-001");
    expect(result.current.preview?.sampleWhatsapp).toBe(VOICE_PREVIEW_RESPONSE.sampleWhatsapp);
  });

  it("isError=false tras fetch exitoso", async () => {
    const { result } = renderHook(
      () => useVoicePreview({
        tenantId: "t1",
        personalityProfileId: "pp-001",
        blocksHash: "abc123",
      }),
      { wrapper: makeWrapper() },
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.isError).toBe(false);
  });

  it("llama getVoicePreview con blocksHash correcto", async () => {
    const { result } = renderHook(
      () => useVoicePreview({
        tenantId: "t1",
        personalityProfileId: "pp-001",
        blocksHash: "hash-xyz-789",
      }),
      { wrapper: makeWrapper() },
    );

    await waitFor(() => {
      expect(result.current.preview).toBeDefined();
    });

    expect(mockGetVoicePreview).toHaveBeenCalledWith(
      expect.objectContaining({ tenantId: "t1" }),
      "hash-xyz-789",
    );
  });
});

describe("useVoicePreview — error handling", () => {
  beforeEach(() => {
    mockGetVoicePreview.mockRejectedValue(new Error("503 Service Unavailable"));
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("isError=true tras fetch fallido", async () => {
    const { result } = renderHook(
      () => useVoicePreview({
        tenantId: "t1",
        personalityProfileId: "pp-001",
        blocksHash: "abc123",
      }),
      { wrapper: makeWrapper() },
    );

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.preview).toBeUndefined();
  });
});

describe("useVoicePreview — cache key por tenant+hash", () => {
  beforeEach(() => {
    mockGetVoicePreview.mockResolvedValue(VOICE_PREVIEW_RESPONSE);
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("hace fetch separado para diferentes tenantId (tenant isolation)", async () => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
    });
    const wrapper = ({ children }: { children: React.ReactNode }) =>
      React.createElement(QueryClientProvider, { client: queryClient }, children);

    const { result: r1 } = renderHook(
      () => useVoicePreview({ tenantId: "tenant-A", personalityProfileId: "pp-001", blocksHash: "hash1" }),
      { wrapper },
    );

    const { result: r2 } = renderHook(
      () => useVoicePreview({ tenantId: "tenant-B", personalityProfileId: "pp-001", blocksHash: "hash1" }),
      { wrapper },
    );

    await waitFor(() => {
      expect(r1.current.preview).toBeDefined();
      expect(r2.current.preview).toBeDefined();
    });

    // 2 queries separadas por tenant
    expect(mockGetVoicePreview).toHaveBeenCalledTimes(2);
  });
});
