// voseo-allowed: test fixture that detects voseo in UI — glosario list is test data, not user-facing copy
/**
 * lisa-marca-i18n.spec.ts — SC-11 i18n Spanish neutro verification
 *
 * Gherkin: "Dado que la interfaz está en español neutro LatAm,
 *           cuando el propietario navega por las sub-sub-tabs de Marca,
 *           entonces todos los textos visibles usan tuteo (no voseo)
 *           y ortografía correcta (tildes, ñ, ¿¡)."
 *
 * Validators: e2e_i18n_spanish_neutro + arch_spanish_neutro_pre_commit
 *
 * POMs: LisaMarcaPage
 *
 * Note: This test scans visible text at runtime. The pre-commit hook
 * (arch_spanish_neutro_pre_commit) scans static source files.
 * Both layers are complementary.
 *
 * downstream-regression-na: brand-local vitalia e2e spec F2-S7
 *
 * @see 04-validators.yaml § test_construction_plan step 19
 */

import {
  test,
  expect,
  gotoMarca,
  LISA_MARCA_FIXTURE,
} from "./fixtures/lisa-marca.fixture";
import { LisaMarcaPage } from "./poms/lisa-marca-page.pom";

// ---------------------------------------------------------------------------
// Voseo detection list (from .claude/rules/spanish-text.md glosario)
// ---------------------------------------------------------------------------

const VOSEO_IMPERATIVES = [
  "configurá",
  "agregá",
  "escribí",
  "guardá",
  "revisá",
  "seleccioná",
  "elegí",
  "mirá",
  "dejá",
  "poné",
  "usá",
  "hacé",
  "empezá",
  "arrancá",
  "subí",
  "bajá",
  "abrí",
  "volvé",
  "andá",
  "cambiá",
  "linkeá",
  "marcá",
  "compartí",
  "contá",
  "explicá",
  "mostrá",
  "probá",
];

/**
 * Scans all visible text content on the page for voseo imperatives.
 * Returns list of matches found.
 */
async function scanForVoseo(
  page: import("@playwright/test").Page,
): Promise<string[]> {
  const visibleText = await page.evaluate(() => {
    const walker = document.createTreeWalker(
      document.body,
      NodeFilter.SHOW_TEXT,
      {
        acceptNode: (node) => {
          const parent = node.parentElement;
          if (!parent) return NodeFilter.FILTER_REJECT;
          // Skip hidden, script, style elements
          const style = window.getComputedStyle(parent);
          if (style.display === "none" || style.visibility === "hidden") {
            return NodeFilter.FILTER_REJECT;
          }
          const tag = parent.tagName.toLowerCase();
          if (["script", "style", "noscript"].includes(tag)) {
            return NodeFilter.FILTER_REJECT;
          }
          return NodeFilter.FILTER_ACCEPT;
        },
      },
    );

    const texts: string[] = [];
    let node = walker.nextNode();
    while (node) {
      const text = (node.textContent ?? "").trim().toLowerCase();
      if (text.length > 0) {
        texts.push(text);
      }
      node = walker.nextNode();
    }
    return texts;
  });

  const matches: string[] = [];
  for (const text of visibleText) {
    for (const voseo of VOSEO_IMPERATIVES) {
      // Match word boundary (not partial — e.g. "arranca" vs "arrancá")
      const regex = new RegExp(`\\b${voseo}\\b`, "i");
      if (regex.test(text)) {
        matches.push(`"${voseo}" found in: "${text.substring(0, 60)}"`);
      }
    }
  }
  return matches;
}

// ---------------------------------------------------------------------------
// Test suite — SC-11: i18n Spanish neutro verification
// ---------------------------------------------------------------------------

