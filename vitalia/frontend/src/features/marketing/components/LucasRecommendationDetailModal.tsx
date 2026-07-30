// cap: public_landing.public-clinic-landing
// story-origin: TBD
/**
 * LucasRecommendationDetailModal — full-detail view of a Lucas recommendation
 * Shows: analysis (rationaleJson), projection, action_payload preview, Aprobar/Rechazar/Posponer 7d
 * SC-MK-01: click card → detail modal
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 */
"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { cn } from "@/lib/cn";
import { MARKETING_COPY } from "../copy";
import type { LucasRecommendation } from "../types/lucas-recommendation";

export type LucasRecommendationDetailModalProps = {
  rec: LucasRecommendation;
  onClose: () => void;
  onApprove?: (rec: LucasRecommendation) => void;
  onReject?: (rec: LucasRecommendation) => void;
  /** RBAC role — recepcion role cannot approve */
  userRole?: string;
};

export function LucasRecommendationDetailModal({
  rec,
  onClose,
  onApprove,
  onReject,
  userRole,
}: LucasRecommendationDetailModalProps) {
  const dialogRef = useRef<HTMLDivElement>(null);
  const [activeTab, setActiveTab] = useState<"analysis" | "payload">(
    "analysis",
  );

  const isRecepcion = userRole === "recepcion";
  const canApprove = !isRecepcion && rec.status === "open";

  // Close on ESC
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

  // Format ISO datetime for display
  const formatDate = (iso: string) => {
    return new Date(iso).toLocaleString("es-PE", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const statusBadge = () => {
    switch (rec.status) {
      case "approved":
        return (
          <span className="vt-text-cian-bold text-xs font-semibold px-2 py-0.5 rounded-full vt-bg-tab-active">
            {MARKETING_COPY.recommendations.approvedBadge}
          </span>
        );
      case "rejected":
        return (
          <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-red-100 text-red-700">
            {MARKETING_COPY.recommendations.rejectedBadge}
          </span>
        );
      case "expired":
        return (
          <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-gray-100 text-gray-600">
            {MARKETING_COPY.recommendations.expiredBadge}
          </span>
        );
      case "undone":
        return (
          <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-amber-100 text-amber-700">
            {MARKETING_COPY.recommendations.undoneBadge}
          </span>
        );
      default:
        return null;
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
        aria-labelledby="detail-modal-title"
        tabIndex={-1}
        className="fixed inset-0 z-50 flex items-center justify-center p-4"
        onKeyDown={handleKeyDown}
      >
        <div className="vt-bg-surface rounded-xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto border vt-border">
          {/* Header */}
          <div className="flex items-start justify-between p-6 border-b vt-border">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-xs font-bold vt-text-cian-bold uppercase tracking-widest">
                  LU
                </span>
                <span className="text-xs vt-text-azul-marino-bold opacity-60">
                  #{rec.priority}
                </span>
                {statusBadge()}
              </div>
              <h2
                id="detail-modal-title"
                className="text-lg font-semibold vt-text-azul-marino-bold leading-snug"
              >
                {rec.title}
              </h2>
              <p className="text-sm vt-text-azul-marino-bold opacity-70 mt-1 leading-relaxed">
                {rec.body}
              </p>
            </div>
            <button
              type="button"
              onClick={onClose}
              aria-label={MARKETING_COPY.ui.close}
              className="ml-4 p-2 rounded-lg hover:bg-gray-100 transition-colors flex-shrink-0"
            >
              <svg
                width="20"
                height="20"
                viewBox="0 0 20 20"
                fill="currentColor"
                aria-hidden="true"
              >
                <path
                  fillRule="evenodd"
                  d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                  clipRule="evenodd"
                />
              </svg>
            </button>
          </div>

          {/* Metrics row */}
          <div className="px-6 py-4 flex gap-6 border-b vt-border bg-gray-50/50">
            {rec.confidencePct !== null && (
              <div className="flex flex-col gap-0.5">
                <span className="text-xs text-gray-500 font-medium">
                  {MARKETING_COPY.recommendations.confidenceLabel}
                </span>
                <span className="text-base font-bold vt-text-cian-bold">
                  {rec.confidencePct}%
                </span>
              </div>
            )}
            {rec.projectedImpactText && (
              <div className="flex flex-col gap-0.5">
                <span className="text-xs text-gray-500 font-medium">
                  {MARKETING_COPY.recommendations.impactLabel}
                </span>
                <span className="text-base font-semibold vt-text-azul-marino-bold">
                  {rec.projectedImpactText}
                </span>
              </div>
            )}
            <div className="flex flex-col gap-0.5">
              <span className="text-xs text-gray-500 font-medium">
                {MARKETING_COPY.recommendations.priorityLabel}
              </span>
              <span className="text-base font-semibold vt-text-azul-marino-bold">
                {rec.priority}
              </span>
            </div>
          </div>

          {/* Tabs */}
          <div className="flex border-b vt-border px-6">
            <button
              type="button"
              onClick={() => setActiveTab("analysis")}
              className={cn(
                "py-3 px-4 text-sm font-medium border-b-2 transition-colors",
                activeTab === "analysis"
                  ? "vt-border-b-cian vt-text-cian-bold"
                  : "border-transparent text-gray-500 hover:text-gray-700",
              )}
            >
              Análisis
            </button>
            {rec.actionPayloadJson && (
              <button
                type="button"
                onClick={() => setActiveTab("payload")}
                className={cn(
                  "py-3 px-4 text-sm font-medium border-b-2 transition-colors",
                  activeTab === "payload"
                    ? "vt-border-b-cian vt-text-cian-bold"
                    : "border-transparent text-gray-500 hover:text-gray-700",
                )}
              >
                Acción a ejecutar
              </button>
            )}
          </div>

          {/* Tab content */}
          <div className="p-6">
            {activeTab === "analysis" && (
              <div className="space-y-3">
                {Object.entries(rec.rationaleJson).map(([key, value]) => (
                  <div
                    key={key}
                    className="flex justify-between items-center py-2 border-b vt-border last:border-0"
                  >
                    <span className="text-sm text-gray-600 font-medium capitalize">
                      {key.replace(/_/g, " ")}
                    </span>
                    <span className="text-sm font-semibold vt-text-azul-marino-bold">
                      {String(value)}
                    </span>
                  </div>
                ))}
                {Object.keys(rec.rationaleJson).length === 0 && (
                  <p className="text-sm text-gray-500 italic">
                    Sin datos de análisis disponibles.
                  </p>
                )}
              </div>
            )}
            {activeTab === "payload" && rec.actionPayloadJson && (
              <pre className="text-xs bg-gray-50 rounded-lg p-4 overflow-x-auto vt-border border font-mono">
                {JSON.stringify(rec.actionPayloadJson, null, 2)}
              </pre>
            )}
          </div>

          {/* Audit trail (approval info) */}
          {rec.approvedAt && (
            <div className="px-6 pb-4">
              <div className="text-xs text-gray-500 bg-gray-50 rounded-lg p-3 border vt-border">
                Aprobada el {formatDate(rec.approvedAt)}
                {rec.undoUntil && (
                  <span className="ml-2">
                    · Ventana de deshacer hasta {formatDate(rec.undoUntil)}
                  </span>
                )}
              </div>
            </div>
          )}

          {/* Actions */}
          {rec.status === "open" && (
            <div className="flex items-center justify-end gap-3 px-6 py-4 border-t vt-border bg-gray-50/50">
              {onReject && (
                <button
                  type="button"
                  onClick={() => onReject(rec)}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border vt-border rounded-lg hover:bg-gray-50 transition-colors"
                >
                  {MARKETING_COPY.recommendations.rejectButton}
                </button>
              )}
              <div className="relative group">
                {onApprove && (
                  <button
                    type="button"
                    onClick={() => canApprove && onApprove(rec)}
                    disabled={!canApprove}
                    className={cn(
                      "px-4 py-2 text-sm font-semibold rounded-lg transition-colors",
                      canApprove
                        ? "vt-bg-tab-active vt-text-cian-bold hover:opacity-90"
                        : "bg-gray-200 text-gray-400 cursor-not-allowed",
                    )}
                  >
                    {MARKETING_COPY.recommendations.approveButton}
                  </button>
                )}
                {isRecepcion && (
                  <span className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-1.5 text-xs text-white bg-gray-800 rounded-lg whitespace-nowrap pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity">
                    No tienes permiso para aprobar recomendaciones
                  </span>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
