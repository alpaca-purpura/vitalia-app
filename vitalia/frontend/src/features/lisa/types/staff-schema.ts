// cap: clinics.lisa.doctores
// story-origin: vitalia-fase2-lisa-doctores
/**
 * staff-schema.ts — Zod schemas for NuevoIntegrante form + availability block forms.
 *
 * NuevoIntegranteModal is submit-driven (atomic create — one exception to autosave).
 * Credential validation is country-specific:
 *   PE: CMP — numeric only
 *   AR: Matrícula nacional — alphanumeric
 *   MX: Cédula profesional — alphanumeric
 *   CL: Registro nacional — alphanumeric
 *
 * T-FE-1 vitalia-fase2-lisa-doctores
 * spec_anchor: 03-arch-fe.md § Forms + 01-spec.md § Business rules credential-validator-country-specific
 * downstream-regression-na: brand-local vitalia FE schema; no cross-brand consumers
 */

import { z } from "zod";

// ── Country-specific credential validators ─────────────────────────────────────

/**
 * Credential validation per country (mirrors backend credential_validator.py).
 * PE: CMP numeric only. AR/MX/CL: alphanumeric.
 */
function credentialRefinement(country: string, credential: string): boolean {
  if (!credential) return true; // Required check handled separately
  switch (country) {
    case "PE":
      return /^\d+$/.test(credential);
    case "AR":
    case "MX":
    case "CL":
      return /^[A-Za-z0-9\s-]+$/.test(credential);
    default:
      return true;
  }
}

function credentialErrorMessage(country: string): string {
  switch (country) {
    case "PE":
      return "La credencial CMP debe ser numérica";
    case "AR":
      return "La matrícula debe contener solo letras, números o guiones";
    case "MX":
      return "La cédula profesional debe contener solo letras, números o guiones";
    case "CL":
      return "El registro nacional debe contener solo letras, números o guiones";
    default:
      return "Credencial inválida";
  }
}

// ── Doctor create schema (NuevoIntegranteModal — submit-driven) ────────────────

export const doctorCreateSchema = z
  .object({
    firstName: z
      .string()
      .min(1, "El nombre es requerido")
      .max(100, "Máximo 100 caracteres"),
    lastName: z
      .string()
      .min(1, "El apellido es requerido")
      .max(100, "Máximo 100 caracteres"),
    dni: z
      .string()
      .min(1, "El documento es requerido")
      .max(20, "Máximo 20 caracteres"),
    email: z
      .string()
      .email("Correo electrónico inválido")
      .max(200, "Máximo 200 caracteres"),
    phone: z
      .string()
      .max(30, "Máximo 30 caracteres")
      .optional()
      .or(z.literal("")),
    specialty: z
      .string()
      .max(100, "Máximo 100 caracteres")
      .optional()
      .or(z.literal("")),
    credential: z
      .string()
      .min(1, "La credencial es requerida")
      .max(50, "Máximo 50 caracteres"),
    credentialCountry: z.enum(["PE", "AR", "MX", "CL"]),
    active: z.boolean(),
  })
  .superRefine((data, ctx) => {
    if (!credentialRefinement(data.credentialCountry, data.credential)) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: credentialErrorMessage(data.credentialCountry),
        path: ["credential"],
      });
    }
  });

export type DoctorCreateFormValues = z.infer<typeof doctorCreateSchema>;

// ── Bio schema (autosave patch) ────────────────────────────────────────────────

export const bioSchema = z.object({
  bioInputsNotes: z.string().max(5000, "Máximo 5000 caracteres").optional(),
  bioLinks: z.array(z.string().url("URL inválida")).max(20),
  bioPublicResumen: z
    .string()
    .max(2000, "Máximo 2000 caracteres")
    .optional()
    .or(z.literal("")),
  bioPublicFormacion: z
    .string()
    .max(2000, "Máximo 2000 caracteres")
    .optional()
    .or(z.literal("")),
  bioPublicEnfoque: z
    .string()
    .max(2000, "Máximo 2000 caracteres")
    .optional()
    .or(z.literal("")),
});

