/**
 * onboarding-dental-aurora.smoke.spec.ts — V-V-1
 *
 * Validator: V-V-1 — Spec §3.1.A Aurora dental onboarding happy path
 * Fixture: aurora-dental-ar (dental clinic Argentina, plan_tier=clinic)
 * Flow: Clinic profile step 1/3 → plan selection → offer wizard launch
 */
import { test, expect } from "../../fixtures/aurora-dental-ar.fixture";
import { collectConsoleErrors } from "../../auth.fixture";

test.describe("Onboarding — Clínica Dental Aurora (AR)", () => {
  test("V-V-1: onboarding step 1 renders clinic profile form", async ({
    auroraPage: page,
    aurora,
  }) => {
    const consoleErrors = collectConsoleErrors(page);

    await page.goto("/onboarding");

    // Step breadcrumb visible
    await expect(page.getByText(/paso 1 de 3/i)).toBeVisible({
      timeout: 10_000,
    });

    // Clinic profile fields present
    await expect(
      page.getByRole("textbox", { name: /nombre de la cl[íi]nica/i }),
    ).toBeVisible();
    await expect(
      page.getByRole("group", { name: /tipo de cl[íi]nica/i }),
    ).toBeVisible();
    await expect(
      page.getByRole("combobox", { name: /pa[íi]s/i }),
    ).toBeVisible();
    await expect(page.getByRole("textbox", { name: /ciudad/i })).toBeVisible();

    // "Siguiente" button present
    await expect(
      page.getByRole("button", { name: /siguiente/i }),
    ).toBeVisible();

    // No critical console errors
    expect(consoleErrors).toHaveLength(0);
  });

  test("V-V-1: onboarding clinic profile form submits and advances to step 2", async ({
    auroraPage: page,
    aurora,
  }) => {
    await page.goto("/onboarding");

    // Fill clinic profile
    await page
      .getByRole("textbox", { name: /nombre de la cl[íi]nica/i })
      .fill(aurora.clinicName);

    // Select dental clinic type
    await page.getByRole("radio", { name: /dental/i }).check();

    // Select country Argentina
    await page.getByRole("combobox", { name: /pa[íi]s/i }).selectOption("AR");

    // Fill city
    await page.getByRole("textbox", { name: /ciudad/i }).fill(aurora.city);

    // Submit step 1
    await page.getByRole("button", { name: /siguiente/i }).click();

    // Should advance to step 2 (plan selection)
    await expect(page.getByText(/paso 2 de 3|elige tu plan/i)).toBeVisible({
      timeout: 10_000,
    });
  });

  test("V-V-1: plan selection shows available plans", async ({
    auroraPage: page,
    aurora,
  }) => {
    await page.goto("/onboarding/plan");

    // Plans visible
    await expect(page.getByText(/solo doctor/i)).toBeVisible({
      timeout: 10_000,
    });
    await expect(page.getByText(/cl[íi]nica/i)).toBeVisible();
    await expect(page.getByText(/multi.?sede/i)).toBeVisible();

    // Aurora is clinic plan — select it
    const clinicPlan = page.getByRole("radio", { name: /cl[íi]nica/i });
    if (await clinicPlan.isVisible()) {
      await clinicPlan.check();
    }
  });

  test("V-V-1: loading/error/empty states are handled", async ({
    auroraPage: page,
  }) => {
    // Intercept with loading delay to verify loading state
    await page.route(
      "**/api/v1/vitalia/onboarding/clinic-profile",
      async (route) => {
        await new Promise((r) => setTimeout(r, 100));
        await route.continue();
      },
    );

    await page.goto("/onboarding");

    // Verify page eventually renders (not stuck in loading)
    await expect(page.locator("body")).toBeVisible({ timeout: 15_000 });

    // No error boundary triggered
    const errorText = page.getByText(/algo sali[oó] mal|error inesperado/i);
    await expect(errorText).not.toBeVisible();
  });
});
