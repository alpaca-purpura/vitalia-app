// cap: lisa.servicios
// story-origin: vitalia-fase2-lisa-servicios T-6
/**
 * ServiciosDirectoryHeader.tsx — Catalog header: search + filters + "+ Nuevo servicio".
 *
 * Client Component (onClick/onChange). Reuses Shadcn Input, Select, Button from
 * components/ui/ (canon Select — NEVER native <select>). Mirrors the shipped
 * StaffDirectoryHeader pattern.
 *
 * Filters: especialidad (category) · peldaño (rung) · estado (active). The rung
 * filter is FE-side (no-op on the wire until the BE exposes value_level — see
 * servicios.types.ts GAP note), but the control ships so the escalera/catalog UX
 * is complete.
 *
 * "+ Nuevo servicio" navigates to the create route (T-7 owns the form); here it
 * only routes — per the T-6 scope ("'+ Nuevo' only navigates").
 *
 * Spanish neutro LatAm — sin voseo.
 *
 * T-6 vitalia-fase2-lisa-servicios
 * spec_anchor: 03-arch-fe.md § 5 ServiciosDirectoryHeader + mockups/catalogo.html search-row
 * downstream-regression-na: brand-local vitalia FE component; no cross-brand consumers
 */

"use client";

import { useRouter } from "next/navigation";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Search, Plus } from "lucide-react";
import { RUNG_META } from "../../types/servicios-labels";
import type {
  ServiciosFilters,
  OfferValueLevel,
} from "../../types/servicios.types";

const CATEGORY_OPTIONS = [
  "Odontología",
  "Medicina estética",
  "Oftalmología",
  "Psicología",
  "Dermatología",
  "Nutrición",
  "Fisioterapia",
  "Otra",
] as const;

const ALL = "__all__";

export interface ServiciosDirectoryHeaderProps {
  filters: ServiciosFilters;
  tenantId: string;
  onSearch: (q: string) => void;
  onCategory: (category: string | null) => void;
  onRung: (rung: OfferValueLevel | null) => void;
  onActive: (active: ServiciosFilters["active"]) => void;
}

/**
 * ServiciosDirectoryHeader — title + "+ Nuevo servicio" + search + 3 filters.
 */
export function ServiciosDirectoryHeader({
  filters,
  tenantId,
  onSearch,
  onCategory,
  onRung,
  onActive,
}: ServiciosDirectoryHeaderProps) {
  const router = useRouter();
  const goNuevo = () => router.push(`/${tenantId}/lisa/servicios/nuevo`);

  return (
    <div className="space-y-3">
      {/* Title row */}
      <div className="flex items-center justify-between gap-3">
        <div>
          <h1 className="text-lg font-semibold text-foreground">Servicios</h1>
          <p className="text-xs text-muted-foreground">
            Catálogo de la clínica · precios, modalidad y escalera de valor
          </p>
        </div>
        <Button
          onClick={goNuevo}
          size="sm"
          data-testid="btn-nuevo-servicio"
          className="shrink-0 gap-1.5 bg-agent-lisa text-foreground hover:opacity-90"
        >
          <Plus className="h-4 w-4" aria-hidden="true" />
          <span className="hidden sm:inline">Nuevo servicio</span>
          <span className="sm:hidden">Nuevo</span>
        </Button>
      </div>

      {/* Search + filters row */}
      <div className="flex flex-wrap items-center gap-2">
        {/* Search */}
        <div className="relative min-w-48 flex-1">
          <Search
            className="pointer-events-none absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground"
            aria-hidden="true"
          />
          <Input
            className="pl-8 text-sm"
            placeholder="Buscar servicio…"
            value={filters.search}
            onChange={(e) => onSearch(e.target.value)}
            aria-label="Buscar servicio"
            data-testid="input-buscar-servicio"
          />
        </div>

        {/* Especialidad / category filter */}
        <Select
          value={filters.category ?? ALL}
          onValueChange={(v) => onCategory(v === ALL ? null : v)}
        >
          <SelectTrigger
            className="w-40 text-sm"
            aria-label="Filtrar por especialidad"
            data-testid="select-especialidad-servicio"
          >
            <SelectValue placeholder="Especialidad" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={ALL}>Todas</SelectItem>
            {CATEGORY_OPTIONS.map((c) => (
              <SelectItem key={c} value={c}>
                {c}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        {/* Peldaño / rung filter */}
        <Select
          value={filters.rung ?? ALL}
          onValueChange={(v) =>
            onRung(v === ALL ? null : (v as OfferValueLevel))
          }
        >
          <SelectTrigger
            className="w-44 text-sm"
            aria-label="Filtrar por peldaño"
            data-testid="select-peldano"
          >
            <SelectValue placeholder="Peldaño" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={ALL}>Todos los peldaños</SelectItem>
            {RUNG_META.map((r) => (
              <SelectItem key={r.id} value={r.id}>
                {r.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        {/* Estado / active filter */}
        <Select
          value={filters.active}
          onValueChange={(v) => onActive(v as ServiciosFilters["active"])}
        >
          <SelectTrigger
            className="w-32 text-sm"
            aria-label="Filtrar por estado"
            data-testid="select-estado-servicio"
          >
            <SelectValue placeholder="Estado" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Todos</SelectItem>
            <SelectItem value="active">Activos</SelectItem>
            <SelectItem value="inactive">Inactivos</SelectItem>
          </SelectContent>
        </Select>
      </div>
    </div>
  );
}
