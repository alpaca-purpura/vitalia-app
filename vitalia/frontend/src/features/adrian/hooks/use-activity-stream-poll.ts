// cap: adrian.inbox
// story-origin: TBD
"use client";

/**
 * use-activity-stream-poll.ts — Orchestrates polling enablement for AgentActivityStream.
 *
 * Reads expandedActivityStream from inbox-store Zustand and the current
 * conversationId from nuqs URL state. Passes the derived `enabled` flag
 * to useActivityStream.
 *
 * Separating this logic from the component keeps AgentActivityStream thin
 * and makes the polling behavior independently testable.
 *
 * downstream-regression-na: brand-local FE hook; no cross-brand consumers
 */

import { useInboxStore } from "../store/inbox-store";
import { useInboxUrlState } from "../lib/url-state";
import { useActivityStream } from "../api/use-activity-stream";
import type { ActivityStreamResponse } from "../api/use-activity-stream";
import type { UseQueryResult } from "@tanstack/react-query";

export interface UseActivityStreamPollResult extends Pick<
  UseQueryResult<ActivityStreamResponse>,
  "data" | "isLoading" | "isError" | "error"
> {
  /** Whether polling is currently active */
  isPolling: boolean;
}

/**
 * Orchestrates activity stream polling based on expanded state + selected conversation.
 *
 * Usage in AgentActivityStream component:
 *   const { data, isLoading, isPolling } = useActivityStreamPoll();
 */
export function useActivityStreamPoll(): UseActivityStreamPollResult {
  const expandedActivityStream = useInboxStore((s) => s.expandedActivityStream);
  const [{ conv: conversationId }] = useInboxUrlState();

  const query = useActivityStream(conversationId, expandedActivityStream);

  return {
    data: query.data,
    isLoading: query.isLoading,
    isError: query.isError,
    error: query.error,
    isPolling: expandedActivityStream && !!conversationId,
  };
}
