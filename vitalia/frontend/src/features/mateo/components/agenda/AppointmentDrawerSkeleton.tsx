// cap: scheduling.mateo-agenda
// story-origin: vitalia-fase2-s1-TBD
"use client";

/**
 * AppointmentDrawerSkeleton.tsx — Loading skeleton for AppointmentDrawer.
 * T-14 vitalia-fase2-valeria-agenda
 *
 * Shown while useAppointmentDetail is loading (drawer opened, fetch in flight).
 * Uses Shadcn Skeleton primitives — matches 5-section layout of the real drawer.
 *
 * Named exports only — NO default exports (FSD-Lite boundary enforcement).
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 * spec_anchor: 03-arch.md § 6.6 + 06-tickets.yaml T-14
 */

import { Skeleton } from "@/components/ui/skeleton";

// ── Component ─────────────────────────────────────────────────────────────────

/**
 * Renders skeleton placeholders matching the AppointmentDrawer layout.
 * Includes header skeleton + 5 accordion section skeletons.
 */
export function AppointmentDrawerSkeleton() {
  return (
    <div
      className="flex flex-col gap-4 p-6"
      role="status"
      aria-label="Cargando detalle del turno…"
      aria-busy="true"
    >
      {/* Header skeleton: avatar + name + DNI + button */}
      <div className="flex items-start gap-3">
        <Skeleton className="h-10 w-10 rounded-full shrink-0" />
        <div className="flex flex-col gap-2 flex-1">
          <Skeleton className="h-4 w-32" />
          <Skeleton className="h-3 w-24" />
        </div>
        <Skeleton className="h-8 w-28" />
      </div>

      <Skeleton className="h-px w-full" />

      {/* Accordion section skeletons × 5 */}
      {Array.from({ length: 5 }).map((_, i) => (
        <div key={i} className="flex flex-col gap-2 border-b pb-4">
          <div className="flex items-center justify-between py-1">
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-4 w-4 rounded-sm" />
          </div>
          {/* First 2 expanded by default — show content skeleton */}
          {i < 2 && (
            <div className="flex flex-col gap-2 pl-1">
              <Skeleton className="h-3 w-full" />
              <Skeleton className="h-3 w-3/4" />
              <Skeleton className="h-3 w-1/2" />
            </div>
          )}
        </div>
      ))}

      <span className="sr-only">Cargando información del turno</span>
    </div>
  );
}
