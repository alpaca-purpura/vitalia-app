// cap: adrian.inbox
// story-origin: vitalia-fase2-adrian-inbox
/**
 * inbox.types.ts — Consolidated TypeScript types for Adrián Inbox.
 * T-4 vitalia-fase2-adrian-inbox (MIGRATE + MERGE)
 *
 * Merges:
 *   - features/inbox/types/{message,activity-event,action-receipt,tools-state,conversation-detail}.ts
 *   - features/adrian/components/inbox/types.ts (parity subset)
 *
 * camelCase mirror of Pydantic DTOs. ISO 8601 datetimes as `string`.
 * Optional fields explicit (field?: type).
 *
 * HIPAA-lite: Message.body_text may contain indirect PHI.
 *   Use PiiMaskedSpan + RequireRole for rendering.
 *
 * downstream-regression-na: brand-local FE types; no cross-brand consumers
 * spec_anchor: 03-arch-fe.md § 2 + 06-tickets.yaml T-4
 */

import type { Conversation, Lead } from "@/features/crm-shared";

// ── Channel / list types (from parity) ───────────────────────────────────────

/** Channel abbreviation source */
export type InboxChannel = "whatsapp" | "instagram" | "telegram" | "email" | "web";

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
 * F1: mock data only. F2+: real API response (mirrored from BE DTO camelCase).
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
  email: "EM",
  web: "WB",
} as const;

// ── Message types ─────────────────────────────────────────────────────────────

/** Who sent the message. */
export type MessageSenderType =
  | "patient"
  | "agent_ai"
  | "agent_human"
  | "system";

/** Supported media types for message attachments. */
export type MessageMediaKind =
  | "audio"
  | "image"
  | "video"
  | "document"
  | "sticker";

/**
 * Message — mirrors Pydantic MessageResponse.
 * Maps vitalia_messages table row (PHI-scoped: tenant_id + clinic_id).
 */
export interface Message {
  /** UUID primary key */
  id: string;
  /** FK → vitalia_conversations.id */
  conversation_id: string;
  /** Who sent the message */
  sender_type: MessageSenderType;
  /** FK → users.id for human senders; null for agent_ai / system */
  sender_user_id: string | null;
  /** Plain-text body (null for media-only messages) */
  body_text: string | null;
  /** Presence indicates a media attachment */
  media_kind: MessageMediaKind | null;
  /** CDN URL for the media asset */
  media_url: string | null;
  /** Audio duration in seconds (only for media_kind="audio") */
  media_duration_s: number | null;
  /** Whisper STT transcription text (null if not transcribed or failed) */
  transcription_text: string | null;
  /** Whisper confidence score 0..1 (null if not transcribed) */
  transcription_confidence: number | null;
  /** ISO 8601 timestamp of retraction; null if not retracted */
  retracted_at: string | null;
  /** Whether the retraction API call to the channel succeeded */
  retract_succeeded: boolean | null;
  /** Handler mode at time of send (reflects conversation state) */
  handler_mode: "ai" | "human";
  /** ISO 8601 timestamp when sent to the channel */
  sent_at: string;
  /** ISO 8601 expiry for undo action receipt chip (null = no undo available) */
  action_receipt_expires_at: string | null;
  /**
   * Delivery state for OUTGOING messages — drives WhatsApp-style ✓ / ✓✓ receipts.
   * TODO(BE): not populated yet; the FE defaults to "sent" (single ✓) so the wiring
   * is ready the moment the channel adapters report delivery/read (UI-AUDIT-3).
   */
  delivery_status?: "sent" | "delivered" | "read" | null;
}

// ── Activity event types ──────────────────────────────────────────────────────

/**
 * Activity event type discriminants.
 * Maps to Adrián trace event kinds visible to clinic operators.
 */
export type ActivityEventKind =
  | "tool_call"
  | "llm_call"
  | "turn_start"
  | "turn_end"
  | "proposal_generated"
  | "mode_changed"
  | "message_sent"
  | "message_retracted"
  | "adrian_paused"
  | "compliance_blocked"
  | "nudge_sent";

/**
 * ActivityEvent — mirrors Pydantic ActivityEventResponse.
 * Sourced from copilot_trace_event table filtered by conversation_id.
 */
