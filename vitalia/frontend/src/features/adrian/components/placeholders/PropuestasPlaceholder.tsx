// cap: sales_agent.adrian-3-tools-mvp
// story-origin: vitalia-fase1-s10-TBD
/**
 * PropuestasPlaceholder — EmptyState genérico para Adrián/Propuestas.
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
 * PropuestasPlaceholder — placeholder genérico adrian/propuestas.
 */
export function PropuestasPlaceholder() {
  const meta = RIBBON_SUBTABS.adrian.find((s) => s.id === "propuestas")!;
  return (
    <EmptyState
      icon={meta.icon}
      title={`${meta.label} — próximamente`}
      description="Esta vista vive acá. El contenido real se cablea en Fase 2."
    />
  );
}
