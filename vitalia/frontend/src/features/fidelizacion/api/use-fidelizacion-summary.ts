// cap: patients.nps-tracking
// story-origin: TBD
"use client";

/**
 * use-fidelizacion-summary — React Query hook for KPIs hero data.
 *
 * Endpoint: GET /api/v1/vitalia/fidelization/summary?period={period}
 * Auth: Clerk getToken() + (tenantId).
 *
 * downstream-regression-na: brand-local FE hook; no cross-brand consumers
 */

import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@clerk/nextjs";
import { useTenantId } from "@/hooks/useTenantId";
import { vitaliaFetch } from "@/lib/fetch-client";
import type { FidelizacionSummaryResponse } from "../types/fidelizacion-summary";
import type { FidelizacionPeriod } from "../types/url-state";

/**
 * Fetches aggregated KPIs summary for fidelización module.
 *
 * @param period - Time window filter ("7d" | "30d" | "90d")
 */
export function useFidelizacionSummary(period: FidelizacionPeriod) {
  const { getToken, isLoaded, isSignedIn } = useAuth();
  const tenantId = useTenantId();

  return useQuery({
    queryKey: ["fidelizacion", "summary", period],
    queryFn: async () => {
      const token = await getToken();
      if (!token || !tenantId) throw new Error("Not authenticated");

      return vitaliaFetch<FidelizacionSummaryResponse>(
        `/api/v1/vitalia/fidelization/summary?period=${period}`,
        { token, tenantId },
      );
    },
    enabled: isLoaded && isSignedIn === true,
    staleTime: 60_000, // 1 min
    refetchOnWindowFocus: true,
  });
}
