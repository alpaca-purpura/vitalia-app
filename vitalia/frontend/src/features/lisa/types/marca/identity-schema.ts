// cap: brand_studio.lisa-marca
// story-origin: vitalia-fase2-s7-TBD
/**
 * identity-schema.ts — Zod schema for brand identity section.
 *
 * IMPORT verbatim from nicolify/frontend/src/features/brand-studio/schemas/identity.schema.ts
 * Adapted to Zod (RHF resolver) for vitalia/features/lisa.
 *
 * T-8 vitalia-fase2-lisa-marca
 * spec_anchor: 03-arch.md § 5 + CONTEXT-BRIEF § 5 (REUSE map)
 * downstream-regression-na: brand-local vitalia FE schema; no cross-brand consumers
 */

import { z } from "zod";

export const identitySchema = z.object({
  brand_name: z.string().min(1, "El nombre es requerido").max(120, "Máximo 120 caracteres"),
  tagline: z.string().max(200, "Máximo 200 caracteres").optional(),
  description: z.string().max(1000, "Máximo 1000 caracteres").optional(),
  industry: z.string().max(200, "Máximo 200 caracteres").optional(),
  website: z
    .string()
    .url("Ingresa una URL válida (ej: https://...)")
    .max(500, "Máximo 500 caracteres")
    .optional()
    .or(z.literal("")),
  founding_year: z
    .string()
    .regex(/^\d{4}$/, "Ingresa un año válido (ej: 2020)")
    .optional()
    .or(z.literal("")),
  language: z
    .string()
    .regex(/^[a-z]{2}$/, "Usa el código ISO de 2 letras (ej: es)")
    .optional()
    .or(z.literal("")),
  timezone: z.string().max(100, "Máximo 100 caracteres").optional(),
});

export type IdentityFormValues = z.infer<typeof identitySchema>;
