// cap: brand_studio.lisa-marca
// story-origin: vitalia-fase2-s7-TBD
/**
 * team-schema.ts — Zod schema for team member collection.
 *
 * IMPORT verbatim from nicolify/frontend/src/features/brand-studio/schemas/team-member-item.schema.ts
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

/** Gallery image item — 1 sub-field → cards mode per form-runtime-array.md. */
const galleryItemSchema = z.object({
  value: z.string().url("Ingresa una URL válida").min(1, "Requerido"),
});

/** Per-team-member form. Backed by TeamMemberUpdateDTO. */
export const teamMemberItemSchema = z.object({
  name: z
    .string()
    .min(1, "El nombre es requerido")
    .max(120, "Máximo 120 caracteres"),
  role: z.string().max(200, "Máximo 200 caracteres").optional(),
  is_primary_voice: z.boolean().optional(),
  headshot_url: optionalUrl,
  bio: z.string().max(1000, "Máximo 1000 caracteres").optional(),
  gender: z.string().max(50, "Máximo 50 caracteres").optional(),
  communication_style: z.string().max(200, "Máximo 200 caracteres").optional(),
  work_whatsapp: z.string().max(30, "Máximo 30 caracteres").optional(),
  personal_website: optionalUrl,
  personal_linkedin: optionalUrl,
  personal_instagram: optionalUrl,
  personal_tiktok: optionalUrl,
  personal_facebook: optionalUrl,
  gallery: z.array(galleryItemSchema).optional(),
  sort_order: z.number().int().optional(),
});

export type TeamMemberFormValues = z.infer<typeof teamMemberItemSchema>;
