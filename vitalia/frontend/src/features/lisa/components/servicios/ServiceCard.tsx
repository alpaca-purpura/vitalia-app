// cap: lisa.servicios
// story-origin: vitalia-fase2-lisa-servicios T-6
/**
 * ServiceCard.tsx — Catalog card for a single offer/service.
 *
 * ★ CANON DIVERGENCE (documented in T-6-impl-log.md § Canon divergences):
 *   The design-system canon recommends `EntityInfoCard` (Opción B) for grids, but
 *   EntityInfoCard's `status` slot is a single Badge chip (EntityStatus = {label,
 *   variant}). This card's footer needs THREE composed controls — a ChipOrigen
 *   (estandar/personalizado), the price/duration metrics row, and an interactive
 *   "Activo" toggle — which EntityInfoCard cannot host. So ServiceCard is a bespoke
 *   `<article>` composing the SAME @/components/ui atoms (Badge, Button, DropdownMenu)
 *   + the shipped ChipOrigen molecule, EXACTLY like the shipped StaffCard precedent
 *   (same `border` + `top-0 h-1 bg-agent-lisa` accent, same `cn` from "@/lib/cn").
 *   No primitive is reinvented; only the composition is bespoke.
 *
 * Footer (Round-3 simplified, matches mockups/catalogo.html .eic-foot): NO rung
 * badge; avatar-stack (specialists, optional) + ChipOrigen + "Activo" toggle.
 * Metrics row = price (+ "💳 N cuotas" chip when financed). Head = emoji media +
 * kebab ⋮ (DropdownMenu — edit/delete). Clicking the card body navigates to the
 * workspace (T-7 route); the kebab + toggle stopPropagation.
 *
 * Spanish neutro LatAm — sin voseo.
 *
 * T-6 vitalia-fase2-lisa-servicios
 * spec_anchor: 03-arch-fe.md § 5 ServiceCard + mockups/catalogo.html + 01-spec.md AC-1/AC-10
 * downstream-regression-na: brand-local vitalia FE component; no cross-brand consumers
 */

"use client";

import { useRouter } from "next/navigation";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { MoreVertical, Pencil, Trash2 } from "lucide-react";
import { cn } from "@/lib/cn";
import { ChipOrigen } from "./ChipOrigen";
import { MODALITY_LABEL } from "../../types/servicios-labels";
import type { ServiceListItem } from "../../types/servicios.types";

const CATEGORY_EMOJI: Record<string, string> = {
  odontologia: "🦷",
  "medicina estetica": "💉",
  oftalmologia: "👁️",
  psicologia: "🧠",
  dermatologia: "🧴",
  nutricion: "🥗",
  fisioterapia: "💪",
};

function categoryEmoji(category: string | null): string {
  if (!category) return "🩺";
  return CATEGORY_EMOJI[category.toLowerCase()] ?? "🩺";
}

/** Origen derived FE-side from the presence of a canonical_service_ref (RN-30). */
function deriveOrigen(item: ServiceListItem): "estandar" | "personalizado" {
  return item.canonical_service_ref ? "estandar" : "personalizado";
}

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

export interface ServiceCardProps {
  item: ServiceListItem;
  tenantId: string;
  /** Toggle is_active (catalog Switch). */
  onToggleActive: (offerId: string, next: boolean) => void;
  /** Soft-delete (kebab ⋮). */
  onDelete: (offerId: string) => void;
  /** Optional: number of installments shown as a "💳 N cuotas" chip. */
  installments?: number | null;
}

/**
 * ServiceCard — one offer in the catalog grid.
 * data-testid="service-card-{offer_id}" for selectors.
 */
