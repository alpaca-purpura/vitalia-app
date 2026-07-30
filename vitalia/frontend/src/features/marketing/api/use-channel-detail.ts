// cap: public_landing.public-clinic-landing
// story-origin: TBD
/**
 * useChannelDetail — fetches channel integration details for a provider
 * downstream-regression-na: brand-local FE hook; no cross-brand consumers
 */
"use client";

import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@clerk/nextjs";
import { useTenantId } from "@/hooks/useTenantId";
import { useClinicId } from "@/hooks/useClinicId";
import { fetchClient } from "@/lib/api/fetchClient";
import type { ProviderSlug, ChannelDetailResponse } from "../types/channel";

export type UseChannelDetailOptions = {
  provider: ProviderSlug;
};

export function useChannelDetail({ provider }: UseChannelDetailOptions) {
  const { getToken, isLoaded, isSignedIn } = useAuth();
  const tenantId = useTenantId();
  const clinicId = useClinicId();

  return useQuery({
    queryKey: ["marketing", "channels", provider, { clinicId }],
    queryFn: async () => {
      const token = await getToken();
      if (!token || !tenantId) throw new Error("Not authenticated");
      return fetchClient<ChannelDetailResponse[]>(
        `/api/v1/vitalia/marketing/channels/${encodeURIComponent(provider)}`,
        {
          token,
          tenantId,
          clinicId,
        },
      );
    },
    enabled: isLoaded && isSignedIn === true && Boolean(clinicId),
    staleTime: 30_000,
  });
}
