import { describe, it, expect } from "vitest";
import { clinicProfileSchema } from "@/features/vitalia/schemas/clinic-profile-schema";

describe("clinicProfileSchema", () => {
  it("accepts valid clinic profile input", () => {
    const result = clinicProfileSchema.safeParse({
      clinic_name: "Aurora Dental",
      clinic_type: "dental",
      country: "AR",
      city: "Buenos Aires",
    });
    expect(result.success).toBe(true);
  });

  it("rejects clinic_name shorter than 2 chars", () => {
    const result = clinicProfileSchema.safeParse({
      clinic_name: "A",
      clinic_type: "dental",
      country: "AR",
      city: "Buenos Aires",
    });
    expect(result.success).toBe(false);
  });

  it("rejects invalid clinic_type", () => {
    const result = clinicProfileSchema.safeParse({
      clinic_name: "Aurora Dental",
      clinic_type: "veterinary",
      country: "AR",
      city: "Buenos Aires",
    });
    expect(result.success).toBe(false);
  });

  it("rejects invalid country", () => {
    const result = clinicProfileSchema.safeParse({
      clinic_name: "Aurora Dental",
      clinic_type: "dental",
      country: "ZZ",
      city: "Buenos Aires",
    });
    expect(result.success).toBe(false);
  });

  it("accepts all valid clinic_type values", () => {
    const types = ["dental", "psychology", "psychiatry", "wellness"] as const;
    for (const clinic_type of types) {
      const result = clinicProfileSchema.safeParse({
        clinic_name: "Test Clinic",
        clinic_type,
        country: "MX",
        city: "Ciudad de México",
      });
      expect(result.success).toBe(true);
    }
  });

  it("infers correct TypeScript type from schema", () => {
    const valid = {
      clinic_name: "Mindful Psych",
      clinic_type: "psychology" as const,
      country: "CL" as const,
      city: "Santiago",
    };
    const result = clinicProfileSchema.parse(valid);
    expect(result.clinic_type).toBe("psychology");
    expect(result.country).toBe("CL");
  });
});
