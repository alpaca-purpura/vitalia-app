// cap: crm.adrian-embudo
// story-origin: vitalia-fase2-adrian-embudo
/**
 * adrian/index.ts — Feature public API (FSD-Lite boundary matrix).
 * F1-S10 vitalia-fase1-empty-states (origin)
 * F3-T-3 vitalia-fase2-adrian-inbox (2026-06-03): AdrianInboxView + getInitialInboxState
 * F3-T-4 vitalia-fase2-adrian-inbox (2026-06-03): full inbox migration (MIGRATE + MERGE + DELETE orphan)
 * T-FE-1 vitalia-fase2-adrian-embudo (2026-06-03): +RecuperarPlaceholder
 *
 * T-4: Exports full migrated inbox (components + hooks + types + store).
 *       features/inbox/ orphan DELETED; everything lives here now.
 *
 * NO default exports (arch fitness test enforces named exports only).
 * FSD-Lite: no cross-feature imports. Consumers import via this barrel.
 *
 * downstream-regression-na: brand-local FE barrel; no cross-brand consumers
 */

// ── Inbox root component ──────────────────────────────────────────────────────
export { AdrianInboxView } from "./components/inbox/AdrianInboxView";
export type { AdrianInboxViewProps } from "./components/inbox/AdrianInboxView";

// ── SSR server-side fetch — Server Components only ───────────────────────────
// NOTE: Safe in server context only. Do NOT import in "use client" components.
export { getInitialInboxState } from "./api/inbox-server";
export type {
  GetInitialInboxStateOptions,
  InitialInboxState,
  InboxConversationSummary,
} from "./api/inbox-server";

// ── Placeholder components (backward-compat) ──────────────────────────────────
export { OutboundPlaceholder } from "./components/placeholders/OutboundPlaceholder";
export { PropuestasPlaceholder } from "./components/placeholders/PropuestasPlaceholder";
export { EmbudoPlaceholder } from "./components/placeholders/EmbudoPlaceholder";

// ── Placeholder components (T-FE-1 special: RecuperarPlaceholder) ─────────────
// Real RecuperarView + FrozenLeadRow ship in T-FE-3.
export { RecuperarPlaceholder } from "./components/placeholders/RecuperarPlaceholder";

// ── Inbox components (T-4 MIGRATE + MERGE from features/inbox/) ──────────────
export { CampaignTag } from "./components/inbox/CampaignTag";
export { ConversationItem } from "./components/inbox/ConversationItem";
export { InboxConvList } from "./components/inbox/InboxConvList";
export { ConversationListPanel } from "./components/inbox/ConversationListPanel";
export { InboxThread } from "./components/inbox/InboxThread";
export { MessageBubble } from "./components/inbox/MessageBubble";
export type { MessageBubbleProps } from "./components/inbox/MessageBubble";
export { MessageInput } from "./components/inbox/MessageInput";
export type { MessageInputProps } from "./components/inbox/MessageInput";
export { ThreadHeader } from "./components/inbox/ThreadHeader";
export { TakeoverBanner } from "./components/inbox/TakeoverBanner";
export type { TakeoverBannerProps } from "./components/inbox/TakeoverBanner";
export { ContactSidebar } from "./components/inbox/ContactSidebar";
export { ContactSidebarToggle } from "./components/inbox/ContactSidebarToggle";

// ── Embudo components (T-FE-2 vitalia-fase2-adrian-embudo 2026-06-03) ─────────
export { AdrianEmbudoView } from "./components/embudo/AdrianEmbudoView";
export type { AdrianEmbudoViewProps } from "./components/embudo/AdrianEmbudoView";
export { KanbanBoard } from "./components/embudo/KanbanBoard";
export { PipelineColumn } from "./components/embudo/PipelineColumn";
export { LeadCard } from "./components/embudo/LeadCard";
export type { LeadCardProps } from "./components/embudo/LeadCard";
export { LeadsTable } from "./components/embudo/LeadsTable";
export { EmbudoHeader } from "./components/embudo/EmbudoHeader";
export { EmbudoMetrics } from "./components/embudo/EmbudoMetrics";
export { EmbudoFilters } from "./components/embudo/EmbudoFilters";
export { OverrideReasonDialog } from "./components/embudo/OverrideReasonDialog";
export { SortBySelect } from "./components/embudo/SortBySelect";

