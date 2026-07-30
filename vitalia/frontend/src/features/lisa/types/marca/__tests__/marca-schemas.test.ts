// voseo-allowed: test fixture detects voseo patterns in error messages (spanish-text.md § Magic comment escape)
/**
 * marca-schemas.test.ts — Vitest unit tests for Lisa Marca Zod schemas.
 *
 * T-8 vitalia-fase2-lisa-marca (VALIDATORS: fe_test_zod_schemas)
 * Tests:
 *   1. identitySchema — required fields, URL, founding_year
 *   2. contactSchema — email, URL fields
 *   3. visualsSchema — hex color, URL
 *   4. teamMemberItemSchema — required fields
 *   5. testimonialItemSchema — rating bounds, date format
 *   6. personalitySchema — 4 archetypes ONLY (A-FE arch test)
 *   7. prohibitedPhraseSchema — severity enum
 *   8. trustSignalsSchema — country_code, years bounds
 *   9. presenceSchema — URL, social media
 *   10. voicePreviewSchema — UUID, hash
 *   11. Spanish neutro — no voseo in error messages (A-FE arch test)
 *
 * spec_anchor: 04-validators.yaml fe_test_zod_schemas + fe_arch_test_personality_schema_4_archetypes
 * downstream-regression-na: brand-local vitalia FE tests; no cross-brand consumers
 */

import { describe, it, expect } from "vitest";
import {
  identitySchema,
  contactSchema,
  visualsSchema,
  teamMemberItemSchema,
  testimonialItemSchema,
  personalitySchema,
  prohibitedPhraseSchema,
  trustSignalsSchema,
  presenceSchema,
  voicePreviewRequestSchema,
  voicePreviewResponseSchema,
  SALUD_ARCHETYPES,
} from "../index";

// ── identitySchema ─────────────────────────────────────────────────────────────
describe("identitySchema", () => {
  it("passes with valid minimal data", () => {
    const result = identitySchema.safeParse({ brand_name: "Clínica Lima" });
    expect(result.success).toBe(true);
  });

  it("fails when brand_name is empty", () => {
    const result = identitySchema.safeParse({ brand_name: "" });
    expect(result.success).toBe(false);
  });

  it("passes with valid website URL", () => {
    const result = identitySchema.safeParse({
      brand_name: "Clínica Lima",
      website: "https://clinicalima.pe",
    });
    expect(result.success).toBe(true);
  });

  it("fails with invalid website URL", () => {
    const result = identitySchema.safeParse({
      brand_name: "Clínica Lima",
      website: "not-a-url",
    });
    expect(result.success).toBe(false);
  });

  it("passes with empty website (optional field)", () => {
    const result = identitySchema.safeParse({
      brand_name: "Clínica Lima",
      website: "",
    });
    expect(result.success).toBe(true);
  });

  it("fails with invalid founding_year format", () => {
    const result = identitySchema.safeParse({
      brand_name: "Clínica Lima",
      founding_year: "año 2020",
    });
    expect(result.success).toBe(false);
  });

  it("passes with valid founding_year", () => {
    const result = identitySchema.safeParse({
      brand_name: "Clínica Lima",
      founding_year: "2018",
    });
    expect(result.success).toBe(true);
  });
});

// ── contactSchema ──────────────────────────────────────────────────────────────
describe("contactSchema", () => {
  it("passes with all optional empty", () => {
    const result = contactSchema.safeParse({});
    expect(result.success).toBe(true);
  });

  it("fails with invalid support_email", () => {
    const result = contactSchema.safeParse({ support_email: "not-an-email" });
    expect(result.success).toBe(false);
  });

  it("passes with valid support_email", () => {
    const result = contactSchema.safeParse({
      support_email: "soporte@clinica.pe",
    });
    expect(result.success).toBe(true);
  });

  it("fails with invalid social_linkedin URL", () => {
    const result = contactSchema.safeParse({
      social_linkedin: "linkedin/perfil",
    });
    expect(result.success).toBe(false);
  });
});

