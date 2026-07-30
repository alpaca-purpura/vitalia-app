// cap: platform.lift-shell-chrome-ui-kit
/**
 * Shell organism barrel — named exports only (NO default exports).
 *
 * ⛔ NO re-export Group/Panel/Separator from react-resizable-panels.
 *    Consumers import those directly from "react-resizable-panels".
 *
 * T-K2 — @luana/ui-kit 0.4.0
 */

// ── Types (public surface) ──────────────────────────────────────────────────
export type {
  AgentClassBundle,
  GetAgentClasses,
  ShellAgentDescriptor,
  ShellLayoutLabels,
  ShellLayoutProps,
  ShellPersistedState,
  ShellStore,
  ShellChatStore,
  ShellChatMessage,
  ShellChatStatus,
  ShellConversationMeta,
  ShellMessageRole,
  ShellStoreState,
  ShellChatStoreApi,
  ShellTestIds,
  ShellSubTabMeta,
  ShellRoutingOptions,
  CreateShellStoreOptions,
  SupervisorOpen,
} from "./types";

// ── Store factory ───────────────────────────────────────────────────────────
export { createShellStore } from "./create-shell-store";

// ── Routing helpers ─────────────────────────────────────────────────────────
export {
  extractAgentFromPath,
  extractSubtabFromPath,
  extractSubSubTabFromPath,
} from "./routing";

// ── Layout ──────────────────────────────────────────────────────────────────
export { ShellLayout } from "./ShellLayout";
// ShellLayoutProps lives in ./types and is re-exported below via the types block.

export { ShellLayoutClient } from "./ShellLayoutClient";
// ShellLayoutClientProps = ShellLayoutProps (same props, no separate type).

// ── Supervisor sidebar ───────────────────────────────────────────────────────
export { SupervisorSidebar } from "./SupervisorSidebar";
export type { SupervisorSidebarProps } from "./SupervisorSidebar";

export { SupervisorCollapsedStrip } from "./SupervisorCollapsedStrip";
export type { SupervisorCollapsedStripProps } from "./SupervisorCollapsedStrip";

export { SupervisorHistory } from "./SupervisorHistory";

// ── Ribbon nav ───────────────────────────────────────────────────────────────
export { Ribbon } from "./Ribbon";
export type { RibbonProps } from "./Ribbon";

export { RibbonTab } from "./RibbonTab";

// ── Sub-tabs / sub-sub-tabs ──────────────────────────────────────────────────
export { SubTabsBar } from "./SubTabsBar";
export type { SubTabsBarProps } from "./SubTabsBar";

export { SubTab } from "./SubTab";
export type { SubTabProps } from "./SubTab";

export { SubSubTabsBar } from "./SubSubTabsBar";
export type { SubSubTabsBarProps, ShellSubSubTabMeta } from "./SubSubTabsBar";

// ── App panel slot ───────────────────────────────────────────────────────────
export { AppPanelSlot } from "./AppPanelSlot";
export type { AppPanelSlotProps } from "./AppPanelSlot";

// ── Chat panel & components ──────────────────────────────────────────────────
export { ChatPanel } from "./ChatPanel";
export type { ChatPanelProps } from "./ChatPanel";

export { ChatHeader } from "./ChatHeader";
export type { ChatHeaderProps } from "./ChatHeader";

export { ChatComposer } from "./ChatComposer";
export type { ChatComposerProps } from "./ChatComposer";

export { ChatMessages } from "./ChatMessages";
export type { ChatMessagesProps } from "./ChatMessages";

export { MessageBubble } from "./MessageBubble";
export type { MessageBubbleProps } from "./MessageBubble";

export { TypingIndicator } from "./TypingIndicator";
export type { TypingIndicatorProps } from "./TypingIndicator";

export { DelegateMarker } from "./DelegateMarker";
export type { DelegateMarkerProps } from "./DelegateMarker";

// ── Toggle pill ──────────────────────────────────────────────────────────────
export { TogglePill, TogglePillContent } from "./TogglePill";
export type { TogglePillProps, TogglePillItem } from "./TogglePill";

// ── Misc molecules ───────────────────────────────────────────────────────────
export { TopBarShell } from "./TopBarShell";
export type { TopBarShellProps } from "./TopBarShell";

export { StatusDot } from "./StatusDot";
export type { StatusDotProps, StatusDotVariant } from "./StatusDot";

export { ConfigTab } from "./ConfigTab";
export type { ConfigTabProps } from "./ConfigTab";

export { EmptyState } from "./EmptyState";
export type { EmptyStateProps } from "./EmptyState";

export { EmptyStateInline } from "./EmptyStateInline";
export type { EmptyStateInlineProps } from "./EmptyStateInline";

export { HistoryGroup } from "./HistoryGroup";
export type { HistoryGroupProps } from "./HistoryGroup";

export { HistoryItem } from "./HistoryItem";
export type { HistoryItemProps } from "./HistoryItem";

export { PlaceholderCard } from "./PlaceholderCard";
export type { PlaceholderCardProps } from "./PlaceholderCard";

// ── Hooks ────────────────────────────────────────────────────────────────────
export { useKeyboardShortcuts } from "./useKeyboardShortcuts";
export { useViewportGuard } from "./useViewportGuard";

// ── Agent tw-classes (type re-exports only — no brand token functions) ───────
// Brand injects getAgentClasses fn; kit only re-exports the bundle type.
export type { AgentClassBundle as AgentTwBundle } from "./_agent-tw-classes";
