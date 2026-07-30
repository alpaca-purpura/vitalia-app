/**
 * visual-goldens.spec.ts — 13 visual golden tests (F1-S8 SubTabsBar ratchet)
 *
 * F1-S8 vitalia-fase1-sub-tabs-line2 — T-6
 *
 * ITER-1: Goldens generated with `--update-snapshots --project=visual`.
 * Ratification: Chris side-by-side review required before ratchet locks.
 *
 * Per shell-mockup-per-component.md protocol — goldens against ratified HTML mockup:
 *   vitalia/docs/product/stories/vitalia-fase1-sub-tabs-line2/mockups/sub-tabs.html
 *
 * 13 PNGs per 06-tickets.yaml T-6 gherkin_coverage (visual scenarios):
 *   01. sub-tabs-lisa-light.png      — Lisa active (lisa/marca), light 1280x800
 *   02. sub-tabs-lisa-dark.png       — Lisa active, dark 1280x800
 *   03. sub-tabs-lucas-light.png     — Lucas active (lucas/lanzar, 5 tabs), light 1280x800
 *   04. sub-tabs-lucas-dark.png      — Lucas active, dark 1280x800
 *   05. sub-tabs-adrian-light.png    — Adrián active (adrian/inbox), light 1280x800
 *   06. sub-tabs-adrian-dark.png     — Adrián active, dark 1280x800
 *   07. sub-tabs-valeria-light.png   — Valeria active (valeria/agenda, 2 tabs), light 1280x800
 *   08. sub-tabs-valeria-dark.png    — Valeria active, dark 1280x800
 *   09. sub-tabs-camila-light.png    — Camila active (camila/voz), light 1280x800
 *   10. sub-tabs-camila-dark.png     — Camila active, dark 1280x800
 *   11. sub-tabs-config-light.png    — Config active (config/cuenta), light 1280x800 (neutral)
 *   12. sub-tabs-config-dark.png     — Config active, dark 1280x800 (neutral)
 *   13. sub-tabs-mobile-lucas-375.png — Lucas active, mobile 375x667 (overflow-x-auto)
 *
 * Visual project config (playwright.config.ts):
 *   snapshotPathTemplate: "e2e/__screenshots__/{testFilePath}/{arg}{ext}"
 *   maxDiffPixelRatio: 0.001 (0.1% tolerance)
 *   animations: "disabled"
 *   caret: "hide"
 *
 * Generation command (iter-1, requires ratified_visual_by_chris=true):
 *   cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
 *     npx playwright test --project=visual \
 *     e2e/regression/vitalia-fase1-sub-tabs-line2/visual-goldens.spec.ts \
 *     --update-snapshots
 *
 * downstream-regression-na: brand-local E2E visual spec; no cross-brand consumers
 */

import { expect } from "@playwright/test";
import { test } from "../../fixtures/shell-theme.fixture";
import { SubTabsBarPage } from "./poms/sub-tabs-bar-page.pom";

const DESKTOP_VIEWPORT = { width: 1280, height: 800 };
const MOBILE_VIEWPORT = { width: 375, height: 667 };
const TENANT_ID = process.env["E2E_TENANT_ID"] ?? "vitalia-test-tenant";

// ---------------------------------------------------------------------------
// § 1 — Per-agent active state goldens (light mode, 1280x800)
// ---------------------------------------------------------------------------

test.describe("visual goldens — active agent light 1280 (F1-S8)", () => {
  test.use({ viewport: DESKTOP_VIEWPORT });

  test("active lisa light 1280", async ({ shellPage }) => {
    const pom = new SubTabsBarPage(shellPage);
    await pom.goto({ tenantId: TENANT_ID, agent: "lisa", subtab: "marca" });
    await expect(pom.getSubTabsBar()).toBeAttached();
    await shellPage.waitForTimeout(200);
    await expect(pom.getSubTabsBar()).toHaveScreenshot(
      "sub-tabs-lisa-light.png",
    );
  });

  test("active lucas light 1280", async ({ shellPage }) => {
    const pom = new SubTabsBarPage(shellPage);
    await pom.goto({ tenantId: TENANT_ID, agent: "lucas", subtab: "lanzar" });
    await expect(pom.getSubTabsBar()).toBeAttached();
    await shellPage.waitForTimeout(200);
    await expect(pom.getSubTabsBar()).toHaveScreenshot(
      "sub-tabs-lucas-light.png",
    );
  });

  test("active adrian light 1280", async ({ shellPage }) => {
    const pom = new SubTabsBarPage(shellPage);
    await pom.goto({ tenantId: TENANT_ID, agent: "adrian", subtab: "inbox" });
    await expect(pom.getSubTabsBar()).toBeAttached();
    await shellPage.waitForTimeout(200);
    await expect(pom.getSubTabsBar()).toHaveScreenshot(
      "sub-tabs-adrian-light.png",
    );
  });

  test("active valeria light 1280", async ({ shellPage }) => {
    const pom = new SubTabsBarPage(shellPage);
    await pom.goto({ tenantId: TENANT_ID, agent: "valeria", subtab: "agenda" });
    await expect(pom.getSubTabsBar()).toBeAttached();
    await shellPage.waitForTimeout(200);
    await expect(pom.getSubTabsBar()).toHaveScreenshot(
      "sub-tabs-valeria-light.png",
    );
  });

  test("active camila light 1280", async ({ shellPage }) => {
    const pom = new SubTabsBarPage(shellPage);
    await pom.goto({ tenantId: TENANT_ID, agent: "camila", subtab: "voz" });
    await expect(pom.getSubTabsBar()).toBeAttached();
    await shellPage.waitForTimeout(200);
    await expect(pom.getSubTabsBar()).toHaveScreenshot(
      "sub-tabs-camila-light.png",
    );
  });

  test("active config light 1280", async ({ shellPage }) => {
    const pom = new SubTabsBarPage(shellPage);
    await pom.goto({ tenantId: TENANT_ID, agent: "config", subtab: "cuenta" });
    await expect(pom.getSubTabsBar()).toBeAttached();
    await shellPage.waitForTimeout(200);
    await expect(pom.getSubTabsBar()).toHaveScreenshot(
      "sub-tabs-config-light.png",
    );
  });
});

