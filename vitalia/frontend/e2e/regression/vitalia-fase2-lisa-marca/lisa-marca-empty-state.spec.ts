// voseo-allowed: test that asserts absence of voseo imperatives in empty-state CTA — regex patterns are test data
/**
 * lisa-marca-empty-state.spec.ts — SC-8 Empty state copy (real backend)
 *
 * Gherkin: "Dado que un tenant accede a las sub-sub-tabs de lisa/marca,
 *           cuando una sección no tiene datos,
 *           entonces se muestra el estado vacío apropiado con CTA en español neutro."
 *
 * HONEST: backend REAL (sin mock del backend-bajo-prueba). El estado vacío
 * genuino requiere un tenant sin configurar — el tenant de prueba tiene seed, así
 * que NO se puede fingir vacío mockeando los reads (eso era el verde falso, RN-1).
 * Por eso este spec verifica lo que SÍ es comprobable con datos reales: los
 * placeholders y los CTA de estado-vacío están en español neutro (sin voseo), y
 * la lógica de empty-state es tolerante (renderiza lista O empty-state según el
 * estado real). Aserciones web-first.
 *
 * POMs: LisaMarcaPage, IdentidadSectionPage, PresenciaSectionPage
 *
 * downstream-regression-na: brand-local vitalia e2e spec F2-S7
 *
 * @see e2e/fixtures/real-backend-forward.fixture.ts
 * @see 06-tickets.yaml T-1 deliverable 4
 */

import {
  test,
  expect,
  gotoMarca,
  LISA_MARCA_FIXTURE,
} from "./fixtures/lisa-marca.fixture";
import { LisaMarcaPage } from "./poms/lisa-marca-page.pom";
import { IdentidadSectionPage } from "./poms/identidad-section.pom";
import { PresenciaSectionPage } from "./poms/presencia-section.pom";

// Voseo imperatives que NO deben aparecer en CTAs / placeholders de empty-state.
const VOSEO_IMPERATIVES =
  /agregá|escribí|configurá|ponés|hacés|empezá|hacé|subí|arrastrá/;

// ---------------------------------------------------------------------------
// Test suite — SC-8: empty state copy (real backend)
// ---------------------------------------------------------------------------

test.describe("SC-8 — Estado vacío: copy en español neutro (backend real)", () => {
  test.beforeEach(async ({ marcaPage }) => {
    await gotoMarca(marcaPage, LISA_MARCA_FIXTURE.tenantId, "identidad");
  });

  test("identidad muestra placeholders en español neutro (sin voseo)", async ({
    marcaPage,
  }) => {
    const marcaPagePom = new LisaMarcaPage(
      marcaPage,
      LISA_MARCA_FIXTURE.tenantId,
    );
    const identidad = new IdentidadSectionPage(marcaPage);

    await marcaPagePom.waitForLoaded();

    const namePlaceholder =
      await identidad.nameInput.getAttribute("placeholder");
    if (namePlaceholder) {
      expect(namePlaceholder.toLowerCase()).not.toMatch(VOSEO_IMPERATIVES);
    }
  });

  test("presencia: la sección trust-signals renderiza (lista o estado vacío)", async ({
    marcaPage,
  }) => {
    const marcaPagePom = new LisaMarcaPage(
      marcaPage,
      LISA_MARCA_FIXTURE.tenantId,
    );

    await marcaPagePom.waitForLoaded();
    await marcaPagePom.clickTabPresencia();
    await marcaPagePom.waitForActiveSubsubtab("presencia");

    const presencia = new PresenciaSectionPage(marcaPage);
    await presencia.waitForTrustSignalsLoaded();

    // Web-first: la sección renderiza (lista O empty-state según datos reales).
    await expect(presencia.trustSignalsSection).toBeVisible({ timeout: 10_000 });
  });

  test("los campos de identidad permiten escribir y el autosave funciona", async ({
    marcaPage,
  }) => {
    const marcaPagePom = new LisaMarcaPage(
      marcaPage,
      LISA_MARCA_FIXTURE.tenantId,
    );
    const identidad = new IdentidadSectionPage(marcaPage);

    await marcaPagePom.waitForLoaded();

    const patched: number[] = [];
    const onResponse = (response: import("@playwright/test").Response) => {
      if (
        response.url().includes("/api/v1/lisa/marca/identity") &&
        response.request().method() === "PATCH"
      ) {
        patched.push(response.status());
      }
    };
    marcaPage.on("response", onResponse);

    const newName = `Nueva clínica ${Date.now()}`;
    await identidad.fillName(newName);
    await marcaPagePom.waitForAutosaveSuccess();

    await expect
      .poll(() => patched.length, { timeout: 5_000 })
      .toBeGreaterThan(0);
    expect(patched[patched.length - 1]).toBe(200);

    marcaPage.off("response", onResponse);
  });

  test("el CTA de estado-vacío de presencia (si aparece) no usa voseo", async ({
    marcaPage,
  }) => {
    const marcaPagePom = new LisaMarcaPage(
      marcaPage,
      LISA_MARCA_FIXTURE.tenantId,
    );

    await marcaPagePom.waitForLoaded();
    await marcaPagePom.clickTabPresencia();
    await marcaPagePom.waitForActiveSubsubtab("presencia");

    const presencia = new PresenciaSectionPage(marcaPage);
    await presencia.waitForTrustSignalsLoaded();

    const isEmpty = await presencia.isTrustSignalsEmptyStateVisible();
    if (isEmpty) {
      const emptyStateText =
        await presencia.trustSignalsEmptyState.textContent();
      if (emptyStateText) {
        expect(emptyStateText.toLowerCase()).not.toMatch(VOSEO_IMPERATIVES);
      }
    }
  });
});
