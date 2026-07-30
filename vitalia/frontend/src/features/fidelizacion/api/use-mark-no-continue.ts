// cap: patients.nps-tracking
// story-origin: TBD
"use client";

/**
 * use-mark-no-continue — Mutation hook for marking patient decided not to continue.
 *
 * Endpoint: POST /api/v1/vitalia/fidelization/patients/{patientId}/mark-no-continue
 *
 * downstream-regression-na: brand-local FE hook; no cross-brand consumers
 */

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "@clerk/nextjs";
import { useTenantId } from "@/hooks/useTenantId";
import { vitaliaFetch } from "@/lib/fetch-client";
import type {
  MarkNoContinueRequest,
  MarkNoContinueResponse,
} from "../types/re-engagement";

interface MarkNoContinueArgs {
  patientId: string;
  payload: MarkNoContinueRequest;
}

/**
 * Mutation for marking a patient as decided not to continue treatment.
 */
export function useMarkNoContinue() {
  const queryClient = useQueryClient();
  const { getToken} = useAuth();
  const tenantId = useTenantId();

  return useMutation({
    mutationFn: async ({ patientId, payload }: MarkNoContinueArgs) => {
      const token = await getToken();
      if (!token || !tenantId) throw new Error("Not authenticated");

      return vitaliaFetch<MarkNoContinueResponse>(
        `/api/v1/vitalia/fidelization/patients/${patientId}/mark-no-continue`,
        {
          token,
          tenantId, method: "POST",
          body: JSON.stringify(payload),
        },
      );
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["fidelizacion"] });
    },
  });
}
