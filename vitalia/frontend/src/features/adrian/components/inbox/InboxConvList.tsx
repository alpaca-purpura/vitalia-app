// cap: adrian.inbox
// story-origin: TBD
/**
 * ConversationList.tsx — Renders the scrollable conversation list.
 *
 * Fork/adapter pattern per ADR-vitalia-001 (physical fork, NOT cross-brand import).
 * Based on nicolify/closer-studio/ConversationList pattern — retokenized for vitalia.
 *
 * Responsibilities:
 *   - Render ConversationItem × N
 *   - Loading skeleton (3 items) when isLoading=true
 *   - Empty state via ListEmptyState when conversations=[] and !isLoading
 *   - Selected item highlight via aria-selected
 *   - Accessible: role="listbox" (selectable list), aria-label, keyboard nav
 *
 * HIPAA-lite: patientName is passed through — callers must apply PHI masking
 * upstream before passing the name prop (RequireRole/PiiMaskedSpan pattern).
 *
 * "use client" NOT needed — no state/effects. Parent ConversationListPanel is client.
 *
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 */

import { cn } from "@/lib/cn";
import type { Conversation } from "@/features/crm-shared";
import { ConversationItem } from "./ConversationItem";
import { ListEmptyState } from "./ListEmptyState";
import type { ListEmptyStateVariant } from "./ListEmptyState";

/** Loading skeleton row */
function ConversationItemSkeleton() {
  return (
    <li
      role="presentation"
      data-testid="conversation-item-skeleton"
      aria-hidden="true"
      className="flex flex-col gap-2 border-b vt-border px-4 py-3"
    >
      <div className="flex items-center gap-2">
        <div className="h-4 w-4 animate-pulse rounded vt-bg-muted" />
        <div className="h-3 flex-1 animate-pulse rounded vt-bg-muted" />
        <div className="h-3 w-8 animate-pulse rounded vt-bg-muted" />
      </div>
      <div className="ml-6 h-3 w-3/4 animate-pulse rounded vt-bg-muted" />
    </li>
  );
}

interface InboxConvListProps {
  conversations: Conversation[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  /** Shows loading skeleton rows when true */
  isLoading?: boolean;
  /** Empty state variant to show when conversations=[] and !isLoading */
  emptyVariant?: ListEmptyStateVariant;
  /** CTA callback for noResultsFilter empty state */
  onClearFilters?: () => void;
  /**
   * Resolver for patient name from lead_id.
   * In production, caller provides this by lifting Lead data.
   * Default: show "—" (safe fallback while data loads).
   */
  getPatientName?: (leadId: string) => string;
  className?: string;
}

/**
 * ConversationList — accessible scrollable list of conversations.
 * Handles loading, empty, and populated states.
 */
export function InboxConvList({
  conversations,
  selectedId,
  onSelect,
  isLoading = false,
  emptyVariant = "noConversations",
  onClearFilters,
  getPatientName,
  className,
}: InboxConvListProps) {
  // Loading state — show 5 skeleton rows
  if (isLoading) {
    return (
      <ul
        role="listbox"
        aria-label="Conversaciones — cargando"
        aria-busy="true"
        className={cn("flex flex-col overflow-y-auto", className)}
      >
        {Array.from({ length: 5 }).map((_, i) => (
          <ConversationItemSkeleton key={i} />
        ))}
      </ul>
    );
  }

  // Empty state
  if (conversations.length === 0) {
    return (
      <div
        className={cn("flex flex-1 items-start justify-center pt-8", className)}
        data-testid="conversation-list-empty-wrapper"
      >
        <ListEmptyState
          variant={emptyVariant}
          onClearFilters={onClearFilters}
        />
      </div>
    );
  }

  // Populated list
  return (
    <ul
      role="listbox"
      aria-label="Conversaciones"
      aria-multiselectable="false"
      className={cn("flex flex-col overflow-y-auto", className)}
    >
      {conversations.map((conv) => (
        <ConversationItem
          key={conv.id}
          conversation={conv}
          isSelected={conv.id === selectedId}
          onSelect={onSelect}
          patientName={getPatientName ? getPatientName(conv.lead_id) : "—"}
        />
      ))}
    </ul>
  );
}
