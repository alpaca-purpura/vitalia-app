// cap: platform.lift-shell-chrome-ui-kit
"use client";

/**
 * ChatPanel — brand-agnostic chat organism root (ex-ValeriaChat).
 * T-K2 port of vitalia ValeriaChat (F1-S6).
 *
 * Brand coupling removed: supervisor identity + stores + catalog + classes all
 * injected by prop. Static agent/status/mode props replaced by prop injection.
 *
 * ★ SACRED RN-4 (2026-06-11 live-fix — grid implicit column):
 *   `grid-cols-[minmax(0,1fr)]` + `min-w-0` MUST stay verbatim.
 *
 *   Root cause: without explicit grid-cols, CSS creates an implicit `auto` column
 *   track that sizes to the WIDEST content (~604px) instead of the container.
 *   Result: messages/composer render wide and get clipped by overflow-hidden as
 *   the panel narrows. `grid-cols-[minmax(0,1fr)]` forces the track to the real
 *   container width → texts re-wrap. `min-w-0` prevents the grid item from
 *   refusing to shrink below its content minimum-width.
 *   NEVER simplify this pattern.
 *
 * Composes ChatHeader + ChatMessages + ChatComposer in a 3-row CSS Grid:
 *   grid-rows-[auto_1fr_auto]
 *   - Row 1 (auto): ChatHeader — fixed height
 *   - Row 2 (1fr): ChatMessages — flex-1 overflow-y-auto, fills available space
 *   - Row 3 (auto): ChatComposer — fixed height
 *
 * "use client" required: composes Client Components.
 * Named export (NO default) per FSD-Lite enforce.
 */

import { cn } from "@luana/format/utils";
import type {
  GetAgentClasses,
  ShellAgentDescriptor,
  ShellChatStore,
  ShellStore,
  ShellTestIds,
} from "./types";
import { ChatHeader } from "./ChatHeader";
import { ChatMessages } from "./ChatMessages";
import { ChatComposer } from "./ChatComposer";

export interface ChatPanelProps {
  /** Resolved supervisor descriptor (chat agent). */
  supervisor: ShellAgentDescriptor;
  /** Full agent catalog (slug → descriptor) for message resolution. */
  agentCatalog: Record<string, ShellAgentDescriptor>;
  status?: "online" | "offline";
  mode?: "agent" | "web";
  /** Injected stores — kit NEVER imports brand stores directly. */
  useShellStore: ShellStore;
  useChatStore: ShellChatStore;
  /** Brand fn returning Tailwind class bundles for agent slugs. */
  getAgentClasses: GetAgentClasses;
  /** Brand-specific status dot class (e.g. "bg-vitalia-success"). */
  statusDotClass?: string;
  /** CSS class for user bubble background (brand token). */
  userBubbleBgClass?: string;
  /** Optional description for empty state. */
  emptyStateDescription?: string;
  /** Optional testIds override (e2e contract). */
  testIds?: ShellTestIds;
  className?: string;
}

/**
 * ChatPanel — 3-row CSS Grid chat organism (ex-ValeriaChat).
 *
 * Layout contract:
 *   Parent MUST provide h-full (or explicit height) for 1fr row to expand.
 *   SupervisorSidebar wraps this in h-full container — already satisfied.
 *
 * ★ SACRED: grid-cols-[minmax(0,1fr)] + min-w-0 VERBATIM (RN-4 live-fix 2026-06-11).
 * ★ @container on root: ChatHeader uses container query @[24rem]:inline-flex for mode pill.
 */
export function ChatPanel({
  supervisor,
  agentCatalog,
  status = "online",
  mode = "agent",
  useShellStore,
  useChatStore,
  getAgentClasses,
  statusDotClass,
  userBubbleBgClass,
  emptyStateDescription,
  testIds,
  className,
}: ChatPanelProps) {
  return (
    <section
      role="region"
      aria-label={`Chat con ${supervisor.name}`}
      data-testid={testIds?.chat ?? "supervisor-chat"}
      // ★ SACRED RN-4 (2026-06-11 live-fix): grid-rows sin cols explícitas crea columna
      // implícita `auto` que trackea al CONTENIDO más ancho → mensajes/composer recortados
      // por overflow-hidden al achicar el panel. `grid-cols-[minmax(0,1fr)]` fuerza el
      // track al ancho real → textos re-wrappean. + min-w-0 (item del grid del aside
      // no shrinkeaba bajo su contenido). NEVER simplify.
      className={cn(
        "@container grid min-w-0 grid-rows-[auto_1fr_auto] grid-cols-[minmax(0,1fr)] overflow-hidden h-full bg-background",
        className,
      )}
    >
      <ChatHeader
        agent={supervisor}
        status={status}
        mode={mode}
        useShellStore={useShellStore}
        useChatStore={useChatStore}
        getAgentClasses={getAgentClasses}
        statusDotClass={statusDotClass}
        testIds={testIds}
      />
      <ChatMessages
        useChatStore={useChatStore}
        supervisor={supervisor}
        agentCatalog={agentCatalog}
        getAgentClasses={getAgentClasses}
        userBubbleBgClass={userBubbleBgClass}
        emptyStateDescription={emptyStateDescription}
      />
      <ChatComposer
        useChatStore={useChatStore}
        supervisorName={supervisor.name}
        composerInputId={testIds?.composerPlaceholder ?? "shell-chat-composer"}
      />
    </section>
  );
}
