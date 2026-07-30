// cap: shell-organism.shell-vitalia
// story-origin: TBD
"use client";

import { useAuth } from "@clerk/nextjs";
import { useQuery } from "@tanstack/react-query";
import { vitaliaFetch } from "@/lib/fetch-client";
import type { TreatmentFollowupStateResponse } from "../types/treatment.types";
import { vitaliaQueryKeys } from "./query-keys";

export function useTreatmentSnapshot(treatmentId: string) {
  const { getToken, isLoaded, isSignedIn, sessionClaims } = useAuth();

  return useQuery({
    queryKey: vitaliaQueryKeys.treatments.followup(treatmentId),
    queryFn: async (): Promise<TreatmentFollowupStateResponse> => {
      const token = await getToken();
      const tenantId = (
        sessionClaims?.public_metadata as Record<string, unknown>
      )?.active_tenant_id as string | undefined;
      if (!token) throw new Error("Not authenticated");
      return vitaliaFetch<TreatmentFollowupStateResponse>(
        `/api/v1/vitalia/treatments/${treatmentId}/followup`,
        { token, tenantId: tenantId ?? "" },
      );
    },
    enabled: isLoaded && isSignedIn === true && Boolean(treatmentId),
    refetchInterval: 1000 * 30, // Poll every 30s for followup state updates
  });
}
