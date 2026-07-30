// cap: shell-organism.shell-vitalia
// story-origin: TBD
"use client";

import { useAuth } from "@clerk/nextjs";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { vitaliaFetch } from "@/lib/fetch-client";
import type { TreatmentSummary } from "../types/treatment.types";
import { vitaliaQueryKeys } from "./query-keys";

export interface TreatmentCreatePayload {
  booking_id: string;
  plan_template_slug: string;
  procedure_date: string;
}

export function useTreatmentCreate() {
  const { getToken, sessionClaims } = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (
      data: TreatmentCreatePayload,
    ): Promise<TreatmentSummary> => {
      const token = await getToken();
      const tenantId = (
        sessionClaims?.public_metadata as Record<string, unknown>
      )?.active_tenant_id as string | undefined;
      if (!token) throw new Error("Not authenticated");
      return vitaliaFetch<TreatmentSummary>("/api/v1/vitalia/treatments", {
        token,
        tenantId: tenantId ?? "",
        method: "POST",
        body: JSON.stringify(data),
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: vitaliaQueryKeys.treatments.list(),
      });
    },
  });
}
