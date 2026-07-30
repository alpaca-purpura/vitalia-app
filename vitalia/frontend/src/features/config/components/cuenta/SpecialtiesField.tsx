// cap: configuracion.cuenta
// story-origin: vitalia-fase2-config-cuenta
"use client";
/**
 * SpecialtiesField.tsx — Multi-select specialty chips using @luana/ui-kit Select.
 *
 * Renders specialties as togglable chips (add/remove).
 * Uses Select (Shadcn-style, ui-kit) for adding new items from catalog.
 * NO native <select> (arch test enforces this).
 *
 * T-1 vitalia-fase2-config-cuenta
 * spec_anchor: 03-arch.md § 10 (SpecialtiesField) + mockups/cuenta.html
 * downstream-regression-na: brand-local vitalia FE component; no cross-brand consumers
 */

import { useCallback } from "react";
import { cn } from "@/lib/utils";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { X } from "lucide-react";
import type { SpecialtyEntryDTO } from "../../types/cuenta.types";

export interface SpecialtiesFieldProps {
  /** Currently selected specialty IDs (catalog entry slugs — lo que persiste config_json) */
  value: string[];
  /** Catalog entries for the tenant's country ({id, name, tier}) */
  catalog: SpecialtyEntryDTO[];
  /** Called when specialty IDs change */
  onChange: (next: string[]) => void;
  /** Whether the field is in a loading state */
  isLoading?: boolean;
  className?: string;
}

/**
 * SpecialtiesField — multi-select chips for primary specialties.
 * Uses Select from @luana/ui-kit (via components/ui/select).
 * NO native <select> element.
 */
export function SpecialtiesField({
  value,
  catalog,
  onChange,
  isLoading = false,
  className,
}: SpecialtiesFieldProps) {
  const handleAdd = useCallback(
    (specialty: string) => {
      if (!value.includes(specialty)) {
        onChange([...value, specialty]);
      }
    },
    [value, onChange],
  );

  const handleRemove = useCallback(
    (specialty: string) => {
      onChange(value.filter((s) => s !== specialty));
    },
    [value, onChange],
  );

  // id → display name (chips muestran name; persiste id)
  const nameById = new Map(catalog.map((e) => [e.id, e.name]));

  // Available options = catalog entries not yet selected
  const available = catalog.filter((e) => !value.includes(e.id));

  return (
    <div
      className={cn("flex flex-col gap-2", className)}
      data-testid="specialties-field"
    >
      {/* Selected chips */}
      {value.length > 0 && (
        <div
          className="flex flex-wrap gap-1.5"
          aria-label="Especialidades seleccionadas"
        >
          {value.map((specialty) => (
            <Badge
              key={specialty}
              variant="secondary"
              className="flex items-center gap-1 pr-1"
            >
              <span>{nameById.get(specialty) ?? specialty}</span>
              <button
                type="button"
                aria-label={`Quitar ${nameById.get(specialty) ?? specialty}`}
                className={cn(
                  "ml-0.5 rounded-sm p-0.5 transition-colors",
                  "hover:bg-muted focus-visible:ring-1 focus-visible:ring-ring",
                )}
                onClick={() => handleRemove(specialty)}
                disabled={isLoading}
              >
                <X className="h-3 w-3" aria-hidden="true" />
              </button>
            </Badge>
          ))}
        </div>
      )}

      {/* Add from catalog */}
      {available.length > 0 && (
        <Select
          onValueChange={handleAdd}
          disabled={isLoading}
          value=""
        >
          <SelectTrigger
            className="w-full sm:w-[280px]"
            aria-label="Agregar especialidad"
          >
            <SelectValue placeholder="Agregar especialidad..." />
          </SelectTrigger>
          <SelectContent>
            {available.map((entry) => (
              <SelectItem key={entry.id} value={entry.id}>
                {entry.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      )}

      {/* Empty state */}
      {value.length === 0 && available.length === 0 && (
        <p className="text-sm text-muted-foreground">
          No hay especialidades disponibles para tu país.
        </p>
      )}
    </div>
  );
}

SpecialtiesField.displayName = "SpecialtiesField";
