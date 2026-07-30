// cap: public_landing.public-clinic-landing
// story-origin: TBD
/**
 * useStageDetail — fetches detailed metrics for a specific bowtie stage
 * downstream-regression-na: brand-local FE hook; no cross-brand consumers
 */
"use client";

import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@clerk/nextjs";
import { useTenantId } from "@/hooks/useTenantId";
import { useClinicId } from "@/hooks/useClinicId";
import { fetchClient } from "@/lib/api/fetchClient";
import type { RecommendationStage } from "../types/lucas-recommendation";
import type { StageDetailResponse } from "../types/bowtie";

export type UseStageDetailOptions = {
  stage: RecommendationStage;
  period?: "7d" | "30d" | "90d";
};

export function useStageDetail({
  stage,
  period = "30d",
}: UseStageDetailOptions) {
  const { getToken, isLoaded, isSignedIn } = useAuth();
  const tenantId = useTenantId();
  const clinicId = useClinicId();

  return useQuery({
    queryKey: ["marketing", "stage", stage, { period, clinicId }],
    queryFn: async () => {
      const token = await getToken();
      if (!token || !tenantId) throw new Error("Not authenticated");
      return fetchClient<StageDetailResponse>(
        `/api/v1/vitalia/marketing/stage/${encodeURIComponent(stage)}?period=${period}`,
        {
          token,
          tenantId, clinicId,
        },
      );
    },
    enabled: isLoaded && isSignedIn === true && Boolean(clinicId),
    staleTime: 60_000,
  });
}
