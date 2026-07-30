// cap: patients.nps-tracking
// story-origin: TBD
"use client";

/**
 * PausePatientModal — pause follow-up for a patient.
 *
 * Form: duration (7 | 30 | custom days) + optional reason.
 * Uses native form state (RHF not installed — using React useState for minimal form).
 *
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 */

import { useEffect, useRef, useState } from "react";
import { cn } from "@/lib/cn";
import { FIDELIZACION_COPY } from "../copy";
import { usePausePatient } from "../api/use-pause-patient";

interface PausePatientModalProps {
  eventId: string;
  patientId: string;
  onClose: () => void;
}

const DURATION_OPTIONS = [
  {
    value: "7",
    label: FIDELIZACION_COPY.modals.pausePatient.durationOptions["7"],
  },
  {
    value: "30",
    label: FIDELIZACION_COPY.modals.pausePatient.durationOptions["30"],
  },
  {
    value: "custom",
    label: FIDELIZACION_COPY.modals.pausePatient.durationOptions.custom,
  },
] as const;

export function PausePatientModal({
  patientId,
  onClose,
}: PausePatientModalProps) {
  const copy = FIDELIZACION_COPY.modals.pausePatient;
  const mutation = usePausePatient();
  const titleId = "pause-patient-modal-title";
  const overlayRef = useRef<HTMLDivElement>(null);
  const firstFocusRef = useRef<HTMLButtonElement>(null);

  const [duration, setDuration] = useState<"7" | "30" | "custom">("7");
  const [customDays, setCustomDays] = useState("");
  const [reason, setReason] = useState("");

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

  const resolvedDays =
    duration === "custom" ? parseInt(customDays, 10) : parseInt(duration, 10);
  const isValid = !isNaN(resolvedDays) && resolvedDays > 0;

  async function handleConfirm() {
    if (!isValid) return;
    await mutation.mutateAsync({
      patientId,
      payload: { durationDays: resolvedDays, reason: reason.trim() || null },
    });
    onClose();
  }

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

        <div className="p-4 space-y-4">
          <p className="text-sm text-[hsl(var(--vitalia-muted,220_10%_55%))]">
            {copy.description}
          </p>

          {/* Duration selector */}
          <fieldset>
            <legend className="mb-2 text-sm font-medium text-[hsl(var(--vitalia-fg,220_25%_15%))]">
              {copy.durationLabel}
            </legend>
            <div className="flex gap-2 flex-wrap">
              {DURATION_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  type="button"
                  aria-pressed={duration === opt.value}
                  onClick={() => setDuration(opt.value)}
                  className={cn(
                    "rounded px-3 py-1.5 text-sm font-medium border transition-colors",
                    duration === opt.value
                      ? "border-[hsl(var(--vitalia-primary,210_90%_50%))] bg-[hsl(var(--vitalia-primary,210_90%_50%))] text-white"
                      : "border-[hsl(var(--vitalia-border,220_13%_91%))] text-[hsl(var(--vitalia-fg,220_25%_15%))] hover:bg-[hsl(var(--vitalia-bg-soft,220_20%_96%))]",
                  )}
                >
                  {opt.label}
                </button>
              ))}
            </div>
            {duration === "custom" && (
              <input
                type="number"
                min="1"
                max="365"
                value={customDays}
                onChange={(e) => setCustomDays(e.target.value)}
                placeholder="Días (ej.: 60)"
                className="mt-2 w-full rounded border border-[hsl(var(--vitalia-border,220_13%_91%))] px-3 py-1.5 text-sm"
                aria-label="Número de días personalizados"
              />
            )}
          </fieldset>

          {/* Reason (optional) */}
          <div>
            <label
              htmlFor="pause-reason"
              className="mb-1 block text-sm font-medium text-[hsl(var(--vitalia-fg,220_25%_15%))]"
            >
              {copy.reasonLabel}
            </label>
            <input
              id="pause-reason"
              type="text"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder={copy.reasonPlaceholder}
              maxLength={200}
              className="w-full rounded border border-[hsl(var(--vitalia-border,220_13%_91%))] px-3 py-1.5 text-sm"
            />
          </div>
        </div>

        <footer className="flex justify-end gap-2 border-t border-[hsl(var(--vitalia-border,220_13%_91%))] p-4">
          <button
            ref={firstFocusRef}
            type="button"
            onClick={onClose}
            disabled={mutation.isPending}
            className="rounded px-3 py-1.5 text-sm font-medium text-[hsl(var(--vitalia-muted,220_10%_55%))] hover:bg-[hsl(var(--vitalia-bg-soft,220_20%_96%))] disabled:opacity-50"
          >
            {copy.cancel}
          </button>
          <button
            type="button"
            onClick={() => void handleConfirm()}
            disabled={mutation.isPending || !isValid}
            aria-busy={mutation.isPending}
            className="rounded px-3 py-1.5 text-sm font-medium text-white bg-[hsl(var(--vitalia-primary,210_90%_50%))] hover:bg-[hsl(var(--vitalia-primary-hover,210_90%_45%))] disabled:opacity-60"
          >
            {mutation.isPending ? "Pausando..." : copy.confirm}
          </button>
        </footer>
      </div>
    </div>
  );
}
