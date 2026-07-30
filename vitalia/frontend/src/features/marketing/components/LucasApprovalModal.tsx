// cap: public_landing.public-clinic-landing
// story-origin: TBD
/**
 * LucasApprovalModal — confirmation dialog before approving a Lucas recommendation
 * Warning: reversible (5-min undo window). Idempotency-Key per mutation call.
 * SC-MK-01: approve → receipt + undo chip countdown
 * SC-MK-04: recepcion role disabled + tooltip
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 */
"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { cn } from "@/lib/cn";
import { MARKETING_COPY } from "../copy";
import { useApproveRecommendation } from "../api/use-approve-recommendation";
import { useMarketingStore } from "../store/marketing-store";
import type { LucasRecommendation } from "../types/lucas-recommendation";

export type LucasApprovalModalProps = {
  rec: LucasRecommendation;
  onClose: () => void;
  /** RBAC role — recepcion cannot approve */
  userRole?: string;
};

export function LucasApprovalModal({
  rec,
  onClose,
  userRole,
}: LucasApprovalModalProps) {
  const dialogRef = useRef<HTMLDivElement>(null);
  const [phase, setPhase] = useState<"confirm" | "approved">("confirm");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const approve = useApproveRecommendation();
  const setPendingUndoTimer = useMarketingStore((s) => s.setPendingUndoTimer);

  const isRecepcion = userRole === "recepcion";
  const canApprove = !isRecepcion;

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

  const handleApprove = async () => {
    if (!canApprove) return;
    setErrorMsg(null);
    try {
      const result = await approve.mutateAsync({ recId: rec.id });
      // Store undo timer from BE undoUntil
      if (result.undoUntil) {
        const expiryMs = new Date(result.undoUntil).getTime();
        setPendingUndoTimer(rec.id, expiryMs);
      }
      setPhase("approved");
      // Auto-close after 3s
      setTimeout(() => onClose(), 3000);
    } catch {
      setErrorMsg("No se pudo aprobar la recomendación. Intenta de nuevo.");
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
        aria-labelledby="approval-modal-title"
        tabIndex={-1}
        className="fixed inset-0 z-50 flex items-center justify-center p-4"
        onKeyDown={handleKeyDown}
      >
        <div className="vt-bg-surface rounded-xl shadow-2xl w-full max-w-md border vt-border">
          {phase === "confirm" ? (
            <>
              {/* Confirm phase */}
              <div className="p-6">
                <div className="flex items-center gap-3 mb-4">
                  <div className="flex-shrink-0 w-10 h-10 rounded-full vt-bg-tab-active flex items-center justify-center">
                    <span className="text-sm font-bold vt-text-cian-bold">
                      LU
                    </span>
                  </div>
                  <h2
                    id="approval-modal-title"
                    className="text-lg font-semibold vt-text-azul-marino-bold"
                  >
                    {MARKETING_COPY.recommendations.approvalConfirmTitle}
                  </h2>
                </div>

                <p className="text-sm text-gray-600 leading-relaxed mb-2">
                  {MARKETING_COPY.recommendations.approvalConfirmDescription}
                </p>

                <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 mb-4">
                  <p className="text-xs text-amber-700 font-medium">
                    Esta acción es reversible durante 5 minutos después de
                    aprobar.
                  </p>
                </div>

                <div className="rounded-lg bg-gray-50 border vt-border p-3 mb-4">
                  <p className="text-xs text-gray-500 font-medium mb-1">
                    Recomendación
                  </p>
                  <p className="text-sm font-semibold vt-text-azul-marino-bold">
                    {rec.title}
                  </p>
                </div>

                {errorMsg && (
                  <div className="rounded-lg bg-red-50 border border-red-200 p-3 mb-4">
                    <p className="text-sm text-red-600">{errorMsg}</p>
                  </div>
                )}

                {isRecepcion && (
                  <p
                    className="text-sm text-red-600 mb-4 font-medium"
                    aria-live="polite"
                  >
                    No tienes permiso para aprobar recomendaciones
                  </p>
                )}
              </div>

              <div className="flex items-center justify-end gap-3 px-6 py-4 border-t vt-border bg-gray-50/50 rounded-b-xl">
                <button
                  type="button"
                  onClick={onClose}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border vt-border rounded-lg hover:bg-gray-50 transition-colors"
                >
                  {MARKETING_COPY.recommendations.approvalCancelButton}
                </button>
                <button
                  type="button"
                  onClick={() => void handleApprove()}
                  disabled={!canApprove || approve.isPending}
                  aria-disabled={!canApprove || approve.isPending}
                  className={cn(
                    "px-4 py-2 text-sm font-semibold rounded-lg transition-colors",
                    canApprove && !approve.isPending
                      ? "vt-bg-tab-active vt-text-cian-bold hover:opacity-90"
                      : "bg-gray-200 text-gray-400 cursor-not-allowed",
                  )}
                >
                  {approve.isPending
                    ? "Aprobando..."
                    : MARKETING_COPY.recommendations.approvalConfirmButton}
                </button>
              </div>
            </>
          ) : (
            <>
              {/* Approved receipt phase */}
              <div className="p-6 text-center">
                <div className="w-12 h-12 rounded-full vt-bg-tab-active flex items-center justify-center mx-auto mb-4">
                  <svg
                    width="24"
                    height="24"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2.5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    className="vt-text-cian-bold"
                    aria-hidden="true"
                  >
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                </div>
                <h2
                  id="approval-modal-title"
                  className="text-lg font-semibold vt-text-azul-marino-bold mb-2"
                >
                  {MARKETING_COPY.recommendations.approvedBadge}
                </h2>
                <p className="text-sm text-gray-600">
                  Lucas ejecutará esta acción en breve.
                </p>
                <p className="text-xs text-gray-400 mt-2">
                  {MARKETING_COPY.recommendations.undoTimerLabel} 5 minutos
                </p>
                <p className="text-xs text-gray-400 mt-4">
                  Cerrando automáticamente...
                </p>
              </div>
            </>
          )}
        </div>
      </div>
    </>
  );
}
