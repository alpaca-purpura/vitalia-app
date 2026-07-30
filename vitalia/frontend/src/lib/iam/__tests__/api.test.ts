/**
 * lib/iam/api.ts unit tests — F1-S9 T-2 (TDD RED-first per tdd-mandatory.md)
 *
 * SC-5 gherkin coverage:
 *   - happy 200 → returns TenantSchema[]
 *   - 401 → throws IamApiError with code='unauthorized', status=401
 *   - 500 → throws IamApiError with code='unknown', status=500
 *   - AbortError (timeout) → throws IamApiError with code='network_failure'
 *   - empty array response → returns [] (NOT throws — Q6 edge: no-tenants is valid state)
 *
 * spec_anchor: 06-tickets.yaml T-2 gherkin_coverage + 04-validators.yaml val-fe-vitest-unit-iam-api
 * anti-duplication: fetchUserTenants consumes core GET /api/v1/iam/users/me/tenants (not duplicated)
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import type { TenantSchema } from "../types";

// Mock @clerk/nextjs/server before import (server-side module)
vi.mock("@clerk/nextjs/server", () => ({
  auth: vi.fn(),
}));

import { fetchUserTenants, IamApiError } from "../api";
import { auth } from "@clerk/nextjs/server";

const mockAuth = vi.mocked(auth);

const MOCK_TOKEN = "mock-clerk-jwt-token-12345";
const MOCK_TENANT: TenantSchema = {
  id: "clinic-abc-123",
  name: "Clínica San Rafael",
  slug: "clinica-san-rafael",
  role: "admin",
};

// Helper to mock auth().getToken()
function setupAuthMock(token: string | null = MOCK_TOKEN) {
  mockAuth.mockResolvedValue({
    getToken: vi.fn().mockResolvedValue(token),
  } as unknown as Awaited<ReturnType<typeof auth>>);
}

describe("fetchUserTenants — happy path (SC-5 network_failure related)", () => {
  let originalEnv: string | undefined;

  beforeEach(() => {
    originalEnv = process.env["NEXT_PUBLIC_API_URL"];
    vi.resetAllMocks();
  });

  afterEach(() => {
    if (originalEnv !== undefined) {
      process.env["NEXT_PUBLIC_API_URL"] = originalEnv;
    } else {
      delete process.env["NEXT_PUBLIC_API_URL"];
    }
  });

  it("happy 200 — returns TenantSchema[] on successful response", async () => {
    setupAuthMock(MOCK_TOKEN);
    const tenants: TenantSchema[] = [MOCK_TENANT];

    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => tenants,
      }),
    );

    const result = await fetchUserTenants("user-123");

    expect(result).toEqual(tenants);
    expect(result).toHaveLength(1);
    expect(result[0]?.id).toBe("clinic-abc-123");
    expect(result[0]?.name).toBe("Clínica San Rafael");
  });

  it("happy 200 empty array — returns [] (NOT throws; Q6: no-tenants is valid response)", async () => {
    setupAuthMock(MOCK_TOKEN);

    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => [],
      }),
    );

    const result = await fetchUserTenants("user-no-tenants");

    expect(result).toEqual([]);
    expect(Array.isArray(result)).toBe(true);
  });

  it("uses NEXT_PUBLIC_API_URL env var when set", async () => {
    process.env["NEXT_PUBLIC_API_URL"] = "http://vitalia-api.example.com";
    setupAuthMock(MOCK_TOKEN);

    const fetchSpy = vi.fn().mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => [MOCK_TENANT],
    });
    vi.stubGlobal("fetch", fetchSpy);

    await fetchUserTenants("user-123");

    expect(fetchSpy).toHaveBeenCalledWith(
      "http://vitalia-api.example.com/api/v1/iam/users/me/tenants",
      expect.any(Object),
    );
  });

  it("defaults to http://localhost:8002 when NEXT_PUBLIC_API_URL is not set", async () => {
    delete process.env["NEXT_PUBLIC_API_URL"];
    setupAuthMock(MOCK_TOKEN);

    const fetchSpy = vi.fn().mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => [],
    });
    vi.stubGlobal("fetch", fetchSpy);

    await fetchUserTenants("user-123");

    expect(fetchSpy).toHaveBeenCalledWith(
      "http://localhost:8002/api/v1/iam/users/me/tenants",
      expect.any(Object),
    );
  });

  it("sends Authorization Bearer header with Clerk token", async () => {
    setupAuthMock(MOCK_TOKEN);

    const fetchSpy = vi.fn().mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => [],
    });
    vi.stubGlobal("fetch", fetchSpy);

    await fetchUserTenants("user-123");

    expect(fetchSpy).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: `Bearer ${MOCK_TOKEN}`,
        }),
      }),
    );
  });

  it("sends cache: 'no-store' to prevent stale tenant list", async () => {
    setupAuthMock(MOCK_TOKEN);

    const fetchSpy = vi.fn().mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => [],
    });
    vi.stubGlobal("fetch", fetchSpy);

    await fetchUserTenants("user-123");

    expect(fetchSpy).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        cache: "no-store",
      }),
    );
  });
});

describe("fetchUserTenants — error paths (SC-5)", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it("401 — throws IamApiError with code='unauthorized' and status=401", async () => {
    setupAuthMock(MOCK_TOKEN);

    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 401,
        statusText: "Unauthorized",
      }),
    );

    const err = await fetchUserTenants("user-123").catch((e: unknown) => e);
    expect(err).toBeInstanceOf(IamApiError);
    expect(err).toMatchObject({
      code: "unauthorized",
      status: 401,
    });
  });

  it("403 — throws IamApiError with code='forbidden' and status=403", async () => {
    setupAuthMock(MOCK_TOKEN);

    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValueOnce({
        ok: false,
        status: 403,
        statusText: "Forbidden",
      }),
    );

    await expect(fetchUserTenants("user-123")).rejects.toMatchObject({
      code: "forbidden",
      status: 403,
    });
  });

  it("500 — throws IamApiError with code='unknown' and status=500", async () => {
    setupAuthMock(MOCK_TOKEN);

    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: "Internal Server Error",
      }),
    );

    await expect(fetchUserTenants("user-123")).rejects.toMatchObject({
      code: "unknown",
      status: 500,
    });
  });

  it("503 — throws IamApiError with code='unknown' and status=503", async () => {
    setupAuthMock(MOCK_TOKEN);

    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValueOnce({
        ok: false,
        status: 503,
        statusText: "Service Unavailable",
      }),
    );

    await expect(fetchUserTenants("user-123")).rejects.toMatchObject({
      code: "unknown",
      status: 503,
    });
  });

  it("AbortError (network timeout) — throws IamApiError with code='network_failure'", async () => {
    setupAuthMock(MOCK_TOKEN);

    const abortError = new DOMException(
      "The operation was aborted.",
      "AbortError",
    );
    vi.stubGlobal("fetch", vi.fn().mockRejectedValueOnce(abortError));

    await expect(fetchUserTenants("user-123")).rejects.toMatchObject({
      code: "network_failure",
    });
  });

  it("TypeError (DNS failure / network down) — throws IamApiError with code='network_failure'", async () => {
    setupAuthMock(MOCK_TOKEN);

    vi.stubGlobal(
      "fetch",
      vi.fn().mockRejectedValueOnce(new TypeError("Failed to fetch")),
    );

    await expect(fetchUserTenants("user-123")).rejects.toMatchObject({
      code: "network_failure",
    });
  });

  it("no Clerk token (null) — throws IamApiError with code='unauthorized'", async () => {
    setupAuthMock(null);

    await expect(fetchUserTenants("user-123")).rejects.toMatchObject({
      code: "unauthorized",
    });
  });

  it("IamApiError is instanceof Error (supports try/catch type narrowing)", async () => {
    setupAuthMock(MOCK_TOKEN);

    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValueOnce({
        ok: false,
        status: 401,
        statusText: "Unauthorized",
      }),
    );

    try {
      await fetchUserTenants("user-123");
      expect.fail("Should have thrown");
    } catch (err) {
      expect(err).toBeInstanceOf(Error);
      expect(err).toBeInstanceOf(IamApiError);
    }
  });
});
