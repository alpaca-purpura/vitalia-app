// cap: lisa.servicios
// story-origin: vitalia-fase2-lisa-servicios T-6
/**
 * EscaleraView.tsx — The value-ladder (escalera) view: 5 FIXED medical rungs.
 *
 * Layout (mockups/escalera.html):
 *   - rung 1 (lead_magnet · "Gancho gratuito")  → full-width on top
 *   - rungs 2-3-4 (activacion/transformacion/maximizacion) → 3-column band
 *   - rung 5 (corporativo · "Plan / convenio")   → full-width at bottom
 *
 * Items come from useEscalera (page_size=200, no pagination) grouped client-side
 * by value_level. Drag a PERSONALIZADO service from one rung to another →
 * useMoveRung (DEGRADED no-op + optimistic cache + toast until BE wires
 * value_level — RN-30 + Upstream deficiency in T-6-impl-log). ESTANDAR services
 * are LOCKED to their canonical rung (the draggable is disabled in RungColumn).
 *
 * @dnd-kit/core: DndContext + PointerSensor + KeyboardSensor (default
 * coordinateGetter — escalera is a MOVE between droppables, not a sortable
 * reorder, so @dnd-kit/sortable is not needed).
 *
 * Spanish neutro LatAm — sin voseo.
 *
 * T-6 vitalia-fase2-lisa-servicios
 * spec_anchor: 03-arch-fe.md § 5 EscaleraView + mockups/escalera.html + AC-3/RN-2/RN-30
 * downstream-regression-na: brand-local vitalia FE component; no cross-brand consumers
 */

"use client";

import { useMemo } from "react";
import {
  DndContext,
  PointerSensor,
  KeyboardSensor,
  useSensor,
  useSensors,
  type DragEndEvent,
} from "@dnd-kit/core";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { AlertTriangle } from "lucide-react";
import { RungColumn } from "./RungColumn";
import { useEscalera, useMoveRung } from "../../api/servicios";
import { RUNG_META } from "../../types/servicios-labels";
import type {
  ServiceListItem,
  ServiceListResponse,
  OfferValueLevel,
} from "../../types/servicios.types";

/** The single rung an item belongs to (fallback transformacion = the spine). */
function rungOf(item: ServiceListItem): OfferValueLevel {
  return item.value_level ?? "transformacion";
}

export interface EscaleraViewProps {
  tenantId: string;
  initialData?: ServiceListResponse;
}

/**
 * EscaleraView — the escalera sub-sub-tab body.
 */
export function EscaleraView({ tenantId, initialData }: EscaleraViewProps) {
  const { data, isLoading, isError, refetch } = useEscalera({ initialData });
  const moveRung = useMoveRung();

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: { distance: 6 },
    }),
    useSensor(KeyboardSensor),
  );

  // Group items by rung.
  const byRung = useMemo(() => {
    const groups: Record<OfferValueLevel, ServiceListItem[]> = {
      lead_magnet: [],
      activacion: [],
      transformacion: [],
      maximizacion: [],
      corporativo: [],
    };
    for (const it of data?.items ?? []) {
      groups[rungOf(it)].push(it);
    }
    return groups;
  }, [data?.items]);

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    if (!over) return;
    const toRung = over.id as OfferValueLevel;
    const fromRung = active.data.current?.from as OfferValueLevel | undefined;
    const locked = Boolean(active.data.current?.locked);
    // RN-30: estandar services are locked (draggable disabled), but guard anyway.
    if (locked || fromRung === toRung) return;
    moveRung.mutate({ offerId: String(active.id), toRung });
  };

  if (isLoading) {
    return (
      <div className="space-y-3" data-testid="escalera-skeleton">
        <Skeleton className="h-24 w-full rounded-xl" />
        <section className="grid grid-cols-1 gap-3 md:grid-cols-3">
          <Skeleton className="h-40 w-full rounded-xl" />
          <Skeleton className="h-40 w-full rounded-xl" />
          <Skeleton className="h-40 w-full rounded-xl" />
        </section>
        <Skeleton className="h-24 w-full rounded-xl" />
      </div>
    );
  }

  if (isError) {
    return (
      <section
        className="flex flex-col items-center gap-3 rounded-xl border border-border bg-card p-8 text-center"
        data-testid="escalera-error"
        role="alert"
      >
        <AlertTriangle className="h-8 w-8 text-destructive" aria-hidden="true" />
        <p className="text-sm font-medium text-foreground">
          No pudimos cargar tu escalera de valor
        </p>
        <Button size="sm" variant="outline" onClick={() => void refetch()}>
          Reintentar
        </Button>
      </section>
    );
  }

  const [rung1, rung2, rung3, rung4, rung5] = RUNG_META;

  return (
    <div className="space-y-3" data-testid="escalera-grid">
      <p className="text-xs text-muted-foreground">
        Tus servicios ordenados por su rol en el recorrido del paciente: del
        primer contacto gratis al tratamiento de mayor valor. Arrastra un
        servicio personalizado para cambiarlo de peldaño.
      </p>

      <DndContext sensors={sensors} onDragEnd={handleDragEnd}>
        {/* Rung 1 — full width */}
        <RungColumn meta={rung1} items={byRung[rung1.id]} tenantId={tenantId} />

        {/* Rungs 2-3-4 — 3-column band */}
        <section className="grid grid-cols-1 gap-3 md:grid-cols-3">
          <RungColumn
            meta={rung2}
            items={byRung[rung2.id]}
            tenantId={tenantId}
          />
          <RungColumn
            meta={rung3}
            items={byRung[rung3.id]}
            tenantId={tenantId}
          />
          <RungColumn
            meta={rung4}
            items={byRung[rung4.id]}
            tenantId={tenantId}
          />
        </section>

        {/* Rung 5 — full width */}
        <RungColumn meta={rung5} items={byRung[rung5.id]} tenantId={tenantId} />
      </DndContext>

      <p className="mt-1 rounded-lg bg-muted/40 px-3 py-2 text-xs text-muted-foreground">
        💡 No tienes que llenar todos los peldaños. Pero un recorrido completo
        (gancho → primera visita → tratamiento → premium → plan) hace que Adrián
        tenga siempre algo para ofrecer en cada momento de la conversación.
      </p>
    </div>
  );
}
