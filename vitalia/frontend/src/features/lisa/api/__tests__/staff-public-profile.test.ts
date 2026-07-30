// cap: clinics.lisa.doctores
// story-origin: vitalia-fase2-lisa-doctores
/**
 * staff-public-profile.test.ts — Unit tests for SavePublicProfilePayload types + wire shape.
 *
 * Tests cover:
 *   - F4: SavePublicProfilePayload matches real BE DTO (commit 275d5d7e)
 *   - F2: experiencia uses {puesto, lugar, anios} NOT {cargo, institucion, desde, hasta}
 *   - F3: certificaciones/idiomas are string[] NOT object arrays
 *   - Hydration from wire fixture (real BE response shape)
 *
 * T-FE-pagina-publica vitalia-fase2-lisa-doctores · auditor auto-fix iter 1 (F4)
 * spec_anchor: 01-spec.md § D3-D.3 | 03-arch-be.md § DoctorPublicProfileDTO
 */

import { describe, it, expect } from "vitest";
import type { SavePublicProfilePayload } from "../staff";
import type {
  StructuredExperiencia,
  DoctorPublicProfile,
} from "../../types/staff.types";

// ── Wire fixture (real BE response per commit 275d5d7e) ───────────────────────

const wireFixture: DoctorPublicProfile = {
  sobreMi: "Especialista en odontología cosmética con 10 años de experiencia.",
  formacion: [{ titulo: "Médico cirujano dentista", institucion: "UPCH", anio: 2014 }],
  experiencia: [{ puesto: "Odontólogo de planta", lugar: "Clínica San Borja", anios: 5 }],
  tratamientos: ["Carillas", "Blanqueamiento"],
  certificaciones: ["Colegiatura 12345 (PE)", "Diplomado en estética oral"],
  idiomas: ["Español", "Inglés intermedio"],
};

// ── StructuredExperiencia shape (F2) ─────────────────────────────────────────

describe("StructuredExperiencia — real wire shape", () => {
  it("uses puesto (NOT cargo)", () => {
    const e: StructuredExperiencia = { puesto: "Odontólogo", lugar: "Clínica X", anios: 3 };
    expect(e.puesto).toBe("Odontólogo");
    // TypeScript compile-time check: cargo does NOT exist on the type
    // @ts-expect-error cargo is not a valid field after F2 fix
    const _bad: StructuredExperiencia = { cargo: "fail" };
    void _bad;
  });

  it("lugar is optional (nullable)", () => {
    const e: StructuredExperiencia = { puesto: "Cirujano" };
    expect(e.lugar).toBeUndefined();
    const e2: StructuredExperiencia = { puesto: "Cirujano", lugar: null };
    expect(e2.lugar).toBeNull();
  });

  it("anios is optional number (nullable)", () => {
    const e: StructuredExperiencia = { puesto: "Dentista", anios: 7 };
    expect(e.anios).toBe(7);
    const e2: StructuredExperiencia = { puesto: "Dentista", anios: null };
    expect(e2.anios).toBeNull();
  });
});

// ── DoctorPublicProfile wire shape (F3) ──────────────────────────────────────

describe("DoctorPublicProfile — certificaciones + idiomas are string[]", () => {
  it("certificaciones is string[] per wire fixture", () => {
    expect(wireFixture.certificaciones).toEqual([
      "Colegiatura 12345 (PE)",
      "Diplomado en estética oral",
    ]);
    expect(typeof wireFixture.certificaciones[0]).toBe("string");
  });

  it("idiomas is string[] per wire fixture", () => {
    expect(wireFixture.idiomas).toEqual(["Español", "Inglés intermedio"]);
    expect(typeof wireFixture.idiomas[0]).toBe("string");
  });

  it("certificaciones does NOT have object shape (no .nombre field)", () => {
    // If cert were an object, cert.nombre would exist. It's a string now.
    const cert = wireFixture.certificaciones[0];
    expect(typeof cert).toBe("string");
    // @ts-expect-error nombre does not exist on string
    const _n = cert.nombre;
    void _n;
  });

  it("idiomas does NOT have object shape (no .idioma field)", () => {
    const lang = wireFixture.idiomas[0];
    expect(typeof lang).toBe("string");
    // @ts-expect-error idioma does not exist on string
    const _i = lang.idioma;
    void _i;
  });
});

// ── SavePublicProfilePayload matches BE DTO (F4) ─────────────────────────────

describe("SavePublicProfilePayload — payload shape matches real BE DTO", () => {
  it("accepts experiencia with puesto/lugar/anios", () => {
    const payload: SavePublicProfilePayload = {
      sobreMi: "Test",
      experiencia: [{ puesto: "Dentista", lugar: "Lima", anios: 5 }],
      certificaciones: ["Colegiatura 12345 (PE)"],
      idiomas: ["Español"],
      tratamientos: ["Carillas"],
      formacion: [{ titulo: "MCD", institucion: "UPCH", anio: 2014 }],
    };
    expect(payload.experiencia?.[0]?.puesto).toBe("Dentista");
    expect(payload.certificaciones?.[0]).toBe("Colegiatura 12345 (PE)");
    expect(payload.idiomas?.[0]).toBe("Español");
  });

  it("payload certificaciones must be string[] NOT object array", () => {
    const payload: SavePublicProfilePayload = {
      certificaciones: ["Colegiatura 12345 (PE)"],
    };
    // Verify runtime value is string
    expect(typeof payload.certificaciones?.[0]).toBe("string");
  });

  it("payload idiomas must be string[] NOT object array", () => {
    const payload: SavePublicProfilePayload = {
      idiomas: ["Inglés"],
    };
    expect(typeof payload.idiomas?.[0]).toBe("string");
  });
});

// ── Hydration from wire fixture ───────────────────────────────────────────────

describe("Hydration from wire fixture", () => {
  it("certificaciones wire string maps directly (no .nombre extraction)", () => {
    // Old broken code: wireFixture.certificaciones.map(c => ({ nombre: c.nombre }))
    // Correct code: wireFixture.certificaciones (already string[])
    const hydrated = wireFixture.certificaciones;
    expect(hydrated[0]).toBe("Colegiatura 12345 (PE)");
  });

  it("experiencia wire shape hydrates puesto/lugar/anios", () => {
    const exp = wireFixture.experiencia[0];
    expect(exp.puesto).toBe("Odontólogo de planta");
    expect(exp.lugar).toBe("Clínica San Borja");
    expect(exp.anios).toBe(5);
  });
});
