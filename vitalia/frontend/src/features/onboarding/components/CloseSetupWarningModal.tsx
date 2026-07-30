// cap: onboarding.clinic-onboarding-3step
// story-origin: TBD
"use client";
/**
 * CloseSetupWarningModal — AlertDialog confirming wizard close with progress save note.
 *
 * Per spec: "¿Cerrar el asistente? Tus avances se guardan"
 * Uses native HTML dialog pattern (no Shadcn AlertDialog since components/ui/ is not populated).
 * Keyboard accessible: Escape closes, focus trap maintained.
 *
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 */

import { useEffect, useRef } from "react";
import { cn } from "@/lib/cn";
import { WIZARD_COPY } from "../config/copy";

export interface CloseSetupWarningModalProps {
  /** Whether the modal is open */
  isOpen: boolean;
  /** Called when user confirms close */
  onConfirmClose: () => void;
  /** Called when user cancels (stays in wizard) */
  onCancel: () => void;
}

/**
 * Warning modal confirming wizard exit with autosave reassurance.
 * Accessible: focus trap, Escape handler, aria-modal.
 */
export function CloseSetupWarningModal({
  isOpen,
  onConfirmClose,
  onCancel,
}: CloseSetupWarningModalProps) {
  const dialogRef = useRef<HTMLDivElement>(null);
  const cancelBtnRef = useRef<HTMLButtonElement>(null);
  const copy = WIZARD_COPY.closeModal;

  // Focus cancel button when dialog opens
  useEffect(() => {
    if (isOpen) {
      cancelBtnRef.current?.focus();
    }
  }, [isOpen]);

  // Escape key handler
  useEffect(() => {
    if (!isOpen) return;
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape") onCancel();
    };
    document.addEventListener("keydown", handleEscape);
    return () => document.removeEventListener("keydown", handleEscape);
  }, [isOpen, onCancel]);

  // Trap focus inside dialog
  useEffect(() => {
    if (!isOpen || !dialogRef.current) return;
    const focusable = dialogRef.current.querySelectorAll<HTMLElement>(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])',
    );
    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    const trap = (e: KeyboardEvent) => {
      if (e.key !== "Tab") return;
      if (e.shiftKey) {
        if (document.activeElement === first) {
          e.preventDefault();
          last?.focus();
        }
      } else {
        if (document.activeElement === last) {
          e.preventDefault();
          first?.focus();
        }
      }
    };
    document.addEventListener("keydown", trap);
    return () => document.removeEventListener("keydown", trap);
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-40 bg-black/40 backdrop-blur-sm transition-opacity duration-150"
        onClick={onCancel}
        aria-hidden="true"
      />

      {/* Dialog */}
      <div
        ref={dialogRef}
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="close-wizard-title"
        aria-describedby="close-wizard-desc"
        className={cn(
          "fixed inset-0 z-50 flex items-center justify-center p-4",
          "pointer-events-none",
        )}
      >
        <div
          className={cn(
            "w-full max-w-md rounded-2xl bg-white shadow-2xl p-6 space-y-4",
            "pointer-events-auto",
            "animate-in fade-in-0 zoom-in-95 duration-150",
          )}
        >
          {/* Icon */}
          <div className="flex items-center gap-3">
            <div
              className="w-10 h-10 rounded-full bg-amber-100 flex items-center justify-center flex-shrink-0"
              aria-hidden="true"
            >
              <svg
                width="20"
                height="20"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="text-amber-600"
                aria-hidden="true"
              >
                <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
                <line x1="12" y1="9" x2="12" y2="13" />
                <line x1="12" y1="17" x2="12.01" y2="17" />
              </svg>
            </div>
            <h2
              id="close-wizard-title"
              className="text-base font-semibold text-gray-900"
            >
              {copy.title}
            </h2>
          </div>

          <p
            id="close-wizard-desc"
            className="text-sm text-gray-600 leading-relaxed"
          >
            {copy.description}
          </p>

          {/* Actions */}
          <div className="flex gap-3 justify-end pt-2">
            <button
              ref={cancelBtnRef}
              type="button"
              onClick={onCancel}
              className={cn(
                "rounded-xl px-4 py-2 text-sm font-medium",
                "bg-blue-700 text-white",
                "hover:bg-blue-800 transition-colors duration-150",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-600",
              )}
            >
              {copy.cancelButton}
            </button>
            <button
              type="button"
              onClick={onConfirmClose}
              className={cn(
                "rounded-xl px-4 py-2 text-sm font-medium border border-gray-300",
                "text-gray-700 bg-white",
                "hover:bg-gray-50 transition-colors duration-150",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gray-400",
              )}
            >
              {copy.confirmButton}
            </button>
          </div>
        </div>
      </div>
    </>
  );
}

CloseSetupWarningModal.displayName = "CloseSetupWarningModal";
