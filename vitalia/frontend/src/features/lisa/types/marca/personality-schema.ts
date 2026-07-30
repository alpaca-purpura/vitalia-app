// cap: brand_studio.lisa-marca
// story-origin: vitalia-fase2-s7-TBD
/**
 * personality-schema.ts — Zod schema for brand personality (ADAPT salud overlay).
 *
 * BASE: nicolify/frontend/src/features/brand-studio/schemas/personality.schema.ts
 * ADAPT for vitalia (D5-archetype, OQ-B):
 *   - 4 salud-friendly Jung archetypes ONLY: caregiver, sage, healer, hero
 *   - Remove: outlaw, magician, lover, innocent (not salud-appropriate)
 *   - Default: caregiver
 *   - Voice 6 blocks (compiler v2): identity, context, asi_hablo, asi_no_hablo, tech_context, format
 *
 * T-8 vitalia-fase2-lisa-marca
 * spec_anchor: 03-arch.md § 5 + D5-archetype + OQ-B + CONTEXT-BRIEF § 2
 * downstream-regression-na: brand-local vitalia FE schema; no cross-brand consumers
 */

import { z } from "zod";

/**
 * Salud-friendly archetypes — 4 only (D5-archetype, OQ-B).
 * Server-side ENFORCED via Pydantic enum (see BE brand_studio/domain/archetype.py).
 * FE enum must mirror BE enum EXACTLY (arch test fe_arch_test_personality_schema_4_archetypes).
 */
export const SALUD_ARCHETYPES = [
  "caregiver",
  "sage",
  "healer",
  "hero",
] as const;

export type SaludArchetype = (typeof SALUD_ARCHETYPES)[number];

export const saludArchetypeEnum = z.enum(SALUD_ARCHETYPES, {
  message: "Selecciona un arquetipo: Cuidador, Sabio, Sanador o Héroe",
});

/**
 * Voice compiler v2 — 6 blocks per PersonalityProfile (sales-agent-brand-voice.md).
 * Slot 5 BRAND_VOICE cache prefix. LIBRARY-ONLY (no LLM dispatch in FE).
 * Blocks: identity, context, asi_hablo, asi_no_hablo, tech_context, format.
 */
export const voiceBlocksSchema = z.object({
  identity: z
    .string()
    .max(2000, "Máximo 2000 caracteres")
    .optional(),
  context: z
    .string()
    .max(2000, "Máximo 2000 caracteres")
    .optional(),
  asi_hablo: z
    .string()
    .max(2000, "Máximo 2000 caracteres")
    .optional(),
  asi_no_hablo: z
    .string()
    .max(2000, "Máximo 2000 caracteres")
    .optional(),
  tech_context: z
    .string()
    .max(2000, "Máximo 2000 caracteres")
    .optional(),
  format: z
    .string()
    .max(2000, "Máximo 2000 caracteres")
    .optional(),
});

/** Full personality form schema — archetype + core values + traits + voice blocks. */
export const personalitySchema = z.object({
  archetype: saludArchetypeEnum,
  core_values: z
    .string()
    .max(1000, "Máximo 1000 caracteres")
    .optional(),
  personality_traits: z
    .string()
    .max(1000, "Máximo 1000 caracteres")
    .optional(),
  voice_blocks: voiceBlocksSchema.optional(),
});

export type PersonalityFormValues = z.infer<typeof personalitySchema>;
export type VoiceBlocksFormValues = z.infer<typeof voiceBlocksSchema>;