// ── visualsSchema ──────────────────────────────────────────────────────────────
describe("visualsSchema", () => {
  it("passes with empty data (all optional)", () => {
    const result = visualsSchema.safeParse({});
    expect(result.success).toBe(true);
  });

  it("passes with valid hex color", () => {
    const result = visualsSchema.safeParse({ primary_color: "#01B2F8" });
    expect(result.success).toBe(true);
  });

  it("fails with invalid hex color", () => {
    const result = visualsSchema.safeParse({ primary_color: "azul" });
    expect(result.success).toBe(false);
  });

  it("passes with valid logo_url", () => {
    const result = visualsSchema.safeParse({
      logo_url: "https://cdn.clinica.pe/logo.png",
    });
    expect(result.success).toBe(true);
  });
});

// ── teamMemberItemSchema ───────────────────────────────────────────────────────
describe("teamMemberItemSchema", () => {
  it("passes with minimal required name", () => {
    const result = teamMemberItemSchema.safeParse({ name: "Dr. Carlos Ríos" });
    expect(result.success).toBe(true);
  });

  it("fails when name is missing", () => {
    const result = teamMemberItemSchema.safeParse({});
    expect(result.success).toBe(false);
  });

  it("passes with gallery array", () => {
    const result = teamMemberItemSchema.safeParse({
      name: "Dra. Ana Torres",
      gallery: [{ value: "https://cdn.clinica.pe/foto.jpg" }],
    });
    expect(result.success).toBe(true);
  });
});

// ── testimonialItemSchema ──────────────────────────────────────────────────────
describe("testimonialItemSchema", () => {
  it("passes with minimal author_name", () => {
    const result = testimonialItemSchema.safeParse({
      author_name: "Paciente Satisfecha",
    });
    expect(result.success).toBe(true);
  });

  it("fails with rating > 5", () => {
    const result = testimonialItemSchema.safeParse({
      author_name: "Test",
      rating: 6,
    });
    expect(result.success).toBe(false);
  });

  it("fails with rating < 1", () => {
    const result = testimonialItemSchema.safeParse({
      author_name: "Test",
      rating: 0,
    });
    expect(result.success).toBe(false);
  });

  it("fails with invalid captured_at date format", () => {
    const result = testimonialItemSchema.safeParse({
      author_name: "Test",
      captured_at: "01/06/2024",
    });
    expect(result.success).toBe(false);
  });

  it("passes with valid captured_at", () => {
    const result = testimonialItemSchema.safeParse({
      author_name: "Test",
      captured_at: "2024-06-01",
    });
    expect(result.success).toBe(true);
  });
});

// ── personalitySchema — arch gate: 4 archetypes only ─────────────────────────
describe("personalitySchema (salud overlay — fe_arch_test_personality_schema_4_archetypes)", () => {
  it("SALUD_ARCHETYPES contains exactly 4 entries", () => {
    expect(SALUD_ARCHETYPES.length).toBe(4);
  });

  it("SALUD_ARCHETYPES contains caregiver, sage, healer, hero", () => {
    expect(SALUD_ARCHETYPES).toContain("caregiver");
    expect(SALUD_ARCHETYPES).toContain("sage");
    expect(SALUD_ARCHETYPES).toContain("healer");
    expect(SALUD_ARCHETYPES).toContain("hero");
  });

  it("SALUD_ARCHETYPES does NOT contain outlaw, magician, lover, innocent", () => {
    const forbidden = ["outlaw", "magician", "lover", "innocent"];
    for (const arch of forbidden) {
      expect(SALUD_ARCHETYPES).not.toContain(arch);
    }
  });

  it("passes with valid caregiver archetype (default)", () => {
    const result = personalitySchema.safeParse({ archetype: "caregiver" });
    expect(result.success).toBe(true);
  });

  it("passes with all 4 valid archetypes", () => {
    for (const arch of SALUD_ARCHETYPES) {
      const result = personalitySchema.safeParse({ archetype: arch });
      expect(result.success).toBe(true);
    }
  });

  it("fails with non-salud archetype (rebel/outlaw/magician)", () => {
    const forbidden = ["rebel", "outlaw", "magician", "lover", "innocent", "everyman", "explorer", "creator", "ruler", "jester"];
    for (const arch of forbidden) {
      const result = personalitySchema.safeParse({ archetype: arch });
      expect(result.success).toBe(false);
    }
  });

  it("passes with valid voice_blocks", () => {
    const result = personalitySchema.safeParse({
      archetype: "sage",
      voice_blocks: {
        identity: "Somos especialistas en salud integral",
        asi_hablo: "Con calidez y claridad técnica",
        asi_no_hablo: "Sin jerga incomprensible ni frialdad",
      },
    });
    expect(result.success).toBe(true);
  });
});

