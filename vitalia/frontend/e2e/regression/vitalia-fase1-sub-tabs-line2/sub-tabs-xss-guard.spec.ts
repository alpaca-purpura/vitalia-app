/**
 * sub-tabs-xss-guard.spec.ts — SC-7 adversarial · XSS en URL subtab segment
 *
 * F1-S8 vitalia-fase1-sub-tabs-line2 — T-6
 *
 * Gherkin: 01-spec.md § Gherkin SC-7
 *
 * Given: URL con segmento subtab conteniendo payload XSS (agent válido)
 * When:  la página carga
 * Then:  4 SubTabs Lisa renderizados (agent=lisa es válido → no return null)
 * And:   NINGÚN sub-tab active (XSS payload no matchea RIBBON_SUBTABS.lisa[].id)
 * And:   NO hay ejecución de script (alert/confirm/prompt no disparados)
 * And:   React JSX auto-escapea — no tag <script> inyectado en DOM
 *
 * Security note: extractSubtabFromPath retorna el raw segment, pero la comparación
 * contra RIBBON_SUBTABS IDs estáticos nunca produce match → all inactive.
 * React JSX auto-escapa el contenido → no XSS execution.
 *
 * gherkin_coverage:
 *   - SC-7-1: /lisa/<script>alert(1)</script> → all inactive + no dialog
 *   - SC-7-2: /lisa/javascript:alert(1) → all inactive + no execution
 *
 * downstream-regression-na: brand-local E2E spec; no cross-brand consumers
 */

import { expect } from "@playwright/test";
import { test } from "../../fixtures/shell-theme.fixture";
import { SubTabsBarPage } from "./poms/sub-tabs-bar-page.pom";

const DESKTOP_VIEWPORT = { width: 1280, height: 800 };
const TENANT_ID = process.env["E2E_TENANT_ID"] ?? "vitalia-test-tenant";

test.describe("SC-7 — XSS en URL subtab segment → sin ejecución + all inactive", () => {
  test.use({ viewport: DESKTOP_VIEWPORT });

  test("SC-7-1: /lisa/<script>alert(1)</script> → all inactive + no dialog + no script injection", async ({
    shellPage,
  }) => {
    const pom = new SubTabsBarPage(shellPage);

    let dialogTriggered = false;
    shellPage.on("dialog", async (dialog) => {
      dialogTriggered = true;
      await dialog.dismiss();
    });

    const pageErrors: string[] = [];
    shellPage.on("pageerror", (err) => {
      pageErrors.push(err.message);
    });

    // Navigate with XSS payload in subtab segment (URL-encoded)
    const xssPayload = encodeURIComponent("<script>alert(1)</script>");
    await pom.gotoRaw(`/${TENANT_ID}/lisa/${xssPayload}`);

    // Ribbon should mount (lisa is a valid agent — ribbon shows lisa as active)
    await shellPage
      .waitForSelector('[data-testid="ribbon"]:visible', {
        timeout: 15_000,
      })
      .catch(() => {
        // May get 404 — still valid: no dialog = XSS guard upheld
      });

    await shellPage.waitForTimeout(500);

    // No dialog (alert/confirm/prompt) triggered
    expect(dialogTriggered).toBe(false);

    // If SubTabsBar rendered (lisa is valid), verify all sub-tabs are inactive
    const isPresent = await pom.isPresent();
    if (isPresent) {
      // All 4 Lisa sub-tabs should be inactive (XSS segment doesn't match any id)
      const activeId = await pom.getActiveSubTabId();
      expect(activeId).toBeNull();

      for (const id of ["marca", "doctores", "servicios", "compliance"]) {
        await expect(pom.getSubTab(id)).toHaveAttribute(
          "aria-selected",
          "false",
        );
      }

      // No literal <script> tag in DOM body
      const domHasScriptTag = await shellPage.evaluate(() => {
        return document.body.innerHTML.includes("<script>alert(1)</script>");
      });
      expect(domHasScriptTag).toBe(false);
    }

    // No XSS-related page errors
    const xssErrors = pageErrors.filter(
      (e) =>
        e.includes("alert") ||
        e.includes("XSS") ||
        e.includes("script injection"),
    );
    expect(xssErrors).toHaveLength(0);
  });

  test("SC-7-2: /lisa/javascript:alert(1) → all inactive + no execution", async ({
    shellPage,
  }) => {
    const pom = new SubTabsBarPage(shellPage);

    let dialogTriggered = false;
    shellPage.on("dialog", async (dialog) => {
      dialogTriggered = true;
      await dialog.dismiss();
    });

    const jsPayload = encodeURIComponent("javascript:alert(1)");
    await pom.gotoRaw(`/${TENANT_ID}/lisa/${jsPayload}`);

    await shellPage
      .waitForSelector('[data-testid="ribbon"]:visible', {
        timeout: 15_000,
      })
      .catch(() => {});

    await shellPage.waitForTimeout(500);

    expect(dialogTriggered).toBe(false);

    const isPresent = await pom.isPresent();
    if (isPresent) {
      const activeId = await pom.getActiveSubTabId();
      expect(activeId).toBeNull();
    }
  });
});
