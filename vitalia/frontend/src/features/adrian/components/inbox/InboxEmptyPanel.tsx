// cap: adrian.inbox
// story-origin: vitalia-fase2-adrian-inbox
/**
 * InboxEmptyPanel.tsx — rich empty state for the thread + contact panes (UI-AUDIT #1).
 *
 * Replaces the old plain-text placeholder ("Selecciona una conversación…") with an
 * icon + message + a faded skeleton behind it (so it reads as "content is coming"
 * instead of a dead label). Two variants:
 *   - "thread"  → ghost message bubbles behind
 *   - "contact" → ghost avatar + field rows behind
 *
 * Shown only when there are NO conversations at all (auto-select opens the newest
 * one otherwise — see AdrianInboxView + ConversationListPanel).
 *
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 */

import { MessagesSquare, Contact } from "lucide-react";
import { cn } from "@/lib/cn";
import { INBOX_COPY } from "../../lib/copy";

interface InboxEmptyPanelProps {
  variant: "thread" | "contact";
  className?: string;
  /** Forwarded so callers keep the data-testid the layout/tests expect. */
  "data-testid"?: string;
}

/** Faded skeleton of message bubbles (behind the thread empty message). */
function ThreadSkeleton() {
  return (
    <div
      aria-hidden="true"
      className="absolute inset-0 flex flex-col gap-3 px-6 py-6 opacity-30 [mask-image:linear-gradient(to_bottom,black,transparent)]"
    >
      <div className="h-9 w-2/3 animate-pulse rounded-2xl rounded-tl-sm vt-bg-muted" />
      <div className="h-9 w-1/2 animate-pulse self-end rounded-2xl rounded-tr-sm vt-bg-muted" />
      <div className="h-14 w-3/5 animate-pulse rounded-2xl rounded-tl-sm vt-bg-muted" />
      <div className="h-9 w-2/5 animate-pulse self-end rounded-2xl rounded-tr-sm vt-bg-muted" />
      <div className="h-9 w-1/2 animate-pulse rounded-2xl rounded-tl-sm vt-bg-muted" />
    </div>
  );
}

/** Faded skeleton of contact fields (behind the contact empty message). */
function ContactSkeleton() {
  return (
    <div
      aria-hidden="true"
      className="absolute inset-0 flex flex-col gap-4 px-5 py-6 opacity-30 [mask-image:linear-gradient(to_bottom,black,transparent)]"
    >
      <div className="h-12 w-full animate-pulse rounded-lg vt-bg-muted" />
      <div className="flex flex-col gap-1.5">
        <div className="h-3 w-16 animate-pulse rounded vt-bg-muted" />
        <div className="h-4 w-3/4 animate-pulse rounded vt-bg-muted" />
      </div>
      <div className="flex flex-col gap-1.5">
        <div className="h-3 w-16 animate-pulse rounded vt-bg-muted" />
        <div className="h-4 w-2/3 animate-pulse rounded vt-bg-muted" />
      </div>
      <div className="flex flex-col gap-1.5">
        <div className="h-3 w-16 animate-pulse rounded vt-bg-muted" />
        <div className="h-4 w-1/2 animate-pulse rounded vt-bg-muted" />
      </div>
    </div>
  );
}

/**
 * InboxEmptyPanel — icon + message + faded skeleton for an empty thread/contact pane.
 */
export function InboxEmptyPanel({
  variant,
  className,
  "data-testid": dataTestid,
}: InboxEmptyPanelProps) {
  const isThread = variant === "thread";
  const Icon = isThread ? MessagesSquare : Contact;
  const heading = isThread
    ? INBOX_COPY.thread.emptyHeading
    : INBOX_COPY.thread.contactEmptyHeading;
  const body = isThread
    ? INBOX_COPY.thread.emptyBody
    : INBOX_COPY.thread.contactEmptyBody;

  return (
    <div
      role="status"
      aria-live="polite"
      data-testid={dataTestid}
      className={cn(
        "relative flex h-full w-full items-center justify-center overflow-hidden p-6",
        className,
      )}
    >
      {isThread ? <ThreadSkeleton /> : <ContactSkeleton />}

      {/* Foreground message — sits above the faded skeleton */}
      <div className="relative z-10 flex max-w-[15rem] flex-col items-center gap-2 text-center">
        <span
          className={cn(
            "flex h-12 w-12 items-center justify-center rounded-full",
            "vt-bg-cian-8 vt-text-cian",
          )}
        >
          <Icon className="h-6 w-6" aria-hidden focusable={false} />
        </span>
        <p className="text-sm font-semibold vt-text-foreground">{heading}</p>
        <p className="text-xs leading-relaxed vt-text-muted">{body}</p>
      </div>
    </div>
  );
}
