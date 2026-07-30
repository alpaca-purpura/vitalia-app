// cap: lisa.servicios
// story-origin: vitalia-fase2-lisa-servicios T-6
/**
 * servicios-schema.ts — Zod schemas (RHF resolvers) for the servicios forms.
 *
 * Discriminated union by `modality` (RHF + Zod, ADR-vitalia-004 § 5):
 *   - unica        → one-off, no extra fields
 *   - sesiones     → sessionsCount >= 1 + interval {value, unit}
 *   - recurrente   → cadence {value, unit}
 *
 * price: z.number().min(0) (RN-11 — no negative prices).
 * variants: optional repeater {name, price>=0, note?}.
 *
 * NOTE (T-6 scope): the create/edit FORM itself ships in T-7 (workspace leaves).
 * T-6 only needs the create-custom + create-from-template payload schemas (used by
 * the "+ Nuevo servicio" flow + the biblioteca empty-state) and the shared
 * value-with-unit primitive. The full sales-brief form stays in T-7.
 *
 * T-6 vitalia-fase2-lisa-servicios
 * spec_anchor: 03-arch-fe.md § 5 forms + 01-spec.md RN-11
 */

import { z } from "zod";

// ── Shared value-with-unit primitive (interval / cadence) ───────────────────────

export const timeUnitSchema = z.enum(["dias", "semanas", "meses", "anios"]);
export type TimeUnit = z.infer<typeof timeUnitSchema>;

export const valueWithUnitSchema = z.object({
  value: z.number().int().min(1, "Debe ser al menos 1"),
  unit: timeUnitSchema,
});
export type ValueWithUnit = z.infer<typeof valueWithUnitSchema>;

// ── Variant repeater ────────────────────────────────────────────────────────────

export const variantSchema = z.object({
  name: z.string().min(1, "Requerido"),
  price: z.number().min(0, "El precio no puede ser negativo"),
  note: z.string().optional(),
});
export type VariantFormValues = z.infer<typeof variantSchema>;

// ── Create custom service (discriminated union by modality) ─────────────────────

const baseCustomFields = {
  public_name: z.string().min(1, "El nombre es requerido"),
  price: z.number().min(0, "El precio no puede ser negativo"), // RN-11
  currency: z.string().optional().nullable(),
  category: z.string().optional().nullable(),
  variants: z.array(variantSchema).optional(),
};

export const createCustomServicioSchema = z.discriminatedUnion("modality", [
  z.object({ ...baseCustomFields, modality: z.literal("unica") }),
  z.object({
    ...baseCustomFields,
    modality: z.literal("sesiones"),
    sessionsCount: z.number().int().min(1, "Al menos 1 sesión"),
    interval: valueWithUnitSchema,
  }),
  z.object({
    ...baseCustomFields,
    modality: z.literal("recurrente"),
    cadence: valueWithUnitSchema,
  }),
]);
export type CreateCustomServicioFormValues = z.infer<
  typeof createCustomServicioSchema
>;

// ── Create from template (biblioteca) ───────────────────────────────────────────

export const createFromTemplateSchema = z.object({
  canonical_service_ref: z.string().min(1),
  clinic_type: z.string().min(1),
});
export type CreateFromTemplateFormValues = z.infer<
  typeof createFromTemplateSchema
>;
