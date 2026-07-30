// cap: lisa.servicios
// story-origin: vitalia-fase2-lisa-servicios T-6
/**
 * CatalogoView.tsx — Catalog grid of ServiceCards + loading/empty/error states.
 *
 * Composes the canon grid (auto-fill minmax 250px) of bespoke ServiceCards.
 * States (React patterns baseline):
 *   - loading  → Skeleton grid
 *   - error    → inline error with retry
 *   - empty    → invites the biblioteca (AC-7): standard-library starter cards +
 *                "Crear servicio personalizado" CTA → routes to /nuevo (T-7)
 *   - data     → grid + a trailing dashed "+ Nuevo servicio" tile
 *
 * The rung + category filters are applied CLIENT-SIDE here because the wire list
 * endpoint only filters by q + is_active (rung/value_level is not on the wire yet,
 * category is a label match) — keeps the UX complete without an imagined contract.
 *
 * Spanish neutro LatAm — sin voseo.
 *
 * T-6 vitalia-fase2-lisa-servicios
 * spec_anchor: 03-arch-fe.md § 5 CatalogoView + mockups/catalogo.html + 01-spec.md AC-7
 * downstream-regression-na: brand-local vitalia FE component; no cross-brand consumers
 */

"use client";

import { useMemo } from "react";
import { useRouter } from "next/navigation";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { Plus, AlertTriangle, BookOpen } from "lucide-react";
import { cn } from "@/lib/cn";
import { ServiceCard } from "./ServiceCard";
import {
  useServicios,
  useActivateServicio,
  useSoftDeleteServicio,
} from "../../api/servicios";
import type {
  ServiceListItem,
  ServiceListResponse,
  ServiciosFilters,
} from "../../types/servicios.types";

const GRID_CLASS =
  "grid grid-cols-[repeat(auto-fill,minmax(250px,1fr))] gap-3.5";

/** Starter examples for the empty-state biblioteca invite (AC-7). */
const BIBLIOTECA_STARTERS = [
  { emoji: "🦷", name: "Diseño de sonrisa", category: "Odontología" },
  { emoji: "💉", name: "Toxina botulínica", category: "Medicina estética" },
  { emoji: "👁️", name: "Cirugía refractiva", category: "Oftalmología" },
] as const;

export interface CatalogoViewProps {
  tenantId: string;
  filters: ServiciosFilters;
  initialData?: ServiceListResponse;
}

/**
 * CatalogoView — the catalogo sub-sub-tab body.
 */
export function CatalogoView({
  tenantId,
  filters,
  initialData,
}: CatalogoViewProps) {
  const router = useRouter();
  const { data, isLoading, isError, refetch } = useServicios({
    filters,
    initialData,
  });
  const activate = useActivateServicio();
  const softDelete = useSoftDeleteServicio();

  // Client-side rung + category narrowing (wire only does q + is_active).
  const items = useMemo<ServiceListItem[]>(() => {
    const all = data?.items ?? [];
    return all.filter((it) => {
      if (filters.rung && it.value_level !== filters.rung) return false;
      if (
        filters.category &&
        (it.category ?? "").toLowerCase() !== filters.category.toLowerCase()
      ) {
        return false;
      }
      return true;
    });
  }, [data?.items, filters.rung, filters.category]);

  if (isLoading) {
    return (
      <div className={GRID_CLASS} data-testid="catalogo-skeleton">
        {Array.from({ length: 6 }).map((_, i) => (
          <Skeleton key={i} className="h-44 w-full rounded-xl" />
        ))}
      </div>
    );
  }

  if (isError) {
    return (
      <section
        className="flex flex-col items-center gap-3 rounded-xl border border-border bg-card p-8 text-center"
        data-testid="catalogo-error"
        role="alert"
      >
        <AlertTriangle className="h-8 w-8 text-destructive" aria-hidden="true" />
        <p className="text-sm font-medium text-foreground">
          No pudimos cargar tus servicios
        </p>
        <Button size="sm" variant="outline" onClick={() => void refetch()}>
          Reintentar
        </Button>
      </section>
    );
  }

  // Empty state — invite the biblioteca (AC-7).
  if (items.length === 0) {
    return (
      <section
        className="flex flex-col items-center gap-4 rounded-xl border border-dashed border-border bg-card p-8 text-center"
        data-testid="catalogo-empty"
      >
        <span
          aria-hidden="true"
          className="flex h-12 w-12 items-center justify-center rounded-full bg-agent-lisa-soft"
        >
          <BookOpen className="h-6 w-6 text-agent-lisa" aria-hidden="true" />
        </span>
        <div className="space-y-1">
          <p className="text-sm font-semibold text-foreground">
            Empieza tu catálogo desde la biblioteca
          </p>
          <p className="text-xs text-muted-foreground">
            Elige un servicio estándar de tu especialidad y ajusta el precio, o
            crea uno desde cero.
          </p>
        </div>

        <div className="flex flex-wrap justify-center gap-2">
          {BIBLIOTECA_STARTERS.map((s) => (
            <button
              key={s.name}
              type="button"
              onClick={() => router.push(`/${tenantId}/lisa/servicios/nuevo`)}
              data-testid={`biblioteca-starter-${s.name}`}
              className="flex items-center gap-2 rounded-lg border border-border bg-background px-3 py-2 text-xs hover:border-agent-lisa"
            >
              <span aria-hidden>{s.emoji}</span>
              <span className="font-medium text-foreground">{s.name}</span>
              <span className="text-muted-foreground">{s.category}</span>
            </button>
          ))}
        </div>

        <Button
          size="sm"
          onClick={() => router.push(`/${tenantId}/lisa/servicios/nuevo`)}
          data-testid="btn-crear-personalizado"
          className="gap-1.5 bg-agent-lisa text-foreground hover:opacity-90"
        >
          <Plus className="h-4 w-4" aria-hidden="true" />
          Crear servicio personalizado
        </Button>
      </section>
    );
  }

  return (
    <div className={GRID_CLASS} data-testid="catalogo-grid">
      {items.map((item) => (
        <ServiceCard
          key={item.offer_id}
          item={item}
          tenantId={tenantId}
          onToggleActive={(offerId, next) =>
            activate.mutate({ offerId, isActive: next })
          }
          onDelete={(offerId) => softDelete.mutate(offerId)}
        />
      ))}

      {/* Trailing "+ Nuevo servicio" dashed tile */}
      <button
        type="button"
        onClick={() => router.push(`/${tenantId}/lisa/servicios/nuevo`)}
        data-testid="catalogo-nuevo-tile"
        aria-label="Nuevo servicio"
        className={cn(
          "flex min-h-44 flex-col items-center justify-center gap-2 rounded-xl border border-dashed border-border bg-card text-muted-foreground",
          "transition-colors hover:border-agent-lisa hover:text-agent-lisa",
        )}
      >
        <Plus className="h-6 w-6" aria-hidden="true" />
        <span className="text-xs font-medium">Nuevo servicio</span>
      </button>
    </div>
  );
}
