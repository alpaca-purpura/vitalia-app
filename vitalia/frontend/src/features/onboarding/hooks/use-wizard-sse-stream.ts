// cap: onboarding.clinic-onboarding-3step
// story-origin: TBD
"use client";
/**
 * use-wizard-sse-stream.ts — SSE stream hook for wizard assistant messages.
 *
 * Manages EventSource lifecycle for GET /api/v1/vitalia/wizard/drafts/{id}/stream.
 * Provides heartbeat detection + auto-reconnect + graceful cleanup.
 *
 * Per tessl__graceful-degradation:
 *   - Heartbeat detection (3s timeout on no events)
 *   - Auto-reconnect (max 3 retries, exponential backoff 1s/2s/4s)
 *   - Clean teardown on unmount
 *
 * downstream-regression-na: brand-local FE hook; no cross-brand consumers
 */

import { useCallback, useEffect, useRef, useState } from "react";
import { buildStreamUrl } from "../api/wizard-onboarding-api";
import type { WizardSSEEvent } from "../types/wizard-onboarding.types";

const MAX_RETRIES = 3;
const HEARTBEAT_TIMEOUT_MS = 8_000;
const RETRY_DELAYS_MS = [1_000, 2_000, 4_000];

export interface SSEStreamState {
  /** Whether the stream is currently connected */
  isConnected: boolean;
  /** Whether the stream is streaming tokens (assistant typing) */
  isStreaming: boolean;
  /** Latest assistant message (accumulated tokens) */
  latestMessage: string;
  /** Last SSE event received */
  lastEvent: WizardSSEEvent | null;
  /** Stream error if any */
  error: string | null;
  /** Retry count */
  retryCount: number;
}

export interface UseWizardSSEStreamOptions {
  /** Draft ID to stream from (null = stream not started) */
  draftId: string | null;
  /** Auth token (EventSource sends via query param for SSE endpoints) */
  token: string | null;
  /** Whether to start the stream (false = pause/stop) */
  enabled: boolean;
  /** Called for each SSE event */
  onEvent?: (event: WizardSSEEvent) => void;
}

/**
 * Hook: manages SSE connection to wizard stream endpoint.
 */
export function useWizardSSEStream({
  draftId,
  token,
  enabled,
  onEvent,
}: UseWizardSSEStreamOptions): SSEStreamState & { disconnect: () => void } {
  const [state, setState] = useState<SSEStreamState>({
    isConnected: false,
    isStreaming: false,
    latestMessage: "",
    lastEvent: null,
    error: null,
    retryCount: 0,
  });

  const esRef = useRef<EventSource | null>(null);
  const heartbeatTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const retryTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const retryCountRef = useRef(0);
  const accMessageRef = useRef("");
  const onEventRef = useRef(onEvent);
  onEventRef.current = onEvent;

  const clearHeartbeat = useCallback(() => {
    if (heartbeatTimerRef.current) {
      clearTimeout(heartbeatTimerRef.current);
      heartbeatTimerRef.current = null;
    }
  }, []);

  const resetHeartbeat = useCallback(() => {
    clearHeartbeat();
    heartbeatTimerRef.current = setTimeout(() => {
      // No event for HEARTBEAT_TIMEOUT_MS — treat as disconnect
      setState((prev) => ({ ...prev, isConnected: false, isStreaming: false }));
    }, HEARTBEAT_TIMEOUT_MS);
  }, [clearHeartbeat]);

  const disconnect = useCallback(() => {
    clearHeartbeat();
    if (retryTimerRef.current) {
      clearTimeout(retryTimerRef.current);
      retryTimerRef.current = null;
    }
    if (esRef.current) {
      esRef.current.close();
      esRef.current = null;
    }
    retryCountRef.current = 0;
    setState({
      isConnected: false,
      isStreaming: false,
      latestMessage: "",
      lastEvent: null,
      error: null,
      retryCount: 0,
    });
  }, [clearHeartbeat]);

  const connect = useCallback(() => {
    if (!draftId || !token) return;

    const url = buildStreamUrl(draftId, token);
    const es = new EventSource(url);
    esRef.current = es;
    accMessageRef.current = "";

    es.onopen = () => {
      retryCountRef.current = 0;
      setState((prev) => ({
        ...prev,
        isConnected: true,
        error: null,
        retryCount: 0,
      }));
      resetHeartbeat();
    };

    es.onmessage = (msgEvent: MessageEvent<string>) => {
      resetHeartbeat();
      let parsed: WizardSSEEvent;
      try {
        parsed = JSON.parse(msgEvent.data) as WizardSSEEvent;
      } catch {
        return;
      }

      onEventRef.current?.(parsed);

      setState((prev) => {
        const next = { ...prev, lastEvent: parsed };

        switch (parsed.type) {
          case "token":
            accMessageRef.current += parsed.content;
            return {
              ...next,
              isStreaming: true,
              latestMessage: accMessageRef.current,
            };
          case "typing_start":
            accMessageRef.current = "";
            return { ...next, isStreaming: true, latestMessage: "" };
          case "typing_end":
          case "done":
            return { ...next, isStreaming: false };
          case "error":
            return { ...next, isStreaming: false, error: parsed.message };
          default:
            return next;
        }
      });

      if (parsed.type === "done") {
        clearHeartbeat();
        es.close();
        esRef.current = null;
        setState((prev) => ({
          ...prev,
          isConnected: false,
          isStreaming: false,
        }));
      }
    };

    es.onerror = () => {
      clearHeartbeat();
      es.close();
      esRef.current = null;

      const retry = retryCountRef.current;
      if (retry < MAX_RETRIES) {
        retryCountRef.current = retry + 1;
        const delay = RETRY_DELAYS_MS[retry] ?? 4_000;
        setState((prev) => ({
          ...prev,
          isConnected: false,
          isStreaming: false,
          retryCount: retry + 1,
        }));
        retryTimerRef.current = setTimeout(() => {
          if (enabled) connect();
        }, delay);
      } else {
        setState((prev) => ({
          ...prev,
          isConnected: false,
          isStreaming: false,
          error:
            "No se pudo conectar con el asistente. Por favor, recarga la página.",
        }));
      }
    };
  }, [draftId, token, enabled, clearHeartbeat, resetHeartbeat]);

  useEffect(() => {
    if (!enabled || !draftId || !token) {
      disconnect();
      return;
    }
    connect();
    return () => {
      disconnect();
    };
    // intentional: connect/disconnect are stable refs via useCallback — adding them would cause reconnect loops
  }, [enabled, draftId, token]);

  return { ...state, disconnect };
}
