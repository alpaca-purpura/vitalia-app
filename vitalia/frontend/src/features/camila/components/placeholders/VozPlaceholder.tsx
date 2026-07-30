// cap: patients.nps-tracking
// story-origin: vitalia-fase1-s10-TBD
/**
 * VozPlaceholder — placeholder Camila · Voz del paciente.
 * F1-S10 vitalia-fase1-empty-states — T-8
 *
 * 3-modos toggle (decorativo Fase 1) + 3 PlaceholderCards stats + footer aclarado.
 * Copy aclarado per spec § 10.2 batch 2 Chris feedback.
 *
 * Mockup baseline: vitalia/docs/product/stories/vitalia-fase1-empty-states/mockups/camila-voz-placeholder.html
 *
 * Client Component — uses internal React state for toggle mode (visual only, F1).
 * Named export (NO default) per FSD-Lite enforce.
 *
 * F2-S3 documented: wire toggle mode to Zustand store once functional backend available.
 *
 * spec_anchor: 06-tickets.yaml T-8
 * downstream-regression-na: brand-local camila feature; no cross-brand consumers
 */

"use client";

import { TogglePill } from "@/components/shared/shell-organism/TogglePill";
import { PlaceholderCard } from "@/components/shared/shell-organism/PlaceholderCard";

/**
 * Mode IDs for the decorative 3-mode toggle — F1 visual only.
 * F2-S3: wire to Zustand store with `value` + `onValueChange` once
 * TogglePill gains controlled API or replace with controlled Tabs wrapper.
 */
type VozMode = "decide" | "curaduria" | "manual";

const MODES: { value: VozMode; label: string }[] = [
  { value: "decide", label: "🤖 Camila decide" },
  { value: "curaduria", label: "🔍 Curaduría" },
  { value: "manual", label: "✋ Manual" },
];

const STATS: {
  id: string;
  icon: string;
  count: string;
  title: string;
  description: string;
}[] = [
  {
    id: "entrante",
    icon: "📥",
    count: "12",
    title: "Entrante",
    description:
      "Pacientes que respondieron — esperando que Camila analice y categorice",
  },
  {
    id: "curaduria",
    icon: "🔍",
    count: "4",
    title: "Curaduría",
    description: "Casos ambiguos que necesitan tu revisión antes de derivar",
  },
  {
    id: "activos",
    icon: "🔁",
    count: "47",
    title: "Ciclos activos",
    description: "Pacientes en flujo de seguimiento automático",
  },
];

/**
 * VozPlaceholder — Camila · Voz del paciente sub-tab placeholder (Fase 1 visual).
 * Client Component.
 */
export function VozPlaceholder() {
  // F1 decorativo: TogglePill manages active state internally (uncontrolled).
  // F2-S3: replace with controlled variant + Zustand store once mode drives real filtering.
  // The VozMode type anchors the semantic intent for F2 pickup.
  const _defaultMode: VozMode = "decide";

  return (
    <div>
      {/* Header row: title+description left | TogglePill right */}
      <div className="flex items-start justify-between mb-4 gap-4">
        <div className="flex-1">
          <h2 className="text-base font-semibold text-foreground">
            Voz del paciente
          </h2>
          <p className="text-xs text-muted-foreground mt-1">
            Camila pide feedback al paciente tras la visita y categoriza la
            respuesta para derivarla a reactivación, reputación o nueva venta.
          </p>
        </div>
        <TogglePill
          items={MODES}
          defaultValue={_defaultMode}
          data-testid="voz-mode-toggle"
        />
      </div>

      {/* 3 stat cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {STATS.map((stat) => (
          <PlaceholderCard
            key={stat.id}
            icon={stat.icon}
            count={stat.count}
            title={stat.title}
            description={stat.description}
            status="green"
          />
        ))}
      </div>

      {/* Footer aclarado batch 2 — verbatim from spec § 10.2 */}
      <p className="text-center text-[11px] text-muted-foreground mt-6 pt-4 border-t border-border">
        Camila gestiona el ciclo de voz del paciente: te avisa cuando algo sale
        del patrón esperado · te ahorra responder cada feedback uno por uno.
      </p>
    </div>
  );
}
