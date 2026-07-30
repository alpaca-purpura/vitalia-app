// cap: adrian.inbox
// story-origin: TBD
"use client";

/**
 * ConversationThread.tsx — Main thread panel for a single conversation.
 *
 * Fork adapter from nicolify/closer-studio/components/inbox/ConversationThread.tsx.
 * Retokenization: violet-* → vt-purpura-* · amber-* → vt-surface-warning.
 * Header replaced by ThreadHeader (SegmentedControl3Modes + VoiceStyleChip + buttons).
 *
 * Renders:
 *   1. ThreadHeader — mode control + pause + tools + contact sidebar toggle
 *   2. Messages list — scrollable, auto-scrolls to bottom on new messages
 *   3. Empty/loading/error states
 *
 * Message bubbles (full MessageBubble component) deferred to T-inbox-fe-6.
 * This ticket: ThreadHeader assembly + scaffold message list.
 *
 * OCC conflict toast: shows inline error message via isConflict state.
 * Full toast implementation: T-inbox-fe-6.
 *
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 */

import { Fragment, useEffect, useRef } from "react";
import { cn } from "@/lib/cn";
import { useConversationDetail } from "@/features/crm-shared";
import { useTenantLocale } from "@/hooks/useTenantLocale";
import {
  brandColorAlpha,
  getSocialChannel,
} from "@/lib/channels/social-channels";
import { INBOX_COPY } from "../../lib/copy";
import { ThreadHeader } from "./ThreadHeader";
import { ActivityStream } from "./ActivityStream";
import { MessageBubble } from "./MessageBubble";
import { ComposerArea } from "./ComposerArea";
import { PauseAdrianButton } from "./PauseAdrianButton";

/** Centered day-separator pill (WhatsApp pattern · UI-AUDIT #3). */
function DaySeparator({ label }: { label: string }) {
  return (
    <div className="flex justify-center" role="separator" aria-label={label}>
      <span className="rounded-full border vt-border-soft vt-bg-surface px-3 py-0.5 text-[11px] font-medium vt-text-muted shadow-sm">
        {label}
      </span>
    </div>
  );
}

interface InboxThreadProps {
  /** Conversation ID from URL state (?lead=...) */
  conversationId: string;
  className?: string;
}

/** Skeleton row for loading state */
function MessageSkeleton({ width }: { width: string }) {
  return (
    <div
      className={cn("h-10 animate-pulse rounded-xl vt-bg-muted", width)}
      aria-hidden="true"
    />
  );
}

/** Per-turn sender label above a block of consecutive same-sender messages
 *  (UI-AUDIT-2 #2 — replaces the per-bubble A/H avatars to save width). */
function TurnHeader({
  senderType,
  patientName,
}: {
  senderType: string;
  patientName: string | null;
}) {
  const isPatient = senderType === "patient";
  let dot = "vt-bg-muted";
  let text: string;
  let textClass = "vt-text-muted";
  if (senderType === "agent_ai") {
    dot = "vt-bg-cian";
    text = INBOX_COPY.thread.turnAdrian;
    textClass = "vt-text-cian";
  } else if (senderType === "agent_human") {
    dot = "vt-bg-azul-marino";
    text = INBOX_COPY.thread.turnYou;
    textClass = "vt-text-foreground";
  } else {
    text = (patientName ?? "Paciente").trim().split(/\s+/)[0] || "Paciente";
  }
  return (
    <div
      className={cn(
        "flex px-1 pt-1",
        isPatient ? "justify-start" : "justify-end",
      )}
    >
      {/* Pill with a solid bg so the label never blends into the wallpaper (#2b) */}
      <span className="inline-flex items-center gap-1 rounded-full border vt-border-soft vt-bg-surface px-2 py-0.5 shadow-sm">
        <span className={cn("h-1.5 w-1.5 rounded-full", dot)} aria-hidden />
        <span
          className={cn("text-[10px] font-semibold leading-none", textClass)}
        >
          {text}
        </span>
      </span>
    </div>
  );
}

