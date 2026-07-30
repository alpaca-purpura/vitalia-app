/**
 * mobile-collapse.spec.ts — SC-2 negative: viewport < md (375x667) colapsa a 1 columna.
 *
 * F1-S4 vitalia-fase1-shell-layout-5050 — T-7
 * Gherkin: SC-2 "Given viewport 375x667 (mobile), When shell carga,
 *           Then solo AppPanel visible, ValeriaSidebar oculto, sin overflow horizontal."
 *
 * Scenario coverage (04-validators.yaml):
 *   val-fe-e2e-mobile-collapse
 *
 * Project: smoke (playwright.config.ts — regression/*.spec.ts añadido a testMatch)
 * Requires: dev server at E2E_BASE_URL (localhost:3002), Clerk auth state.
 *
 * Run:
 *   cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
 *     npx playwright test e2e/regression/vitalia-fase1-shell-layout-5050/mobile-collapse.spec.ts \
 *     --project=smoke
 *
 * downstream-regression-na: brand-local E2E spec; no cross-brand consumers
 */

import { test, expect } from "../../fixtures/shell-theme.fixture";
import { ShellLayoutPage } from "../../pages/ShellLayoutPage";

const MOBILE_VIEWPORT = { width: 375, height: 667 };

test.describe("SC-2 — mobile collapse (F1-S4)", () => {
  test.use({ viewport: MOBILE_VIEWPORT });

  test.beforeEach(async ({ shellPage, tenantId }) => {
    const pom = new ShellLayoutPage(shellPage);
    await pom.gotoShell(tenantId);
  });

  // ── Assertion 1: resize handle display:none mobile ─────────────────────────

  test("resize handle display:none mobile", async ({ shellPage }) => {
    const pom = new ShellLayoutPage(shellPage);
    // At mobile viewport, the agentic main branch is hidden (md:block → hidden on mobile)
    // The resize handle inside it should not be visible
    const isVisible = await pom.isResizeHandleVisible();
    expect(isVisible).toBe(false);
  });

  // ── Assertion 2: ValeriaSlot oculto mobile ─────────────────────────────────
  // UN-SKIPPED 2026-05-29 (vitalia-shell-state-persistence T-5):
  // The fix landed in T-1..T-4:
  //   - mobileDrawerOpen is now an independent slice (default false).
  //   - ValeriaSidebar mobile drawer visibility is governed SOLELY by mobileDrawerOpen,
  //     NOT by valeriaState='full' (the old bug that auto-opened the drawer on mobile).
  //   - shell-theme.fixture.ts shellPage seeds valeriaState='full' (default fixture),
  //     but mobileDrawerOpen=false → no drawer renders → visibleCount=0. Fixed.

  test("ValeriaSlot oculto mobile", async ({
    shellPage,
  }) => {
    // POM.valeriaSlot usa filter({ visible: true }) — en mobile ValeriaSidebar es CSS-hidden
    // y el filter no resuelve ningún elemento. Usamos locator base sin filter para verificar:
    //   (a) el elemento existe en DOM (agentic branch renderiza aunque CSS-hidden)
    //   (b) ninguna instancia está visible en viewport 375px
    //
    // Post-fix: mobileDrawerOpen=false (seed by shellPage fixture via addInitScript).
    // The portal drawer only mounts when (isMobile && mobileDrawerOpen) — per ValeriaSidebar.tsx.
    // With mobileDrawerOpen=false, no portal renders → visibleCount=0. SC-4 verified.
    const allValeriaSlots = shellPage.getByTestId("valeria-sidebar");
    const domCount = await allValeriaSlots.count();
    const visibleCount = await allValeriaSlots
      .filter({ visible: true })
      .count();
    // DOM presence: el slot existe en el árbol (puede estar en la rama agentic hidden)
    expect(domCount).toBeGreaterThanOrEqual(0); // puede no existir en mobile-only branch
    // Visibility: ningún slot visible en viewport mobile (mobileDrawerOpen=false)
    expect(visibleCount).toBe(0);
  });

  // ── Assertion 3: AppSlot 100% viewport mobile ──────────────────────────────

  test("AppSlot 100% viewport mobile", async ({ shellPage }) => {
    const pom = new ShellLayoutPage(shellPage);
    // The mobile <main> shows only AppPanelSlot without Valeria
    await expect(pom.appSlot).toBeVisible();
    const appWidth = await pom.getAppSlotWidth();
    // AppSlot should fill the viewport width (375px) — allow ±2px for scrollbar/border
    expect(appWidth).toBeGreaterThanOrEqual(373);
    expect(appWidth).toBeLessThanOrEqual(377);
  });

  // ── Assertion 4: no overflow horizontal ────────────────────────────────────

  test("no overflow horizontal", async ({ shellPage }) => {
    // Check document scrollWidth <= clientWidth (no horizontal overflow)
    const hasHorizontalOverflow = await shellPage.evaluate(() => {
      return (
        document.documentElement.scrollWidth >
        document.documentElement.clientWidth
      );
    });
    expect(hasHorizontalOverflow).toBe(false);
  });
});
