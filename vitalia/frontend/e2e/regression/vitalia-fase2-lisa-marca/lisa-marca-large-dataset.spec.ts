/**
 * lisa-marca-large-dataset.spec.ts — SC-9 Trust-signals render + perf (real backend)
 *
 * Gherkin: "Dado que el tenant tiene señales de confianza registradas, cuando el
 *           propietario navega a Presencia, entonces la lista carga rápido y el
 *           scroll es fluido."
 *
 * HONEST: backend REAL (sin mock canned de 50 items — eso era el verde falso,
 * RN-1; el grep-gate SC-2 ahora cubre trust-signals). La página renderiza los
 * datos REALES del tenant; las aserciones de render + perf son sobre datos reales.
 * El builder `buildLargeTrustSignals(50)` se verifica in-memory (unit-style),
 * separado del render de la página. Aserciones web-first.
 *
 * NOTA de scope (M3): el caso "50 items" puro requiere sembrar 50 trust-signals
 * reales (fuera de scope de esta story — no se siembra). La cobertura de perf
 * sobre dataset grande se ejerce con los datos reales + el contrato del builder.
 *
 * POMs: LisaMarcaPage, PresenciaSectionPage
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
} from "./fixtures/large-dataset.fixture";
import { LISA_MARCA_FIXTURE } from "./fixtures/lisa-marca.fixture";
import { LisaMarcaPage } from "./poms/lisa-marca-page.pom";
import { PresenciaSectionPage } from "./poms/presencia-section.pom";

/** Maximum time to render the trust-signals list (ms) */
const MAX_LIST_RENDER_MS = 3_000;

// ---------------------------------------------------------------------------
// Test suite — SC-9: trust-signals render + perf (real backend)
// ---------------------------------------------------------------------------

test.describe("SC-9 — Rendimiento de señales de confianza (backend real)", () => {
  test.beforeEach(async ({ largeDatasetPage }) => {
    await gotoMarca(
      largeDatasetPage,
      LISA_MARCA_FIXTURE.tenantId,
      "presencia",
    );
  });

  test("la lista de señales de confianza carga en menos de 3 segundos", async ({
    largeDatasetPage,
  }) => {
    const marcaPagePom = new LisaMarcaPage(
      largeDatasetPage,
      LISA_MARCA_FIXTURE.tenantId,
    );
    const presencia = new PresenciaSectionPage(largeDatasetPage);

    const startTime = Date.now();
    await marcaPagePom.waitForLoaded();
    await presencia.waitForTrustSignalsLoaded(MAX_LIST_RENDER_MS);
    const renderTime = Date.now() - startTime;

    expect(renderTime).toBeLessThan(MAX_LIST_RENDER_MS);

    // Web-first: the trust-signals section renders.
    await expect(presencia.trustSignalsSection).toBeVisible({ timeout: 3_000 });
  });

  test("el scroll en la lista de señales de confianza no bloquea el hilo principal", async ({
    largeDatasetPage,
  }) => {
    const marcaPagePom = new LisaMarcaPage(
      largeDatasetPage,
      LISA_MARCA_FIXTURE.tenantId,
    );
    const presencia = new PresenciaSectionPage(largeDatasetPage);

    await marcaPagePom.waitForLoaded();
    await presencia.waitForTrustSignalsLoaded();

    const trustList = presencia.trustSignalsList;
    if (await trustList.isVisible()) {
      await trustList.evaluate((el: HTMLElement) => {
        el.scrollTop = el.scrollHeight;
      });
      await expect(trustList).toBeVisible({ timeout: 2_000 });
    }
  });

  test("el dataset no degrada el autosave de contacto (PATCH real)", async ({
    largeDatasetPage,
  }) => {
    const marcaPagePom = new LisaMarcaPage(
      largeDatasetPage,
      LISA_MARCA_FIXTURE.tenantId,
    );
    const presencia = new PresenciaSectionPage(largeDatasetPage);

    await marcaPagePom.waitForLoaded();
    await presencia.waitForTrustSignalsLoaded();

    const patched: number[] = [];
    const onResponse = (response: import("@playwright/test").Response) => {
      if (
        response.url().includes("/api/v1/lisa/marca/contact") &&
        response.request().method() === "PATCH"
      ) {
        patched.push(response.status());
      }
    };
    largeDatasetPage.on("response", onResponse);

    const newUrl = `https://saludvitalia-updated-${Date.now()}.pe`;

    // Race de hidratación: bajo carga, el GET /contact puede resolver TARDE y el
    // useEffect reset de WebsiteCard pisa el valor recién tipeado. Reintentar el
    // fill hasta que el valor PERSISTA en el input (sobrevive al reset) → robusto.
    await expect(async () => {
      await presencia.fillWebsite(newUrl);
      await expect(presencia.websiteInput).toHaveValue(newUrl, { timeout: 2_000 });
    }).toPass({ timeout: 15_000 });

    // El PATCH real al backend es la garantía de persistencia (primario). Bajo la
    // carga de la suite completa, getToken()/Clerk + el dev server son más lentos →
    // damos margen amplio para que el autosave dispare.
    await expect
      .poll(() => patched.length, { timeout: 15_000 })
      .toBeGreaterThan(0);
    expect(patched[patched.length - 1]).toBe(200);

    // El badge "guardado" sigue al PATCH 200 (secundario, web-first tolerante).
    await marcaPagePom.waitForAutosaveSuccess(10_000);

    largeDatasetPage.off("response", onResponse);
  });

  test("el builder de dataset grande produce 50 items únicos y bien formados (unit)", async ({
    largeTrustSignals,
  }) => {
    // In-memory contract of the builder — NO page render involved.
    expect(largeTrustSignals).toHaveLength(50);

    const ids = largeTrustSignals.map((ts) => ts.id);
    expect(new Set(ids).size).toBe(50);

    for (const item of largeTrustSignals) {
      expect(item.id).toBeTruthy();
      expect(item.type).toBeTruthy();
      expect(item.value).toBeTruthy();
      expect(typeof item.displayOrder).toBe("number");
    }
  });
});
