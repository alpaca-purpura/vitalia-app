// cap: sales_agent.adrian-3-tools-mvp
// story-origin: vitalia-fase1-s10-TBD
/**
 * EmbudoPlaceholder — Kanban 6 columnas Pipeline + toggle Kanban|Lista.
 * F1-S10 vitalia-fase1-empty-states — T-4
 *
 * Mockup parity: adrian-embudo-placeholder.html (ratificado Chris batch 2 · 2026-05-26)
 *
 * Client Component — usa TogglePill (Radix Tabs, internal state).
 * Named export (NO default) per FSD-Lite enforce.
 * No hex colors — Tailwind semantic tokens only.
 * Mock data top-of-file — ficticios LatAm (PEN S/).
 * PHI masking: no datos reales (arch test test_no_phi_real_data.test.ts).
 *
 * Horizontal scroll en viewport <1280px via overflow-x-auto wrapper.
 *
 * F2 anchor: columnas y lead-cards reemplazadas por query real adrián embudo API.
 *   Shape documentado: features/adrian/types.ts (leads, pipeline stages).
 *
 * spec_anchor: 03-arch.md § 3.4 + 06-tickets.yaml T-4
 * downstream-regression-na: brand-local placeholder; no cross-brand consumers
 */

"use client";

import {
  TogglePill,
  TogglePillContent,
  type TogglePillItem,
} from "@/components/shared/shell-organism/TogglePill";
import { EmptyState } from "@/components/shared/shell-organism/EmptyState";
import { cn } from "@/lib/utils";

// ── Mock data (ficticios LatAm — PEN currency · NO PHI real) ───────────────

interface LeadCard {
  name: string;
  detail: string;
}

interface KanbanColumn {
  emoji: string;
  label: string;
  count: number;
  value: string;
  leads: LeadCard[];
}

/** Mock pipeline data verbatim from spec § 5 + mockup SSoT */
const MOCK_PIPELINE: KanbanColumn[] = [
  {
    emoji: "⚪",
    label: "Interesado",
    count: 12,
    value: "S/ 84k",
    leads: [
      { name: "María G.", detail: "S/ 7k · WhatsApp · hace 2 días" },
      { name: "Carlos P.", detail: "S/ 4k · Web · hace 4 días" },
      { name: "Sofía R.", detail: "S/ 12k · Meta · hace 1 sem" },
    ],
  },
  {
    emoji: "🟢",
    label: "Calificando",
    count: 8,
    value: "S/ 62k",
    leads: [
      { name: "Ana V.", detail: "S/ 8k · Manual · hace 3 h" },
      { name: "Pedro M.", detail: "S/ 6k · WhatsApp · hace 8 h" },
      { name: "Lucía R.", detail: "S/ 9k · Web · hace 1 día" },
    ],
  },
  {
    emoji: "🟡",
    label: "Considerando",
    count: 5,
    value: "S/ 41k",
    leads: [
      { name: "JP Méndez", detail: "S/ 11k · WhatsApp · hace 2 días" },
      { name: "Marta L.", detail: "S/ 8k · Web · hace 3 días" },
      { name: "Diego F.", detail: "S/ 7k · Meta · hace 5 días" },
    ],
  },
  {
    emoji: "🔵",
    label: "Listo",
    count: 3,
    value: "S/ 28k",
    leads: [
      { name: "Rosa V.", detail: "S/ 12k · Reservado" },
      { name: "Felipe T.", detail: "S/ 9k · Reservado" },
    ],
  },
  {
    emoji: "🟣",
    label: "Reservado",
    count: 2,
    value: "S/ 15k",
    leads: [
      { name: "Camila B.", detail: "S/ 8k · pagó depósito" },
      { name: "Mateo L.", detail: "S/ 7k · pagó total" },
    ],
  },
  {
    emoji: "⚫",
    label: "Decidió no",
    count: 4,
    value: "—",
    leads: [
      { name: "Iván S.", detail: "razón: precio" },
      { name: "Patricia C.", detail: "razón: no disponible" },
    ],
  },
];

// ── Toggle items ─────────────────────────────────────────────────────────────

const TOGGLE_ITEMS: TogglePillItem[] = [
  { value: "kanban", label: "Kanban" },
  { value: "lista", label: "Lista" },
];

// ── Sub-components ────────────────────────────────────────────────────────────

interface KanbanColumnCardProps {
  column: KanbanColumn;
}

function KanbanColumnCard({ column }: KanbanColumnCardProps) {
  return (
    <div className="rounded-md border border-border bg-card p-2">
      {/* Column header */}
      <div className="mb-2 flex items-center justify-between text-xs font-medium">
        <span>
          <span aria-hidden="true">{column.emoji}</span> {column.label}
        </span>
        <span className="text-muted-foreground">
          {column.count} · {column.value}
        </span>
      </div>

      {/* Lead cards */}
      <div className="space-y-1.5">
        {column.leads.map((lead) => (
          <div
            key={lead.name}
            className="rounded border border-border/60 bg-background p-1.5 text-xs"
          >
            <div className="font-medium text-foreground">{lead.name}</div>
            <div className="text-muted-foreground">{lead.detail}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────────────────

/**
 * EmbudoPlaceholder — Pipeline Kanban 6 cols + toggle Kanban|Lista.
 * Client Component (TogglePill manages toggle state via Radix Tabs).
 */
export function EmbudoPlaceholder() {
  return (
    <div className={cn("flex flex-col gap-4")}>
      {/* Header row: title + description + toggle right-aligned */}
      <div className="flex items-start justify-between gap-4">
        <div className="flex flex-col gap-1">
          <h2 className="text-lg font-semibold text-foreground">Embudo</h2>
          <p className="text-sm text-muted-foreground">
            Pipeline de leads en 6 estados (placeholder con leads ficticios).
          </p>
        </div>
        {/* TogglePill is rendered separately from its content — content placed below */}
      </div>

      {/* TogglePill + panels */}
      <TogglePill
        items={TOGGLE_ITEMS}
        defaultValue="kanban"
        data-testid="embudo-toggle"
      >
        {/* Kanban panel */}
        <TogglePillContent value="kanban">
          {/* overflow-x-auto for horizontal scroll on narrow viewports */}
          <div className="overflow-x-auto">
            <div className="grid min-w-[960px] grid-cols-6 gap-2 pt-3">
              {MOCK_PIPELINE.map((col) => (
                <KanbanColumnCard key={col.label} column={col} />
              ))}
            </div>
          </div>
        </TogglePillContent>

        {/* Lista panel — EmptyState placeholder */}
        <TogglePillContent value="lista">
          <EmptyState
            icon="📋"
            title="Vista lista — próximamente"
            description="Tabla con filtros (estado, origen, fecha) + orden por valor / antigüedad / score."
          />
        </TogglePillContent>
      </TogglePill>
    </div>
  );
}
