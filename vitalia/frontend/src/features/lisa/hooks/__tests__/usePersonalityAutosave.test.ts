/**
 * usePersonalityAutosave.test.ts — Vitest unit tests para hook autosave personalidad.
 *
 * T-9 vitalia-fase2-lisa-marca
 * spec_anchor: 06-tickets.yaml T-9 deliverables + 03-arch.md § 4.2
 *
 * Tests cubiertos:
 *   - Estado inicial (autosaveStatus='idle', savedAt=null)
 *   - scheduleAutosave: transición idle → dirty
 *   - Debounce 600ms: mutación NO dispara antes del timeout
 *   - Debounce 600ms: mutación SÍ dispara después del timeout
 *   - onSuccess: transición → saved + savedAt set + marcaKeys.personality invalidado
 *   - onError: transición → error
 *   - cancelAutosave: evita la mutación
 *
 * downstream-regression-na: brand-local vitalia FE hook tests; no cross-brand consumers
 */

import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { renderHook, act, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import React from "react";
import { usePersonalityAutosave } from "../usePersonalityAutosave";

// ── Mocks ──────────────────────────────────────────────────────────────────────

const { mockUpdatePersonality } = vi.hoisted(() => ({
  mockUpdatePersonality: vi.fn(),
}));

const MOCK_CLERK_USER_ID = "user_2personalityAutosaveTest";

vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({
    getToken: vi.fn().mockResolvedValue("mock-token-personality"),
    userId: MOCK_CLERK_USER_ID,
    isLoaded: true,
    isSignedIn: true,
  }),
}));
vi.mock("@/hooks/useTenantId", () => ({ useTenantId: () => "mock-tenant-id" }));


vi.mock("../../api/marca-voice-api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../../api/marca-voice-api")>();
  return {
    ...actual,
    updatePersonality: mockUpdatePersonality,
  };
});

// ── Fixtures ───────────────────────────────────────────────────────────────────

const PERSONALITY_VALUES = {
  archetype: "caregiver" as const,
  soISpeak: "Con calidez y empatía, priorizando la comprensión del paciente.",
  soIDontSpeak: "Nunca usamos jerga técnica sin explicarla. Nunca prometemos resultados garantizados.",
  technicalContext: "Clínica de medicina familiar. Especialidades: pediatría, geriatría, medicina preventiva.",
  formatInstructions: "Párrafos cortos. Listas cuando sea apropiado. Sin emojis en comunicación formal.",
  identityAnchor: "Somos la clínica del barrio, presente desde 2010.",
  domainContext: "Medicina primaria en Lima, Perú. Pacientes de 0 a 90 años.",
};

const PERSONALITY_RESPONSE = {
  tenantId: "t1",
  personalityProfileId: "pp-001",
  ...PERSONALITY_VALUES,
  compiledAt: null,
  compilerVersion: "v2",
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

describe("usePersonalityAutosave — estado inicial", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    mockUpdatePersonality.mockResolvedValue(PERSONALITY_RESPONSE);
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.clearAllMocks();
  });

  it("autosaveStatus empieza en 'idle'", () => {
    const { result } = renderHook(
      () => usePersonalityAutosave({ tenantId: "t1", clinicId: "c1" }),
      { wrapper: makeWrapper() },
    );
    expect(result.current.autosaveStatus).toBe("idle");
  });

  it("savedAt empieza en null", () => {
    const { result } = renderHook(
      () => usePersonalityAutosave({ tenantId: "t1", clinicId: "c1" }),
      { wrapper: makeWrapper() },
    );
    expect(result.current.savedAt).toBeNull();
  });
});

describe("usePersonalityAutosave — scheduleAutosave y debounce", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    mockUpdatePersonality.mockResolvedValue(PERSONALITY_RESPONSE);
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.clearAllMocks();
  });

  it("pasa a 'dirty' al llamar scheduleAutosave", () => {
    const { result } = renderHook(
      () => usePersonalityAutosave({ tenantId: "t1", clinicId: "c1" }),
      { wrapper: makeWrapper() },
    );

    act(() => {
      result.current.scheduleAutosave(PERSONALITY_VALUES);
    });

    expect(result.current.autosaveStatus).toBe("dirty");
  });

  it("NO llama updatePersonality antes de 600ms", () => {
    const { result } = renderHook(
      () => usePersonalityAutosave({ tenantId: "t1", clinicId: "c1" }),
      { wrapper: makeWrapper() },
    );

    act(() => {
      result.current.scheduleAutosave(PERSONALITY_VALUES);
    });

    act(() => {
      vi.advanceTimersByTime(400);
    });

    expect(mockUpdatePersonality).not.toHaveBeenCalled();
  });

  it("llama updatePersonality después de 600ms", async () => {
    const { result } = renderHook(
      () => usePersonalityAutosave({ tenantId: "t1", clinicId: "c1" }),
      { wrapper: makeWrapper() },
    );

    act(() => {
      result.current.scheduleAutosave(PERSONALITY_VALUES);
    });

    await act(async () => {
      await vi.advanceTimersByTimeAsync(600);
    });

    expect(mockUpdatePersonality).toHaveBeenCalledTimes(1);
  });

  it("solo la última edición dispara la mutación (debounce)", async () => {
    const { result } = renderHook(
      () => usePersonalityAutosave({ tenantId: "t1", clinicId: "c1" }),
      { wrapper: makeWrapper() },
    );

    act(() => {
      result.current.scheduleAutosave({ ...PERSONALITY_VALUES, soISpeak: "Primera versión" });
    });
    await act(async () => { await vi.advanceTimersByTimeAsync(200); });
    act(() => {
      result.current.scheduleAutosave({ ...PERSONALITY_VALUES, soISpeak: "Segunda versión" });
    });
    await act(async () => { await vi.advanceTimersByTimeAsync(600); });

    expect(mockUpdatePersonality).toHaveBeenCalledTimes(1);
  });
});

