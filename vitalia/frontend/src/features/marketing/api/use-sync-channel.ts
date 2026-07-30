// cap: public_landing.public-clinic-landing
// story-origin: TBD
/**
 * useSyncChannel — mutation: trigger manual sync for a channel provider
 * Requires Idempotency-Key header (BE enforced for POST mutations)
 * downstream-regression-na: brand-local FE hook; no cross-brand consumers
 */
"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "@clerk/nextjs";
import { useTenantId } from "@/hooks/useTenantId";
import { useClinicId } from "@/hooks/useClinicId";
import { fetchClient } from "@/lib/api/fetchClient";
import type { ProviderSlug, SyncResponse } from "../types/channel";

export type UseSyncChannelVariables = {
  provider: ProviderSlug;
};

export function useSyncChannel() {
  const { getToken} = useAuth();
  const tenantId = useTenantId();
  const clinicId = useClinicId();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ provider }: UseSyncChannelVariables) => {
      const token = await getToken();
      if (!token || !tenantId) throw new Error("Not authenticated");
      return fetchClient<SyncResponse>(
        `/api/v1/vitalia/marketing/channels/${encodeURIComponent(provider)}/sync`,
        {
          method: "POST",
          token,
          tenantId, clinicId,
          headers: {
            "Idempotency-Key": crypto.randomUUID(),
          },
        },
      );
    },
    onSuccess: (_data, variables) => {
      void queryClient.invalidateQueries({
        queryKey: ["marketing", "channels", variables.provider],
      });
    },
  });
}
