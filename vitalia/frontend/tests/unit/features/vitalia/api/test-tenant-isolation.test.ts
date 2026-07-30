import { describe, it, expect, vi, beforeEach } from "vitest";

// Mock global fetch before importing fetchClient
const mockFetch = vi.fn();
global.fetch = mockFetch;

// Mock @clerk/nextjs auth — fetchClient reads session claims
vi.mock("@clerk/nextjs", () => ({
  auth: vi.fn(() => ({
    getToken: vi.fn(async () => "test-jwt-token"),
    sessionClaims: {
      public_metadata: {
        active_tenant_id: "tenant-aurora-dental-ar",
      },
    },
  })),
}));

describe("fetchClient — X-Tenant-ID auto-injection (A2 acceptance criteria)", () => {
  beforeEach(() => {
    mockFetch.mockReset();
    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => ({ result: "ok" }),
    });
  });

  it("injects X-Tenant-ID header from session claims", async () => {
    const { vitaliaFetch } = await import("@/lib/fetch-client");

    await vitaliaFetch("/api/v1/vitalia/onboarding/plans", {
      token: "test-jwt-token",
      tenantId: "tenant-aurora-dental-ar",
    });

    expect(mockFetch).toHaveBeenCalledOnce();
    const [, options] = mockFetch.mock.calls[0];
    expect(options.headers["X-Tenant-ID"]).toBe("tenant-aurora-dental-ar");
    expect(options.headers["Authorization"]).toBe("Bearer test-jwt-token");
  });

  it("sets Content-Type to application/json", async () => {
    const { vitaliaFetch } = await import("@/lib/fetch-client");

    await vitaliaFetch("/api/v1/vitalia/treatments", {
      token: "test-jwt-token",
      tenantId: "tenant-mindful-cl",
    });

    const [, options] = mockFetch.mock.calls[0];
    expect(options.headers["Content-Type"]).toBe("application/json");
  });

  it("throws ApiError on non-ok response", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 404,
      statusText: "Not Found",
      json: async () => ({ detail: "not found" }),
    });

    const { vitaliaFetch, ApiError } = await import("@/lib/fetch-client");

    await expect(
      vitaliaFetch("/api/v1/vitalia/treatments/missing-id", {
        token: "test-jwt-token",
        tenantId: "tenant-aurora-dental-ar",
      })
    ).rejects.toBeInstanceOf(ApiError);
  });

  it("passes custom options to fetch (method, body)", async () => {
    const { vitaliaFetch } = await import("@/lib/fetch-client");

    const body = JSON.stringify({ clinic_name: "Aurora Dental", clinic_type: "dental" });
    await vitaliaFetch("/api/v1/vitalia/onboarding/clinic-profile", {
      token: "test-jwt-token",
      tenantId: "tenant-aurora-dental-ar",
      method: "POST",
      body,
    });

    const [url, options] = mockFetch.mock.calls[0];
    expect(url).toBe("/api/v1/vitalia/onboarding/clinic-profile");
    expect(options.method).toBe("POST");
    expect(options.body).toBe(body);
  });
});
