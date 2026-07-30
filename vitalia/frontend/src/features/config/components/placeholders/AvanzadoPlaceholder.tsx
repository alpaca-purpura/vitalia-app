// cap: iam.iam-scaffold-slice-1
// story-origin: vitalia-fase1-s10-TBD
/**
 * AvanzadoPlaceholder — EmptyState genérico para Config/Avanzado.
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
 * AvanzadoPlaceholder — placeholder genérico config/avanzado.
 */
export function AvanzadoPlaceholder() {
  const meta = RIBBON_SUBTABS.config.find((s) => s.id === "avanzado")!;
  return (
    <EmptyState
      icon={meta.icon}
      title={`${meta.label} — próximamente`}
      description="Esta vista vive acá. El contenido real se cablea en Fase 2."
    />
  );
}
