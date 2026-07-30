/**
 * visual-goldens.spec.ts — 11 visual golden tests (F1-S7 Ribbon 6-tabs ratchet)
 *
 * F1-S7 vitalia-fase1-ribbon-6-tabs — T-5
 *
 * ITER-1: Goldens generated with `--update-snapshots --project=visual`.
 * Ratification: Chris side-by-side review required before ratchet locks.
 * Ratification authorized: ratified_visual_by_chris=true (2026-05-25)
 *
 * Per shell-mockup-per-component.md protocol — goldens against ratified HTML mockup:
 *   vitalia/docs/product/stories/vitalia-fase1-ribbon-6-tabs/mockups/ribbon-6-tabs.html
 *
 * 11 PNGs per 04-validators.yaml gherkin_coverage (visual scenarios):
 *   01. ribbon-active-lisa.png       — Lisa active tab (lisa/marca), light 1280x800
 *   02. ribbon-active-lucas.png      — Lucas active tab (lucas/lanzar), light 1280x800
 *   03. ribbon-active-adrian.png     — Adrián active tab (adrian/inbox), light 1280x800
 *   04. ribbon-active-valeria.png    — Valeria active tab (valeria/agenda), light 1280x800
 *   05. ribbon-active-camila.png     — Camila active tab (camila/voz), light 1280x800
 *   06. ribbon-active-config.png     — ConfigTab active (config/cuenta), light 1280x800
 *   07. ribbon-idle.png              — No active tab (invalid route foobar), light 1280x800
 *   08. ribbon-dark.png              — Valeria active, dark mode, 1280x800
 *   09. ribbon-mobile-375.png        — Lisa active, mobile 375x667
 *   10. ribbon-keyboard-focus.png    — Lucas tab focused via keyboard, light 1280x800
 *   11. ribbon-hover-inactive.png    — Hover on inactive Camila tab, light 1280x800
 *
 * Visual project config (playwright.config.ts):
 *   snapshotPathTemplate: "e2e/__screenshots__/{testFilePath}/{arg}{ext}"
 *   maxDiffPixelRatio: 0.001 (0.1% tolerance)
 *   animations: "disabled"
 *   caret: "hide"
 *
 * Generation command (iter-1, authorized by ratified_visual_by_chris=true 2026-05-25):
 *   cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
 *     npx playwright test --project=visual \
 *     e2e/regression/vitalia-fase1-ribbon-6-tabs/visual-goldens.spec.ts \
 *     --update-snapshots
 *
 * downstream-regression-na: brand-local E2E visual spec; no cross-brand consumers
 */

import { expect } from "@playwright/test";
import { test } from "../../fixtures/shell-theme.fixture";
import { RibbonPage } from "./poms/ribbon-page.pom";

const DESKTOP_VIEWPORT = { width: 1280, height: 800 };
const MOBILE_VIEWPORT = { width: 375, height: 667 };
const TENANT_ID = process.env["E2E_TENANT_ID"] ?? "vitalia-test-tenant";

// ---------------------------------------------------------------------------
// § 1 — Per-agent active state goldens (light, 1280x800)
// Test names match grep patterns from 04-validators.yaml
// ---------------------------------------------------------------------------

test.describe("visual goldens — active agent tabs light (F1-S7)", () => {
  test.use({ viewport: DESKTOP_VIEWPORT });

  test("active lisa light 1280", async ({ shellPage }) => {
    const pom = new RibbonPage(shellPage);
    await pom.goto({ tenantId: TENANT_ID, agent: "lisa", subtab: "marca" });
    await expect(pom.getRibbon()).toBeAttached();
    await shellPage.waitForTimeout(200); // Allow active state CSS to settle
    await expect(pom.getRibbon()).toHaveScreenshot("ribbon-active-lisa.png");
  });

  test("active lucas light 1280", async ({ shellPage }) => {
    const pom = new RibbonPage(shellPage);
    await pom.goto({ tenantId: TENANT_ID, agent: "lucas", subtab: "lanzar" });
    await expect(pom.getRibbon()).toBeAttached();
    await shellPage.waitForTimeout(200);
    await expect(pom.getRibbon()).toHaveScreenshot("ribbon-active-lucas.png");
  });

  test("active adrian light 1280", async ({ shellPage }) => {
    const pom = new RibbonPage(shellPage);
    await pom.goto({ tenantId: TENANT_ID, agent: "adrian", subtab: "inbox" });
    await expect(pom.getRibbon()).toBeAttached();
    await shellPage.waitForTimeout(200);
    await expect(pom.getRibbon()).toHaveScreenshot("ribbon-active-adrian.png");
  });

  test("active valeria light 1280", async ({ shellPage }) => {
    const pom = new RibbonPage(shellPage);
    await pom.goto({ tenantId: TENANT_ID, agent: "valeria", subtab: "agenda" });
    await expect(pom.getRibbon()).toBeAttached();
    await shellPage.waitForTimeout(200);
    await expect(pom.getRibbon()).toHaveScreenshot("ribbon-active-valeria.png");
  });

  test("active camila light 1280", async ({ shellPage }) => {
    const pom = new RibbonPage(shellPage);
    await pom.goto({ tenantId: TENANT_ID, agent: "camila", subtab: "voz" });
    await expect(pom.getRibbon()).toBeAttached();
    await shellPage.waitForTimeout(200);
    await expect(pom.getRibbon()).toHaveScreenshot("ribbon-active-camila.png");
  });

  test("active config light 1280", async ({ shellPage }) => {
    const pom = new RibbonPage(shellPage);
    // Navigate to config/cuenta — ConfigTab should be active
    await shellPage.goto(`/${TENANT_ID}/config/cuenta`);
    await shellPage.waitForSelector('[data-testid="ribbon"]', {
      state: "attached",
      timeout: 15_000,
    });
    await shellPage.waitForTimeout(200);
    await expect(pom.getRibbon()).toHaveScreenshot("ribbon-active-config.png");
  });
});

