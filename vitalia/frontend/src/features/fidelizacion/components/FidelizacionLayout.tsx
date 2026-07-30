// cap: patients.nps-tracking
// story-origin: TBD
"use client";

/**
 * FidelizacionLayout — page orchestrator for fidelización module.
 *
 * Client Component: manages URL state (tab, period) + ephemeral store (modals).
 * Server-First boundary: page.tsx is Server Component; this is the Client leaf.
 *
 * HIPAA-lite: RequireRole wraps all PHI sections.
 * Accessibility: error boundary behavior (error state renders banner, not crash).
 *
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 */

import { Suspense } from "react";
import { cn } from "@/lib/cn";
import { FIDELIZACION_COPY } from "../copy";
import { useFidelizacionSummary } from "../api/use-fidelizacion-summary";
import { useFidelizacionUrlState } from "../hooks/use-fidelizacion-url-state";
import { useFidelizacionStore } from "../hooks/use-fidelizacion-store";
import { FidelizacionKPIsHero } from "./FidelizacionKPIsHero";
import { FidelizacionTabsBar } from "./FidelizacionTabsBar";
import { FidelizacionActivityFooter } from "./FidelizacionActivityFooter";
import { MultiSessionTab } from "./tabs/MultiSessionTab";
import { FollowUpTab } from "./tabs/FollowUpTab";
import { MaintenanceTab } from "./tabs/MaintenanceTab";
import { AbsenceTab } from "./tabs/AbsenceTab";
import { NPSResumenTab } from "./tabs/NPSResumenTab";
import { ConfirmTemplateModal } from "./ConfirmTemplateModal";
import { PausePatientModal } from "./PausePatientModal";
import { ManualCallLoggedModal } from "./ManualCallLoggedModal";
import { SuggestSlotsModal } from "./SuggestSlotsModal";
import { ReEngagementContactSidebar } from "./ReEngagementContactSidebar";
import { RequireRole } from "@/components/shared/phi";
import { useCurrentUser } from "@/hooks/useCurrentUser";
import type { PatternRow } from "../types/re-engagement";

/**
 * Period selector chip bar
 */
function PeriodSelector({
  period,
  onChange,
}: {
  period: "7d" | "30d" | "90d";
  onChange: (p: "7d" | "30d" | "90d") => void;
}) {
  const copy = FIDELIZACION_COPY.period;
  return (
    <div className="flex gap-1" aria-label={copy.label} role="group">
      {(["7d", "30d", "90d"] as const).map((p) => (
        <button
          key={p}
          type="button"
          aria-pressed={period === p}
          onClick={() => onChange(p)}
          className={cn(
            "rounded px-2.5 py-1 text-xs font-medium transition-colors",
            period === p
              ? "bg-[hsl(var(--vitalia-primary,210_90%_50%))] text-white"
              : "text-[hsl(var(--vitalia-muted,220_10%_55%))] hover:text-[hsl(var(--vitalia-fg,220_25%_15%))]",
          )}
        >
          {copy[p]}
        </button>
      ))}
    </div>
  );
}

/**
 * Main fidelización layout — full page orchestrator.
 */
