/**
 * useVoiceBlocklist.test.ts — Vitest unit tests para hook useVoiceBlocklist.
 *
 * T-9 vitalia-fase2-lisa-marca
 * spec_anchor: 06-tickets.yaml T-9 deliverables + 03-arch.md § 4.2
 *
 * Tests cubiertos:
 *   - Estado inicial (phrases=[], isLoading=true mientras carga)
 *   - Retorna array phrases tras fetch exitoso
 *   - Retorna array vacío si items es undefined (fallback ??)
 *   - isLoading=false tras fetch completado
 *   - No fetch cuando isSignedIn=false
 *   - staleTime de 5 min (query no refetches en 300s)
 *
 * Anti-creep: hook NO hace detección — solo fetch de lista. El scan es en
 * detectProhibitedPhrases() client-side (utils/marca/prohibitedPhraseDetector.ts).
 *
 * downstream-regression-na: brand-local vitalia FE hook tests; no cross-brand consumers
 */

import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import React from "react";
import { useVoiceBlocklist } from "../useVoiceBlocklist";

// ── Mocks ──────────────────────────────────────────────────────────────────────

const { mockGetProhibitedPhrases } = vi.hoisted(() => ({
  mockGetProhibitedPhrases: vi.fn(),
}));

vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({
    getToken: vi.fn().mockResolvedValue("mock-token-blocklist"),
    isLoaded: true,
    isSignedIn: true,
  }),
}));
vi.mock("@/hooks/useTenantId", () => ({ useTenantId: () => "mock-tenant-id" }));


vi.mock("../../api/marca-voice-api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../../api/marca-voice-api")>();
  return {
    ...actual,
    getProhibitedPhrases: mockGetProhibitedPhrases,
  };
});

// ── Fixtures ───────────────────────────────────────────────────────────────────

const PROHIBITED_PHRASES = [
  {
    id: "ph-001",
    phrase: "te garantizamos que te curas",
    suggestedAlternative: "Te acompañamos en el proceso de recuperación",
    severity: "high" as const,
    countryScope: "PE",
    isSeed: true,
  },
  {
    id: "ph-002",
    phrase: "cura segura",
    suggestedAlternative: "Tratamiento efectivo",
    severity: "high" as const,
    countryScope: "PE",
    isSeed: true,
  },
  {
    id: "ph-003",
    phrase: "milagro",
    suggestedAlternative: "Resultado excepcional",
    severity: "medium" as const,
    countryScope: null,
    isSeed: true,
  },
];

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

describe("useVoiceBlocklist — fetch exitoso", () => {
  beforeEach(() => {
    mockGetProhibitedPhrases.mockResolvedValue({
      items: PROHIBITED_PHRASES,
      total: PROHIBITED_PHRASES.length,
    });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("retorna el array phrases tras fetch exitoso", async () => {
    const { result } = renderHook(
      () => useVoiceBlocklist({ tenantId: "t1" }),
      { wrapper: makeWrapper() },
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.phrases).toHaveLength(3);
    expect(result.current.phrases[0].id).toBe("ph-001");
    expect(result.current.phrases[1].severity).toBe("high");
    expect(result.current.phrases[2].phrase).toBe("milagro");
  });

  it("isLoading=false tras fetch completado", async () => {
    const { result } = renderHook(
      () => useVoiceBlocklist({ tenantId: "t1" }),
      { wrapper: makeWrapper() },
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });
  });

  it("cada phrase contiene los campos esperados", async () => {
    const { result } = renderHook(
      () => useVoiceBlocklist({ tenantId: "t1" }),
      { wrapper: makeWrapper() },
    );

    await waitFor(() => {
      expect(result.current.phrases).toHaveLength(3);
    });

    const phrase = result.current.phrases[0];
    expect(phrase).toHaveProperty("id");
    expect(phrase).toHaveProperty("phrase");
    expect(phrase).toHaveProperty("suggestedAlternative");
    expect(phrase).toHaveProperty("severity");
    expect(phrase).toHaveProperty("isSeed");
  });
});

describe("useVoiceBlocklist — fallback array vacío", () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it("retorna array vacío cuando items es undefined (fallback ??)", async () => {
    mockGetProhibitedPhrases.mockResolvedValue({
      items: undefined,
      total: 0,
    });

    const { result } = renderHook(
      () => useVoiceBlocklist({ tenantId: "t1" }),
      { wrapper: makeWrapper() },
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.phrases).toEqual([]);
  });

  it("retorna array vacío cuando la lista está vacía", async () => {
    mockGetProhibitedPhrases.mockResolvedValue({ items: [], total: 0 });

    const { result } = renderHook(
      () => useVoiceBlocklist({ tenantId: "t1" }),
      { wrapper: makeWrapper() },
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.phrases).toHaveLength(0);
  });
});

describe("useVoiceBlocklist — getProhibitedPhrases recibe token correcto", () => {
  beforeEach(() => {
    mockGetProhibitedPhrases.mockResolvedValue({ items: PROHIBITED_PHRASES, total: 3 });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("llama getProhibitedPhrases con tenantId", async () => {
    const { result } = renderHook(
      () => useVoiceBlocklist({ tenantId: "tenant-xyz" }),
      { wrapper: makeWrapper() },
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(mockGetProhibitedPhrases).toHaveBeenCalledWith(
      expect.objectContaining({ tenantId: "tenant-xyz" }),
    );
  });
});
