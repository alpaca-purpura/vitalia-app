// cap: patients.nps-tracking
// story-origin: TBD
"use client";

/**
 * ReEngagementCard — polymorphic card for re-engagement patterns.
 *
 * 4 variants: multi_session | follow_up | maintenance | absence.
 * PHI: patient name wrapped with RequireRole + PiiMaskedSpan.
 * Accessibility: article role, keyboard nav, ARIA labels on actions.
 *
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 */

import type { MouseEvent } from "react";
import { cn } from "@/lib/cn";
import { RequireRole } from "@/components/shared/phi";
import { PiiMaskedSpan } from "@/components/shared/phi";
import { FIDELIZACION_COPY } from "../copy";
import type {
  PatternRow,
  ActionDescriptor,
  ActionId,
  MultiSessionData,
  FollowUpData,
  MaintenanceData,
  AbsenceData,
  PatternData,
} from "../types/re-engagement";
import { useCurrentUser } from "@/hooks/useCurrentUser";
import { useTenantLocale } from "@/hooks/useTenantLocale";
import { formatMoney } from "@/lib/format/formatMoney";
import { formatTenantDate } from "@/lib/format/formatTenantDate";

const URGENCY_CLASS_MAP: Record<string, string> = {
  critical:
    "border-l-4 border-l-[hsl(var(--vitalia-danger,0_75%_45%))] bg-[hsl(var(--vitalia-danger-bg,0_100%_97%))]",
  alert:
    "border-l-4 border-l-[hsl(var(--vitalia-warn,38_92%_50%))] bg-[hsl(var(--vitalia-warn-bg,38_100%_97%))]",
  near: "border-l-4 border-l-[hsl(var(--vitalia-info,210_90%_50%))] bg-white",
  waiting:
    "border-l-4 border-l-[hsl(var(--vitalia-muted,220_10%_55%))] bg-white",
  up_to_date:
    "border-l-4 border-l-[hsl(var(--vitalia-success,145_55%_40%))] bg-white",
};

export interface ReEngagementCardHandlers {
  onSendReminder: (row: PatternRow) => void;
  onSuggestSlots: (row: PatternRow) => void;
  onPause: (row: PatternRow) => void;
  onMarkExternal: (row: PatternRow) => void;
  onMarkNoContinue: (row: PatternRow) => void;
  onLogManualCall: (row: PatternRow) => void;
  onOpenConversation: (row: PatternRow) => void;
}

interface ReEngagementCardProps extends ReEngagementCardHandlers {
  row: PatternRow;
  className?: string;
}

function UrgencyBadge({ urgency }: { urgency: PatternRow["urgency"] }) {
  const copy = FIDELIZACION_COPY.urgency;
  return (
    <span
      className="text-xs font-semibold uppercase tracking-wide text-[hsl(var(--vitalia-muted,220_10%_55%))]"
      aria-label={copy.ariaLabel(copy[urgency])}
    >
      {copy[urgency]}
    </span>
  );
}

function MultiSessionBody({
  data,
  timezone,
}: {
  data: MultiSessionData;
  timezone: string;
}) {
  const copy = FIDELIZACION_COPY.multi_session_card;
  return (
    <div className="mt-2 space-y-1 text-sm text-[hsl(var(--vitalia-fg,220_25%_15%))]">
      <p className="font-medium">{data.offerLabel}</p>
      <p>
        {copy.sessionsProgress(data.sessionsCompleted, data.sessionsExpected)}
      </p>
      <p className="text-[hsl(var(--vitalia-muted,220_10%_55%))]">
        {copy.gap(data.gapDays)}
      </p>
      <p className="text-[hsl(var(--vitalia-muted,220_10%_55%))]">
        {copy.lastSession}: {formatTenantDate(data.lastSessionDate, timezone)}
      </p>
    </div>
  );
}

function FollowUpBody({
  data,
  timezone,
}: {
  data: FollowUpData;
  timezone: string;
}) {
  const copy = FIDELIZACION_COPY.follow_up_card;
  return (
    <div className="mt-2 space-y-1 text-sm text-[hsl(var(--vitalia-fg,220_25%_15%))]">
      <p>{copy.followUpIn(data.daysUntilDue)}</p>
      <p className="text-[hsl(var(--vitalia-muted,220_10%_55%))]">
        {copy.doctor} {data.doctorName}
      </p>
      {data.followUpReason && (
        <p className="text-[hsl(var(--vitalia-muted,220_10%_55%))]">
          {copy.reason}: {data.followUpReason}
        </p>
      )}
      <p className="text-[hsl(var(--vitalia-muted,220_10%_55%))] text-xs">
        Vence: {formatTenantDate(data.followUpDueAt, timezone)}
      </p>
    </div>
  );
}

function MaintenanceBody({
  data,
  timezone,
}: {
  data: MaintenanceData;
  timezone: string;
}) {
  const copy = FIDELIZACION_COPY.maintenance_card;
  return (
    <div className="mt-2 space-y-1 text-sm text-[hsl(var(--vitalia-fg,220_25%_15%))]">
      <p className="font-medium">{data.offerLabel}</p>
      <p>{data.cadenceLabel}</p>
      <p>{copy.daysUntil(data.daysUntilDue)}</p>
      <p className="text-[hsl(var(--vitalia-muted,220_10%_55%))] text-xs">
        {copy.lastService}: {formatTenantDate(data.lastServiceDate, timezone)}
      </p>
    </div>
  );
}

