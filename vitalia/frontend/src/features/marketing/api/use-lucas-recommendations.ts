// cap: public_landing.public-clinic-landing
// story-origin: TBD
/**
 * useLucasRecommendations — fetches open recommendations for a tenant+clinic
 * downstream-regression-na: brand-local FE hook; no cross-brand consumers
 */
"use client";

import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@clerk/nextjs";
import { useTenantId } from "@/hooks/useTenantId";
import { useClinicId } from "@/hooks/useClinicId";
import { fetchClient } from "@/lib/api/fetchClient";
import type { LucasRecommendationsResponse } from "../types/lucas-recommendation";

export function useLucasRecommendations() {
  const { getToken, isLoaded, isSignedIn } = useAuth();
  const tenantId = useTenantId();
  const clinicId = useClinicId();

  return useQuery({
    queryKey: ["marketing", "recommendations", { clinicId }],
    queryFn: async () => {
      const token = await getToken();
      if (!token || !tenantId) throw new Error("Not authenticated");
      return fetchClient<LucasRecommendationsResponse>(
        "/api/v1/vitalia/marketing/recommendations",
        {
          token,
          tenantId,
          clinicId,
        },
      );
    },
    enabled: isLoaded && isSignedIn === true && Boolean(clinicId),
    staleTime: 30_000,
  });
}
