// cap: shell-organism.shell-vitalia
// story-origin: TBD
"use client";

import { useAuth } from "@clerk/nextjs";
import { useQuery } from "@tanstack/react-query";
import { vitaliaFetch } from "@/lib/fetch-client";
import type { PatientDetailResponse } from "../types/treatment.types";
import { vitaliaQueryKeys } from "./query-keys";

export function usePatient(id: string) {
  const { getToken, isLoaded, isSignedIn, sessionClaims } = useAuth();

  return useQuery({
    queryKey: vitaliaQueryKeys.patients.detail(id),
    queryFn: async (): Promise<PatientDetailResponse> => {
      const token = await getToken();
      const tenantId = (
        sessionClaims?.public_metadata as Record<string, unknown>
      )?.active_tenant_id as string | undefined;
      if (!token) throw new Error("Not authenticated");
      return vitaliaFetch<PatientDetailResponse>(
        `/api/v1/vitalia/patients/${id}`,
        { token, tenantId: tenantId ?? "" },
      );
    },
    enabled: isLoaded && isSignedIn === true && Boolean(id),
  });
}
