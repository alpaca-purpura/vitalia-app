// cap: marketing.lucas-stage-recommendations
// story-origin: vitalia-fase1-s10-TBD
/**
 * ResultadosPlaceholder — EmptyState genérico para Lucas/Resultados.
 * F1-S10 vitalia-fase1-empty-states — T-2
 *
 * Consumes RIBBON_SUBTABS SSoT (READ-ONLY) para icon + label.
 * Server Component — named export.
 *
 * spec_anchor: 03-arch.md § 3.3 + 06-tickets.yaml T-2
 * downstream-regression-na: brand-local placeholder; no cross-brand consumers
 */

import { RIBBON_SUBTABS } from "@/lib/agent-catalog";
import { EmptyState } from "@/components/shared/shell-organism/EmptyState";

/**
 * ResultadosPlaceholder — placeholder genérico lucas/resultados.
 */
export function ResultadosPlaceholder() {
  const meta = RIBBON_SUBTABS.lucas.find((s) => s.id === "resultados")!;
  return (
    <EmptyState
      icon={meta.icon}
      title={`${meta.label} — próximamente`}
      description="Esta vista vive acá. El contenido real se cablea en Fase 2."
    />
  );
}
