/**
 * use-transcribe-audio.test.ts — Tests for useTranscribeAudio hook.
 *
 * Covers:
 * - SC-01: Happy path — audio blob uploaded, transcription returned
 * - SC-02: Low-confidence response returned (confidence < 0.5) — result still returned, UI handles
 * - Error path — server returns 4xx, hook surfaces error
 * - PHI safety: no PHI in outbound headers beyond tenant/clinic IDs
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor, act } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { createElement } from "react";
import { useTranscribeAudio } from "../use-transcribe-audio";
import type { TranscribeAudioResult } from "../use-transcribe-audio";

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

// Mock fetch (useTranscribeAudio uses raw fetch for multipart/form-data)
const mockFetch = vi.fn();
vi.stubGlobal("fetch", mockFetch);

const CONVERSATION_ID = "conv-transcribe-001";

const mockTranscribeResult: TranscribeAudioResult = {
  transcription_text:
    "Buenos días, quisiera información sobre el tratamiento dental.",
  transcription_confidence: 0.92,
  media_url: "https://cdn.vitalia.com/audio/abc123.webm",
};

const mockLowConfidenceResult: TranscribeAudioResult = {
  transcription_text: "...",
  transcription_confidence: 0.32,
  media_url: "https://cdn.vitalia.com/audio/abc456.webm",
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

describe("useTranscribeAudio", () => {
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

  it("SC-01: uploads audio blob and returns transcription with high confidence", async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => mockTranscribeResult,
    });

    const { result } = renderHook(() => useTranscribeAudio(), {
      wrapper: createWrapper(queryClient),
    });

    const audioBlob = new Blob(["fake-audio-data"], {
      type: "audio/webm;codecs=opus",
    });

    await act(async () => {
      result.current.mutate({
        conversationId: CONVERSATION_ID,
        audioBlob,
        mimeType: "audio/webm;codecs=opus",
      });
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual(mockTranscribeResult);
    expect(
      result.current.data?.transcription_confidence,
    ).toBeGreaterThanOrEqual(0.5);

    // Verify endpoint called correctly
    expect(mockFetch).toHaveBeenCalledOnce();
    const [url] = mockFetch.mock.calls[0] as [string, RequestInit];
    expect(url).toContain(`/conversations/${CONVERSATION_ID}/transcribe-audio`);
  });

  it("SC-02: returns low-confidence result (< 0.5) — UI layer responsible for fallback message", async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => mockLowConfidenceResult,
    });

    const { result } = renderHook(() => useTranscribeAudio(), {
      wrapper: createWrapper(queryClient),
    });

    const audioBlob = new Blob(["noisy-audio"], { type: "audio/webm" });

    await act(async () => {
      result.current.mutate({
        conversationId: CONVERSATION_ID,
        audioBlob,
      });
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    // Hook returns result as-is — UI is responsible for checking confidence < 0.5
    expect(result.current.data?.transcription_confidence).toBeLessThan(0.5);
    expect(result.current.data?.transcription_text).toBe("...");
  });

  it("surfaces error when server returns non-OK response", async () => {
    mockFetch.mockResolvedValue({
      ok: false,
      status: 422,
    });

    const { result } = renderHook(() => useTranscribeAudio(), {
      wrapper: createWrapper(queryClient),
    });

    const audioBlob = new Blob(["invalid-audio"], { type: "audio/webm" });

    await act(async () => {
      result.current.mutate({
        conversationId: CONVERSATION_ID,
        audioBlob,
      });
    });

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.error).toBeDefined();
  });

  it("PHI safety: Authorization header present, no PHI in headers", async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => mockTranscribeResult,
    });

    const { result } = renderHook(() => useTranscribeAudio(), {
      wrapper: createWrapper(queryClient),
    });

    const audioBlob = new Blob(["audio"], { type: "audio/webm" });

    await act(async () => {
      result.current.mutate({
        conversationId: CONVERSATION_ID,
        audioBlob,
      });
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    const [, options] = mockFetch.mock.calls[0] as [string, RequestInit];
    const headers = options.headers as Record<string, string>;

    // Auth + tenant scoping headers present
    expect(headers["Authorization"]).toBe("Bearer mock-token");
    expect(headers["X-Tenant-ID"]).toBe("mock-tenant-id");
    expect(headers["X-Clinic-ID"]).toBe("clinic-abc");

    // No PHI (patient name, diagnosis, etc.) in headers
    const headerValues = Object.values(headers).join(" ").toLowerCase();
    expect(headerValues).not.toContain("patient");
    expect(headerValues).not.toContain("diagnosis");
  });
});
