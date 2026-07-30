// cap: shell-organism.shell-vitalia
// story-origin: TBD
"use client";

import { useAuth } from "@clerk/nextjs";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { vitaliaFetch } from "@/lib/fetch-client";
import type {
  RescheduleBookingRequest,
  RescheduleBookingResponse,
} from "../types/booking.types";
import { vitaliaQueryKeys } from "./query-keys";

export function useBookingReschedule(bookingId: string) {
  const { getToken, sessionClaims } = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (
      data: RescheduleBookingRequest,
    ): Promise<RescheduleBookingResponse> => {
      const token = await getToken();
      const tenantId = (
        sessionClaims?.public_metadata as Record<string, unknown>
      )?.active_tenant_id as string | undefined;
      if (!token) throw new Error("Not authenticated");
      return vitaliaFetch<RescheduleBookingResponse>(
        `/api/v1/vitalia/bookings/${bookingId}/reschedule`,
        {
          token,
          tenantId: tenantId ?? "",
          method: "POST",
          body: JSON.stringify(data),
        },
      );
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: vitaliaQueryKeys.bookings.detail(bookingId),
      });
      queryClient.invalidateQueries({
        queryKey: vitaliaQueryKeys.bookings.list(),
      });
    },
  });
}
