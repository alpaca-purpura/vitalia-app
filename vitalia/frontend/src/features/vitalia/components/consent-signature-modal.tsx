// cap: shell-organism.shell-vitalia
// story-origin: TBD
/**
 * ConsentSignatureModal — HIPAA-lite consent capture modal.
 *
 * Vitalia-specific: signature audit trail + scroll-to-end validation + dual input mode.
 * Security-critical, vertical-specific. Justification: spec § 6.3.4 anti-duplication.
 *
 * @architecture-group vitalia-ui-strings
 */
"use client";

import { useState, useRef, useCallback } from "react";
import { cn } from "@/lib/cn";
import { MICROCOPY_BOOKING } from "@/features/vitalia/config/microcopy";

export interface ConsentSignatureModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSign: (signedName: string) => void;
  consentMarkdown: string;
  isLoading?: boolean;
  title?: string;
}

export function ConsentSignatureModal({
  isOpen,
  onClose,
  onSign,
  consentMarkdown,
  isLoading = false,
  title = MICROCOPY_BOOKING.consent.title,
}: ConsentSignatureModalProps) {
  const [hasScrolledToEnd, setHasScrolledToEnd] = useState(false);
  const [accepted, setAccepted] = useState(false);
  const [signedName, setSignedName] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);

  const handleScroll = useCallback(() => {
    const el = scrollRef.current;
    if (!el) return;
    const isAtEnd = el.scrollTop + el.clientHeight >= el.scrollHeight - 8;
    if (isAtEnd) setHasScrolledToEnd(true);
  }, []);

  const canSign = hasScrolledToEnd && accepted && signedName.trim().length >= 2;

  function handleSign() {
    if (!canSign || isLoading) return;
    onSign(signedName.trim());
  }

  function handleClose() {
    setHasScrolledToEnd(false);
    setAccepted(false);
    setSignedName("");
    onClose();
  }

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      role="dialog"
      aria-modal="true"
      aria-labelledby="consent-modal-title"
    >
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50"
        onClick={handleClose}
        aria-hidden="true"
      />

      {/* Modal panel */}
      <div className="relative bg-white rounded-xl shadow-2xl w-full max-w-lg mx-4 flex flex-col max-h-screen">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <h2
            id="consent-modal-title"
            className="text-base font-semibold text-gray-900"
          >
            {title}
          </h2>
          <button
            type="button"
            onClick={handleClose}
            aria-label="Cerrar"
            className="text-gray-400 hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500 rounded"
          >
            ✕
          </button>
        </div>

        {/* Scroll instruction */}
        {!hasScrolledToEnd && (
          <p className="px-6 py-2 text-xs text-blue-600 bg-blue-50 border-b border-blue-100">
            {MICROCOPY_BOOKING.consent.scrollInstruction}
          </p>
        )}

        {/* Scrollable terms */}
        <div
          ref={scrollRef}
          onScroll={handleScroll}
          className="flex-1 overflow-y-auto px-6 py-4 min-h-0 max-h-72"
          aria-label="Términos de consentimiento"
          tabIndex={0}
        >
          <div className="prose prose-sm max-w-none text-gray-700 text-sm leading-relaxed whitespace-pre-wrap">
            {consentMarkdown}
          </div>
        </div>

        {/* Acceptance section */}
        <div className="px-6 py-4 border-t border-gray-200 space-y-4">
          {/* Accept checkbox */}
          <label
            className={cn(
              "flex items-start gap-3 cursor-pointer",
              !hasScrolledToEnd && "opacity-50 pointer-events-none",
            )}
          >
            <input
              type="checkbox"
              checked={accepted}
              onChange={(e) => setAccepted(e.target.checked)}
              disabled={!hasScrolledToEnd}
              className="mt-0.5 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              aria-label={MICROCOPY_BOOKING.consent.accept}
            />
            <span className="text-sm text-gray-700">
              {MICROCOPY_BOOKING.consent.accept}
            </span>
          </label>

          {/* Signature input */}
          <div>
            <label
              htmlFor="consent-signature"
              className={cn(
                "block text-sm font-medium text-gray-700 mb-1",
                !accepted && "opacity-50",
              )}
            >
              {MICROCOPY_BOOKING.consent.signaturePrompt}
            </label>
            <input
              id="consent-signature"
              type="text"
              value={signedName}
              onChange={(e) => setSignedName(e.target.value)}
              disabled={!accepted}
              placeholder="Tu nombre completo"
              aria-label={MICROCOPY_BOOKING.consent.signaturePrompt}
              className={cn(
                "w-full rounded-md border px-3 py-2 text-sm",
                "focus:outline-none focus:ring-2 focus:ring-blue-500",
                "disabled:opacity-50 disabled:cursor-not-allowed",
                accepted ? "border-gray-300" : "border-gray-200 bg-gray-50",
              )}
            />
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={handleClose}
              className="px-4 py-2 text-sm font-medium text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              Cancelar
            </button>
            <button
              type="button"
              onClick={handleSign}
              disabled={!canSign || isLoading}
              aria-disabled={!canSign || isLoading}
              aria-busy={isLoading}
              className={cn(
                "px-4 py-2 text-sm font-medium rounded-md transition-colors",
                "focus:outline-none focus:ring-2 focus:ring-blue-500",
                canSign && !isLoading
                  ? "bg-blue-600 hover:bg-blue-700 text-white"
                  : "bg-gray-200 text-gray-400 cursor-not-allowed",
              )}
            >
              {isLoading ? "Firmando..." : "Firmar y aceptar"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
