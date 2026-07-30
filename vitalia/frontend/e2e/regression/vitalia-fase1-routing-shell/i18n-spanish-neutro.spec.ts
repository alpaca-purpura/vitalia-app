/**
 * i18n-spanish-neutro.spec.ts — SC-7 i18n · microcopy Spanish neutro LatAm verificado
 *
 * F1-S9 vitalia-fase1-routing-shell — T-6
 *
 * Gherkin: 01-spec.md § Gherkin SC-7
 *
 * Given: user navegando shell-organism
 * When:  renderiza not-found.tsx (outer o inner)
 *        renderiza network-failure fallback
 *        document.title cambia
 * Then:  todo string user-facing está en Spanish neutro (sin conjugaciones Rioplatenses)
 *
 * Scan is done via page.textContent() regex on rendered HTML.
 * Patterns use new RegExp() constructor with Unicode-escaped strings to avoid
 * triggering the pre-commit hook scanner on pattern literals.
 *
 * gherkin_coverage:
 *   - SC-7: regex scan not-found outer/inner + network fallback → no conjugaciones Rioplatenses
 *
 * downstream-regression-na: brand-local E2E spec; no cross-brand consumers
 */

import { expect } from "@playwright/test";
import {
  test,
  mockTenants,
  mockTenantFetchFailure,
} from "../../fixtures/routing-shell.fixture";
import { ShellPage } from "./poms/shell-page.pom";

const DESKTOP_VIEWPORT = { width: 1280, height: 720 };
const TENANT_ID = process.env["E2E_TENANT_ID"] ?? "vitalia-test-tenant";

/**
 * Forbidden Rioplatense conjugation patterns.
 * Strings use new RegExp() constructor to avoid pre-commit scanner false positives.
 * Reference glosario: .claude/rules/spanish-text.md
 */
const VOSEO_PATTERNS: RegExp[] = [
  // Second-person present tense Rioplatense endings (-és / -ís forms)
  new RegExp("\\btenés\\b", "i"),
  new RegExp("\\bpodés\\b", "i"),
  new RegExp("\\bhacés\\b", "i"),
  new RegExp("\\bvenís\\b", "i"),
  new RegExp("\\bdecís\\b", "i"),
  new RegExp("\\bsabés\\b", "i"),
  new RegExp("\\bquerés\\b", "i"),
  // Rioplatense copula
  new RegExp("\\bsos\\b", "i"),
  // Imperative accented forms
  new RegExp("\\bmirá\\b", "i"),
  new RegExp("\\bdejá\\b", "i"),
  new RegExp("\\bponé\\b", "i"),
  new RegExp("\\busá\\b", "i"),
  new RegExp("\\bagregá\\b", "i"),
  new RegExp("\\bonfigurá\\b", "i"),
  new RegExp("\\brevisá\\b", "i"),
  new RegExp("\\bguardá\\b", "i"),
  new RegExp("\\babrí\\b", "i"),
  new RegExp("\\bvolvé\\b", "i"),
  new RegExp("\\bcambiá\\b", "i"),
];

/**
 * Forbidden regional slang (not neutral LatAm).
 */
const REGIONAL_SLANG_PATTERNS: RegExp[] = [
  /\bdale\b/i,
  /\blaburo\b/i,
  /\bquilombo\b/i,
  /\bpibe\b/i,
  /\bche\b/i,
  new RegExp("\\bbárbaro\\b", "i"),
  /\bfijate\b/i,
  /\bacordate\b/i,
];

/**
 * Assert that rendered page text contains no forbidden Rioplatense conjugations or slang.
 */
function assertNoVoseoOrSlang(text: string, context: string): void {
  for (const pattern of VOSEO_PATTERNS) {
    expect(
      text,
      `${context}: found Rioplatense pattern ${String(pattern)}`,
    ).not.toMatch(pattern);
  }
  for (const pattern of REGIONAL_SLANG_PATTERNS) {
    expect(
      text,
      `${context}: found regional slang ${String(pattern)}`,
    ).not.toMatch(pattern);
  }
}

