// cap: public_landing.public-clinic-landing
// story-origin: TBD
/**
 * ConnectionBadge — 4-state sync status badge with CSS token coloring.
 * States: idle | running | error | disconnected
 * Colors: vt-text-success/warning/danger/neutral CSS vars — NEVER hardcoded HEX.
 *
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 */
"use client";

import { forwardRef } from "react";
import { cn } from "@/lib/cn";
import type { SyncStatus } from "../types/channel";
import { MARKETING_COPY } from "../copy";

export type ConnectionBadgeVariant = "default" | "success";

export type ConnectionBadgeProps = {
  status: SyncStatus;
  /** Override variant — pass "success" to force green (e.g., recently connected idle) */
  variant?: ConnectionBadgeVariant;
  label?: string;
  className?: string;
};

function getStatusClasses(
  status: SyncStatus,
  variant?: ConnectionBadgeVariant,
): string {
  if (variant === "success") {
    return "vt-text-success";
  }
  switch (status) {
    case "idle":
      return "vt-text-neutral";
    case "running":
      return "vt-text-warning";
    case "error":
      return "vt-text-danger";
    case "disconnected":
      return "vt-text-danger";
    default:
      return "vt-text-neutral";
  }
}

function getDefaultLabel(status: SyncStatus): string {
  switch (status) {
    case "idle":
      return MARKETING_COPY.channels.idleStatus;
    case "running":
      return MARKETING_COPY.channels.runningStatus;
    case "error":
      return MARKETING_COPY.channels.errorStatus;
    case "disconnected":
      return MARKETING_COPY.channels.disconnectedStatus;
    default:
      return status;
  }
}

/**
 * ConnectionBadge — pill badge showing channel sync status.
 * Uses CSS var tokens (vt-text-*) exclusively — no hardcoded colors.
 */
export const ConnectionBadge = forwardRef<
  HTMLSpanElement,
  ConnectionBadgeProps
>(({ status, variant, label, className }, ref) => {
  const colorClass = getStatusClasses(status, variant);
  const displayLabel = label ?? getDefaultLabel(status);

  return (
    <span
      ref={ref}
      data-testid="connection-badge"
      data-state={status}
      className={cn(
        "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium",
        "vt-bg-surface-alt border vt-border",
        colorClass,
        className,
      )}
    >
      <span
        className="h-1.5 w-1.5 rounded-full bg-current"
        aria-hidden="true"
      />
      {displayLabel}
    </span>
  );
});
ConnectionBadge.displayName = "ConnectionBadge";
