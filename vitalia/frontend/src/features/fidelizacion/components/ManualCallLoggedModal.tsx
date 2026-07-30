// cap: patients.nps-tracking
// story-origin: TBD
"use client";

/**
 * ManualCallLoggedModal — log a manual phone call to a patient.
 *
 * Form: notes (textarea) + outcome radio.
 *
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 */

import { useEffect, useRef, useState } from "react";
import { cn } from "@/lib/cn";
import { FIDELIZACION_COPY } from "../copy";
import { useLogManualCall } from "../api/use-log-manual-call";
import type { LogManualCallRequest } from "../types/re-engagement";

interface ManualCallLoggedModalProps {
  eventId: string;
  patientId: string;
  onClose: () => void;
}

type CallOutcome = LogManualCallRequest["outcome"];

const OUTCOME_OPTIONS: { value: CallOutcome; label: string }[] = [
  {
    value: "reached",
    label: FIDELIZACION_COPY.modals.manualCall.outcomeOptions.reached,
  },
  {
    value: "voicemail",
    label: FIDELIZACION_COPY.modals.manualCall.outcomeOptions.voicemail,
  },
  {
    value: "no_answer",
    label: FIDELIZACION_COPY.modals.manualCall.outcomeOptions.no_answer,
  },
];

export function ManualCallLoggedModal({
  patientId,
  onClose,
}: ManualCallLoggedModalProps) {
  const copy = FIDELIZACION_COPY.modals.manualCall;
  const mutation = useLogManualCall();
  const titleId = "manual-call-modal-title";
  const overlayRef = useRef<HTMLDivElement>(null);
  const firstFocusRef = useRef<HTMLButtonElement>(null);

  const [notes, setNotes] = useState("");
  const [outcome, setOutcome] = useState<CallOutcome>("reached");

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

  async function handleConfirm() {
    await mutation.mutateAsync({
      patientId,
      payload: {
        notes: notes.trim(),
        outcome,
        callDurationSeconds: null,
      },
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
          {/* Outcome radio */}
          <fieldset>
            <legend className="mb-2 text-sm font-medium text-[hsl(var(--vitalia-fg,220_25%_15%))]">
              {copy.outcomeLabel}
            </legend>
            <div className="space-y-2">
              {OUTCOME_OPTIONS.map((opt) => (
                <label
                  key={opt.value}
                  className="flex items-center gap-2 cursor-pointer text-sm"
                >
                  <input
                    type="radio"
                    name="call-outcome"
                    value={opt.value}
                    checked={outcome === opt.value}
                    onChange={() => setOutcome(opt.value)}
                    className="accent-[hsl(var(--vitalia-primary,210_90%_50%))]"
                  />
                  {opt.label}
                </label>
              ))}
            </div>
          </fieldset>

          {/* Notes */}
          <div>
            <label
              htmlFor="call-notes"
              className="mb-1 block text-sm font-medium text-[hsl(var(--vitalia-fg,220_25%_15%))]"
            >
              {copy.notesLabel}
            </label>
            <textarea
              id="call-notes"
              rows={3}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder={copy.notesPlaceholder}
              maxLength={500}
              className="w-full rounded border border-[hsl(var(--vitalia-border,220_13%_91%))] px-3 py-1.5 text-sm resize-none"
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
            disabled={mutation.isPending}
            aria-busy={mutation.isPending}
            className={cn(
              "rounded px-3 py-1.5 text-sm font-medium text-white",
              "bg-[hsl(var(--vitalia-primary,210_90%_50%))] hover:bg-[hsl(var(--vitalia-primary-hover,210_90%_45%))]",
              "disabled:opacity-60",
            )}
          >
            {mutation.isPending ? "Registrando..." : copy.confirm}
          </button>
        </footer>
      </div>
    </div>
  );
}
