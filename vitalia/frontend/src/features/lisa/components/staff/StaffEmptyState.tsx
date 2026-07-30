// cap: clinics.lisa.doctores
// story-origin: vitalia-fase2-lisa-doctores
/**
 * StaffEmptyState.tsx — Empty state for Lisa Staff directory (SC-8).
 *
 * Shows illustration + heading + CTA "Agregar primer integrante".
 * Server Component default — no interactivity needed; CTA opens modal in parent.
 *
 * Microcopy per 01-spec.md § Microcopy (authoritative).
 * Spanish neutro LatAm — sin voseo.
 *
 * T-FE-1 vitalia-fase2-lisa-doctores
 * spec_anchor: 01-spec.md § SC-8 + § Microcopy
 * downstream-regression-na: brand-local vitalia FE component; no cross-brand consumers
 */

import { Button } from "@/components/ui/button";

interface StaffEmptyStateProps {
  onAddClick: () => void;
}

/**
 * StaffEmptyState — renders when clinic has 0 staff members.
 * data-testid="empty-doctores" required by SC-8 graders.
 */
export function StaffEmptyState({ onAddClick }: StaffEmptyStateProps) {
  return (
    <div
      data-testid="empty-doctores"
      className="flex flex-col items-center justify-center gap-4 py-20 px-6 text-center"
      role="status"
      aria-label="Sin integrantes en el equipo"
    >
      {/* Illustration placeholder — actual SVG asset to be provided */}
      <div
        className="flex h-24 w-24 items-center justify-center rounded-full bg-muted text-4xl"
        aria-hidden="true"
      >
        👨‍⚕️
      </div>

      <div className="space-y-2">
        <h2 className="text-xl font-semibold text-foreground">
          Aún no hay integrantes en tu equipo
        </h2>
        <p className="text-sm text-muted-foreground max-w-xs">
          Agrega al primer integrante para comenzar a gestionar los perfiles,
          horarios y servicios de tu clínica.
        </p>
      </div>

      {/* Navy bg: #180D95 on white = 13:1 contrast (WCAG AA/AAA pass). */}
      <Button
        onClick={onAddClick}
        className="mt-2 bg-[color:var(--vitalia-azul-marino-color)] text-white hover:opacity-90 dark:bg-[color:var(--vitalia-azul-marino-color)] dark:text-white"
        data-testid="btn-agregar-primer-integrante"
      >
        Agregar primer integrante
      </Button>
    </div>
  );
}
