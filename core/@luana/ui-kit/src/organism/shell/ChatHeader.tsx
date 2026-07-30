// cap: platform.lift-shell-chrome-ui-kit
"use client";

/**
 * ChatHeader — shell organism chat panel header (brand-agnostic).
 * T-K2 port of vitalia ChatHeader (F1-S6 T-3 + shell-core-hardening T-3).
 *
 * Brand coupling removed — agent identity, store, catalog, statusDotClass and
 * agent class helpers all injected by prop (RN-2, SC-7).
 *
 * ★ SACRED RN-4 (2026-06-11 live-fix): container query `@[24rem]:inline-flex`
 * on mode pill — depends on PANEL width (not viewport). NEVER change to a
 * breakpoint (`md:inline-flex`) — that fires on viewport width and breaks on
 * narrow panel + wide viewport. VERBATIM from vitalia ChatHeader.
 *
 * ★ Store action name (RN-2): collapseValeria → collapseSupervisor
 *   in kit store API (ShellStoreState). Brand thin wrapper re-exports under
 *   legacy alias if needed.
 *
 * "use client" required: useState (imgError fallback) + event handlers.
 *
 * Named export (NO default) per FSD-Lite enforce.
 */

import { useState } from "react";
import { Clock, PanelLeftClose, Plus } from "lucide-react";
import { cn } from "@luana/format/utils";
import { Badge } from "../../badge";
import { Button } from "../../button";
import type {
  GetAgentClasses,
  ShellAgentDescriptor,
  ShellChatStore,
  ShellChatStoreApi,
  ShellStore,
  ShellStoreState,
  ShellTestIds,
} from "./types";

export interface ChatHeaderProps {
  /** Resolved agent descriptor for this chat. */
  agent: ShellAgentDescriptor;
  status?: "online" | "offline";
  mode?: "agent" | "web";
  /** Injected stores — kit NEVER imports brand stores directly. */
  useShellStore: ShellStore;
  useChatStore: ShellChatStore;
  /** Brand fn returning Tailwind class bundles for agent slugs. */
  getAgentClasses: GetAgentClasses;
  /** Brand-specific status dot class (e.g. "bg-vitalia-success"). */
  statusDotClass?: string;
  /** Optional testIds override (e2e contract). */
  testIds?: Pick<ShellTestIds, "chatHeader" | "chatAvatar" | "chatStatusDot" | "chatModePill">;
  className?: string;
}

/**
 * ChatHeader — renders agent avatar, name, status text, mode pill + action buttons.
 *
 * Avatar has onError fallback showing initial letter in agent color circle.
 * Status dot is decorative (aria-hidden).
 * ★ Mode Pill uses `@[24rem]:inline-flex` container query (not viewport breakpoint).
 * Action buttons: nueva conversación · historial (toggle) · colapsar supervisor.
 */
export function ChatHeader({
  agent,
  status = "online",
  mode = "agent",
  useShellStore,
  useChatStore,
  getAgentClasses,
  statusDotClass,
  testIds,
  className,
}: ChatHeaderProps) {
  const [imgError, setImgError] = useState(false);

  const historyOpen = useShellStore((s: ShellStoreState) => s.historyOpen);
  const toggleHistory = useShellStore((s: ShellStoreState) => s.toggleHistory);
  const collapseSupervisor = useShellStore((s: ShellStoreState) => s.collapseSupervisor);
  const newConversation = useChatStore((s: ShellChatStoreApi) => s.newConversation);

  const agentClasses = getAgentClasses(agent.slug);
  // AgentClassBundle fields: accentBg | softBg | accentText | accentBorder

  const statusText =
    status === "online" ? `En línea · ${agent.role}` : "Desconectada";

  const modeLabel = mode === "agent" ? "🤖 Modo agente" : "🌐 Modo web";

  const historyLabel = historyOpen ? "Ocultar historial" : "Mostrar historial";

  return (
    <header
      data-testid={testIds?.chatHeader ?? "chat-header"}
      className={cn(
        "flex items-center gap-3 border-b border-border px-4 h-14 shrink-0",
        className,
      )}
    >
      {/* Avatar 9×9 con status dot */}
      <div className="relative shrink-0">
        <div
          data-testid={testIds?.chatAvatar ?? "supervisor-avatar"}
          className={cn(
            "h-9 w-9 rounded-full overflow-hidden flex items-center justify-center",
            agentClasses.accentBg,
          )}
          aria-hidden="true"
        >
          {imgError || !agent.thumbnail ? (
            <span className="text-sm font-semibold text-white select-none">
              {agent.initial}
            </span>
          ) : (
            <img
              src={agent.thumbnail}
              alt=""
              className="h-9 w-9 object-cover"
              onError={() => setImgError(true)}
            />
          )}
        </div>
        <span
          data-testid={testIds?.chatStatusDot ?? "supervisor-status-dot"}
          className={cn(
            "absolute bottom-0 right-0 h-2 w-2 rounded-full ring-2 ring-card",
            statusDotClass ?? "bg-green-500",
          )}
          aria-hidden="true"
        />
      </div>

      {/* Name + status text — min-w-[72px]: agent name always complete even at minimum
          panel width (narrowest panel: name truncates before pill). */}
      <div className="flex flex-col min-w-[72px] flex-1">
        <span className="text-sm font-medium text-foreground leading-tight truncate">
          {agent.name}
        </span>
        {/* a11y: text-foreground/60 ≥4.5:1 contrast; text-muted-foreground (3.4:1 light)
            fails wcag2aa at 12px */}
        <span className="text-xs text-foreground/60 leading-tight truncate">
          {statusText}
        </span>
      </div>

      {/* Mode Pill — Shadcn Badge variant outline.
          ★ SACRED RN-4: `@[24rem]:inline-flex` = container query on panel width.
          NEVER change to viewport breakpoint (md:inline-flex). */}
      <Badge
        variant="outline"
        data-testid={testIds?.chatModePill ?? "chat-mode-pill"}
        className="hidden min-w-0 max-w-[110px] truncate text-[11px] @[24rem]:inline-flex"
      >
        {modeLabel}
      </Badge>

      {/* Action buttons: nueva conv · historial (toggle) · colapsar supervisor */}
      <div className="flex shrink-0 items-center gap-0.5">
        <Button
          variant="ghost"
          size="icon"
          aria-label="Nueva conversación"
          title="Nueva conversación"
          onClick={newConversation}
          className="h-8 w-8"
        >
          <Plus className="size-4" aria-hidden="true" />
        </Button>
        <Button
          variant="ghost"
          size="icon"
          aria-label={historyLabel}
          title={historyLabel}
          aria-pressed={historyOpen}
          onClick={toggleHistory}
          className="h-8 w-8"
        >
          <Clock className="size-4" aria-hidden="true" />
        </Button>
        <Button
          variant="ghost"
          size="icon"
          aria-label={`Colapsar a ${agent.name}`}
          title={`Colapsar a ${agent.name}`}
          onClick={collapseSupervisor}
          className="h-8 w-8"
        >
          <PanelLeftClose className="size-4" aria-hidden="true" />
        </Button>
      </div>
    </header>
  );
}
