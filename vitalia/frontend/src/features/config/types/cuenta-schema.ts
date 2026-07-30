// cap: configuracion.cuenta
// story-origin: vitalia-fase2-config-cuenta
/**
 * cuenta-schema.ts — Zod validation schemas for config/cuenta forms.
 *
 * Client-side validation (UX preview). Backend is authoritative.
 * Includes fiscal-id format validators per country (preview only; BE validates final).
 *
 * T-1 vitalia-fase2-config-cuenta
 * spec_anchor: 03-arch.md § 5 + 03-arch.md § § Open Questions (fiscal validator)
 * downstream-regression-na: brand-local vitalia FE schema; no cross-brand consumers
 */

import { z } from "zod";

// ── Fiscal ID client-side format validators (UX preview — BE is authoritative) ─
// Reference: 03-arch.md § Open Questions + § § 7 (_shared/validation/fiscal_id_validator.py)

/** CUIT Argentina: 11 digits (no dashes in validation — accept with or without dashes) */
const CUIT_REGEX = /^\d{2}-?\d{8}-?\d{1}$/;
/** RUC Perú: 11 digits */
const RUC_REGEX = /^\d{11}$/;
/** RFC México: 12-13 alphanumeric */
const RFC_REGEX = /^[A-Z&Ñ]{3,4}[0-9]{6}[A-Z0-9]{3}$/i;
/** RUT Chile: 8-9 digits with optional verifier */
const RUT_CL_REGEX = /^\d{7,8}-?[0-9Kk]$/;
/** NIT Colombia: 9 digits with optional verifier */
const NIT_CO_REGEX = /^\d{9}-?\d{1}$/;
/** RUT Uruguay: 12 digits */
const RUT_UY_REGEX = /^\d{12}$/;

/**
 * Returns a fiscal ID validator for the given country.
 * Falls back to freetext (no format validation) for unsupported countries.
 */
function fiscalIdValidatorForCountry(country: string) {
  switch (country.toUpperCase()) {
    case "AR":
      return z
        .string()
        .regex(CUIT_REGEX, "El CUIT debe tener 11 dígitos (ej. 20-12345678-0)");
    case "PE":
      return z
        .string()
        .regex(RUC_REGEX, "El RUC debe tener 11 dígitos");
    case "MX":
      return z
        .string()
        .regex(RFC_REGEX, "El RFC debe tener 12 o 13 caracteres alfanuméricos");
    case "CL":
      return z
        .string()
        .regex(RUT_CL_REGEX, "El RUT debe tener 7 u 8 dígitos más dígito verificador");
    case "CO":
      return z
        .string()
        .regex(NIT_CO_REGEX, "El NIT debe tener 9 dígitos más dígito verificador");
    case "UY":
      return z
        .string()
        .regex(RUT_UY_REGEX, "El RUT debe tener 12 dígitos");
    default:
      // Freetext for unsupported countries — backend validates
      return z.string();
  }
}

// ── Account data form schema (datos sub-sub-tab) ──────────────────────────────

export const accountDataSchema = z.object({
  name: z
    .string()
    .min(1, "El nombre comercial es requerido")
    .max(200, "Máximo 200 caracteres"),
  legalName: z.string().max(300, "Máximo 300 caracteres").optional().nullable(),
  /** fiscal_id: validated by country — see SpecialtiesField+component passes country */
  fiscalId: z.string().optional().nullable(),
  address: z.string().max(500, "Máximo 500 caracteres").optional().nullable(),
  phone: z
    .string()
    .max(50, "Máximo 50 caracteres")
    .optional()
    .nullable(),
  email: z
    .string()
    .email("Correo electrónico no válido")
    .max(254, "Máximo 254 caracteres")
    .optional()
    .nullable(),
  primarySpecialties: z.array(z.string()).optional(),
});

export type AccountDataFormValues = z.infer<typeof accountDataSchema>;

// ── Preferences form schema (preferencias sub-sub-tab) ────────────────────────

export const accountPrefsSchema = z.object({
  currency: z.string().length(3, "El código de moneda debe tener 3 letras ISO 4217").optional().nullable(),
  timezone: z.string().min(1, "La zona horaria es requerida"),
});

export type AccountPrefsFormValues = z.infer<typeof accountPrefsSchema>;

// ── Combined PATCH payload schema ─────────────────────────────────────────────

export const accountPatchSchema = z.object({
  name: z.string().min(1).max(200).optional(),
  legalName: z.string().max(300).optional().nullable(),
  fiscalId: z.string().optional().nullable(),
  address: z.string().max(500).optional().nullable(),
  phone: z.string().max(50).optional().nullable(),
  email: z.string().email().max(254).optional().nullable(),
  currency: z.string().length(3).optional().nullable(),
  timezone: z.string().min(1).optional(),
  primarySpecialties: z.array(z.string()).optional(),
});

export type AccountPatchFormValues = z.infer<typeof accountPatchSchema>;

// Export the country-specific validator for use in AccountDataView
export { fiscalIdValidatorForCountry };
