/**
 * i18n-spanish-neutro.spec.ts — SC-9 Spanish neutro LatAm renderizado
 *
 * F1-S5 vitalia-fase1-valeria-rail-history — T-8
 *
 * Gherkin: 01-spec.md § 1 Scenario 9 (i18n)
 *
 * Given: ValeriaSidebar state='full' montado en cualquier viewport
 * When:  Render completo del componente
 * Then:  All user-facing strings are Spanish neutro LatAm (tuteo, no voseo)
 *        Zero voseo match (glosario .claude/rules/spanish-text.md)
 *        Zero English placeholders (TODO / Lorem ipsum / "Search...")
 *
 * SC-9 gherkin_coverage:
 *   - SC-9-1: 'Hoy', 'Ayer', 'Esta semana' group labels present
 *   - SC-9-2: 'Nueva conversación (próximamente)' alert text when pressing 'n'
 *   - SC-9-3: aria-labels español neutro: 'Panel Valeria', 'Cerrar panel Valeria'
 *   - SC-9-4: live region Spanish neutro ('Valeria con historial' / 'Valeria abierta' / 'Valeria cerrada')
 *   - SC-9-5: zero voseo regex match on page text
 *   - SC-9-6: zero English placeholders on page text
 *
 * Mock data (8 items from _mock-conversations.ts):
 *   "Resumen reseñas Google semana", "Ideas campaña Día de la Madre",
 *   "Reporte ocupación martes", "Borrador respuesta a reseña 3⭐",
 *   "Tutorial agenda online turnos", "Plan ofertas mes mayo",
 *   "Métricas conversión landing", "Revisar copy WhatsApp bienvenida"
 *
 * HIPAA-lite: mock data sin PHI, scope NA para F1-S5 (UI chrome).
 *
 * downstream-regression-na: brand-local E2E spec; no cross-brand consumers
 */

// voseo-allowed: this file contains voseo strings ONLY as regex patterns to DETECT violations

import { expect } from "@playwright/test";
import { test } from "../../fixtures/shell-theme.fixture";
import { ValeriaSidebarPage } from "../../pages/ValeriaSidebarPage";

const DESKTOP_VIEWPORT = { width: 1280, height: 800 };

// Expected Spanish neutro strings present in the component
const EXPECTED_STRINGS = [
  "Hoy",
  "Ayer",
  "Esta semana",
  // Mock conversation titles (from _mock-conversations.ts)
  "Resumen reseñas Google semana",
  "Ideas campaña Día de la Madre",
  "Reporte ocupación martes",
  "Borrador respuesta a reseña",
  "Tutorial agenda online turnos",
  "Plan ofertas mes mayo",
] as const;

// Voseo patterns that must NOT appear in user-facing strings
// (per .claude/rules/spanish-text.md glosario)
const VOSEO_PATTERNS = [
  /\bvos\b/i,
  /\bsos\b/i,
  /\btenés\b/i,
  /\bpodés\b/i,
  /\bquerés\b/i,
  /\bsabés\b/i,
  /\bdale\b/i,
  /\bmirá\b/i,
  /\bfijate\b/i,
  /\bagregá\b/i,
  /\bconfigurá\b/i,
  /\busá\b/i,
  /\bhacé\b/i,
  /\babrí\b/i,
] as const;

// English placeholders that must NOT appear in user-facing text
const ENGLISH_PLACEHOLDER_PATTERNS = [
  /\bTODO\b/,
  /Lorem ipsum/i,
  /\bSearch\.\.\./,
  /\bPlaceholder\b/i,
] as const;

