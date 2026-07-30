// cap: shell-organism.shell-vitalia
// story-origin: TBD
"use client";

import { useAuth } from "@clerk/nextjs";
import { useQuery } from "@tanstack/react-query";
import { vitaliaFetch } from "@/lib/fetch-client";
import type { PatientListResponse } from "../types/treatment.types";
import { vitaliaQueryKeys } from "./query-keys";

export function usePatients(filters?: { clinic_type?: string }) {
  const { getToken, isLoaded, isSignedIn, sessionClaims } = useAuth();

  return useQuery({
    queryKey: vitaliaQueryKeys.patients.list(filters),
    queryFn: async (): Promise<PatientListResponse> => {
      const token = await getToken();
      const tenantId = (
        sessionClaims?.public_metadata as Record<string, unknown>
      )?.active_tenant_id as string | undefined;
      if (!token) throw new Error("Not authenticated");
      const params = new URLSearchParams();
      if (filters?.clinic_type) params.set("clinic_type", filters.clinic_type);
      const query = params.toString() ? `?${params.toString()}` : "";
      return vitaliaFetch<PatientListResponse>(
        `/api/v1/vitalia/patients${query}`,
        { token, tenantId: tenantId ?? "" },
      );
    },
    enabled: isLoaded && isSignedIn === true,
  });
}
