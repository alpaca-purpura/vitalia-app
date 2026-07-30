// cap: onboarding.clinic-onboarding-3step
// story-origin: TBD
"use client";
/**
 * use-wizard-completion.ts — Mutation hook for completing onboarding.
 *
 * Calls POST /api/v1/vitalia/wizard/drafts/{draftId}/complete
 * On success: invalidates all wizard queries + triggers completion transition.
 *
 * downstream-regression-na: brand-local FE hook; no cross-brand consumers
 */

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useAuth, useOrganization } from "@clerk/nextjs";
import { completeOnboarding } from "../api/wizard-onboarding-api";
import { wizardQueryKeys } from "./use-wizard-onboarding-state";
import type { CompleteOnboardingResponse } from "../types/wizard-onboarding.types";

export interface UseWizardCompletionOptions {
  draftId: string;
  onSuccess?: (result: CompleteOnboardingResponse) => void;
  onError?: (error: Error) => void;
}

export function useWizardCompletion({
  draftId,
  onSuccess,
  onError,
}: UseWizardCompletionOptions) {
  const { getToken } = useAuth();
  const { organization } = useOrganization();
  const queryClient = useQueryClient();

  return useMutation<CompleteOnboardingResponse, Error, void>({
    mutationFn: async () => {
      const token = await getToken();
      if (!token) throw new Error("No autenticado");
      const tenantId = organization?.id;
      if (!tenantId) throw new Error("Organización no disponible");

      return completeOnboarding({ token, tenantId }, { draftId });
    },
    onSuccess: (result) => {
      // Invalidate all wizard queries — draft is now committed
      void queryClient.invalidateQueries({
        queryKey: wizardQueryKeys.all(),
      });
      onSuccess?.(result);
    },
    onError: (error) => {
      onError?.(error);
    },
  });
}
