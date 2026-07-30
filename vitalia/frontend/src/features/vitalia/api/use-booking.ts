// cap: shell-organism.shell-vitalia
// story-origin: TBD
"use client";

import { useAuth } from "@clerk/nextjs";
import { useQuery } from "@tanstack/react-query";
import { vitaliaFetch } from "@/lib/fetch-client";
import type { BookingSummary } from "../types/booking.types";
import { vitaliaQueryKeys } from "./query-keys";

export function useBooking(id: string) {
  const { getToken, isLoaded, isSignedIn, sessionClaims } = useAuth();

  return useQuery({
    queryKey: vitaliaQueryKeys.bookings.detail(id),
    queryFn: async (): Promise<BookingSummary> => {
      const token = await getToken();
      const tenantId = (
        sessionClaims?.public_metadata as Record<string, unknown>
      )?.active_tenant_id as string | undefined;
      if (!token) throw new Error("Not authenticated");
      return vitaliaFetch<BookingSummary>(`/api/v1/vitalia/bookings/${id}`, {
        token,
        tenantId: tenantId ?? "",
      });
    },
    enabled: isLoaded && isSignedIn === true && Boolean(id),
  });
}
