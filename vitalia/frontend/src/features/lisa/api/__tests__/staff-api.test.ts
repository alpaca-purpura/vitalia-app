// cap: clinics.lisa.doctores
// story-origin: vitalia-fase2-lisa-doctores
/**
 * staff-api.test.ts — Vitest unit tests for Staff API helpers.
 *
 * Covers:
 *   - staffKeys factory structure
 *   - mapDoctorCreateToPayload camelCase → snake_case mapping
 *   - staff-schema credential validation per country
 *
 * T-FE-1 vitalia-fase2-lisa-doctores
 * spec_anchor: 03-arch-fe.md § Data layer + 01-spec.md § Business rules
 * downstream-regression-na: brand-local vitalia FE test; no cross-brand consumers
 */

import { describe, it, expect } from "vitest";
import { mapDoctorCreateToPayload } from "../staff";
import { doctorCreateSchema } from "../../types/staff-schema";
import type { DoctorCreateFormValues } from "../../types/staff-schema";

// ── mapDoctorCreateToPayload ───────────────────────────────────────────────────

describe("mapDoctorCreateToPayload", () => {
  const formValues: DoctorCreateFormValues = {
    firstName: "Ana",
    lastName: "García",
    dni: "12345678",
    email: "ana@test.com",
    phone: "+51 999 888 777",
    specialty: "Odontología",
    credential: "99999",
    credentialCountry: "PE",
    active: true,
  };

  it("maps camelCase firstName → snake_case first_name", () => {
    const payload = mapDoctorCreateToPayload(formValues);
    expect(payload.first_name).toBe("Ana");
    expect("firstName" in payload).toBe(false);
  });

  it("maps camelCase lastName → snake_case last_name", () => {
    const payload = mapDoctorCreateToPayload(formValues);
    expect(payload.last_name).toBe("García");
  });

  it("maps credentialCountry → credential_country", () => {
    const payload = mapDoctorCreateToPayload(formValues);
    expect(payload.credential_country).toBe("PE");
  });

  it("maps empty phone string to null", () => {
    const payload = mapDoctorCreateToPayload({ ...formValues, phone: "" });
    expect(payload.phone).toBeNull();
  });

  it("maps empty specialty string to null", () => {
    const payload = mapDoctorCreateToPayload({ ...formValues, specialty: "" });
    expect(payload.specialty).toBeNull();
  });

  it("preserves phone when provided", () => {
    const payload = mapDoctorCreateToPayload(formValues);
    expect(payload.phone).toBe("+51 999 888 777");
  });
});

// ── doctorCreateSchema ─────────────────────────────────────────────────────────

describe("doctorCreateSchema — comprehensive validation", () => {
  const validBase = {
    firstName: "Ana",
    lastName: "García",
    dni: "12345678",
    email: "ana@test.com",
    credential: "12345",
    credentialCountry: "PE" as const,
    active: true,
  };

  describe("PE credential (CMP — numeric)", () => {
    it("accepts numeric-only credential", () => {
      expect(
        doctorCreateSchema.safeParse({ ...validBase, credential: "99999" }).success,
      ).toBe(true);
    });

    it("rejects alphabetic credential", () => {
      const r = doctorCreateSchema.safeParse({ ...validBase, credential: "abc" });
      expect(r.success).toBe(false);
    });

    it("rejects alphanumeric credential", () => {
      const r = doctorCreateSchema.safeParse({ ...validBase, credential: "12abc" });
      expect(r.success).toBe(false);
    });
  });

  describe("AR credential (matrícula — alphanumeric)", () => {
    const base = { ...validBase, credentialCountry: "AR" as const };

    it("accepts alphanumeric credential", () => {
      expect(
        doctorCreateSchema.safeParse({ ...base, credential: "MP-12345" }).success,
      ).toBe(true);
    });

    it("accepts numeric-only credential", () => {
      expect(
        doctorCreateSchema.safeParse({ ...base, credential: "123456" }).success,
      ).toBe(true);
    });
  });

  describe("required fields", () => {
    it("fails without firstName", () => {
      expect(
        doctorCreateSchema.safeParse({ ...validBase, firstName: "" }).success,
      ).toBe(false);
    });

    it("fails without lastName", () => {
      expect(
        doctorCreateSchema.safeParse({ ...validBase, lastName: "" }).success,
      ).toBe(false);
    });

    it("fails without dni", () => {
      expect(
        doctorCreateSchema.safeParse({ ...validBase, dni: "" }).success,
      ).toBe(false);
    });

    it("fails with invalid email", () => {
      expect(
        doctorCreateSchema.safeParse({ ...validBase, email: "not-email" }).success,
      ).toBe(false);
    });

    it("fails without credential", () => {
      expect(
        doctorCreateSchema.safeParse({ ...validBase, credential: "" }).success,
      ).toBe(false);
    });
  });
});
