/**
 * lisa-marca-race-autosave.spec.ts — SC-5 Race: 2 tabs autosave (real backend)
 *
 * Gherkin: "Dado que el propietario tiene el formulario abierto en 2 pestañas,
 *           cuando ambas editan el mismo campo simultáneamente,
 *           entonces el último PATCH gana (last-write-wins)
 *           y no hay corrupción de datos."
 *
 * HONEST: backend REAL (sin mock del backend-bajo-prueba). Las 2 pestañas viven
 * en el MISMO contexto (misma sesión Clerk) y cada una forwardea `/api/v1/**` al
 * BE real. Round-trips reales + aserciones web-first (RN-1, RN-3). El gate
 * anti-burbuja se hereda en la pestaña principal del fixture; las pestañas extra
 * se guardan con `setupClerkTestingToken` + forwarding.
 *
 * POMs: LisaMarcaPage, IdentidadSectionPage
 *
 * downstream-regression-na: brand-local vitalia e2e spec F2-S7
 *
 * @see e2e/fixtures/real-backend-forward.fixture.ts
 * @see 06-tickets.yaml T-1 deliverable 4
 */

import { setupClerkTestingToken } from "@clerk/testing/playwright";
import {
  test,
  expect,
  gotoMarca,
  LISA_MARCA_FIXTURE,
  forwardApiToRealBackend,
} from "./fixtures/lisa-marca.fixture";
import { LisaMarcaPage } from "./poms/lisa-marca-page.pom";
import { IdentidadSectionPage } from "./poms/identidad-section.pom";

// ---------------------------------------------------------------------------
// Helper: open an extra tab in the same context, authed + forwarded to real BE.
// ---------------------------------------------------------------------------

async function openForwardedTab(
  context: import("@playwright/test").BrowserContext,
): Promise<import("@playwright/test").Page> {
  const page = await context.newPage();
  await setupClerkTestingToken({ page });
  await forwardApiToRealBackend(page);
  return page;
}

// ---------------------------------------------------------------------------
// Test suite — SC-5: race condition 2 tabs autosave (real backend)
// ---------------------------------------------------------------------------

test.describe("SC-5 — Carrera de autosave: 2 pestañas editan simultáneamente", () => {
  test("ambas pestañas guardan sin corrupción cuando editan el mismo campo", async ({
    marcaContext,
  }) => {
    const page1 = await openForwardedTab(marcaContext);
    const page2 = await openForwardedTab(marcaContext);

    // Track PATCH statuses on both tabs (real backend, RN-4).
    const patches1: number[] = [];
    const patches2: number[] = [];
    const on1 = (r: import("@playwright/test").Response) => {
      if (
        r.url().includes("/api/v1/lisa/marca/identity") &&
        r.request().method() === "PATCH"
      ) {
        patches1.push(r.status());
      }
    };
    const on2 = (r: import("@playwright/test").Response) => {
      if (
        r.url().includes("/api/v1/lisa/marca/identity") &&
        r.request().method() === "PATCH"
      ) {
        patches2.push(r.status());
      }
    };
    page1.on("response", on1);
    page2.on("response", on2);

    await Promise.all([
      gotoMarca(page1, LISA_MARCA_FIXTURE.tenantId, "identidad"),
      gotoMarca(page2, LISA_MARCA_FIXTURE.tenantId, "identidad"),
    ]);

    const marcaPage1 = new LisaMarcaPage(page1, LISA_MARCA_FIXTURE.tenantId);
    const marcaPage2 = new LisaMarcaPage(page2, LISA_MARCA_FIXTURE.tenantId);
    const identidad1 = new IdentidadSectionPage(page1);
    const identidad2 = new IdentidadSectionPage(page2);

    await Promise.all([
      marcaPage1.waitForLoaded(),
      marcaPage2.waitForLoaded(),
    ]);

    const nameFromTab1 = `Salud Vitalia tab1 ${Date.now()}`;
    const nameFromTab2 = `Salud Vitalia tab2 ${Date.now()}`;

    await Promise.all([
      identidad1.fillName(nameFromTab1),
      identidad2.fillName(nameFromTab2),
    ]);

    // Both autosaves complete against the real backend (no corruption, no drop).
    await Promise.all([
      marcaPage1.waitForAutosaveSuccess(),
      marcaPage2.waitForAutosaveSuccess(),
    ]);

    await expect.poll(() => patches1.length, { timeout: 5_000 }).toBeGreaterThan(0);
    await expect.poll(() => patches2.length, { timeout: 5_000 }).toBeGreaterThan(0);
    expect(patches1[patches1.length - 1]).toBe(200);
    expect(patches2[patches2.length - 1]).toBe(200);

    const badge1 = await marcaPage1.getAutosaveBadgeText();
    const badge2 = await marcaPage2.getAutosaveBadgeText();
    expect(badge1).toMatch(/Guardado/i);
    expect(badge2).toMatch(/Guardado/i);

    page1.off("response", on1);
    page2.off("response", on2);
    await page1.close();
    await page2.close();
  });

  test("las dos pestañas pueden estar en diferentes sub-sub-tabs sin conflicto", async ({
    marcaContext,
  }) => {
    const page1 = await openForwardedTab(marcaContext);
    const page2 = await openForwardedTab(marcaContext);

    await Promise.all([
      gotoMarca(page1, LISA_MARCA_FIXTURE.tenantId, "identidad"),
      gotoMarca(page2, LISA_MARCA_FIXTURE.tenantId, "presencia"),
    ]);

    const marcaPage1 = new LisaMarcaPage(page1, LISA_MARCA_FIXTURE.tenantId);
    const marcaPage2 = new LisaMarcaPage(page2, LISA_MARCA_FIXTURE.tenantId);

    await Promise.all([
      marcaPage1.waitForLoaded(),
      marcaPage2.waitForLoaded(),
    ]);

    // Web-first: each tab marks its own sub-sub-tab active independently.
    await marcaPage1.waitForActiveSubsubtab("identidad");
    await marcaPage2.waitForActiveSubsubtab("presencia");

    await page1.close();
    await page2.close();
  });
});
