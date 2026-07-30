/**
 * visual-goldens.spec.ts — 6 visual golden tests (F1-S4 shell layout mockup ratchet).
 *
 * F1-S4 vitalia-fase1-shell-layout-5050 — T-7
 *
 * FASE 7B: tests UNSKIPPED post Chris ratify visual side-by-side 2026-05-23 PM.
 * Goldens generados con `--update-snapshots --project=visual` (config visual project
 * en playwright.config.ts incluye regression dir visual-goldens.spec.ts).
 *
 * 6 test cases per 06-tickets.yaml gherkin_coverage (visual scenario):
 *   1. agentic light 1280x800 — matches shell-layout-agentic.html (light)
 *   2. agentic dark 1280x800  — matches shell-layout-agentic.html (dark)
 *   3. agentic rail 1280x800  — agentic mode valeriaState='rail' (light)
 *   4. web light 1280x800     — matches shell-layout-web.html (light)
 *   5. web dark 1280x800      — matches shell-layout-web.html (dark)
 *   6. agentic mobile 375x667 — grid 1-col, AppPanel 100%, ValeriaSidebar oculto
 *
 * Visual project config (playwright.config.ts):
 *   snapshotPathTemplate: "e2e/__screenshots__/{testFilePath}/{arg}{ext}"
 *   maxDiffPixelRatio: 0.001 (0.1% tolerance)
 *   animations: "disabled"
 *   caret: "hide"
 *
 * Mockup references (ratified by Chris 2026-05-23):
 *   - vitalia/docs/product/stories/vitalia-fase1-shell-layout-5050/mockups/shell-layout-agentic.html
 *   - vitalia/docs/product/stories/vitalia-fase1-shell-layout-5050/mockups/shell-layout-web.html
 *
 * Fase 7B generation command (post Chris ratification only):
 *   cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
 *     npx playwright test --project=visual \
 *     e2e/regression/vitalia-fase1-shell-layout-5050/visual-goldens.spec.ts \
 *     --update-snapshots
 *
 * downstream-regression-na: brand-local E2E visual spec; no cross-brand consumers
 */

import { test, expect } from "../../fixtures/shell-theme.fixture";
import { ShellLayoutPage } from "../../pages/ShellLayoutPage";

const DESKTOP_VIEWPORT = { width: 1280, height: 800 };
const MOBILE_VIEWPORT = { width: 375, height: 667 };

// ---------------------------------------------------------------------------
// § 1 — Agentic mode goldens (1280x800)
// ---------------------------------------------------------------------------

test.describe("visual goldens — agentic mode (F1-S4)", () => {
  test.use({ viewport: DESKTOP_VIEWPORT });

  test("agentic light 1280x800 matches", async ({ shellPage, tenantId }) => {
    const pom = new ShellLayoutPage(shellPage);
    await pom.gotoShell(tenantId);
    await expect(pom.topBar).toBeVisible();
    await expect(shellPage).toHaveScreenshot("agentic-1280x800-light.png", {
      fullPage: false,
    });
  });

  test("agentic dark 1280x800 matches", async ({ darkShellPage, tenantId }) => {
    const pom = new ShellLayoutPage(darkShellPage);
    await pom.gotoShell(tenantId);
    await expect(pom.topBar).toBeVisible();
    await expect(darkShellPage).toHaveScreenshot("agentic-1280x800-dark.png", {
      fullPage: false,
    });
  });

  test("agentic rail 1280x800 matches", async ({ shellPage, tenantId }) => {
    const pom = new ShellLayoutPage(shellPage);
    await pom.gotoShell(tenantId);
    // Set valeriaState='rail' for this golden
    await pom.setValeriaStateViaStore("rail");
    await expect(pom.topBar).toBeVisible();
    await expect(shellPage).toHaveScreenshot("agentic-rail-1280x800.png", {
      fullPage: false,
    });
  });
});

// ---------------------------------------------------------------------------
// § 2 — Web mode goldens (1280x800)
// ---------------------------------------------------------------------------

test.describe("visual goldens — web mode (F1-S4)", () => {
  test.use({ viewport: DESKTOP_VIEWPORT });

  test("web light 1280x800 matches", async ({ shellPage, tenantId }) => {
    const pom = new ShellLayoutPage(shellPage);
    await pom.gotoShell(tenantId);
    await pom.setShellModeViaStore("web");
    await expect(pom.topBar).toBeVisible();
    await expect(shellPage).toHaveScreenshot("web-1280x800-light.png", {
      fullPage: false,
    });
  });

  test("web dark 1280x800 matches", async ({ darkShellPage, tenantId }) => {
    const pom = new ShellLayoutPage(darkShellPage);
    await pom.gotoShell(tenantId);
    await pom.setShellModeViaStore("web");
    await expect(pom.topBar).toBeVisible();
    await expect(darkShellPage).toHaveScreenshot("web-1280x800-dark.png", {
      fullPage: false,
    });
  });
});

// ---------------------------------------------------------------------------
// § 3 — Mobile golden (375x667)
// ---------------------------------------------------------------------------

test.describe("visual goldens — mobile (F1-S4)", () => {
  test.use({ viewport: MOBILE_VIEWPORT });

  test("agentic mobile 375x667 matches", async ({ shellPage, tenantId }) => {
    const pom = new ShellLayoutPage(shellPage);
    await pom.gotoShell(tenantId);
    await expect(pom.appSlot).toBeVisible();
    await expect(shellPage).toHaveScreenshot("agentic-mobile-375x667.png", {
      fullPage: false,
    });
  });
});