// ── prohibitedPhraseSchema ─────────────────────────────────────────────────────
describe("prohibitedPhraseSchema", () => {
  it("passes with phrase + severity warning", () => {
    const result = prohibitedPhraseSchema.safeParse({
      phrase: "te garantizamos que te curas",
      severity: "warning",
    });
    expect(result.success).toBe(true);
  });

  it("passes with suggested_alternative as null", () => {
    const result = prohibitedPhraseSchema.safeParse({
      phrase: "cura segura",
      suggested_alternative: null,
      severity: "block",
    });
    expect(result.success).toBe(true);
  });

  it("fails when phrase is empty", () => {
    const result = prohibitedPhraseSchema.safeParse({
      phrase: "",
      severity: "warning",
    });
    expect(result.success).toBe(false);
  });

  it("fails with invalid severity", () => {
    const result = prohibitedPhraseSchema.safeParse({
      phrase: "ejemplo",
      severity: "critical",
    });
    expect(result.success).toBe(false);
  });
});

// ── trustSignalsSchema ─────────────────────────────────────────────────────────
describe("trustSignalsSchema", () => {
  it("passes with empty data (all optional)", () => {
    const result = trustSignalsSchema.safeParse({});
    expect(result.success).toBe(true);
  });

  it("passes with valid certifications array", () => {
    const result = trustSignalsSchema.safeParse({
      certifications: [
        { country_code: "PE", cert_code: "MINSA-GCL-001", custom_label: "Registro Sanitario MINSA" },
      ],
    });
    expect(result.success).toBe(true);
  });

  it("fails with invalid country_code (lowercase)", () => {
    const result = trustSignalsSchema.safeParse({
      certifications: [{ country_code: "pe", cert_code: "MINSA-001" }],
    });
    expect(result.success).toBe(false);
  });

  it("fails with negative years_experience", () => {
    const result = trustSignalsSchema.safeParse({ years_experience: -1 });
    expect(result.success).toBe(false);
  });

  it("passes with valid years_experience", () => {
    const result = trustSignalsSchema.safeParse({ years_experience: 15 });
    expect(result.success).toBe(true);
  });
});

// ── presenceSchema ─────────────────────────────────────────────────────────────
describe("presenceSchema", () => {
  it("passes with empty data (all optional)", () => {
    const result = presenceSchema.safeParse({});
    expect(result.success).toBe(true);
  });

  it("passes with valid website_url", () => {
    const result = presenceSchema.safeParse({
      website_url: "https://clinica-lima.pe",
    });
    expect(result.success).toBe(true);
  });

  it("fails with invalid website_url", () => {
    const result = presenceSchema.safeParse({ website_url: "clinica-lima" });
    expect(result.success).toBe(false);
  });

  it("passes with social_media object", () => {
    const result = presenceSchema.safeParse({
      social_media: {
        instagram: "clinicalima",
        tiktok: "@clinicalima",
        google_business: "https://g.page/clinicalima",
      },
    });
    expect(result.success).toBe(true);
  });

  it("passes with locations array", () => {
    const result = presenceSchema.safeParse({
      locations: [
        { name: "Sede Miraflores", address: "Av. Larco 1234, Miraflores, Lima" },
      ],
    });
    expect(result.success).toBe(true);
  });

  it("fails when location name is empty", () => {
    const result = presenceSchema.safeParse({
      locations: [{ name: "", address: "Av. Larco 1234" }],
    });
    expect(result.success).toBe(false);
  });
});

