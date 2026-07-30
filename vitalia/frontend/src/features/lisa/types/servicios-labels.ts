// cap: lisa.servicios
// story-origin: vitalia-fase2-lisa-servicios T-6
/**
 * servicios-labels.ts — FE-local MEDICAL labels for the ladder rungs (RN-2 override).
 *
 * ★ M2 / RN-2: the engine's OfferValueLevel.label_es is generic GTM language
 *   ("Lead magnet", "Activación", …). Vitalia overrides them with the medical
 *   vocabulary clinicians expect. These labels are hardcoded FE-side ON PURPOSE —
 *   we do NOT consume the engine label_es blindly (M2). The 5 rung ids stay the
 *   wire values; only the human label + icon are vitalia-flavoured.
 *
 * Ladder layout (03-arch-fe.md § 7): rung 1 full-width on top · rungs 2-3-4 as a
 * 3-column band in the middle · rung 5 full-width at the bottom.
 *
 * T-6 vitalia-fase2-lisa-servicios
 * spec_anchor: 03-arch-fe.md § 7 escalera + 01-spec.md RN-2
 */

import type { OfferValueLevel } from "./servicios.types";

export interface RungMeta {
  id: OfferValueLevel;
  /** "PELDAÑO N" heading label (1-based, layout order). */
  numero: string;
  /** Medical label (RN-2 override of engine label_es). */
  label: string;
  /** Short clarifying line shown under the rung heading. */
  explain: string;
  /** Layout slot: full-width header, 3-col middle band, full-width footer. */
  layout: "full" | "band";
  /** Token utility classes for the rung badge (bg + text). */
  badgeClass: string;
}

/**
 * The 5 FIXED rungs in ladder order (top → bottom).
 * Order matters: RUNG_ORDER drives the escalera layout.
 */
export const RUNG_META: readonly RungMeta[] = [
  {
    id: "lead_magnet",
    numero: "PELDAÑO 1",
    label: "Gancho gratuito",
    explain: "Lo que atrae al paciente sin costo (primera valoración, guía).",
    layout: "full",
    badgeClass: "bg-emerald-100 text-emerald-700",
  },
  {
    id: "activacion",
    numero: "PELDAÑO 2",
    label: "Primera visita",
    explain: "El primer servicio pago — la puerta de entrada.",
    layout: "band",
    badgeClass: "bg-sky-100 text-sky-700",
  },
  {
    id: "transformacion",
    numero: "PELDAÑO 3",
    label: "Tratamiento principal",
    explain: "El servicio central que resuelve el problema del paciente.",
    layout: "band",
    badgeClass: "bg-violet-100 text-violet-700",
  },
  {
    id: "maximizacion",
    numero: "PELDAÑO 4",
    label: "Premium",
    explain: "La versión ampliada o de mayor valor.",
    layout: "band",
    badgeClass: "bg-amber-100 text-amber-700",
  },
  {
    id: "corporativo",
    numero: "PELDAÑO 5",
    label: "Plan / convenio",
    explain: "Acuerdos con empresas o planes a medida.",
    layout: "full",
    badgeClass: "bg-slate-100 text-slate-700",
  },
] as const;

/** Quick id → label lookup (medical). */
export const RUNG_LABEL_ES: Record<OfferValueLevel, string> = Object.fromEntries(
  RUNG_META.map((r) => [r.id, r.label]),
) as Record<OfferValueLevel, string>;

/** Ladder rung ids in layout order. */
export const RUNG_ORDER: readonly OfferValueLevel[] = RUNG_META.map((r) => r.id);

/** Modality → short human label + icon (used on the card modality indicator). */
export const MODALITY_LABEL: Record<string, string> = {
  unica: "Única",
  sesiones: "Por sesiones",
  recurrente: "Recurrente",
};
