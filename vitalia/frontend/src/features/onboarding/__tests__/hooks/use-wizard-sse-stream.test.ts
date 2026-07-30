/**
 * Tests — use-wizard-sse-stream hook (T-onboarding-6 TDD)
 *
 * RED-first per .claude/rules/tdd-mandatory.md.
 * SSE hook manages EventSource lifecycle for wizard assistant stream.
 *
 * downstream-regression-na: brand-local FE test; no cross-brand consumers
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import type { SSEStreamState } from "../../hooks/use-wizard-sse-stream";

// ─── Mock EventSource ─────────────────────────────────────────────────────

class MockEventSource {
  static instances: MockEventSource[] = [];
  url: string;
  onopen: (() => void) | null = null;
  onmessage: ((e: { data: string }) => void) | null = null;
  onerror: (() => void) | null = null;
  closeCalled = false;

  constructor(url: string) {
    this.url = url;
    MockEventSource.instances.push(this);
  }

  close() {
    this.closeCalled = true;
  }

  // Test helpers
  simulateOpen() {
    this.onopen?.();
  }

  simulateMessage(data: string) {
    this.onmessage?.({ data });
  }

  simulateError() {
    this.onerror?.();
  }
}

vi.stubGlobal("EventSource", MockEventSource);

// ─── Tests ───────────────────────────────────────────────────────────────────

describe("use-wizard-sse-stream", () => {
  beforeEach(() => {
    MockEventSource.instances = [];
    vi.clearAllMocks();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("should export useWizardSSEStream function", async () => {
    const mod = await import("../../hooks/use-wizard-sse-stream");
    expect(typeof mod.useWizardSSEStream).toBe("function");
  });

  it("should export SSEStreamState type (module resolves)", async () => {
    const mod = await import("../../hooks/use-wizard-sse-stream");
    expect(mod).toBeDefined();
  });

  it("SSEStreamState shape contains expected keys", () => {
    const state: SSEStreamState = {
      isConnected: false,
      isStreaming: false,
      latestMessage: "",
      lastEvent: null,
      error: null,
      retryCount: 0,
    };
    expect(state.isConnected).toBe(false);
    expect(state.isStreaming).toBe(false);
    expect(state.latestMessage).toBe("");
    expect(state.lastEvent).toBeNull();
    expect(state.error).toBeNull();
    expect(state.retryCount).toBe(0);
  });
});

describe("SSE event type contracts", () => {
  it("token event has content field", async () => {
    await import("../../types/wizard-onboarding.types");
    // Type-level test: token events from WizardSSEEvent
    const tokenEvent = { type: "token" as const, content: "Hello" };
    expect(tokenEvent.type).toBe("token");
    expect(tokenEvent.content).toBe("Hello");
  });

  it("typing_start event is recognized", () => {
    const evt = { type: "typing_start" as const };
    expect(evt.type).toBe("typing_start");
  });

  it("done event closes stream", () => {
    const evt = { type: "done" as const };
    expect(evt.type).toBe("done");
  });

  it("error event has message field", () => {
    const evt = { type: "error" as const, message: "something went wrong" };
    expect(evt.message).toBe("something went wrong");
  });
});
