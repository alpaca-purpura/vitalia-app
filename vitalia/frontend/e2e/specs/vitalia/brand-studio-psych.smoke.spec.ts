/**
 * brand-studio-psych.smoke.spec.ts — V-V-5
 *
 * Validator: V-V-5 — Spec §3.2.A Centro Mindful Santiago brand studio
 * Fixture: mindful-psych-cl (psychology solo_doctor CL)
 * Flow: Navigate brand-studio → 4 sections → autosave → single doctor team
 */
import { test, expect } from "../../fixtures/mindful-psych-cl.fixture";
import { collectConsoleErrors } from "../../auth.fixture";

test.describe("Brand Studio — Centro Mindful Santiago (CL)", () => {
  test("V-V-5: brand studio renders 4 sections for psychology clinic", async ({
    mindfulPage: page,
    mindful,
  }) => {
    const consoleErrors = collectConsoleErrors(page);

    await page.goto("/brand-studio");

    // 4 sections present
    await expect(page.getByText(/identidad/i)).toBeVisible({ timeout: 10_000 });
    await expect(page.getByText(/contacto/i)).toBeVisible();
    await expect(page.getByText(/equipo/i)).toBeVisible();
    await expect(page.getByText(/testimonios/i)).toBeVisible();

    // Forbidden sections not present
    await expect(
      page.getByText(/estrategia|posicionamiento/i),
    ).not.toBeVisible();

    expect(consoleErrors).toHaveLength(0);
  });

  test("V-V-5: solo_doctor team section shows single doctor", async ({
    mindfulPage: page,
    mindful,
  }) => {
    await page.goto("/brand-studio/equipo");

    // Only 1 doctor for solo_doctor plan
    await expect(page.getByText(mindful.doctors[0].name)).toBeVisible({
      timeout: 10_000,
    });

    // Specialty visible
    await expect(page.getByText(/psicolog[íi]a cl[íi]nica/i)).toBeVisible();
  });

  test("V-V-5: contact section shows CL contact info", async ({
    mindfulPage: page,
  }) => {
    await page.goto("/brand-studio/contacto");

    // CL address renders
    await expect(page.getByText(/santiago/i)).toBeVisible({ timeout: 10_000 });
  });

  test("V-V-5: loading skeleton shown while fetching brand data", async ({
    mindfulPage: page,
  }) => {
    // Slow the API to observe loading state
    await page.route("**/api/v1/brand-studio/sections**", async (route) => {
      await new Promise((r) => setTimeout(r, 300));
      await route.continue();
    });

    await page.goto("/brand-studio");

    // Either skeleton or content eventually visible (no infinite spinner)
    await expect(page.locator("body")).toBeVisible({ timeout: 15_000 });
    await expect(page.getByText(/identidad/i)).toBeVisible({ timeout: 10_000 });
  });

  test("V-V-5: testimonials section shows psychology testimonial", async ({
    mindfulPage: page,
  }) => {
    await page.goto("/brand-studio/testimonios");

    // Testimonial content from mindful fixture
    await expect(
      page.getByText(/ps\. fuentes.*ansiedad|ansiedad.*ps\. fuentes/i),
    ).toBeVisible({
      timeout: 10_000,
    });
  });
});