// ---------------------------------------------------------------------------
// § 2 — Idle state golden (no active tab)
// ---------------------------------------------------------------------------

test.describe("visual goldens — idle state (F1-S7)", () => {
  test.use({ viewport: DESKTOP_VIEWPORT });

  test("idle light 1280", async ({ shellPage }) => {
    const pom = new RibbonPage(shellPage);
    // Navigate to invalid agent — no tab should be active
    await pom.gotoRaw(`/${TENANT_ID}/foobar/baz`);
    await shellPage.waitForSelector('[data-testid="ribbon"]', {
      state: "attached",
      timeout: 15_000,
    });
    await shellPage.waitForTimeout(200);
    await expect(pom.getRibbon()).toHaveScreenshot("ribbon-idle.png");
  });
});

// ---------------------------------------------------------------------------
// § 3 — Dark mode golden (Valeria active, dark)
// ---------------------------------------------------------------------------

test.describe("visual goldens — dark mode (F1-S7)", () => {
  test.use({ viewport: DESKTOP_VIEWPORT });

  test("active valeria dark 1280", async ({ darkShellPage }) => {
    const pom = new RibbonPage(darkShellPage);
    await pom.goto({ tenantId: TENANT_ID, agent: "valeria", subtab: "agenda" });
    await expect(pom.getRibbon()).toBeAttached();
    await darkShellPage.waitForTimeout(200);
    await expect(pom.getRibbon()).toHaveScreenshot("ribbon-dark.png");
  });
});

// ---------------------------------------------------------------------------
// § 4 — Mobile golden (Lisa active, 375x667)
// ---------------------------------------------------------------------------

test.describe("visual goldens — mobile viewport (F1-S7)", () => {
  test.use({ viewport: MOBILE_VIEWPORT });

  test("mobile 375", async ({ shellPage }) => {
    const pom = new RibbonPage(shellPage);
    await pom.goto({ tenantId: TENANT_ID, agent: "lisa", subtab: "marca" });
    await expect(pom.getRibbon()).toBeAttached();
    await shellPage.waitForTimeout(200);
    await expect(pom.getRibbon()).toHaveScreenshot("ribbon-mobile-375.png");
  });
});

// ---------------------------------------------------------------------------
// § 5 — Keyboard focus golden (Lucas focused, Lisa active)
// ---------------------------------------------------------------------------

test.describe("visual goldens — keyboard focus state (F1-S7)", () => {
  test.use({ viewport: DESKTOP_VIEWPORT });

  test("keyboard focus 1280", async ({ shellPage }) => {
    const pom = new RibbonPage(shellPage);
    await pom.goto({ tenantId: TENANT_ID, agent: "lisa", subtab: "marca" });

    // Focus Lucas tab via keyboard
    await pom.getTab("lucas").focus();
    await shellPage.waitForTimeout(100);

    // Verify Lucas is focused (focus ring should be visible)
    const focusedSlug = await pom.getFocusedTabSlug();
    expect(focusedSlug).toBe("lucas");

    await expect(pom.getRibbon()).toHaveScreenshot("ribbon-keyboard-focus.png");
  });
});

// ---------------------------------------------------------------------------
// § 6 — Hover inactive tab golden (hover on Camila, Lisa active)
// ---------------------------------------------------------------------------

test.describe("visual goldens — hover inactive tab (F1-S7)", () => {
  test.use({ viewport: DESKTOP_VIEWPORT });

  test("hover inactive 1280", async ({ shellPage }) => {
    const pom = new RibbonPage(shellPage);
    await pom.goto({ tenantId: TENANT_ID, agent: "lisa", subtab: "marca" });

    // Hover over Camila tab (inactive tab hover state)
    await pom.getTab("camila").hover();
    await shellPage.waitForTimeout(200); // Allow hover CSS to apply

    await expect(pom.getRibbon()).toHaveScreenshot("ribbon-hover-inactive.png");
  });
});
