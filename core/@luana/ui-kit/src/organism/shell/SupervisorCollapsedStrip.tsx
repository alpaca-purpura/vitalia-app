// cap: platform.lift-shell-chrome-ui-kit
"use client";

/**
 * SupervisorCollapsedStrip — state-A tira-avatar (~44px vertical strip).
 * T-K2 port of vitalia ValeriaCollapsedStrip (vitalia-shell-core-hardening T-3).
 *
 * Rendered at the left edge when the supervisor is CLOSED (state A,
 * supervisorOpen='closed'). Behaviour-fidelity, not pixel:
 *   - REAL supervisor avatar (brand thumbnail) with onError → initial fallback.
 *   - decorative status dot (aria-hidden) — color via injected statusDotClass.
 *   - supervisor label (vertical, hover-discoverable affordance).
 *   - whole strip is one <button> → openSupervisor() reopens to B (chat-only,
 *     no history · RN-12 / SC-5). focus-visible ring.
 *
 * Brand data flows by prop: supervisorName / supervisorThumbnail / supervisorInitial
 * / supervisorSoftBg (getAgentClasses(...).softBg) / statusDotClass / testIds.
 * Zero brand tokens in logic (RN-2).
 *
 * "use client" required: onClick + img onError useState.
 *
 * data-testid preserved EXACT (brand-injected via testIds):
 * supervisorCollapsedStrip, supervisorStripStatusDot.
 */

import { useState } from "react";
import { cn } from "@luana/format/utils";

export interface SupervisorCollapsedStripProps {
  /** open the supervisor in chat (store action). */
  onOpenSupervisor: () => void;
  supervisorName: string;
  /** avatar image src; falls back to initial circle on error/absent. */
  supervisorThumbnail?: string;
  supervisorInitial?: string;
  /** soft bg class for the avatar circle (getAgentClasses(supervisorSlug).softBg). */
  supervisorSoftBg?: string;
  /** status-dot bg class (brand token, e.g. "bg-emerald-500"). */
  statusDotClass?: string;
  /** brand e2e testids. */
  stripTestId?: string;
  statusDotTestId?: string;
  /** aria-label (Spanish neutro; brand passes e.g. "Abrir a Valeria"). */
  openLabel: string;
  className?: string;
}

/**
 * SupervisorCollapsedStrip — 44px vertical tira-avatar for state A.
 * Click reopens the supervisor into chat (history stays closed · RN-12).
 */
export function SupervisorCollapsedStrip({
  onOpenSupervisor,
  supervisorName,
  supervisorThumbnail,
  supervisorInitial,
  supervisorSoftBg,
  statusDotClass,
  stripTestId,
  statusDotTestId,
  openLabel,
  className,
}: SupervisorCollapsedStripProps) {
  const [imgError, setImgError] = useState(false);
  const showInitial = imgError || !supervisorThumbnail;

  return (
    <button
      type="button"
      aria-label={openLabel}
      data-testid={stripTestId}
      onClick={onOpenSupervisor}
      className={cn(
        "group flex w-11 shrink-0 flex-col items-center gap-3 border-r border-border bg-card py-3",
        "transition-colors hover:bg-accent/40",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-inset",
        className,
      )}
    >
      {/* Avatar 7×7 con status dot — REAL brand asset, onError → initial */}
      <span className="relative shrink-0">
        <span
          className={cn(
            "flex h-7 w-7 items-center justify-center overflow-hidden rounded-full",
            supervisorSoftBg,
          )}
          aria-hidden="true"
        >
          {showInitial ? (
            <span className="text-xs font-semibold text-white select-none">
              {supervisorInitial}
            </span>
          ) : (
            <img
              src={supervisorThumbnail}
              alt=""
              className="h-7 w-7 object-cover"
              onError={() => setImgError(true)}
            />
          )}
        </span>
        <span
          data-testid={statusDotTestId}
          className={cn(
            "absolute bottom-0 right-0 h-2 w-2 rounded-full ring-2 ring-card",
            statusDotClass,
          )}
          aria-hidden="true"
        />
      </span>

      {/* Vertical supervisor label — hover-discoverable */}
      <span
        className="text-xs font-medium tracking-wide text-foreground/70 [writing-mode:vertical-rl] rotate-180 group-hover:text-foreground"
        aria-hidden="true"
      >
        {supervisorName}
      </span>
    </button>
  );
}
