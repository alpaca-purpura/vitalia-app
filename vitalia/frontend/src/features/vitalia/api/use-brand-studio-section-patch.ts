// cap: shell-organism.shell-vitalia
// story-origin: TBD
"use client";

import { useAuth } from "@clerk/nextjs";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { vitaliaFetch } from "@/lib/fetch-client";
import { vitaliaQueryKeys } from "./query-keys";
import type { BrandStudioSection } from "./use-brand-studio-sections";

export interface PatchBrandStudioSectionPayload {
  section_type: "identity" | "contact" | "medical_team" | "testimonials";
  data: Record<string, unknown>;
}

export function useBrandStudioSectionPatch() {
  const { getToken, sessionClaims } = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (
      payload: PatchBrandStudioSectionPayload,
    ): Promise<BrandStudioSection> => {
      const token = await getToken();
      const tenantId = (
        sessionClaims?.public_metadata as Record<string, unknown>
      )?.active_tenant_id as string | undefined;
      if (!token) throw new Error("Not authenticated");
      return vitaliaFetch<BrandStudioSection>(
        `/api/v1/vitalia/brand-studio/sections/${payload.section_type}`,
        {
          token,
          tenantId: tenantId ?? "",
          method: "PATCH",
          body: JSON.stringify({ data: payload.data }),
        },
      );
    },
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({
        queryKey: vitaliaQueryKeys.brandStudio.sections(),
      });
      queryClient.invalidateQueries({
        queryKey: vitaliaQueryKeys.brandStudio.section(variables.section_type),
      });
    },
  });
}
