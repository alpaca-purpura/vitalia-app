// cap: sales_agent.inbox-handler-mode-occ
// story-origin: TBD
/**
 * conversation.ts — Zod schema for Conversation runtime validation.
 *
 * SSoT for API response validation (consumed by hooks in crm-shared/api/ + inbox/api/).
 * Mirrors Pydantic ConversationResponse shape exactly (snake_case).
 * Schema is the source of truth — types are inferred from it.
 *
 * Consumer: features/crm-shared/api/use-conversations.ts (T-inbox-fe-2)
 *           features/inbox/api/use-conversation-detail.ts (T-inbox-fe-2)
 *           features/pipeline (Ola 2)
 *
 * downstream-regression-na: brand-local FE schema; no cross-brand consumers
 */
import { z } from "zod";

import { leadStageSchema } from "./lead";

/** Supported channel enum */
export const conversationChannelSchema = z.enum([
  "whatsapp",
  "instagram",
  "facebook_messenger",
  "web",
  "walk_in",
  "phone",
]);

/** Conversation lifecycle status enum */
export const conversationStatusSchema = z.enum([
  "active",
  "paused",
  "closed",
  "archived",
]);

/** Handler mode enum */
export const handlerModeSchema = z.enum(["ai", "human"]);

/**
 * conversationSchema — Zod schema for Conversation API response.
 * Validates runtime data from GET /api/v1/vitalia/crm/conversations/{id}
 * and list responses.
 *
 * Note: updated_at is used as ETag for OCC (If-Match header in SetMode).
 */
export const conversationSchema = z.object({
  id: z.string().uuid(),
  lead_id: z.string().uuid(),
  tenant_id: z.string().uuid(),
  clinic_id: z.string().uuid(),
  patient_id: z.string().uuid().nullable(),
  channel: conversationChannelSchema,
  status: conversationStatusSchema,
  handler_mode: handlerModeSchema,
  proposal_required: z.boolean(),
  pause_until: z.string().datetime({ offset: true }).nullable(),
  help_needed: z.boolean(),
  help_needed_reason: z.string().nullable(),
  unread_media_count: z.number().int().nonnegative(),
  last_message_at: z.string().datetime({ offset: true }),
  last_message_preview: z.string().nullable(),
  messages_count: z.number().int().nonnegative(),
  stage_decision: leadStageSchema.nullable(),
  linked_offer_id: z.string().uuid().nullable(),
  /** ISO 8601 — used as ETag for OCC If-Match header */
  updated_at: z.string().datetime({ offset: true }),
});

/** Message sender type enum */
export const messageSenderTypeSchema = z.enum([
  "patient",
  "agent_ai",
  "agent_human",
  "system",
]);

/** Message media kind enum */
export const messageMediaKindSchema = z.enum([
  "audio",
  "image",
  "video",
  "document",
  "sticker",
]);

/** Message schema */
export const messageSchema = z.object({
  id: z.string().uuid(),
  conversation_id: z.string().uuid(),
  sender_type: messageSenderTypeSchema,
  sender_user_id: z.string().uuid().nullable(),
  body_text: z.string().nullable(),
  media_kind: messageMediaKindSchema.nullable(),
  media_url: z.string().url().nullable(),
  media_duration_s: z.number().nonnegative().nullable(),
  transcription_text: z.string().nullable(),
  transcription_confidence: z.number().min(0).max(1).nullable(),
  retracted_at: z.string().datetime({ offset: true }).nullable(),
  retract_succeeded: z.boolean().nullable(),
  handler_mode: handlerModeSchema,
  sent_at: z.string().datetime({ offset: true }),
  action_receipt_expires_at: z.string().datetime({ offset: true }).nullable(),
});

/** Action receipt schema */
export const actionReceiptSchema = z.object({
  message_id: z.string().uuid(),
  expires_at: z.string().datetime({ offset: true }),
});

/** Tool invocation status enum */
export const toolInvocationStatusSchema = z.enum([
  "pending",
  "success",
  "error",
  "skipped",
]);

/** Tool invocation schema */
export const toolInvocationSchema = z.object({
  tool_name: z.string().min(1),
  invoked_at: z.string().datetime({ offset: true }),
  status: toolInvocationStatusSchema,
  result_summary: z.string().nullable(),
});

/** Tools state schema */
export const toolsStateSchema = z.object({
  conversation_id: z.string().uuid(),
  invocations: z.array(toolInvocationSchema),
  updated_at: z.string().datetime({ offset: true }),
});

/** Full conversation detail schema (compound response) */
export const conversationDetailSchema = z.object({
  conversation: conversationSchema,
  /** PHI fields in lead are validated but must be displayed via PiiMaskedSpan */
  lead: z.object({
    id: z.string().uuid(),
    tenant_id: z.string().uuid(),
    clinic_id: z.string().uuid(),
    name: z.string().min(1),
    phone: z.string().nullable(),
    email: z.string().email().nullable().or(z.null()),
    stage: leadStageSchema,
    last_conversation_id: z.string().uuid().nullable(),
  }),
  messages: z.array(messageSchema),
  action_receipts: z.array(actionReceiptSchema),
  tools_state: toolsStateSchema.nullable(),
});

/** Paginated conversation list response schema */
export const conversationListResponseSchema = z.object({
  items: z.array(conversationSchema),
  total: z.number().int().nonnegative(),
  page: z.number().int().positive(),
  page_size: z.number().int().positive(),
});

/** Activity event kind enum */
export const activityEventKindSchema = z.enum([
  "tool_call",
  "llm_call",
  "turn_start",
  "turn_end",
  "proposal_generated",
  "mode_changed",
  "message_sent",
  "message_retracted",
  "adrian_paused",
  "compliance_blocked",
]);

/** Activity event schema */
export const activityEventSchema = z.object({
  id: z.string().uuid(),
  conversation_id: z.string().uuid(),
  kind: activityEventKindSchema,
  summary: z.string(),
  payload_redacted: z.record(z.string(), z.unknown()).nullable(),
  occurred_at: z.string().datetime({ offset: true }),
});

/** Activity stream list response schema */
export const activityStreamResponseSchema = z.object({
  events: z.array(activityEventSchema),
  conversation_id: z.string().uuid(),
});

/** Inferred TypeScript types */
export type ConversationSchema = z.infer<typeof conversationSchema>;
export type ConversationChannelSchema = z.infer<
  typeof conversationChannelSchema
>;
export type ConversationStatusSchema = z.infer<typeof conversationStatusSchema>;
export type HandlerModeSchema = z.infer<typeof handlerModeSchema>;
export type MessageSchema = z.infer<typeof messageSchema>;
export type ActionReceiptSchema = z.infer<typeof actionReceiptSchema>;
export type ToolsStateSchema = z.infer<typeof toolsStateSchema>;
export type ConversationDetailSchema = z.infer<typeof conversationDetailSchema>;
export type ConversationListResponseSchema = z.infer<
  typeof conversationListResponseSchema
>;
export type ActivityEventSchema = z.infer<typeof activityEventSchema>;
export type ActivityStreamResponseSchema = z.infer<
  typeof activityStreamResponseSchema
>;
