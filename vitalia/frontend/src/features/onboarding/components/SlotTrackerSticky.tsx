// cap: onboarding.clinic-onboarding-3step
// story-origin: TBD
"use client";
/**
 * SlotTrackerSticky — horizontal slot pills showing confirmed/pending wizard slots.
 *
 * Visual reference: wizard-brand-studio.html (mockup v1 Batch 7)
 * Layout: px-4 py-3, border-b, bg surface-alt
 * Pills: confirmed = green bg + green text ("✓ Nombre")
 *         pending  = cyan bg + cyan text ("○ 1er tratamiento")
 *
 * Per mockup:
 *   - confirmed: vt-bg-success-subtle vt-text-success
 *   - pending:   vt-bg-cian-subtle vt-text-cian
 *   - optional:  vt-bg-muted vt-text-muted
 *
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 */

import { cn } from "@/lib/cn";
import { WIZARD_COPY } from "../config/copy";
import type { WizardSlot } from "../types/wizard-onboarding.types";

export interface SlotTrackerStickyProps {
  /** All wizard slots (confirmed + pending) */
  slots: WizardSlot[];
  /** Additional CSS classes */
  className?: string;
}

function SlotPill({ slot }: { slot: WizardSlot }) {
  const isConfirmed = slot.status === "confirmed";
  const isPending = slot.status === "pending";
  const isOptional = slot.status === "optional";

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full px-3 py-1 text-xs font-medium whitespace-nowrap transition-colors duration-200",
        isConfirmed && "bg-green-100 text-green-700",
        isPending && "bg-cyan-50 text-cyan-600",
        isOptional && "bg-gray-100 text-gray-500",
      )}
      role="status"
      aria-label={`${slot.label}: ${
        isConfirmed
          ? WIZARD_COPY.slotTracker.statusConfirmed
          : isPending
            ? WIZARD_COPY.slotTracker.statusPending
            : WIZARD_COPY.slotTracker.statusOptional
      }`}
    >
      <span aria-hidden="true">
        {isConfirmed
          ? WIZARD_COPY.slotTracker.confirmedPrefix
          : WIZARD_COPY.slotTracker.pendingPrefix}
      </span>
      <span>{slot.label}</span>
    </span>
  );
}

SlotPill.displayName = "SlotPill";

/**
 * Sticky slot tracker — shows slot pills across the top of the chat panel.
 */
export function SlotTrackerSticky({
  slots,
  className,
}: SlotTrackerStickyProps) {
  const visibleSlots = slots.filter((s) => s.status !== "rejected");

  return (
    <div
      className={cn(
        "flex items-center gap-2 overflow-x-auto px-4 py-3 border-b",
        "bg-gray-50 scrollbar-none",
        className,
      )}
      role="region"
      aria-label={WIZARD_COPY.a11y.slotTrackerLabel}
    >
      {visibleSlots.length === 0 ? (
        <p className="text-xs text-gray-400 italic">
          {WIZARD_COPY.slotTracker.emptyState}
        </p>
      ) : (
        <div className="flex items-center gap-1.5 flex-nowrap min-w-0">
          {visibleSlots.map((slot) => (
            <SlotPill key={slot.slotId} slot={slot} />
          ))}
        </div>
      )}
    </div>
  );
}

SlotTrackerSticky.displayName = "SlotTrackerSticky";
