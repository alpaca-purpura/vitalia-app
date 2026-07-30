// cap: patients.nps-tracking
// story-origin: TBD
"use client";

/**
 * use-re-engagement-patterns — React Query hook for pattern listing per tab.
 *
 * Endpoint: GET /api/v1/vitalia/fidelization/re-engagement/patterns
 *   ?pattern={pattern}&period={period}&vertical={v}&doctorId={d}&urgency[]={u}
 *
 * downstream-regression-na: brand-local FE hook; no cross-brand consumers
 */

import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@clerk/nextjs";
import { useTenantId } from "@/hooks/useTenantId";
import { vitaliaFetch } from "@/lib/fetch-client";
import type {
  PatternListResponse,
  ReEngagementPattern,
  UrgencyLevel,
} from "../types/re-engagement";
import type { FidelizacionPeriod } from "../types/url-state";

interface UseReEngagementPatternsArgs {
  pattern: ReEngagementPattern;
  period: FidelizacionPeriod;
  vertical?: string | null;
  doctorId?: string | null;
  urgency?: UrgencyLevel[];
}

/**
 * Fetches re-engagement pattern rows for the active tab.
 */
export function useReEngagementPatterns(args: UseReEngagementPatternsArgs) {
  const { getToken, isLoaded, isSignedIn } = useAuth();
  const tenantId = useTenantId();

  return useQuery({
    queryKey: [
      "fidelizacion",
      "patterns",
      args.pattern,
      args.period,
      args.vertical,
      args.doctorId,
      args.urgency,
    ],
    queryFn: async () => {
      const token = await getToken();
      if (!token || !tenantId) throw new Error("Not authenticated");

      const params = new URLSearchParams({
        pattern: args.pattern,
        period: args.period,
      });

      if (args.vertical) params.set("vertical", args.vertical);
      if (args.doctorId) params.set("doctor_id", args.doctorId);
      if (args.urgency && args.urgency.length > 0) {
        args.urgency.forEach((u) => params.append("urgency", u));
      }

      return vitaliaFetch<PatternListResponse>(
        `/api/v1/vitalia/fidelization/re-engagement/patterns?${params.toString()}`,
        { token, tenantId },
      );
    },
    enabled: isLoaded && isSignedIn === true,
    staleTime: 30_000,
    refetchOnWindowFocus: true,
  });
}
