// cap: public_landing.public-clinic-landing
// story-origin: TBD
/**
 * LucasStageRecommendationsCard — top 3 priority recommendations inline, "Ver todas" expand
 * Click card → LucasRecommendationDetailModal (which hosts Aprobar / Rechazar)
 * SC-MK-01: recommendations panel
 * HIPAA-lite: dual filter tenant+clinic via useLucasRecommendations (clinicId falsy → disabled)
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 */
"use client";

import { useState } from "react";
import { cn } from "@/lib/cn";
import { MARKETING_COPY } from "../copy";
import { useLucasRecommendations } from "../api/use-lucas-recommendations";
import { LucasRecommendationDetailModal } from "./LucasRecommendationDetailModal";
import { LucasApprovalModal } from "./LucasApprovalModal";
import { LucasRejectModal } from "./LucasRejectModal";
import { LucasUndoChip } from "./LucasUndoChip";
import type {
  LucasRecommendation,
  RecommendationStage,
} from "../types/lucas-recommendation";

export type LucasStageRecommendationsCardProps = {
  /** Filter by stage. If omitted, shows all stages (cross-stage view). */
  stage?: RecommendationStage;
  /** RBAC role passed down from page/layout */
  userRole?: string;
  className?: string;
};

const VISIBLE_COUNT = 3;

type ModalState =
  | { kind: "none" }
  | { kind: "detail"; rec: LucasRecommendation }
  | { kind: "approve"; rec: LucasRecommendation }
  | { kind: "reject"; recId: string };

export function LucasStageRecommendationsCard({
  stage,
  userRole,
  className,
}: LucasStageRecommendationsCardProps) {
  const { data, isLoading, isError, refetch } = useLucasRecommendations();
  const [expanded, setExpanded] = useState(false);
  const [modal, setModal] = useState<ModalState>({ kind: "none" });

  // Filter open recommendations by stage (if provided), sorted by priority asc
  const allRecs = (data?.items ?? [])
    .filter((r) => r.status === "open")
    .filter((r) => (stage ? r.stage === stage : true))
    .sort((a, b) => a.priority - b.priority);

  const visibleRecs = expanded ? allRecs : allRecs.slice(0, VISIBLE_COUNT);
  const hasMore = allRecs.length > VISIBLE_COUNT;

  const closeModal = () => setModal({ kind: "none" });

  const handleCardClick = (rec: LucasRecommendation) => {
    setModal({ kind: "detail", rec });
  };

  const handleApproveFromDetail = (rec: LucasRecommendation) => {
    setModal({ kind: "approve", rec });
  };

  const handleRejectFromDetail = (rec: LucasRecommendation) => {
    setModal({ kind: "reject", recId: rec.id });
  };

  if (isLoading) {
    return (
      <div
        className={cn("rounded-xl border vt-border p-6", className)}
        aria-busy="true"
        aria-label={MARKETING_COPY.recommendations.loadingMessage}
      >
        <div className="flex items-center gap-3 mb-4">
          <div className="w-8 h-8 rounded-full vt-bg-tab-active flex items-center justify-center">
            <span className="text-xs font-bold vt-text-cian-bold">LU</span>
          </div>
          <div className="h-5 w-40 bg-gray-200 rounded animate-pulse" />
        </div>
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="h-16 bg-gray-100 rounded-lg animate-pulse"
            />
          ))}
        </div>
        {/* Accessible status indicator */}
        <span role="status" className="sr-only">
          {MARKETING_COPY.recommendations.loadingMessage}
        </span>
      </div>
    );
  }

  if (isError) {
    return (
      <div className={cn("rounded-xl border vt-border p-6", className)}>
        <div className="flex items-center gap-3 mb-3">
          <div className="w-8 h-8 rounded-full vt-bg-tab-active flex items-center justify-center">
            <span className="text-xs font-bold vt-text-cian-bold">LU</span>
          </div>
          <h3 className="text-base font-semibold vt-text-azul-marino-bold">
            {MARKETING_COPY.recommendations.title}
          </h3>
        </div>
        <p className="text-sm text-red-600 mb-3">
          {MARKETING_COPY.recommendations.errorMessage}
        </p>
        <button
          type="button"
          onClick={() => void refetch()}
          className="text-sm font-medium vt-text-cian-bold hover:underline"
        >
          {MARKETING_COPY.ui.retry}
        </button>
      </div>
    );
  }

  if (allRecs.length === 0) {
    return (
      <div className={cn("rounded-xl border vt-border p-6", className)}>
        <div className="flex items-center gap-3 mb-3">
          <div className="w-8 h-8 rounded-full vt-bg-tab-active flex items-center justify-center">
            <span className="text-xs font-bold vt-text-cian-bold">LU</span>
          </div>
          <h3 className="text-base font-semibold vt-text-azul-marino-bold">
            {MARKETING_COPY.recommendations.title}
          </h3>
        </div>
        <p className="text-sm text-gray-500 italic">
          {MARKETING_COPY.recommendations.emptyMessage}
        </p>
      </div>
    );
  }

  return (
    <>
      <div
        className={cn(
          "rounded-xl border vt-border p-6 vt-bg-surface",
          className,
        )}
      >
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full vt-bg-tab-active flex items-center justify-center flex-shrink-0">
              <span className="text-xs font-bold vt-text-cian-bold">LU</span>
            </div>
            <div>
              <h3 className="text-base font-semibold vt-text-azul-marino-bold leading-tight">
                {MARKETING_COPY.recommendations.title}
              </h3>
              <p className="text-xs text-gray-500">
                {MARKETING_COPY.recommendations.subtitle}
              </p>
            </div>
          </div>
          <span className="text-xs text-gray-400 font-medium">
            {allRecs.length} activas
          </span>
        </div>

        {/* Recommendation cards */}
        <div className="space-y-3">
          {visibleRecs.map((rec) => (
            <RecommendationItem
              key={rec.id}
              rec={rec}
              onClick={handleCardClick}
            />
          ))}
        </div>

        {/* Expand / collapse */}
        {hasMore && (
          <div className="mt-4 pt-3 border-t vt-border">
            <button
              type="button"
              onClick={() => setExpanded((v) => !v)}
              className="text-sm font-medium vt-text-cian-bold hover:underline"
              aria-expanded={expanded}
            >
              {expanded ? "Ver menos" : `Ver todas (${allRecs.length})`}
            </button>
          </div>
        )}
      </div>

      {/* Modals */}
      {modal.kind === "detail" && (
        <LucasRecommendationDetailModal
          rec={modal.rec}
          onClose={closeModal}
          onApprove={handleApproveFromDetail}
          onReject={handleRejectFromDetail}
          userRole={userRole}
        />
      )}
      {modal.kind === "approve" && (
        <LucasApprovalModal
          rec={modal.rec}
          onClose={closeModal}
          userRole={userRole}
        />
      )}
      {modal.kind === "reject" && (
        <LucasRejectModal recId={modal.recId} onClose={closeModal} />
      )}
    </>
  );
}

