// cap: brand_studio.lisa-marca
// story-origin: vitalia-fase1-s10-TBD
/**
 * MarcaPlaceholder — EmptyState genérico para Lisa/Marca.
 * F1-S10 vitalia-fase1-empty-states — T-2
 *
 * Consumes RIBBON_SUBTABS SSoT (READ-ONLY) para icon + label.
 * 16 genéricos: wrappers EmptyState boilerplate. Fase 2 los reemplaza.
 *
 * Server Component — no state, no effects.
 * Named export (NO default) per FSD-Lite enforce.
 *
 * spec_anchor: 03-arch.md § 3.3 + 06-tickets.yaml T-2
 * downstream-regression-na: brand-local placeholder; no cross-brand consumers
 */

import { RIBBON_SUBTABS } from "@/lib/agent-catalog";
import { EmptyState } from "@/components/shared/shell-organism/EmptyState";

/**
 * MarcaPlaceholder — placeholder genérico lisa/marca.
 * Muestra icon + label de RIBBON_SUBTABS["lisa"] con descripción ratificada.
 */
export function MarcaPlaceholder() {
  const meta = RIBBON_SUBTABS.lisa.find((s) => s.id === "marca")!;
  return (
    <EmptyState
      icon={meta.icon}
      title={`${meta.label} — próximamente`}
      description="Esta vista vive acá. El contenido real se cablea en Fase 2."
    />
  );
}