// ── Embudo API / SSR (T-FE-2) ─────────────────────────────────────────────────
export { useEmbudoBoard } from "./api/embudo-board";
export { useLeadStageMutation } from "./api/lead-stage-mutation";
// NOTE: getEmbudoBoardInitialState is Server-only; import directly (not via barrel)
// to avoid bundling server code in client components.

// ── Embudo Zustand store (T-FE-2) ────────────────────────────────────────────
export { useEmbudoUiStore } from "./store/embudo-ui-store";
export type { PendingOverride } from "./store/embudo-ui-store";

// ── Embudo types (T-FE-2) ─────────────────────────────────────────────────────
export type {
  BoardColumn,
  BoardResponse,
  BoardKpis,
  LeadCardDTO,
  LeadDetailResponse,
  StageTransitionPayload,
  StageTransitionResponse,
  FrozenListResponse,
  FrozenLeadDTO,
  BoardFilters,
  ScoreFactor,
  AutonomyInfo,
  TimelineEntry,
  TimelineResponse,
} from "./types/embudo.types";

// ── T-FE-3 components (vitalia-fase2-adrian-embudo 2026-06-03) ───────────────
// Lead workspace (opción C — EntitySubNavBar + 2 views)
export { LeadWorkspace } from "./components/embudo/lead/LeadWorkspace";
export type { LeadWorkspaceProps } from "./components/embudo/lead/LeadWorkspace";
export { ResumenView } from "./components/embudo/lead/ResumenView";
export type { ResumenViewProps } from "./components/embudo/lead/ResumenView";
export { HistorialView } from "./components/embudo/lead/HistorialView";
export type { HistorialViewProps } from "./components/embudo/lead/HistorialView";
export { LeadSummaryHeader } from "./components/embudo/lead/LeadSummaryHeader";
export type { LeadSummaryHeaderProps } from "./components/embudo/lead/LeadSummaryHeader";
export { ScoreBreakdown } from "./components/embudo/lead/ScoreBreakdown";
export type { ScoreBreakdownProps } from "./components/embudo/lead/ScoreBreakdown";

// Nuevo lead (V5 — ruta-hoja /embudo/nuevo)
export { NewLeadPage } from "./components/embudo/nuevo/NewLeadPage";
export type { NewLeadPageProps } from "./components/embudo/nuevo/NewLeadPage";

// Recuperar (V4 — sub-tab hermana /recuperar)
export { RecuperarView } from "./components/recuperar/RecuperarView";
export type { RecuperarViewProps } from "./components/recuperar/RecuperarView";
export { FrozenLeadRow } from "./components/recuperar/FrozenLeadRow";
export type { FrozenLeadRowProps } from "./components/recuperar/FrozenLeadRow";

// ── T-FE-3 API hooks ──────────────────────────────────────────────────────────
export { useLeadDetail, useLeadTimeline } from "./api/lead";
export { useFrozenLeads, useReactivateLead } from "./api/frozen";
export { useDiagnose } from "./api/diagnose";
export { useCreateLead } from "./api/create-lead";
export type { CreateLeadPayload } from "./api/create-lead";

// ── T-FE-3 Zod schemas ────────────────────────────────────────────────────────
export { newLeadSchema, CHANNEL_OPTIONS } from "./types/embudo-schema";
export type { NewLeadFormData } from "./types/embudo-schema";

// ── T-FE-1 vitalia-fase2-adrian-canal-inbound — operator instruction (SC-8) ──
export { InstructionChip } from "./components/inbox/InstructionChip";
export type { InstructionChipProps } from "./components/inbox/InstructionChip";
export { useOperatorInstruction, getEffectiveMode } from "./hooks/use-operator-instruction";
export { operatorInstructionApi } from "./api/operator-instruction";
export type {
  SetOperatorInstructionRequest,
  SetOperatorInstructionResponse,
  ComposerMode,
} from "./types/operator-instruction";
