// cap: crm.crm-scaffold-slice-1
// story-origin: TBD
/**
 * lead.ts — Zod schema for Lead runtime validation.
 *
 * SSoT for API response validation (consumed by use-leads hook in crm-shared/api/).
 * Mirrors Pydantic LeadResponse shape exactly (snake_case).
 * Schema is the source of truth — types are inferred from it.
 *
 * Consumer: features/crm-shared/api/use-leads.ts (T-inbox-fe-2)
 *           features/inbox (this story — scaffold)
 *           features/pipeline (Ola 2)
 *           features/agenda (Ola 2)
 *
 * PHI fields: name, phone, email — validated but displayed via PiiMaskedSpan.
 *
 * downstream-regression-na: brand-local FE schema; no cross-brand consumers
 */
import { z } from "zod";

/** CRM funnel stage enum */
export const leadStageSchema = z.enum([
  "interesado",
  "calificando",
  "considerando",
  "listo",
  "reservado_deposito",
  "decidio_no",
]);

/** Lead attribution source enum */
export const leadOriginSchema = z.enum([
  "sales_agent",
  "walk_in",
  "phone_manual",
  "proactive_outbound",
]);

/** Attribution sub-object schema */
export const leadAttributionSchema = z.object({
  origin: leadOriginSchema,
  channel: z.string().nullable(),
  attributed_at: z.string().datetime({ offset: true }),
});

/**
 * leadSchema — Zod schema for Lead API response.
 * Validates runtime data from GET /api/v1/vitalia/crm/leads/{id}
 * and GET /api/v1/vitalia/crm/leads (list items).
 */
export const leadSchema = z.object({
  id: z.string().uuid(),
  tenant_id: z.string().uuid(),
  clinic_id: z.string().uuid(),
  /** PHI: display via PiiMaskedSpan kind="name" */
  name: z.string().min(1),
  /** PHI: display via PiiMaskedSpan kind="phone" */
  phone: z.string().nullable(),
  /** PHI: display via PiiMaskedSpan kind="email" */
  email: z.string().email().nullable().or(z.null()),
  stage: leadStageSchema,
  attribution: leadAttributionSchema,
  last_conversation_id: z.string().uuid().nullable(),
  created_at: z.string().datetime({ offset: true }),
  updated_at: z.string().datetime({ offset: true }),
});

/** Paginated lead list response schema */
export const leadListResponseSchema = z.object({
  items: z.array(leadSchema),
  total: z.number().int().nonnegative(),
  page: z.number().int().positive(),
  page_size: z.number().int().positive(),
});

/** Inferred TypeScript types from schemas */
export type LeadSchema = z.infer<typeof leadSchema>;
export type LeadStageSchema = z.infer<typeof leadStageSchema>;
export type LeadOriginSchema = z.infer<typeof leadOriginSchema>;
export type LeadListResponseSchema = z.infer<typeof leadListResponseSchema>;
