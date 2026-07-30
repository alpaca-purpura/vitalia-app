// cap: public_landing.public-clinic-landing
// story-origin: TBD
/**
 * useAttributionMatrix — fetches attribution matrix for a tenant+clinic
 * downstream-regression-na: brand-local FE hook; no cross-brand consumers
 * HIPAA-lite: NO PHI in UTM, NO patient names in attribution
 */
"use client";

import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@clerk/nextjs";
import { useTenantId } from "@/hooks/useTenantId";
import { useClinicId } from "@/hooks/useClinicId";
import { fetchClient } from "@/lib/api/fetchClient";
import type { AttributionMatrixResponse } from "../types/attribution";

export type UseAttributionMatrixOptions = {
  period?: "7d" | "30d" | "90d";
};

export function useAttributionMatrix({
  period = "30d",
}: UseAttributionMatrixOptions = {}) {
  const { getToken, isLoaded, isSignedIn } = useAuth();
  const tenantId = useTenantId();
  const clinicId = useClinicId();

  return useQuery({
    queryKey: ["marketing", "attribution", { period, clinicId }],
    queryFn: async () => {
      const token = await getToken();
      if (!token || !tenantId) throw new Error("Not authenticated");
      return fetchClient<AttributionMatrixResponse>(
        `/api/v1/vitalia/marketing/attribution-matrix?period=${period}`,
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