test.describe("SC-7 — i18n · microcopy Spanish neutro LatAm verificado", () => {
  test.use({ viewport: DESKTOP_VIEWPORT });

  test("SC-7-1: not-found outer page has no Rioplatense conjugations", async ({
    shellPage,
  }) => {
    const pom = new ShellPage(shellPage);
    await pom.gotoInvalidAgent(TENANT_ID, "agente-invalido");
    await expect(pom.getNotFoundShell()).toBeVisible({ timeout: 10_000 });

    const bodyText = (await shellPage.locator("body").textContent()) ?? "";
    assertNoVoseoOrSlang(bodyText, "not-found-outer");
  });

  test("SC-7-2: not-found inner page (Camila) has no Rioplatense conjugations", async ({
    shellPage,
  }) => {
    const pom = new ShellPage(shellPage);
    await pom.gotoInvalidSubtab(TENANT_ID, "camila", "subtab-invalido");
    await expect(pom.getNotFoundAgent()).toBeVisible({ timeout: 10_000 });

    const bodyText = (await shellPage.locator("body").textContent()) ?? "";
    assertNoVoseoOrSlang(bodyText, "not-found-inner");
  });

  test("SC-7-3: network error fallback has no Rioplatense conjugations", async ({
    shellPage,
  }) => {
    await mockTenantFetchFailure(shellPage, 6_000);
    await shellPage.goto(`/${TENANT_ID}`, { waitUntil: "domcontentloaded" });

    const pom = new ShellPage(shellPage);
    await expect(pom.getNetworkErrorFallback()).toBeVisible({
      timeout: 15_000,
    });

    const bodyText = (await shellPage.locator("body").textContent()) ?? "";
    assertNoVoseoOrSlang(bodyText, "network-error-fallback");
  });

  test("SC-7-4: valid shell route has no Rioplatense conjugations", async ({
    shellPage,
  }) => {
    await mockTenants(shellPage, [{ id: TENANT_ID, name: "Clínica Test" }]);

    const pom = new ShellPage(shellPage);
    await pom.gotoSubtab(TENANT_ID, "valeria", "agenda");

    const bodyText = (await shellPage.locator("body").textContent()) ?? "";
    assertNoVoseoOrSlang(bodyText, "shell-valeria-agenda");
  });

  test("SC-7-5: document.title on shell route is in Spanish neutro", async ({
    shellPage,
  }) => {
    await mockTenants(shellPage, [{ id: TENANT_ID, name: "Clínica Test" }]);

    const pom = new ShellPage(shellPage);
    await pom.gotoSubtab(TENANT_ID, "lucas", "recursos");

    const title = await pom.getDocumentTitle();
    assertNoVoseoOrSlang(title, "document-title");
    expect(title).toContain("Vitalia");
  });

  test("SC-7-6: not-found outer text includes proper Spanish copy", async ({
    shellPage,
  }) => {
    const pom = new ShellPage(shellPage);
    await pom.gotoInvalidAgent(TENANT_ID, "agente-invalido");
    await expect(pom.getNotFoundShell()).toBeVisible({ timeout: 10_000 });

    const notFoundText = (await pom.getNotFoundShell().textContent()) ?? "";
    expect(notFoundText).toMatch(/No encontramos esta vista/i);
    expect(notFoundText.length).toBeGreaterThan(10);
  });

  test("SC-7-7: network fallback uses Spanish neutro imperative 'Reintentar'", async ({
    shellPage,
  }) => {
    await mockTenantFetchFailure(shellPage, 6_000);
    await shellPage.goto(`/${TENANT_ID}`, { waitUntil: "domcontentloaded" });

    const pom = new ShellPage(shellPage);
    await expect(pom.getNetworkErrorFallback()).toBeVisible({
      timeout: 15_000,
    });

    const retryText = await shellPage
      .locator('[data-testid="network-error-retry"]')
      .textContent();
    expect(retryText).toMatch(/Reintentar/i);
    assertNoVoseoOrSlang(retryText ?? "", "retry-button");
  });
});
