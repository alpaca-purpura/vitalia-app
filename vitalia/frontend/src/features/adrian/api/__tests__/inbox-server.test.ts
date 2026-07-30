// cap: adrian.inbox
// story-origin: vitalia-fase2-adrian-inbox
/**
 * inbox-server.test.ts — RED-first tests for getInitialInboxState.
 * T-3 vitalia-fase2-adrian-inbox
 *
 * SC-7 (empty_state): when backend unavailable, returns empty fallback (no throw).
 * SC-8 (network_failure): on network error, returns empty fallback (graceful degradation).
 *
 * downstream-regression-na: brand-local server-side tests; no cross-brand consumers
 */

import { describe, it, expect, vi, beforeEach } from "vitest";

// Mock @clerk/nextjs/server before importing the module under test
vi.mock("@clerk/nextjs/server", () => ({
  auth: vi.fn(),
}));

// Import after mock declaration
import { getInitialInboxState } from "../inbox-server";
import { auth } from "@clerk/nextjs/server";

const mockAuth = vi.mocked(auth);

function setupValidToken(token = "mock-token") {
  mockAuth.mockResolvedValue({
    getToken: vi.fn().mockResolvedValue(token),
  } as unknown as Awaited<ReturnType<typeof auth>>);
}

function setupNoToken() {
  mockAuth.mockResolvedValue({
    getToken: vi.fn().mockResolvedValue(null),
  } as unknown as Awaited<ReturnType<typeof auth>>);
}

beforeEach(() => {
  vi.clearAllMocks();
  global.fetch = vi.fn();
});

describe("getInitialInboxState — SC-7 empty_state (graceful degradation)", () => {
  it("returns empty fallback when token is null (unauthenticated)", async () => {
    setupNoToken();

    const result = await getInitialInboxState({
      tenantId: "tenant-123",
      convId: null,
      filter: null,
    });

    expect(result).toMatchObject({
      conversations: [],
      detail: null,
    });
    expect(result.tenantId).toBe("tenant-123");
  });

  it("returns empty fallback when BE returns non-2xx", async () => {
    setupValidToken();
    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: false,
      status: 503,
      statusText: "Service Unavailable",
    });

    const result = await getInitialInboxState({
      tenantId: "tenant-xyz",
      convId: null,
      filter: "sin-leer",
    });

    expect(result.conversations).toEqual([]);
    expect(result.detail).toBeNull();
  });
});

describe("getInitialInboxState — SC-8 network_failure", () => {
  it("does NOT throw on network error — returns empty fallback", async () => {
    setupValidToken();
    (global.fetch as ReturnType<typeof vi.fn>).mockRejectedValue(
      new Error("Network error"),
    );

    await expect(
      getInitialInboxState({
        tenantId: "tenant-abc",
        convId: null,
        filter: null,
      }),
    ).resolves.toMatchObject({
      conversations: [],
      detail: null,
    });
  });

  it("returns empty fallback on auth() rejection", async () => {
    mockAuth.mockRejectedValue(new Error("Auth service unavailable"));

    const result = await getInitialInboxState({
      tenantId: "tenant-def",
      convId: null,
      filter: null,
    });

    expect(result.conversations).toEqual([]);
    expect(result.detail).toBeNull();
  });
});

describe("getInitialInboxState — shape contract", () => {
  it("returns valid InitialInboxState shape on success", async () => {
    setupValidToken();
    const mockConversations = [
      {
        id: "conv-1",
        tenantId: "tenant-123",
        clinicId: "clinic-1",
        channel: "whatsapp",
        handlerMode: "ai",
        proposalRequired: false,
        updatedAt: "2026-06-03T10:00:00Z",
      },
    ];
    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: true,
      json: vi.fn().mockResolvedValue({ conversations: mockConversations }),
    });

    const result = await getInitialInboxState({
      tenantId: "tenant-123",
      convId: null,
      filter: null,
    });

    expect(result.conversations).toHaveLength(1);
    expect(result.conversations[0]).toHaveProperty("id", "conv-1");
    expect(result.detail).toBeNull();
    expect(result.tenantId).toBe("tenant-123");
  });
});
