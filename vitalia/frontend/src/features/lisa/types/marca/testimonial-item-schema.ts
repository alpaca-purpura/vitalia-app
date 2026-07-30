// cap: brand_studio.lisa-marca
// story-origin: vitalia-fase2-s7-TBD
/**
 * testimonial-item-schema.ts — Zod schema for testimonial collection.
 *
 * IMPORT verbatim from nicolify/frontend/src/features/brand-studio/schemas/testimonial-item.schema.ts
 * Adapted to Zod (RHF resolver) for vitalia/features/lisa.
 *
 * T-8 vitalia-fase2-lisa-marca
 * spec_anchor: 03-arch.md § 5 + CONTEXT-BRIEF § 5 (REUSE map)
 * downstream-regression-na: brand-local vitalia FE schema; no cross-brand consumers
 */

import { z } from "zod";

const optionalUrl = z
  .string()
  .url("Ingresa una URL válida (ej: https://...)")
  .optional()
  .or(z.literal(""));

const mediaTypeEnum = z.enum(["text", "video", "audio", "image"]);

/** Tag item — 1 sub-field → cards mode per form-runtime-array.md. */
const tagItemSchema = z.object({
  value: z.string().min(1, "Requerido").max(50, "Máximo 50 caracteres"),
});

/** Per-testimonial form. Backed by TestimonialUpdateDTO. */
export const testimonialItemSchema = z.object({
  author_name: z
    .string()
    .min(1, "El nombre del autor es requerido")
    .max(120, "Máximo 120 caracteres"),
  author_role: z.string().max(200, "Máximo 200 caracteres").optional(),
  author_avatar_url: optionalUrl,
  content: z.string().max(2000, "Máximo 2000 caracteres").optional(),
  media_type: mediaTypeEnum.optional(),
  media_url: optionalUrl,
  rating: z.number().min(1, "Mínimo 1").max(5, "Máximo 5").optional(),
  source_url: optionalUrl,
  captured_at: z
    .string()
    .regex(/^\d{4}-\d{2}-\d{2}$/, "Usa el formato AAAA-MM-DD")
    .optional()
    .or(z.literal("")),
  language: z
    .string()
    .regex(/^[a-z]{2}$/, "Usa el código ISO de 2 letras (ej: es)")
    .optional()
    .or(z.literal("")),
  tags: z.array(tagItemSchema).optional(),
});

export type TestimonialItemFormValues = z.infer<typeof testimonialItemSchema>;
