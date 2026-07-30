// cap: adrian.inbox
// story-origin: TBD
"use client";

/**
 * ModeToggle.tsx — 2-state segmented control for Adrián handler mode (Chris UI #3).
 *
 * Maps UI segment values to API mode:
 *   "adrian-decide"  → handler_mode="ai" + proposal_required=false
 *   "adrian-consulta"→ handler_mode="ai" + proposal_required=true
 *
 * Manual typing is no longer a mode — it is the "Pausar Adrián" state, owned by
 * ThreadComposerDock (pause → composer enabled → you write).
 *
 * Each segment shows an icon + label + descriptive title so it's clear what it does
 * ("no se entiende que son" → readable labels + tooltips). Active = filled cian.
 *
 * OCC: Passes conversation.updated_at as If-Match ETag via useModeToggle.
 * On 409 conflict: optimistic rollback + caller shows conflict toast.
 *
 * Accessibility: role="radiogroup" container + role="radio" buttons + aria-checked.
 * INP < 200ms: optimistic update via useModeToggle (no waiting for server).
 *
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 */

import { Sparkles, ClipboardCheck } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { INBOX_COPY } from "../../lib/copy";
import { cn } from "@/lib/cn";
import type { SegmentedModeValue } from "../../hooks/use-mode-toggle";

interface ModeToggleProps {
  /** Current segment value (derived from conversation.handler_mode + proposal_required) */
  value: SegmentedModeValue;
  /** Called when user selects a new segment */
  onChange: (value: SegmentedModeValue) => void;
  /** Whether a mode change mutation is in-flight */
  isPending?: boolean;
  /** Whether the last mutation resulted in a 409 OCC conflict */
  isConflict?: boolean;
  className?: string;
}

/** Ordered segment definitions for rendering */
const SEGMENTS: Array<{
  value: SegmentedModeValue;
  label: string;
  title: string;
  icon: LucideIcon;
}> = [
  {
    value: "adrian-decide",
    label: INBOX_COPY.segmentedMode.adrianDecide,
    title: INBOX_COPY.segmentedMode.adrianDecideHint,
    icon: Sparkles,
  },
  {
    value: "adrian-consulta",
    label: INBOX_COPY.segmentedMode.adrianConsulta,
    title: INBOX_COPY.segmentedMode.adrianConsultaHint,
    icon: ClipboardCheck,
  },
];

/**
 * ModeToggle — inline 2-state toggle for conversation handler mode.
 * Uses role="radiogroup" / role="radio" pattern for accessibility (WCAG 2.1 AA).
 */
export function ModeToggle({
  value,
  onChange,
  isPending = false,
  isConflict = false,
  className,
}: ModeToggleProps) {
  return (
    <div
      role="radiogroup"
      aria-label={INBOX_COPY.segmentedMode.ariaLabel}
      data-testid="segmented-control-3-modes"
      data-conflict={isConflict ? "true" : undefined}
      className={cn(
        "inline-flex items-center gap-0.5 rounded-lg border vt-border vt-bg-surface p-0.5",
        isConflict && "ring-2 ring-red-400",
        className,
      )}
    >
      {SEGMENTS.map((seg) => {
        const isActive = seg.value === value;
        const Icon = seg.icon;
        return (
          <button
            key={seg.value}
            type="button"
            role="radio"
            aria-checked={isActive}
            title={seg.title}
            data-testid={`segment-${seg.value}`}
            disabled={isPending}
            onClick={() => {
              if (!isActive) onChange(seg.value);
            }}
            className={cn(
              "inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs transition-colors cursor-pointer",
              "focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2",
              "focus-visible:outline-[var(--agent-adrian)]",
              "disabled:opacity-50 disabled:cursor-not-allowed",
              // Active = green ("encendido / atendiendo") per Chris UI #2.
              isActive
                ? "vt-bg-success text-white font-semibold shadow-sm"
                : "vt-text-muted hover:vt-bg-muted font-medium",
            )}
          >
            <Icon className="h-3.5 w-3.5 shrink-0" aria-hidden focusable={false} />
            <span>{seg.label}</span>
          </button>
        );
      })}
    </div>
  );
}