/** Per-channel chat wallpaper: a tiled watermark of the REAL social-network logo.
 *  Chris UI #1: cream/white ink (var(--vt-watermark-ink)) instead of the faint
 *  brand-color tint, at a higher opacity so the logos actually read — the channel
 *  cue is still carried by the color tint behind. Generic channels (email/web)
 *  render no logo. Dark-safe (warm near-white ink + higher dark opacity). */
function ChatWallpaper({ channel }: { channel: string }) {
  const meta = getSocialChannel(channel);
  if (meta.kind !== "social" || !meta.logoPath) return null;
  const pid = `vt-wp-${meta.slug}`;
  return (
    <svg
      aria-hidden="true"
      className="pointer-events-none absolute inset-0 h-full w-full opacity-50"
      style={{ color: "var(--vt-watermark-ink)" }}
    >
      <defs>
        <pattern
          id={pid}
          width="120"
          height="120"
          patternUnits="userSpaceOnUse"
          patternTransform="rotate(-12)"
        >
          <g fill="currentColor">
            <path d={meta.logoPath} transform="translate(14 16) scale(1.5)" />
            <path d={meta.logoPath} transform="translate(74 78) scale(0.95)" />
          </g>
        </pattern>
      </defs>
      <rect width="100%" height="100%" fill={`url(#${pid})`} />
    </svg>
  );
}

/** Day bucket key (YYYY-MM-DD in tenant tz) for grouping messages by day. */
function fmtDayKey(iso: string, tz: string): string {
  try {
    return new Intl.DateTimeFormat("en-CA", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      timeZone: tz,
    }).format(new Date(iso));
  } catch {
    return iso.slice(0, 10);
  }
}

/** Human day label: Hoy / Ayer / "14 de mayo" (tenant tz + locale). */
function dayLabel(iso: string, tz: string, locale: string): string {
  const key = fmtDayKey(iso, tz);
  const today = fmtDayKey(new Date().toISOString(), tz);
  const yesterdayDate = new Date();
  yesterdayDate.setDate(yesterdayDate.getDate() - 1);
  const yesterday = fmtDayKey(yesterdayDate.toISOString(), tz);
  if (key === today) return INBOX_COPY.thread.dayToday;
  if (key === yesterday) return INBOX_COPY.thread.dayYesterday;
  try {
    return new Intl.DateTimeFormat(locale, {
      day: "numeric",
      month: "long",
      timeZone: tz,
    }).format(new Date(iso));
  } catch {
    return key;
  }
}

/**
 * ConversationThread — full thread panel.
 * Client Component: owns scroll behavior + conversation detail query.
 */
