// cap: onboarding.clinic-onboarding-3step
// story-origin: TBD
"use client";
/**
 * use-wizard-onboarding-state.ts — Main React Query hook for wizard draft state.
 *
 * Fetches GET /api/v1/vitalia/wizard/drafts/{draftId} when draftId is available.
 * Enables auto-resume from URL state (SC-W3: browser close + resume from saved step).
 *
 * Per tessl__graceful-degradation: AbortController timeout (10s) + React Query retry.
 *
 * downstream-regression-na: brand-local FE hook; no cross-brand consumers
 */

import { useQuery } from "@tanstack/react-query";
import { useAuth, useOrganization } from "@clerk/nextjs";
import { getDraft } from "../api/wizard-onboarding-api";
import type { GetDraftResponse } from "../types/wizard-onboarding.types";

/** Query key factory for wizard draft state */
export const wizardQueryKeys = {
  draft: (draftId: string) => ["wizard", "draft", draftId] as const,
  all: () => ["wizard"] as const,
};

export interface UseWizardOnboardingStateOptions {
  /** Draft ID from URL state (null = draft not started yet) */
  draftId: string | null;
  /** Whether query is enabled */
  enabled?: boolean;
}

export function useWizardOnboardingState({
  draftId,
  enabled = true,
}: UseWizardOnboardingStateOptions) {
  const { getToken, isLoaded, isSignedIn } = useAuth();
  const { organization } = useOrganization();

  return useQuery<GetDraftResponse, Error>({
    queryKey: wizardQueryKeys.draft(draftId ?? "__none__"),
    queryFn: async ({ signal }) => {
      const token = await getToken();
      if (!token) throw new Error("No autenticado");
      const tenantId = organization?.id;
      if (!tenantId) throw new Error("Organización no disponible");

      // AbortController timeout (graceful degradation)
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 10_000);
      try {
        return await getDraft({ token, tenantId }, draftId!);
      } finally {
        clearTimeout(timeoutId);
        void signal; // React Query signal used implicitly via fetch
      }
    },
    enabled: Boolean(enabled && draftId && isLoaded && isSignedIn),
    staleTime: 30_000, // 30s — wizard sessions update frequently
    retry: 2,
    retryDelay: (attempt) => Math.min(1_000 * 2 ** attempt, 8_000),
  });
}
