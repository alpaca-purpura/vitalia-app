// cap: brand_studio.lisa-marca
// story-origin: vitalia-fase2-s7-TBD
/**
 * prohibited-phrase-schema.ts — Zod schema for vitalia prohibited phrases (NEW).
 *
 * vitalia_prohibited_phrases table — brand-local (no cross-brand mirror detected).
 * Soft warning (configurable per tenant, does NOT block persistence).
 * Seed: PE defaults 10 rows.
 *
 * T-8 vitalia-fase2-lisa-marca
 * spec_anchor: 03-arch.md § 5 + D2-voice + CONTEXT-BRIEF § 2
 * downstream-regression-na: brand-local vitalia FE schema; no cross-brand consumers
 */

import { z } from "zod";

export const phraseSeverityEnum = z.enum(["warning", "block"] as const, {
  message: "Selecciona: advertencia o bloqueo",
});

export type PhraseSeverity = z.infer<typeof phraseSeverityEnum>;

/** Per-prohibited-phrase form. Backed by ProhibitedPhraseDTO. */
export const prohibitedPhraseSchema = z.object({
  phrase: z.string().min(1, "La frase es requerida").max(300, "Máximo 300 caracteres"),
  suggested_alternative: z
    .string()
    .max(300, "Máximo 300 caracteres")
    .nullable()
    .optional(),
  severity: phraseSeverityEnum,
});

export type ProhibitedPhraseFormValues = z.infer<typeof prohibitedPhraseSchema>;
