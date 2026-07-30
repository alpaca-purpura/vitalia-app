// cap: patients.nps-tracking
// story-origin: TBD
"use client";

/**
 * use-log-manual-call — Mutation hook for logging a manual call.
 *
 * Endpoint: POST /api/v1/vitalia/fidelization/patients/{patientId}/log-call
 *
 * downstream-regression-na: brand-local FE hook; no cross-brand consumers
 */

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "@clerk/nextjs";
import { useTenantId } from "@/hooks/useTenantId";
import { vitaliaFetch } from "@/lib/fetch-client";
import type {
  LogManualCallRequest,
  LogManualCallResponse,
} from "../types/re-engagement";

interface LogManualCallArgs {
  patientId: string;
  payload: LogManualCallRequest;
}

/**
 * Mutation for logging a manual phone call to a patient.
 */
export function useLogManualCall() {
  const queryClient = useQueryClient();
  const { getToken} = useAuth();
  const tenantId = useTenantId();

  return useMutation({
    mutationFn: async ({ patientId, payload }: LogManualCallArgs) => {
      const token = await getToken();
      if (!token || !tenantId) throw new Error("Not authenticated");

      return vitaliaFetch<LogManualCallResponse>(
        `/api/v1/vitalia/fidelization/patients/${patientId}/log-call`,
        {
          token,
          tenantId, method: "POST",
          body: JSON.stringify(payload),
        },
      );
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["fidelizacion"] });
      void queryClient.invalidateQueries({
        queryKey: ["fidelizacion", "activity"],
      });
    },
  });
}
