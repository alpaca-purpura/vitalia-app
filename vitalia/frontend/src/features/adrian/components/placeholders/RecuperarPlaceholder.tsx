// cap: crm.adrian-embudo
// story-origin: vitalia-fase2-adrian-embudo
/**
 * RecuperarPlaceholder — Sub-tab hermana de Embudo (Adrián Recuperar V4).
 *
 * T-FE-1 vitalia-fase2-adrian-embudo (2026-06-03):
 * Placeholder until T-FE-3 ships the real RecuperarView page.tsx at /adrian/recuperar.
 *
 * Shows the upcoming V4 functionality: congelados + diagnose + decidio-no reactivación.
 *
 * Server Component (no state).
 * Named export per FSD-Lite enforce.
 * No hardcoded hex — Tailwind semantic tokens only.
 * No PHI real data.
 *
 * spec_anchor: 01-spec.md § V4 Recuperar + 03-arch-fe.md § FSD-Lite layout
 * downstream-regression-na: brand-local placeholder; no cross-brand consumers
 */

import { EmptyState } from "@/components/shared/shell-organism/EmptyState";

/**
 * RecuperarPlaceholder — placeholder for the Recuperar sub-tab.
 * Real implementation (RecuperarView + FrozenLeadRow) ships in T-FE-3.
 */
export function RecuperarPlaceholder() {
  return (
    <EmptyState
      icon="🧊"
      title="Recuperar — próximamente"
      description="Aquí verás los leads congelados y los que decidieron no. Adrián los diagnostica y te muestra cómo reactivarlos."
    />
  );
}