export function FidelizacionLayout() {
  const { role } = useCurrentUser();
  const {
    urlState,
    setTab,
    setPeriod,
    openConfirmTemplateModal,
    closeConfirmTemplateModal,
    openPauseModal,
    closePauseModal,
    openManualCallModal,
    closeManualCallModal,
    openSuggestSlotsModal,
    closeSuggestSlotsModal,
  } = useFidelizacionUrlState();

  const store = useFidelizacionStore();
  const { data: summary, isPending: summaryPending } = useFidelizacionSummary(
    urlState.period,
  );

  const copy = FIDELIZACION_COPY;

  // Shared action handlers for all tabs
  function handleSendReminder(row: PatternRow) {
    openConfirmTemplateModal(row.reEngagementEventId);
    store.selectPatient(row.patientId);
  }

  function handleSuggestSlots(row: PatternRow) {
    openSuggestSlotsModal(row.reEngagementEventId);
    store.selectPatient(row.patientId);
  }

  function handlePause(row: PatternRow) {
    openPauseModal(row.reEngagementEventId);
    store.selectPatient(row.patientId);
  }

  function handleMarkExternal(row: PatternRow) {
    // TODO: call useMarkExternal mutation directly (no modal needed)
    store.selectPatient(row.patientId);
  }

  function handleMarkNoContinue(row: PatternRow) {
    // TODO: call useMarkNoContinue mutation directly (no modal needed)
    store.selectPatient(row.patientId);
  }

  function handleLogManualCall(row: PatternRow) {
    openManualCallModal(row.reEngagementEventId);
    store.selectPatient(row.patientId);
  }

  function handleOpenConversation(row: PatternRow) {
    // Navigate to inbox with the conversation — per 03-arch-fe.md § 3
    // Use window.location for now (no router.push needed for external nav)
    store.selectPatient(row.patientId);
  }

  const cardHandlers = {
    onSendReminder: handleSendReminder,
    onSuggestSlots: handleSuggestSlots,
    onPause: handlePause,
    onMarkExternal: handleMarkExternal,
    onMarkNoContinue: handleMarkNoContinue,
    onLogManualCall: handleLogManualCall,
    onOpenConversation: handleOpenConversation,
  };

  const tabCommonProps = {
    period: urlState.period,
    vertical: urlState.vertical,
    doctorId: urlState.doctor,
    urgency: urlState.urgency,
    ...cardHandlers,
  };

  return (
    <RequireRole
      roles={["doctor", "nurse", "admin_clinic"]}
      userRole={role}
      fallback={
        <div
          role="alert"
          className="rounded-lg border border-[hsl(var(--vitalia-danger,0_75%_45%))] bg-[hsl(var(--vitalia-danger-bg,0_100%_97%))] p-6 text-sm text-[hsl(var(--vitalia-danger,0_75%_45%))]"
        >
          {copy.errors.phiAccessDenied}
        </div>
      }
    >
      <div className="flex h-full flex-col gap-0">
        {/* Page header */}
        <header className="flex items-center justify-between border-b border-[hsl(var(--vitalia-border,220_13%_91%))] px-6 py-4">
          <div>
            <h1 className="text-xl font-semibold text-[hsl(var(--vitalia-fg,220_25%_15%))]">
              {copy.page.title}
            </h1>
            <p className="text-sm text-[hsl(var(--vitalia-muted,220_10%_55%))]">
              {copy.page.description}
            </p>
          </div>
          <PeriodSelector period={urlState.period} onChange={setPeriod} />
        </header>

        {/* KPIs hero */}
        <div className="border-b border-[hsl(var(--vitalia-border,220_13%_91%))] px-6 py-4">
          <FidelizacionKPIsHero isPending={summaryPending} data={summary} />
        </div>

        {/* Tabs bar */}
        <FidelizacionTabsBar activeTab={urlState.tab} onTabChange={setTab} />

        {/* Tab content */}
        <main className="flex-1 overflow-y-auto">
          {urlState.tab === "multisession" && (
            <MultiSessionTab {...tabCommonProps} />
          )}
          {urlState.tab === "followup" && <FollowUpTab {...tabCommonProps} />}
          {urlState.tab === "maintenance" && (
            <MaintenanceTab {...tabCommonProps} />
          )}
          {urlState.tab === "absence" && <AbsenceTab {...tabCommonProps} />}
          {urlState.tab === "nps" && <NPSResumenTab period={urlState.period} />}
        </main>

        {/* Activity footer */}
        <Suspense>
          <FidelizacionActivityFooter />
        </Suspense>

        {/* Contact sidebar */}
        {store.selectedPatientId && (
          <ReEngagementContactSidebar
            patientId={store.selectedPatientId}
            onClose={() => store.selectPatient(null)}
          />
        )}

        {/* Modals (rendered in portal via fixed position) */}
        {urlState.confirmTemplateModal && (
          <ConfirmTemplateModal
            eventId={urlState.confirmTemplateModal}
            patientId={store.selectedPatientId ?? ""}
            payload={{
              templateId: "",
              pattern: "multi_session",
              slotValues: {},
              triggerSource: "manual",
            }}
            previewText="[Vista previa del template se cargará desde el evento]"
            onClose={closeConfirmTemplateModal}
          />
        )}

        {urlState.pauseModal && store.selectedPatientId && (
          <PausePatientModal
            eventId={urlState.pauseModal}
            patientId={store.selectedPatientId}
            onClose={closePauseModal}
          />
        )}

        {urlState.manualCallModal && store.selectedPatientId && (
          <ManualCallLoggedModal
            eventId={urlState.manualCallModal}
            patientId={store.selectedPatientId}
            onClose={closeManualCallModal}
          />
        )}

        {urlState.suggestSlotsModal && store.selectedPatientId && (
          <SuggestSlotsModal
            eventId={urlState.suggestSlotsModal}
            patientId={store.selectedPatientId}
            doctorId={urlState.doctor}
            onClose={closeSuggestSlotsModal}
          />
        )}
      </div>
    </RequireRole>
  );
}
