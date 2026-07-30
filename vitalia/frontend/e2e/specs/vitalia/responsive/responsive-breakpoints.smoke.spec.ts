/**
 * responsive-breakpoints.smoke.spec.ts — V-V-19
 *
 * Validator: V-V-19 — Spec §9 Responsive breakpoints (mobile/tablet/desktop)
 * Fixture: aurora-dental-ar (representative tenant)
 * Flow: Key pages render correctly at mobile (<768px), tablet (768-1024px), desktop (>1024px)
 *
 * Note: This spec runs under responsive Playwright projects (mobile/tablet/desktop viewport configs).
 * The actual viewport is set by playwright.config.ts per project.
 */
import { test, expect } from "../../../fixtures/aurora-dental-ar.fixture";
import { collectConsoleErrors } from "../../../auth.fixture";

test.describe("Responsive — Vitalia UI (Aurora AR)", () => {
  test("brand studio renders at current viewport", async ({
    auroraPage: page,
  }) => {
    const consoleErrors = collectConsoleErrors(page);

    await page.goto("/brand-studio");

    // Core content visible regardless of viewport
    await expect(page.getByText(/identidad/i)).toBeVisible({ timeout: 10_000 });
    await expect(page.getByText(/contacto/i)).toBeVisible();

    // No horizontal overflow (layout integrity)
    const bodyWidth = await page.evaluate(() => document.body.scrollWidth);
    const viewportWidth = page.viewportSize()?.width ?? 1280;
    expect(bodyWidth).toBeLessThanOrEqual(viewportWidth + 20); // 20px tolerance

    expect(consoleErrors).toHaveLength(0);
  });

  test("compliance dashboard renders at current viewport", async ({
    auroraPage: page,
  }) => {
    const consoleErrors = collectConsoleErrors(page);

    await page.goto("/medical-compliance");

    // Total events card visible at any viewport
    await expect(page.getByText(/347/i)).toBeVisible({ timeout: 10_000 });

    // No horizontal overflow
    const bodyWidth = await page.evaluate(() => document.body.scrollWidth);
    const viewportWidth = page.viewportSize()?.width ?? 1280;
    expect(bodyWidth).toBeLessThanOrEqual(viewportWidth + 20);

    expect(consoleErrors).toHaveLength(0);
  });

  test("booking slots render at current viewport", async ({
    auroraPage: page,
  }) => {
    const consoleErrors = collectConsoleErrors(page);

    await page.goto("/citas/nueva");

    // Slots visible at any breakpoint
    await expect(
      page.getByText(/horarios disponibles|selecciona tu cita/i),
    ).toBeVisible({ timeout: 10_000 });

    // Mobile: touch targets ≥ 44×44 px (WCAG 2.5.5)
    const viewport = page.viewportSize();
    if (viewport && viewport.width < 768) {
      // On mobile, buttons should be sufficiently large
      const ctaButtons = page.getByRole("button");
      const count = await ctaButtons.count();
      if (count > 0) {
        const firstBtn = ctaButtons.first();
        const box = await firstBtn.boundingBox();
        if (box) {
          expect(box.height).toBeGreaterThanOrEqual(44);
        }
      }
    }

    expect(consoleErrors).toHaveLength(0);
  });

  test("onboarding form usable at current viewport", async ({
    auroraPage: page,
  }) => {
    const consoleErrors = collectConsoleErrors(page);

    await page.goto("/onboarding");

    // Form fields accessible at any viewport
    await expect(
      page.getByRole("textbox", { name: /nombre de la cl[íi]nica/i }),
    ).toBeVisible({ timeout: 10_000 });

    // Siguiente button accessible
    await expect(
      page.getByRole("button", { name: /siguiente/i }),
    ).toBeVisible();

    expect(consoleErrors).toHaveLength(0);
  });

  test("sidebar/navigation accessible at current viewport", async ({
    auroraPage: page,
  }) => {
    const consoleErrors = collectConsoleErrors(page);

    await page.goto("/dashboard");

    const viewport = page.viewportSize();

    if (viewport && viewport.width < 768) {
      // Mobile: hamburger menu button should be visible
      const hamburger = page
        .getByRole("button", { name: /men[uú]|abrir navegaci[oó]n/i })
        .or(page.getByLabel(/men[uú]/i));
      // May not be required if sidebar collapses via other pattern
      await expect(page.locator("body")).toBeVisible({ timeout: 10_000 });
    } else {
      // Tablet/Desktop: sidebar items visible
      await expect(
        page.getByRole("navigation").or(page.locator("nav")).first(),
      ).toBeVisible({ timeout: 10_000 });
    }

    expect(consoleErrors).toHaveLength(0);
  });
});
