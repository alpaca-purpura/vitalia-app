// cap: adrian.inbox
// story-origin: vitalia-fase2-adrian-inbox
/**
 * inbox-schema.ts — Zod validation schemas for Adrián Inbox payloads.
 * T-4 vitalia-fase2-adrian-inbox (NEW)
 *
 * Validates mutation payloads (send message, set mode, nudge) before submission.
 * Integrated with RHF (zodResolver) in Composer form.
 *
 * No autosave — Composer is submit-driven (send/mode/nudge are atomic).
 * Toasts via sonner on validation failure.
 *
 * downstream-regression-na: brand-local FE schemas; no cross-brand consumers
 * spec_anchor: 03-arch-fe.md § 9 + 06-tickets.yaml T-4
 */

import { z } from "zod";

// ── Send message schema ───────────────────────────────────────────────────────

export const sendMessageSchema = z.object({
  /** Plain-text message body. Min 1 char after trim. */
  body_text: z
    .string()
    .trim()
    .min(1, "El mensaje no puede estar vacío")
    .max(4096, "El mensaje es demasiado largo"),
  /** Optional idempotency key (client-generated UUID v4) */
  idempotency_key: z.string().uuid().optional(),
});

export type SendMessagePayload = z.infer<typeof sendMessageSchema>;

// ── Set mode schema (discriminated union) ─────────────────────────────────────

const setModeAiSchema = z.object({
  mode: z.literal("ai"),
  proposal_required: z.boolean(),
  expected_updated_at: z.string(),
});

const setModeHumanSchema = z.object({
  mode: z.literal("human"),
  proposal_required: z.literal(false),
  expected_updated_at: z.string(),
});

/**
 * Discriminated union on `mode` field.
 * Enforces: human mode cannot have proposal_required=true.
 */
export const setModeSchema = z.discriminatedUnion("mode", [
  setModeAiSchema,
  setModeHumanSchema,
]);

export type SetModePayload = z.infer<typeof setModeSchema>;

// ── Nudge schema ──────────────────────────────────────────────────────────────

export const nudgeSchema = z.object({
  /**
   * Optional reason for nudge (shown in activity stream summary).
   * Spanish neutro, max 280 chars.
   */
  reason: z
    .string()
    .trim()
    .max(280, "La razón es demasiado larga")
    .optional(),
  /** Optional idempotency key to prevent double-nudge on same day */
  idempotency_key: z.string().uuid().optional(),
});

export type NudgePayload = z.infer<typeof nudgeSchema>;

// ── Inbox filter schema ───────────────────────────────────────────────────────

const VALID_FILTERS = [
  "todos",
  "sin-leer",
  "asignadas",
  "esperando",
  "bot-activo",
  "cerradas",
] as const;

export type InboxFilterValue = (typeof VALID_FILTERS)[number];

export const inboxFilterSchema = z.enum(VALID_FILTERS);
