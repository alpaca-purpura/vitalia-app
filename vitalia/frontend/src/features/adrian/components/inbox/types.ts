// cap: sales_agent.inbox-handler-mode-occ
// story-origin: vitalia-fase1-s10-TBD
/**
 * inbox/types.ts — Shared types for Adrián Inbox molecules.
 * F1-S10 vitalia-fase1-empty-states — T-5
 *
 * ConversationListItem: shape for list + thread + sidebar.
 * Brand-local (NO cross-brand import). Pattern conceptually inspired by
 * ap_sales_agent/closer-studio shape (F2 lift candidate to core/luana-core-ui/inbox/).
 *
 * spec_anchor: 03-arch.md § 3.3 + 06-tickets.yaml T-5
 * downstream-regression-na: brand-local vitalia; no cross-brand consumers
 */

/** Channel abbreviation source */
export type InboxChannel = "whatsapp" | "instagram" | "telegram";

/** Lead temperature — visual heat indicator */
export type LeadTemp = "hot" | "warm" | "cold";

/** Funnel stage — maps to Spanish neutro label */
export type FunnelStage = "rapport" | "discovery" | "presentation" | "closing";

/** Who is currently handling this conversation */
export type HandlerMode = "bot" | "human";

/** Campaign origin pill data */
export interface CampaignRef {
  id: string;
  name: string;
}

/**
 * ConversationListItem — shape for the Adrián Inbox conversation list.
 * F1: mock data only. F2: real API response (mirrored from BE DTO camelCase).
 */
export interface ConversationListItem {
  leadId: string;
  displayName: string;
  lastMessagePreview: string;
  /** Relative time string — e.g. "hace 2 min". F2: computed from ISO 8601. */
  lastActivityRelative: string;
  channel: InboxChannel;
  temp: LeadTemp;
  stage: FunnelStage;
  handlerMode: HandlerMode;
  campaign?: CampaignRef;
}

/** Maps FunnelStage → Spanish neutro label (spec § 10 verbatim) */
export const STAGE_LABEL: Record<FunnelStage, string> = {
  rapport: "Nuevo",
  discovery: "Calificando",
  presentation: "Negociando",
  closing: "Cerrando",
} as const;

/** Maps InboxChannel → abbreviation */
export const CHANNEL_ABBR: Record<InboxChannel, string> = {
  whatsapp: "WA",
  instagram: "IG",
  telegram: "TG",
} as const;
