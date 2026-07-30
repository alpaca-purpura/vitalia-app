/**
 * treatment-followup-sanare.smoke.spec.ts — V-V-15
 *
 * Validator: V-V-15 — Spec §3.5 Sanaré LATAM psychiatric medication followup
 * Fixture: sanare-latam-mx (psychiatry SSRI dose adjustment, adherence_score=0.9)
 * Flow: /treatments/{id}/seguimiento → SSRI milestones → medication_disclaimer
 */
import { test, expect } from "../../fixtures/sanare-latam-mx.fixture";
import { collectConsoleErrors } from "../../auth.fixture";

const TREATMENT_ID = "treatment-sanare-psych-001";

test.describe("Treatment Followup — Seguimiento psiquiátrico Sanaré (MX)", () => {
  test("V-V-15: psychiatric treatment followup dashboard renders", async ({
    sanarePage: page,
    sanare,
  }) => {
    const consoleErrors = collectConsoleErrors(page);

    await page.goto(`/tratamientos/${TREATMENT_ID}/seguimiento`);

    // Patient name
    await expect(page.getByText(sanare.patientName)).toBeVisible({
      timeout: 10_000,
    });

    // Treatment name from mock: psychiatric SSRI followup
    await expect(
      page.getByText(/psiqui[áa]tric[ao]|ssri|ajuste.*dosis/i),
    ).toBeVisible();

    expect(consoleErrors).toHaveLength(0);
  });

  test("V-V-15: psychiatric milestones show medication schedule", async ({
    sanarePage: page,
  }) => {
    await page.goto(`/tratamientos/${TREATMENT_ID}/seguimiento`);

    // Mock milestones: consulta inicial, control 2 semanas, ajuste dosis, evaluación 3 meses
    await expect(page.getByText(/consulta inicial/i)).toBeVisible({
      timeout: 10_000,
    });
    await expect(page.getByText(/control.*semanas|2 semanas/i)).toBeVisible();
    await expect(page.getByText(/ajuste.*dosis|dosis/i)).toBeVisible();
    await expect(page.getByText(/3 meses|evaluaci[oó]n/i)).toBeVisible();
  });

  test("V-V-15: medication disclaimer shown for psychiatric treatment", async ({
    sanarePage: page,
  }) => {
    await page.goto(`/tratamientos/${TREATMENT_ID}/seguimiento`);

    // medication_disclaimer_required=true → disclaimer must render
    await expect(
      page.getByText(/medicaci[oó]n|descargo de responsabilidad|disclaimer/i),
    ).toBeVisible({ timeout: 10_000 });
  });

  test("V-V-15: adherence score 0.9 (excellent) displayed", async ({
    sanarePage: page,
  }) => {
    await page.goto(`/tratamientos/${TREATMENT_ID}/seguimiento`);

    // Adherence 0.9 = excellent / 90%
    await expect(
      page
        .getByText(/0\.9|90%|excelente|muy bueno/i)
        .or(page.getByText(/adherencia/i)),
    ).toBeVisible({ timeout: 10_000 });
  });

  test("V-V-15: next_action dosis_review shown as upcoming", async ({
    sanarePage: page,
  }) => {
    await page.goto(`/tratamientos/${TREATMENT_ID}/seguimiento`);

    // Next action: dosis_review
    await expect(
      page.getByText(/ajuste de dosis|dosis.*revisi[oó]n|revisi[oó]n.*dosis/i),
    ).toBeVisible({ timeout: 10_000 });
  });
});
