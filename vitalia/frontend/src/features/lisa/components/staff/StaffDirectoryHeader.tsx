// cap: clinics.lisa.doctores
// story-origin: vitalia-fase2-lisa-doctores
/**
 * StaffDirectoryHeader.tsx — Directory header with + Nuevo integrante + search + filters.
 *
 * Client Component — needs onClick + onChange handlers.
 * Reuses Shadcn Input, Select, Button from components/ui/.
 *
 * Microcopy per 01-spec.md § Microcopy (authoritative).
 * Spanish neutro LatAm — sin voseo.
 *
 * T-FE-1 vitalia-fase2-lisa-doctores
 * spec_anchor: 01-spec.md § Wireframes Directorio + § Microcopy
 * downstream-regression-na: brand-local vitalia FE component; no cross-brand consumers
 */

"use client";

import { type RefObject } from "react";
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
import type { StaffFilters } from "../../types/staff.types";

const SPECIALTY_OPTIONS = [
  "Odontología",
  "Medicina estética",
  "Oftalmología",
  "Psicología",
  "Psiquiatría",
  "Dermatología",
  "Nutrición",
  "Fisioterapia",
  "Otra",
] as const;

interface StaffDirectoryHeaderProps {
  filters: StaffFilters;
  onQ: (q: string) => void;
  onSpecialty: (specialty: string) => void;
  onActive: (active: "true" | "false" | "") => void;
  onAddNew: () => void;
  /** Ref forwarded to the "+ Nuevo integrante" button for focus-return (WCAG 2.4.3). */
  addNewRef?: RefObject<HTMLButtonElement | null>;
}

/**
 * StaffDirectoryHeader — page title + "+ Nuevo integrante" + search + filters.
 */
export function StaffDirectoryHeader({
  filters,
  onQ,
  onSpecialty,
  onActive,
  onAddNew,
  addNewRef,
}: StaffDirectoryHeaderProps) {
  return (
    <div className="space-y-3">
      {/* Title row */}
      <div className="flex items-center justify-between gap-3">
        <div>
          <h1 className="text-lg font-semibold text-foreground">Staff</h1>
          <p className="text-xs text-muted-foreground">
            Equipo de la clínica · perfiles, horarios y servicios
          </p>
        </div>
        <Button
          ref={addNewRef}
          onClick={onAddNew}
          size="sm"
          data-testid="btn-nuevo-integrante"
          className="shrink-0 gap-1.5 bg-agent-lisa text-foreground hover:opacity-90"
        >
          <Plus className="h-4 w-4" aria-hidden="true" />
          <span className="hidden sm:inline">Nuevo integrante</span>
          <span className="sm:hidden">Nuevo</span>
        </Button>
      </div>

      {/* Search + filters row */}
      <div className="flex flex-wrap items-center gap-2">
        {/* Search */}
        <div className="relative flex-1 min-w-48">
          <Search
            className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground pointer-events-none"
            aria-hidden="true"
          />
          <Input
            className="pl-8 text-sm"
            placeholder="Buscar integrante…"
            value={filters.q ?? ""}
            onChange={(e) => onQ(e.target.value)}
            aria-label="Buscar integrante"
            data-testid="input-buscar"
          />
        </div>

        {/* Specialty filter */}
        <Select
          value={filters.specialty ?? ""}
          onValueChange={(v) => onSpecialty(v === "__all__" ? "" : v)}
        >
          <SelectTrigger
            className="w-40 text-sm"
            aria-label="Filtrar por especialidad"
            data-testid="select-especialidad"
          >
            <SelectValue placeholder="Especialidad" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="__all__">Todas</SelectItem>
            {SPECIALTY_OPTIONS.map((s) => (
              <SelectItem key={s} value={s}>
                {s}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        {/* Active filter */}
        <Select
          value={filters.active ?? ""}
          onValueChange={(v) =>
            onActive(v === "__all__" ? "" : (v as "true" | "false"))
          }
        >
          <SelectTrigger
            className="w-32 text-sm"
            aria-label="Filtrar por estado activo"
            data-testid="select-activo"
          >
            <SelectValue placeholder="Estado" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="__all__">Todos</SelectItem>
            <SelectItem value="true">Activos</SelectItem>
            <SelectItem value="false">Inactivos</SelectItem>
          </SelectContent>
        </Select>
      </div>
    </div>
  );
}
