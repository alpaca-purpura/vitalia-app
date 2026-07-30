// cap: brand_studio.lisa-marca
// story-origin: vitalia-fase1-s10-TBD
/**
 * ServiciosPlaceholder — placeholder especial Lisa/Servicios con toggle Catálogo|Escalera.
 * F1-S10 vitalia-fase1-empty-states — T-3
 *
 * Renders:
 *   - SubTabHeader: "Servicios" + description
 *   - TogglePill: Catálogo (default) | Escalera
 *   - Catálogo pane: grid 2/3/5 cols + 4 PlaceholderCards tratamiento + 1 CTA outline dashed
 *   - Escalera pane: EmptyState "Escalera de valor — próximamente"
 *
 * Client Component — TogglePill requiere estado Radix Tabs (client boundary).
 * Named export (NO default) per FSD-Lite enforce.
 * No PHI real. Mock data hardcoded LatAm Perú baseline (S/ PEN).
 *
 * spec_anchor: 06-tickets.yaml T-3 + 01-spec.md § 10 + mockup lisa-servicios-placeholder.html
 * downstream-regression-na: brand-local placeholder; no cross-brand consumers
 */

"use client";

import {
  TogglePill,
  TogglePillContent,
} from "@/components/shared/shell-organism/TogglePill";
import { PlaceholderCard } from "@/components/shared/shell-organism/PlaceholderCard";
import { EmptyState } from "@/components/shared/shell-organism/EmptyState";
import { cn } from "@/lib/utils";

/** Mock treatment data — LatAm Perú baseline. No PHI. */
const MOCK_TREATMENTS = [
  {
    id: "limpieza-dental",
    icon: "🦷",
    title: "Limpieza dental",
    description: "S/ 120 · 30 min",
    status: "green" as const,
    statusLabel: "activo",
  },
  {
    id: "blanqueamiento",
    icon: "✨",
    title: "Blanqueamiento",
    description: "S/ 380 · 60 min",
    status: "green" as const,
    statusLabel: "activo",
  },
  {
    id: "implante",
    icon: "🦴",
    title: "Implante",
    description: "S/ 2,400 · 90 min",
    status: "yellow" as const,
    statusLabel: "borrador",
  },
  {
    id: "mantenimiento-periodontal",
    icon: "🪥",
    title: "Mantenimiento periodontal",
    description: "S/ 180 · 45 min",
    status: "green" as const,
    statusLabel: "activo",
  },
] as const;

const TOGGLE_ITEMS = [
  { value: "catalogo", label: "Catálogo" },
  { value: "escalera", label: "Escalera" },
] as const;

/**
 * ServiciosPlaceholder — especial placeholder para Lisa/Servicios.
 * Client Component (toggle state via Radix Tabs).
 */
export function ServiciosPlaceholder() {
  return (
    <div className="flex flex-col gap-0" data-testid="servicios-placeholder">
      {/* Header row: title + description + toggle pill right-aligned */}
      <div className="flex items-start justify-between gap-4 pb-4 border-b border-border mb-6">
        <div className="flex flex-col gap-1">
          <h2 className="text-lg font-semibold text-foreground">Servicios</h2>
          <p className="text-sm text-muted-foreground max-w-lg">
            Catálogo de tratamientos y escalera de valor (placeholder Fase 1).
          </p>
        </div>
      </div>

      {/* Toggle + panes */}
      <TogglePill
        items={TOGGLE_ITEMS as unknown as { value: string; label: string }[]}
        defaultValue="catalogo"
        data-testid="servicios-toggle"
      >
        {/* ── Catálogo pane ────────────────────────────────────── */}
        <TogglePillContent value="catalogo" data-testid="pane-catalogo">
          <div
            className="mt-4 grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3"
            data-testid="catalogo-grid"
          >
            {MOCK_TREATMENTS.map((treatment) => (
              <PlaceholderCard
                key={treatment.id}
                icon={treatment.icon}
                title={treatment.title}
                description={treatment.description}
                status={treatment.status}
              />
            ))}

            {/* CTA outline dashed — "Nuevo tratamiento" */}
            <div
              role="button"
              tabIndex={0}
              aria-label="Agregar nuevo tratamiento"
              data-testid="nuevo-tratamiento-cta"
              className={cn(
                "rounded-lg border-2 border-dashed border-border bg-transparent p-4",
                "flex flex-col items-center justify-center gap-1",
                "text-muted-foreground cursor-pointer",
                "hover:border-primary/50 hover:text-foreground transition-colors",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
              )}
            >
              <span aria-hidden="true" className="text-2xl select-none">
                +
              </span>
              <span className="text-sm text-center leading-tight">
                Nuevo tratamiento
              </span>
            </div>
          </div>
        </TogglePillContent>

        {/* ── Escalera pane ────────────────────────────────────── */}
        <TogglePillContent value="escalera" data-testid="pane-escalera">
          <EmptyState
            icon="📈"
            title="Escalera de valor — próximamente"
            description="Aquí vivirán los niveles de la escalera de valor del paciente (lead magnet → consulta → tratamiento core → upsell)."
            className="mt-4"
          />
        </TogglePillContent>
      </TogglePill>
    </div>
  );
}
