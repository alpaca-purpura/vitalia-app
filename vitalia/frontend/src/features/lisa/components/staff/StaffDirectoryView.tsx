// cap: clinics.lisa.doctores
// story-origin: vitalia-fase2-lisa-doctores
/**
 * StaffDirectoryView.tsx — Staff directory grid with filters, pagination, states.
 *
 * Client Component — needs React Query hooks + Zustand store + URL filter sync.
 * Renders: StaffDirectoryHeader + EntitySubNavBar(entity=null) + grid/loading/empty/error.
 *
 * States:
 *   loading  → skeleton cards ×6
 *   success  → grid cards + pagination
 *   empty    → StaffEmptyState + CTA
 *   error    → StaffErrorBanner + Reintentar
 *
 * SC-7: network failure → error banner + retry (no blank screen).
 * SC-8: 0 doctors → empty state with illustration + CTA.
 * SC-9: 1000+ doctors → server-side pagination (page=1 pageSize=24).
 *
 * T-FE-1 vitalia-fase2-lisa-doctores
 * spec_anchor: 01-spec.md § Wireframes Directorio + § Estados visuales + § SC-7/SC-8/SC-9
 * downstream-regression-na: brand-local vitalia FE component; no cross-brand consumers
 */

"use client";

import { useRef } from "react";
import { useParams } from "next/navigation";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { StaffDirectoryHeader } from "./StaffDirectoryHeader";
import { StaffCard } from "./StaffCard";
import { StaffEmptyState } from "./StaffEmptyState";
import { StaffErrorBanner } from "./StaffErrorBanner";
import { NuevoIntegranteModal } from "./NuevoIntegranteModal";
import { useStaffList } from "../../api/staff";
import { useStaffFilters } from "../../hooks/use-staff-filters";
import { useStaffUiStore } from "../../store/staff-ui-store";
import type { PaginatedDoctors } from "../../types/staff.types";

interface StaffDirectoryViewProps {
  /** SSR initial data — hydrates React Query cache to avoid first-fetch flash */
  initialData?: PaginatedDoctors;
}

/**
 * StaffDirectoryView — renders the lisa/staff directory.
 * Client root (per ADR-vitalia-004 § 3.3: "use client" here, page.tsx stays Server).
 */
export function StaffDirectoryView({ initialData }: StaffDirectoryViewProps) {
  const params = useParams<{ tenantId: string }>();
  const tenantId = params?.tenantId ?? "";

  // triggerRef: track the "+ Nuevo integrante" button so the modal can
  // return focus to it on close (WCAG 2.4.3 SC-10).
  const nuevoTriggerRef = useRef<HTMLButtonElement>(null);

  const { filters, setQ, setSpecialty, setActive, setPage } =
    useStaffFilters();
  const { nuevoIntegranteOpen, openNuevoIntegrante, closeNuevoIntegrante } =
    useStaffUiStore();

  const { data, isLoading, isError, refetch } = useStaffList({
    filters,
    initialData,
  });

  const doctors = data?.items ?? [];
  const total = data?.total ?? 0;
  const page = filters.page ?? 1;
  const pageSize = 24;
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const isEmpty = !isLoading && !isError && doctors.length === 0;

  return (
    <div className="flex flex-col gap-4" data-testid="staff-directory">
      {/* Header: title + CTA + search + filters */}
      <StaffDirectoryHeader
        filters={filters}
        onQ={setQ}
        onSpecialty={setSpecialty}
        onActive={setActive}
        onAddNew={openNuevoIntegrante}
        addNewRef={nuevoTriggerRef}
      />

      {/* Loading state: skeleton ×6 */}
      {isLoading && (
        <div
          role="status"
          aria-label="Cargando equipo…"
          aria-busy="true"
          className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3"
          data-testid="staff-skeleton"
        >
          {Array.from({ length: 6 }).map((_, i) => (
            <div
              key={`skeleton-${i}`}
              className="rounded-xl border border-border bg-card p-4 space-y-3"
            >
              <div className="flex items-start gap-3">
                <Skeleton className="h-14 w-14 rounded-full" />
                <div className="flex-1 space-y-2">
                  <Skeleton className="h-4 w-2/3" />
                  <Skeleton className="h-3 w-1/3" />
                </div>
              </div>
              <div className="grid grid-cols-3 gap-1">
                <Skeleton className="h-8 rounded" />
                <Skeleton className="h-8 rounded" />
                <Skeleton className="h-8 rounded" />
              </div>
              <Skeleton className="h-8 w-full rounded" />
            </div>
          ))}
        </div>
      )}

      {/* Error state: banner + retry */}
      {isError && !isLoading && (
        <StaffErrorBanner onRetry={() => void refetch()} />
      )}

      {/* Empty state: illustration + CTA */}
      {isEmpty && (
        <StaffEmptyState onAddClick={openNuevoIntegrante} />
      )}

      {/* Success state: grid cards */}
      {!isLoading && !isError && doctors.length > 0 && (
        <>
          <div
            className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3"
            role="list"
            aria-label="Lista de integrantes del equipo"
            data-testid="staff-grid"
          >
            {doctors.map((doctor) => (
              <div role="listitem" key={doctor.id}>
                <StaffCard doctor={doctor} tenantId={tenantId} />
              </div>
            ))}
          </div>

          {/* Pagination (SC-9: server-side, page size 24) */}
          {totalPages > 1 && (
            <nav
              aria-label="Paginación del directorio"
              className="flex items-center justify-center gap-2 mt-2"
              data-testid="staff-pagination"
            >
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage(page - 1)}
                disabled={page <= 1}
                aria-label="Página anterior"
              >
                <ChevronLeft className="h-4 w-4" />
              </Button>

              <span className="text-sm text-muted-foreground">
                {page} de {totalPages}
              </span>

              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage(page + 1)}
                disabled={page >= totalPages}
                aria-label="Página siguiente"
              >
                <ChevronRight className="h-4 w-4" />
              </Button>
            </nav>
          )}
        </>
      )}

      {/* NuevoIntegrante modal — triggerRef enables WCAG 2.4.3 focus-return on close. */}
      <NuevoIntegranteModal
        open={nuevoIntegranteOpen}
        onClose={closeNuevoIntegrante}
        triggerRef={nuevoTriggerRef}
      />
    </div>
  );
}
