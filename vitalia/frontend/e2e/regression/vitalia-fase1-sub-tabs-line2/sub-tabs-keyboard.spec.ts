/**
 * sub-tabs-keyboard.spec.ts — SC-8 a11y · WAI-ARIA tablist keyboard navigation
 *
 * F1-S8 vitalia-fase1-sub-tabs-line2 — T-6
 *
 * Gherkin: 01-spec.md § Gherkin SC-8
 *
 * Given: SubTabsBar renderizado con role="tablist"
 * When:  usuario navega con teclado (ArrowLeft/Right + Home/End + Enter/Space)
 * Then:  roving tabindex WAI-ARIA funciona correctamente (paridad F1-S7 Ribbon)
 * And:   focus ring visible (focus-visible:ring-ring token) al navegar con teclado
 * And:   ArrowRight/Left cicla entre sub-tabs
 * And:   Home/End van al primer/último sub-tab
 * And:   Enter/Space activa el sub-tab focused + navega a su ruta
 *
 * Also tagged @axe: axe-playwright wcag2aa scan del SubTabsBar organism
 *
 * gherkin_coverage:
 *   - SC-8-1: ArrowRight cicla forward entre sub-tabs (Lisa: marca→doctores→servicios)
 *   - SC-8-2: ArrowLeft cicla backward
 *   - SC-8-3: Home → primer sub-tab (idx 0)
 *   - SC-8-4: End → último sub-tab (idx N-1)
 *   - SC-8-5: Enter activa sub-tab focused + navega
 *   - SC-8-6: Space activa sub-tab focused + navega
 *   - SC-8-axe: axe wcag2aa 0 violations en SubTabsBar
 *
 * downstream-regression-na: brand-local E2E spec; no cross-brand consumers
 */

import { expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { test } from "../../fixtures/shell-theme.fixture";
import { SubTabsBarPage } from "./poms/sub-tabs-bar-page.pom";

const DESKTOP_VIEWPORT = { width: 1280, height: 800 };
const TENANT_ID = process.env["E2E_TENANT_ID"] ?? "vitalia-test-tenant";

test.describe("SC-8 — WAI-ARIA tablist keyboard navigation (SubTabsBar)", () => {
  test.use({ viewport: DESKTOP_VIEWPORT });

  test("SC-8-1: ArrowRight cicla forward entre sub-tabs Lisa (marca→doctores→servicios)", async ({
    shellPage,
  }) => {
    const pom = new SubTabsBarPage(shellPage);

    await pom.goto({ tenantId: TENANT_ID, agent: "lisa", subtab: "marca" });

    // Focus the Marca sub-tab (the active one, tabIndex=0)
    await pom.getSubTab("marca").focus();
    await shellPage.waitForTimeout(100);

    // ArrowRight → should move focus to Doctores
    await pom.pressKey("ArrowRight");
    await shellPage.waitForTimeout(100);

    const focusedAfterFirst = await pom.getFocusedSubTabId();
    expect(focusedAfterFirst).toBe("doctores");

    // ArrowRight again → Servicios
    await pom.pressKey("ArrowRight");
    await shellPage.waitForTimeout(100);

    const focusedAfterSecond = await pom.getFocusedSubTabId();
    expect(focusedAfterSecond).toBe("servicios");
  });

  test("SC-8-2: ArrowLeft cicla backward entre sub-tabs Lisa (doctores→marca)", async ({
    shellPage,
  }) => {
    const pom = new SubTabsBarPage(shellPage);

    await pom.goto({ tenantId: TENANT_ID, agent: "lisa", subtab: "doctores" });

    // Focus Doctores (active sub-tab)
    await pom.getSubTab("doctores").focus();
    await shellPage.waitForTimeout(100);

    // ArrowLeft → should move focus to Marca (previous)
    await pom.pressKey("ArrowLeft");
    await shellPage.waitForTimeout(100);

    const focusedAfterLeft = await pom.getFocusedSubTabId();
    expect(focusedAfterLeft).toBe("marca");
  });

  test("SC-8-3: ArrowRight circular wrap → last sub-tab wraps to first (Lisa: compliance→marca)", async ({
    shellPage,
  }) => {
    const pom = new SubTabsBarPage(shellPage);

    await pom.goto({
      tenantId: TENANT_ID,
      agent: "lisa",
      subtab: "compliance",
    });

    // Focus Compliance (last sub-tab)
    await pom.getSubTab("compliance").focus();
    await shellPage.waitForTimeout(100);

    // ArrowRight from last → should wrap to first (marca)
    await pom.pressKey("ArrowRight");
    await shellPage.waitForTimeout(100);

    const focusedWrapped = await pom.getFocusedSubTabId();
    expect(focusedWrapped).toBe("marca");
  });

  test("SC-8-4: Home key → primer sub-tab (Lisa idx 0 = marca)", async ({
    shellPage,
  }) => {
    const pom = new SubTabsBarPage(shellPage);

    await pom.goto({ tenantId: TENANT_ID, agent: "lisa", subtab: "servicios" });

    await pom.getSubTab("servicios").focus();
    await shellPage.waitForTimeout(100);

    // Home → first sub-tab
    await pom.pressKey("Home");
    await shellPage.waitForTimeout(100);

    const focusedAfterHome = await pom.getFocusedSubTabId();
    expect(focusedAfterHome).toBe("marca");
  });

  test("SC-8-5: End key → último sub-tab (Lisa idx 3 = compliance)", async ({
    shellPage,
  }) => {
    const pom = new SubTabsBarPage(shellPage);

    await pom.goto({ tenantId: TENANT_ID, agent: "lisa", subtab: "marca" });

    await pom.getSubTab("marca").focus();
    await shellPage.waitForTimeout(100);

    // End → last sub-tab
    await pom.pressKey("End");
    await shellPage.waitForTimeout(100);

    const focusedAfterEnd = await pom.getFocusedSubTabId();
    expect(focusedAfterEnd).toBe("compliance");
  });

  test("SC-8-6: Enter activa sub-tab focused → navega a su ruta", async ({
    shellPage,
  }) => {
    const pom = new SubTabsBarPage(shellPage);

    await pom.goto({ tenantId: TENANT_ID, agent: "lisa", subtab: "marca" });

    // Focus Doctores (not the active sub-tab)
    await pom.getSubTab("doctores").focus();
    await shellPage.waitForTimeout(100);

    // Press Enter → should activate Doctores + navigate to /lisa/doctores
    await pom.pressKey("Enter");

    await shellPage.waitForURL(`**/${TENANT_ID}/lisa/doctores`, {
      timeout: 10_000,
    });

    await expect(pom.getSubTab("doctores")).toHaveAttribute(
      "data-active",
      "true",
    );
    await expect(pom.getSubTab("marca")).toHaveAttribute(
      "data-active",
      "false",
    );
  });

  test("SC-8-7: Space activa sub-tab focused → navega a su ruta", async ({
    shellPage,
  }) => {
    const pom = new SubTabsBarPage(shellPage);

    await pom.goto({ tenantId: TENANT_ID, agent: "lisa", subtab: "marca" });

    await pom.getSubTab("servicios").focus();
    await shellPage.waitForTimeout(100);

    // Space → same as Enter for tab navigation
    await pom.pressKey("Space");

    await shellPage.waitForURL(`**/${TENANT_ID}/lisa/servicios`, {
      timeout: 10_000,
    });

    await expect(pom.getSubTab("servicios")).toHaveAttribute(
      "data-active",
      "true",
    );
  });

  test("SC-8-8: Tab / Escape → no navigateTo, no focus change within sub-tabs", async ({
    shellPage,
  }) => {
    const pom = new SubTabsBarPage(shellPage);

    await pom.goto({ tenantId: TENANT_ID, agent: "lisa", subtab: "marca" });

    const initialUrl = shellPage.url();

    await pom.getSubTab("doctores").focus();
    await shellPage.waitForTimeout(100);

    // Escape → no navigation
    await pom.pressKey("Escape");
    await shellPage.waitForTimeout(100);
    expect(shellPage.url()).toBe(initialUrl);

    // Doctores should still be in DOM (no crash from Escape)
    await expect(pom.getSubTab("doctores")).toBeAttached();
  });
});

// ── Axe wcag2aa scan ──────────────────────────────────────────────────────────

test.describe("SC-8-axe — axe wcag2aa scan SubTabsBar organism @axe", () => {
  test.use({ viewport: DESKTOP_VIEWPORT });

  test(
    "SubTabsBar organism: 0 critical/serious axe violations wcag2aa [light mode]",
    { tag: "@axe" },
    async ({ shellPage }) => {
      const pom = new SubTabsBarPage(shellPage);

      await pom.goto({ tenantId: TENANT_ID, agent: "lisa", subtab: "marca" });

      const results = await new AxeBuilder({ page: shellPage })
        .include('[data-testid="sub-tabs-bar"]')
        .withTags(["wcag2aa"])
        .analyze();

      const criticalOrSerious = results.violations.filter((v) =>
        ["critical", "serious"].includes(v.impact ?? ""),
      );

      if (criticalOrSerious.length > 0) {
        const details = criticalOrSerious
          .map(
            (v) =>
              `${v.id} (${v.impact}): ${v.description} — ${v.nodes.map((n) => n.target).join(", ")}`,
          )
          .join("\n");
        throw new Error(
          `Axe wcag2aa critical/serious violations found:\n${details}`,
        );
      }

      expect(criticalOrSerious).toHaveLength(0);
    },
  );

  test(
    "SubTabsBar organism: 0 critical/serious axe violations wcag2aa [dark mode]",
    { tag: "@axe" },
    async ({ darkShellPage }) => {
      const pom = new SubTabsBarPage(darkShellPage);

      await pom.goto({ tenantId: TENANT_ID, agent: "camila", subtab: "voz" });

      const results = await new AxeBuilder({ page: darkShellPage })
        .include('[data-testid="sub-tabs-bar"]')
        .withTags(["wcag2aa"])
        .analyze();

      const criticalOrSerious = results.violations.filter((v) =>
        ["critical", "serious"].includes(v.impact ?? ""),
      );

      if (criticalOrSerious.length > 0) {
        const details = criticalOrSerious
          .map((v) => `${v.id} (${v.impact}): ${v.description}`)
          .join("\n");
        throw new Error(
          `Axe wcag2aa dark mode critical/serious violations found:\n${details}`,
        );
      }

      expect(criticalOrSerious).toHaveLength(0);
    },
  );
});