// ---------------------------------------------------------------------------
// § 2 — Per-agent active state goldens (dark mode, 1280x800)
// ---------------------------------------------------------------------------

test.describe("visual goldens — active agent dark 1280 (F1-S8)", () => {
  test.use({ viewport: DESKTOP_VIEWPORT });

  test("active lisa dark 1280", async ({ darkShellPage }) => {
    const pom = new SubTabsBarPage(darkShellPage);
    await pom.goto({ tenantId: TENANT_ID, agent: "lisa", subtab: "marca" });
    await expect(pom.getSubTabsBar()).toBeAttached();
    await darkShellPage.waitForTimeout(200);
    await expect(pom.getSubTabsBar()).toHaveScreenshot(
      "sub-tabs-lisa-dark.png",
    );
  });

  test("active lucas dark 1280", async ({ darkShellPage }) => {
    const pom = new SubTabsBarPage(darkShellPage);
    await pom.goto({ tenantId: TENANT_ID, agent: "lucas", subtab: "lanzar" });
    await expect(pom.getSubTabsBar()).toBeAttached();
    await darkShellPage.waitForTimeout(200);
    await expect(pom.getSubTabsBar()).toHaveScreenshot(
      "sub-tabs-lucas-dark.png",
    );
  });

  test("active adrian dark 1280", async ({ darkShellPage }) => {
    const pom = new SubTabsBarPage(darkShellPage);
    await pom.goto({ tenantId: TENANT_ID, agent: "adrian", subtab: "inbox" });
    await expect(pom.getSubTabsBar()).toBeAttached();
    await darkShellPage.waitForTimeout(200);
    await expect(pom.getSubTabsBar()).toHaveScreenshot(
      "sub-tabs-adrian-dark.png",
    );
  });

  test("active valeria dark 1280", async ({ darkShellPage }) => {
    const pom = new SubTabsBarPage(darkShellPage);
    await pom.goto({ tenantId: TENANT_ID, agent: "valeria", subtab: "agenda" });
    await expect(pom.getSubTabsBar()).toBeAttached();
    await darkShellPage.waitForTimeout(200);
    await expect(pom.getSubTabsBar()).toHaveScreenshot(
      "sub-tabs-valeria-dark.png",
    );
  });

  test("active camila dark 1280", async ({ darkShellPage }) => {
    const pom = new SubTabsBarPage(darkShellPage);
    await pom.goto({ tenantId: TENANT_ID, agent: "camila", subtab: "voz" });
    await expect(pom.getSubTabsBar()).toBeAttached();
    await darkShellPage.waitForTimeout(200);
    await expect(pom.getSubTabsBar()).toHaveScreenshot(
      "sub-tabs-camila-dark.png",
    );
  });

  test("active config dark 1280", async ({ darkShellPage }) => {
    const pom = new SubTabsBarPage(darkShellPage);
    await pom.goto({ tenantId: TENANT_ID, agent: "config", subtab: "cuenta" });
    await expect(pom.getSubTabsBar()).toBeAttached();
    await darkShellPage.waitForTimeout(200);
    await expect(pom.getSubTabsBar()).toHaveScreenshot(
      "sub-tabs-config-dark.png",
    );
  });
});

// ---------------------------------------------------------------------------
// § 3 — Mobile overflow golden (Lucas 5 sub-tabs, 375x667)
// ---------------------------------------------------------------------------

test.describe("visual goldens — mobile overflow 375 (F1-S8)", () => {
  test.use({ viewport: MOBILE_VIEWPORT });

  test("mobile lucas 375", async ({ shellPage }) => {
    const pom = new SubTabsBarPage(shellPage);
    await pom.goto({ tenantId: TENANT_ID, agent: "lucas", subtab: "lanzar" });
    await expect(pom.getSubTabsBar()).toBeAttached();
    await shellPage.waitForTimeout(200);
    await expect(pom.getSubTabsBar()).toHaveScreenshot(
      "sub-tabs-mobile-lucas-375.png",
    );
  });
});
