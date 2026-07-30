// cap: platform.lift-shell-chrome-ui-kit
"use client";

/**
 * MessageBubble — brand-agnostic chat bubble atom.
 * T-K2 port of vitalia MessageBubble (F1-S6).
 *
 * Brand coupling removed: agent descriptor injected by prop (not AGENT_CATALOG import).
 * Supervisor color class injected by prop (not hardcoded bg-agent-valeria).
 *
 * XSS guard: content rendered via JSX text children — React auto-escapes.
 * NEVER dangerouslySetInnerHTML.
 *
 * Named export (NO default) per FSD-Lite enforce.
 */

import { cn } from "@luana/format/utils";
import type { ShellAgentDescriptor } from "./types";

export interface MessageBubbleProps {
  role: "bot" | "user";
  content: string;
  time?: string;
  /** Agent descriptor for bot messages — determines footer label. */
  agent?: ShellAgentDescriptor;
  /** Override footer label (e.g. "Camila (vía Valeria)"). If not provided uses agent name. */
  footerLabel?: string;
  /** CSS class for the user bubble background (brand-injected, e.g. "bg-agent-valeria"). */
  userBubbleBgClass?: string;
  className?: string;
}

/**
 * MessageBubble — renders a single chat message bubble.
 *
 * Bot: left-aligned, bg-card with border, footer "AgentName · HH:MM"
 * User: right-aligned, userBubbleBgClass text-white, footer "HH:MM"
 *
 * Content is rendered as JSX text children (React auto-escapes — XSS safe).
 */
export function MessageBubble({
  role,
  content,
  time,
  agent,
  footerLabel,
  userBubbleBgClass = "bg-primary",
  className,
}: MessageBubbleProps) {
  if (role === "bot") {
    const label = footerLabel ?? agent?.name ?? "";

    return (
      <div
        className={cn("flex flex-col gap-1 self-start max-w-[80%]", className)}
      >
        <div
          data-testid="msg-bubble"
          data-role="bot"
          className="bg-card border border-border text-foreground rounded-2xl rounded-bl-sm px-3 py-2 text-sm leading-relaxed whitespace-pre-wrap"
        >
          {content}
        </div>
        {(time ?? label) ? (
          /* a11y: text-foreground/60 ≥4.5:1 contrast; text-muted-foreground (3.4:1 light) fails wcag2aa */
          <span className="text-[10px] text-foreground/60 px-1">
            {time ? `${label} · ${time}` : label}
          </span>
        ) : null}
      </div>
    );
  }

  // role === 'user'
  return (
    <div
      className={cn(
        "flex flex-col gap-1 self-end max-w-[80%] items-end",
        className,
      )}
    >
      <div
        data-testid="msg-bubble"
        data-role="user"
        className={cn(
          // text-white verbatim del original — el bg viene del brand vía
          // userBubbleBgClass (accent del supervisor, AA con white en paletas brand).
          "text-white rounded-2xl rounded-br-sm px-3 py-2 text-sm leading-relaxed whitespace-pre-wrap",
          userBubbleBgClass,
        )}
      >
        {content}
      </div>
      {time ? (
        /* a11y: text-foreground/60 ≥4.5:1 contrast */
        <span className="text-[10px] text-foreground/60 px-1">{time}</span>
      ) : null}
    </div>
  );
}
