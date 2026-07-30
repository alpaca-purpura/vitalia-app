// cap: shell-organism.shell-vitalia
// story-origin: TBD
"use client";

import { useAuth } from "@clerk/nextjs";
import { useQuery } from "@tanstack/react-query";
import { vitaliaFetch } from "@/lib/fetch-client";
import type { AvailableSlotsResponse } from "../types/booking.types";
import { vitaliaQueryKeys } from "./query-keys";

export interface AvailableSlotsFilters {
  doctor_id: string;
  offer_id?: string;
  window_days?: number;
}

export function useBookingAvailability(filters: AvailableSlotsFilters) {
  const { getToken, isLoaded, isSignedIn, sessionClaims } = useAuth();

  return useQuery({
    queryKey: vitaliaQueryKeys.bookings.slots({
      doctor_id: filters.doctor_id,
      offer_id: filters.offer_id,
    }),
    queryFn: async (): Promise<AvailableSlotsResponse> => {
      const token = await getToken();
      const tenantId = (
        sessionClaims?.public_metadata as Record<string, unknown>
      )?.active_tenant_id as string | undefined;
      if (!token) throw new Error("Not authenticated");
      const params = new URLSearchParams({ doctor_id: filters.doctor_id });
      if (filters.offer_id) params.set("offer_id", filters.offer_id);
      if (filters.window_days)
        params.set("window_days", String(filters.window_days));
      return vitaliaFetch<AvailableSlotsResponse>(
        `/api/v1/vitalia/bookings/available-slots?${params.toString()}`,
        { token, tenantId: tenantId ?? "" },
      );
    },
    enabled: isLoaded && isSignedIn === true && Boolean(filters.doctor_id),
  });
}
