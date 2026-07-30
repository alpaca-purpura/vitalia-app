// cap: agentic.lucas-daily-analysis
// story-origin: TBD
"use client";

/**
 * ActivityStreamSticky — collapsible activity stream panel.
 *
 * Height: 32px collapsed / 240px expanded.
 * Shows recent agent actions + user actions in chronological order.
 *
 * All colors via vt-* CSS classes from globals.css (no hsl literals in TSX).
 */

import { useState, useCallback } from "react";
import { cn } from "@/lib/cn";
import { AgentAttribution } from "../agents/AgentAttribution";
import type { AgentRole } from "../agents/agent-names";

export interface ActivityItem {
  id: string;
  type: "agent" | "user";
  agentRole?: AgentRole | string;
  userName?: string;
  action: string;
  target?: string;
  /** Already-formatted relative timestamp */
  timestamp: string;
}

export interface ActivityStreamStickyProps {
  /** Activity items to display (most recent first) */
  items?: ActivityItem[];
  /** Whether the stream is loading more items */
  isLoading?: boolean;
  /** Additional CSS classes */
  className?: string;
}

/**
 * Sticky collapsible activity stream.
 * 32px collapsed header / 240px expanded list.
 */
export function ActivityStreamSticky({
  items = [],
  isLoading = false,
  className,
}: ActivityStreamStickyProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const handleToggle = useCallback(() => {
    setIsExpanded((prev) => !prev);
  }, []);

  return (
    <div
      className={cn(
        "flex flex-col vt-bg-surface border vt-border",
        "rounded-[var(--radius-lg)] overflow-hidden",
        "transition-[max-height] duration-300 ease-in-out",
        isExpanded ? "max-h-60" : "max-h-8",
        className,
      )}
      aria-label="Flujo de actividad reciente"
    >
      {/* Collapsed header / toggle button */}
      <button
        onClick={handleToggle}
        className={cn(
          "flex items-center justify-between h-8 px-3 shrink-0",
          "text-xs font-medium vt-text-muted",
          "hover:vt-bg-muted transition-colors",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset vt-ring-cian",
        )}
        aria-expanded={isExpanded}
        aria-controls="activity-stream-list"
      >
        <span>Actividad reciente</span>
        <span
          aria-hidden="true"
          className="transition-transform duration-200"
          style={{ transform: isExpanded ? "rotate(180deg)" : "rotate(0deg)" }}
        >
          ↓
        </span>
      </button>

      {/* Expanded content */}
      <div
        id="activity-stream-list"
        className={cn(
          "overflow-y-auto divide-y vt-divide-border-soft",
          isExpanded ? "opacity-100" : "opacity-0 pointer-events-none",
        )}
        aria-hidden={!isExpanded}
        role="feed"
        aria-label="Lista de actividades"
        aria-busy={isLoading}
      >
        {/* Loading state */}
        {isLoading && (
          <div className="px-3 py-3 text-xs vt-text-muted" aria-live="polite">
            Cargando actividad...
          </div>
        )}

        {/* Empty state */}
        {!isLoading && items.length === 0 && (
          <div
            className="px-3 py-3 text-xs vt-text-faint text-center"
            aria-label="Sin actividad reciente"
          >
            Sin actividad reciente
          </div>
        )}

        {/* Activity items */}
        {items.map((item) => (
          <article
            key={item.id}
            className="px-3 py-2"
            aria-label={`Actividad: ${item.action}`}
          >
            {item.type === "agent" && item.agentRole ? (
              <AgentAttribution
                role={item.agentRole}
                action={item.action}
                target={item.target}
                timestamp={item.timestamp}
              />
            ) : (
              <div className="flex items-center gap-2 text-xs vt-text-muted">
                <span className="font-medium vt-text">
                  {item.userName ?? "Usuario"}
                </span>
                <span>{item.action}</span>
                {item.target && (
                  <span className="font-medium vt-text truncate max-w-[120px]">
                    {item.target}
                  </span>
                )}
                {item.timestamp && (
                  <span className="ml-auto vt-text-faint shrink-0">
                    {item.timestamp}
                  </span>
                )}
              </div>
            )}
          </article>
        ))}
      </div>
    </div>
  );
}
