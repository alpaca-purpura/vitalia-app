// cap: brand_studio.lisa-marca
// story-origin: vitalia-fase2-s7-TBD
/**
 * presence-schema.ts — Zod schema for vitalia brand presence / Presencia (NEW).
 *
 * Covers: website, social media (instagram/tiktok/facebook/google_business/whatsapp),
 * locations. Used in Presencia sub-sub-tab.
 *
 * T-8 vitalia-fase2-lisa-marca
 * spec_anchor: 03-arch.md § 5 + CONTEXT-BRIEF § 2 + 01-spec.md Presencia
 * downstream-regression-na: brand-local vitalia FE schema; no cross-brand consumers
 */

import { z } from "zod";

const optionalUrl = z
  .string()
  .url("Ingresa una URL válida (ej: https://...)")
  .optional()
  .or(z.literal(""));

/**
 * Location entry — ≥4 sub-fields → split form mode per form-runtime-array.md default.
 */
export const locationEntrySchema = z.object({
  name: z
    .string()
    .min(1, "El nombre de la sede es requerido")
    .max(200, "Máximo 200 caracteres"),
  address: z
    .string()
    .min(1, "La dirección es requerida")
    .max(500, "Máximo 500 caracteres"),
});

export type LocationEntry = z.infer<typeof locationEntrySchema>;

/** Social media links — vitalia-specific channels (OQ). */
export const socialMediaSchema = z.object({
  instagram: z.string().max(100, "Máximo 100 caracteres").optional(),
  tiktok: z.string().max(100, "Máximo 100 caracteres").optional(),
  facebook: z.string().max(100, "Máximo 100 caracteres").optional(),
  google_business: optionalUrl,
  whatsapp: z.string().max(30, "Máximo 30 caracteres").optional(),
});

/** Full presence form schema. */
export const presenceSchema = z.object({
  website_url: optionalUrl,
  social_media: socialMediaSchema.optional(),
  locations: z.array(locationEntrySchema).optional(),
});

export type PresenceFormValues = z.infer<typeof presenceSchema>;
export type SocialMediaFormValues = z.infer<typeof socialMediaSchema>;
