// cap: public_landing.public-clinic-landing
// story-origin: TBD
/**
 * useBowtiesSummary — fetches bowtie funnel summary for a tenant+clinic
 * downstream-regression-na: brand-local FE hook; no cross-brand consumers
 */
"use client";

import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@clerk/nextjs";
import { useTenantId } from "@/hooks/useTenantId";
import { useClinicId } from "@/hooks/useClinicId";
import { fetchClient } from "@/lib/api/fetchClient";
import type { BowtieSummaryResponse } from "../types/bowtie";

export type UseBowtieSummaryOptions = {
  period?: "7d" | "30d" | "90d";
};

export function useBowtieSummary({
  period = "30d",
}: UseBowtieSummaryOptions = {}) {
  const { getToken, isLoaded, isSignedIn } = useAuth();
  const tenantId = useTenantId();
  const clinicId = useClinicId();

  return useQuery({
    queryKey: ["marketing", "bowtie", "summary", { period, clinicId }],
    queryFn: async () => {
      const token = await getToken();
      if (!token || !tenantId) throw new Error("Not authenticated");
      return fetchClient<BowtieSummaryResponse>(
        `/api/v1/vitalia/marketing/bowtie/summary?period=${period}`,
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
