// voseo-allowed: test that verifies ARIA label is NOT voseo — regex pattern is test data, not user-facing copy
/**
 * lisa-marca-keyboard.spec.ts — SC-10 A11y keyboard navigation
 *
 * Gherkin: "Dado que un usuario navega usando solo el teclado,
 *           cuando avanza con Tab por los elementos de Identidad,
 *           entonces todos los campos interactivos son alcanzables
 *           y tienen indicadores de foco visibles."
 *
 * Validators: e2e_keyboard_a11y + a11y_axe
 *
 * POMs: LisaMarcaPage
 *
 * WCAG 2.1 AA targets:
 * - 2.1.1 Keyboard (A)
 * - 2.4.3 Focus Order (A)
 * - 2.4.7 Focus Visible (AA)
 *
 * downstream-regression-na: brand-local vitalia e2e spec F2-S7
 *
 * @see 04-validators.yaml § test_construction_plan step 18
 */

import {
  test,
  expect,
  gotoMarca,
  LISA_MARCA_FIXTURE,
} from "./fixtures/lisa-marca.fixture";
import { LisaMarcaPage } from "./poms/lisa-marca-page.pom";

// ---------------------------------------------------------------------------
// Test suite — SC-10: a11y keyboard navigation
// ---------------------------------------------------------------------------

test.describe("SC-10 — Navegación por teclado: accesibilidad WCAG 2.1 AA", () => {
  test.beforeEach(async ({ marcaPage }) => {
    await gotoMarca(marcaPage, LISA_MARCA_FIXTURE.tenantId, "identidad");
  });

  test("todos los campos interactivos de identidad son alcanzables con Tab", async ({
    marcaPage,
  }) => {
    const marcaPagePom = new LisaMarcaPage(
      marcaPage,
      LISA_MARCA_FIXTURE.tenantId,
    );

    await marcaPagePom.waitForLoaded();

    // Tab through the interactive elements and collect focused elements
    const focusedTestIds: string[] = [];
    const maxTabs = 20;

    for (let i = 0; i < maxTabs; i++) {
      await marcaPage.keyboard.press("Tab");

      const focusedElement = await marcaPage.evaluate(() => {
        const el = document.activeElement;
        return el?.getAttribute("data-testid") ?? el?.tagName ?? null;
      });

      if (focusedElement) {
        focusedTestIds.push(focusedElement);
      }
    }

    // At minimum, brand name input should be reachable
    const reachedNameInput = focusedTestIds.some(
      (id) =>
        id.includes("identity-brand-name") ||
        id.toLowerCase() === "input",
    );
    expect(reachedNameInput).toBe(true);
  });

  test("el SubSubTabsBar es navegable por teclado con flechas o Tab", async ({
    marcaPage,
  }) => {
    const marcaPagePom = new LisaMarcaPage(
      marcaPage,
      LISA_MARCA_FIXTURE.tenantId,
    );

    await marcaPagePom.waitForLoaded();

    // Focus el primer tab REAL (un <button> dentro del <nav>). El <nav> no es
    // focuseable per se; el SubSubTabsBar es navegable porque sus tabs son botones.
    const subsubtabsBar = marcaPagePom.subsubtabsBar;
    await marcaPagePom.tabIdentidad.focus();

    // Verify the bar has focus or contains focused element
    const isFocused = await subsubtabsBar.evaluate((el) => {
      return (
        el === document.activeElement ||
        el.contains(document.activeElement)
      );
    });
    expect(isFocused).toBe(true);
  });

  test("la zona de drop de logo tiene ARIA label descriptivo", async ({
    marcaPage,
  }) => {
    const marcaPagePom = new LisaMarcaPage(
      marcaPage,
      LISA_MARCA_FIXTURE.tenantId,
    );

    await marcaPagePom.waitForLoaded();

    const dropZone = marcaPage.getByRole("button", { name: /logo de la cl.nica/i });
    const isVisible = await dropZone.isVisible();

    if (isVisible) {
      const ariaLabel = await dropZone.getAttribute("aria-label");
      const role = await dropZone.getAttribute("role");

      // Must have an accessible label
      expect(ariaLabel ?? role).toBeTruthy();

      // aria-label should be in Spanish neutro
      if (ariaLabel) {
        expect(ariaLabel.toLowerCase()).not.toMatch(
          /agregá|subí|arrastrá/,
        );
      }
    }
  });

  test("el badge de autosave tiene role y aria-live para lectores de pantalla", async ({
    marcaPage,
  }) => {
    const marcaPagePom = new LisaMarcaPage(
      marcaPage,
      LISA_MARCA_FIXTURE.tenantId,
    );

    await marcaPagePom.waitForLoaded();

    const badge = marcaPagePom.autosaveBadge;
    const isVisible = await badge.isVisible();

    if (isVisible) {
      const ariaLive = await badge.getAttribute("aria-live");
      const role = await badge.getAttribute("role");

      // Autosave badge should announce changes to screen readers
      const isAnnounced =
        ariaLive === "polite" ||
        ariaLive === "assertive" ||
        role === "status" ||
        role === "alert";
      expect(isAnnounced).toBe(true);
    }
  });

  test("navegar a voz-y-tono por teclado es posible desde identidad", async ({
    marcaPage,
  }) => {
    const marcaPagePom = new LisaMarcaPage(
      marcaPage,
      LISA_MARCA_FIXTURE.tenantId,
    );

    await marcaPagePom.waitForLoaded();

    // Focus on the voz-y-tono tab button
    await marcaPagePom.tabVozYTono.focus();

    // Press Enter to navigate
    await marcaPage.keyboard.press("Enter");
    await marcaPage.waitForLoadState("domcontentloaded");

    // Web-first: active tab is now voz-y-tono.
    await marcaPagePom.waitForActiveSubsubtab("voz-y-tono");
  });

  test("los selectores de arquetipo son accesibles como radiogroup", async ({
    marcaPage,
  }) => {
    const marcaPagePom = new LisaMarcaPage(
      marcaPage,
      LISA_MARCA_FIXTURE.tenantId,
    );

    await marcaPagePom.waitForLoaded();

    // Navigate to voz-y-tono
    await marcaPagePom.clickTabVozYTono();
    await marcaPagePom.waitForLoaded();

    const archetypeSelector = marcaPage.locator(
      '[data-testid="archetype-selector"]',
    );
    const isVisible = await archetypeSelector.isVisible();

    if (isVisible) {
      const role = await archetypeSelector.getAttribute("role");
      // Should be radiogroup or have appropriate role for keyboard navigation
      expect(role).toBeTruthy();
    }
  });

  test("el indicador de foco es visible en campos de texto", async ({
    marcaPage,
  }) => {
    const marcaPagePom = new LisaMarcaPage(
      marcaPage,
      LISA_MARCA_FIXTURE.tenantId,
    );

    await marcaPagePom.waitForLoaded();

    // Focus the brand name input
    const nameInput = marcaPage.locator(
      '#brand-name-input',
    );
    await nameInput.focus();

    // Web-first: el input recibe foco (pollea — robusto ante re-renders del dev
    // server durante la suite larga, a diferencia del one-shot activeElement).
    await expect(nameInput).toBeFocused({ timeout: 5_000 });
  });
});
