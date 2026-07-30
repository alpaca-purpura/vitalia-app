// cap: shell-organism.shell-vitalia
// story-origin: TBD
"use client";

import { useAuth } from "@clerk/nextjs";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { vitaliaFetch } from "@/lib/fetch-client";
import type {
  CreateBookingRequest,
  CreateBookingResponse,
} from "../types/booking.types";
import { vitaliaQueryKeys } from "./query-keys";

export function useBookingCreate() {
  const { getToken, sessionClaims } = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (
      data: CreateBookingRequest,
    ): Promise<CreateBookingResponse> => {
      const token = await getToken();
      const tenantId = (
        sessionClaims?.public_metadata as Record<string, unknown>
      )?.active_tenant_id as string | undefined;
      if (!token) throw new Error("Not authenticated");
      return vitaliaFetch<CreateBookingResponse>("/api/v1/vitalia/bookings", {
        token,
        tenantId: tenantId ?? "",
        method: "POST",
        body: JSON.stringify(data),
      });
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: vitaliaQueryKeys.bookings.slots({
          doctor_id: variables.doctor_id,
        }),
      });
      queryClient.invalidateQueries({
        queryKey: vitaliaQueryKeys.bookings.list(),
      });
    },
  });
}
