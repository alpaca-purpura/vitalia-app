/**
 * a11y-mobile-drawer.spec.ts — SC-8 mobile drawer aria-modal + focus trap
 *
 * F1-S5 vitalia-fase1-valeria-rail-history — T-8 / T-5.bis hotfix
 *
 * Gherkin: 01-spec.md § 1 Scenario 8 (a11y)
 *
 * Given: Viewport 375x667, valeriaState='full' (drawer open)
 * When:  User interacts with drawer
 * Then:  drawer has aria-modal=true, backdrop aria-hidden=true,
 *        Esc closes drawer, X closes drawer, axe 0 violations
 *
 * SC-8 gherkin_coverage:
 *   - SC-8-1: mobile drawer renders aside (role=complementary, aria-modal=true)
 *   - SC-8-2: backdrop has aria-hidden=true
 *   - SC-8-3: click backdrop closes drawer
 *   - SC-8-4: press Esc closes drawer (valeriaState → 'collapsed')
 *   - SC-8-5: click X button closes drawer
 *   - SC-8-6: axe wcag2aa 0 violations — mobile drawer open state @axe
 *
 * Mobile drawer renders when:
 *   (a) viewport width < 768px (matchMedia resolves to isMobile=true)
 *   (b) valeriaState !== 'collapsed'
 *
 * ─── T-5.bis FIX — PRODUCTION BUG RESOLVED ───────────────────────────────────
 *
 * STATUS: All SC-8 tests are now ACTIVE (skip removed).
 *
 * BUG ORIGIN (T-8 diagnosis):
 *   ValeriaSidebar was rendered inside `<main className="... hidden md:block">`.
 *   At mobile viewport (<768px), `display: none` applied to the entire block,
 *   preventing position:fixed children from rendering per CSS spec.
 *
 * FIX (T-5.bis — ValeriaSidebar.tsx):
 *   React.createPortal() wraps the mobile drawer JSX when isMobile && isExpanded.
 *   The portal mounts directly on document.body, escaping the hidden parent.
 *   React tree stays intact (ValeriaSidebar remains child of ShellOrganismLayoutClient
 *   for state/context purposes). ShellOrganismLayoutClient.tsx NOT modified.
 *
 * GHERKIN_COVERAGE STATUS:
 *   SC-8-1..SC-8-6: ACTIVE — tests pass with T-5.bis Portal fix.
 *
 * downstream-regression-na: brand-local E2E spec; no cross-brand consumers
 */

import { expect } from "@playwright/test";
import { AxeBuilder } from "@axe-core/playwright";
import { test } from "../../fixtures/shell-theme.fixture";
import { ValeriaSidebarPage } from "../../pages/ValeriaSidebarPage";

const MOBILE_VIEWPORT = { width: 375, height: 667 };

// Mobile drawer aside selector — targets ONLY the mobile drawer (has aria-modal)
const MOBILE_DRAWER_SELECTOR =
  "[data-testid=valeria-sidebar][aria-modal='true']";

// T-5.bis: Production bug (display:none parent) fixed via React.createPortal()
// in ValeriaSidebar.tsx. All SC-8 tests are now active.

