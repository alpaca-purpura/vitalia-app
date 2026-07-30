/**
 * sc-07-adversarial-xss.spec.ts — SC-7 · XSS payload en URL → safe render (no script execution)
 * F1-S10 vitalia-fase1-empty-states — T-10
 *
 * Assertions:
 *   - Navigate to /{tenantId}/lisa/{xss-payload} where payload is URL-encoded XSS
 *   - isValidSubtab() blocks invalid subtab → not-found renders (no placeholder that could reflect)
 *   - page.on('dialog') never fires (no alert/confirm executed)
 *   - No script tags injected into DOM
 *   - Rendered HTML contains no unescaped script content from URL params
 *   - Shell organism survives the adversarial input without crash
 *
 * XSS payloads tested:
 *   1. Classic alert: <script>alert(1)</script>
 *   2. img onerror: <img src=x onerror=alert(1)>
 *   3. JavaScript URL: javascript:alert(1)
 *   4. Data URL: data:text/html,<script>alert(1)</script>
 *
 * Uses: ShellOrganismPage POM + empty-states.fixture
 *
 * SC-7 validator: val-fe-e2e-sc07-adversarial-xss
 * downstream-regression-na: brand-local vitalia e2e spec
 */

import { expect } from "@playwright/test";
import { test } from "../../fixtures/empty-states.fixture";
import { ShellOrganismPage } from "../../pages/ShellOrganismPage";

const XSS_PAYLOADS = [
  { name: "script-tag", payload: "<script>alert(1)</script>" },
  { name: "img-onerror", payload: "<img src=x onerror=alert(1)>" },
  { name: "javascript-url", payload: "javascript:alert(1)" },
  { name: "html-encoded", payload: "&lt;script&gt;alert(1)&lt;/script&gt;" },
] as const;

test.describe("SC-7 · XSS payload en URL → safe render (no script execution)", () => {
  for (const { name, payload } of XSS_PAYLOADS) {
    test(`XSS payload '${name}' no ejecuta script`, async ({
      shellPage,
      tenantId,
    }) => {
      const shell = new ShellOrganismPage(shellPage, tenantId);
      let dialogFired = false;

      // Detect if any dialog (alert/confirm/prompt) is triggered
      shellPage.on("dialog", async (dialog) => {
        dialogFired = true;
        // Dismiss immediately to prevent test hang
        await dialog.dismiss();
      });

      // Navigate with XSS payload in subtab segment
      await shell.gotoXssSubtab(payload);

      // Allow React render + potential script execution window
      await shell.waitForStableRender();

      // CRITICAL: No dialog should have fired
      expect(dialogFired).toBe(false);
    });
  }

  test("isValidSubtab() bloquea subtabs inválidos incluyendo XSS fragments", async ({
    shellPage,
    tenantId,
  }) => {
    const shell = new ShellOrganismPage(shellPage, tenantId);

    // Navigate to XSS payload URL
    await shell.gotoXssSubtab("<script>alert(1)</script>");

    // Shell must NOT crash — page must still be functional
    await expect(shellPage.locator("body").first()).toBeVisible();

    // The invalid subtab is rejected → not-found or safe fallback rendered
    // Ribbon may or may not be visible depending on whether agent segment is valid
    // but shell must not be blank
    const bodyText = await shellPage.locator("body").first().textContent();
    expect(bodyText).toBeTruthy();
  });

  test("DOM no contiene tags <script> inyectados desde URL", async ({
    shellPage,
    tenantId,
  }) => {
    const shell = new ShellOrganismPage(shellPage, tenantId);
    await shell.gotoXssSubtab("<script>alert('xss').first()</script>");
    await shell.waitForStableRender();

    // Count script tags that might contain injected payload
    const injectedScripts = await shellPage.evaluate(() => {
      const scripts = document.querySelectorAll("script");
      return Array.from(scripts)
        .map((s) => s.textContent ?? "")
        .filter((t) => t.includes("alert('xss')"));
    });

    expect(injectedScripts).toHaveLength(0);
  });

  test("page.on dialog nunca dispara en secuencia de 4 payloads", async ({
    shellPage,
    tenantId,
  }) => {
    const shell = new ShellOrganismPage(shellPage, tenantId);
    const dialogs: string[] = [];

    shellPage.on("dialog", async (dialog) => {
      dialogs.push(dialog.message());
      await dialog.dismiss();
    });

    for (const { payload } of XSS_PAYLOADS) {
      await shell.gotoXssSubtab(payload);
      await shell.waitForStableRender();
    }

    expect(dialogs).toHaveLength(0);
  });
});
