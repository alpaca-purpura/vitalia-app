// cap: shell-organism.shell-vitalia
// story-origin: TBD
"use client";

import { useAuth } from "@clerk/nextjs";
import { useQuery } from "@tanstack/react-query";
import { vitaliaFetch } from "@/lib/fetch-client";
import { vitaliaQueryKeys } from "./query-keys";

export interface BrandStudioSection {
  section_id: string;
  section_type: "identity" | "contact" | "medical_team" | "testimonials";
  data: Record<string, unknown>;
  updated_at: string;
}

export interface BrandStudioSectionsResponse {
  sections: BrandStudioSection[];
  tenant_id: string;
}

export function useBrandStudioSections() {
  const { getToken, isLoaded, isSignedIn, sessionClaims } = useAuth();

  return useQuery({
    queryKey: vitaliaQueryKeys.brandStudio.sections(),
    queryFn: async (): Promise<BrandStudioSectionsResponse> => {
      const token = await getToken();
      const tenantId = (
        sessionClaims?.public_metadata as Record<string, unknown>
      )?.active_tenant_id as string | undefined;
      if (!token) throw new Error("Not authenticated");
      return vitaliaFetch<BrandStudioSectionsResponse>(
        "/api/v1/vitalia/brand-studio/sections",
        { token, tenantId: tenantId ?? "" },
      );
    },
    enabled: isLoaded && isSignedIn === true,
  });
}
