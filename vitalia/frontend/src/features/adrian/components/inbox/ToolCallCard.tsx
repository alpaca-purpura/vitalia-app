// cap: adrian.inbox
// story-origin: vitalia-fase2-adrian-inbox
/**
 * ToolCallCard.tsx — T-5 NEW.
 *
 * Collapsible inline card for agent tool-call display in the thread.
 *
 * Shows: "Adrián usó `{tool_name}` → {result_summary}"
 * Collapsed by default. Expand to see full result JSON.
 *
 * Consumed by InboxThread for messages with type "tool" or "tool_call".
 *
 * Accessibility: uses <details>/<summary> for native browser expand/collapse
 * (keyboard accessible, no JS needed for toggle state).
 *
 * No "use client" needed — uses <details> which is native HTML.
 * Parent (InboxThread) is already a client component.
 *
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 */

import { cn } from "@/lib/cn";

// ── Types ────────────────────────────────────────────────────────────────────

export interface ToolCallCardProps {
  /** Tool name (e.g. "check_availability", "get_patient_details") */
  toolName: string;
  /**
   * Short summary of the result shown inline.
   * e.g. "3 turnos disponibles" or "Error: paciente no encontrado"
   */
  resultSummary?: string | null;
  /**
   * Full result payload (JSON-stringifiable) for the expanded detail.
   * Optional — if not provided, the card is not expandable.
   */
  resultPayload?: unknown;
  /** Whether the tool call resulted in an error */
  isError?: boolean;
  className?: string;
}

// ── ToolCallCard ─────────────────────────────────────────────────────────────

/**
 * ToolCallCard — collapsible inline card for tool-call messages.
 *
 * Renders a <details> element so the toggle is:
 * - Keyboard accessible natively (Enter/Space on summary)
 * - Screen-reader friendly (role=group with accessible name)
 * - No JS needed for open/close state
 */
export function ToolCallCard({
  toolName,
  resultSummary,
  resultPayload,
  isError = false,
  className,
}: ToolCallCardProps) {
  const hasDetail =
    resultPayload !== undefined &&
    resultPayload !== null;

  const summaryText = resultSummary ?? (isError ? "Error al ejecutar" : "Completado");

  return (
    <div
      className={cn(
        "rounded-lg border px-3 py-2 text-xs font-mono",
        "vt-border vt-bg-muted/40",
        isError && "border-red-200 bg-red-50/40 dark:border-red-900/30 dark:bg-red-950/20",
        className,
      )}
      data-testid="tool-call-card"
      data-tool-name={toolName}
      data-is-error={isError ? "true" : undefined}
    >
      {hasDetail ? (
        <details>
          <summary
            className={cn(
              "cursor-pointer select-none list-none",
              "flex items-center gap-1.5",
              "focus-visible:outline focus-visible:outline-2 focus-visible:rounded",
              "focus-visible:outline-[var(--agent-adrian)]",
              isError ? "text-red-600 dark:text-red-400" : "vt-text-muted",
            )}
            aria-label={`Detalle de herramienta ${toolName}`}
          >
            <span aria-hidden="true" className="text-[10px]">▶</span>
            <span className="font-semibold vt-text-foreground">{toolName}</span>
            <span className="vt-text-muted">→</span>
            <span>{summaryText}</span>
          </summary>

          {/* Expanded detail */}
          <pre
            className={cn(
              "mt-2 overflow-x-auto whitespace-pre-wrap break-all",
              "rounded-md vt-bg-muted/60 p-2 text-[10px]",
              "vt-text-foreground",
            )}
            aria-label={`Resultado completo de ${toolName}`}
          >
            {typeof resultPayload === "string"
              ? resultPayload
              : JSON.stringify(resultPayload, null, 2)}
          </pre>
        </details>
      ) : (
        /* Non-expandable: simple row */
        <div
          className={cn(
            "flex items-center gap-1.5",
            isError ? "text-red-600 dark:text-red-400" : "vt-text-muted",
          )}
        >
          <span className="font-semibold vt-text-foreground">{toolName}</span>
          <span className="vt-text-muted">→</span>
          <span>{summaryText}</span>
        </div>
      )}
    </div>
  );
}
