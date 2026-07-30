/**
 * use-attach-media.test.ts — Tests for useAttachMedia hook.
 *
 * Covers:
 * - SC-01: Happy path — file uploaded, CDN media_url returned
 * - SC-02: Large file upload (image) — media_kind "image" returned
 * - Error path — server returns 4xx, hook surfaces error
 * - PHI safety: clinic-scoped headers present, no PHI in headers
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor, act } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { createElement } from "react";
import { useAttachMedia } from "../use-attach-media";
import type { AttachMediaResult } from "../use-attach-media";

// Mock Clerk
vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({
    getToken: vi.fn().mockResolvedValue("mock-token"),
    orgId: "org-test-tenant",
    isLoaded: true,
    isSignedIn: true,
  }),
}));
vi.mock("@/hooks/useTenantId", () => ({ useTenantId: () => "mock-tenant-id" }));


// Mock useClinicId
vi.mock("@/hooks/useClinicId", () => ({
  useClinicId: () => "clinic-abc",
}));

// Mock fetch (useAttachMedia uses raw fetch for multipart/form-data)
const mockFetch = vi.fn();
vi.stubGlobal("fetch", mockFetch);

const CONVERSATION_ID = "conv-attach-001";

const mockAudioResult: AttachMediaResult = {
  media_url: "https://cdn.vitalia.com/audio/abc123.webm",
  media_kind: "audio",
  size_bytes: 48_000,
  duration_s: 6,
};

const mockImageResult: AttachMediaResult = {
  media_url: "https://cdn.vitalia.com/images/def456.jpg",
  media_kind: "image",
  size_bytes: 512_000,
  duration_s: null,
};

function createWrapper(queryClient: QueryClient) {
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return createElement(
      QueryClientProvider,
      { client: queryClient },
      children,
    );
  };
}

describe("useAttachMedia", () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });
    vi.clearAllMocks();
  });

  it("SC-01: uploads audio file and returns CDN media_url with media_kind=audio", async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => mockAudioResult,
    });

    const { result } = renderHook(() => useAttachMedia(), {
      wrapper: createWrapper(queryClient),
    });

    const audioFile = new File(["fake-audio-data"], "recording.webm", {
      type: "audio/webm",
    });

    await act(async () => {
      result.current.mutate({
        conversationId: CONVERSATION_ID,
        file: audioFile,
      });
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual(mockAudioResult);
    expect(result.current.data?.media_kind).toBe("audio");
    expect(result.current.data?.media_url).toContain("cdn.vitalia.com");

    // Verify correct endpoint
    const [url] = mockFetch.mock.calls[0] as [string, RequestInit];
    expect(url).toContain(`/conversations/${CONVERSATION_ID}/attach`);
  });

  it("SC-02: uploads image file and returns media_kind=image with null duration_s", async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => mockImageResult,
    });

    const { result } = renderHook(() => useAttachMedia(), {
      wrapper: createWrapper(queryClient),
    });

    const imageFile = new File(["fake-image-data"], "photo.jpg", {
      type: "image/jpeg",
    });

    await act(async () => {
      result.current.mutate({
        conversationId: CONVERSATION_ID,
        file: imageFile,
      });
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data?.media_kind).toBe("image");
    expect(result.current.data?.duration_s).toBeNull();
    expect(result.current.data?.size_bytes).toBeGreaterThan(0);
  });

  it("surfaces error when server returns non-OK response", async () => {
    mockFetch.mockResolvedValue({
      ok: false,
      status: 413, // Payload too large
    });

    const { result } = renderHook(() => useAttachMedia(), {
      wrapper: createWrapper(queryClient),
    });

    const largeFile = new File(["too-large"], "big.jpg", {
      type: "image/jpeg",
    });

    await act(async () => {
      result.current.mutate({
        conversationId: CONVERSATION_ID,
        file: largeFile,
      });
    });

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.error).toBeDefined();
  });

  it("PHI safety: clinic-scoped headers present, no PHI in headers", async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => mockAudioResult,
    });

    const { result } = renderHook(() => useAttachMedia(), {
      wrapper: createWrapper(queryClient),
    });

    const file = new File(["data"], "attachment.webm", { type: "audio/webm" });

    await act(async () => {
      result.current.mutate({
        conversationId: CONVERSATION_ID,
        file,
      });
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    const [, options] = mockFetch.mock.calls[0] as [string, RequestInit];
    const headers = options.headers as Record<string, string>;

    // Dual filter headers present (tenant + clinic per hipaa-lite.md)
    expect(headers["Authorization"]).toBe("Bearer mock-token");
    expect(headers["X-Tenant-ID"]).toBe("mock-tenant-id");
    expect(headers["X-Clinic-ID"]).toBe("clinic-abc");

    // No PHI in headers
    const headerValues = Object.values(headers).join(" ").toLowerCase();
    expect(headerValues).not.toContain("patient");
    expect(headerValues).not.toContain("name");
    expect(headerValues).not.toContain("diagnosis");
  });
});
