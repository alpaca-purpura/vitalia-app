// cap: shell-organism.shell-vitalia
// story-origin: TBD
"use client";

import { useAuth } from "@clerk/nextjs";
import { useQuery } from "@tanstack/react-query";
import { vitaliaFetch } from "@/lib/fetch-client";
import type { TreatmentDetailResponse } from "../types/treatment.types";
import { vitaliaQueryKeys } from "./query-keys";

export function useTreatment(id: string) {
  const { getToken, isLoaded, isSignedIn, sessionClaims } = useAuth();

  return useQuery({
    queryKey: vitaliaQueryKeys.treatments.detail(id),
    queryFn: async (): Promise<TreatmentDetailResponse> => {
      const token = await getToken();
      const tenantId = (
        sessionClaims?.public_metadata as Record<string, unknown>
      )?.active_tenant_id as string | undefined;
      if (!token) throw new Error("Not authenticated");
      return vitaliaFetch<TreatmentDetailResponse>(
        `/api/v1/vitalia/treatments/${id}`,
        { token, tenantId: tenantId ?? "" },
      );
    },
    enabled: isLoaded && isSignedIn === true && Boolean(id),
  });
}
