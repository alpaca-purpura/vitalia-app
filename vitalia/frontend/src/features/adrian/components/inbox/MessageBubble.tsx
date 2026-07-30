// cap: adrian.inbox
// story-origin: TBD
"use client";

/**
 * MessageBubble.tsx — Renders a single message in the conversation thread.
 *
 * Fork adapter from nicolify/closer-studio/components/inbox/MessageBubble.tsx.
 * Retokenization: violet-* → vt-* CSS utility classes + vitalia CSS vars.
 * sender_type adapted: "patient" | "agent_ai" | "agent_human" | "system"
 *   (nicolify used "user" | "assistant" | "system" with different semantics).
 *
 * Renders:
 *   - "patient" → right-aligned dark bubble (patient message)
 *   - "agent_ai" → left-aligned with gradient_adrian avatar + "✨ auto" chip
 *                  + ActionReceiptUndoChip if within 5-minute window
 *   - "agent_human" → left-aligned human avatar (no undo chip)
 *   - "system" → centered pill (info/event notification)
 *
 * XSS safety (SC-04): React default escaping — NO dangerouslySetInnerHTML.
 * All text content rendered via JSX `{}` interpolation (React escapes HTML entities).
 *
 * Media rendering:
 *   - media_kind="audio" → VoiceMessagePlayer
 *   - media_kind="image" → ImageAnalysisCard
 *   - media_kind="video"|"document"|"sticker" → stub label (Slice 2)
 *
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 */

import { Check, CheckCheck } from "lucide-react";
import { cn } from "@/lib/cn";
import { useTenantLocale } from "@/hooks/useTenantLocale";
import { getSocialChannel } from "@/lib/channels/social-channels";
import { VoiceMessagePlayer } from "./VoiceMessagePlayer";
import { ImageAnalysisCard } from "./ImageAnalysisCard";
import { ActionReceiptUndoChip } from "./ActionReceiptUndoChip";
import { INBOX_COPY } from "../../lib/copy";
import type { Message } from "../../types/inbox.types";

export interface MessageBubbleProps {
  message: Message;
  /** ISO 8601 updated_at from the parent conversation (used for OCC if-match) */
  conversationUpdatedAt: string;
  /** Patient first name (for system message context) */
  patientName?: string | null;
  /** Conversation channel — tints the outgoing bubble with the network color (#2c). */
  channel?: string;
  className?: string;
}

// ─── Media content renderer ───────────────────────────────────────────────────

function MessageContent({ message }: { message: Message }) {
  // Audio message
  if (message.media_kind === "audio" && message.media_url) {
    return (
      <VoiceMessagePlayer
        mediaUrl={message.media_url}
        durationS={message.media_duration_s}
        transcriptionText={message.transcription_text}
        transcriptionConfidence={message.transcription_confidence}
      />
    );
  }

  // Image message
  if (message.media_kind === "image" && message.media_url) {
    return <ImageAnalysisCard mediaUrl={message.media_url} />;
  }

  // Video / document / sticker (Slice 2 stubs)
  if (message.media_kind === "video") {
    return (
      <span className="text-xs vt-text-muted italic">
        {INBOX_COPY.multimedia.documentLabel}
      </span>
    );
  }
  if (message.media_kind === "document") {
    return (
      <span className="text-xs vt-text-muted italic">
        {INBOX_COPY.multimedia.documentLabel}
      </span>
    );
  }
  if (message.media_kind === "sticker") {
    return (
      <span className="text-xs vt-text-muted italic">
        {INBOX_COPY.multimedia.stickerLabel}
      </span>
    );
  }

  // Text message — React escapes body_text by default (SC-04: no dangerouslySetInnerHTML)
  if (message.body_text) {
    return (
      // NOTE (SC-04): {message.body_text} is React JSX interpolation — React automatically
      // escapes HTML entities. <script>alert('xss')</script> renders as literal text.
      <span className="text-sm leading-relaxed whitespace-pre-wrap break-words">
        {message.body_text}
      </span>
    );
  }

  return null;
}

// ─── System message ───────────────────────────────────────────────────────────

function SystemMessage({ message }: { message: Message }) {
  return (
    <div
      className="flex justify-center my-1"
      role="status"
      aria-live="polite"
      data-testid="message-bubble-system"
    >
      <span
        className={cn(
          "text-xs vt-text-muted px-3 py-1 rounded-full",
          "vt-bg-muted border vt-border-soft",
        )}
      >
        {/* SC-04: React escapes body_text — no dangerouslySetInnerHTML */}
        {message.body_text}
      </span>
    </div>
  );
}

// ─── Timestamp helper (WhatsApp-style per-bubble hour) ────────────────────────

/** Formats a message timestamp as HH:mm in the tenant timezone/locale (UI-AUDIT #3). */
function formatBubbleTime(
  iso: string,
  timezone: string,
  locale: string,
): string {
  try {
    return new Intl.DateTimeFormat(locale, {
      hour: "2-digit",
      minute: "2-digit",
      timeZone: timezone,
    }).format(new Date(iso));
  } catch {
    return "";
  }
}

// ─── Delivery receipt (WhatsApp-style ✓ / ✓✓) ────────────────────────────────