test.describe("SC-8 — mobile drawer a11y", () => {
  // Force mobile viewport at the describe level.
  // Note: smoke project uses Desktop Chrome context; setViewportSize in test
  // changes CSS media queries for that page, making md:hidden inactive at 375px.
  test.use({ viewport: MOBILE_VIEWPORT });

  test("SC-8-1: mobile drawer has role='dialog' + aria-modal='true'", async ({
    authedPage,
  }) => {
    await authedPage.setViewportSize(MOBILE_VIEWPORT);

    const pom = new ValeriaSidebarPage(authedPage);
    await pom.goto({
      valeriaState: "full",
      shellMode: "agentic",
      theme: "light",
    });

    // Mobile drawer renders as fixed overlay when isMobile=true.
    // ★ T-8.bis a11y fix: role="dialog" (not "complementary") porque aria-modal
    //   no es válido en role=complementary per WCAG/ARIA spec. Dialog role
    //   permite aria-modal + focus trap correctly.
    const mobileDrawer = authedPage.locator(MOBILE_DRAWER_SELECTOR);
    await expect(mobileDrawer).toBeVisible({ timeout: 5_000 });
    await expect(mobileDrawer).toHaveAttribute("role", "dialog");
    await expect(mobileDrawer).toHaveAttribute("aria-modal", "true");
    await expect(mobileDrawer).toHaveAttribute("aria-expanded", "true");
    await expect(mobileDrawer).toHaveAttribute("aria-label", "Panel Valeria");
  });

  test("SC-8-2: mobile drawer backdrop has aria-hidden='true'", async ({
    authedPage,
  }) => {
    await authedPage.setViewportSize(MOBILE_VIEWPORT);

    const pom = new ValeriaSidebarPage(authedPage);
    await pom.goto({
      valeriaState: "full",
      shellMode: "agentic",
      theme: "light",
    });

    await expect(pom.drawerBackdrop).toBeVisible({ timeout: 3_000 });
    await expect(pom.drawerBackdrop).toHaveAttribute("aria-hidden", "true");
  });

  test("SC-8-3: click backdrop closes mobile drawer", async ({
    authedPage,
  }) => {
    await authedPage.setViewportSize(MOBILE_VIEWPORT);

    const pom = new ValeriaSidebarPage(authedPage);
    await pom.goto({
      valeriaState: "full",
      shellMode: "agentic",
      theme: "light",
    });

    await expect(pom.drawerBackdrop).toBeVisible({ timeout: 3_000 });

    // dispatchEvent bypasses Next.js dev portal overlay
    await pom.drawerBackdrop.dispatchEvent("click");
    await authedPage.waitForTimeout(200);

    await expect(pom.drawerBackdrop).not.toBeVisible({ timeout: 3_000 });

    const state = await pom.getValeriaState();
    expect(state).toBe("collapsed");
  });

  test("SC-8-4: press Esc closes mobile drawer (valeriaState → 'collapsed')", async ({
    authedPage,
  }) => {
    await authedPage.setViewportSize(MOBILE_VIEWPORT);

    const pom = new ValeriaSidebarPage(authedPage);
    await pom.goto({
      valeriaState: "full",
      shellMode: "agentic",
      theme: "light",
    });

    const mobileDrawer = authedPage.locator(MOBILE_DRAWER_SELECTOR);
    await expect(mobileDrawer).toBeVisible({ timeout: 3_000 });

    await pom.pressShortcut("Escape");
    await authedPage.waitForTimeout(200);

    const state = await pom.getValeriaState();
    expect(state).toBe("collapsed");
  });

  test("SC-8-5: click X button closes mobile drawer", async ({
    authedPage,
  }) => {
    await authedPage.setViewportSize(MOBILE_VIEWPORT);

    const pom = new ValeriaSidebarPage(authedPage);
    await pom.goto({
      valeriaState: "full",
      shellMode: "agentic",
      theme: "light",
    });

    await expect(pom.drawerCloseBtn).toBeVisible({ timeout: 3_000 });

    await pom.drawerCloseBtn.dispatchEvent("click");
    await authedPage.waitForTimeout(200);

    await expect(pom.drawerCloseBtn).not.toBeVisible({ timeout: 3_000 });

    const state = await pom.getValeriaState();
    expect(state).toBe("collapsed");
  });

  test("SC-8-6: axe wcag2aa 0 violations — mobile drawer open state @axe", async ({
    authedPage,
  }) => {
    await authedPage.setViewportSize(MOBILE_VIEWPORT);

    const pom = new ValeriaSidebarPage(authedPage);
    await pom.goto({
      valeriaState: "full",
      shellMode: "agentic",
      theme: "light",
    });

    const mobileDrawer = authedPage.locator(MOBILE_DRAWER_SELECTOR);
    await expect(mobileDrawer).toBeVisible({ timeout: 5_000 });

    const results = await new AxeBuilder({ page: authedPage })
      .withTags(["wcag2a", "wcag2aa"])
      .include(MOBILE_DRAWER_SELECTOR)
      .analyze();

    expect(results.violations).toEqual([]);
  });
});
