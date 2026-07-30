// cap: brand_studio.lisa-marca
// story-origin: vitalia-fase2-s7-TBD
/**
 * trust-signals-schema.ts — Zod schema for vitalia trust signals (NEW).
 *
 * Hybrid trust catalog per país (OQ-D): PE seed 8 entries + free-text "Otra".
 * Used in Presencia sub-sub-tab for trust/authority signals.
 *
 * T-8 vitalia-fase2-lisa-marca
 * spec_anchor: 03-arch.md § 5 + OQ-D + CONTEXT-BRIEF § 2
 * downstream-regression-na: brand-local vitalia FE schema; no cross-brand consumers
 */

import { z } from "zod";

/**
 * Single certification entry — hybrid catalog (catalog code OR free-text).
 * ≥4 sub-fields → split form mode per form-runtime-array.md default.
 */
export const certificationEntrySchema = z.object({
  country_code: z
    .string()
    .regex(/^[A-Z]{2}$/, "Usa código ISO de país (ej: PE, MX, CO)")
    .optional()
    .or(z.literal("")),
  cert_code: z
    .string()
    .min(1, "El código es requerido")
    .max(100, "Máximo 100 caracteres"),
  custom_label: z
    .string()
    .max(200, "Máximo 200 caracteres")
    .optional(),
});

export type CertificationEntry = z.infer<typeof certificationEntrySchema>;

/** Full trust signals form schema. */
export const trustSignalsSchema = z.object({
  certifications: z.array(certificationEntrySchema).optional(),
  awards: z.array(z.string().min(1, "Requerido").max(300, "Máximo 300 caracteres")).optional(),
  years_experience: z
    .number({ error: "Ingresa un número válido" })
    .int("Debe ser un número entero")
    .min(0, "Debe ser mayor o igual a 0")
    .max(200, "Valor no válido")
    .optional(),
  patients_count: z
    .string()
    .max(50, "Máximo 50 caracteres")
    .optional(),
});

export type TrustSignalsFormValues = z.infer<typeof trustSignalsSchema>;
