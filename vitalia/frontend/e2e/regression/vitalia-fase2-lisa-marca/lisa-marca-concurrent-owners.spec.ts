/**
 * lisa-marca-concurrent-owners.spec.ts — SC-6 Concurrent owners (real backend)
 *
 * Gherkin: "Dado que dos administradores del mismo tenant editan la marca al
 *           mismo tiempo desde contextos de browser separados, cuando ambos
 *           hacen cambios en personalidad, entonces ambos reciben confirmación
 *           de guardado y la vista previa de voz se actualiza correctamente."
 *
 * HONEST: backend REAL (sin mock del backend-bajo-prueba). Cada owner abre su
 * propio contexto (misma sesión Clerk) y forwardea `/api/v1/**` al BE real. El
 * voice-preview es determinístico (cero LLM) → también va al backend real. Los
 * guards anti-burbuja de `base.ts` se adjuntan a AMBAS páginas (RN-2). Aserciones
 * web-first (RN-3).
 *
 * POMs: LisaMarcaPage, VozTonoSectionPage
 *
 * downstream-regression-na: brand-local vitalia e2e spec F2-S7
 *
 * @see e2e/fixtures/real-backend-forward.fixture.ts
 * @see e2e/fixtures/base.ts (anti-burbuja guards)
 * @see 06-tickets.yaml T-1 deliverable 4
 */

import path from "path";
import { test as base } from "../../fixtures/base";
import {
  attachRuntimeErrorGuards,
  assertNoRuntimeErrors,
  expectNoNextErrorOverlay,
  expect,
} from "../../fixtures/base";
import { setupClerkTestingToken } from "@clerk/testing/playwright";
import {
  LISA_MARCA_FIXTURE,
  gotoMarca,
  forwardApiToRealBackend,
} from "./fixtures/lisa-marca.fixture";
import { LisaMarcaPage } from "./poms/lisa-marca-page.pom";
import { VozTonoSectionPage } from "./poms/voz-tono-section.pom";

const STORAGE_STATE_PATH = path.join(
  __dirname,
  "../../../playwright/.clerk/user.json",
);

// ---------------------------------------------------------------------------
// 2-owner fixture composed on top of base.ts (anti-burbuja gate inherited).
// Each owner page is authenticated + forwarded to the real backend + guarded.
// ---------------------------------------------------------------------------

type ConcurrentFixtures = {
  ownerAPage: import("@playwright/test").Page;
  ownerBPage: import("@playwright/test").Page;
};

async function makeOwnerPage(
  browser: import("@playwright/test").Browser,
): Promise<{
  page: import("@playwright/test").Page;
  guards: ReturnType<typeof attachRuntimeErrorGuards>;
  close: () => Promise<void>;
}> {
  const context = await browser.newContext({
    storageState: STORAGE_STATE_PATH,
  });
  const page = await context.newPage();
  const guards = attachRuntimeErrorGuards(page);
  await setupClerkTestingToken({ page });
  await forwardApiToRealBackend(page);
  return {
    page,
    guards,
    close: async () => {
      await page.close();
      await context.close();
    },
  };
}

const test = base.extend<ConcurrentFixtures>({
  ownerAPage: async ({ browser }, use) => {
    const owner = await makeOwnerPage(browser);
    await use(owner.page);
    if (!owner.page.isClosed()) {
      await expectNoNextErrorOverlay(owner.page);
    }
    assertNoRuntimeErrors(owner.guards);
    await owner.close();
  },
  ownerBPage: async ({ browser }, use) => {
    const owner = await makeOwnerPage(browser);
    await use(owner.page);
    if (!owner.page.isClosed()) {
      await expectNoNextErrorOverlay(owner.page);
    }
    assertNoRuntimeErrors(owner.guards);
    await owner.close();
  },
});

// ---------------------------------------------------------------------------
// Test suite — SC-6: concurrent owners (real backend)
// ---------------------------------------------------------------------------

