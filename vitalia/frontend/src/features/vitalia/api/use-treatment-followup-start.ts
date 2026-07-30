// cap: shell-organism.shell-vitalia
// story-origin: TBD
"use client";

import { useAuth } from "@clerk/nextjs";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { vitaliaFetch } from "@/lib/fetch-client";
import type { StartFollowupRequest } from "../types/treatment.types";
import { vitaliaQueryKeys } from "./query-keys";

interface StartFollowupResponse {
  treatment_id: string;
  status: string;
  current_step: string;
}

export function useTreatmentFollowupStart(treatmentId: string) {
  const { getToken, sessionClaims } = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (
      data: StartFollowupRequest,
    ): Promise<StartFollowupResponse> => {
      const token = await getToken();
      const tenantId = (
        sessionClaims?.public_metadata as Record<string, unknown>
      )?.active_tenant_id as string | undefined;
      if (!token) throw new Error("Not authenticated");
      return vitaliaFetch<StartFollowupResponse>(
        `/api/v1/vitalia/treatments/${treatmentId}/start-followup`,
        {
          token,
          tenantId: tenantId ?? "",
          method: "POST",
          body: JSON.stringify(data),
        },
      );
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: vitaliaQueryKeys.treatments.detail(treatmentId),
      });
      queryClient.invalidateQueries({
        queryKey: vitaliaQueryKeys.treatments.followup(treatmentId),
      });
    },
  });
}
