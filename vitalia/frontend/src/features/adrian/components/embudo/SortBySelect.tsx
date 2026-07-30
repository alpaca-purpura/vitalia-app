// cap: crm.adrian-embudo
// story-origin: vitalia-fase2-adrian-embudo
/**
 * SortBySelect — Sort order selector for the Embudo board (RN-17).
 * T-FE-2 vitalia-fase2-adrian-embudo
 *
 * Options: antigüedad en etapa (default) · score · valor · última actividad.
 * Spanish neutro labels (sin voseo).
 * Reuses Shadcn Select from components/ui/.
 *
 * spec_anchor: 01-spec.md § RN-17
 */
"use client";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { BoardFilters } from "../../types/embudo.types";

const SORT_OPTIONS: { value: NonNullable<BoardFilters["sort"]>; label: string }[] = [
  { value: "stage_age_desc", label: "Antigüedad en etapa" },
  { value: "score_desc", label: "Score" },
  { value: "value_desc", label: "Valor" },
  { value: "last_activity_desc", label: "Última actividad" },
];

export interface SortBySelectProps {
  value: NonNullable<BoardFilters["sort"]>;
  onChange: (value: NonNullable<BoardFilters["sort"]>) => void;
}

export function SortBySelect({ value, onChange }: SortBySelectProps) {
  return (
    <Select value={value} onValueChange={onChange}>
      <SelectTrigger
        className="h-8 w-[180px] text-xs"
        aria-label="Ordenar leads por"
        data-testid="sort-by-select"
      >
        <SelectValue placeholder="Ordenar por" />
      </SelectTrigger>
      <SelectContent>
        {SORT_OPTIONS.map((opt) => (
          <SelectItem key={opt.value} value={opt.value} className="text-xs">
            {opt.label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
