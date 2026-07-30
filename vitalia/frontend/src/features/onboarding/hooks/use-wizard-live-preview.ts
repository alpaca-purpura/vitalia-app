// cap: onboarding.clinic-onboarding-3step
// story-origin: TBD
"use client";
/**
 * use-wizard-live-preview.ts — Debounced live preview simulation hook.
 *
 * Calls POST /api/v1/vitalia/wizard/drafts/{draftId}/simulate
 * Debounces 1500ms after slot confirm to avoid hammering LLM endpoint.
 *
 * Per spec 03-arch-fe.md: "LivePreview debounced 1.5s after slot confirm".
 *
 * downstream-regression-na: brand-local FE hook; no cross-brand consumers
 */

import { useCallback, useEffect, useRef, useState } from "react";
import { useAuth, useOrganization } from "@clerk/nextjs";
import { simulateVoice } from "../api/wizard-onboarding-api";
import type {
  SimulateVoiceRequest,
  SimulateVoiceResponse,
} from "../types/wizard-onboarding.types";

const DEBOUNCE_MS = 1_500;

export interface LivePreviewState {
  isLoading: boolean;
  data: SimulateVoiceResponse | null;
  error: string | null;
  lastUpdatedAt: string | null;
}

export interface UseWizardLivePreviewOptions {
  draftId: string | null;
  /** When profilePartial changes, triggers debounced re-simulation */
  profilePartial: Record<string, unknown> | null;
  /** Whether to trigger simulation (false = panel hidden) */
  enabled?: boolean;
}

export function useWizardLivePreview({
  draftId,
  profilePartial,
  enabled = true,
}: UseWizardLivePreviewOptions): LivePreviewState & {
  triggerSimulate: (payload: SimulateVoiceRequest) => void;
} {
  const { getToken } = useAuth();
  const { organization } = useOrganization();

  const [state, setState] = useState<LivePreviewState>({
    isLoading: false,
    data: null,
    error: null,
    lastUpdatedAt: null,
  });

  const debounceTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const profileRef = useRef(profilePartial);
  profileRef.current = profilePartial;

  const executeSimulate = useCallback(
    async (payload: SimulateVoiceRequest) => {
      if (!draftId) return;

      const token = await getToken();
      if (!token) return;
      const tenantId = organization?.id;
      if (!tenantId) return;

      setState((prev) => ({ ...prev, isLoading: true, error: null }));
      try {
        const result = await simulateVoice(
          { token, tenantId },
          draftId,
          payload,
        );
        setState({
          isLoading: false,
          data: result,
          error: null,
          lastUpdatedAt: new Date().toISOString(),
        });
      } catch (err) {
        setState((prev) => ({
          ...prev,
          isLoading: false,
          error:
            err instanceof Error
              ? err.message
              : "Error al generar vista previa",
        }));
      }
    },
    [draftId, getToken, organization],
  );

  /** Debounced trigger — replaces any pending simulation */
  const triggerSimulate = useCallback(
    (payload: SimulateVoiceRequest) => {
      if (!enabled || !draftId) return;

      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
      debounceTimerRef.current = setTimeout(() => {
        void executeSimulate(payload);
      }, DEBOUNCE_MS);
    },
    [enabled, draftId, executeSimulate],
  );

  // Auto-trigger when profilePartial changes (debounced)
  useEffect(() => {
    if (!enabled || !draftId || !profilePartial) return;

    triggerSimulate({
      profilePartial,
      scenario: "whatsapp_greeting",
    });

    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
    // intentional: JSON.stringify used to deep-compare profilePartial object — adding profilePartial directly would trigger on every render
  }, [JSON.stringify(profilePartial), enabled, draftId]);

  return { ...state, triggerSimulate };
}
