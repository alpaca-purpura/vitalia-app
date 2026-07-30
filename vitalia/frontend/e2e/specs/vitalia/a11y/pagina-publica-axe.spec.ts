// cap: clinics.lisa.doctores
// story-origin: vitalia-fase2-lisa-doctores
/**
 * pagina-publica-axe.spec.ts — SC-D3D-13: wcag2aa axe scan for /d/** public doctor page.
 *
 * SC-D3D-13: Public doctor profile page passes wcag2aa (axe-core).
 *   - No auth required (public page)
 *   - Mocks the public endpoint to return a doctor with all fields populated
 *   - Asserts 0 critical/serious violations per wcag2aa standard
 *
 * T-FE-pagina-publica vitalia-fase2-lisa-doctores · auditor auto-fix iter 1 (F4/Step5)
 * spec_anchor: 04-validators.yaml § SC-D3D-13
 * playwright-expert: AxeBuilder + graceful import (package may not be installed)
 *
 * Run:
 *   cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 npx playwright test \
 *     e2e/specs/vitalia/a11y/pagina-publica-axe.spec.ts
 *
 * downstream-regression-na: brand-local vitalia a11y spec; no cross-brand consumers
 */

import { test, expect } from "@playwright/test";

// Graceful import — @axe-core/playwright may not be installed
let AxeBuilder: (typeof import("@axe-core/playwright"))["default"] | null = null;

const CLINICA_SLUG = "clinica-dental-lima";
const DOCTOR_SLUG = "ana-garcia";

const MOCK_DOCTOR_RESPONSE = {
  displayName: "Dra. Ana García",
  specialty: "Odontología Cosmética",
  avatarKey: null,
  clinicName: "Clínica Dental Lima",
  credentialLabel: "CMP 12345 (PE)",
  sobreMi: "Especialista en odontología cosmética con 10 años de experiencia.",
  formacion: [{ titulo: "Médico Cirujano Dentista", institucion: "UPCH", anio: 2014 }],
  // F2: real wire shape — puesto/lugar/anios (NOT cargo)
  experiencia: [{ puesto: "Odontólogo de planta", lugar: "Clínica San Borja", anios: 5 }],
  tratamientos: ["Carillas", "Blanqueamiento", "Implantes"],
  // F3: string[] (NOT object array)
  certificaciones: ["Colegiatura 12345 (PE)", "Diplomado en estética oral"],
  idiomas: ["Español", "Inglés intermedio"],
};

test.describe("SC-D3D-13: Public doctor page — wcag2aa accessibility (axe)", () => {
  test.beforeAll(async () => {
    try {
      const axeModule = await import("@axe-core/playwright");
      AxeBuilder = axeModule.default;
    } catch {
      AxeBuilder = null;
    }
  });

  test("SC-D3D-13: /d/[clinica]/[doctor] passes wcag2aa — 0 critical/serious violations", async ({
    page,
  }) => {
    if (!AxeBuilder) {
      test.skip(
        true,
        "@axe-core/playwright not installed — run: npm i -D @axe-core/playwright",
      );
      return;
    }

    // Mock public endpoint (no auth required)
    await page.route(
      `**/api/v1/vitalia/public/clinics/${CLINICA_SLUG}/doctors/${DOCTOR_SLUG}`,
      async (route) => {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify(MOCK_DOCTOR_RESPONSE),
        });
      },
    );

    const base = process.env["E2E_BASE_URL"] ?? "http://localhost:3002";
    await page.goto(`${base}/d/${CLINICA_SLUG}/${DOCTOR_SLUG}`);
    await page.waitForLoadState("domcontentloaded");

    const results = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa"])
      .analyze();

    const criticalOrSerious = results.violations.filter(
      (v) => v.impact === "critical" || v.impact === "serious",
    );

    if (criticalOrSerious.length > 0) {
      const details = criticalOrSerious
        .map(
          (v) =>
            `[${v.impact ?? "unknown"}] ${v.id}: ${v.description}\n  Nodes: ${v.nodes.slice(0, 2).map((n) => n.html).join(" | ")}`,
        )
        .join("\n");
      expect.soft(
        criticalOrSerious.length,
        `SC-D3D-13 FAIL — ${criticalOrSerious.length} critical/serious wcag2aa violations:\n${details}`,
      ).toBe(0);
    }

    // Smoke: key content visible
    await expect(page.getByText("Dra. Ana García")).toBeVisible();
    await expect(page.getByText("Odontólogo de planta")).toBeVisible();
    await expect(page.getByText("Colegiatura 12345 (PE)")).toBeVisible();
  });
});
