/**
 * brand-studio-dental.smoke.spec.ts — V-V-4
 *
 * Validator: V-V-4 — Spec §3.2.A Aurora dental brand studio 4 sections
 * Fixture: aurora-dental-ar
 * Flow: Navigate brand-studio → fill 4 sections → autosave fires → preview link
 */
import { test, expect } from "../../fixtures/aurora-dental-ar.fixture";
import { collectConsoleErrors } from "../../auth.fixture";

test.describe("Brand Studio — Clínica Dental Aurora (AR)", () => {
  test("V-V-4: brand studio renders with 4 enabled sections", async ({
    auroraPage: page,
    aurora,
  }) => {
    const consoleErrors = collectConsoleErrors(page);

    await page.goto("/brand-studio");

    // Section navigation visible
    await expect(page.getByText(/identidad/i)).toBeVisible({ timeout: 10_000 });
    await expect(page.getByText(/contacto/i)).toBeVisible();
    await expect(page.getByText(/equipo/i)).toBeVisible();
    await expect(page.getByText(/testimonios/i)).toBeVisible();

    // Forbidden sections NOT visible (per spec §3.2.A)
    await expect(
      page.getByText(/story|estrategia|posicionamiento/i),
    ).not.toBeVisible();

    expect(consoleErrors).toHaveLength(0);
  });

  test("V-V-4: identity section has expected fields", async ({
    auroraPage: page,
    aurora,
  }) => {
    await page.goto("/brand-studio/identidad");

    // Core identity fields
    await expect(
      page.getByRole("textbox", { name: /nombre de la cl[íi]nica/i }),
    ).toBeVisible({ timeout: 10_000 });
    await expect(page.getByRole("textbox", { name: /tagline/i })).toBeVisible();

    // Color palette section
    await expect(page.getByText(/paleta de colores/i)).toBeVisible();
  });

  test("V-V-4: identity section autosaves on change", async ({
    auroraPage: page,
    aurora,
  }) => {
    // Track autosave PATCH request
    let autosaveFired = false;
    await page.route("**/api/v1/brand-studio/sections**", async (route) => {
      if (route.request().method() === "PATCH") {
        autosaveFired = true;
      }
      await route.continue();
    });

    await page.goto("/brand-studio/identidad");

    // Type in tagline to trigger autosave
    const taglineField = page.getByRole("textbox", { name: /tagline/i });
    if (await taglineField.isVisible()) {
      await taglineField.fill("Tu sonrisa, nuestra prioridad");
      // Autosave fires on-change (non-negotiable per form-runtime-array rule)
      await page.waitForTimeout(600); // debounce
      expect(autosaveFired).toBe(true);
    }
  });

  test("V-V-4: team section shows doctor list", async ({
    auroraPage: page,
    aurora,
  }) => {
    await page.goto("/brand-studio/equipo");

    // Doctors from fixture should render
    for (const doctor of aurora.doctors) {
      await expect(page.getByText(doctor.name)).toBeVisible({
        timeout: 10_000,
      });
    }
  });

  test("V-V-4: testimonials section renders", async ({
    auroraPage: page,
    aurora,
  }) => {
    await page.goto("/brand-studio/testimonios");

    // At least one testimonial visible
    await expect(page.getByText(/excelente atenci[oó]n/i)).toBeVisible({
      timeout: 10_000,
    });
  });

  test("V-V-4: landing preview CTA visible", async ({ auroraPage: page }) => {
    await page.goto("/brand-studio");

    // Preview link button
    await expect(
      page
        .getByRole("link", { name: /vista previa landing/i })
        .or(page.getByRole("button", { name: /vista previa/i })),
    ).toBeVisible({ timeout: 10_000 });
  });
});
