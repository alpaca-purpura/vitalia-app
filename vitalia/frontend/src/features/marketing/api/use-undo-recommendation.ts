// cap: public_landing.public-clinic-landing
// story-origin: TBD
/**
 * useUndoRecommendation — mutation: undo an approved recommendation (within undo window)
 * Requires Idempotency-Key header (BE enforced for POST mutations)
 * BE returns 410 Gone if undo window expired (UndoWindowExpiredError)
 * downstream-regression-na: brand-local FE hook; no cross-brand consumers
 */
"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "@clerk/nextjs";
import { useTenantId } from "@/hooks/useTenantId";
import { useClinicId } from "@/hooks/useClinicId";
import { fetchClient } from "@/lib/api/fetchClient";
import type { UndoRecommendationResponse } from "../types/lucas-recommendation";

export type UndoRecommendationVariables = {
  recId: string;
};

export function useUndoRecommendation() {
  const { getToken} = useAuth();
  const tenantId = useTenantId();
  const clinicId = useClinicId();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ recId }: UndoRecommendationVariables) => {
      const token = await getToken();
      if (!token || !tenantId) throw new Error("Not authenticated");
      return fetchClient<UndoRecommendationResponse>(
        `/api/v1/vitalia/marketing/recommendations/${encodeURIComponent(recId)}/undo`,
        {
          method: "POST",
          token,
          tenantId, clinicId,
          headers: {
            "Idempotency-Key": crypto.randomUUID(),
          },
        },
      );
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: ["marketing", "recommendations"],
      });
    },
  });
}
