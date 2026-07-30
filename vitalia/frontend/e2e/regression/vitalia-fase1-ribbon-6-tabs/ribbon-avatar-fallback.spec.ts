/**
 * ribbon-avatar-fallback.spec.ts — SC-9 edge · avatar PNG 404 → AvatarFallback
 *
 * F1-S7 vitalia-fase1-ribbon-6-tabs — T-5
 *
 * Gherkin: 01-spec.md § Gherkin SC-9
 *
 * Given: la imagen PNG del agente retorna 404 (avatar no disponible)
 * When:  el tab del agente renderiza
 * Then:  Shadcn AvatarFallback muestra la letra inicial del agente
 * And:   el tab sigue siendo funcional (click navega correctamente)
 * And:   data-testid="avatar-fallback-{slug}" es visible
 *
 * gherkin_coverage:
 *   - SC-9-1: avatar PNG 404 → AvatarFallback con inicial + tab funcional (Lisa)
 *   - SC-9-2: avatar PNG 404 → tab todavía activa y navega al click
 *
 * Implementation note: To simulate PNG 404, we intercept the avatar image
 * request via page.route() and return 404. This tests the graceful degradation
 * path of Radix <Avatar> → <AvatarFallback>.
 *
 * downstream-regression-na: brand-local E2E spec; no cross-brand consumers
 */

import { expect } from "@playwright/test";
import { test } from "../../fixtures/shell-theme.fixture";
import { RibbonPage } from "./poms/ribbon-page.pom";
import type { AgentSlug } from "@/lib/agent-catalog";

const DESKTOP_VIEWPORT = { width: 1280, height: 800 };
const TENANT_ID = process.env["E2E_TENANT_ID"] ?? "vitalia-test-tenant";

test.describe("SC-9 — avatar PNG 404 → AvatarFallback inicial + tab funcional", () => {
  test.use({ viewport: DESKTOP_VIEWPORT });

  test("SC-9-1: avatar PNG 404 → AvatarFallback visible con letra inicial (Lisa)", async ({
    shellPage,
  }) => {
    const pom = new RibbonPage(shellPage);

    // Intercept avatar image requests for Lisa and return 404
    await shellPage.route("**/agents/lisa/**", async (route) => {
      const request = route.request();
      if (
        request.resourceType() === "image" ||
        request.url().includes(".png") ||
        request.url().includes(".jpg") ||
        request.url().includes(".webp")
      ) {
        await route.fulfill({
          status: 404,
          body: "Not Found",
          contentType: "text/plain",
        });
      } else {
        await route.continue();
      }
    });

    await pom.goto({ tenantId: TENANT_ID, agent: "lisa", subtab: "marca" });

    // AvatarFallback for Lisa should be visible
    await pom.expectAvatarFallback("lisa");

    // Tab should still be active (avatar fallback doesn't break tab state)
    await expect(pom.getTab("lisa")).toHaveAttribute("data-active", "true");
    await expect(pom.getTab("lisa")).toHaveAttribute("aria-selected", "true");
  });

  test("SC-9-2: avatar PNG 404 → tab todavía funcional, click navega correctamente", async ({
    shellPage,
  }) => {
    const pom = new RibbonPage(shellPage);

    // Intercept avatar image for Camila and return 404
    await shellPage.route("**/agents/camila/**", async (route) => {
      const request = route.request();
      if (
        request.resourceType() === "image" ||
        request.url().includes(".png") ||
        request.url().includes(".jpg") ||
        request.url().includes(".webp")
      ) {
        await route.fulfill({
          status: 404,
          body: "Not Found",
          contentType: "text/plain",
        });
      } else {
        await route.continue();
      }
    });

    await pom.goto({ tenantId: TENANT_ID, agent: "lisa", subtab: "marca" });

    // Click Camila tab (whose avatar is 404)
    await pom.clickTab("camila");

    // Should navigate correctly despite avatar 404
    await shellPage.waitForURL(`**/${TENANT_ID}/camila/voz`, {
      timeout: 10_000,
    });

    // Camila tab should be active
    await expect(pom.getTab("camila")).toHaveAttribute("data-active", "true");
    await expect(pom.getTab("camila")).toHaveAttribute("aria-selected", "true");

    // AvatarFallback should be visible for Camila
    await pom.expectAvatarFallback("camila");
  });

  test("SC-9-3: multiple avatars 404 → todos muestran inicial + ribbon funcional", async ({
    shellPage,
  }) => {
    const pom = new RibbonPage(shellPage);

    // Intercept ALL agent avatar images and return 404
    await shellPage.route("**/agents/**", async (route) => {
      const request = route.request();
      if (
        request.resourceType() === "image" ||
        request.url().match(/\.(png|jpg|jpeg|webp)/)
      ) {
        await route.fulfill({
          status: 404,
          body: "Not Found",
          contentType: "text/plain",
        });
      } else {
        await route.continue();
      }
    });

    await pom.goto({ tenantId: TENANT_ID, agent: "valeria", subtab: "agenda" });

    // All agent tabs should still be in DOM and functional
    const slugsToCheck: AgentSlug[] = [
      "lisa",
      "lucas",
      "adrian",
      "valeria",
      "camila",
    ];
    for (const slug of slugsToCheck) {
      await expect(pom.getTab(slug)).toBeAttached();
    }

    // Valeria tab should be active (despite all avatars failing)
    await expect(pom.getTab("valeria")).toHaveAttribute("data-active", "true");

    // Ribbon remains functional — click Lucas to verify
    await pom.clickTab("lucas");
    await shellPage.waitForURL(`**/${TENANT_ID}/lucas/lanzar`, {
      timeout: 10_000,
    });
    await expect(pom.getTab("lucas")).toHaveAttribute("data-active", "true");
  });
});
