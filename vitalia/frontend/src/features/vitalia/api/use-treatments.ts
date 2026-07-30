// cap: shell-organism.shell-vitalia
// story-origin: TBD
"use client";

import { useAuth } from "@clerk/nextjs";
import { useQuery } from "@tanstack/react-query";
import { vitaliaFetch } from "@/lib/fetch-client";
import type { TreatmentListResponse } from "../types/treatment.types";
import { vitaliaQueryKeys } from "./query-keys";

export function useTreatments() {
  const { getToken, isLoaded, isSignedIn, sessionClaims } = useAuth();

  return useQuery({
    queryKey: vitaliaQueryKeys.treatments.list(),
    queryFn: async (): Promise<TreatmentListResponse> => {
      const token = await getToken();
      const tenantId = (
        sessionClaims?.public_metadata as Record<string, unknown>
      )?.active_tenant_id as string | undefined;
      if (!token) throw new Error("Not authenticated");
      return vitaliaFetch<TreatmentListResponse>("/api/v1/vitalia/treatments", {
        token,
        tenantId: tenantId ?? "",
      });
    },
    enabled: isLoaded && isSignedIn === true,
  });
}
