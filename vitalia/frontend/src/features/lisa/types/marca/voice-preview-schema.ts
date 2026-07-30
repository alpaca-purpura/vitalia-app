// cap: brand_studio.lisa-marca
// story-origin: vitalia-fase2-s7-TBD
/**
 * voice-preview-schema.ts — Zod schema for voice preview request/response (NEW).
 *
 * Voice preview (OQ-C): BE endpoint /api/v1/lisa/marca/voice-preview
 * server-side compile + LRU cache per (tenant_id, profile_id, compiler_version, hash(blocks)).
 * Library-only compiler v2 — NO LLM dispatch in FE.
 * Preview footer ÚNICO debajo Tratamiento+idioma card (OQ-E).
 *
 * T-8 vitalia-fase2-lisa-marca
 * spec_anchor: 03-arch.md § 5 + OQ-C + OQ-E + CONTEXT-BRIEF § 2
 * downstream-regression-na: brand-local vitalia FE schema; no cross-brand consumers
 */

import { z } from "zod";

/** Request payload for voice preview endpoint. */
export const voicePreviewRequestSchema = z.object({
  tenant_id: z.string().uuid("ID de tenant inválido"),
  profile_id: z.string().uuid("ID de perfil inválido"),
  blocks_hash: z.string().min(1, "Requerido").max(64, "Máximo 64 caracteres"),
});

/** Response from voice preview endpoint. */
export const voicePreviewResponseSchema = z.object({
  whatsapp_cobranza_sample: z
    .string()
    .max(2000, "Máximo 2000 caracteres"),
  email_reactivacion_sample: z
    .string()
    .max(5000, "Máximo 5000 caracteres"),
});

/** Wrapper for request + response (used in React Query hook). */
export const voicePreviewSchema = z.object({
  request: voicePreviewRequestSchema,
  response: voicePreviewResponseSchema,
});

export type VoicePreviewRequest = z.infer<typeof voicePreviewRequestSchema>;
export type VoicePreviewResponse = z.infer<typeof voicePreviewResponseSchema>;
export type VoicePreviewPayload = z.infer<typeof voicePreviewSchema>;
