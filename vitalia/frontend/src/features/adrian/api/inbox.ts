// cap: adrian.inbox
// story-origin: vitalia-fase2-adrian-inbox
/**
 * inbox.ts — Consolidated React Query hooks for Adrián Inbox.
 * T-4 vitalia-fase2-adrian-inbox (NEW — aggregates migrated hooks)
 *
 * Re-exports all inbox hooks from their individual files for a single
 * import surface. Consumers can import from this file or from individual
 * hook files directly (both are valid per FSD-Lite barrel pattern).
 *
 * RQ key convention: ['adrian','inbox', action, ...filtersStable]
 * per 03-arch-fe.md § 4 + test_react_query_keys_convention.test.ts.
 *
 * Polling:
 *   - conversations list: refetchInterval 10_000ms
 *   - activity stream: refetchInterval 5_000ms (only when expanded)
 *
 * downstream-regression-na: brand-local FE barrel; no cross-brand consumers
 * spec_anchor: 03-arch-fe.md § 4 + 06-tickets.yaml T-4
 */

// ── Key factory ───────────────────────────────────────────────────────────────
export {
  conversationsListKey,
  conversationDetailKey,
  activityStreamKey,
  toolsStateKey,
  nudgeKey,
} from "./_keys";
export type { ConversationsFilters } from "./_keys";

// ── Data-fetching hooks ───────────────────────────────────────────────────────
export { useActivityStream } from "./use-activity-stream";
export type { ActivityStreamResponse } from "./use-activity-stream";

export { useToolsState } from "./use-tools-state";

// ── Mutation hooks ────────────────────────────────────────────────────────────
export { useSendMessage } from "./use-send-message";
export type { SendMessageInput } from "./use-send-message";

export { useRetractMessage } from "./use-retract-message";
export type {
  RetractMessageInput,
  RetractMessageResult,
} from "./use-retract-message";

export { useSetMode } from "./use-set-mode";
export type { SetModeInput, SetModeResult } from "./use-set-mode";

export { usePauseAdrian } from "./use-pause-adrian";
export type {
  PauseAdrianInput,
  PauseAdrianResult,
} from "./use-pause-adrian";

export { useProactiveOutbound } from "./use-proactive-outbound";
export type {
  ProactiveOutboundInput,
  ProactiveOutboundResult,
} from "./use-proactive-outbound";

export { useAttachMedia } from "./use-attach-media";
export type {
  AttachMediaInput,
  AttachMediaResult,
} from "./use-attach-media";

export { useTranscribeAudio } from "./use-transcribe-audio";
export type {
  TranscribeAudioInput,
  TranscribeAudioResult,
} from "./use-transcribe-audio";

// ── SSR server-side ───────────────────────────────────────────────────────────
export { getInitialInboxState } from "./inbox-server";
export type {
  GetInitialInboxStateOptions,
  InitialInboxState,
  InboxConversationSummary,
} from "./inbox-server";
