// cap: adrian.inbox
// story-origin: TBD
"use client";

/**
 * ActivityStream.tsx — Sticky activity stream bar for Adrián's trace events.
 *
 * Collapses to 32px header bar / expands to 240px scrollable event list.
 * Polls every 5s while expanded (via useActivityStream with enabled flag).
 * Shows last 8 events (most recent first), pre-sanitized server-side.
 *
 * Per 03-arch-fe.md § 7:
 *   - Sticky bottom of conversation thread pane
 *   - Expanded state controlled by useInboxStore.expandedActivityStream
 *   - useActivityStream polled only when expanded (enabled=expandedActivityStream)
 *
 * PHI note: payload_redacted is pre-sanitized server-side. FE never receives PHI here.
 *
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 */

import { Activity } from "lucide-react";
import { cn } from "@/lib/cn";
import { useActivityStream } from "../../api/use-activity-stream";
import { useInboxStore } from "../../store/inbox-store";
import { INBOX_COPY } from "../../lib/copy";
import { useTenantLocale } from "@/hooks/useTenantLocale";
import { formatTenantTime } from "@/lib/format/formatTenantTime";
import { ToolCallCard } from "./ToolCallCard";
import type { ActivityEvent, ActivityEventKind } from "../../types/inbox.types";

/** Max events to show in the stream (last N, chronological order reversed) */
const MAX_VISIBLE_EVENTS = 8;

/** Icon mapping per event kind (emoji fallbacks — no external icon dependency) */
const KIND_ICONS: Record<ActivityEventKind, string> = {
  tool_call: "🔧",
  llm_call: "🤖",
  turn_start: "▶",
  turn_end: "⏹",
  proposal_generated: "📋",
  mode_changed: "🔄",
  message_sent: "💬",
  message_retracted: "↩",
  adrian_paused: "⏸",
  compliance_blocked: "🚫",
  nudge_sent: "📤",
};

interface ActivityStreamProps {
  /** Conversation to stream activity for */
  conversationId: string | null | undefined;
  /** Additional CSS classes for outer wrapper */
  className?: string;
}

/** Single activity event row */
function ActivityEventItem({
  event,
  index,
  timezone,
  locale,
}: {
  event: ActivityEvent;
  index: number;
  timezone: string;
  locale: string;
}) {
  const kindLabel =
    INBOX_COPY.activityStream.eventKinds[event.kind] ?? event.kind;
  const icon = KIND_ICONS[event.kind] ?? "•";

  return (
    <li
      data-testid={`activity-event-item-${index}`}
      className="flex items-start gap-2 py-1.5 border-b vt-border-soft last:border-0"
    >
      {/* Kind icon */}
      <span aria-hidden="true" className="shrink-0 text-xs leading-5">
        {icon}
      </span>

      {/* Content — tool_call events render as a collapsible ToolCallCard */}
      <div className="flex-1 min-w-0">
        {event.kind === "tool_call" ? (
          <ToolCallCard
            toolName={
              typeof event.payload_redacted?.tool_name === "string"
                ? event.payload_redacted.tool_name
                : kindLabel
            }
            resultSummary={event.summary}
            resultPayload={event.payload_redacted ?? undefined}
            isError={event.payload_redacted?.is_error === true}
          />
        ) : (
          <>
            <span className="text-xs font-medium vt-text-foreground mr-1">
              {kindLabel}
            </span>
            <span className="text-xs vt-text-muted truncate">
              {event.summary}
            </span>
          </>
        )}
      </div>

      {/* Timestamp — per master-data.md: formatTenantTime (never toLocaleTimeString) */}
      <time
        dateTime={event.occurred_at}
        className="shrink-0 text-xs vt-text-faint tabular-nums"
        title={event.occurred_at}
      >
        {formatTenantTime(event.occurred_at, timezone, locale)}
      </time>
    </li>
  );
}

/**
 * AgentActivityStream — sticky bottom bar showing Adrián's recent trace events.
 * Collapsed: 32px header bar with toggle.
 * Expanded: 240px scrollable list of last 8 events.
 */
export function ActivityStream({
  conversationId,
  className,
}: ActivityStreamProps) {
  const expanded = useInboxStore((s) => s.expandedActivityStream);
  const toggleActivityStream = useInboxStore((s) => s.toggleActivityStream);
  const { timezone, locale } = useTenantLocale();

  const { data, isLoading } = useActivityStream(conversationId, expanded);

  // Last MAX_VISIBLE_EVENTS events (most recent last in array from BE → show slice from end)
  const allEvents: ActivityEvent[] = data?.events ?? [];
  const visibleEvents = allEvents.slice(-MAX_VISIBLE_EVENTS);

  return (
    <div
      data-testid="agent-activity-stream"
      className={cn(
        "flex flex-col border-t vt-border vt-bg-surface transition-all duration-200 ease-in-out",
        expanded ? "min-h-[240px] max-h-[240px]" : "h-8",
        className,
      )}
      aria-label={INBOX_COPY.activityStream.ariaLabel}
    >
      {/* Header bar — always visible, 32px */}
      <div className="flex items-center justify-between px-3 h-8 shrink-0">
        {/* Title */}
        <span className="inline-flex items-center gap-1.5 text-xs font-medium vt-text-muted select-none">
          <Activity className="h-3.5 w-3.5 shrink-0" aria-hidden focusable={false} />
          {INBOX_COPY.activityStream.title}
        </span>

        {/* Toggle button */}
        <button
          data-testid="activity-stream-toggle"
          onClick={toggleActivityStream}
          aria-expanded={expanded}
          aria-label={
            expanded
              ? INBOX_COPY.activityStream.collapseAriaLabel
              : INBOX_COPY.activityStream.expandAriaLabel
          }
          aria-controls="activity-stream-body"
          className={cn(
            "inline-flex items-center justify-center w-6 h-6 rounded",
            "vt-text-muted hover:vt-text-foreground hover:vt-bg-muted/40",
            "transition-colors focus-visible:outline focus-visible:outline-2",
            "focus-visible:outline-[var(--vitalia-cian)]",
          )}
        >
          {/* Chevron icon — rotates on expand */}
          <svg
            aria-hidden="true"
            className={cn(
              "w-3.5 h-3.5 transition-transform",
              expanded ? "rotate-180" : "",
            )}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2.5}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M5 15l7-7 7 7"
            />
          </svg>
        </button>
      </div>

      {/* Body — events list, only rendered when expanded */}
      {expanded && (
        <div
          id="activity-stream-body"
          className="flex-1 overflow-y-auto px-3 pb-2"
        >
          {isLoading ? (
            <div
              aria-busy="true"
              aria-label="Cargando actividad…"
              className="space-y-1 py-1"
            >
              {[1, 2, 3].map((i) => (
                <div
                  key={i}
                  className="h-7 rounded vt-bg-muted/20 animate-pulse"
                />
              ))}
            </div>
          ) : visibleEvents.length === 0 ? (
            <p className="text-xs vt-text-muted py-3 text-center">
              {INBOX_COPY.activityStream.empty}
            </p>
          ) : (
            <ul
              data-testid="activity-event-list"
              aria-label={INBOX_COPY.activityStream.ariaLabel}
              className="space-y-0"
            >
              {visibleEvents.map((event, idx) => (
                <ActivityEventItem
                  key={event.id}
                  event={event}
                  index={idx}
                  timezone={timezone}
                  locale={locale}
                />
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
