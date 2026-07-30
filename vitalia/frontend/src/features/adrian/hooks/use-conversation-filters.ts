// cap: adrian.inbox
// story-origin: TBD
"use client";

/**
 * use-conversation-filters.ts — Derives React Query filter shape from nuqs URL state.
 *
 * Bridges the InboxUrlState (nuqs, URL-centric) to the ConversationsFilters shape
 * expected by useConversations React Query hook.
 *
 * Returns a stable object reference (via useMemo) to prevent unnecessary re-renders
 * and query re-fetches when URL state hasn't changed.
 *
 * downstream-regression-na: brand-local FE hook; no cross-brand consumers
 */

import { useMemo } from "react";
import { useInboxUrlState } from "../lib/url-state";
import type { ConversationsFilters } from "@/features/crm-shared";

/** URL mode value → API handler_mode filter value */
const URL_MODE_TO_API: Record<string, string> = {
  "adrian-decide": "ai",
  "adrian-consulta": "ai",
  "yo-escribo": "human",
};

/** URL status value → API status filter value */
const URL_STATUS_TO_API: Record<string, string> = {
  active: "active",
  "waiting-deposit": "paused",
  "nps-pending": "paused",
  closed: "closed",
};

/** URL stage value → API stage filter value */
const URL_STAGE_TO_API: Record<string, string> = {
  interested: "interesado",
  considering: "considerando",
  "ready-to-book": "listo",
  "decided-no": "decidio_no",
};

/**
 * Converts the current nuqs URL state into a ConversationsFilters object
 * suitable for the useConversations React Query hook.
 */
export function useConversationFilters(): ConversationsFilters {
  const [urlState] = useInboxUrlState();

  return useMemo<ConversationsFilters>(
    () => ({
      channel: urlState.channel ?? null,
      status: urlState.status
        ? (URL_STATUS_TO_API[urlState.status] ?? null)
        : null,
      stage: urlState.stage ? (URL_STAGE_TO_API[urlState.stage] ?? null) : null,
      mode: urlState.mode ? (URL_MODE_TO_API[urlState.mode] ?? null) : null,
      period: urlState.period ?? null,
      helpNeeded: urlState.helpNeeded ?? null,
      unreadMedia: urlState.unreadMedia ?? null,
      search: urlState.search ?? null,
    }),
    [
      urlState.channel,
      urlState.status,
      urlState.stage,
      urlState.mode,
      urlState.period,
      urlState.helpNeeded,
      urlState.unreadMedia,
      urlState.search,
    ],
  );
}
