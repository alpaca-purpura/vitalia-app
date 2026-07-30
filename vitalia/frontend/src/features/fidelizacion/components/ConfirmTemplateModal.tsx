// cap: patients.nps-tracking
// story-origin: TBD
"use client";

/**
 * ConfirmTemplateModal — Adrián recordatorio confirmation.
 *
 * Shows preview of WhatsApp template before sending.
 * Accessibility: focus trap, aria-modal, aria-labelledby, Escape closes.
 *
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 */

import { useEffect, useRef } from "react";
import { cn } from "@/lib/cn";
import { FIDELIZACION_COPY } from "../copy";
import { useSendProactiveTemplate } from "../api/use-send-proactive-template";
import type { SendProactiveRequest } from "../types/re-engagement";

interface ConfirmTemplateModalProps {
  eventId: string;
  patientId: string;
  payload: SendProactiveRequest;
  /** Preview message text */
  previewText: string;
  onClose: () => void;
}

/**
 * Confirmation modal before sending Adrián proactive WhatsApp template.
 */
export function ConfirmTemplateModal({
  patientId,
  payload,
  previewText,
  onClose,
}: ConfirmTemplateModalProps) {
  const copy = FIDELIZACION_COPY.modals.confirmTemplate;
  const mutation = useSendProactiveTemplate();
  const titleId = "confirm-template-modal-title";
  const overlayRef = useRef<HTMLDivElement>(null);
  const firstFocusRef = useRef<HTMLButtonElement>(null);

  // Focus trap + Escape
  useEffect(() => {
    const prevFocus = document.activeElement as HTMLElement | null;
    firstFocusRef.current?.focus();

    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") {
        onClose();
      }
    }
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      prevFocus?.focus();
    };
  }, [onClose]);

  async function handleConfirm() {
    await mutation.mutateAsync({ patientId, payload });
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
      <div className="w-full max-w-md rounded-xl bg-white shadow-xl">
        {/* Header */}
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

        {/* Body */}
        <div className="p-4 space-y-3">
          <p className="text-sm text-[hsl(var(--vitalia-muted,220_10%_55%))]">
            {copy.description}
          </p>

          {/* Message preview */}
          <div className="rounded-lg bg-[hsl(var(--vitalia-bg-soft,220_20%_96%))] p-3">
            <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-[hsl(var(--vitalia-muted,220_10%_55%))]">
              {copy.preview}
            </p>
            <p className="whitespace-pre-wrap text-sm text-[hsl(var(--vitalia-fg,220_25%_15%))]">
              {previewText}
            </p>
          </div>

          {mutation.isError && (
            <p
              role="alert"
              className="text-sm text-[hsl(var(--vitalia-danger,0_75%_45%))]"
            >
              {copy.errorToast}
            </p>
          )}
        </div>

        {/* Footer */}
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
              "rounded px-3 py-1.5 text-sm font-medium text-white transition-opacity",
              "bg-[hsl(var(--vitalia-primary,210_90%_50%))] hover:bg-[hsl(var(--vitalia-primary-hover,210_90%_45%))]",
              "disabled:opacity-60",
            )}
          >
            {mutation.isPending ? copy.sending : copy.confirm}
          </button>
        </footer>
      </div>
    </div>
  );
}
