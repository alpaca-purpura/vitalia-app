// cap: patients.nps-tracking
// story-origin: TBD
"use client";

/**
 * use-availability-slots — Availability slots hook for suggest slots modal.
 *
 * NOTE: features/agenda module does not exist yet.
 * Placeholder hook that fetches from appointments API directly.
 * When /agenda feature is built, replace with re-export from @/features/agenda.
 *
 * Endpoint: GET /api/v1/vitalia/scheduling/availability?doctorId={d}&from={from}&days={days}
 *
 * downstream-regression-na: brand-local FE hook; no cross-brand consumers
 */

import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@clerk/nextjs";
import { useTenantId } from "@/hooks/useTenantId";
import { vitaliaFetch } from "@/lib/fetch-client";

export interface AvailabilitySlot {
  id: string;
  doctorId: string;
  doctorName: string;
  startsAt: string;
  durationMinutes: number;
  specialtyLabel: string;
}

export interface AvailabilitySlotsResponse {
  slots: AvailabilitySlot[];
}

interface UseAvailabilitySlotsArgs {
  doctorId: string | null;
  /** Number of days ahead to search */
  daysAhead?: number;
  enabled?: boolean;
}

/**
 * Fetches available appointment slots for suggest slots modal.
 */
export function useAvailabilitySlots({
  doctorId,
  daysAhead = 14,
  enabled = true,
}: UseAvailabilitySlotsArgs) {
  const { getToken, isLoaded, isSignedIn } = useAuth();
  const tenantId = useTenantId();

  return useQuery({
    queryKey: ["fidelizacion", "availability-slots", doctorId, daysAhead],
    queryFn: async () => {
      const token = await getToken();
      if (!token || !tenantId) throw new Error("Not authenticated");

      const params = new URLSearchParams({ days: String(daysAhead) });
      if (doctorId) params.set("doctor_id", doctorId);

      return vitaliaFetch<AvailabilitySlotsResponse>(
        `/api/v1/vitalia/scheduling/availability?${params.toString()}`,
        { token, tenantId },
      );
    },
    enabled: isLoaded && isSignedIn === true && enabled,
    staleTime: 60_000,
  });
}
