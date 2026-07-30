// cap: adrian.inbox
// story-origin: TBD
"use client";

/**
 * AdrianToolsSheet.tsx — Read-only tools panel for Adrián's active tools.
 *
 * Right-side panel (420px). Displays tool invocations for the current conversation
 * in read-only mode. Tools cannot be manually invoked from the UI (HIPAA-lite:
 * tool invocations are Adrián's autonomous actions, not operator controls).
 *
 * Key behaviors:
 * - Opened via ToolsSheetTrigger in ThreadHeader (useInboxStore, not managed here)
 * - Tool invocations fetched via useToolsState (cached 30s)
 * - Shows hipaaGuardNote explaining why tools are disabled / read-only
 * - Links to /offer-studio to configure tool behavior
 *
 * Per 03-arch-fe.md § 7: Panel pattern (right side, slide-over).
 * Per hipaa-lite.md: tools display PHI-safe summaries only (server-redacted).
 *
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 */

import { cn } from "@/lib/cn";
import { useToolsState } from "../../api/use-tools-state";
import { INBOX_COPY } from "../../lib/copy";
import { useTenantLocale } from "@/hooks/useTenantLocale";
import { formatTenantDateTime } from "@/lib/format/formatTenantDateTime";
import type {
  ToolInvocation,
  ToolInvocationStatus,
} from "../../types/inbox.types";

interface AdrianToolsSheetProps {
  /** Whether the panel is visible */
  open: boolean;
  /** Called when user clicks the close button */
  onClose: () => void;
  /** Conversation to load tools for */
  conversationId: string | null | undefined;
  /** Additional CSS classes */
  className?: string;
}

/** Status badge color variants — using vt-* semantic tokens per globals.css */
const STATUS_CLASSES: Record<ToolInvocationStatus, string> = {
  success: "vt-text-success vt-bg-success-12 vt-border-success-30",
  running: "vt-text-primary vt-bg-primary/10 border-transparent",
  completed: "vt-text-success vt-bg-success-12 vt-border-success-30",
  error: "vt-text-danger vt-bg-danger-soft vt-border-danger-soft",
  failed: "vt-text-danger vt-bg-danger-soft vt-border-danger-soft",
  pending: "vt-text-muted vt-bg-muted/20 border-transparent",
  skipped: "vt-text-muted vt-bg-muted/10 border-transparent",
};

/** Maps invocation status to display copy */
function statusLabel(status: ToolInvocationStatus): string {
  if (status === "success") return INBOX_COPY.toolsSheet.statusEnabled;
  return INBOX_COPY.toolsSheet.statusDisabled;
}

/** Single tool invocation row (read-only) */
function ToolRow({
  invocation,
  timezone,
  locale,
}: {
  invocation: ToolInvocation;
  timezone: string;
  locale: string;
}) {
  return (
    <li
      data-testid={`tool-row-${invocation.tool_name}`}
      className={cn(
        "rounded-lg border vt-border p-3 space-y-1.5",
        "vt-bg-surface",
      )}
    >
      {/* Tool name + status badge */}
      <div className="flex items-center justify-between gap-2">
        <span className="text-sm font-medium vt-text-foreground truncate">
          {invocation.tool_name}
        </span>
        <span
          className={cn(
            "inline-flex shrink-0 items-center px-2 py-0.5 text-xs font-medium rounded-[var(--radius-pill)] border",
            STATUS_CLASSES[invocation.status],
          )}
        >
          {statusLabel(invocation.status)}
        </span>
      </div>

      {/* Result summary (server-rendered Spanish neutro, PHI-safe) */}
      {invocation.result_summary && (
        <p className="text-xs vt-text-muted leading-snug">
          {invocation.result_summary}
        </p>
      )}

      {/* Invoked timestamp — per master-data.md: formatTenantDateTime (never toLocaleDateString) */}
      <p className="text-xs vt-text-faint">
        {INBOX_COPY.toolsSheet.lastUsed.replace(
          "{date}",
          invocation.invoked_at ? formatTenantDateTime(invocation.invoked_at, timezone, locale) : "—",
        )}
      </p>
    </li>
  );
}

