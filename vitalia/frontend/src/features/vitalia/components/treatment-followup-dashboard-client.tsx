// cap: shell-organism.shell-vitalia
// story-origin: TBD
/**
 * TreatmentFollowupDashboardClient — main dashboard for treatment followup.
 *
 * Renders: treatment timeline + chat history + next action card + status
 * banners + manual handoff / send consent / view audit CTAs.
 *
 * Spec § 4.4 + § 5.5 + § 8.5.
 *
 * @architecture-group vitalia-ui-strings
 */
"use client";

import { useState, useCallback } from "react";
import { cn } from "@/lib/cn";
import { MICROCOPY_TREATMENT } from "@/features/vitalia/config/microcopy";
import { useTreatment } from "@/features/vitalia/api/use-treatment";
import { useTreatmentSnapshot } from "@/features/vitalia/api/use-treatment-snapshot";
import { TreatmentTimeline } from "@/features/vitalia/components/treatment-timeline";
import type { TreatmentMilestone } from "@/features/vitalia/components/treatment-timeline";

// ── Types ─────────────────────────────────────────────────────────────────────

export type TreatmentDashboardStatus =
  | "active"
  | "paused_safety_escalation"
  | "paused_awaiting_clinic"
  | "completed";

export interface TreatmentFollowupDashboardClientProps {
  treatmentId: string;
  className?: string;
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function deriveMilestones(currentStep: string): TreatmentMilestone[] {
  const order = ["d0", "d5", "d14", "d90"] as const;
  const stepIndex = order.indexOf(currentStep as (typeof order)[number]);
  return order.map((name, i) => ({
    name,
    status:
      i < stepIndex ? "completed" : i === stepIndex ? "current" : "pending",
  }));
}

function deriveDashboardStatus(
  paused_reason: string | null,
  current_step: string,
): TreatmentDashboardStatus {
  if (!paused_reason) {
    if (current_step === "completed") return "completed";
    return "active";
  }
  if (
    paused_reason.toLowerCase().includes("safety") ||
    paused_reason.toLowerCase().includes("symptom")
  ) {
    return "paused_safety_escalation";
  }
  return "paused_awaiting_clinic";
}

// ── Sub-components ────────────────────────────────────────────────────────────

function StatusBanner({ status }: { status: TreatmentDashboardStatus }) {
  if (status === "active") return null;

  if (status === "paused_safety_escalation") {
    return (
      <div
        className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 flex items-start gap-3"
        role="alert"
        aria-live="polite"
      >
        <span className="text-red-600 mt-0.5 text-lg" aria-hidden="true">
          ⚠
        </span>
        <p className="text-sm text-red-700">
          {MICROCOPY_TREATMENT.alerts.symptomsReported}
        </p>
      </div>
    );
  }

  if (status === "paused_awaiting_clinic") {
    return (
      <div
        className="rounded-lg border border-yellow-200 bg-yellow-50 px-4 py-3 flex items-start gap-3"
        role="status"
        aria-live="polite"
      >
        <span className="text-yellow-600 mt-0.5 text-lg" aria-hidden="true">
          ⏸
        </span>
        <p className="text-sm text-yellow-700">
          Tratamiento pausado. Esperando intervención de la clínica.
        </p>
      </div>
    );
  }

  if (status === "completed") {
    return (
      <div
        className="rounded-lg border border-green-200 bg-green-50 px-4 py-3 flex items-start gap-3"
        role="status"
      >
        <span className="text-green-600 mt-0.5 text-lg" aria-hidden="true">
          ✓
        </span>
        <p className="text-sm text-green-700">
          Tratamiento completado exitosamente.
        </p>
      </div>
    );
  }

  return null;
}

function NextActionCard({
  nextScheduledAt,
  adherenceScore,
}: {
  nextScheduledAt: string | null;
  adherenceScore: number | null;
}) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4 space-y-3">
      <h3 className="text-sm font-semibold text-gray-900">Próxima acción</h3>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">
            Próximo mensaje
          </p>
          <p className="text-sm text-gray-800">
            {nextScheduledAt
              ? new Date(nextScheduledAt).toLocaleDateString("es", {
                  day: "2-digit",
                  month: "short",
                  hour: "2-digit",
                  minute: "2-digit",
                })
              : "—"}
          </p>
        </div>
        <div>
          <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">
            {MICROCOPY_TREATMENT.adherence.label}
          </p>
          <p className="text-sm text-gray-800">
            {typeof adherenceScore === "number" ? `${adherenceScore}%` : "—"}
          </p>
        </div>
      </div>
    </div>
  );
}

// ── CTA bar ───────────────────────────────────────────────────────────────────

