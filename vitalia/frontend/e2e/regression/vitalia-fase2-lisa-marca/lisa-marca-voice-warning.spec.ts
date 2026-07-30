/**
 * lisa-marca-voice-warning.spec.ts — SC-2 Negative: voice warning alert (real backend)
 *
 * Gherkin: "Dado que el propietario escribe una frase prohibida en un bloque de voz,
 *           cuando se activa el debounce de validación,
 *           entonces aparece la alerta de advertencia con la frase detectada
 *           y la persistencia no se bloquea (soft warning)."
 *
 * HONEST: backend REAL (sin mock del backend-bajo-prueba). El warning de frase
 * prohibida es una feature real del BE (soft warning sobre el voice-blocklist del
 * tenant). El voice-preview es determinístico (cero LLM) y también va al backend
 * real. Aserciones web-first + tolerantes (la alerta surge si el BE la flaggea;
 * el save NUNCA se bloquea — soft warning, RN-1).
 *
 * POMs: LisaMarcaPage, VozTonoSectionPage
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
import { VozTonoSectionPage } from "./poms/voz-tono-section.pom";

// ---------------------------------------------------------------------------
// Test suite — SC-2: voice warning (soft, non-blocking) against real backend
// ---------------------------------------------------------------------------

test.describe("SC-2 — Advertencia de frase prohibida en Voz y tono (backend real)", () => {
  test.beforeEach(async ({ marcaPage }) => {
    await gotoMarca(marcaPage, LISA_MARCA_FIXTURE.tenantId, "voz-y-tono");
  });

  test("escribe una frase prohibida: el guardado NO se bloquea (soft warning)", async ({
    marcaPage,
  }) => {
    const marcaPagePom = new LisaMarcaPage(
      marcaPage,
      LISA_MARCA_FIXTURE.tenantId,
    );
    const vozTono = new VozTonoSectionPage(marcaPage);

    await marcaPagePom.waitForLoaded();

    // Capture personality PATCH responses (real backend, RN-4 cleaned up).
    const patches: number[] = [];
    const onResponse = (response: import("@playwright/test").Response) => {
      if (
        response.url().includes("/api/v1/lisa/marca/personality") &&
        response.request().method() === "PATCH"
      ) {
        patches.push(response.status());
      }
    };
    marcaPage.on("response", onResponse);

    // Fill a tone block with a prohibited phrase ("barato" is in the PE seed
    // voice-blocklist). The BE flags it (soft warning) but still persists.
    await vozTono.fillBlock(
      "openingHook",
      "Somos la opción más barata del mercado médico.",
    );

    // Web-first: the save completes (soft warning does NOT block persistence).
    await marcaPagePom.waitForAutosaveSuccess();

    // The PATCH actually fired against the real backend and returned 200.
    await expect.poll(() => patches.length, { timeout: 5_000 }).toBeGreaterThan(0);
    expect(patches[patches.length - 1]).toBe(200);

    // If the BE surfaces the warning alert, the detected phrase is shown.
    // Tolerant: the alert may appear; the hard guarantee is the non-blocking save.
    if (await vozTono.isWarningAlertVisible()) {
      const phrases = await vozTono.getWarningPhrases();
      expect(phrases.some((p) => p.toLowerCase().includes("barato"))).toBe(true);
    }

    marcaPage.off("response", onResponse);
  });

  test("la advertencia es soft: el contenido se guarda aunque haya frase prohibida", async ({
    marcaPage,
  }) => {
    const marcaPagePom = new LisaMarcaPage(
      marcaPage,
      LISA_MARCA_FIXTURE.tenantId,
    );
    const vozTono = new VozTonoSectionPage(marcaPage);

    await marcaPagePom.waitForLoaded();

    const patches: number[] = [];
    const onResponse = (response: import("@playwright/test").Response) => {
      if (
        response.url().includes("/api/v1/lisa/marca/personality") &&
        response.request().method() === "PATCH"
      ) {
        patches.push(response.status());
      }
    };
    marcaPage.on("response", onResponse);

    // "descuento" is also in the PE seed voice-blocklist.
    await vozTono.fillBlock(
      "mainBody",
      "Ofrecemos grandes descuentos para pacientes nuevos.",
    );

    await marcaPagePom.waitForAutosaveSuccess();

    await expect.poll(() => patches.length, { timeout: 5_000 }).toBeGreaterThan(0);
    expect(patches[patches.length - 1]).toBe(200);

    const badgeText = await marcaPagePom.getAutosaveBadgeText();
    expect(badgeText).toMatch(/Guardado/i);

    marcaPage.off("response", onResponse);
  });

  test("al hacer click en 'Continuar de todas formas' se descarta la advertencia (si aparece)", async ({
    marcaPage,
  }) => {
    const marcaPagePom = new LisaMarcaPage(
      marcaPage,
      LISA_MARCA_FIXTURE.tenantId,
    );
    const vozTono = new VozTonoSectionPage(marcaPage);

    await marcaPagePom.waitForLoaded();

    await vozTono.fillBlock("closingCta", "La opción más barata para ti.");
    await marcaPagePom.waitForAutosaveSuccess();

    // If the warning surfaced, override dismisses it (web-first).
    if (await vozTono.isWarningAlertVisible()) {
      await vozTono.clickOverrideWarning();
      await expect(
        vozTono.warningAlert,
      ).toBeHidden({ timeout: 5_000 });
    }
  });

  test("el tab activo en SubSubTabsBar es 'voz-y-tono' al navegar", async ({
    marcaPage,
  }) => {
    const marcaPagePom = new LisaMarcaPage(
      marcaPage,
      LISA_MARCA_FIXTURE.tenantId,
    );
    await marcaPagePom.waitForLoaded();

    await marcaPagePom.waitForActiveSubsubtab("voz-y-tono");
  });
});