export function ServiceCard({
  item,
  tenantId,
  onToggleActive,
  onDelete,
  installments,
}: ServiceCardProps) {
  const router = useRouter();
  const origen = deriveOrigen(item);
  // G2-F10: go straight to /resumen?from=catalogo so the origin survives (the bare
  // edge-redirect would strip the query) → the workspace back-pill reads "Catálogo".
  const workspaceHref = `/${tenantId}/lisa/servicios/${item.offer_id}/resumen?from=catalogo`;
  const isDraft = item.status === "draft";

  const goWorkspace = () => router.push(workspaceHref);

  return (
    <article
      className={cn(
        "group relative flex flex-col gap-3 overflow-hidden rounded-xl border border-border bg-card p-4 pt-5",
        "cursor-pointer transition-all hover:border-agent-lisa hover:shadow-md",
        !item.is_active && "opacity-60",
      )}
      data-testid={`service-card-${item.offer_id}`}
      data-origen={origen}
      role="button"
      tabIndex={0}
      aria-label={`Servicio ${item.public_name}`}
      onClick={goWorkspace}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          goWorkspace();
        }
      }}
    >
      {/* Lisa accent bar */}
      <span
        aria-hidden="true"
        className="absolute inset-x-0 top-0 h-1 bg-agent-lisa"
      />

      {/* Head: emoji media + kebab */}
      <div className="flex items-start justify-between gap-2">
        <span
          aria-hidden="true"
          className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-agent-lisa-soft text-xl"
        >
          {categoryEmoji(item.category)}
        </span>

        <DropdownMenu>
          <DropdownMenuTrigger
            asChild
            onClick={(e) => e.stopPropagation()}
          >
            <button
              type="button"
              aria-label={`Acciones de ${item.public_name}`}
              data-testid={`service-card-kebab-${item.offer_id}`}
              className="rounded-md p-1 text-muted-foreground hover:bg-muted hover:text-foreground"
            >
              <MoreVertical className="h-4 w-4" aria-hidden="true" />
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent
            align="end"
            onClick={(e) => e.stopPropagation()}
          >
            <DropdownMenuItem onSelect={goWorkspace}>
              <Pencil className="mr-2 h-4 w-4" aria-hidden="true" />
              Editar
            </DropdownMenuItem>
            <DropdownMenuItem
              onSelect={() => onDelete(item.offer_id)}
              className="text-destructive focus:text-destructive"
              data-testid={`service-card-delete-${item.offer_id}`}
            >
              <Trash2 className="mr-2 h-4 w-4" aria-hidden="true" />
              Eliminar
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      {/* Title + hint (category · duration) */}
      <div className="space-y-1">
        <p className="truncate text-sm font-semibold text-foreground">
          {item.public_name}
        </p>
        <p className="truncate text-xs text-muted-foreground">
          {[item.category, MODALITY_LABEL[item.modality]]
            .filter(Boolean)
            .join(" · ")}
        </p>
      </div>

      {/* Metrics: price (+ cuotas chip) */}
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-sm font-semibold text-foreground">
          {formatPrice(item.price, item.currency)}
        </span>
        {installments != null && installments > 1 && (
          <span className="inline-flex items-center gap-1 rounded-full bg-muted px-2 py-0.5 text-xs text-muted-foreground">
            <span aria-hidden>💳</span>
            {installments} cuotas
          </span>
        )}
      </div>

      {/* Footer: chip-origen + Activo toggle */}
      <div className="mt-auto flex items-center justify-between gap-2 border-t border-border pt-2">
        <ChipOrigen
          origen={origen}
          standardName={origen === "estandar" ? item.public_name : undefined}
        />

        {/* "Activo" toggle — bespoke role=switch button (no Switch atom in
            components/ui/; canon allows composed atoms per StaffCard precedent). */}
        <button
          type="button"
          role="switch"
          aria-checked={item.is_active}
          aria-label={item.is_active ? "Desactivar servicio" : "Activar servicio"}
          data-testid={`service-card-toggle-${item.offer_id}`}
          onClick={(e) => {
            e.stopPropagation();
            onToggleActive(item.offer_id, !item.is_active);
          }}
          className="flex items-center gap-1.5 text-xs font-medium text-muted-foreground"
        >
          <span
            aria-hidden="true"
            className={cn(
              "relative inline-flex h-4 w-7 items-center rounded-full transition-colors",
              item.is_active ? "bg-agent-lisa" : "bg-muted",
            )}
          >
            <span
              className={cn(
                "inline-block h-3 w-3 transform rounded-full bg-card transition-transform",
                item.is_active ? "translate-x-3.5" : "translate-x-0.5",
              )}
            />
          </span>
          {isDraft ? "Activo (borrador)" : "Activo"}
        </button>
      </div>
    </article>
  );
}