test.describe("SC-11 — Español neutro LatAm: verificación de voseo en la UI", () => {
  test("identidad no contiene voseo en textos visibles", async ({
    marcaPage,
  }) => {
    const marcaPagePom = new LisaMarcaPage(
      marcaPage,
      LISA_MARCA_FIXTURE.tenantId,
    );

    await gotoMarca(marcaPage, LISA_MARCA_FIXTURE.tenantId, "identidad");
    await marcaPagePom.waitForLoaded();

    const voseoMatches = await scanForVoseo(marcaPage);

    // Report all matches as a clear failure message
    if (voseoMatches.length > 0) {
      const summary = voseoMatches.join("\n");
      expect(voseoMatches).toHaveLength(0);
      // If test fails, the message will include the summary
      console.error(`Voseo found in identidad:\n${summary}`);
    }

    expect(voseoMatches).toHaveLength(0);
  });

  test("voz-y-tono no contiene voseo en textos visibles de la UI", async ({
    marcaPage,
  }) => {
    const marcaPagePom = new LisaMarcaPage(
      marcaPage,
      LISA_MARCA_FIXTURE.tenantId,
    );

    await gotoMarca(marcaPage, LISA_MARCA_FIXTURE.tenantId, "voz-y-tono");
    await marcaPagePom.waitForLoaded();

    const voseoMatches = await scanForVoseo(marcaPage);
    expect(voseoMatches).toHaveLength(0);
  });

  test("presencia no contiene voseo en textos visibles", async ({
    marcaPage,
  }) => {
    const marcaPagePom = new LisaMarcaPage(
      marcaPage,
      LISA_MARCA_FIXTURE.tenantId,
    );

    await gotoMarca(marcaPage, LISA_MARCA_FIXTURE.tenantId, "presencia");
    await marcaPagePom.waitForLoaded();

    const voseoMatches = await scanForVoseo(marcaPage);
    expect(voseoMatches).toHaveLength(0);
  });

  test("los labels del SubSubTabsBar están en español neutro correcto", async ({
    marcaPage,
  }) => {
    const marcaPagePom = new LisaMarcaPage(
      marcaPage,
      LISA_MARCA_FIXTURE.tenantId,
    );

    await gotoMarca(marcaPage, LISA_MARCA_FIXTURE.tenantId, "identidad");
    await marcaPagePom.waitForLoaded();

    // Get SubSubTabsBar text content
    const tabsBarText =
      await marcaPagePom.subsubtabsBar.textContent();
    if (tabsBarText) {
      const lowerText = tabsBarText.toLowerCase();
      // Verify expected tab labels in Spanish
      expect(lowerText).toContain("identidad");
      expect(lowerText).toContain("voz");
      expect(lowerText).toContain("presencia");
    }
  });

  test("los placeholders de los inputs usan tuteo", async ({ marcaPage }) => {
    const marcaPagePom = new LisaMarcaPage(
      marcaPage,
      LISA_MARCA_FIXTURE.tenantId,
    );

    await gotoMarca(marcaPage, LISA_MARCA_FIXTURE.tenantId, "identidad");
    await marcaPagePom.waitForLoaded();

    // Collect all placeholder texts
    const placeholders = await marcaPage.evaluate(() => {
      const inputs = Array.from(
        document.querySelectorAll("input[placeholder], textarea[placeholder]"),
      );
      return inputs
        .map((el) => (el as HTMLInputElement).placeholder)
        .filter(Boolean);
    });

    for (const placeholder of placeholders) {
      const lower = placeholder.toLowerCase();
      for (const voseo of VOSEO_IMPERATIVES) {
        const regex = new RegExp(`\\b${voseo}\\b`, "i");
        expect(regex.test(lower)).toBe(false);
      }
    }
  });

  test("los mensajes de error de validación usan tuteo", async ({
    marcaPage,
  }) => {
    const marcaPagePom = new LisaMarcaPage(
      marcaPage,
      LISA_MARCA_FIXTURE.tenantId,
    );

    await gotoMarca(marcaPage, LISA_MARCA_FIXTURE.tenantId, "identidad");
    await marcaPagePom.waitForLoaded();

    // Trigger a validation error by filling an invalid value and blurring
    const nameInput = marcaPage.locator(
      '#brand-name-input',
    );

    // Clear the field to trigger required validation
    await nameInput.fill("");
    await nameInput.press("Tab"); // Blur to trigger validation

    // Check for any validation error messages
    const errorMessages = await marcaPage.$$eval(
      '[role="alert"], [data-testid*="error"], .form-error',
      (els) =>
        els
          .map((el) => el.textContent ?? "")
          .filter((t) => t.trim().length > 0),
    );

    for (const msg of errorMessages) {
      const lower = msg.toLowerCase();
      for (const voseo of VOSEO_IMPERATIVES) {
        const regex = new RegExp(`\\b${voseo}\\b`, "i");
        if (regex.test(lower)) {
          expect(
            false,
            `Voseo "${voseo}" found in error message: "${msg}"`,
          ).toBe(true);
        }
      }
    }
  });

  test("las tildes en textos de la UI son correctas (ortografía)", async ({
    marcaPage,
  }) => {
    const marcaPagePom = new LisaMarcaPage(
      marcaPage,
      LISA_MARCA_FIXTURE.tenantId,
    );

    await gotoMarca(marcaPage, LISA_MARCA_FIXTURE.tenantId, "identidad");
    await marcaPagePom.waitForLoaded();

    // Common words that should have tildes — check they're NOT written without them
    const incorrectForms = [
      "configuracion", // should be "configuración"
      "informacion", // should be "información"
      "descripcion", // should be "descripción"
      "personalizacion", // should be "personalización"
      "visualizacion", // should be "visualización"
    ];

    const allText = await marcaPage.evaluate(
      () => document.body.textContent ?? "",
    );
    const lowerText = allText.toLowerCase();

    for (const incorrect of incorrectForms) {
      // Only flag if we find the incorrect form but not the correct one
      if (lowerText.includes(incorrect)) {
        const correctForm = `${incorrect.slice(0, -4)}ción`;
        // This is informational — the page text should use the accented form
        expect(lowerText).toContain(correctForm);
      }
    }
  });
});
