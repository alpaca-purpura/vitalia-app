// cap: patients.nps-tracking
// story-origin: TBD
"use client";

/**
 * use-nps-responses — React Query hook for NPS reduced table.
 *
 * Endpoint: GET /api/v1/vitalia/fidelization/nps/responses?period={period}
 *
 * downstream-regression-na: brand-local FE hook; no cross-brand consumers
 */

import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@clerk/nextjs";
import { useTenantId } from "@/hooks/useTenantId";
import { vitaliaFetch } from "@/lib/fetch-client";
import type { NPSSummaryResponse } from "../types/nps";
import type { FidelizacionPeriod } from "../types/url-state";

/**
 * Fetches NPS summary + reduced row list.
 */
export function useNpsResponses(period: FidelizacionPeriod) {
  const { getToken, isLoaded, isSignedIn } = useAuth();
  const tenantId = useTenantId();

  return useQuery({
    queryKey: ["fidelizacion", "nps", period],
    queryFn: async () => {
      const token = await getToken();
      if (!token || !tenantId) throw new Error("Not authenticated");

      return vitaliaFetch<NPSSummaryResponse>(
        `/api/v1/vitalia/fidelization/nps/responses?period=${period}`,
        { token, tenantId },
      );
    },
    enabled: isLoaded && isSignedIn === true,
    staleTime: 60_000,
  });
}
