// cap: adrian.inbox
// story-origin: TBD
/**
 * url-state.ts — Inbox URL state schema (nuqs parsers).
 *
 * All params use history: 'replace' (intra-route sub-state).
 * Inter-route navigation (sidebar) uses Next.js router.push() directly.
 *
 * Schema mirrors INBOX_URL_SCHEMA from 03-arch-fe.md § 3.
 * Consumed by: InboxPageClient · use-conversation-filters (T-inbox-fe-2).
 *
 * downstream-regression-na: brand-local FE url-state; no cross-brand consumers
 */
"use client";

import {
  parseAsBoolean,
  parseAsString,
  parseAsStringEnum,
  useQueryStates,
} from "nuqs";

/** Supported conversation channel filter values */
export type InboxChannelFilter =
  | "whatsapp"
  | "instagram"
  | "telegram"
  | "tiktok"
  | "facebook"
  | "email";

/** Conversation status filter values */
export type InboxStatusFilter =
  | "active"
  | "waiting-deposit"
  | "nps-pending"
  | "closed";

/** CRM stage filter values (maps to LeadStage subset) */
export type InboxStageFilter =
  | "interested"
  | "considering"
  | "ready-to-book"
  | "decided-no";

/** Adrián handler mode filter */
export type InboxModeFilter =
  | "adrian-decide"
  | "adrian-consulta"
  | "yo-escribo";

/** Date range filter */
export type InboxPeriodFilter = "today" | "yesterday" | "week" | "month";

/**
 * INBOX_URL_SCHEMA — nuqs parser definitions for inbox route.
 * All params are optional (null when not set).
 */
export const INBOX_URL_SCHEMA = {
  /** Selected conversation id — spec RN-14/AC-3: deep-link param is `?conv={id}` (UUID, no PHI) */
  conv: parseAsString,
  /** Channel filter chip */
  channel: parseAsStringEnum<InboxChannelFilter>([
    "whatsapp",
    "instagram",
    "telegram",
    "tiktok",
    "facebook",
    "email",
  ]),
  /** Conversation status filter */
  status: parseAsStringEnum<InboxStatusFilter>([
    "active",
    "waiting-deposit",
    "nps-pending",
    "closed",
  ]),
  /** CRM stage filter */
  stage: parseAsStringEnum<InboxStageFilter>([
    "interested",
    "considering",
    "ready-to-book",
    "decided-no",
  ]),
  /** Handler mode filter */
  mode: parseAsStringEnum<InboxModeFilter>([
    "adrian-decide",
    "adrian-consulta",
    "yo-escribo",
  ]),
  /** Date period filter */
  period: parseAsStringEnum<InboxPeriodFilter>([
    "today",
    "yesterday",
    "week",
    "month",
  ]),
  /** Show only conversations where operator help is requested */
  helpNeeded: parseAsBoolean,
  /** Show only conversations with unread media (audio/images) */
  unreadMedia: parseAsBoolean,
  /** Search query (debounced 300ms in SearchInput) */
  search: parseAsString,
} as const;

/** Inferred type of inbox URL state values */
export type InboxUrlState = {
  [K in keyof typeof INBOX_URL_SCHEMA]: ReturnType<
    (typeof INBOX_URL_SCHEMA)[K]["parseServerSide"]
  >;
};

/**
 * useInboxUrlState — hook for reading + updating inbox URL state.
 * All updates use history: 'replace' to avoid polluting browser history.
 *
 * Usage:
 *   const [params, setParams] = useInboxUrlState();
 *   setParams({ conv: conversationId });
 */
export function useInboxUrlState() {
  return useQueryStates(INBOX_URL_SCHEMA, { history: "replace" });
}
