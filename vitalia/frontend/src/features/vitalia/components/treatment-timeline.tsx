// cap: shell-organism.shell-vitalia
// story-origin: TBD
/**
 * TreatmentTimeline — visual horizontal timeline for D0/D5/D14/D90 milestones.
 *
 * Vitalia-specific: medical milestone names + adherence score overlay.
 * Generic timeline (e.g., @luana/shared/event-timeline) insufficient.
 * Justification: spec § 6.3.3 anti-duplication.
 *
 * @architecture-group vitalia-ui-strings
 */
"use client";

import { cn } from "@/lib/cn";
import { MICROCOPY_TREATMENT } from "@/features/vitalia/config/microcopy";

export type MilestoneName = "d0" | "d5" | "d14" | "d90";

export interface TreatmentMilestone {
  name: MilestoneName;
  status: "completed" | "current" | "pending";
  date?: string | null;
}

export interface TreatmentTimelineProps {
  milestones: TreatmentMilestone[];
  adherenceScore?: number | null;
  currentStep?: string;
  className?: string;
}

const MILESTONE_ORDER: MilestoneName[] = ["d0", "d5", "d14", "d90"];

function adherenceColor(score: number): string {
  if (score >= 80) return "text-green-700 bg-green-100";
  if (score >= 50) return "text-yellow-700 bg-yellow-100";
  return "text-red-700 bg-red-100";
}

function MilestoneNode({
  milestone,
  label,
}: {
  milestone: TreatmentMilestone;
  label: string;
}) {
  const isCompleted = milestone.status === "completed";
  const isCurrent = milestone.status === "current";
  const isPending = milestone.status === "pending";

  return (
    <div className="flex flex-col items-center gap-2">
      <span
        className={cn(
          "w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold border-2",
          isCompleted && "bg-green-600 border-green-600 text-white",
          isCurrent && "bg-white border-blue-600 text-blue-600",
          isPending && "bg-white border-gray-300 text-gray-400",
        )}
        role="img"
        aria-label={`${label}: ${isCompleted ? MICROCOPY_TREATMENT.adherence.done : isCurrent ? "En progreso" : MICROCOPY_TREATMENT.adherence.pending}`}
      >
        {isCompleted ? "✓" : isPending ? "○" : "●"}
      </span>
      <span
        className={cn(
          "text-xs font-medium text-center",
          isCompleted && "text-green-700",
          isCurrent && "text-blue-700",
          isPending && "text-gray-400",
        )}
      >
        {label}
      </span>
      {milestone.date && (
        <span className="text-xs text-gray-400 text-center">
          {milestone.date}
        </span>
      )}
    </div>
  );
}

export function TreatmentTimeline({
  milestones,
  adherenceScore,
  currentStep,
  className,
}: TreatmentTimelineProps) {
  const sortedMilestones = MILESTONE_ORDER.map(
    (name) =>
      milestones.find((m) => m.name === name) ?? {
        name,
        status: "pending" as const,
        date: null,
      },
  );

  return (
    <section
      className={cn("space-y-4", className)}
      aria-label={MICROCOPY_TREATMENT.title}
    >
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-gray-900">
          {MICROCOPY_TREATMENT.title}
        </h3>
        {typeof adherenceScore === "number" && adherenceScore !== null && (
          <span
            className={cn(
              "text-xs font-medium px-2 py-1 rounded-full",
              adherenceColor(adherenceScore),
            )}
            aria-label={`${MICROCOPY_TREATMENT.adherence.label}: ${adherenceScore}%`}
          >
            {MICROCOPY_TREATMENT.adherence.label}: {adherenceScore}%
          </span>
        )}
      </div>

      {currentStep && (
        <p className="text-xs text-gray-500">
          Paso actual:{" "}
          <span className="font-medium text-gray-700">{currentStep}</span>
        </p>
      )}

      {/* Timeline */}
      <div
        className="relative flex items-start justify-between"
        role="list"
        aria-label="Hitos del tratamiento"
      >
        {/* Connector line */}
        <div
          className="absolute top-5 left-5 right-5 h-0.5 bg-gray-200"
          aria-hidden="true"
        />
        {sortedMilestones.map((milestone) => (
          <div key={milestone.name} role="listitem" className="relative z-10">
            <MilestoneNode
              milestone={milestone}
              label={MICROCOPY_TREATMENT.milestones[milestone.name]}
            />
          </div>
        ))}
      </div>

      {/* Legend */}
      <div className="flex items-center gap-4 text-xs text-gray-500">
        <span className="flex items-center gap-1">
          <span
            className="w-3 h-3 rounded-full bg-green-600 inline-block"
            aria-hidden="true"
          />
          {MICROCOPY_TREATMENT.adherence.done}
        </span>
        <span className="flex items-center gap-1">
          <span
            className="w-3 h-3 rounded-full border-2 border-blue-600 inline-block"
            aria-hidden="true"
          />
          En progreso
        </span>
        <span className="flex items-center gap-1">
          <span
            className="w-3 h-3 rounded-full border-2 border-gray-300 inline-block"
            aria-hidden="true"
          />
          {MICROCOPY_TREATMENT.adherence.pending}
        </span>
      </div>
    </section>
  );
}
