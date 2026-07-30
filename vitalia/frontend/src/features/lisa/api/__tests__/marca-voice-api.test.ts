// cap: brand_studio.lisa-marca
// story-origin: estabilizar-harness-e2e-lisa-marca
/**
 * marca-voice-api.test.ts — Vitest unit tests para el api-layer de Voz y tono.
 *
 * Foco (sub-bug #2, story estabilizar-harness-e2e-lisa-marca):
 *   updatePersonality MUST mandar el Clerk userId real como X-User-ID,
 *   NUNCA el tenantId (el tenant como actor de audit = bug HIPAA-lite "quién").
 *
 * Estos tests son HONESTOS por construcción: mockean la DEPENDENCIA (fetchClient)
 * y ejercen la función real updatePersonality. PROHIBIDO mockear updatePersonality
 * para "verificarla" (eso es el false-green RN-1 que esta misma story combate).
 *
 * spec_anchor: 06-tickets.yaml T-2 deliverables + 03-arch.md § PARTE D + 04-validators SC-6
 * downstream-regression-na: brand-local vitalia FE api-layer test; no cross-brand consumers
 */

import { describe, it, expect, beforeEach, vi } from "vitest";

// ── Mock de la dependencia (fetchClient), NO de la función bajo prueba ──────────
const { mockFetchClient } = vi.hoisted(() => ({
  mockFetchClient: vi.fn(),
}));

vi.mock("@/lib/api/fetchClient", () => ({
  fetchClient: mockFetchClient,
}));

import { updatePersonality } from "../marca-voice-api";
import type { PersonalityPatchPayload } from "../marca-voice-api";

// ── Fixtures ───────────────────────────────────────────────────────────────────

const CLERK_USER_ID = "user_2abcDEF1234567890";
const TENANT_ID = "11111111-2222-3333-4444-555555555555"; // UUID-shaped (Clerk org placeholder del bug)

const PAYLOAD: PersonalityPatchPayload = {
  archetype: "caregiver",
  soISpeak: "Con calidez y empatía clínica.",
};

function headersOf(callIndex = 0): Record<string, string> {
  const [, options] = mockFetchClient.mock.calls[callIndex] as [
    string,
    { headers?: Record<string, string> },
  ];
  return options.headers ?? {};
}

// ── Tests ──────────────────────────────────────────────────────────────────────

describe("updatePersonality — actor de audit real (X-User-ID = Clerk userId)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockFetchClient.mockResolvedValue({});
  });

  it("manda X-User-ID === opts.userId (Clerk userId real)", async () => {
    await updatePersonality(
      { token: "t", tenantId: TENANT_ID, userId: CLERK_USER_ID, userRole: "owner" },
      PAYLOAD,
    );

    expect(mockFetchClient).toHaveBeenCalledTimes(1);
    expect(headersOf()["X-User-ID"]).toBe(CLERK_USER_ID);
  });

  it("NUNCA manda el tenantId como X-User-ID (el bug sub-bug #2)", async () => {
    await updatePersonality(
      { token: "t", tenantId: TENANT_ID, userId: CLERK_USER_ID },
      PAYLOAD,
    );

    expect(headersOf()["X-User-ID"]).not.toBe(TENANT_ID);
  });

  it("preserva X-User-Role para el RBAC guard (default 'owner')", async () => {
    await updatePersonality(
      { token: "t", tenantId: TENANT_ID, userId: CLERK_USER_ID },
      PAYLOAD,
    );
    expect(headersOf()["X-User-Role"]).toBe("owner");
  });

  it("respeta el userRole explícito cuando se provee", async () => {
    await updatePersonality(
      { token: "t", tenantId: TENANT_ID, userId: CLERK_USER_ID, userRole: "admin_clinic" },
      PAYLOAD,
    );
    expect(headersOf()["X-User-Role"]).toBe("admin_clinic");
  });

  it("usa método PATCH sobre /api/v1/lisa/marca/personality", async () => {
    await updatePersonality(
      { token: "t", tenantId: TENANT_ID, userId: CLERK_USER_ID },
      PAYLOAD,
    );
    const [url, options] = mockFetchClient.mock.calls[0] as [
      string,
      { method?: string },
    ];
    expect(url).toBe("/api/v1/lisa/marca/personality");
    expect(options.method).toBe("PATCH");
  });
});

describe("updatePersonality — guard sin actor (no mutación anónima)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockFetchClient.mockResolvedValue({});
  });

  it("lanza Error si userId es null (no manda un actor falso)", async () => {
    await expect(
      updatePersonality(
        { token: "t", tenantId: TENANT_ID, userId: null },
        PAYLOAD,
      ),
    ).rejects.toThrow();
    expect(mockFetchClient).not.toHaveBeenCalled();
  });

  it("lanza Error si userId es undefined (no fallback a tenantId)", async () => {
    await expect(
      updatePersonality({ token: "t", tenantId: TENANT_ID }, PAYLOAD),
    ).rejects.toThrow();
    expect(mockFetchClient).not.toHaveBeenCalled();
  });
});
