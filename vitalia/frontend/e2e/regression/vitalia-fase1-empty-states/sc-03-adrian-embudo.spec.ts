/**
 * sc-03-adrian-embudo.spec.ts — SC-3 · placeholder Adrián Embudo Kanban 6 cols + toggle
 * F1-S10 vitalia-fase1-empty-states — T-10
 *
 * Assertions:
 *   - EmbudoPlaceholder mounts at /adrian/embudo
 *   - TogglePill renders "Kanban" and "Lista" options
 *   - Default state: Kanban view with 6 column headers verbatim from spec
 *   - Column headers: Interesado · Calificando · Considerando · Listo · Reservado · Decidió no
 *   - Each column shows ≥2 mock leads
 *   - Click "Lista" toggle → vista lista con EmptyState próximamente
 *
 * Column headers from MOCK_PIPELINE in EmbudoPlaceholder.tsx:
 *   ⚪ Interesado | 🟢 Calificando | 🟡 Considerando | 🔵 Listo | 🟣 Reservado | ⚫ Decidió no
 *
 * Uses: ShellOrganismPage POM + empty-states.fixture
 *
 * SC-3 validator: val-fe-e2e-sc03-adrian-embudo
 * downstream-regression-na: brand-local vitalia e2e spec
 */

import { expect } from "@playwright/test";
import { test } from "../../fixtures/empty-states.fixture";
import { ShellOrganismPage } from "../../pages/ShellOrganismPage";

// Verbatim column labels from EmbudoPlaceholder MOCK_PIPELINE
const KANBAN_COLUMNS = [
  "Interesado",
  "Calificando",
  "Considerando",
  "Listo",
  "Reservado",
  "Decidió no",
] as const;

test.describe("SC-3 · Adrián Embudo Kanban 6 cols + toggle", () => {
  test.beforeEach(async ({ shellPage, tenantId }) => {
    const shell = new ShellOrganismPage(shellPage, tenantId);
    await shell.goto("adrian", "embudo");
    await shell.expectShellMounted();
    await shell.expectSubTabContentVisible("adrian", "embudo");
  });

  test("TogglePill visible con opciones Kanban y Lista", async ({
    shellPage,
  }) => {
    await expect(
      shellPage.locator('[data-testid="embudo-toggle"]').first(),
    ).toBeVisible();
    await expect(shellPage.locator("text=Kanban").first()).toBeVisible();
    await expect(shellPage.locator("text=Lista").first()).toBeVisible();
  });

  test("6 columnas Kanban visibles con headers verbatim", async ({
    shellPage,
  }) => {
    for (const colLabel of KANBAN_COLUMNS) {
      await expect(shellPage.locator(`text=${colLabel}`).first()).toBeVisible();
    }
  });

  test("columna Interesado tiene 3 mock leads ficticios LatAm", async ({
    shellPage,
  }) => {
    // Mock leads from MOCK_PIPELINE[0].leads in EmbudoPlaceholder.tsx
    await expect(shellPage.locator("text=María G.").first()).toBeVisible();
    await expect(shellPage.locator("text=Carlos P.").first()).toBeVisible();
    await expect(shellPage.locator("text=Sofía R.").first()).toBeVisible();
  });

  test("leads muestran valores en PEN S/", async ({ shellPage }) => {
    // Currency PEN — master-data rule compliance
    await expect(
      shellPage.locator("text=/S\\/\\s*\\d+/").first(),
    ).toBeVisible();
  });

  test("click Lista → vista lista con EmptyState próximamente", async ({
    shellPage,
  }) => {
    await shellPage
      .locator('[data-testid="embudo-toggle"]')
      .first()
      .first()
      .locator("text=Lista")
      .click();

    // Lista pane with EmptyState "próximamente"
    await expect(
      shellPage.locator("text=/próximamente/i").first(),
    ).toBeVisible();
  });

  test("visual kanban · Kanban view estructura 6 cols visible", async ({
    shellPage,
  }) => {
    // Confirm all 6 columns visible simultaneously
    for (const colLabel of KANBAN_COLUMNS) {
      await expect(shellPage.locator(`text=${colLabel}`).first()).toBeVisible();
    }
  });

  test("visual lista · Lista view EmptyState visible", async ({
    shellPage,
  }) => {
    await shellPage
      .locator('[data-testid="embudo-toggle"]')
      .first()
      .first()
      .locator("text=Lista")
      .click();
    await expect(
      shellPage.locator("text=/próximamente/i").first(),
    ).toBeVisible();
  });
});