function AbsenceBody({
  data,
  userRole,
  timezone,
  currency,
}: {
  data: AbsenceData;
  userRole: string | null | undefined;
  timezone: string;
  currency: string;
}) {
  const copy = FIDELIZACION_COPY.absence_card;
  return (
    <div className="mt-2 space-y-1 text-sm text-[hsl(var(--vitalia-fg,220_25%_15%))]">
      <p>{copy.monthsInactive(data.monthsInactive)}</p>
      <p className="text-[hsl(var(--vitalia-muted,220_10%_55%))] text-xs">
        {copy.lastAppointment}:{" "}
        {formatTenantDate(data.lastAppointmentDate, timezone)}
      </p>
      {/* Lifetime value — PHI in context (known patient) */}
      <RequireRole
        roles={["doctor", "nurse", "admin_clinic"]}
        userRole={userRole}
      >
        {data.lifetimeValueCents !== null && (
          <p className="text-[hsl(var(--vitalia-muted,220_10%_55%))] text-xs">
            {copy.lifetimeValue}:{" "}
            {formatMoney(
              data.lifetimeValueCents / 100,
              data.currency ?? currency,
            )}
          </p>
        )}
      </RequireRole>
      {!data.marketingOptIn && (
        <p className="text-[hsl(var(--vitalia-warn,38_92%_50%))] text-xs">
          {copy.noMarketing}
        </p>
      )}
    </div>
  );
}

function PatternBody({
  data,
  userRole,
  timezone,
  currency,
}: {
  data: PatternData;
  userRole: string | null | undefined;
  timezone: string;
  currency: string;
}) {
  switch (data.kind) {
    case "multi_session":
      return <MultiSessionBody data={data} timezone={timezone} />;
    case "follow_up":
      return <FollowUpBody data={data} timezone={timezone} />;
    case "maintenance":
      return <MaintenanceBody data={data} timezone={timezone} />;
    case "absence":
      return (
        <AbsenceBody
          data={data}
          userRole={userRole}
          timezone={timezone}
          currency={currency}
        />
      );
  }
}

function ActionButton({
  action,
  label,
  onClick,
}: {
  action: ActionDescriptor;
  label: string;
  onClick: (e: MouseEvent<HTMLButtonElement>) => void;
}) {
  return (
    <button
      type="button"
      disabled={!action.enabled}
      onClick={action.enabled ? onClick : undefined}
      aria-disabled={!action.enabled}
      aria-describedby={
        !action.enabled && action.disabledReason
          ? `disabled-reason-${action.id}`
          : undefined
      }
      title={!action.enabled ? (action.disabledReason ?? undefined) : undefined}
      className={cn(
        "rounded px-2 py-1 text-xs font-medium transition-colors",
        action.enabled
          ? "bg-[hsl(var(--vitalia-primary,210_90%_50%))] text-white hover:bg-[hsl(var(--vitalia-primary-hover,210_90%_45%))]"
          : "cursor-not-allowed bg-[hsl(var(--vitalia-bg-soft,220_20%_96%))] text-[hsl(var(--vitalia-muted,220_10%_55%))]",
      )}
    >
      {label}
    </button>
  );
}

/**
 * Re-engagement card — polymorphic across 4 pattern types.
 * PHI-guarded patient name via RequireRole + PiiMaskedSpan.
 */
export function ReEngagementCard({
  row,
  onSendReminder,
  onSuggestSlots,
  onPause,
  onMarkExternal,
  onMarkNoContinue,
  onLogManualCall,
  onOpenConversation,
  className,
}: ReEngagementCardProps) {
  const { role } = useCurrentUser();
  const { timezone, currency } = useTenantLocale();
  const copy = FIDELIZACION_COPY.actions;

  const actionMap: Record<ActionId, () => void> = {
    send_reminder: () => onSendReminder(row),
    suggest_slots: () => onSuggestSlots(row),
    pause_patient: () => onPause(row),
    mark_external: () => onMarkExternal(row),
    mark_no_continue: () => onMarkNoContinue(row),
    open_conversation: () => onOpenConversation(row),
    call_manually: () => onLogManualCall(row),
  };

  return (
    <article
      data-testid={`re-engagement-card-${row.pattern}-${row.reEngagementEventId}`}
      className={cn(
        "rounded-md border p-4 transition-shadow hover:shadow-sm",
        URGENCY_CLASS_MAP[row.urgency],
        className,
      )}
    >
      {/* Header: urgency + PHI-guarded patient name */}
      <header className="flex items-center justify-between gap-2">
        <UrgencyBadge urgency={row.urgency} />
        <RequireRole
          roles={["doctor", "nurse", "admin_clinic"]}
          userRole={role}
          fallback={
            <PiiMaskedSpan
              value={row.patientName}
              fieldType="name"
              className="text-sm text-[hsl(var(--vitalia-muted,220_10%_55%))]"
            />
          }
        >
          <span className="text-sm font-medium text-[hsl(var(--vitalia-fg,220_25%_15%))]">
            {row.patientName}
          </span>
        </RequireRole>
      </header>

      {/* Pattern-specific body */}
      <PatternBody
        data={row.patternData}
        userRole={role}
        timezone={timezone}
        currency={currency}
      />

      {/* Actions row */}
      <footer className="mt-3 flex flex-wrap gap-2">
        {row.acciones.map((action) => (
          <ActionButton
            key={action.id}
            action={action}
            label={copy[action.id]}
            onClick={(e) => {
              e.stopPropagation();
              actionMap[action.id]();
            }}
          />
        ))}
      </footer>
    </article>
  );
}
