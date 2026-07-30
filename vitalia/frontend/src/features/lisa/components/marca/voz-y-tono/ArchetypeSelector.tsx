// cap: brand_studio.lisa-marca
// story-origin: vitalia-fase2-s7-TBD
"use client";

/**
 * ArchetypeSelector.tsx — 4 salud-friendly archetype cards (OQ-B).
 *
 * Renders exactly 4 radio cards: Caregiver (default), Sage, Healer, Hero.
 * NO outlaw / magician / lover / innocent (anti-creep D5-archetype).
 *
 * Accessibility: role="radiogroup" + each card is role="radio" with aria-checked.
 * Loading: skeleton with aria-label="Cargando arquetipos".
 *
 * T-6 vitalia-fase2-lisa-marca
 * spec_anchor: 06-tickets.yaml T-6 A1 + 04-validators.yaml fe_test_archetype_4_salud
 * downstream-regression-na: brand-local vitalia FE component; no cross-brand consumers
 */

import { cn } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import type { SaludArchetype } from "../../../types/marca/personality-schema";

// ── Archetype display catalog (FE-only labels/icons — vitalia brand-local) ────

interface ArchetypeCardData {
  value: SaludArchetype;
  label: string;
  emoji: string;
  description: string;
}

const ARCHETYPE_CARDS: ArchetypeCardData[] = [
  {
    value: "caregiver",
    label: "Cuidador",
    emoji: "🤝",
    description: "Empatía, acompañamiento y cuidado genuino del paciente.",
  },
  {
    value: "sage",
    label: "Sabio",
    emoji: "📚",
    description: "Conocimiento experto, claridad clínica y orientación confiable.",
  },
  {
    value: "healer",
    label: "Sanador",
    emoji: "✨",
    description: "Transformación, bienestar integral y restauración de la salud.",
  },
  {
    value: "hero",
    label: "Héroe",
    emoji: "💪",
    description: "Compromiso con resultados, superación y excelencia clínica.",
  },
];

// ── Loading skeleton ──────────────────────────────────────────────────────────

function ArchetypeCardsSkeleton() {
  return (
    <section
      aria-label="Cargando arquetipos"
      aria-busy="true"
      className="flex flex-col gap-3"
    >
      <p className="text-sm font-semibold text-foreground">Arquetipo principal</p>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-[110px] rounded-lg" />
        ))}
      </div>
    </section>
  );
}

// ── ArchetypeSelector ─────────────────────────────────────────────────────────

export interface ArchetypeSelectorProps {
  selected: SaludArchetype | null;
  onSelect: (archetype: SaludArchetype) => void;
  isLoading: boolean;
  /** If set, shows a "Sugerido" badge on the matching card (OQ-B default=caregiver). */
  recommendedArchetype?: SaludArchetype;
  className?: string;
}

export function ArchetypeSelector({
  selected,
  onSelect,
  isLoading,
  recommendedArchetype,
  className,
}: ArchetypeSelectorProps) {
  if (isLoading) {
    return <ArchetypeCardsSkeleton />;
  }

  return (
    <section className={cn("flex flex-col gap-3", className)}>
      <p className="text-sm font-semibold text-foreground">Arquetipo principal</p>
      <div
        role="radiogroup"
        data-testid="archetype-selector"
        aria-label="Selecciona el arquetipo de tu clínica"
        className="grid grid-cols-2 gap-3 sm:grid-cols-4"
      >
        {ARCHETYPE_CARDS.map((card) => {
          const isSelected = selected === card.value;
          const isRecommended = recommendedArchetype === card.value;

          return (
            <button
              key={card.value}
              role="radio"
              data-testid={`archetype-card-${card.value}`}
              data-selected={isSelected}
              aria-checked={isSelected}
              aria-label={card.label}
              onClick={() => onSelect(card.value)}
              className={cn(
                "relative flex flex-col items-center gap-2 rounded-lg border p-4 text-center transition-all",
                "hover:border-primary/60 hover:bg-accent/30",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
                isSelected
                  ? "border-primary bg-primary/5 shadow-sm"
                  : "border-border bg-card",
              )}
            >
              {isRecommended && (
                <Badge
                  variant="secondary"
                  className="absolute -top-2 left-1/2 -translate-x-1/2 whitespace-nowrap text-[10px]"
                >
                  Sugerido
                </Badge>
              )}
              <span className="text-2xl" aria-hidden="true">
                {card.emoji}
              </span>
              <span
                className={cn(
                  "text-sm font-semibold",
                  isSelected ? "text-primary" : "text-foreground",
                )}
              >
                {card.label}
              </span>
              <span className="text-xs text-muted-foreground leading-snug">
                {card.description}
              </span>
            </button>
          );
        })}
      </div>
    </section>
  );
}

ArchetypeSelector.displayName = "ArchetypeSelector";
