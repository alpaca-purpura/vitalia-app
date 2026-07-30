// cap: adrian.inbox
// story-origin: TBD
/**
 * ConversationItem.tsx — Single row in the conversation list.
 *
 * Displays:
 *   - Patient name (PHI — rendered via text but no PiiMaskedSpan here since
 *     name is passed as prop already resolved; PHI wrapping happens at the
 *     data-fetching layer in ConversationList).
 *   - Channel icon + last message preview
 *   - Relative time (last_message_at)
 *   - Badges: 🔴 help_needed · 📎 unread_media_count > 0
 *   - Stage chip (stage_decision when set)
 *   - aria-selected for keyboard navigation
 *
 * Memoized (React.memo) — list can have 50+ items.
 * Server Component NOT possible (needs onClick). "use client" at parent level.
 *
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 */

import { memo } from "react";
import { cn } from "@/lib/cn";
import { useTenantLocale } from "@/hooks/useTenantLocale";
import { SocialLogo } from "@/components/shared/channels/SocialLogo";
import {
  brandColorAlpha,
  getSocialChannel,
} from "@/lib/channels/social-channels";
import { StageBadge } from "./StageBadge";
import type { Conversation } from "@/features/crm-shared";

/**
 * Formats ISO 8601 date to relative label (hoy/ayer/dd MMM).
 * Per master-data.md: uses Intl.DateTimeFormat with tenant timezone+locale for fallback.
 * Accepts tenant timezone + locale to keep pure function (no hook dependency).
 */
function formatRelativeTime(
  iso: string,
  timezone: string,
  locale: string,
): string {
  const date = new Date(iso);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMin = Math.floor(diffMs / 60_000);
  if (diffMin < 60) return `${diffMin}m`;
  const diffH = Math.floor(diffMin / 60);
  if (diffH < 24) return `${diffH}h`;
  const diffD = Math.floor(diffH / 24);
  if (diffD === 1) return "Ayer";
  if (diffD < 7) return `${diffD}d`;
  // Fallback: locale-aware short date with tenant timezone (never hardcoded "es-419")
  return new Intl.DateTimeFormat(locale, {
    day: "numeric",
    month: "short",
    timeZone: timezone,
  }).format(date);
}

interface ConversationItemProps {
  conversation: Conversation;
  isSelected: boolean;
  onSelect: (id: string) => void;
  /** Patient name (PHI resolved by parent — already masked/role-gated upstream) */
  patientName: string;
  className?: string;
}

/**
 * ConversationItem — list row for a single conversation.
 * Memoized to prevent unnecessary re-renders when parent list re-renders.
 */
export const ConversationItem = memo(function ConversationItem({
  conversation,
  isSelected,
  onSelect,
  patientName,
  className,
}: ConversationItemProps) {
  const { timezone, locale } = useTenantLocale();
  const {
    id,
    channel,
    help_needed,
    unread_media_count,
    stage_decision,
    last_message_at,
    last_message_preview,
    handler_mode,
  } = conversation;

  // Per master-data.md: pass tenant timezone+locale — never hardcoded locale
  const relTime = formatRelativeTime(last_message_at, timezone, locale);
  const isAiMode = handler_mode === "ai";

  return (
    <li
      role="option"
      aria-selected={isSelected}
      data-testid="conversation-item"
      onClick={() => onSelect(id)}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          onSelect(id);
        }
      }}
      tabIndex={0}
      className={cn(
        "flex cursor-pointer flex-col gap-1 px-4 py-3",
        // Constant 3px left rail (transparent until selected) — avoids layout shift.
        "border-b vt-border border-l-[3px] transition-colors",
        "focus-visible:outline focus-visible:outline-2",
        "focus-visible:outline-inset focus-visible:vt-outline-primary",
        !isSelected && "border-l-transparent hover:vt-bg-muted",
        className,
      )}
      // Selected (UI-AUDIT-2 #3): the mini-card wears the SOCIAL NETWORK color
      // (soft fill + brand rail) so you see at a glance which channel + which conv.
      style={
        isSelected
          ? {
              backgroundColor: brandColorAlpha(channel, 0.12),
              borderLeftColor: getSocialChannel(channel).brandColorVar,
            }
          : undefined
      }
    >
      {/* Row 1: Name + time + badges (channel logo moved to bottom-right, UI-AUDIT-2 #3) */}
      <div className="flex items-center gap-2">
        {/* Patient name — bolder when selected; foreground color so it reads on
            ANY channel-tinted selected bg (UI-AUDIT-3 — cian clashed with green/pink). */}
        <span
          className={cn(
            "min-w-0 flex-1 truncate text-sm vt-text-foreground",
            isSelected ? "font-semibold" : "font-medium",
          )}
        >
          {patientName}
        </span>

        {/* Indicators */}
        <div className="flex shrink-0 items-center gap-1">
          {help_needed && (
            <span
              data-testid="help-needed-badge"
              aria-label="Adrián pide ayuda"
              title="Adrián pide ayuda"
              className="text-xs"
            >
              🔴
            </span>
          )}
          {unread_media_count > 0 && (
            <span
              data-testid="unread-media-badge"
              aria-label={`${unread_media_count} archivo sin abrir`}
              title={`${unread_media_count} archivo sin abrir`}
              className="text-xs"
            >
              📎
            </span>
          )}
          {/* AI mode indicator */}
          {isAiMode && (
            <span
              aria-label="Adrián activo"
              title="Adrián activo"
              className="inline-flex h-4 w-4 items-center justify-center rounded-full vt-bg-primary/20 text-[10px]"
              aria-hidden="true"
            >
              ✦
            </span>
          )}
        </div>

        {/* Relative time */}
        <time
          dateTime={last_message_at}
          className="shrink-0 text-[10px] vt-text-muted"
        >
          {relTime}
        </time>
      </div>

      {/* Row 2: Last message preview */}
      {last_message_preview && (
        <p className="truncate text-xs vt-text-muted">
          {last_message_preview}
        </p>
      )}

      {/* Row 3: Stage chip (left) + REAL social logo bottom-right (UI-AUDIT-2 #3) */}
      <div className="flex items-center justify-between gap-2">
        {stage_decision ? (
          <StageBadge stage={stage_decision} data-testid="stage-chip" />
        ) : (
          <span aria-hidden />
        )}
        <SocialLogo
          channel={channel}
          size={16}
          title={getSocialChannel(channel).label}
          className="shrink-0"
        />
      </div>
    </li>
  );
});