function CtaBar({
  treatmentId,
  status,
  onTakeConversation,
}: {
  treatmentId: string;
  status: TreatmentDashboardStatus;
  onTakeConversation: () => void;
}) {
  return (
    <div className="flex flex-wrap gap-3">
      <button
        type="button"
        onClick={onTakeConversation}
        disabled={status === "completed"}
        className={cn(
          "rounded-md px-4 py-2 text-sm font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500",
          status === "paused_safety_escalation"
            ? "bg-red-600 text-white hover:bg-red-700 disabled:opacity-50"
            : "bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed",
        )}
        aria-label={MICROCOPY_TREATMENT.actions.takeConversation}
      >
        {MICROCOPY_TREATMENT.actions.takeConversation}
      </button>

      <button
        type="button"
        disabled={status === "completed"}
        className="rounded-md border border-gray-200 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
        aria-label={MICROCOPY_TREATMENT.actions.sendConsent}
      >
        {MICROCOPY_TREATMENT.actions.sendConsent}
      </button>

      <a
        href={`/compliance?patient=${treatmentId}`}
        className="rounded-md border border-gray-200 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 inline-flex items-center"
        aria-label={MICROCOPY_TREATMENT.actions.viewAuditLog}
      >
        {MICROCOPY_TREATMENT.actions.viewAuditLog}
      </a>
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────────────────

export function TreatmentFollowupDashboardClient({
  treatmentId,
  className,
}: TreatmentFollowupDashboardClientProps) {
  const [isTakingConversation, setIsTakingConversation] = useState(false);

  const {
    data: treatment,
    isLoading: isTreatmentLoading,
    isError: isTreatmentError,
  } = useTreatment(treatmentId);

  const { data: snapshot, isLoading: isSnapshotLoading } =
    useTreatmentSnapshot(treatmentId);

  const isLoading = isTreatmentLoading || isSnapshotLoading;

  const handleTakeConversation = useCallback(() => {
    setIsTakingConversation(true);
    // TODO: open handoff modal / POST /api/v1/vitalia/treatments/{id}/manual-handoff
    // Wired in T-fe-6
  }, []);

  if (isLoading) {
    return (
      <div
        className={cn("flex flex-col gap-6", className)}
        role="status"
        aria-busy={true}
        aria-label="Cargando seguimiento de tratamiento"
      >
        {/* Skeleton timeline */}
        <div className="space-y-4">
          <div className="h-4 w-48 rounded bg-gray-200 animate-pulse" />
          <div className="flex items-center justify-between">
            {[0, 1, 2, 3].map((i) => (
              <div key={i} className="flex flex-col items-center gap-2">
                <div className="h-10 w-10 rounded-full bg-gray-200 animate-pulse" />
                <div className="h-3 w-10 rounded bg-gray-200 animate-pulse" />
              </div>
            ))}
          </div>
        </div>
        {/* Skeleton cards */}
        <div className="h-24 w-full rounded-lg bg-gray-100 animate-pulse" />
        <div className="flex gap-3">
          {[0, 1, 2].map((i) => (
            <div
              key={i}
              className="h-9 w-36 rounded-md bg-gray-200 animate-pulse"
            />
          ))}
        </div>
      </div>
    );
  }

  if (isTreatmentError || !treatment) {
    return (
      <div
        className={cn(
          "rounded-lg border border-red-200 bg-red-50 p-6 text-center",
          className,
        )}
        role="alert"
      >
        <p className="text-sm text-red-700">
          Error al cargar el tratamiento. Intenta recargar la página.
        </p>
      </div>
    );
  }

  const currentStep = snapshot?.current_step ?? treatment.current_step;
  const adherenceScore = snapshot?.adherence_score ?? treatment.adherence_score;
  const nextScheduledAt =
    snapshot?.next_scheduled_at ?? treatment.next_scheduled_at;
  const pausedReason = snapshot?.paused_reason ?? treatment.paused_reason;

  const milestones = deriveMilestones(currentStep);
  const dashboardStatus = deriveDashboardStatus(pausedReason, currentStep);

  return (
    <div className={cn("flex flex-col gap-6", className)}>
      {/* Page title */}
      <div>
        <h2 className="text-base font-semibold text-gray-900">
          {MICROCOPY_TREATMENT.title}
        </h2>
        <p className="text-sm text-gray-500">
          Plan:{" "}
          <span className="font-medium">{treatment.plan_template_slug}</span>
        </p>
      </div>

      {/* Status banner */}
      <StatusBanner status={dashboardStatus} />

      {/* Timeline */}
      <TreatmentTimeline
        milestones={milestones}
        adherenceScore={adherenceScore}
        currentStep={currentStep}
      />

      {/* Next action card */}
      <NextActionCard
        nextScheduledAt={nextScheduledAt}
        adherenceScore={adherenceScore}
      />

      {/* CTA bar */}
      <CtaBar
        treatmentId={treatmentId}
        status={dashboardStatus}
        onTakeConversation={handleTakeConversation}
      />

      {/* Taking conversation indicator */}
      {isTakingConversation && (
        <div
          className="rounded-lg border border-blue-200 bg-blue-50 px-4 py-3"
          role="status"
          aria-live="polite"
        >
          <p className="text-sm text-blue-700">
            Tomando control de la conversación...
          </p>
        </div>
      )}
    </div>
  );
}
