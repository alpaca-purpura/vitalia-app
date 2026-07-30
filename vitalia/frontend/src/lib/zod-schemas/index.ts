// cap: platform.shell-foundation-shadcn-tailwind-v4
// story-origin: TBD
/**
 * zod-schemas/index.ts — Public API barrel for shared Zod schemas.
 *
 * SSoT for runtime API response validation (Ola 1+).
 * Consumed by: features/crm-shared/api · features/inbox/api · features/pipeline · features/agenda
 *
 * NO default exports (arch fitness enforces).
 * downstream-regression-na: brand-local FE schemas; no cross-brand consumers
 */

export {
  leadSchema,
  leadStageSchema,
  leadOriginSchema,
  leadAttributionSchema,
  leadListResponseSchema,
} from "./lead";

export type {
  LeadSchema,
  LeadStageSchema,
  LeadOriginSchema,
  LeadListResponseSchema,
} from "./lead";

export {
  conversationSchema,
  conversationChannelSchema,
  conversationStatusSchema,
  handlerModeSchema,
  messageSchema,
  messageSenderTypeSchema,
  messageMediaKindSchema,
  actionReceiptSchema,
  toolInvocationSchema,
  toolInvocationStatusSchema,
  toolsStateSchema,
  conversationDetailSchema,
  conversationListResponseSchema,
  activityEventSchema,
  activityEventKindSchema,
  activityStreamResponseSchema,
} from "./conversation";

export type {
  ConversationSchema,
  ConversationChannelSchema,
  ConversationStatusSchema,
  HandlerModeSchema,
  MessageSchema,
  ActionReceiptSchema,
  ToolsStateSchema,
  ConversationDetailSchema,
  ConversationListResponseSchema,
  ActivityEventSchema,
  ActivityStreamResponseSchema,
} from "./conversation";
