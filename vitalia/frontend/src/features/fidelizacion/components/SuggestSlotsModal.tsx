// cap: patients.nps-tracking
// story-origin: TBD
"use client";

/**
 * SuggestSlotsModal — calendar mini with 3-5 available slots.
 *
 * Shows available appointment slots for suggest to patient.
 *
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 */

import { useEffect, useRef, useState } from "react";
import { cn } from "@/lib/cn";
import { FIDELIZACION_COPY } from "../copy";
import { useAvailabilitySlots } from "../api/use-availability-slots";
import { formatTenantDate } from "@/lib/format/formatTenantDate";
import { useTenantLocale } from "@/hooks/useTenantLocale";

interface SuggestSlotsModalProps {
  eventId: string;
  patientId: string;
  doctorId: string | null;
  onClose: () => void;
  onConfirm?: (slotIds: string[]) => void;
}

export function SuggestSlotsModal({
  doctorId,
  onClose,
  onConfirm,
}: SuggestSlotsModalProps) {
  const copy = FIDELIZACION_COPY.modals.suggestSlots;
  const titleId = "suggest-slots-modal-title";
  const overlayRef = useRef<HTMLDivElement>(null);
  const firstFocusRef = useRef<HTMLButtonElement>(null);
  const { timezone } = useTenantLocale();

  const { data, isPending } = useAvailabilitySlots({
    doctorId,
    daysAhead: 14,
    enabled: true,
  });

  const [selectedSlotIds, setSelectedSlotIds] = useState<string[]>([]);

  useEffect(() => {
    const prevFocus = document.activeElement as HTMLElement | null;
    firstFocusRef.current?.focus();

    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      prevFocus?.focus();
    };
  }, [onClose]);

  function toggleSlot(slotId: string) {
    setSelectedSlotIds((prev) =>
      prev.includes(slotId)
        ? prev.filter((id) => id !== slotId)
        : prev.length < 3
          ? [...prev, slotId]
          : prev,
    );
  }

  function handleConfirm() {
    onConfirm?.(selectedSlotIds);
    onClose();
  }

  const slots = data?.slots.slice(0, 5) ?? [];

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby={titleId}
      ref={overlayRef}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
      onClick={(e) => {
        if (e.target === overlayRef.current) onClose();
      }}
    >
      <div className="w-full max-w-sm rounded-xl bg-white shadow-xl">
        <header className="flex items-start justify-between border-b border-[hsl(var(--vitalia-border,220_13%_91%))] p-4">
          <h2
            id={titleId}
            className="text-base font-semibold text-[hsl(var(--vitalia-fg,220_25%_15%))]"
          >
            {copy.title}
          </h2>
          <button
            type="button"
            onClick={onClose}
            aria-label={FIDELIZACION_COPY.accessibility.closeModal}
            className="ml-2 rounded p-1 text-[hsl(var(--vitalia-muted,220_10%_55%))] hover:bg-[hsl(var(--vitalia-bg-soft,220_20%_96%))]"
          >
            ✕
          </button>
        </header>

        <div className="p-4 space-y-3">
          <p className="text-sm text-[hsl(var(--vitalia-muted,220_10%_55%))]">
            {copy.description}
          </p>

          {isPending ? (
            <div className="space-y-2">
              {Array.from({ length: 3 }).map((_, i) => (
                <div
                  key={i}
                  className="h-10 animate-pulse rounded bg-[hsl(var(--vitalia-bg-soft,220_20%_96%))]"
                />
              ))}
            </div>
          ) : slots.length === 0 ? (
            <p className="text-sm text-[hsl(var(--vitalia-muted,220_10%_55%))]">
              {copy.noSlots}
            </p>
          ) : (
            <ul className="space-y-2" aria-label="Turnos disponibles">
              {slots.map((slot) => {
                const isSelected = selectedSlotIds.includes(slot.id);
                return (
                  <li key={slot.id}>
                    <button
                      type="button"
                      aria-pressed={isSelected}
                      onClick={() => toggleSlot(slot.id)}
                      className={cn(
                        "w-full text-left rounded border px-3 py-2 text-sm transition-colors",
                        isSelected
                          ? "border-[hsl(var(--vitalia-primary,210_90%_50%))] bg-[hsl(var(--vitalia-primary-bg,210_100%_97%))] text-[hsl(var(--vitalia-primary,210_90%_50%))]"
                          : "border-[hsl(var(--vitalia-border,220_13%_91%))] hover:bg-[hsl(var(--vitalia-bg-soft,220_20%_96%))]",
                      )}
                    >
                      <span className="font-medium">{slot.doctorName}</span>
                      <span className="ml-2 text-[hsl(var(--vitalia-muted,220_10%_55%))]">
                        {formatTenantDate(slot.startsAt, timezone)} ·{" "}
                        {slot.specialtyLabel} · {slot.durationMinutes} min
                      </span>
                    </button>
                  </li>
                );
              })}
            </ul>
          )}
        </div>

        <footer className="flex justify-end gap-2 border-t border-[hsl(var(--vitalia-border,220_13%_91%))] p-4">
          <button
            ref={firstFocusRef}
            type="button"
            onClick={onClose}
            className="rounded px-3 py-1.5 text-sm font-medium text-[hsl(var(--vitalia-muted,220_10%_55%))] hover:bg-[hsl(var(--vitalia-bg-soft,220_20%_96%))]"
          >
            {copy.cancel}
          </button>
          <button
            type="button"
            onClick={handleConfirm}
            disabled={selectedSlotIds.length === 0}
            className="rounded px-3 py-1.5 text-sm font-medium text-white bg-[hsl(var(--vitalia-primary,210_90%_50%))] hover:bg-[hsl(var(--vitalia-primary-hover,210_90%_45%))] disabled:opacity-60"
          >
            {copy.confirm}
          </button>
        </footer>
      </div>
    </div>
  );
}
