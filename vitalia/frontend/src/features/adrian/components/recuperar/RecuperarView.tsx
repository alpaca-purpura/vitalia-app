// cap: crm.adrian-embudo
// story-origin: vitalia-fase2-adrian-embudo
/**
 * RecuperarView — sub-tab hermana de Embudo (/adrian/recuperar, V4).
 * T-FE-3 vitalia-fase2-adrian-embudo
 *
 * Two segments:
 *   🧊 Recién congelados (inactividad / sin respuesta presupuesto / agente trabado)
 *   🚫 Decidió no reciente (closure_reason + cohorte Camila)
 *
 * Horizon: short-term recovery operated by Adrián.
 * Long-term (90d Camila cohorts) → story camila-reactivar (not this).
 *
 * States: loading (skeleton) · empty ("Sin leads para recuperar 🎉") · success · error.
 *
 * spec_anchor: 01-spec.md § V4 + 03-arch-fe.md § RecuperarView D.11
 * downstream-regression-na: brand-local vitalia FE
 */
"use client";

import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/shared/shell-organism/EmptyState";
import { useFrozenLeads } from "../../api/frozen";
import { FrozenLeadRow } from "./FrozenLeadRow";

// ── Types ─────────────────────────────────────────────────────────────────────

export interface RecuperarViewProps {
  tenantId: string;
}

// ── Loading skeleton ──────────────────────────────────────────────────────────

function RecuperarSkeleton() {
  return (
    <div
      className="flex flex-col gap-3 p-4"
      aria-busy="true"
      role="status"
      aria-label="Cargando leads para recuperar"
    >
      {[1, 2, 3].map((i) => (
        <Skeleton key={i} className="h-24 w-full rounded-lg" />
      ))}
    </div>
  );
}

// ── Component ─────────────────────────────────────────────────────────────────

/**
 * RecuperarView — shows frozen + decidio_no leads with AI diagnose + reactivate.
 *
 * Short-term Adrián recovery (≤14d frozen / recently lost).
 * Links to Camila cohorte for long-term (90d) recovery.
 */
export function RecuperarView({ tenantId: _tenantId }: RecuperarViewProps) {
  const { data, isLoading, isError } = useFrozenLeads();

  if (isLoading) return <RecuperarSkeleton />;

  if (isError || !data) {
    return (
      <div className="p-4 text-sm text-muted-foreground" role="alert">
        No se pudieron cargar los leads para recuperar. Intenta recargar la
        página.
      </div>
    );
  }

  const { recienCongelados, decidioNo } = data;
  const hasAny = recienCongelados.length > 0 || decidioNo.length > 0;

  if (!hasAny) {
    return (
      <div data-testid="recuperar-empty">
        <EmptyState
          icon="✅"
          title="Sin leads para recuperar"
          description="¡Todo el pipeline está activo! Los leads congelados aparecerán aquí."
        />
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6 p-4" data-testid="recuperar-view">

      {/* ── Recién congelados ─────────────────────────────────────────────── */}
      {recienCongelados.length > 0 && (
        <section aria-labelledby="recien-congelados-heading">
          <h2
            id="recien-congelados-heading"
            className="text-sm font-semibold text-muted-foreground uppercase tracking-wide mb-3 flex items-center gap-2"
          >
            <span aria-hidden="true">🧊</span>
            Recién congelados
            <span className="font-normal text-xs normal-case tracking-normal">
              ({recienCongelados.length})
            </span>
          </h2>
          <ul className="flex flex-col gap-3" role="list">
            {recienCongelados.map((lead) => (
              <li key={lead.id}>
                <FrozenLeadRow lead={lead} segment="recien" />
              </li>
            ))}
          </ul>
        </section>
      )}

      {/* ── Decidió no ───────────────────────────────────────────────────── */}
      {decidioNo.length > 0 && (
        <section aria-labelledby="decidio-no-heading">
          <h2
            id="decidio-no-heading"
            className="text-sm font-semibold text-muted-foreground uppercase tracking-wide mb-3 flex items-center gap-2"
          >
            <span aria-hidden="true">🚫</span>
            Decidió no reciente
            <span className="font-normal text-xs normal-case tracking-normal">
              ({decidioNo.length})
            </span>
          </h2>
          <p className="text-xs text-muted-foreground mb-3">
            Reactivación puntual disponible. La cadencia de 90 días la gestiona
            Camila.
          </p>
          <ul className="flex flex-col gap-3" role="list">
            {decidioNo.map((lead) => (
              <li key={lead.id}>
                <FrozenLeadRow lead={lead} segment="decidio_no" />
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