export type BioFormValues = z.infer<typeof bioSchema>;

// ── Availability block schema (recurrent vs one-off — discriminated union) ─────
//
// D3-F: RepeatPreset drives the Select "Repetir":
//   "none"      → kind: one_off (crear bloque puntual desde recurrente)
//   "daily"     → daysOfWeek: [0,1,2,3,4,5,6], interval: 1
//   "weekly"    → daysOfWeek: [dayOfWeek from draft], interval: 1
//   "biweekly"  → daysOfWeek: [dayOfWeek from draft], interval: 2
//   "custom"    → user configures daysOfWeek[] + interval via sub-editor
//
// Human summary (formatRecurrenceSummary) derives from daysOfWeek + interval + endConditionKind.

export type RepeatPreset = "none" | "daily" | "weekly" | "biweekly" | "custom";

const recurrentBlockSchema = z
  .object({
    kind: z.literal("recurrent"),
    /** D3-F: repeat preset driving the Select "Repetir" */
    repeatPreset: z.enum(["none", "daily", "weekly", "biweekly", "custom"]),
    /** D3-F: list of weekday indices — 0=Monday..6=Sunday (min 1 element) */
    daysOfWeek: z
      .array(z.number().int().min(0).max(6))
      .min(1, "Selecciona al menos un día"),
    /** D3-F: recurrence interval in weeks (≥1) */
    interval: z.number().int().min(1, "El intervalo debe ser al menos 1"),
    startTime: z
      .string()
      .regex(/^\d{2}:\d{2}$/, "Formato inválido (HH:mm)"),
    endTime: z
      .string()
      .regex(/^\d{2}:\d{2}$/, "Formato inválido (HH:mm)"),
    endConditionKind: z.enum(["end_date", "occurrences", "open_ended"]),
    endDate: z.string().optional().nullable(),
    occurrences: z.number().int().min(1).optional().nullable(),
  })
  .superRefine((data, ctx) => {
    if (data.endConditionKind === "end_date" && !data.endDate) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "Selecciona una fecha de fin",
        path: ["endDate"],
      });
    }
    if (data.endConditionKind === "occurrences" && !data.occurrences) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "Ingresa el número de repeticiones",
        path: ["occurrences"],
      });
    }
    if (data.repeatPreset === "custom" && data.daysOfWeek.length === 0) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "Selecciona al menos un día",
        path: ["daysOfWeek"],
      });
    }
  });

const oneOffBlockSchema = z.object({
  kind: z.literal("one_off"),
  specificDate: z.string().min(1, "Selecciona una fecha"),
  startTime: z
    .string()
    .regex(/^\d{2}:\d{2}$/, "Formato inválido (HH:mm)"),
  endTime: z
    .string()
    .regex(/^\d{2}:\d{2}$/, "Formato inválido (HH:mm)"),
});

export const availabilityBlockSchema = z.discriminatedUnion("kind", [
  recurrentBlockSchema,
  oneOffBlockSchema,
]);

export type AvailabilityBlockFormValues = z.infer<
  typeof availabilityBlockSchema
>;

// ── Doctor perfil autosave schema (T-FE-2) ──────────────────────────────────

export const doctorPerfilSchema = z.object({
  specialty: z.string().max(100, "Máximo 100 caracteres").optional().or(z.literal("")),
  phone: z.string().max(30, "Máximo 30 caracteres").optional().or(z.literal("")),
  yearsExperience: z
    .string()
    .regex(/^\d*$/, "Debe ser un número")
    .optional()
    .or(z.literal("")),
  languages: z.string().max(200, "Máximo 200 caracteres").optional().or(z.literal("")),
  visibleEnLanding: z.boolean(),
});

export type DoctorPerfilFormValues = z.infer<typeof doctorPerfilSchema>;
