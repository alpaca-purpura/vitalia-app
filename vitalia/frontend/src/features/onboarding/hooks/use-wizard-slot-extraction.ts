// cap: onboarding.clinic-onboarding-3step
// story-origin: TBD
"use client";
/**
 * use-wizard-slot-extraction.ts — Mutation hook for extracting tenant context.
 *
 * Calls POST /api/v1/vitalia/wizard/drafts/{draftId}/extract
 * Invalidates wizard draft query on success.
 *
 * Per tessl__graceful-degradation: AbortController timeout (30s for extraction — LLM call).
 *
 * downstream-regression-na: brand-local FE hook; no cross-brand consumers
 */

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useAuth, useOrganization } from "@clerk/nextjs";
import { extractContext } from "../api/wizard-onboarding-api";
import { wizardQueryKeys } from "./use-wizard-onboarding-state";
import type {
  ExtractContextRequest,
  ExtractContextResponse,
} from "../types/wizard-onboarding.types";

export interface UseWizardSlotExtractionOptions {
  draftId: string;
  onSuccess?: (result: ExtractContextResponse) => void;
  onError?: (error: Error) => void;
}

export function useWizardSlotExtraction({
  draftId,
  onSuccess,
  onError,
}: UseWizardSlotExtractionOptions) {
  const { getToken } = useAuth();
  const { organization } = useOrganization();
  const queryClient = useQueryClient();

  return useMutation<ExtractContextResponse, Error, ExtractContextRequest>({
    mutationFn: async (payload) => {
      const token = await getToken();
      if (!token) throw new Error("No autenticado");
      const tenantId = organization?.id;
      if (!tenantId) throw new Error("Organización no disponible");

      return extractContext({ token, tenantId }, draftId, payload);
    },
    onSuccess: (result) => {
      // Invalidate draft state so SlotTracker re-fetches updated slots
      void queryClient.invalidateQueries({
        queryKey: wizardQueryKeys.draft(draftId),
      });
      onSuccess?.(result);
    },
    onError: (error) => {
      onError?.(error);
    },
  });
}
