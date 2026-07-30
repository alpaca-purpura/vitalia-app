// cap: brand_studio.lisa-marca
// story-origin: vitalia-fase2-s7-TBD
/**
 * visuals-schema.ts — Zod schema for brand visuals section.
 *
 * IMPORT verbatim from nicolify/frontend/src/features/brand-studio/schemas/visuals.schema.ts
 * Adapted to Zod (RHF resolver) for vitalia/features/lisa.
 * ClinicBrandVisuals extends ExtractedVisuals stub (D4-extract: pipeline STUB).
 *
 * T-8 vitalia-fase2-lisa-marca
 * spec_anchor: 03-arch.md § 5 + CONTEXT-BRIEF § 5 (REUSE map) + D4-extract (STUB)
 * downstream-regression-na: brand-local vitalia FE schema; no cross-brand consumers
 */

import { z } from "zod";

const hexColor = z
  .string()
  .regex(/^#[0-9a-fA-F]{6}$/, "Ingresa un color hexadecimal de 6 dígitos (ej: formato #RRGGBB)")
  .optional()
  .or(z.literal(""));

const optionalUrl = z
  .string()
  .url("Ingresa una URL válida (ej: https://...)")
  .optional()
  .or(z.literal(""));

/** Base visuals — verbatim from nicolify visuals schema fields. */
export const visualsSchema = z.object({
  primary_color: hexColor,
  secondary_color: hexColor,
  accent_color: hexColor,
  background_color: hexColor,
  surface_color: hexColor,
  text_primary_color: hexColor,
  text_secondary_color: hexColor,
  font_heading: z.string().max(100, "Máximo 100 caracteres").optional(),
  font_body: z.string().max(100, "Máximo 100 caracteres").optional(),
  font_accent: z.string().max(100, "Máximo 100 caracteres").optional(),
  design_style: z.string().max(200, "Máximo 200 caracteres").optional(),
  photography_style: z.string().max(500, "Máximo 500 caracteres").optional(),
  icon_style: z.string().max(100, "Máximo 100 caracteres").optional(),
  visual_references: z.string().max(1000, "Máximo 1000 caracteres").optional(),
  logo_url: optionalUrl,
  favicon_url: optionalUrl,
});

/** Salud overlay: ClinicBrandVisuals extends base visuals. D4-extract: stub fields. */
export const clinicVisualsSchema = visualsSchema.extend({
  /**
   * D4-extract STUB: visual extraction from URL.
   * Pipeline disabled until /pm-luana accepts proposal 2026-05-26-lift-brand-visual-extraction-to-core.
   * Extract button is disabled with tooltip "Próximamente — extracción automática".
   */
  extract_from_url_stub: z
    .string()
    .url("Ingresa una URL válida")
    .optional()
    .or(z.literal("")),
});

export type VisualsFormValues = z.infer<typeof visualsSchema>;
export type ClinicVisualsFormValues = z.infer<typeof clinicVisualsSchema>;
