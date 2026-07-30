// cap: shell-organism.shell-vitalia
// story-origin: TBD
"use client";

import { useAuth } from "@clerk/nextjs";
import { useQuery } from "@tanstack/react-query";
import { vitaliaFetch } from "@/lib/fetch-client";
import type { BookingListResponse } from "../types/booking.types";
import { vitaliaQueryKeys } from "./query-keys";

export function useBookings(filters?: { status?: string }) {
  const { getToken, isLoaded, isSignedIn, sessionClaims } = useAuth();

  return useQuery({
    queryKey: vitaliaQueryKeys.bookings.list(filters),
    queryFn: async (): Promise<BookingListResponse> => {
      const token = await getToken();
      const tenantId = (
        sessionClaims?.public_metadata as Record<string, unknown>
      )?.active_tenant_id as string | undefined;
      if (!token) throw new Error("Not authenticated");
      const params = new URLSearchParams();
      if (filters?.status) params.set("status", filters.status);
      const query = params.toString() ? `?${params.toString()}` : "";
      return vitaliaFetch<BookingListResponse>(
        `/api/v1/vitalia/bookings${query}`,
        { token, tenantId: tenantId ?? "" },
      );
    },
    enabled: isLoaded && isSignedIn === true,
  });
}
