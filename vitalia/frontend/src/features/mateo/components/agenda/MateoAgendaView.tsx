// cap: scheduling.mateo-agenda
// story-origin: vitalia-fase2-s1-TBD
"use client";

/**
 * MateoAgendaView.tsx — Client root component for Valeria Agenda sub-tab.
 * T-12 vitalia-fase2-valeria-agenda · F2-S1
 *
 * Root client boundary for the Agenda sub-tab.
 * Responsibilities:
 *   1. Hydrate React Query cache with SSR initialData.
 *   2. Mount useAgendaGrid with polling (refetchInterval: 30_000).
 *   3. Sync useFreshness on each data update.
 *   4. Track AGENDA_VIEWED telemetry on mount (fire-and-forget, PHI-safe).
 *   5. Compose full page: AgendaHeader + AgendaPresetFilters + AgendaCalendar
 *      + AppointmentDrawer + CrearCitaButton (desktop + FAB mobile).
 *
 * ADR-vitalia-004 § 3.3 — Client root composición cementada.
 *   - onSlotClick wired to openDrawer
 *   - AppointmentDrawer conditionally mounted when drawerOpen && selectedSlotId
 *   - AgendaPresetFilters always mounted
 *   - CrearCitaButton desktop + FAB (mobile)
 *   - monthAggregates passed to AgendaCalendar when view === "mes"
 *
 * Named exports only — NO default exports (FSD-Lite boundary enforcement).
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 * spec_anchor: 03-arch.md § 6.4 + 06-tickets.yaml T-12
 */

import { useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@clerk/nextjs";
import { useQueryClient } from "@tanstack/react-query";
import { Loader2 } from "lucide-react";
import { cn } from "@/lib/cn";
import { AgendaHeader } from "./AgendaHeader";
import { AgendaCalendar } from "./AgendaCalendar";
import { AgendaPresetFilters } from "./AgendaPresetFilters";
import { AppointmentDrawer } from "./AppointmentDrawer";
import { CrearCitaButton } from "./CrearCitaButton";
import { useAgendaGrid, useAgendaAggregates, agendaKeys } from "../../api/agenda";
import { useDrawerStore } from "../../store/agenda-store";
import { useAgendaFilters } from "../../hooks/useAgendaFilters";
import { useFreshness } from "../../hooks/useFreshness";
import { trackEvent, TrackEventType } from "../../lib/telemetry";
import { useTenantLocale } from "@/hooks/useTenantLocale";
import { useClinicId } from "@/hooks/useClinicId";
import type { AgendaGridResponseDTO } from "../../types/agenda-schema";
import type { AgendaView, AgendaFilter } from "../../types/agenda.types";

// ── Types ─────────────────────────────────────────────────────────────────────

export interface MateoAgendaViewProps {
  /** SSR initial data — hydrates React Query cache on first render. */
  initialData: AgendaGridResponseDTO;
  /** Initial view mode from URL. */
  initialView: AgendaView;
  /** Initial ISO 8601 date string from URL. */
  initialDate: string;
  /** Initial preset filter from URL. Null = no filter. */
  initialPresetFilter: AgendaFilter | null;
  /** Tenant ID from URL params (injected by page.tsx Server Component). */
  tenantId: string;
}

// ── Component ─────────────────────────────────────────────────────────────────

/**
 * Root client boundary for Valeria Agenda sub-tab.
 *
 * Hydrates React Query cache with SSR data, then polls every 30 seconds.
 * T-13 + T-14 will add calendar grid + appointment drawer as children.
 */
export function MateoAgendaView({
  initialData,
  initialView,
  initialDate,
  initialPresetFilter,
  tenantId,
}: MateoAgendaViewProps) {
  const queryClient = useQueryClient();
  const router = useRouter();
  const { view, date, presetFilter } = useAgendaFilters();
  const { drawerOpen, selectedSlotId, openDrawer } = useDrawerStore();
  const { freshnessLabel, updateFreshness } = useFreshness();
  const { currency, timezone, locale } = useTenantLocale();
  const clinicId = useClinicId();
  const { getToken } = useAuth();

  // T-FE-1: Empty slot click → push to nueva-cita with date/time prefill
  const handleEmptySlotClick = useCallback(
    (emptyDate: string, emptyTime: string) => {
      router.push(
        `/${tenantId}/mateo/agenda/nueva-cita?date=${emptyDate}&time=${emptyTime}`,
      );
    },
    [router, tenantId],
  );

  // Resolve effective view/date (URL overrides initial props after mount)
  const effectiveView = view ?? initialView;
  const effectiveDate = date ?? initialDate;

  // Hydrate React Query cache with SSR data on mount.
  // Uses initialPresetFilter (not null) to align the cache key with the live hook.
  // F6 fix: key must match what the live hook uses (initialPresetFilter, not null).
  useEffect(
    () => {
      queryClient.setQueryData(
        agendaKeys.grid(tenantId, initialView, initialDate, initialPresetFilter),
        initialData,
      );
    },
    // Intentionally run once on mount — SSR hydration
    // queryClient ref is stable, initial* props are server-rendered constants
    // biome-ignore lint: intentional empty deps for SSR hydration
    [],
  );

  // Track AGENDA_VIEWED on mount (fire-and-forget, PHI-safe).
  // Intentionally empty deps — run once on mount only.
  // tenant/clinic ride as headers via fetchClient (tenant_id no longer in payload).
  useEffect(
    () => {
      void (async () => {
        const token = await getToken();
        void trackEvent(
          TrackEventType.AGENDA_VIEWED,
          { view_mode: effectiveView },
          { token, tenantId, clinicId },
        );
      })();
    },
    // biome-ignore lint: intentional empty deps for mount-once telemetry
    [],
  );

  // Fetch grid data with 30s polling
  const { data, isLoading, isError, dataUpdatedAt } = useAgendaGrid({
    tenantId,
    view: effectiveView,
    date: effectiveDate,
    presetFilter: presetFilter ?? undefined,
    queryOptions: {
      placeholderData: initialData,
    },
  });

  // Month aggregates: A5 — useAgendaAggregates shape (AgendaAggregatesResponse) does not
  // match MonthAggregates (month+days) expected by AgendaCalendar. Passing null until
  // MonthCalendar adapter is implemented in a follow-up ticket.
  // TODO(T-13+): wire aggregatesQuery.data once MonthAggregates adapter is built.
  void useAgendaAggregates;  // import retained for future use

  // Sync freshness indicator with latest serverTime from BE
  useEffect(() => {
    if (data?.serverTime) {
      updateFreshness(data.serverTime);
    }
  }, [data?.serverTime, dataUpdatedAt, updateFreshness]);

  return (
    <main
      className={cn(
        "flex h-full flex-col gap-0 overflow-hidden",
        drawerOpen && "md:pr-0",
      )}
      aria-label="Agenda de citas"
    >
      {/* Header: view toggle + date picker + freshness indicator */}
      <AgendaHeader
        tenantId={tenantId}
        freshnessLabel={freshnessLabel}
      />

      {/* Preset filter chips — always rendered (T-16) */}
      <AgendaPresetFilters />

      {/* Loading overlay — shown only on initial load (not polling refresh) */}
      {isLoading && !data && (
        <div
          className="flex flex-1 items-center justify-center"
          aria-live="polite"
          aria-busy="true"
        >
          <Loader2
            className="h-8 w-8 animate-spin text-muted-foreground"
            aria-hidden="true"
          />
          <span className="sr-only">Cargando agenda…</span>
        </div>
      )}

      {/* Error state — shown when fetch fails and no data available */}
      {isError && !data && (
        <div
          className="flex flex-1 items-center justify-center"
          role="alert"
          aria-live="assertive"
        >
          <p className="text-sm text-destructive">
            Error al cargar la agenda. Reintentando…
          </p>
        </div>
      )}

      {/* Main content area — grid + drawer */}
      {(data || !isLoading) && (
        <section
          className="relative flex flex-1 overflow-hidden"
          aria-label="Grilla de citas"
        >
          {/* AgendaCalendar — dispatches to Day/Week/Month variant (T-13) */}
          <AgendaCalendar
            slots={data?.slots ?? []}
            tenantId={tenantId}
            monthAggregates={null}
            isLoading={isLoading && !data}
            onSlotClick={openDrawer}
            onEmptySlotClick={handleEmptySlotClick}
            className="flex-1"
          />
          {/* Empty-state announcement for screen readers (also tested by T-12 suite) */}
          {data && data.slots.length === 0 && !isLoading && (
            <p
              className="sr-only"
              aria-live="polite"
            >
              Sin citas para mostrar en este período.
            </p>
          )}

          {/* AppointmentDrawer — conditionally mounted when slot is selected (T-14) */}
          {drawerOpen && selectedSlotId && (
            <AppointmentDrawer
              tenantId={tenantId}
              tenantCurrency={currency}
              tenantLocale={locale}
              tenantTimezone={timezone}
            />
          )}
        </section>
      )}

      {/* CrearCitaButton — desktop variant (inline) + FAB mobile (fixed) (T-16) */}
      {clinicId && (
        <>
          {/* Desktop: positioned in lower-right of content area */}
          <CrearCitaButton
            tenantId={tenantId}
            clinicId={clinicId}
            variant="button"
            className="absolute bottom-6 right-6 hidden md:flex"
          />
          {/* Mobile FAB: fixed bottom-right */}
          <CrearCitaButton
            tenantId={tenantId}
            clinicId={clinicId}
            variant="fab"
            className="md:hidden"
          />
        </>
      )}
    </main>
  );
}