test.describe("SC-9 — i18n Spanish neutro LatAm", () => {
  test.use({ viewport: DESKTOP_VIEWPORT });

  test("SC-9-1: group labels 'Hoy', 'Ayer', 'Esta semana' rendered in history", async ({
    valeriaFullPage,
  }) => {
    const pom = new ValeriaSidebarPage(valeriaFullPage);
    await pom.goto({ valeriaState: "full", shellMode: "agentic" });

    // Group labels visible — use exact text to avoid strict mode violations
    // (timestamps like "Ayer 19:02" also match "Ayer" non-exact)
    await expect(
      valeriaFullPage.getByText("Hoy", { exact: true }).first(),
    ).toBeVisible();
    await expect(
      valeriaFullPage.getByText("Ayer", { exact: true }).first(),
    ).toBeVisible();
    await expect(
      valeriaFullPage.getByText("Esta semana", { exact: true }).first(),
    ).toBeVisible();

    // At least one conversation title visible (mock data loaded)
    await expect(
      valeriaFullPage.getByText("Resumen reseñas Google semana"),
    ).toBeVisible();
  });

  test("SC-9-2: press 'n' shows alert 'Nueva conversación (próximamente)'", async ({
    valeriaFullPage,
  }) => {
    const pom = new ValeriaSidebarPage(valeriaFullPage);
    await pom.goto({ valeriaState: "full", shellMode: "agentic" });

    // Register dialog handler BEFORE press (auto-accept prevents test hang)
    let capturedMessage = "";
    valeriaFullPage.on("dialog", async (dialog) => {
      capturedMessage = dialog.message();
      await dialog.accept();
    });

    await pom.pressShortcut("n");

    // Brief wait for dialog event to fire + handler to run
    await valeriaFullPage.waitForTimeout(500);

    expect(capturedMessage).toBe("Nueva conversación (próximamente)");
  });

  test("SC-9-3: aria-labels are Spanish neutro", async ({
    valeriaFullPage,
  }) => {
    const pom = new ValeriaSidebarPage(valeriaFullPage);
    await pom.goto({ valeriaState: "full", shellMode: "agentic" });

    // Aside label
    await expect(pom.sidebar).toHaveAttribute("aria-label", "Panel Valeria");

    // No aria-label should contain English
    const asidesWithAriaLabel = valeriaFullPage.locator(
      "[data-testid=valeria-sidebar] [aria-label]",
    );
    const count = await asidesWithAriaLabel.count();
    for (let i = 0; i < count; i++) {
      const label = await asidesWithAriaLabel.nth(i).getAttribute("aria-label");
      if (label) {
        // Must not contain raw English placeholder patterns
        for (const pattern of ENGLISH_PLACEHOLDER_PATTERNS) {
          expect(label).not.toMatch(pattern);
        }
      }
    }
  });

  test("SC-9-4: live region text is Spanish neutro per valeriaState", async ({
    valeriaFullPage,
  }) => {
    const pom = new ValeriaSidebarPage(valeriaFullPage);

    // full → 'Valeria con historial'
    await pom.goto({ valeriaState: "full", shellMode: "agentic" });
    await expect(
      valeriaFullPage
        .getByRole("status")
        .filter({ hasText: "Valeria con historial" }),
    ).toBeAttached();

    // rail → 'Valeria abierta'
    await pom.goto({ valeriaState: "rail", shellMode: "agentic" });
    await expect(
      valeriaFullPage
        .getByRole("status")
        .filter({ hasText: "Valeria abierta" }),
    ).toBeAttached();

    // collapsed → 'Valeria cerrada'
    await pom.goto({ valeriaState: "collapsed", shellMode: "web" });
    await expect(
      valeriaFullPage
        .getByRole("status")
        .filter({ hasText: "Valeria cerrada" }),
    ).toBeAttached();
  });

  test("SC-9-5: zero voseo patterns in rendered sidebar text", async ({
    valeriaFullPage,
  }) => {
    const pom = new ValeriaSidebarPage(valeriaFullPage);
    await pom.goto({ valeriaState: "full", shellMode: "agentic" });

    // Get all text content from the sidebar
    const sidebarText = (await pom.sidebar.textContent()) ?? "";

    for (const pattern of VOSEO_PATTERNS) {
      expect(
        sidebarText,
        `Voseo pattern ${pattern} found in sidebar text`,
      ).not.toMatch(pattern);
    }
  });

  test("SC-9-6: zero English placeholders in sidebar text", async ({
    valeriaFullPage,
  }) => {
    const pom = new ValeriaSidebarPage(valeriaFullPage);
    await pom.goto({ valeriaState: "full", shellMode: "agentic" });

    const sidebarText = (await pom.sidebar.textContent()) ?? "";

    for (const pattern of ENGLISH_PLACEHOLDER_PATTERNS) {
      expect(
        sidebarText,
        `English placeholder pattern ${pattern} found in sidebar text`,
      ).not.toMatch(pattern);
    }

    // Verify expected Spanish strings are present
    for (const str of EXPECTED_STRINGS) {
      expect(sidebarText).toContain(str);
    }
  });
});