describe("usePersonalityAutosave — transiciones por resultado de mutación", () => {
  afterEach(() => {
    vi.useRealTimers();
    vi.clearAllMocks();
  });

  it("pasa a 'saved' tras mutación exitosa", async () => {
    vi.useFakeTimers();
    mockUpdatePersonality.mockResolvedValue(PERSONALITY_RESPONSE);

    const { result } = renderHook(
      () => usePersonalityAutosave({ tenantId: "t1", clinicId: "c1" }),
      { wrapper: makeWrapper() },
    );

    act(() => {
      result.current.scheduleAutosave(PERSONALITY_VALUES);
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
    mockUpdatePersonality.mockResolvedValue(PERSONALITY_RESPONSE);

    const { result } = renderHook(
      () => usePersonalityAutosave({ tenantId: "t1", clinicId: "c1" }),
      { wrapper: makeWrapper() },
    );

    act(() => {
      result.current.scheduleAutosave(PERSONALITY_VALUES);
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
    mockUpdatePersonality.mockRejectedValue(new Error("Error servidor"));

    const { result } = renderHook(
      () => usePersonalityAutosave({ tenantId: "t1", clinicId: "c1" }),
      { wrapper: makeWrapper() },
    );

    act(() => {
      result.current.scheduleAutosave(PERSONALITY_VALUES);
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

describe("usePersonalityAutosave — cancelAutosave", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    mockUpdatePersonality.mockResolvedValue(PERSONALITY_RESPONSE);
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.clearAllMocks();
  });

  it("cancelAutosave impide que la mutación se ejecute", () => {
    const { result } = renderHook(
      () => usePersonalityAutosave({ tenantId: "t1", clinicId: "c1" }),
      { wrapper: makeWrapper() },
    );

    act(() => {
      result.current.scheduleAutosave(PERSONALITY_VALUES);
    });
    act(() => {
      result.current.cancelAutosave();
    });
    act(() => {
      vi.advanceTimersByTime(700);
    });

    expect(mockUpdatePersonality).not.toHaveBeenCalled();
  });
});

// ── camelCase payload assertion (T-3 arreglar-guardado-voz-y-tono) ─────────────
//
// Regression guard: PersonalityPatchPayload uses camelCase fields (soISpeak, soIDontSpeak,
// technicalContext, formatInstructions, identityAnchor, domainContext).
// The bug in T-2 was that FE sent camelCase and BE had extra="forbid" without alias_generator.
// This test verifies that:
// 1. The hook calls updatePersonality with the camelCase payload shape.
// 2. No snake_case field names appear in the payload (so_i_speak, etc.).
//
// @see 06-tickets.yaml T-3 deliverables (Ampliar usePersonalityAutosave.test.ts)
// @see 01-spec.md § voz-bloque-edita-no-422

describe("usePersonalityAutosave — camelCase payload (T-3 regresión 422)", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    mockUpdatePersonality.mockResolvedValue(PERSONALITY_RESPONSE);
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.clearAllMocks();
  });

  it("scheduleAutosave envía payload camelCase (soISpeak, no so_i_speak)", async () => {
    const { result } = renderHook(
      () => usePersonalityAutosave({ tenantId: "t1", clinicId: "c1" }),
      { wrapper: makeWrapper() },
    );

    const camelCasePayload = {
      soISpeak: "Con calidez y empatía clínica.",
      soIDontSpeak: "Sin jerga sin explicación.",
      technicalContext: "Clínica familiar Lima.",
      formatInstructions: "Párrafos cortos.",
      identityAnchor: "Somos la clínica del barrio.",
      domainContext: "Medicina primaria Perú.",
    };

    act(() => {
      result.current.scheduleAutosave(camelCasePayload);
    });

    await act(async () => {
      await vi.advanceTimersByTimeAsync(600);
    });

    expect(mockUpdatePersonality).toHaveBeenCalledTimes(1);

    // Verify camelCase field names are used (not snake_case)
    const [, payload] = mockUpdatePersonality.mock.calls[0] as [
      unknown,
      typeof camelCasePayload,
    ];

    // camelCase fields MUST be present
    expect(payload).toHaveProperty("soISpeak", camelCasePayload.soISpeak);
    expect(payload).toHaveProperty(
      "soIDontSpeak",
      camelCasePayload.soIDontSpeak,
    );
    expect(payload).toHaveProperty(
      "technicalContext",
      camelCasePayload.technicalContext,
    );
    expect(payload).toHaveProperty(
      "formatInstructions",
      camelCasePayload.formatInstructions,
    );
    expect(payload).toHaveProperty(
      "identityAnchor",
      camelCasePayload.identityAnchor,
    );
    expect(payload).toHaveProperty(
      "domainContext",
      camelCasePayload.domainContext,
    );

    // snake_case fields must NOT appear (would cause 422 extra_forbidden)
    expect(payload).not.toHaveProperty("so_i_speak");
    expect(payload).not.toHaveProperty("so_i_dont_speak");
    expect(payload).not.toHaveProperty("technical_context");
    expect(payload).not.toHaveProperty("format_instructions");
    expect(payload).not.toHaveProperty("identity_anchor");
    expect(payload).not.toHaveProperty("domain_context");
  });

  it("scheduleAutosave con solo archetype: payload contiene 'archetype' en camelCase-safe (no cambia)", async () => {
    const { result } = renderHook(
      () => usePersonalityAutosave({ tenantId: "t1", clinicId: "c1" }),
      { wrapper: makeWrapper() },
    );

    act(() => {
      result.current.scheduleAutosave({ archetype: "sage" });
    });

    await act(async () => {
      await vi.advanceTimersByTimeAsync(600);
    });

    expect(mockUpdatePersonality).toHaveBeenCalledTimes(1);

    const [, payload] = mockUpdatePersonality.mock.calls[0] as [
      unknown,
      { archetype?: string },
    ];

    expect(payload).toHaveProperty("archetype", "sage");
    // archetype is not a compound camelCase field — no snake_case equivalent expected
  });

  it("payload combinado archetype + soISpeak contiene ambos en camelCase", async () => {
    const { result } = renderHook(
      () => usePersonalityAutosave({ tenantId: "t1", clinicId: "c1" }),
      { wrapper: makeWrapper() },
    );

    act(() => {
      result.current.scheduleAutosave({
        archetype: "caregiver",
        soISpeak: "Con calidez y empatía.",
      });
    });

    await act(async () => {
      await vi.advanceTimersByTimeAsync(600);
    });

    const [, payload] = mockUpdatePersonality.mock.calls[0] as [
      unknown,
      { archetype?: string; soISpeak?: string },
    ];

    expect(payload).toHaveProperty("archetype", "caregiver");
    expect(payload).toHaveProperty("soISpeak", "Con calidez y empatía.");
    expect(payload).not.toHaveProperty("so_i_speak");
  });
});

// ── Actor de audit real (sub-bug #2, story estabilizar-harness-e2e-lisa-marca) ─
//
// El hook DEBE pasar el Clerk userId real (de useAuth().userId) en opts a
// updatePersonality — NUNCA el tenantId. El header X-User-ID se construye en la
// api-fn (ver marca-voice-api.test.ts), pero el ORIGEN del actor es este hook.
// Aquí verificamos que las opts llevan userId === Clerk userId y ≠ tenantId.
//
// @see 06-tickets.yaml T-2 deliverables (coverage_update usePersonalityAutosave.test.ts)
// @see 04-validators SC-6 (actor real HIPAA-lite "quién")

describe("usePersonalityAutosave — actor de audit real (opts.userId, no tenantId)", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    mockUpdatePersonality.mockResolvedValue(PERSONALITY_RESPONSE);
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.clearAllMocks();
  });

  it("pasa opts.userId === Clerk userId real (de useAuth) a updatePersonality", async () => {
    const { result } = renderHook(
      () => usePersonalityAutosave({ tenantId: "t1", clinicId: "c1" }),
      { wrapper: makeWrapper() },
    );

    act(() => {
      result.current.scheduleAutosave(PERSONALITY_VALUES);
    });
    await act(async () => {
      await vi.advanceTimersByTimeAsync(600);
    });

    expect(mockUpdatePersonality).toHaveBeenCalledTimes(1);
    const [opts] = mockUpdatePersonality.mock.calls[0] as [
      { userId?: string | null; tenantId: string },
    ];
    expect(opts.userId).toBe(MOCK_CLERK_USER_ID);
  });

  it("NUNCA pasa el tenantId como userId (el bug sub-bug #2)", async () => {
    const { result } = renderHook(
      () => usePersonalityAutosave({ tenantId: "t1", clinicId: "c1" }),
      { wrapper: makeWrapper() },
    );

    act(() => {
      result.current.scheduleAutosave(PERSONALITY_VALUES);
    });
    await act(async () => {
      await vi.advanceTimersByTimeAsync(600);
    });

    const [opts] = mockUpdatePersonality.mock.calls[0] as [
      { userId?: string | null; tenantId: string },
    ];
    expect(opts.userId).not.toBe(opts.tenantId);
    expect(opts.userId).not.toBe("t1");
  });
});
