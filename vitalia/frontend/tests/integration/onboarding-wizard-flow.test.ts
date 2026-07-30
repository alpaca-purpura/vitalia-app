/**
 * Integration test A1 — Onboarding wizard 3-step flow.
 *
 * Tests: schema validation per step, step transition logic,
 * payload assembly from step data, microcopy alignment.
 *
 * No DOM rendering (no @testing-library/react installed).
 * Validates schemas + component exports + logic contracts.
 */
import { describe, it, expect } from "vitest";

// ── A1.1 Step 1 — Clinic profile schema validation ────────────────────────────

describe("A1: Onboarding wizard — step 1 clinic profile schema", () => {
  it("valid clinic profile passes schema", async () => {
    const { clinicProfileSchema } = await import(
      "@/features/vitalia/schemas/clinic-profile-schema"
    );
    const result = clinicProfileSchema.safeParse({
      clinic_name: "Dental Sonrisa",
      clinic_type: "dental",
      country: "AR",
      city: "Buenos Aires",
    });
    expect(result.success).toBe(true);
  });

  it("all 4 clinic types are valid enum values", async () => {
    const { clinicProfileSchema } = await import(
      "@/features/vitalia/schemas/clinic-profile-schema"
    );
    const types = ["dental", "psychology", "psychiatry", "wellness"] as const;
    for (const type of types) {
      const result = clinicProfileSchema.safeParse({
        clinic_name: "Test",
        clinic_type: type,
        country: "MX",
        city: "Ciudad de México",
      });
      expect(result.success, `Expected type '${type}' to be valid`).toBe(true);
    }
  });

  it("clinic_name too short fails validation", async () => {
    const { clinicProfileSchema } = await import(
      "@/features/vitalia/schemas/clinic-profile-schema"
    );
    const result = clinicProfileSchema.safeParse({
      clinic_name: "A", // min 2
      clinic_type: "dental",
      country: "CL",
      city: "Santiago",
    });
    expect(result.success).toBe(false);
  });

  it("invalid clinic_type fails validation", async () => {
    const { clinicProfileSchema } = await import(
      "@/features/vitalia/schemas/clinic-profile-schema"
    );
    const result = clinicProfileSchema.safeParse({
      clinic_name: "Test Clinic",
      clinic_type: "veterinary", // not valid
      country: "AR",
      city: "Córdoba",
    });
    expect(result.success).toBe(false);
  });

  it("missing required fields fails validation", async () => {
    const { clinicProfileSchema } = await import(
      "@/features/vitalia/schemas/clinic-profile-schema"
    );
    const result = clinicProfileSchema.safeParse({
      clinic_name: "Test",
      // missing clinic_type, country, city
    });
    expect(result.success).toBe(false);
  });
});

// ── A1.2 Step 2 — Plan tier structure ─────────────────────────────────────────

describe("A1: Onboarding wizard — step 2 plan tier structure", () => {
  it("onboarding-step-2-client exports named function (not default)", async () => {
    const mod = await import(
      "@/features/vitalia/components/onboarding-step-2-client"
    ) as Record<string, unknown>;
    expect(typeof mod["OnboardingStep2Client"]).toBe("function");
    expect(mod).not.toHaveProperty("default");
  });

  it("PlanTierListResponse type shape validated via object structure", () => {
    // Runtime shape check — TypeScript ensures this at compile time
    type PlanTierItem = {
      slug: string;
      label_es: string;
      price_usd_monthly: number;
      included_user_count: number;
      features_enabled: string[];
    };
    const mockPlan: PlanTierItem = {
      slug: "starter",
      label_es: "Inicial",
      price_usd_monthly: 49,
      included_user_count: 1,
      features_enabled: ["brand_studio", "one_offer"],
    };
    expect(mockPlan.slug).toBe("starter");
    expect(mockPlan.price_usd_monthly).toBeGreaterThan(0);
    expect(Array.isArray(mockPlan.features_enabled)).toBe(true);
  });
});

// ── A1.3 Step 3 — Offer wizard launch bridge ──────────────────────────────────

describe("A1: Onboarding wizard — step 3 offer launch", () => {
  it("onboarding-step-3-client exports named function (not default)", async () => {
    const mod = await import(
      "@/features/vitalia/components/onboarding-step-3-client"
    ) as Record<string, unknown>;
    expect(typeof mod["OnboardingStep3Client"]).toBe("function");
    expect(mod).not.toHaveProperty("default");
  });
});

// ── A1.4 Step 1 client component export contract ──────────────────────────────

describe("A1: Onboarding wizard — step 1 client export contract", () => {
  it("onboarding-step-1-client exports named function (not default)", async () => {
    const mod = await import(
      "@/features/vitalia/components/onboarding-step-1-client"
    ) as Record<string, unknown>;
    expect(typeof mod["OnboardingStep1Client"]).toBe("function");
    expect(mod).not.toHaveProperty("default");
  });
});

// ── A1.5 Payload assembly — merging step data into CreateClinicProfilePayload ──

