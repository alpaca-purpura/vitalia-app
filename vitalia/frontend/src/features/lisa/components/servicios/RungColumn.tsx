// cap: lisa.servicios
// story-origin: vitalia-fase2-lisa-servicios T-6
/**
 * RungColumn.tsx — One fixed rung (peldaño) of the value escalera.
 *
 * Two states (per mockups/escalera.html):
 *   - filled → lad-cards (draggable when personalizado; LOCKED when estandar · RN-30)
 *             + "+ Crear aquí" (routes to /nuevo?rung=…).
 *   - empty  → rung-explain + biblioteca examples + "+ Crear desde la biblioteca".
 *
 * Drop target: the whole column is a @dnd-kit/core droppable (id = rung id). A
 * personalizado service can be dragged INTO it; estandar services are LOCKED to
 * their canonical rung (RN-30) so their lad-card is NOT draggable.
 *
 * Spanish neutro LatAm — sin voseo.
 *
 * T-6 vitalia-fase2-lisa-servicios
 * spec_anchor: 03-arch-fe.md § 5 RungColumn + mockups/escalera.html .rung-col + AC-3/RN-2/RN-30
 * downstream-regression-na: brand-local vitalia FE component; no cross-brand consumers
 */

"use client";

import { useRouter } from "next/navigation";
import { useDraggable, useDroppable } from "@dnd-kit/core";
import { CSS } from "@dnd-kit/utilities";
import { Lock } from "lucide-react";
import { cn } from "@/lib/cn";
import type { RungMeta } from "../../types/servicios-labels";
import type {
  ServiceListItem,
  OfferValueLevel,
} from "../../types/servicios.types";

/** Biblioteca examples shown when a rung is empty (AC-3). Keyed by rung id. */
const RUNG_EXAMPLES: Record<OfferValueLevel, string[]> = {
  lead_magnet: ["Evaluación inicial gratuita", "Primera consulta sin costo"],
  activacion: ["Limpieza dental", "Consulta de valoración"],
  transformacion: ["Diseño de sonrisa", "Implante dental", "Ortodoncia"],
  maximizacion: [
    "Carillas de porcelana",
    "Ortodoncia invisible premium",
    "Rehabilitación oral completa",
  ],
  corporativo: [
    "Plan de mantenimiento anual",
    "Membresía familiar",
    "Convenio con empresa",
  ],
};

function formatPrice(price: number | null, currency: string | null): string {
  if (price == null) return "Sin precio";
  const cur = currency ?? "USD";
  try {
    return new Intl.NumberFormat("es", {
      style: "currency",
      currency: cur,
      maximumFractionDigits: 0,
    }).format(price);
  } catch {
    return `${cur} ${price}`;
  }
}

function isStandard(item: ServiceListItem): boolean {
  return Boolean(item.canonical_service_ref);
}

/** A single draggable lad-card inside a rung. */
function LadCard({
  item,
  tenantId,
}: {
  item: ServiceListItem;
  tenantId: string;
}) {
  const router = useRouter();
  const locked = isStandard(item);
  const { attributes, listeners, setNodeRef, transform, isDragging } =
    useDraggable({
      id: item.offer_id,
      disabled: locked,
      data: { from: item.value_level, locked },
    });

  const style = transform
    ? { transform: CSS.Translate.toString(transform) }
    : undefined;

  return (
    <div
      ref={setNodeRef}
      style={style}
      data-testid={`lad-card-${item.offer_id}`}
      data-locked={locked}
      className={cn(
        "flex items-center justify-between gap-2 rounded-md border border-border bg-card px-2.5 py-2 text-xs",
        "border-l-[3px] border-l-agent-lisa",
        locked ? "cursor-default" : "cursor-grab active:cursor-grabbing",
        isDragging && "opacity-50 shadow-md",
      )}
      {...(locked ? {} : attributes)}
      {...(locked ? {} : listeners)}
    >
      <button
        type="button"
        onClick={() =>
          // G2-F10: from=escalera → workspace back-pill reads "Escalera" + vuelve allí.
          router.push(`/${tenantId}/lisa/servicios/${item.offer_id}/resumen?from=escalera`)
        }
        className="flex min-w-0 items-center gap-1.5 truncate text-left font-medium text-foreground"
      >
        {locked && (
          <Lock
            className="h-3 w-3 shrink-0 text-muted-foreground"
            aria-label="Servicio estándar (peldaño fijo)"
          />
        )}
        <span className="truncate">{item.public_name}</span>
      </button>
      <span className="shrink-0 font-semibold text-muted-foreground">
        {formatPrice(item.price, item.currency)}
      </span>
    </div>
  );
}

export interface RungColumnProps {
  meta: RungMeta;
  items: ServiceListItem[];
  tenantId: string;
}

/**
 * RungColumn — one peldaño with its services or an empty-state invite.
 * Whole column is a droppable; id = rung id.
 */
export function RungColumn({ meta, items, tenantId }: RungColumnProps) {
  const router = useRouter();
  const { setNodeRef, isOver } = useDroppable({ id: meta.id });
  const isEmpty = items.length === 0;
  const goNuevo = () =>
    router.push(`/${tenantId}/lisa/servicios/nuevo?rung=${meta.id}`);

  return (
    <section
      ref={setNodeRef}
      aria-label={`Peldaño ${meta.label}`}
      data-testid={`rung-col-${meta.id}`}
      data-empty={isEmpty}
      data-over={isOver}
      className={cn(
        "flex flex-col gap-2 rounded-xl border border-border bg-card p-3",
        meta.layout === "full" && "w-full",
        isOver && "border-agent-lisa ring-1 ring-agent-lisa",
      )}
    >
      {/* Head: número + badge médico + explain */}
      <div className="space-y-1">
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            {meta.numero}
          </span>
          <span
            className={cn(
              "rounded-full px-2 py-0.5 text-xs font-medium",
              meta.badgeClass,
            )}
          >
            {meta.label}
          </span>
        </div>
        <p className="text-xs text-muted-foreground">{meta.explain}</p>
      </div>

      {/* Body */}
      {isEmpty ? (
        <div className="space-y-2">
          <div
            className="rounded-lg border border-dashed border-border bg-muted/40 p-2.5 text-xs text-muted-foreground"
            data-testid={`rung-empty-hint-${meta.id}`}
          >
            <p className="mb-1">
              Aún no tienes un servicio en este peldaño. En la{" "}
              <strong>biblioteca estándar</strong> puedes encontrar:
            </p>
            <ul className="list-disc space-y-0.5 pl-4">
              {RUNG_EXAMPLES[meta.id].map((ex) => (
                <li key={ex}>{ex}</li>
              ))}
            </ul>
          </div>
          <button
            type="button"
            onClick={goNuevo}
            data-testid={`rung-create-${meta.id}`}
            className="w-full rounded-md border border-dashed border-border py-1.5 text-xs font-medium text-agent-lisa hover:border-agent-lisa"
          >
            + Crear desde la biblioteca
          </button>
        </div>
      ) : (
        <div className="space-y-2">
          {items.map((item) => (
            <LadCard key={item.offer_id} item={item} tenantId={tenantId} />
          ))}
          <button
            type="button"
            onClick={goNuevo}
            data-testid={`rung-create-${meta.id}`}
            className="w-full rounded-md border border-dashed border-border py-1.5 text-xs font-medium text-muted-foreground hover:border-agent-lisa hover:text-agent-lisa"
          >
            + Crear aquí
          </button>
        </div>
      )}
    </section>
  );
}