// ── voicePreviewSchema ─────────────────────────────────────────────────────────
describe("voicePreviewRequestSchema", () => {
  it("passes with valid UUIDs and hash", () => {
    const result = voicePreviewRequestSchema.safeParse({
      tenant_id: "550e8400-e29b-41d4-a716-446655440000",
      profile_id: "550e8400-e29b-41d4-a716-446655440001",
      blocks_hash: "abc123def456",
    });
    expect(result.success).toBe(true);
  });

  it("fails with non-UUID tenant_id", () => {
    const result = voicePreviewRequestSchema.safeParse({
      tenant_id: "not-a-uuid",
      profile_id: "550e8400-e29b-41d4-a716-446655440001",
      blocks_hash: "abc123",
    });
    expect(result.success).toBe(false);
  });
});

describe("voicePreviewResponseSchema", () => {
  it("passes with sample strings", () => {
    const result = voicePreviewResponseSchema.safeParse({
      whatsapp_cobranza_sample: "Hola, te recuerdo que tienes una cita mañana.",
      email_reactivacion_sample: "Estimado paciente, ha pasado un tiempo...",
    });
    expect(result.success).toBe(true);
  });
});

// ── Spanish neutro — no voseo in error messages ────────────────────────────────
describe("Spanish neutro error messages (fe_test_schemas_messages_spanish_neutro)", () => {
  const voseoPatterns = [
    /configurá/,
    /agregá/,
    /revisá/,
    /guardá/,
    /escribí/,
    /tenés/,
    /podés/,
    /querés/,
    /hacés/,
  ];

  function extractErrorMessages(schema: { safeParse: (v: unknown) => { success: boolean; error?: { issues: Array<{ message: string }> } } }, input: unknown): string[] {
    const result = schema.safeParse(input);
    if (result.success || !result.error) return [];
    return result.error.issues.map((e) => e.message);
  }

  it("identitySchema error messages have no voseo", () => {
    const msgs = extractErrorMessages(identitySchema, { brand_name: "", website: "bad-url" });
    for (const msg of msgs) {
      for (const pattern of voseoPatterns) {
        expect(msg).not.toMatch(pattern);
      }
    }
  });

  it("personalitySchema error messages have no voseo", () => {
    const msgs = extractErrorMessages(personalitySchema, { archetype: "rebel" });
    for (const msg of msgs) {
      for (const pattern of voseoPatterns) {
        expect(msg).not.toMatch(pattern);
      }
    }
  });

  it("presenceSchema error messages have no voseo", () => {
    const msgs = extractErrorMessages(presenceSchema, { website_url: "bad" });
    for (const msg of msgs) {
      for (const pattern of voseoPatterns) {
        expect(msg).not.toMatch(pattern);
      }
    }
  });

  it("trustSignalsSchema error messages have no voseo", () => {
    const msgs = extractErrorMessages(trustSignalsSchema, { years_experience: -5 });
    for (const msg of msgs) {
      for (const pattern of voseoPatterns) {
        expect(msg).not.toMatch(pattern);
      }
    }
  });
});

// ── fe_arch_test_no_phi_in_schemas ────────────────────────────────────────────
describe("fe_arch_test_no_phi_in_schemas (no PHI field names)", () => {
  const phiFieldNames = [
    "patient_dni",
    "patient_id",
    "diagnosis",
    "treatment_plan",
    "medication",
    "dosage",
    "allergies",
    "symptoms",
    "medical_notes",
    "lab_results",
    "vital_signs",
    "imaging_url",
  ];

  function schemaKeys(schema: { _def?: { shape?: Record<string, unknown> } }): string[] {
    if (schema._def?.shape) {
      return Object.keys(schema._def.shape);
    }
    return [];
  }

  it("identitySchema has no PHI field names", () => {
    const keys = schemaKeys(identitySchema);
    for (const phi of phiFieldNames) {
      expect(keys).not.toContain(phi);
    }
  });

  it("personalitySchema has no PHI field names", () => {
    const keys = schemaKeys(personalitySchema);
    for (const phi of phiFieldNames) {
      expect(keys).not.toContain(phi);
    }
  });

  it("presenceSchema has no PHI field names", () => {
    const keys = schemaKeys(presenceSchema);
    for (const phi of phiFieldNames) {
      expect(keys).not.toContain(phi);
    }
  });
});
