// cap: brand_studio.lisa-marca
// story-origin: vitalia-fase2-s7-TBD
/**
 * contact-schema.ts — Zod schema for brand contact section.
 *
 * IMPORT verbatim from nicolify/frontend/src/features/brand-studio/schemas/contact.schema.ts
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

const optionalEmail = z
  .string()
  .email("Ingresa un correo válido")
  .optional()
  .or(z.literal(""));

export const contactSchema = z.object({
  support_email: optionalEmail,
  sales_email: optionalEmail,
  phone: z.string().max(30, "Máximo 30 caracteres").optional(),
  whatsapp: z.string().max(30, "Máximo 30 caracteres").optional(),
  address: z.string().max(400, "Máximo 400 caracteres").optional(),
  social_instagram: z.string().max(100, "Máximo 100 caracteres").optional(),
  social_linkedin: optionalUrl,
  social_youtube: optionalUrl,
  social_tiktok: z.string().max(100, "Máximo 100 caracteres").optional(),
  social_facebook: z.string().max(100, "Máximo 100 caracteres").optional(),
  social_twitter: z.string().max(100, "Máximo 100 caracteres").optional(),
  testimonials_url: optionalUrl,
});

export type ContactFormValues = z.infer<typeof contactSchema>;
