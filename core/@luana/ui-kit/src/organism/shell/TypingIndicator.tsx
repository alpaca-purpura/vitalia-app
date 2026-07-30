// cap: platform.lift-shell-chrome-ui-kit
"use client";

/**
 * TypingIndicator — brand-agnostic rich typing bubble.
 * T-K2 port of vitalia TypingIndicator (F1-S6).
 *
 * Brand coupling removed: agent descriptor + class bundle injected by prop.
 * NO import from brand _agent-tw-classes or AGENT_CATALOG.
 *
 * CSS keyframe `.typing-dot` defined in the brand's globals.css (vitalia F1-S6).
 * Kit consumers are responsible for including that keyframe.
 *
 * CRITICAL: No dynamic class construction (e.g. `bg-${slug}-soft`).
 * All class names come from the injected getAgentClasses bundle.
 *
 * Named export (NO default) per FSD-Lite enforce.
 */

import { cn } from "@luana/format/utils";
import type { AgentClassBundle, GetAgentClasses, ShellAgentDescriptor } from "./types";

export interface TypingIndicatorProps {
  /** Resolved agent descriptor that is typing. */
  agent: ShellAgentDescriptor;
  /** Brand fn returning Tailwind class bundles for agent slugs. */
  getAgentClasses: GetAgentClasses;
  /** Override the action text (e.g. "está abriendo Voz del paciente").
   *  If omitted: "{agent.name} está escribiendo…" */
  text?: string;
  className?: string;
}

/**
 * TypingIndicator — renders a rich typing bubble.
 *
 * Layout:
 *   [agent-soft bg bubble]
 *     <AgentName> <actionText> [...animated dots]
 *
 * Dots animated via CSS @keyframes typing-dot (nth-child delays in brand globals.css).
 * aria-hidden on dots (decorative animation).
 */
export function TypingIndicator({
  agent,
  getAgentClasses,
  text,
  className,
}: TypingIndicatorProps) {
  const classes: AgentClassBundle = getAgentClasses(agent.slug);
  const actionText = text ?? `${agent.name} está escribiendo…`;

  // Split: if starts with agent name, show name bold + rest normal
  const namePrefix = agent.name + " ";
  let namePart = agent.name;
  let restPart = actionText;

  if (actionText.startsWith(namePrefix)) {
    restPart = actionText.slice(namePrefix.length);
  } else {
    // Custom text — show as-is without name highlighting
    namePart = "";
    restPart = actionText;
  }

  return (
    <div
      className={cn("flex flex-col gap-1 self-start max-w-[80%]", className)}
    >
      <div
        data-testid="msg-thinking"
        data-agent={agent.slug}
        className={cn(
          "rounded-2xl rounded-bl-sm px-3 py-2 text-sm leading-relaxed flex items-center gap-2",
          classes.softBg,
        )}
      >
        {namePart ? (
          <span className={cn("font-medium", classes.accentText)}>
            {namePart}
          </span>
        ) : null}
        {/* a11y: text-foreground/80 gives ≥4.5:1 contrast on agent-soft bg in both light+dark. */}
        <span className="text-foreground/80">{restPart}</span>
        <span className="flex items-end gap-0.5 ml-1" aria-hidden="true">
          <span
            className={cn(
              "typing-dot h-1.5 w-1.5 rounded-full",
              classes.accentBg,
            )}
          />
          <span
            className={cn(
              "typing-dot h-1.5 w-1.5 rounded-full",
              classes.accentBg,
            )}
          />
          <span
            className={cn(
              "typing-dot h-1.5 w-1.5 rounded-full",
              classes.accentBg,
            )}
          />
        </span>
      </div>
    </div>
  );
}
