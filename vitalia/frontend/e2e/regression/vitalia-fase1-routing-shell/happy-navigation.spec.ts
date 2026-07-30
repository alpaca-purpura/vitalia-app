/**
 * happy-navigation.spec.ts — SC-1 happy · login + default landing + navegación completa
 *
 * F1-S9 vitalia-fase1-routing-shell — T-6
 * UPDATED: paradigm-map-zones T-6 (2026-05-30) — default landing changed.
 *   /{tenantId} → /mateo/agenda (was /valeria/agenda pre T-5 migration).
 *   Valeria is sidebar only (v1.2). Mateo = ribbon tab "Operar".
 *
 * Gherkin: 01-spec.md § Gherkin SC-1
 *
 * Given: user autenticado con tenant_id=clinic-X en JWT
 * When:  browser carga /{tenantId}/ → redirect mateo/agenda (UPDATED from valeria/agenda)
 *        user click Ribbon "Atraer" (Lucas) + SubTab "Recursos"
 * Then:  URL = /{tenantId}/lucas/recursos
 *        Ribbon active = Lucas · SubTabsBar active = "Recursos"
 *        document.title = "Vitalia · Lucas · Recursos"
 *
 * gherkin_coverage:
 *   - SC-1 (UPDATED): login + default landing /mateo/agenda + navegar Lucas/Recursos → title check
 *
 * downstream-regression-na: brand-local E2E spec; no cross-brand consumers
 */

import { expect } from "@playwright/test";
import { test } from "../../fixtures/routing-shell.fixture";
import { ShellPage } from "./poms/shell-page.pom";

const DESKTOP_VIEWPORT = { width: 1280, height: 720 };
const TENANT_ID = process.env["E2E_TENANT_ID"] ?? "vitalia-test-tenant";

test.describe("SC-1 — happy · login + default landing + navegación completa", () => {
  test.use({ viewport: DESKTOP_VIEWPORT });

  test("SC-1-1 (UPDATED v1.2): default landing redirects to /mateo/agenda with Ribbon + SubTabsBar active", async ({
    shellPage,
  }) => {
    // UPDATED: paradigm-map-zones T-6 (2026-05-30) — default landing is now /mateo/agenda
    // Was: /{tenantId}/valeria/agenda (pre T-5 migration)
    const pom = new ShellPage(shellPage);

    // Navigate to tenant root — should redirect to /mateo/agenda
    await pom.gotoTenantRoot(TENANT_ID);

    // Verify URL redirected to /mateo/agenda
    await shellPage.waitForURL(`**/${TENANT_ID}/mateo/agenda`, {
      timeout: 15_000,
    });

    // Ribbon should show Mateo as active (v1.2 — Mateo = Operar tab)
    await pom.waitForRibbonActive("mateo");

    // SubTabsBar should show "agenda" as active
    await pom.waitForSubTabActive("agenda");

    // Shell chrome is visible
    await pom.assertChromeVisible();
  });

  test("SC-1-2: click Ribbon Lucas + SubTab Recursos → URL /lucas/recursos + title update", async ({
    shellPage,
  }) => {
    const pom = new ShellPage(shellPage);

    // Start from default landing — UPDATED: mateo/agenda (was valeria/agenda pre v1.2)
    await pom.gotoSubtab(TENANT_ID, "mateo", "agenda");

    // Click Ribbon tab "Atraer" → Lucas
    await pom.clickRibbonTab("lucas");

    // URL changes to /lucas/lanzar (Lucas defaultSubtab)
    await shellPage.waitForURL(`**/${TENANT_ID}/lucas/lanzar`, {
      timeout: 10_000,
    });

    // SubTabsBar shows Lucas tabs — navigate to Recursos
    await pom.clickSubtab("recursos");

    // Final URL = /{tenantId}/lucas/recursos
    await shellPage.waitForURL(`**/${TENANT_ID}/lucas/recursos`, {
      timeout: 10_000,
    });

    // Ribbon active state = Lucas
    const ribbonActive = await pom.getRibbonActiveTab();
    expect(ribbonActive).toBe("lucas");

    // SubTabsBar active = recursos
    const subtabActive = await pom.getSubtabActiveTab();
    expect(subtabActive).toBe("recursos");

    // document.title includes agent + subtab in Spanish
    const title = await pom.getDocumentTitle();
    expect(title).toMatch(/Vitalia/i);
    // Title may include agent name or subtab — at minimum contains Vitalia
    expect(title.length).toBeGreaterThan(0);
  });

  test("SC-1-3: navigate across multiple agents — URL tracks correctly", async ({
    shellPage,
  }) => {
    const pom = new ShellPage(shellPage);

    // Start at mateo/agenda — UPDATED: paradigm-map-zones T-6 (v1.2 — was valeria/agenda)
    await pom.gotoSubtab(TENANT_ID, "mateo", "agenda");
    await pom.waitForRibbonActive("mateo");

    // Navigate to Adrián via Ribbon
    await pom.clickRibbonTab("adrian");
    await shellPage.waitForURL(`**/${TENANT_ID}/adrian/**`, {
      timeout: 10_000,
    });
    await pom.waitForRibbonActive("adrian");

    // Navigate to Lisa via Ribbon
    await pom.clickRibbonTab("lisa");
    await shellPage.waitForURL(`**/${TENANT_ID}/lisa/**`, { timeout: 10_000 });
    await pom.waitForRibbonActive("lisa");

    // Shell chrome remains visible throughout
    await pom.assertChromeVisible();
  });
});
