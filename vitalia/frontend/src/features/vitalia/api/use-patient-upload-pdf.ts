// cap: shell-organism.shell-vitalia
// story-origin: TBD
"use client";

import { useAuth } from "@clerk/nextjs";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { vitaliaFetch } from "@/lib/fetch-client";
import type {
  UploadMedicalPdfRequest,
  UploadMedicalPdfResponse,
} from "../types/treatment.types";
import { vitaliaQueryKeys } from "./query-keys";

export function usePatientUploadPdf(patientId: string) {
  const { getToken, sessionClaims } = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (
      data: UploadMedicalPdfRequest,
    ): Promise<UploadMedicalPdfResponse> => {
      const token = await getToken();
      const tenantId = (
        sessionClaims?.public_metadata as Record<string, unknown>
      )?.active_tenant_id as string | undefined;
      if (!token) throw new Error("Not authenticated");
      return vitaliaFetch<UploadMedicalPdfResponse>(
        `/api/v1/vitalia/patients/${patientId}/upload-medical-pdf`,
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
        queryKey: vitaliaQueryKeys.patients.detail(patientId),
      });
    },
  });
}