export interface ActivityEvent {
  /** UUID primary key */
  id: string;
  /** FK → vitalia_conversations.id */
  conversation_id: string;
  /** Discriminant for rendering icon + label */
  kind: ActivityEventKind;
  /** Human-readable summary (Spanish neutro, server-rendered) */
  summary: string;
  /** Pre-sanitized metadata snippet (no PHI per hipaa-lite.md) */
  payload_redacted: Record<string, unknown> | null;
  /** ISO 8601 event timestamp */
  occurred_at: string;
}

// ── Action receipt types ──────────────────────────────────────────────────────

/**
 * ActionReceipt — mirrors Pydantic ActionReceiptResponse.
 * Temporary undo window for retractable actions (5-minute window).
 */
export interface ActionReceipt {
  /** UUID primary key */
  id: string;
  /** FK → vitalia_messages.id */
  message_id: string;
  /** FK → vitalia_conversations.id */
  conversation_id: string;
  /** ISO 8601 expiry timestamp */
  expires_at: string;
  /** Whether the receipt has been used (undo triggered) */
  used: boolean;
  /** ISO 8601 creation timestamp */
  created_at: string;
}

// ── Tools state types ─────────────────────────────────────────────────────────

/** Lifecycle status of a tool invocation */
export type ToolInvocationStatus =
  | "pending"
  | "running"
  | "completed"
  | "success"
  | "error"
  | "failed"
  | "skipped";

/**
 * ToolInvocation — a single tool call record within an agent turn.
 * Reflects LangGraph tool node execution.
 */
export interface ToolInvocation {
  /** Tool identifier (from brand tools registry) */
  tool_name: string;
  /** Human-readable display name */
  display_name: string;
  /** Lifecycle status */
  status: ToolInvocationStatus;
  /** ISO 8601 start timestamp */
  started_at: string | null;
  /** ISO 8601 completion timestamp */
  completed_at: string | null;
  /**
   * ISO 8601 timestamp when the tool was invoked in a conversation turn.
   * Used by AdrianToolsSheet for last-invoked display.
   */
  invoked_at: string | null;
  /**
   * Server-rendered Spanish neutro result summary (PHI-safe, pre-sanitized).
   * Shown in AdrianToolsSheet for operator visibility.
   */
  result_summary: string | null;
  /** Whether the tool is currently enabled for this conversation */
  enabled: boolean;
  /** Reason tool is disabled (null if enabled) */
  disabled_reason: string | null;
  /** ISO 8601 last-used timestamp (null if never used in any turn) */
  last_used_at: string | null;
}

/**
 * ToolsState — mirrors Pydantic ToolsStateResponse.
 * Aggregate of all tool invocations for a conversation.
 */
export interface ToolsState {
  /** FK → vitalia_conversations.id */
  conversation_id: string;
  /** List of tool invocations for this conversation */
  invocations: ToolInvocation[];
  /** FK → offer if conversation is offer-scoped */
  linked_offer_id: string | null;
}

// ── Conversation detail compound type ────────────────────────────────────────

/**
 * ConversationDetail — full compound response for a single conversation thread.
 * Mirrors Pydantic ConversationDetailResponse.
 */
export interface ConversationDetail {
  /** The conversation entity */
  conversation: Conversation;
  /** The lead / patient contact associated with this conversation */
  lead: Lead;
  /** Ordered list of messages in the thread (chronological) */
  messages: Message[];
  /** Active action receipts (for undo chip rendering) */
  action_receipts: ActionReceipt[];
  /** Agent tools state for the conversation (null if agent not active) */
  tools_state: ToolsState | null;
}

// ── 2-Modos backend mapping (Chris UI #3 — manual typing is now "Pausar") ──────

/** The 2 UI modes presented in the segmented control */
export type SegmentedModeValue = "adrian-decide" | "adrian-consulta";

/** Maps UI segment value → API mode input */
export const SEGMENT_TO_API: Record<
  SegmentedModeValue,
  { newMode: "ai" | "human"; proposalRequired: boolean }
> = {
  "adrian-decide": { newMode: "ai", proposalRequired: false },
  "adrian-consulta": { newMode: "ai", proposalRequired: true },
};
