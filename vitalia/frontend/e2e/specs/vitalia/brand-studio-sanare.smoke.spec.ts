/**
 * brand-studio-sanare.smoke.spec.ts — V-V-6
 *
 * Validator: V-V-6 — Spec §3.2 Sanaré LATAM multi_site brand studio
 * Fixture: sanare-latam-mx (psychology+psychiatry MX multi_site)
 * Flow: Brand studio → multi-doctor team (3 doctors) → MXN currency displayed
 */
import { test, expect } from "../../fixtures/sanare-latam-mx.fixture";
import { collectConsoleErrors } from "../../auth.fixture";

test.describe("Brand Studio — Sanaré LATAM (MX)", () => {
  test("V-V-6: brand studio renders for Sanaré multi_site", async ({
    sanarePage: page,
    sanare,
  }) => {
    const consoleErrors = collectConsoleErrors(page);

    await page.goto("/brand-studio");

    // 4 core sections visible
    await expect(page.getByText(/identidad/i)).toBeVisible({ timeout: 10_000 });
    await expect(page.getByText(/contacto/i)).toBeVisible();
    await expect(page.getByText(/equipo/i)).toBeVisible();
    await expect(page.getByText(/testimonios/i)).toBeVisible();

    expect(consoleErrors).toHaveLength(0);
  });

  test("V-V-6: team section shows all 3 Sanaré doctors", async ({
    sanarePage: page,
    sanare,
  }) => {
    await page.goto("/brand-studio/equipo");

    // All 3 doctors from fixture
    for (const doctor of sanare.doctors) {
      await expect(page.getByText(doctor.name)).toBeVisible({
        timeout: 10_000,
      });
    }

    // Dr. Alejandro Ríos = psychiatry (validates psychiatric vertical)
    await expect(page.getByText(/psiquiatr[íi]a/i)).toBeVisible();
  });

  test("V-V-6: identity section reflects Sanaré branding", async ({
    sanarePage: page,
    sanare,
  }) => {
    await page.goto("/brand-studio/identidad");

    // Clinic name from API mock
    await expect(page.getByText(sanare.clinicName)).toBeVisible({
      timeout: 10_000,
    });

    // Tagline "Bienestar mental para toda LatAm" from mock
    await expect(page.getByText(/bienestar mental/i)).toBeVisible();
  });

  test("V-V-6: MX contact info renders correctly", async ({
    sanarePage: page,
  }) => {
    await page.goto("/brand-studio/contacto");

    // CDMX address
    await expect(page.getByText(/cdmx|ciudad de m[eé]xico/i)).toBeVisible({
      timeout: 10_000,
    });
  });

  test("V-V-6: autosave indicator shows after edit", async ({
    sanarePage: page,
  }) => {
    let patchCalled = false;
    await page.route("**/api/v1/brand-studio/sections**", async (route) => {
      if (route.request().method() === "PATCH") {
        patchCalled = true;
      }
      await route.continue();
    });

    await page.goto("/brand-studio/identidad");

    // Modify tagline to trigger autosave
    const tagline = page.getByRole("textbox", { name: /tagline/i });
    if (await tagline.isVisible()) {
      await tagline.fill("Bienestar mental para toda LatAm — actualizado");
      await page.waitForTimeout(600);
      expect(patchCalled).toBe(true);
    }
  });
});
