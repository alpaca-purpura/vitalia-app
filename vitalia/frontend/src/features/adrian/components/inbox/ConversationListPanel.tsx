// cap: adrian.inbox
// story-origin: TBD
/**
 * ConversationListPanel.tsx — Left pane container (320px) of the inbox layout.
 *
 * Composes:
 *   SearchInput (debounced 300ms, drives URL ?search=)
 *   FilterChips (channel/status/stage/mode/period/helpNeeded/unreadMedia → URL params)
 *   InboxConvList (React Query data, skeleton, empty states)
 *
 * URL state (nuqs) owned here via useInboxUrlState.
 * useConversationFilters bridges URL → React Query filters.
 * useConversations fetches paginated conversations list.
 *
 * "use client" required: useInboxUrlState (nuqs), useConversations (React Query),
 *   useInboxStore (Zustand), useState for local search debounce bridge.
 *
 * HIPAA-lite: patient names fetched separately via useLeads — passed as lookup fn.
 * PHI fields (name) are displayed using plain text since ConversationListPanel
 * only shows name preview. Full PHI masking applies in ConversationThread/ContactSidebar.
 *
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 */
"use client";

import { useEffect, useMemo } from "react";
import { useParams } from "next/navigation";
import { useInboxUrlState } from "../../lib/url-state";
import { useInboxStore } from "../../store/inbox-store";
import {
  getLastViewedConv,
  setLastViewedConv,
} from "../../lib/last-viewed-conv";
import { useConversationFilters } from "../../hooks/use-conversation-filters";
import { useConversations, useLeads } from "@/features/crm-shared";
import { SearchInput } from "./SearchInput";
import { FilterChips } from "./FilterChips";
import type { FilterChipsValue } from "./FilterChips";
import { InboxConvList } from "./InboxConvList";
import { INBOX_COPY } from "../../lib/copy";
import { cn } from "@/lib/cn";

interface ConversationListPanelProps {
  className?: string;
}

/**
 * ConversationListPanel — 320px left pane containing search + filters + list.
 *
 * Wires URL state (nuqs) ↔ React Query ↔ child components.
 * Handles loading / error / empty states per tessl__react-patterns baseline.
 */
export function ConversationListPanel({
  className,
}: ConversationListPanelProps) {
  const [urlState, setUrlState] = useInboxUrlState();
  const setActiveConvId = useInboxStore((s) => s.setActiveConvId);
  const activeConvId = useInboxStore((s) => s.activeConvId);
  const params = useParams();
  const tenantId =
    typeof params?.tenantId === "string" ? params.tenantId : "";
  const filters = useConversationFilters();
  const { data, isLoading, isError } = useConversations(filters);
  const { data: leadsData } = useLeads();

  const conversations = data?.conversations ?? [];

  // Auto-select on entry (UI-AUDIT #1): re-open the last conversation the operator
  // was viewing (persisted UUID) or, on a first visit, the newest one. Skips if a
  // conversation is already chosen (URL ?conv= or store) or the list is empty.
  useEffect(() => {
    if (isLoading) return;
    if (urlState.conv || activeConvId || conversations.length === 0) return;
    const persisted = tenantId ? getLastViewedConv(tenantId) : null;
    const target =
      persisted && conversations.some((c) => c.id === persisted)
        ? persisted
        : conversations[0]!.id;
    setActiveConvId(target);
    void setUrlState({ conv: target });
    if (tenantId) setLastViewedConv(tenantId, target);
    // setActiveConvId / setUrlState are stable; resolve only from the inputs below.
  }, [isLoading, urlState.conv, activeConvId, conversations, tenantId]);

  // Resolve patient names from leads (operator triage view). Names come from the
  // leads endpoint (server-side decrypted) and are shown to authorized operators.
  const leadNameById = useMemo(() => {
    const map = new Map<string, string>();
    for (const lead of leadsData?.leads ?? []) map.set(lead.id, lead.name);
    return map;
  }, [leadsData]);

  // Determine empty variant based on active filters
  function getEmptyVariant():
    | "noConversations"
    | "noHelpNeeded"
    | "noMediaUnread"
    | "noResultsFilter" {
    if (urlState.helpNeeded) return "noHelpNeeded";
    if (urlState.unreadMedia) return "noMediaUnread";
    const hasOtherFilter =
      urlState.channel !== null ||
      urlState.status !== null ||
      urlState.stage !== null ||
      urlState.mode !== null ||
      urlState.period !== null ||
      urlState.search !== null;
    if (hasOtherFilter) return "noResultsFilter";
    return "noConversations";
  }

  function handleClearFilters() {
    void setUrlState({
      channel: null,
      status: null,
      stage: null,
      mode: null,
      period: null,
      helpNeeded: null,
      unreadMedia: null,
      search: null,
    });
  }

  function handleSearchChange(val: string | null) {
    void setUrlState({ search: val });
  }

  function handleFiltersChange(next: FilterChipsValue) {
    void setUrlState({
      channel: next.channel,
      status: next.status,
      stage: next.stage,
      mode: next.mode,
      period: next.period,
      helpNeeded: next.helpNeeded,
      unreadMedia: next.unreadMedia,
    });
  }

  function handleSelect(conversationId: string) {
    // Store drives the thread/contact panels (guaranteed re-render); URL keeps the
    // selection shareable + highlights the active row.
    setActiveConvId(conversationId);
    void setUrlState({ conv: conversationId });
    // Remember it so the next visit re-opens this conversation (UI-AUDIT #1).
    if (tenantId) setLastViewedConv(tenantId, conversationId);
  }

  // Derive current FilterChipsValue from URL state
  const filterChipsValue: FilterChipsValue = {
    channel: urlState.channel ?? null,
    status: urlState.status ?? null,
    stage: urlState.stage ?? null,
    mode: urlState.mode ?? null,
    period: urlState.period ?? null,
    helpNeeded: urlState.helpNeeded ?? null,
    unreadMedia: urlState.unreadMedia ?? null,
  };

  return (
    <div
      className={cn("flex h-full flex-col overflow-hidden", className)}
      data-testid="conversation-list-panel-inner"
    >
      {/* Search bar */}
      <div className="shrink-0 border-b vt-border px-3 py-2">
        <SearchInput
          value={urlState.search ?? ""}
          onChange={handleSearchChange}
        />
      </div>

      {/* Filter chips */}
      <div className="shrink-0 border-b vt-border py-2">
        <FilterChips value={filterChipsValue} onChange={handleFiltersChange} />
      </div>

      {/* Error state */}
      {isError && !isLoading && (
        <div
          role="alert"
          aria-live="assertive"
          className="shrink-0 px-4 py-2 text-xs vt-text-danger"
          data-testid="conversations-error"
        >
          {INBOX_COPY.errors.loadConversations}
        </div>
      )}

      {/* Conversation list — scrollable, takes remaining height */}
      <div className="min-h-0 flex-1 overflow-hidden">
        <InboxConvList
          conversations={conversations}
          selectedId={urlState.conv ?? activeConvId ?? null}
          onSelect={handleSelect}
          isLoading={isLoading}
          emptyVariant={getEmptyVariant()}
          onClearFilters={handleClearFilters}
          getPatientName={(leadId) => leadNameById.get(leadId) ?? "—"}
          className="h-full"
        />
      </div>
    </div>
  );
}
