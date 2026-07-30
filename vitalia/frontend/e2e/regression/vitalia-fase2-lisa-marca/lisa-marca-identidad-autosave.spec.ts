/**
 * lisa-marca-identidad-autosave.spec.ts — SC-1 Happy path: autosave identity (real backend)
 *
 * Gherkin: "Dado que el propietario edita el nombre de la marca,
 *           cuando el debounce de 600ms expira,
 *           entonces el badge muestra 'Guardado' y el PATCH fue enviado."
 *
 * HONEST: backend REAL (sin mock del backend-bajo-prueba). El transporte (auth +
 * forwarding a :8002 + gate anti-burbuja base.ts) se compone desde
 * `real-backend-forward.fixture`. Round-trip real: editar → autosave → recargar
 * → persiste. Aserciones web-first sobre estado hidratado (RN-1, RN-3).
 *
 * POMs: LisaMarcaPage, IdentidadSectionPage
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

// ---------------------------------------------------------------------------
// Test suite — SC-1: happy autosave identity (real backend)
// ---------------------------------------------------------------------------

test.describe("SC-1 — Autosave identidad: nombre de marca", () => {
  test.beforeEach(async ({ marcaPage }) => {
    await gotoMarca(marcaPage, LISA_MARCA_FIXTURE.tenantId, "identidad");
  });

  test("edita el nombre de la marca y el autosave persiste en 600ms", async ({
    marcaPage,
  }) => {
    const marcaPagePom = new LisaMarcaPage(
      marcaPage,
      LISA_MARCA_FIXTURE.tenantId,
    );
    const identidad = new IdentidadSectionPage(marcaPage);

    await marcaPagePom.waitForLoaded();

    // Capture PATCH responses on the real backend (RN-4: cleaned up at end).
    const identityPatch: { status: number }[] = [];
    const onResponse = (response: import("@playwright/test").Response) => {
      if (
        response.url().includes("/api/v1/lisa/marca/identity") &&
        response.request().method() === "PATCH"
      ) {
        identityPatch.push({ status: response.status() });
      }
    };
    marcaPage.on("response", onResponse);

    // Edit the brand name with a unique value so the round-trip is observable.
    const newName = `Salud Vitalia Premium ${Date.now()}`;
    await identidad.fillName(newName);

    // Web-first: badge transitions to saved (saving may be too brief on localhost).
    await marcaPagePom.waitForAutosaveSaving().catch(() => {
      /* saving too brief on localhost — proceed to success check */
    });
    await marcaPagePom.waitForAutosaveSuccess();

    // The PATCH was actually sent to the real backend and returned 200.
    await expect
      .poll(() => identityPatch.length, {
        timeout: 5_000,
        message: "PATCH /identity must have been sent to the real backend",
      })
      .toBeGreaterThan(0);
    expect(identityPatch[identityPatch.length - 1]?.status).toBe(200);

    const badgeText = await marcaPagePom.getAutosaveBadgeText();
    expect(badgeText).toMatch(/Guardado/i);

    // Web-first: the input keeps the new value (no revert).
    await expect(identidad.nameInput).toHaveValue(newName, { timeout: 5_000 });

    marcaPage.off("response", onResponse);
  });

  test("edita el tagline y el badge de autosave transiciona a estado guardado", async ({
    marcaPage,
  }) => {
    const marcaPagePom = new LisaMarcaPage(
      marcaPage,
      LISA_MARCA_FIXTURE.tenantId,
    );
    const identidad = new IdentidadSectionPage(marcaPage);

    await marcaPagePom.waitForLoaded();

    const identityPatch: { status: number }[] = [];
    const onResponse = (response: import("@playwright/test").Response) => {
      if (
        response.url().includes("/api/v1/lisa/marca/identity") &&
        response.request().method() === "PATCH"
      ) {
        identityPatch.push({ status: response.status() });
      }
    };
    marcaPage.on("response", onResponse);

    // Write-then-assert (RN-6): el tenant de test puede estar vacío y el form
    // exige un brand_name válido para que el autosave dispare. Sembramos un
    // nombre válido primero (auto-contenido, sin depender de otro test ni seed).
    await identidad.fillName(`Salud Vitalia ${Date.now()}`);
    await expect
      .poll(() => identityPatch.length, {
        timeout: 6_000,
        message: "el PATCH de siembra del nombre debe llegar al backend real",
      })
      .toBeGreaterThan(0);
    const patchesAfterSeed = identityPatch.length;

    // Ahora editamos el tagline → debe disparar un PATCH NUEVO.
    const newTagline = `Tu salud, nuestro compromiso ${Date.now()}`;
    await identidad.fillTagline(newTagline);

    await expect
      .poll(() => identityPatch.length, {
        timeout: 6_000,
        message: "editar el tagline debe disparar un PATCH adicional",
      })
      .toBeGreaterThan(patchesAfterSeed);
    expect(identityPatch[identityPatch.length - 1]?.status).toBe(200);
    await marcaPagePom.waitForAutosaveSuccess();
    await expect(identidad.taglineInput).toHaveValue(newTagline, {
      timeout: 5_000,
    });

    marcaPage.off("response", onResponse);
  });

  test("el tab activo en SubSubTabsBar es 'identidad' al navegar directamente", async ({
    marcaPage,
  }) => {
    const marcaPagePom = new LisaMarcaPage(
      marcaPage,
      LISA_MARCA_FIXTURE.tenantId,
    );

    await marcaPagePom.waitForLoaded();

    // Web-first: SubSubTabsBar marks identidad active.
    await marcaPagePom.waitForActiveSubsubtab("identidad");
  });

  test("los datos de identidad se cargan desde el backend al montar", async ({
    marcaPage,
  }) => {
    const marcaPagePom = new LisaMarcaPage(
      marcaPage,
      LISA_MARCA_FIXTURE.tenantId,
    );
    const identidad = new IdentidadSectionPage(marcaPage);

    await marcaPagePom.waitForLoaded();

    // Round-trip honesto (RN-6, write-then-reload-then-assert): en vez de asumir
    // un seed pre-existente, escribimos un nombre único, esperamos el PATCH real,
    // recargamos, y verificamos que el backend lo hidrató de vuelta (persistió).
    const seededName = `Carga Vitalia ${Date.now()}`;
    const identityPatch: { status: number }[] = [];
    const onResponse = (response: import("@playwright/test").Response) => {
      if (
        response.url().includes("/api/v1/lisa/marca/identity") &&
        response.request().method() === "PATCH"
      ) {
        identityPatch.push({ status: response.status() });
      }
    };
    marcaPage.on("response", onResponse);

    await identidad.fillName(seededName);
    await expect
      .poll(() => identityPatch.length, { timeout: 6_000 })
      .toBeGreaterThan(0);
    expect(identityPatch[identityPatch.length - 1]?.status).toBe(200);
    marcaPage.off("response", onResponse);

    // Recargar y verificar que el backend devuelve el valor recién guardado.
    await marcaPage.reload();
    await marcaPage.waitForLoadState("domcontentloaded");
    await marcaPagePom.waitForLoaded();
    await expect(identidad.nameInput).toHaveValue(seededName, {
      timeout: 10_000,
    });
  });
});