/** Outgoing-only delivery receipt: ✓ sent · ✓✓ delivered · ✓✓ (cian) read. */
function DeliveryReceipt({
  status,
}: {
  status: "sent" | "delivered" | "read";
}) {
  if (status === "sent") {
    return (
      <Check className="h-3 w-3 vt-text-muted" aria-label="Enviado" focusable={false} />
    );
  }
  const isRead = status === "read";
  return (
    <CheckCheck
      className={cn("h-3 w-3", isRead ? "vt-text-cian" : "vt-text-muted")}
      aria-label={isRead ? "Leído" : "Entregado"}
      focusable={false}
    />
  );
}

// ─── Main MessageBubble ───────────────────────────────────────────────────────

/**
 * MessageBubble — renders one message with correct layout per sender_type.
 *
 * Orientation (UI-AUDIT #4 — WhatsApp business inbox convention):
 *   - patient (the customer, incoming)         → LEFT, clear surface bubble
 *   - agent_ai / agent_human (us, outgoing)    → RIGHT, brand-filled bubble
 * Each bubble carries its own HH:mm timestamp (UI-AUDIT #3).
 *
 * No per-bubble avatar (UI-AUDIT-2 #2 — saves precious horizontal width). The
 * "who sent this turn" label (Adrián · Auto / Tú · Manual / patient name) is
 * rendered once above each turn block by InboxThread.
 */
export function MessageBubble({
  message,
  conversationUpdatedAt,
  channel,
  className,
}: MessageBubbleProps) {
  const { timezone, locale } = useTenantLocale();
  const {
    sender_type,
    retracted_at,
    action_receipt_expires_at,
    conversation_id,
    sent_at,
  } = message;

  // System messages get special centered pill layout
  if (sender_type === "system") {
    return <SystemMessage message={message} />;
  }

  const isPatient = sender_type === "patient";
  const isAI = sender_type === "agent_ai";
  const isHuman = sender_type === "agent_human";

  const isRetracted = retracted_at !== null;

  // Determine if ActionReceiptUndoChip should be shown
  const showUndoChip =
    isAI && action_receipt_expires_at !== null && !isRetracted;

  const timeLabel = formatBubbleTime(sent_at, timezone, locale);

  // Outgoing (Adrián/human) bubble = SOLID surface tinted with the channel color
  // (#2c — combines with the channel-tinted wallpaper). Opaque via --vt-bubble-base.
  const isOutgoing = isAI || isHuman;
  const outgoingBg =
    isOutgoing && !isRetracted && channel
      ? `color-mix(in srgb, ${getSocialChannel(channel).brandColorVar} 14%, var(--vt-bubble-base))`
      : undefined;

  return (
    <div
      className={cn(
        "flex gap-2 max-w-[85%]",
        // Patient on the LEFT (incoming); Adrián/human on the RIGHT (outgoing).
        isPatient ? "mr-auto flex-row" : "ml-auto flex-row-reverse",
        className,
      )}
      data-testid="message-bubble"
      data-sender={sender_type}
    >
      {/* Bubble body (no avatar — turn label is rendered by InboxThread) */}
      <div
        className={cn(
          "flex flex-col gap-1 min-w-0",
          isPatient ? "items-start" : "items-end",
        )}
      >
        {/* Message content bubble */}
        <div
          className={cn(
            // shadow-sm lifts every bubble off the wallpaper so none reads as
            // "transparent" (UI-AUDIT-3 — WhatsApp-style elevation).
            "rounded-2xl px-3 py-2 text-sm shadow-sm",
            // Patient (incoming, left): clear white surface bubble — easy to read
            isPatient &&
              !isRetracted &&
              "vt-bg-surface vt-text-foreground border vt-border rounded-tl-sm",
            // Outgoing (Adrián/human, right): solid channel-tinted bubble (bg via style)
            isOutgoing &&
              !isRetracted &&
              "vt-text-foreground border vt-border-soft rounded-tr-sm",
            // Retracted: muted strikethrough
            isRetracted &&
              "vt-bg-muted vt-text-muted border vt-border-soft line-through opacity-60",
            isRetracted && (isPatient ? "rounded-tl-sm" : "rounded-tr-sm"),
          )}
          style={outgoingBg ? { backgroundColor: outgoingBg } : undefined}
        >
          {isRetracted ? (
            <span className="text-xs italic" aria-label="Mensaje revertido">
              [Mensaje revertido]
            </span>
          ) : (
            <>
              <MessageContent message={message} />
              {/* WhatsApp-style hour + delivery receipt (✓/✓✓) for outgoing (UI-AUDIT #3) */}
              {timeLabel && (
                <div className="mt-0.5 flex items-center justify-end gap-1">
                  <time
                    dateTime={sent_at}
                    className="text-[10px] tabular-nums vt-text-muted"
                    data-testid="message-bubble-time"
                  >
                    {timeLabel}
                  </time>
                  {isOutgoing && (
                    <DeliveryReceipt
                      status={message.delivery_status ?? "sent"}
                    />
                  )}
                </div>
              )}
            </>
          )}
        </div>

        {/* ActionReceiptUndoChip — only for AI messages within 5-min window */}
        {showUndoChip && (
          <div className="flex justify-end">
            <ActionReceiptUndoChip
              messageId={message.id}
              conversationId={conversation_id}
              expiresAt={action_receipt_expires_at!}
              conversationUpdatedAt={conversationUpdatedAt}
            />
          </div>
        )}
      </div>
    </div>
  );
}
