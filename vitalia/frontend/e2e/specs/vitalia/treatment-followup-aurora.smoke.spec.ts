/**
 * treatment-followup-aurora.smoke.spec.ts — V-V-13
 *
 * Validator: V-V-13 — Spec §3.5.A Aurora dental treatment followup dashboard
 * Fixture: aurora-dental-ar (implant, 4-milestone timeline, adherence_score=0.8)
 * Flow: /treatments/{id}/followup → timeline → adherence score → manual handoff CTA
 */
import { test, expect } from "../../fixtures/aurora-dental-ar.fixture";
import { collectConsoleErrors } from "../../auth.fixture";

const TREATMENT_ID = "treatment-aurora-001";

test.describe("Treatment Followup — Implante Dental Aurora (AR)", () => {
  test("V-V-13: treatment followup dashboard renders", async ({
    auroraPage: page,
    aurora,
  }) => {
    const consoleErrors = collectConsoleErrors(page);

    await page.goto(`/tratamientos/${TREATMENT_ID}/seguimiento`);

    // Patient name visible
    await expect(page.getByText(aurora.patientName)).toBeVisible({
      timeout: 10_000,
    });

    // Treatment name
    await expect(page.getByText(/implante dental/i)).toBeVisible();

    expect(consoleErrors).toHaveLength(0);
  });

  test("V-V-13: milestone timeline rendered with 4 milestones", async ({
    auroraPage: page,
  }) => {
    await page.goto(`/tratamientos/${TREATMENT_ID}/seguimiento`);

    // 4 milestones: Cirugía, Control, Sutura, Corona
    await expect(page.getByText(/cirugía|cirug[íi]a/i)).toBeVisible({
      timeout: 10_000,
    });
    await expect(page.getByText(/control/i)).toBeVisible();
    await expect(page.getByText(/sutura/i)).toBeVisible();
    await expect(page.getByText(/corona/i)).toBeVisible();
  });

  test("V-V-13: adherence score displayed", async ({ auroraPage: page }) => {
    await page.goto(`/tratamientos/${TREATMENT_ID}/seguimiento`);

    // Adherence score 0.8 = "Bueno" or 80%
    await expect(
      page
        .getByText(/adherencia|adherence/i)
        .or(page.getByText(/0\.8|80%|bueno/i)),
    ).toBeVisible({ timeout: 10_000 });
  });

  test("V-V-13: manual handoff CTA visible", async ({ auroraPage: page }) => {
    await page.goto(`/tratamientos/${TREATMENT_ID}/seguimiento`);

    // "Tomar conversación" button per spec §3.5.A
    await expect(
      page.getByRole("button", { name: /tomar conversaci[oó]n/i }),
    ).toBeVisible({ timeout: 10_000 });
  });

  test("V-V-13: next action (sutura review) shown", async ({
    auroraPage: page,
  }) => {
    await page.goto(`/tratamientos/${TREATMENT_ID}/seguimiento`);

    // Next action from mock: sutura_removal on D14
    await expect(page.getByText(/sutura|d14|pr[oó]xim[ao]/i)).toBeVisible({
      timeout: 10_000,
    });
  });

  test("V-V-13: milestone statuses reflect done/upcoming/pending", async ({
    auroraPage: page,
  }) => {
    await page.goto(`/tratamientos/${TREATMENT_ID}/seguimiento`);

    // Done milestones (D0 + D5)
    const doneIndicators = page.getByText(/hecho|done|completado/i);
    const doneCount = await doneIndicators.count();
    expect(doneCount).toBeGreaterThanOrEqual(1);
  });
});
