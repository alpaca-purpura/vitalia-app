// cap: shell-organism.shell-vitalia
// story-origin: TBD
"use client";

import { useAuth } from "@clerk/nextjs";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { vitaliaFetch } from "@/lib/fetch-client";
import type { CreateClinicProfileResponse } from "../types/vitalia.types";
import { vitaliaQueryKeys } from "./query-keys";

export interface CreateClinicProfilePayload {
  clinic_name: string;
  clinic_type: "dental" | "psychology" | "psychiatry" | "wellness";
  country: string;
  city: string;
  plan_tier: string;
}

export function useClinicProfileCreate() {
  const { getToken, sessionClaims } = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (
      data: CreateClinicProfilePayload,
    ): Promise<CreateClinicProfileResponse> => {
      const token = await getToken();
      const tenantId = (
        sessionClaims?.public_metadata as Record<string, unknown>
      )?.active_tenant_id as string | undefined;
      if (!token) throw new Error("Not authenticated");
      return vitaliaFetch<CreateClinicProfileResponse>(
        "/api/v1/vitalia/onboarding/clinic-profile",
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
        queryKey: vitaliaQueryKeys.onboarding.status(),
      });
    },
  });
}
