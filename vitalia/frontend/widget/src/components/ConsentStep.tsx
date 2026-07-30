/**
 * ConsentStep — consent signature step in the booking widget.
 *
 * Reuses ConsentSignatureModal pattern from T-fe-3 but adapted for the standalone
 * iframe widget (no Next.js imports, no Clerk). Per 03-arch-fe.md § 9 + spec § 5.4.
 *
 * Accessibility: focus trap inside iframe (per D11 + spec § 10).
 * Spanish neutro LatAm: all user-facing strings from microcopy constants.
 */

import { useState, useRef, useCallback } from "react";
import { cn } from "../lib/cn";

// Widget-local microcopy (no @/features/vitalia/config import — standalone bundle)
const COPY = {
  title: "Consentimiento informado",
  scrollInstruction: "Lee y desplaza hasta el final para continuar",
  accept: "Acepto los términos del consentimiento",
  signaturePrompt: "Firma con tu nombre completo",
  signaturePlaceholder: "Tu nombre completo",
  back: "Atrás",
  confirm: "Firmar y aceptar",
  signing: "Firmando...",
} as const;

export interface ConsentStepProps {
  consentMarkdown: string;
  onSign: (signedName: string) => void;
  onBack: () => void;
  isLoading: boolean;
  /** Optional title override */
  title?: string;
}

export function ConsentStep({
  consentMarkdown,
  onSign,
  onBack,
  isLoading,
  title = COPY.title,
}: ConsentStepProps) {
  const [hasScrolledToEnd, setHasScrolledToEnd] = useState(false);
  const [accepted, setAccepted] = useState(false);
  const [signedName, setSignedName] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);

  const canSign = hasScrolledToEnd && accepted && signedName.trim().length >= 2 && !isLoading;

  const handleScroll = useCallback(() => {
    const el = scrollRef.current;
    if (!el) return;
    const isAtEnd = el.scrollTop + el.clientHeight >= el.scrollHeight - 8;
    if (isAtEnd) setHasScrolledToEnd(true);
  }, []);

  function handleSign() {
    if (!canSign) return;
    onSign(signedName.trim());
  }

  return (
    <div className="flex flex-col h-full" role="region" aria-label="Paso de consentimiento">
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-100">
        <h2 className="text-base font-semibold text-gray-900">{title}</h2>
      </div>

      {/* Scroll instruction */}
      {!hasScrolledToEnd && (
        <div
          className="px-4 py-2 text-xs text-blue-600 bg-blue-50 border-b border-blue-100"
          role="note"
          aria-live="polite"
        >
          {COPY.scrollInstruction}
        </div>
      )}

      {/* Scrollable terms */}
      <div
        ref={scrollRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto px-4 py-3 min-h-0"
        aria-label="Términos de consentimiento"
        tabIndex={0}
        style={{ maxHeight: "240px" }}
      >
        <div className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">
          {consentMarkdown}
        </div>
      </div>

      {/* Acceptance section */}
      <div className="border-t border-gray-100 px-4 py-4 space-y-4">
        {/* Accept checkbox */}
        <label
          className={cn(
            "flex items-start gap-3 cursor-pointer",
            !hasScrolledToEnd && "opacity-40 pointer-events-none"
          )}
        >
          <input
            type="checkbox"
            checked={accepted}
            onChange={(e) => setAccepted(e.target.checked)}
            disabled={!hasScrolledToEnd}
            className="mt-0.5 h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            aria-checked={accepted}
            aria-label={COPY.accept}
          />
          <span className="text-sm text-gray-700 select-none">{COPY.accept}</span>
        </label>

        {/* Signature input */}
        <div>
          <label
            htmlFor="widget-consent-signature"
            className={cn(
              "block text-sm font-medium text-gray-700 mb-1",
              !accepted && "opacity-40"
            )}
          >
            {COPY.signaturePrompt}
          </label>
          <input
            id="widget-consent-signature"
            type="text"
            value={signedName}
            onChange={(e) => setSignedName(e.target.value)}
            disabled={!accepted}
            placeholder={COPY.signaturePlaceholder}
            aria-label={COPY.signaturePrompt}
            aria-required="true"
            aria-invalid={accepted && signedName.trim().length < 2}
            className={cn(
              "w-full rounded-lg border px-3 py-2 text-sm",
              "focus:outline-none focus:ring-2 focus:ring-blue-500",
              "disabled:opacity-40 disabled:cursor-not-allowed",
              accepted ? "border-gray-300 bg-white" : "border-gray-200 bg-gray-50"
            )}
          />
        </div>

        {/* Actions */}
        <div className="flex gap-3">
          <button
            type="button"
            onClick={onBack}
            className={cn(
              "flex-1 px-4 py-2 text-sm font-medium text-gray-700",
              "border border-gray-300 rounded-lg",
              "hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-400"
            )}
          >
            {COPY.back}
          </button>
          <button
            type="button"
            onClick={handleSign}
            disabled={!canSign}
            aria-disabled={!canSign}
            aria-busy={isLoading}
            className={cn(
              "flex-1 px-4 py-2 text-sm font-medium rounded-lg transition-colors",
              "focus:outline-none focus:ring-2 focus:ring-blue-500",
              canSign
                ? "bg-blue-600 hover:bg-blue-700 text-white"
                : "bg-gray-100 text-gray-400 cursor-not-allowed"
            )}
          >
            {isLoading ? COPY.signing : COPY.confirm}
          </button>
        </div>
      </div>
    </div>
  );
}
