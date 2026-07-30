// cap: public_landing.public-clinic-landing
// story-origin: TBD
/**
 * useReferrals — fetches referrals data for a tenant+clinic
 * downstream-regression-na: brand-local FE hook; no cross-brand consumers
 * HIPAA-lite: topReferrers contains only referrerPatientIdHash (NEVER patient.name)
 */
"use client";

import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@clerk/nextjs";
import { useTenantId } from "@/hooks/useTenantId";
import { useClinicId } from "@/hooks/useClinicId";
import { fetchClient } from "@/lib/api/fetchClient";
import type { ReferralsResponse } from "../types/referrals";

export type UseReferralsOptions = {
  period?: "7d" | "30d" | "90d";
};

export function useReferrals({ period = "30d" }: UseReferralsOptions = {}) {
  const { getToken, isLoaded, isSignedIn } = useAuth();
  const tenantId = useTenantId();
  const clinicId = useClinicId();

  return useQuery({
    queryKey: ["marketing", "referrals", { period, clinicId }],
    queryFn: async () => {
      const token = await getToken();
      if (!token || !tenantId) throw new Error("Not authenticated");
      return fetchClient<ReferralsResponse>(
        `/api/v1/vitalia/marketing/referrals?period=${period}`,
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