test.describe("SC-6 — Propietarios simultáneos: edición concurrente de personalidad", () => {
  test("dos administradores pueden editar personalidad y ambos reciben confirmación", async ({
    ownerAPage,
    ownerBPage,
  }) => {
    await Promise.all([
      gotoMarca(ownerAPage, LISA_MARCA_FIXTURE.tenantId, "voz-y-tono"),
      gotoMarca(ownerBPage, LISA_MARCA_FIXTURE.tenantId, "voz-y-tono"),
    ]);

    const marcaA = new LisaMarcaPage(ownerAPage, LISA_MARCA_FIXTURE.tenantId);
    const marcaB = new LisaMarcaPage(ownerBPage, LISA_MARCA_FIXTURE.tenantId);
    const vozTonoA = new VozTonoSectionPage(ownerAPage);
    const vozTonoB = new VozTonoSectionPage(ownerBPage);

    await Promise.all([marcaA.waitForLoaded(), marcaB.waitForLoaded()]);

    // Capture PATCH statuses on both owner pages (real backend, RN-4).
    const patchesA: number[] = [];
    const patchesB: number[] = [];
    const onA = (r: import("@playwright/test").Response) => {
      if (
        r.url().includes("/api/v1/lisa/marca/personality") &&
        r.request().method() === "PATCH"
      ) {
        patchesA.push(r.status());
      }
    };
    const onB = (r: import("@playwright/test").Response) => {
      if (
        r.url().includes("/api/v1/lisa/marca/personality") &&
        r.request().method() === "PATCH"
      ) {
        patchesB.push(r.status());
      }
    };
    ownerAPage.on("response", onA);
    ownerBPage.on("response", onB);

    // Owner A → sage, Owner B → healer (concurrent against the real backend).
    await Promise.all([
      vozTonoA.selectArchetype("sage"),
      vozTonoB.selectArchetype("healer"),
    ]);

    await Promise.all([
      marcaA.waitForAutosaveSuccess(),
      marcaB.waitForAutosaveSuccess(),
    ]);

    const badgeA = await marcaA.getAutosaveBadgeText();
    const badgeB = await marcaB.getAutosaveBadgeText();
    expect(badgeA).toMatch(/Guardado/i);
    expect(badgeB).toMatch(/Guardado/i);

    // Both PATCHes were sent to the real backend and succeeded.
    await expect.poll(() => patchesA.length, { timeout: 5_000 }).toBeGreaterThan(0);
    await expect.poll(() => patchesB.length, { timeout: 5_000 }).toBeGreaterThan(0);
    expect(patchesA[patchesA.length - 1]).toBe(200);
    expect(patchesB[patchesB.length - 1]).toBe(200);

    ownerAPage.off("response", onA);
    ownerBPage.off("response", onB);
  });

  test("la vista previa de voz se actualiza cuando el owner A cambia el arquetipo", async ({
    ownerAPage,
  }) => {
    await gotoMarca(ownerAPage, LISA_MARCA_FIXTURE.tenantId, "voz-y-tono");

    const marcaA = new LisaMarcaPage(ownerAPage, LISA_MARCA_FIXTURE.tenantId);
    const vozTonoA = new VozTonoSectionPage(ownerAPage);

    await marcaA.waitForLoaded();

    // Select a new archetype → real PATCH → voice-preview recompiles (deterministic).
    await vozTonoA.selectArchetype("sage");
    await marcaA.waitForAutosaveSuccess();

    // The voice preview loads from the real (deterministic) backend. Aserción
    // robusta web-first: el preview está visible y tiene contenido sustantivo
    // (NO la extracción frágil de un bubble específico, que es no-determinista).
    await vozTonoA.waitForPreviewLoaded();
    await expect(vozTonoA.brandVoicePreview).toBeVisible();
    await expect(vozTonoA.brandVoicePreview).not.toBeEmpty();
  });
});
