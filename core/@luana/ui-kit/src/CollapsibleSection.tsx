// cap: lisa.servicios (origin: vitalia-fase2-lisa-servicios T-R0 · promotion 2026-06-16-collapsible-section-ui-kit)
"use client";

/**
 * CollapsibleSection.tsx — Molécula colapsable de sección (@luana/ui-kit).
 *
 * Compone primitivos YA exportados de @luana/ui-kit:
 *   - `Accordion` / `AccordionItem` / `AccordionTrigger` / `AccordionContent`
 *     (Radix UI accordion — uncontrolled, single-item, collapsible)
 *   - `Group` / `GroupHeader`
 *     (barrita de agente + error semántico + card, canon §2.6)
 *
 * Anatomía:
 *   ┌╴ agent-color LEFT strip (border-l-4, token-driven) ─────────────────────┐
 *   │  [AccordionTrigger]  título          summary/contador  ▾                  │
 *   │  Falta: campo A, campo B   ← inline alert (GroupHeader, opcional)         │
 *   │  ─────────────────────────────────────────────────────────────────────── │
 *   │  [AccordionContent]  children (body colapsable)                           │
 *   └─────────────────────────────────────────────────────────────────────────┘
 *
 * `defaultOpen` → uncontrolled `defaultValue` en Radix Accordion.
 * Sin `value`/`onValueChange` controlados (YAGNI — se agrega cuando un
 * consumer real lo necesite).
 *
 * Token-driven: accentVar / accentClass NUNCA hex.
 * Spanish neutro LatAm en todo texto user-facing (sin voseo).
 *
 * Promotion proposal: docs/promotion-protocol/proposals/2026-06-16-collapsible-section-ui-kit.md
 * SSoT contrato: vitalia/docs/product/stories/vitalia-fase2-lisa-servicios/03-arch-reconcile-delta.md § Part D
 *
 * T-R0 · vitalia-fase2-lisa-servicios reconcile delta 2026-06-16
 */

import * as React from "react";

import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "./accordion";
import { Group, GroupHeader } from "./Group";

// ── CollapsibleSectionProps ───────────────────────────────────────────────────

export interface CollapsibleSectionProps {
  /** Título de la sección (se renderiza en el trigger). */
  title: string;
  /**
   * Si el body está abierto al montar (uncontrolled).
   * @default false
   */
  defaultOpen?: boolean;
  /**
   * Contenido adicional a la derecha del título en el header (ej. "6 campos").
   * Acepta cualquier ReactNode o string.
   */
  summary?: React.ReactNode;
  /**
   * Barrita de agente a la izquierda via CSS var (ej. "--agent-lisa").
   * Aplicado inline: `borderLeftColor: hsl(var(accentVar))`.
   * Token-driven, NUNCA hex. Delega a Group.accentVar.
   */
  accentVar?: string;
  /**
   * Barrita de agente a la izquierda via utility Tailwind (ej. "border-l-agent-lisa").
   * Alternativa a accentVar cuando existe la utility class.
   * Token-driven, NUNCA hex. Delega a Group.accentClass.
   */
  accentClass?: string;
  /**
   * Estado de error semántico (borde rojo). Delega a Group.hasError.
   */
  hasError?: boolean;
  /**
   * Campos faltantes → alerta inline en el GroupHeader (role="alert").
   * Vacío/undefined → no se muestra. Delega a GroupHeader.missingFields.
   */
  missingFields?: string[];
  /** Body colapsable de la sección. */
  children: React.ReactNode;
  /** Clase extra aplicada al contenedor externo (Group). */
  className?: string;
}

// ── Valor interno del Accordion (un único item por molécula) ─────────────────

const ITEM_VALUE = "section";

// ── CollapsibleSection ────────────────────────────────────────────────────────

/**
 * CollapsibleSection — sección de formulario con header colapsable y
 * barrita de agente.
 *
 * @example
 * ```tsx
 * <CollapsibleSection
 *   title="Identidad"
 *   defaultOpen
 *   accentVar="--agent-lisa"
 *   summary={<span className="text-xs text-muted-foreground">3 campos</span>}
 * >
 *   {/* campos del grupo *\/}
 * </CollapsibleSection>
 * ```
 */
export function CollapsibleSection({
  title,
  defaultOpen = false,
  summary,
  accentVar,
  accentClass,
  hasError = false,
  missingFields,
  children,
  className,
}: CollapsibleSectionProps) {
  return (
    <Group
      accentVar={accentVar}
      accentClass={accentClass}
      hasError={hasError}
      className={className}
    >
      <Accordion
        type="single"
        collapsible
        defaultValue={defaultOpen ? ITEM_VALUE : undefined}
      >
        <AccordionItem value={ITEM_VALUE} className="border-b-0">
          {/* Header: GroupHeader (missingFields) + AccordionTrigger (title + summary + chevron) */}
          {(missingFields?.length ?? 0) > 0 ? (
            <GroupHeader
              title=""
              missingFields={missingFields}
              className="mb-0 pb-0"
            />
          ) : null}
          <AccordionTrigger className="py-3 hover:no-underline">
            <div className="flex flex-1 items-center justify-between gap-2 pr-2">
              <span className="text-sm font-semibold text-foreground">
                {title}
              </span>
              {summary != null ? (
                <span className="shrink-0 text-xs text-muted-foreground">
                  {summary}
                </span>
              ) : null}
            </div>
          </AccordionTrigger>
          <AccordionContent>{children}</AccordionContent>
        </AccordionItem>
      </Accordion>
    </Group>
  );
}

CollapsibleSection.displayName = "CollapsibleSection";