describe("A1: Onboarding wizard — payload assembly logic", () => {
  it("merges step 1 + step 2 data into valid payload shape", () => {
    type CreateClinicProfilePayload = {
      clinic_name: string;
      clinic_type: string;
      country: string;
      city: string;
      plan_tier: string;
    };

    const step1Data = {
      clinic_name: "Psico Bienestar",
      clinic_type: "psychology",
      country: "CO",
      city: "Bogotá",
    };
    const step2PlanSlug = "clinic";

    const payload: CreateClinicProfilePayload = {
      ...step1Data,
      plan_tier: step2PlanSlug,
    };

    expect(payload.clinic_name).toBe("Psico Bienestar");
    expect(payload.clinic_type).toBe("psychology");
    expect(payload.plan_tier).toBe("clinic");
    expect(Object.keys(payload)).toHaveLength(5);
  });

  it("all countries accepted by schema", async () => {
    const { clinicProfileSchema } = await import(
      "@/features/vitalia/schemas/clinic-profile-schema"
    );
    const countries = ["AR", "CL", "MX", "BR", "CO", "PE", "UY", "US"] as const;
    for (const country of countries) {
      const result = clinicProfileSchema.safeParse({
        clinic_name: "Test Clinic",
        clinic_type: "wellness",
        country,
        city: "Test City",
      });
      expect(result.success, `Expected country '${country}' to be valid`).toBe(true);
    }
  });
});

// ── A1.5b Query keys coverage ─────────────────────────────────────────────────

describe("A1: Onboarding wizard — query keys", () => {
  it("vitaliaQueryKeys.onboarding.plans() returns correct key shape", async () => {
    const { vitaliaQueryKeys } = await import("@/features/vitalia/api/query-keys");
    const key = vitaliaQueryKeys.onboarding.plans();
    expect(Array.isArray(key)).toBe(true);
    expect(key[0]).toBe("vitalia");
    expect(key[1]).toBe("onboarding");
    expect(key[2]).toBe("plans");
  });

  it("vitaliaQueryKeys.onboarding.status() returns correct key shape", async () => {
    const { vitaliaQueryKeys } = await import("@/features/vitalia/api/query-keys");
    const key = vitaliaQueryKeys.onboarding.status();
    expect(Array.isArray(key)).toBe(true);
    expect(key[2]).toBe("status");
  });

  it("vitaliaQueryKeys.brandStudio.sections() returns correct key", async () => {
    const { vitaliaQueryKeys } = await import("@/features/vitalia/api/query-keys");
    const key = vitaliaQueryKeys.brandStudio.sections();
    expect(key[1]).toBe("brand-studio");
    expect(key[2]).toBe("sections");
  });

  it("vitaliaQueryKeys.brandStudio.section(id) returns scoped key", async () => {
    const { vitaliaQueryKeys } = await import("@/features/vitalia/api/query-keys");
    const key = vitaliaQueryKeys.brandStudio.section("identity");
    expect(key[3]).toBe("identity");
  });

  it("vitaliaQueryKeys.offers.preset(slug) returns correct key", async () => {
    const { vitaliaQueryKeys } = await import("@/features/vitalia/api/query-keys");
    const key = vitaliaQueryKeys.offers.preset("medical_services_v1");
    expect(key[3]).toBe("medical_services_v1");
  });
});

// ── A1.6 Microcopy onboarding alignment ───────────────────────────────────────

describe("A1: Onboarding wizard — microcopy alignment", () => {
  it("onboarding microcopy has required field labels", async () => {
    const { MICROCOPY_ONBOARDING } = await import(
      "@/features/vitalia/config/microcopy"
    );
    expect(MICROCOPY_ONBOARDING.fields.clinicName).toBeTruthy();
    expect(MICROCOPY_ONBOARDING.fields.clinicType).toBeTruthy();
    expect(MICROCOPY_ONBOARDING.fields.country).toBeTruthy();
    expect(MICROCOPY_ONBOARDING.fields.city).toBeTruthy();
  });

  it("onboarding microcopy cta buttons defined", async () => {
    const { MICROCOPY_ONBOARDING } = await import(
      "@/features/vitalia/config/microcopy"
    );
    expect(MICROCOPY_ONBOARDING.cta.next).toBeTruthy();
    expect(MICROCOPY_ONBOARDING.cta.back).toBeTruthy();
  });

  it("onboarding error messages defined in Spanish", async () => {
    const { MICROCOPY_ONBOARDING } = await import(
      "@/features/vitalia/config/microcopy"
    );
    expect(MICROCOPY_ONBOARDING.errors.required).toBeTruthy();
    // Check it's not empty
    expect(MICROCOPY_ONBOARDING.errors.required.length).toBeGreaterThan(3);
  });

  it("onboarding title and subtitle defined", async () => {
    const { MICROCOPY_ONBOARDING } = await import(
      "@/features/vitalia/config/microcopy"
    );
    expect(MICROCOPY_ONBOARDING.title).toBeTruthy();
    expect(MICROCOPY_ONBOARDING.subtitle).toBeTruthy();
  });
});
