// cap: patients.nps-tracking
// story-origin: TBD
"use client";

/**
 * use-pause-patient — Mutation hook for pausing a patient's follow-up.
 *
 * Endpoint: POST /api/v1/vitalia/fidelization/patients/{patientId}/pause
 *
 * downstream-regression-na: brand-local FE hook; no cross-brand consumers
 */

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "@clerk/nextjs";
import { useTenantId } from "@/hooks/useTenantId";
import { vitaliaFetch } from "@/lib/fetch-client";
import type {
  PausePatientRequest,
  PausePatientResponse,
} from "../types/re-engagement";

interface PausePatientArgs {
  patientId: string;
  payload: PausePatientRequest;
}

/**
 * Mutation for pausing follow-up on a patient.
 */
export function usePausePatient() {
  const queryClient = useQueryClient();
  const { getToken} = useAuth();
  const tenantId = useTenantId();

  return useMutation({
    mutationFn: async ({ patientId, payload }: PausePatientArgs) => {
      const token = await getToken();
      if (!token || !tenantId) throw new Error("Not authenticated");

      return vitaliaFetch<PausePatientResponse>(
        `/api/v1/vitalia/fidelization/patients/${patientId}/pause`,
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
