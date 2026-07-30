// cap: adrian.inbox
// story-origin: TBD
"use client";

/**
 * use-tools-state.ts — React Query hook for agent tools state (read-only).
 *
 * Endpoint: GET /api/v1/vitalia/inbox/conversations/{conversationId}/tools
 *
 * Cached 30s — tools state changes infrequently (read-only for operator).
 * Displayed in AdrianToolsSheet (right-panel Shadcn Sheet).
 *
 * downstream-regression-na: brand-local FE hook; no cross-brand consumers
 */

import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@clerk/nextjs";
import { useTenantId } from "@/hooks/useTenantId";
import { useClinicId } from "@/hooks/useClinicId";
import { fetchClient } from "@/lib/api/fetchClient";
import { toolsStateKey } from "./_keys";
import type { ToolsState } from "../types/inbox.types";

/**
 * Fetches the agent tools state for a conversation.
 *
 * @param conversationId - The conversation to fetch tools for. Pass null to disable.
 */
export function useToolsState(conversationId: string | null | undefined) {
  const { getToken, isLoaded, isSignedIn } = useAuth();
  const tenantId = useTenantId();
  const clinicId = useClinicId();

  return useQuery({
    queryKey: toolsStateKey(conversationId ?? ""),
    queryFn: async () => {
      const token = await getToken();
      if (!token || !tenantId) throw new Error("Not authenticated");
      if (!conversationId) throw new Error("conversationId required");
      return fetchClient<ToolsState>(
        `/api/v1/vitalia/inbox/conversations/${conversationId}/tools`,
        { token, tenantId, clinicId },
      );
    },
    enabled: isLoaded && isSignedIn === true && !!conversationId,
    // Tools change infrequently — cache 30s
    staleTime: 30_000,
    refetchInterval: 30_000,
  });
}
