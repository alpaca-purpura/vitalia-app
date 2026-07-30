// cap: crm.adrian-embudo
// story-origin: vitalia-fase2-adrian-embudo
/**
 * EmbudoHeader — Board header: title + chip + toggle + sort + CTA (D.2 spec).
 * T-FE-2 vitalia-fase2-adrian-embudo
 *
 * spec_anchor: 01-spec.md § V1 Header + D.2
 */
"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { SortBySelect } from "./SortBySelect";
import type { BoardFilters } from "../../types/embudo.types";

const VIEW_OPTIONS = [
  { value: "kanban", label: "Kanban" },
  { value: "lista", label: "Lista" },
] as const;

const OPERATOR_OPTIONS = [
  { value: "agent", label: "Adrián" },
  { value: "todos", label: "Todos" },
] as const;

export interface EmbudoHeaderProps {
  tenantId: string;
  view: "kanban" | "lista";
  sort: NonNullable<BoardFilters["sort"]>;
  operatorFilter: "agent" | "todos";
  onViewChange: (view: "kanban" | "lista") => void;
  onSortChange: (sort: NonNullable<BoardFilters["sort"]>) => void;
  onOperatorFilterChange: (v: "agent" | "todos") => void;
}

export function EmbudoHeader({
  tenantId,
  view,
  sort,
  operatorFilter,
  onViewChange,
  onSortChange,
  onOperatorFilterChange,
}: EmbudoHeaderProps) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-border/60" data-testid="embudo-header">
      {/* Left: title + chip */}
      <div className="flex items-center gap-2">
        <h1 className="text-xl font-semibold text-foreground">Embudo</h1>
        <span
          className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-[hsl(var(--agent-adrian-soft))] text-[hsl(var(--agent-adrian))]"
          aria-label="Adrián opera este embudo"
        >
          🤖 operado por Adrián
        </span>
      </div>

      {/* Right: controls */}
      <div className="flex flex-wrap items-center gap-2">
        {/* Modo Adrián|Todos */}
        <Tabs
          value={operatorFilter}
          onValueChange={(v) => onOperatorFilterChange(v as "agent" | "todos")}
        >
          <TabsList className="h-8">
            {OPERATOR_OPTIONS.map((opt) => (
              <TabsTrigger key={opt.value} value={opt.value} className="text-xs px-3 h-6">
                {opt.label}
              </TabsTrigger>
            ))}
          </TabsList>
        </Tabs>

        {/* Sort selector */}
        <SortBySelect value={sort} onChange={onSortChange} />

        {/* Kanban|Lista toggle */}
        <Tabs
          value={view}
          onValueChange={(v) => onViewChange(v as "kanban" | "lista")}
        >
          <TabsList className="h-8">
            {VIEW_OPTIONS.map((opt) => (
              <TabsTrigger key={opt.value} value={opt.value} className="text-xs px-3 h-6" data-testid={`view-${opt.value}`}>
                {opt.label}
              </TabsTrigger>
            ))}
          </TabsList>
        </Tabs>

        {/* + Nuevo lead */}
        <Button
          asChild
          size="sm"
          className="h-8 gap-1 text-xs"
          aria-label="Crear nuevo lead"
          data-testid="nuevo-lead-button"
        >
          <Link href={`/${tenantId}/adrian/embudo/nuevo`}>
            <span aria-hidden>+</span>
            Nuevo lead
          </Link>
        </Button>
      </div>
    </div>
  );
}
