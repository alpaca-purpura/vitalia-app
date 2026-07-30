// cap: patients.nps-tracking
// story-origin: TBD
"use client";

/**
 * use-activity-stream — React Query hook for activity footer stream.
 *
 * Endpoint: GET /api/v1/vitalia/fidelization/activity?limit={limit}
 *
 * downstream-regression-na: brand-local FE hook; no cross-brand consumers
 */

import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@clerk/nextjs";
import { useTenantId } from "@/hooks/useTenantId";
import { vitaliaFetch } from "@/lib/fetch-client";

export interface ActivityEvent {
  id: string;
  eventType:
    | "template_sent"
    | "response_received"
    | "appointment_booked"
    | "patient_paused"
    | "manual_call_logged";
  patientId: string;
  /** Aggregate/anonymized description — NO PHI patient name */
  descriptionAnonymized: string;
  occurredAt: string;
}

export interface ActivityStreamResponse {
  events: ActivityEvent[];
}

/**
 * Fetches recent fidelización activity for footer stream.
 * Uses anonymized descriptions (NO PHI patient names in this endpoint).
 */
export function useActivityStream(limit: number = 20) {
  const { getToken, isLoaded, isSignedIn } = useAuth();
  const tenantId = useTenantId();

  return useQuery({
    queryKey: ["fidelizacion", "activity", limit],
    queryFn: async () => {
      const token = await getToken();
      if (!token || !tenantId) throw new Error("Not authenticated");

      return vitaliaFetch<ActivityStreamResponse>(
        `/api/v1/vitalia/fidelization/activity?limit=${limit}`,
        { token, tenantId },
      );
    },
    enabled: isLoaded && isSignedIn === true,
    staleTime: 30_000,
    refetchInterval: 30_000, // auto-refresh activity every 30s
  });
}
