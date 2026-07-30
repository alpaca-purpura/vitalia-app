// cap: crm.adrian-embudo
// story-origin: vitalia-fase2-adrian-embudo
/**
 * embudo-schema.ts — Zod schemas for Embudo forms (T-FE-2).
 *
 * Schemas:
 * - overrideReasonSchema: validates reason in OverrideReasonDialog
 *
 * Note: newLeadSchema lives in T-FE-3 (NewLeadPage).
 *
 * Spanish neutro labels (sin voseo) per spanish-text.md.
 * spec_anchor: 03-arch-fe.md § Forms + 03-arch.md § 5
 */
import { z } from "zod";
import type { LeadFunnelStage } from "./embudo.types";

// ── Override reason schema ────────────────────────────────────────────────────

export const overrideReasonSchema = z.object({
  reason: z
    .string()
    .min(1, "La razón es requerida")
    .max(500, "La razón debe tener máximo 500 caracteres"),
  toStage: z.string() as z.ZodType<LeadFunnelStage>,
});

export type OverrideReasonData = z.infer<typeof overrideReasonSchema>;

// ── SLA constants (mirrors BE funnel_machine.py SSoT) ─────────────────────────

/** SLA green threshold in days per stage (RN-11, v3 spec) */
export const STAGE_SLA_DAYS: Partial<Record<LeadFunnelStage, number>> = {
  interesado: 7,
  calificando: 7,
  consulta_agendada: 5,
  plan_presentado: 14,
  // reservado + decidio_no = terminal, no SLA
};

/** Stage display labels (Spanish neutro) */
export const STAGE_LABELS: Record<LeadFunnelStage, string> = {
  interesado: "Interesado",
  calificando: "Calificando",
  consulta_agendada: "Consulta agendada",
  plan_presentado: "Plan presentado",
  reservado: "Reservado",
  decidio_no: "Decidió no",
};

/** Stage emojis for visual distinction */
export const STAGE_EMOJI: Record<LeadFunnelStage, string> = {
  interesado: "⚪",
  calificando: "🟢",
  consulta_agendada: "🟡",
  plan_presentado: "🔵",
  reservado: "🟣",
  decidio_no: "⚫",
};

/** Hot columns shown on the board (RN-18 — decidio_no goes to Recuperar) */
export const BOARD_HOT_STAGES: LeadFunnelStage[] = [
  "interesado",
  "calificando",
  "consulta_agendada",
  "plan_presentado",
  "reservado",
];

/** Allowed next stages per stage (mirrors BE funnel_machine.py STAGE_MACHINE) */
export const STAGE_ALLOWED_NEXT: Record<LeadFunnelStage, LeadFunnelStage[]> = {
  interesado: ["calificando", "decidio_no"],
  calificando: ["consulta_agendada", "decidio_no", "interesado"],
  consulta_agendada: ["plan_presentado", "calificando", "decidio_no"],
  plan_presentado: ["reservado", "consulta_agendada", "decidio_no"],
  reservado: [],
  decidio_no: ["interesado"],
};

/** Whether a stage transition is "adjacent" (no dialog needed) vs "skip" (dialog required) */
export function isAdjacentTransition(
  fromStage: LeadFunnelStage,
  toStage: LeadFunnelStage,
): boolean {
  const allowed = STAGE_ALLOWED_NEXT[fromStage] ?? [];
  // Adjacent = direct next forward or immediate back
  const stageOrder = Object.keys(STAGE_LABELS) as LeadFunnelStage[];
  const fromIdx = stageOrder.indexOf(fromStage);
  const toIdx = stageOrder.indexOf(toStage);
  const isDirectNeighbor = Math.abs(fromIdx - toIdx) === 1;
  return allowed.includes(toStage) && isDirectNeighbor;
}

// ── New lead schema (T-FE-3 — NewLeadPage) ───────────────────────────────────

/** Channel options for new lead form (Spanish neutro labels) */
export const CHANNEL_OPTIONS = [
  { value: "whatsapp", label: "WhatsApp" },
  { value: "instagram", label: "Instagram" },
  { value: "meta", label: "Meta Ads" },
  { value: "referido", label: "Referido" },
  { value: "web", label: "Web" },
  { value: "tiktok", label: "TikTok" },
  { value: "otro", label: "Otro" },
] as const;

/**
 * newLeadSchema — Zod schema for /adrian/embudo/nuevo form.
 *
 * Rules (per spec V5 + SC-nuevo):
 * - nombre: required
 * - canal: required, must be a known channel
 * - teléfono OR email: at least one required (refine)
 * - etapa: default interesado
 * - serviceInterest, tags, notas: optional
 *
 * Spanish neutro LatAm labels (sin voseo).
 */
export const newLeadSchema = z.object({
  name: z
    .string()
    .min(1, "El nombre es requerido")
    .max(200, "El nombre no puede superar 200 caracteres"),
  channel: z
    .string()
    .min(1, "El canal es requerido"),
  phone: z.string().max(30).nullable().optional(),
  email: z.string().email("Correo inválido").nullable().optional().or(z.literal("")),
  stage: z.enum([
    "interesado",
    "calificando",
    "consulta_agendada",
    "plan_presentado",
    "reservado",
    "decidio_no",
  ] as const).default("interesado"),
  serviceInterest: z.string().max(200).nullable().optional(),
  tags: z.array(z.string()).default([]),
  notes: z.string().max(2000).default(""),
}).refine(
  (data) => !!data.phone || !!data.email,
  {
    message: "Ingresa al menos un teléfono o correo para contactar al lead",
    path: ["phone"], // attach error to phone field
  },
);

export type NewLeadFormData = z.infer<typeof newLeadSchema>;
