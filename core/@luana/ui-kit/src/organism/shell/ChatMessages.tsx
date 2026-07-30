// cap: platform.lift-shell-chrome-ui-kit
"use client";

/**
 * ChatMessages — brand-agnostic messages list panel.
 * T-K2 port of vitalia ChatMessages (F1-S6).
 *
 * Brand coupling removed:
 *   - useChatStore injected by prop
 *   - AGENT_CATALOG injected via agentCatalog prop (Record<slug, descriptor>)
 *   - DEFAULT_CHAT_AGENT replaced by supervisorSlug prop
 *   - getAgentClasses injected for TypingIndicator / DelegateMarker
 *   - supervisorBubbleBgClass injected for user bubble color
 *
 * Renders role="log" aria-live="polite" container with:
 * - Empty state when messages.length === 0
 * - Populated list: MessageBubble (bot/user) | DelegateMarker | TypingIndicator
 *
 * Auto-scroll: useEffect [messages.length] scrolls sentinel into view (smooth).
 *
 * Named export (NO default) per FSD-Lite enforce.
 */

import { useEffect, useRef } from "react";
import type {
  GetAgentClasses,
  ShellAgentDescriptor,
  ShellChatMessage,
  ShellChatStore,
  ShellChatStoreApi,
} from "./types";
import { MessageBubble } from "./MessageBubble";
import { TypingIndicator } from "./TypingIndicator";
import { DelegateMarker } from "./DelegateMarker";

// ─── EmptyStateChat ────────────────────────────────────────────────────────────

interface EmptyStateChatProps {
  supervisor: ShellAgentDescriptor;
  /** Brand-specific description text for empty state. */
  emptyStateDescription?: string;
}

/**
 * EmptyStateChat — empty state with supervisor avatar + heading + description.
 * Server-safe (no hooks) — declared inside 'use client' file because parent is client.
 */
function EmptyStateChat({ supervisor, emptyStateDescription }: EmptyStateChatProps) {
  const description = emptyStateDescription ??
    `Pregúntale a ${supervisor.name} lo que necesitas.`;

  return (
    <div className="flex-1 flex items-center justify-center">
      <div className="text-center max-w-[260px]">
        <div
          className="h-16 w-16 rounded-full overflow-hidden mx-auto mb-3"
          aria-hidden="true"
        >
          {supervisor.thumbnail ? (
            <img
              src={supervisor.thumbnail}
              alt=""
              className="h-16 w-16 object-cover"
            />
          ) : (
            <div className="h-16 w-16 rounded-full bg-muted flex items-center justify-center">
              <span className="text-2xl font-bold text-muted-foreground select-none">
                {supervisor.initial}
              </span>
            </div>
          )}
        </div>
        <p className="text-sm font-medium text-foreground mb-1">
          Empieza una conversación
        </p>
        <p className="text-xs text-muted-foreground">
          {description}
        </p>
      </div>
    </div>
  );
}

// ─── ChatMessages ──────────────────────────────────────────────────────────────

export interface ChatMessagesProps {
  /** Injected chat store — kit NEVER imports brand chat store directly. */
  useChatStore: ShellChatStore;
  /** Supervisor descriptor (default agent for messages). */
  supervisor: ShellAgentDescriptor;
  /** Full agent catalog (slug → descriptor). */
  agentCatalog: Record<string, ShellAgentDescriptor>;
  /** Brand fn returning Tailwind class bundles for agent slugs. */
  getAgentClasses: GetAgentClasses;
  /** CSS class for user bubble background (brand token). */
  userBubbleBgClass?: string;
  /** Optional description for the empty state. */
  emptyStateDescription?: string;
  className?: string;
}

/**
 * ChatMessages — messages container with aria-live announcements and auto-scroll.
 * role="log" is the correct ARIA role for chat message history.
 * aria-live="polite" announces new messages to screen readers.
 */
export function ChatMessages({
  useChatStore,
  supervisor,
  agentCatalog,
  getAgentClasses,
  userBubbleBgClass,
  emptyStateDescription,
  className,
}: ChatMessagesProps) {
  const messages = useChatStore((s: ShellChatStoreApi) => s.messages);
  const sentinelRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    sentinelRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length]);

  const resolveAgent = (slug?: string): ShellAgentDescriptor =>
    (slug ? agentCatalog[slug] : null) ?? supervisor;

  const renderMessage = (msg: ShellChatMessage) => {
    switch (msg.role) {
      case "bot":
        return (
          <MessageBubble
            key={msg.id}
            role="bot"
            content={msg.content ?? ""}
            agent={resolveAgent(msg.agent)}
            time={msg.time}
          />
        );

      case "user":
        return (
          <MessageBubble
            key={msg.id}
            role="user"
            content={msg.content ?? ""}
            time={msg.time}
            userBubbleBgClass={userBubbleBgClass}
          />
        );

      case "delegate": {
        const fromAgent = resolveAgent(msg.fromAgent);
        const toAgent = resolveAgent(msg.toAgent);
        return (
          <DelegateMarker
            key={msg.id}
            fromAgent={fromAgent}
            toAgent={toAgent}
            getAgentClasses={getAgentClasses}
            mode={msg.delegateMode ?? "Mantener"}
          />
        );
      }

      case "thinking":
        return (
          <TypingIndicator
            key={msg.id}
            agent={resolveAgent(msg.agent)}
            getAgentClasses={getAgentClasses}
            text={msg.content}
          />
        );

      default:
        return null;
    }
  };

  return (
    <div
      data-testid="chat-messages"
      role="log"
      aria-live="polite"
      aria-label={`Conversación con ${supervisor.name}`}
      // a11y (axe wcag2aa scrollable-region-focusable): una región scrollable
      // debe ser alcanzable por teclado. tabIndex={0} permite enfocarla y
      // scrollear con flechas sin mouse.
      tabIndex={0}
      className={`flex-1 min-h-0 overflow-y-auto px-4 py-4 flex flex-col gap-3 ${className ?? ""}`}
    >
      {messages.length === 0 ? (
        <EmptyStateChat
          supervisor={supervisor}
          emptyStateDescription={emptyStateDescription}
        />
      ) : (
        <>
          {messages.map((msg) => renderMessage(msg))}
          {/* Auto-scroll sentinel */}
          <div ref={sentinelRef} aria-hidden="true" />
        </>
      )}
    </div>
  );
}
