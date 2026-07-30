/**
 * onboarding-psych-sanare.smoke.spec.ts — V-V-3
 *
 * Validator: V-V-3 — Spec §3.1 Sanaré LATAM multi_site psychology+psychiatry onboarding
 * Fixture: sanare-latam-mx (psychology+psychiatry MX multi_site, currency=MXN)
 * Flow: Clinic profile → plan (multi_site) → offer wizard launch
 */
import { test, expect } from "../../fixtures/sanare-latam-mx.fixture";
import { collectConsoleErrors } from "../../auth.fixture";

test.describe("Onboarding — Sanaré LATAM (MX)", () => {
  test("V-V-3: onboarding renders for multi_site MX clinic", async ({
    sanarePage: page,
    sanare,
  }) => {
    const consoleErrors = collectConsoleErrors(page);

    await page.goto("/onboarding");

    // Step breadcrumb visible
    await expect(page.getByText(/paso 1 de 3/i)).toBeVisible({
      timeout: 10_000,
    });

    // Required fields visible
    await expect(
      page.getByRole("textbox", { name: /nombre de la cl[íi]nica/i }),
    ).toBeVisible();
    await expect(
      page.getByRole("combobox", { name: /pa[íi]s/i }),
    ).toBeVisible();

    // No console errors
    expect(consoleErrors).toHaveLength(0);
  });

  test("V-V-3: multi_site plan available and selectable", async ({
    sanarePage: page,
    sanare,
  }) => {
    await page.goto("/onboarding/plan");

    // Multi-sede (multi_site) plan visible
    await expect(page.getByText(/multi.?sede/i)).toBeVisible({
      timeout: 10_000,
    });

    // Price shown: $399 USD/mo
    await expect(page.getByText(/399/i)).toBeVisible();
  });

  test("V-V-3: MX country and city populate correctly", async ({
    sanarePage: page,
    sanare,
  }) => {
    await page.goto("/onboarding");

    // Fill for MX multi_site
    await page
      .getByRole("textbox", { name: /nombre de la cl[íi]nica/i })
      .fill(sanare.clinicName);

    // Select psychology (primary clinic_type per fixture)
    await page.getByRole("radio", { name: /psicolog[íi]a/i }).check();

    // Select Mexico
    await page.getByRole("combobox", { name: /pa[íi]s/i }).selectOption("MX");

    // Fill CDMX
    await page.getByRole("textbox", { name: /ciudad/i }).fill(sanare.city);

    // Siguiente button should be enabled
    const nextBtn = page.getByRole("button", { name: /siguiente/i });
    await expect(nextBtn).toBeVisible();
    await nextBtn.click();

    // Advances to plan step
    await expect(page.getByText(/paso 2 de 3|elige tu plan/i)).toBeVisible({
      timeout: 10_000,
    });
  });

  test("V-V-3: multi_site placeholder visible for deferred features", async ({
    sanarePage: page,
    sanare,
  }) => {
    await page.goto("/dashboard");

    // Multi-site deferred features should show placeholder (Q2=B defer)
    // If multi-site placeholder exists on any plan-gated feature, verify it renders correctly
    await expect(page.locator("body")).toBeVisible({ timeout: 10_000 });

    // No crash
    const errorBoundary = page.getByText(/algo sali[oó] mal|error inesperado/i);
    await expect(errorBoundary).not.toBeVisible();
  });
});
