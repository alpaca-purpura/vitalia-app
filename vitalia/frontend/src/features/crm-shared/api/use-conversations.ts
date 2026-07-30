// cap: __shared__
// story-origin: TBD
"use client";

/**
 * use-conversations.ts — React Query hook for CRM conversations list.
 *
 * Endpoint: GET /api/v1/vitalia/crm/conversations
 * Supports filtering by channel, status, stage, mode, period, helpNeeded, unreadMedia, search.
 *
 * PHI constraint: name/phone/email come via Lead entity embedded in conversation
 * — rendered via PiiMaskedSpan in UI (not in this hook).
 *
 * downstream-regression-na: brand-local FE hook; no cross-brand consumers
 */

import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@clerk/nextjs";
import { useTenantId } from "@/hooks/useTenantId";
import { useClinicId } from "@/hooks/useClinicId";
import { fetchClient } from "@/lib/api/fetchClient";
import type { Conversation } from "../types";

export interface ConversationsFilters {
  channel?: string | null;
  status?: string | null;
  stage?: string | null;
  mode?: string | null;
  period?: string | null;
  helpNeeded?: boolean | null;
  unreadMedia?: boolean | null;
  search?: string | null;
  page?: number;
  pageSize?: number;
}

export interface ConversationsResponse {
  conversations: Conversation[];
  total: number;
  page: number;
  page_size: number;
}

function buildConversationsUrl(filters: ConversationsFilters): string {
  const params = new URLSearchParams();
  if (filters.channel) params.set("channel", filters.channel);
  if (filters.status) params.set("status", filters.status);
  if (filters.stage) params.set("stage", filters.stage);
  if (filters.mode) params.set("mode", filters.mode);
  if (filters.period) params.set("period", filters.period);
  if (filters.helpNeeded != null)
    params.set("help_needed", String(filters.helpNeeded));
  if (filters.unreadMedia != null)
    params.set("unread_media", String(filters.unreadMedia));
  if (filters.search) params.set("search", filters.search);
  if (filters.page != null) params.set("page", String(filters.page));
  if (filters.pageSize != null)
    params.set("page_size", String(filters.pageSize));
  const qs = params.toString();
  return `/api/v1/crm/conversations${qs ? `?${qs}` : ""}`;
}

/**
 * Fetches the paginated conversations list.
 *
 * @param filters - Optional URL-state derived filters (from useInboxUrlState)
 */
export function useConversations(filters: ConversationsFilters = {}) {
  const { getToken, isLoaded, isSignedIn } = useAuth();
  const tenantId = useTenantId();
  const clinicId = useClinicId();

  return useQuery({
    queryKey: ["crm", "conversations", filters],
    queryFn: async () => {
      const token = await getToken();
      if (!token || !tenantId) throw new Error("Not authenticated");
      // BE (crm ConversationListResponse) returns { items, total, limit, offset }.
      // Adapt to the FE ConversationsResponse shape { conversations, total, page, page_size }.
      const res = await fetchClient<{
        items: Conversation[];
        total: number;
        limit: number;
        offset: number;
      }>(buildConversationsUrl(filters), {
        token,
        tenantId,
        clinicId,
      });
      return {
        conversations: res.items,
        total: res.total,
        page: res.limit > 0 ? Math.floor(res.offset / res.limit) + 1 : 1,
        page_size: res.limit,
      } satisfies ConversationsResponse;
    },
    enabled: isLoaded && isSignedIn === true,
    staleTime: 15_000,
  });
}
