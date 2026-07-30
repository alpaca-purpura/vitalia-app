// cap: platform.lift-shell-chrome-ui-kit
"use client";

/**
 * DelegateMarker — brand-agnostic agent handoff delegation marker.
 * T-K2 port of vitalia DelegateMarker (F1-S6 D4).
 *
 * Brand coupling removed: agent descriptors + class bundles injected by prop.
 * NO import from brand _agent-tw-classes or AGENT_CATALOG.
 *
 * Format: italic centered text-xs with agent thumbnail pill + mode label.
 * "→ delegando a [pill AgentName] (modo Mantener)"
 *
 * CRITICAL: No dynamic class construction — all class names from injected bundles.
 *
 * Named export (NO default) per FSD-Lite enforce.
 */

import { cn } from "@luana/format/utils";
import type { AgentClassBundle, GetAgentClasses, ShellAgentDescriptor } from "./types";

export interface DelegateMarkerProps {
  /** Agent that is delegating (unused visually but useful for future labeling). */
  fromAgent?: ShellAgentDescriptor;
  /** Agent receiving the delegation. */
  toAgent: ShellAgentDescriptor;
  /** Brand fn returning Tailwind class bundles for agent slugs. */
  getAgentClasses: GetAgentClasses;
  /** Mode label — e.g. 'Mantener', 'Reactivar', 'Multiplicar'. */
  mode?: string;
  className?: string;
}

/**
 * DelegateMarker — centered italic delegation marker.
 *
 * Renders: → delegando a [thumbnail] AgentName (modo {mode})
 */
export function DelegateMarker({
  toAgent,
  getAgentClasses,
  mode = "Mantener",
  className,
}: DelegateMarkerProps) {
  const toClasses: AgentClassBundle = getAgentClasses(toAgent.slug);

  return (
    <div
      data-testid="msg-delegate"
      className={cn(
        /* a11y: text-foreground/60 ≥4.5:1 contrast */
        "self-center text-xs italic text-foreground/60 flex items-center gap-1.5 py-1",
        className,
      )}
    >
      <span aria-hidden="true">→ delegando a</span>
      <span className="inline-flex items-center gap-1">
        {/* Agent thumbnail mini-circle */}
        <span
          className={cn(
            "h-4 w-4 rounded-full overflow-hidden flex items-center justify-center shrink-0",
            toClasses.accentBg,
          )}
          aria-hidden="true"
        >
          {toAgent.thumbnail ? (
            <img
              src={toAgent.thumbnail}
              alt=""
              className="h-4 w-4 object-cover"
            />
          ) : (
            <span className="text-[8px] font-semibold text-white select-none">
              {toAgent.initial}
            </span>
          )}
        </span>
        <span className={cn("font-medium not-italic", toClasses.accentText)}>
          {toAgent.name}
        </span>
      </span>
      <span className="text-foreground/60">(modo {mode})</span>
    </div>
  );
}
