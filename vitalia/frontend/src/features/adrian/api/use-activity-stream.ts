// cap: adrian.inbox
// story-origin: TBD
"use client";

/**
 * use-activity-stream.ts — React Query polling hook for agent activity stream.
 *
 * Endpoint: GET /api/v1/vitalia/inbox/conversations/{conversationId}/activity-stream
 *
 * Key features:
 * - Polls every 5s when AgentActivityStream panel is expanded
 * - Controlled by `enabled` prop derived from inbox-store.expandedActivityStream
 * - Returns pre-sanitized ActivityEvent objects (PHI redacted server-side)
 *
 * PHI note: payload_redacted is pre-sanitized server-side via sanitize_payload().
 * FE never receives raw PHI in trace events.
 *
 * downstream-regression-na: brand-local FE hook; no cross-brand consumers
 */

import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@clerk/nextjs";
import { useTenantId } from "@/hooks/useTenantId";
import { useClinicId } from "@/hooks/useClinicId";
import { fetchClient } from "@/lib/api/fetchClient";
import { activityStreamKey } from "./_keys";
import type { ActivityEvent } from "../types/inbox.types";

export interface ActivityStreamResponse {
  events: ActivityEvent[];
  total: number;
}

const ACTIVITY_STREAM_POLL_INTERVAL_MS = 5_000;

/**
 * Fetches activity stream events for a conversation.
 *
 * @param conversationId - The conversation to watch. Pass null to disable.
 * @param enabled - Whether to enable polling (driven by expandedActivityStream Zustand flag).
 */
export function useActivityStream(
  conversationId: string | null | undefined,
  enabled: boolean = false,
) {
  const { getToken, isLoaded, isSignedIn } = useAuth();
  const tenantId = useTenantId();
  const clinicId = useClinicId();

  return useQuery({
    queryKey: activityStreamKey(conversationId ?? ""),
    queryFn: async () => {
      const token = await getToken();
      if (!token || !tenantId) throw new Error("Not authenticated");
      if (!conversationId) throw new Error("conversationId required");
      return fetchClient<ActivityStreamResponse>(
        `/api/v1/vitalia/inbox/conversations/${conversationId}/activity-stream`,
        { token, tenantId, clinicId },
      );
    },
    enabled: isLoaded && isSignedIn === true && !!conversationId && enabled,
    // Poll every 5s while expanded; stop when collapsed
    refetchInterval: enabled ? ACTIVITY_STREAM_POLL_INTERVAL_MS : false,
    // Keep previous data visible while polling (avoid flash)
    placeholderData: (prev) => prev,
    staleTime: 0,
  });
}
