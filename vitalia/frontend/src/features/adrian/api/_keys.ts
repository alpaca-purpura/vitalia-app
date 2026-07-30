// cap: adrian.inbox
// story-origin: vitalia-fase2-adrian-inbox
/**
 * _keys.ts — React Query key factory for adrian/inbox feature.
 * T-4 vitalia-fase2-adrian-inbox (MIGRATE from features/inbox/api/_keys.ts)
 *
 * Keys follow convention: ['adrian','inbox', action, ...filtersStable]
 * per 03-arch-fe.md § 4 + architecture fitness test_react_query_keys_convention.test.ts.
 *
 * Change from orphan source: prefixed with 'adrian' root segment for FSD isolation.
 * Cross-invalidation: invalidateQueries({ queryKey: ['adrian','inbox'] }).
 *
 * downstream-regression-na: brand-local FE keys; no cross-brand consumers
 */

/** Root key segments for all inbox queries */
const ADRIAN = "adrian" as const;
const INBOX = "inbox" as const;

/** Filters shape used when listing conversations */
export interface ConversationsFilters {
  channel?: string | null;
  status?: string | null;
  stage?: string | null;
  mode?: string | null;
  period?: string | null;
  helpNeeded?: boolean | null;
  unreadMedia?: boolean | null;
  search?: string | null;
}

/**
 * All conversations list (paginated + filterable).
 * Invalidated on send / retract / mode-change mutations.
 */
export const conversationsListKey = (filters?: ConversationsFilters) =>
  filters
    ? ([ADRIAN, INBOX, "conversations", filters] as const)
    : ([ADRIAN, INBOX, "conversations"] as const);

/**
 * Single conversation detail compound response.
 * Includes messages, action_receipts, tools_state.
 */
export const conversationDetailKey = (conversationId: string) =>
  [ADRIAN, INBOX, "conversation", conversationId] as const;

/**
 * Activity stream events for a conversation.
 * Polled every 5s when ActivityStream is expanded.
 */
export const activityStreamKey = (conversationId: string) =>
  [ADRIAN, INBOX, "activity-stream", conversationId] as const;

/**
 * Tools state for a conversation.
 * Cached 30s — changes infrequent (read-only).
 */
export const toolsStateKey = (conversationId: string) =>
  [ADRIAN, INBOX, "tools", conversationId] as const;

/**
 * Nudge mutation key (T-5 / T-2 endpoint).
 * Used for optimistic mutation tracking.
 */
export const nudgeKey = (conversationId: string) =>
  [ADRIAN, INBOX, "nudge", conversationId] as const;

/**
 * ★ Unified conversation detail key — shared by all surfaces.
 * Mirrors useConversationDetail in crm-shared.
 * MUST be kept in sync with crm-shared/api/use-conversation-detail.ts line 36.
 * Invalidated on stage changes, message send, mode change, pause, etc.
 */
export const conversationDetailKeyForInvalidation = (conversationId: string) =>
  ["crm", "conversation", conversationId] as const;

/**
 * Unified conversations list key for Inbox.
 * Used for list-level invalidations (send message, mode change, pause).
 */
export const conversationsListKeyForInvalidation = () =>
  ["crm", "conversations"] as const;