export function InboxThread({
  conversationId,
  className,
}: InboxThreadProps) {
  const {
    data: detail,
    isLoading,
    isError,
  } = useConversationDetail(conversationId);
  const { timezone, locale } = useTenantLocale();
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [detail?.messages]);

  if (isLoading) {
    return (
      <div
        className={cn("flex flex-col h-full", className)}
        data-testid="conversation-thread"
        aria-busy="true"
      >
        {/* Loading header placeholder */}
        <div className="px-4 py-3 border-b vt-border shrink-0">
          <div className="h-8 w-48 animate-pulse rounded-lg vt-bg-muted mb-2" />
          <div className="h-8 w-64 animate-pulse rounded-lg vt-bg-muted" />
        </div>
        {/* Loading messages */}
        <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3">
          <MessageSkeleton width="w-3/4" />
          <MessageSkeleton width="w-1/2 ml-auto" />
          <MessageSkeleton width="w-2/3" />
          <MessageSkeleton width="w-1/3 ml-auto" />
        </div>
      </div>
    );
  }

  if (isError || !detail) {
    return (
      <div
        className={cn(
          "flex flex-col h-full items-center justify-center gap-2 p-8 text-center",
          className,
        )}
        data-testid="conversation-thread-error"
        role="alert"
      >
        <p className="text-sm font-medium vt-text-foreground">
          {INBOX_COPY.errors.loadThread}
        </p>
        <p className="text-xs vt-text-muted">{INBOX_COPY.errors.retry}</p>
      </div>
    );
  }

  const pauseUntil = detail.conversation.pause_until;
  const isPaused = pauseUntil ? new Date(pauseUntil) > new Date() : false;

  return (
    <div
      className={cn("flex flex-col h-full min-h-0", className)}
      data-testid="conversation-thread"
    >
      {/* Thread header: mode control + tools + contact sidebar toggle */}
      <ThreadHeader detail={detail} />

      {/* Messages list — friendly WhatsApp-style wallpaper behind (UI-AUDIT-2 #5),
          day separators + per-turn sender labels (UI-AUDIT-2 #2), real MessageBubble. */}
      {/* Wallpaper layer is FIXED to the thread viewport (Chris UI #5): wash + tint
          + tiled logo live on this NON-scrolling wrapper; only the inner list scrolls,
          so the background never drags away leaving blank space below the messages. */}
      <div className="relative flex-1 min-h-0 vt-bg-chat-wash">
        {/* Channel-color tint — the dominant "which network" cue (UI-AUDIT-2 #5). */}
        <div
          aria-hidden="true"
          className="pointer-events-none absolute inset-0"
          style={{
            backgroundColor: brandColorAlpha(detail.conversation.channel, 0.04),
          }}
        />
        <ChatWallpaper channel={detail.conversation.channel} />
        <div
          ref={scrollRef}
          className="absolute inset-0 overflow-y-auto"
          aria-label="Mensajes de la conversación"
          data-testid="messages-list"
        >
          <div className="relative space-y-3 px-4 py-4">
          {detail.messages.length === 0 ? (
            <div className="flex items-center justify-center h-full">
              <p className="text-sm vt-text-muted">
                {INBOX_COPY.empty.noConversations.body}
              </p>
            </div>
          ) : (
            detail.messages.map((msg, i) => {
              const prev = i > 0 ? detail.messages[i - 1] : null;
              const showDay =
                !prev ||
                fmtDayKey(prev.sent_at, timezone) !==
                  fmtDayKey(msg.sent_at, timezone);
              const showTurn =
                msg.sender_type !== "system" &&
                (!prev || prev.sender_type !== msg.sender_type || showDay);
              return (
                <Fragment key={msg.id}>
                  {showDay && (
                    <DaySeparator
                      label={dayLabel(msg.sent_at, timezone, locale)}
                    />
                  )}
                  {showTurn && (
                    <TurnHeader
                      senderType={msg.sender_type}
                      patientName={detail.lead.name}
                    />
                  )}
                  <MessageBubble
                    message={msg}
                    conversationUpdatedAt={detail.conversation.updated_at}
                    patientName={detail.lead.name}
                    channel={detail.conversation.channel}
                  />
                </Fragment>
              );
            })
          )}
          </div>
        </div>
      </div>

      {/* Glass-box (RN-6 / AC-6): chronological activity stream of Adrián's actions.
          Self-managed collapse via useInboxStore.expandedActivityStream (toggle in
          ThreadHeader). Collapsed header always visible at the bottom of the thread. */}
      <ActivityStream conversationId={conversationId} className="shrink-0" />

      {/* Composer dock (Chris UI #2/#3): pause status + Pausar Adrián + always-on
          message box. Manual typing replaces the old "Yo escribo" mode; Pausar
          stops Adrián's auto-replies (60 min) so you can take over and write. */}
      <div
        className="shrink-0 border-t vt-border vt-bg-surface"
        data-testid="thread-composer-dock"
      >
        <div className="flex items-center justify-between gap-2 px-3 pt-2">
          <span className="inline-flex items-center gap-1.5 text-[11px] vt-text-muted">
            <span
              aria-hidden
              className={cn(
                "h-2 w-2 rounded-full",
                // Active = blinking green dot ("encendido / funcionando") · Chris UI #2.
                isPaused ? "vt-bg-muted" : "vt-bg-success animate-pulse",
              )}
            />
            {isPaused
              ? INBOX_COPY.composerDock.pausedHint
              : INBOX_COPY.composerDock.activeHint}
          </span>
          <PauseAdrianButton
            conversationId={detail.conversation.id}
            pauseUntil={pauseUntil}
          />
        </div>
        <ComposerArea
          conversation={detail.conversation}
          patientName={detail.lead.name}
        />
      </div>
    </div>
  );
}
