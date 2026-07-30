// cap: adrian.inbox
// story-origin: vitalia-fase2-adrian-inbox
/**
 * lead-stage-meta.ts — Central registry: LeadStage slug → label + color class.
 *
 * Single source of truth for inbox lead-stage chip colors and labels. Mirrors the
 * channel-meta.ts pattern (registry + getter + graceful fallback) so stage chips
 * get a differentiated, dark-aware color instead of a flat neutral chip.
 *
 * Scope: the legacy inbox `LeadStage` enum (interesado…decidio_no). The embudo
 * pipeline uses a DIFFERENT enum (`LeadFunnelStage`) — if it ever needs colored
 * stage chips, lift a shared stage-meta then (anti-duplication.md). Do NOT mirror.
 *
 * Design rules:
 * - Color classes use Tailwind semantic palette utilities (same approach as
 *   channel-meta.ts) WITH dark: variants — no hardcoded hex (arch color test safe).
 * - Labels are Spanish neutro LatAm (sin voseo, tildes correctas).
 *
 * spec_anchor: UI-AUDIT-2026-06-04 #5b (stage chips → colores representativos)
 * downstream-regression-na: brand-local lib; no cross-brand consumers
 */

import type { LeadStage } from "@/features/crm-shared";

/** Metadata for one inbox lead stage. */
export interface LeadStageMeta {
  /** Short Spanish neutro label shown in the chip. */
  label: string;
  /** Tailwind utility class string (soft bg + accent text, light + dark). */
  colorClass: string;
}

/**
 * LEAD_STAGE_META — canonical registry for the 6-value inbox `LeadStage`.
 *
 * Hue intent (warm→cold funnel progression):
 *   interesado          → sky     (early interest)
 *   calificando         → amber   (in qualification)
 *   considerando        → violet  (weighing a proposal)
 *   listo               → indigo  (ready to book)
 *   reservado_deposito  → emerald (converted / deposit paid)
 *   decidio_no          → rose    (lost)
 */
export const LEAD_STAGE_META: Readonly<Record<LeadStage, LeadStageMeta>> = {
  interesado: {
    label: "Interesado",
    colorClass: "bg-sky-100 text-sky-800 dark:bg-sky-900/30 dark:text-sky-300",
  },
  calificando: {
    label: "Calificando",
    colorClass:
      "bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-300",
  },
  considerando: {
    label: "Considerando",
    colorClass:
      "bg-violet-100 text-violet-800 dark:bg-violet-900/30 dark:text-violet-300",
  },
  listo: {
    label: "Listo",
    colorClass:
      "bg-indigo-100 text-indigo-800 dark:bg-indigo-900/30 dark:text-indigo-300",
  },
  reservado_deposito: {
    label: "Con depósito",
    colorClass:
      "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-300",
  },
  decidio_no: {
    label: "Decidió no",
    colorClass: "bg-rose-100 text-rose-800 dark:bg-rose-900/30 dark:text-rose-300",
  },
} as const;

/**
 * Returns stage metadata for a slug, or a neutral fallback for unknown values
 * (so an unexpected stage string never crashes the chip).
 */
export function getLeadStageMeta(slug: string): LeadStageMeta {
  return (
    LEAD_STAGE_META[slug as LeadStage] ?? {
      label: slug,
      colorClass: "bg-muted text-muted-foreground",
    }
  );
}
