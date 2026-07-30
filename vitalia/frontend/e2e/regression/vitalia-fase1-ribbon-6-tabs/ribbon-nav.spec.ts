/**
 * ribbon-nav.spec.ts — SC-1 happy · click tab agente navega a default subtab
 *
 * F1-S7 vitalia-fase1-ribbon-6-tabs — T-5
 *
 * Gherkin: 01-spec.md § Gherkin SC-1
 *
 * Given: usuario en /{tenantId}/lisa/marca, active tab Lisa visible
 * When:  click RibbonTab "Atraer" (Lucas)
 * Then:  router.push("/{tenantId}/lucas/lanzar") se invoca
 * And:   active state migra a Lucas con bg-agent-lucas-soft
 * And:   Lisa tab pierde tint (text-muted-foreground)
 *
 * gherkin_coverage:
 *   - SC-1: click Lucas from active=lisa → URL changes to /lucas/lanzar + Lucas tab active
 *   - Corollary: click Camila → URL changes to /camila/voz + Camila tab active
 *
 * Route: /{tenantId}/lisa/marca (direct navigation via shell root redirect)
 * Port: 3002 (E2E_BASE_URL=http://localhost:3002)
 *
 * downstream-regression-na: brand-local E2E spec; no cross-brand consumers
 */

import { expect } from "@playwright/test";
import { test } from "../../fixtures/shell-theme.fixture";
import { RibbonPage } from "./poms/ribbon-page.pom";

const DESKTOP_VIEWPORT = { width: 1280, height: 800 };
const TENANT_ID = process.env["E2E_TENANT_ID"] ?? "vitalia-test-tenant";

test.describe("SC-1 — click tab agente navega a default subtab", () => {
  test.use({ viewport: DESKTOP_VIEWPORT });

  test("SC-1-1: click Lucas (Atraer) desde active=lisa → URL /lucas/lanzar + Lucas active", async ({
    shellPage,
  }) => {
    const pom = new RibbonPage(shellPage);

    // Navigate to lisa/marca — the shell redirect lands here from /{tenantId}
    await pom.goto({ tenantId: TENANT_ID, agent: "lisa", subtab: "marca" });

    // Verify initial state: Lisa is active
    const initialActive = await pom.getActiveSlug();
    expect(initialActive).toBe("lisa");

    // Click Lucas tab
    await pom.clickTab("lucas");

    // URL should change to /{tenantId}/lucas/lanzar
    await shellPage.waitForURL(`**/${TENANT_ID}/lucas/lanzar`, {
      timeout: 10_000,
    });

    // Lucas tab should now be active
    await expect(pom.getTab("lucas")).toHaveAttribute("data-active", "true");
    await expect(pom.getTab("lucas")).toHaveAttribute("aria-selected", "true");

    // Lisa tab should be inactive
    await expect(pom.getTab("lisa")).toHaveAttribute("data-active", "false");
    await expect(pom.getTab("lisa")).toHaveAttribute("aria-selected", "false");
  });

  test("SC-1-2: click Camila (Mantener) desde active=lisa → URL /camila/voz + Camila active", async ({
    shellPage,
  }) => {
    const pom = new RibbonPage(shellPage);

    await pom.goto({ tenantId: TENANT_ID, agent: "lisa", subtab: "marca" });

    // Click Camila tab
    await pom.clickTab("camila");

    // URL should change to /{tenantId}/camila/voz
    await shellPage.waitForURL(`**/${TENANT_ID}/camila/voz`, {
      timeout: 10_000,
    });

    // Camila tab should now be active
    await expect(pom.getTab("camila")).toHaveAttribute("data-active", "true");
    await expect(pom.getTab("camila")).toHaveAttribute("aria-selected", "true");

    // Lisa tab should be inactive
    await expect(pom.getTab("lisa")).toHaveAttribute("data-active", "false");
  });

  test("SC-1-3: click Adrián (Vender) → URL /adrian/inbox + Adrián active (tildes preservados en slug)", async ({
    shellPage,
  }) => {
    const pom = new RibbonPage(shellPage);

    await pom.goto({ tenantId: TENANT_ID, agent: "lisa", subtab: "marca" });

    // Click Adrián tab (slug = "adrian" without tilde in URL)
    await pom.clickTab("adrian");

    // URL should change to /{tenantId}/adrian/inbox
    await shellPage.waitForURL(`**/${TENANT_ID}/adrian/inbox`, {
      timeout: 10_000,
    });

    // Adrián tab should now be active
    await expect(pom.getTab("adrian")).toHaveAttribute("data-active", "true");
    await expect(pom.getTab("adrian")).toHaveAttribute("aria-selected", "true");
  });
});
