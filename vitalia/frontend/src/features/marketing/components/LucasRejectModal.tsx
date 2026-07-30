// cap: public_landing.public-clinic-landing
// story-origin: TBD
/**
 * LucasRejectModal — reason-required form for rejecting a Lucas recommendation
 * Uses Zod for runtime validation, native React state (RHF not installed in this brand).
 * reason is required (enum); reasonOtherText only when reason === "other"
 * SC-MK-01: reject flow
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 */
"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { z } from "zod";
import { cn } from "@/lib/cn";
import { MARKETING_COPY } from "../copy";
import { useRejectRecommendation } from "../api/use-reject-recommendation";
import type { RejectReason } from "../types/lucas-recommendation";

const rejectSchema = z.object({
  reason: z.enum([
    "not_priority",
    "already_doing",
    "data_wrong",
    "too_risky",
    "other",
  ] as const),
  reasonOtherText: z.string().optional(),
});

export type LucasRejectModalProps = {
  recId: string;
  onClose: () => void;
};

const REJECT_REASONS: { value: RejectReason; label: string }[] = [
  { value: "not_priority", label: MARKETING_COPY.rejectReasons.not_priority },
  { value: "already_doing", label: MARKETING_COPY.rejectReasons.already_doing },
  { value: "data_wrong", label: MARKETING_COPY.rejectReasons.data_wrong },
  { value: "too_risky", label: MARKETING_COPY.rejectReasons.too_risky },
  { value: "other", label: MARKETING_COPY.rejectReasons.other },
];

export function LucasRejectModal({ recId, onClose }: LucasRejectModalProps) {
  const dialogRef = useRef<HTMLDivElement>(null);
  const reject = useRejectRecommendation();

  const [selectedReason, setSelectedReason] = useState<RejectReason | "">("");
  const [otherText, setOtherText] = useState("");
  const [validationError, setValidationError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // ESC key close
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
      }
    },
    [onClose],
  );

  // Focus trap on mount
  useEffect(() => {
    const el = dialogRef.current;
    if (el) {
      el.focus();
    }
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setValidationError(null);

    // Zod validation
    const result = rejectSchema.safeParse({
      reason: selectedReason || undefined,
      reasonOtherText: otherText || undefined,
    });

    if (!result.success) {
      const firstIssue = result.error.issues[0];
      setValidationError(
        firstIssue?.message ?? "Selecciona un motivo para rechazar",
      );
      return;
    }

    setIsSubmitting(true);
    try {
      await reject.mutateAsync({
        recId,
        reason: result.data.reason,
        reasonOtherText:
          result.data.reason === "other"
            ? result.data.reasonOtherText
            : undefined,
      });
      onClose();
    } catch {
      setValidationError("No se pudo rechazar. Intenta de nuevo.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <>
      {/* Overlay */}
      <div
        className="fixed inset-0 z-40 bg-black/50"
        aria-hidden="true"
        onClick={onClose}
      />

      {/* Dialog */}
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="reject-modal-title"
        tabIndex={-1}
        className="fixed inset-0 z-50 flex items-center justify-center p-4"
        onKeyDown={handleKeyDown}
      >
        <div className="vt-bg-surface rounded-xl shadow-2xl w-full max-w-md border vt-border">
          <div className="p-6">
            <h2
              id="reject-modal-title"
              className="text-lg font-semibold vt-text-azul-marino-bold mb-4"
            >
              ¿Por qué rechazas esta recomendación?
            </h2>

            <form onSubmit={(e) => void handleSubmit(e)} noValidate>
              <fieldset className="mb-4">
                <legend className="sr-only">Motivo de rechazo</legend>
                <div className="space-y-2" role="radiogroup">
                  {REJECT_REASONS.map(({ value, label }) => (
                    <label
                      key={value}
                      className={cn(
                        "flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-colors",
                        selectedReason === value
                          ? "vt-border-b-cian vt-bg-tab-active"
                          : "vt-border bg-white hover:bg-gray-50",
                      )}
                    >
                      <input
                        type="radio"
                        name="reason"
                        value={value}
                        aria-label={label}
                        checked={selectedReason === value}
                        onChange={() => setSelectedReason(value)}
                        className="accent-current vt-text-cian-bold"
                      />
                      <span className="text-sm font-medium vt-text-azul-marino-bold">
                        {label}
                      </span>
                    </label>
                  ))}
                </div>

                {validationError && (
                  <p className="mt-2 text-xs text-red-600" role="alert">
                    {validationError}
                  </p>
                )}
              </fieldset>

              {/* Optional other text */}
              {selectedReason === "other" && (
                <div className="mb-4">
                  <label
                    htmlFor="reason-other-text"
                    className="block text-sm font-medium vt-text-azul-marino-bold mb-1"
                  >
                    Especifica el motivo (opcional)
                  </label>
                  <textarea
                    id="reason-other-text"
                    value={otherText}
                    onChange={(e) => setOtherText(e.target.value)}
                    rows={3}
                    className="w-full rounded-lg border vt-border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-current vt-text-azul-marino-bold resize-none"
                    placeholder="Explica brevemente..."
                  />
                </div>
              )}

              <div className="flex items-center justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={onClose}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border vt-border rounded-lg hover:bg-gray-50 transition-colors"
                >
                  {MARKETING_COPY.ui.cancel}
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting || reject.isPending}
                  className={cn(
                    "px-4 py-2 text-sm font-semibold rounded-lg transition-colors",
                    isSubmitting || reject.isPending
                      ? "bg-gray-200 text-gray-400 cursor-not-allowed"
                      : "bg-red-600 text-white hover:bg-red-700",
                  )}
                >
                  {isSubmitting || reject.isPending
                    ? "Rechazando..."
                    : MARKETING_COPY.recommendations.rejectButton}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </>
  );
}