/**
 * AdrianToolsSheet — right slide-over panel showing Adrián's tool invocations.
 * Read-only. Tools cannot be manually triggered from this panel (HIPAA-lite).
 */
export function AdrianToolsSheet({
  open,
  onClose,
  conversationId,
  className,
}: AdrianToolsSheetProps) {
  const { data: toolsState, isLoading } = useToolsState(conversationId);
  const { timezone, locale } = useTenantLocale();

  if (!open) return null;

  const invocations = toolsState?.invocations ?? [];

  return (
    /* Backdrop overlay */
    <div
      className="fixed inset-0 z-40 flex justify-end"
      role="presentation"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      {/* Dimmed backdrop */}
      <div className="absolute inset-0 bg-black/25" aria-hidden="true" />

      {/* Sheet panel */}
      <aside
        data-testid="adrian-tools-sheet"
        role="complementary"
        aria-label={INBOX_COPY.toolsSheet.ariaLabel}
        className={cn(
          "relative z-10 flex flex-col h-full w-[420px] max-w-full",
          "vt-bg-surface border-l vt-border shadow-xl",
          "overflow-y-auto",
          className,
        )}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b vt-border shrink-0">
          <h2 className="text-sm font-semibold vt-text-foreground">
            {INBOX_COPY.toolsSheet.title}
          </h2>
          <button
            data-testid="tools-sheet-close"
            onClick={onClose}
            aria-label="Cerrar panel de herramientas"
            className={cn(
              "inline-flex items-center justify-center rounded-md p-1.5",
              "vt-text-muted hover:vt-text-foreground hover:vt-bg-muted/40",
              "transition-colors focus-visible:outline focus-visible:outline-2",
              "focus-visible:outline-[var(--vitalia-cian)]",
            )}
          >
            {/* Close icon */}
            <svg
              aria-hidden="true"
              className="w-4 h-4"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        {/* HIPAA guard note (read-only explanation) — vt-* semantic tokens per globals.css */}
        <div
          data-testid="hipaa-guard-note"
          className={cn(
            "mx-5 mt-4 p-3 rounded-lg border",
            "vt-border-warning-30 vt-bg-warning-12 vt-text-warning",
            "text-xs leading-snug",
          )}
          role="note"
        >
          {INBOX_COPY.toolsSheet.hipaaGuardNote}
        </div>

        {/* Body — tool list or empty */}
        <div className="flex-1 px-5 py-4 space-y-3">
          {isLoading ? (
            /* Loading skeleton */
            <div
              className="space-y-2"
              aria-busy="true"
              aria-label="Cargando herramientas…"
            >
              {[1, 2, 3].map((i) => (
                <div
                  key={i}
                  className="h-16 rounded-lg vt-bg-muted/20 animate-pulse"
                />
              ))}
            </div>
          ) : invocations.length === 0 ? (
            /* Empty state */
            <p className="text-sm vt-text-muted text-center py-8">
              {INBOX_COPY.toolsSheet.noTools}
            </p>
          ) : (
            /* Tool invocation list (read-only) */
            <ul
              className="space-y-2"
              aria-label={INBOX_COPY.toolsSheet.ariaLabel}
            >
              {invocations.map((inv) => (
                <ToolRow
                  key={`${inv.tool_name}-${inv.invoked_at}`}
                  invocation={inv}
                  timezone={timezone}
                  locale={locale}
                />
              ))}
            </ul>
          )}
        </div>

        {/* Footer — link to offer studio */}
        <div className="shrink-0 px-5 py-4 border-t vt-border">
          <a
            data-testid="offer-studio-link"
            href="/offer-studio"
            className={cn(
              "inline-flex items-center gap-1 text-xs font-medium",
              "text-[var(--vitalia-cian)] hover:underline",
              "focus-visible:outline focus-visible:outline-2",
              "focus-visible:outline-[var(--vitalia-cian)]",
            )}
          >
            {INBOX_COPY.toolsSheet.goToOfferStudio}
          </a>
        </div>
      </aside>
    </div>
  );
}