// --- Private sub-component: single recommendation card ---

type RecommendationItemProps = {
  rec: LucasRecommendation;
  onClick: (rec: LucasRecommendation) => void;
};

function RecommendationItem({ rec, onClick }: RecommendationItemProps) {
  return (
    <div>
      <button
        type="button"
        onClick={() => onClick(rec)}
        className="w-full text-left rounded-lg border vt-border p-4 hover:shadow-sm hover:vt-border-b-cian transition-all group cursor-pointer"
        aria-label={`Ver detalle: ${rec.title}`}
      >
        <div className="flex items-start gap-3">
          {/* Priority badge */}
          <div className="flex-shrink-0 w-6 h-6 rounded-full vt-bg-tab-active flex items-center justify-center mt-0.5">
            <span className="text-xs font-bold vt-text-cian-bold">
              {rec.priority}
            </span>
          </div>

          <div className="flex-1 min-w-0">
            <p className="text-sm font-semibold vt-text-azul-marino-bold leading-snug group-hover:underline">
              {rec.title}
            </p>
            <p className="text-xs text-gray-500 mt-0.5 line-clamp-2 leading-relaxed">
              {rec.body}
            </p>

            <div className="flex items-center gap-3 mt-2">
              {rec.confidencePct !== null && (
                <span className="text-xs text-gray-500">
                  {MARKETING_COPY.recommendations.confidenceLabel}:{" "}
                  <strong className="vt-text-cian-bold font-semibold">
                    {rec.confidencePct}%
                  </strong>
                </span>
              )}
              {rec.projectedImpactText && (
                <span className="text-xs text-gray-500 truncate">
                  {rec.projectedImpactText}
                </span>
              )}
            </div>
          </div>

          {/* Undo chip (if recently approved and within window) */}
          <LucasUndoChip recId={rec.id} />
        </div>
      </button>
    </div>
  );
}
