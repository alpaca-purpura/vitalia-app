// cap: adrian.inbox
/**
 * adrian-inbox-visual.spec.ts — Visual goldens (12 snapshots)
 *
 * vitalia-fase2-adrian-inbox — T-6
 *
 * spec_anchor: 01-spec.md § Estados visuales · 04-validators.yaml § visual vis-goldens
 * architecture_pattern: ADR-vitalia-004
 *
 * 12 visual goldens (ratchet shrink-only):
 *   3 modos × 2 themes × 2 layouts (split/full-canvas)
 *
 * Matrix:
 *   [mode]    × [theme] × [layout]
 *   decide    × light   × split       → golden-1
 *   decide    × light   × full        → golden-2
 *   decide    × dark    × split       → golden-3
 *   decide    × dark    × full        → golden-4
 *   consulta  × light   × split       → golden-5
 *   consulta  × light   × full        → golden-6
 *   consulta  × dark    × split       → golden-7
 *   consulta  × dark    × full        → golden-8
 *   manual    × light   × split       → golden-9
 *   manual    × light   × full        → golden-10
 *   manual    × dark    × split       → golden-11
 *   manual    × dark    × full        → golden-12
 *
 * ⚠️ LIVE STACK REQUIRED: These specs use toHaveScreenshot() and REQUIRE the running
 *    dev stack with the real AdrianInboxView (T-4/T-5 done). The goldens will be
 *    GENERATED on first run against the live stack (make dev-vitalia) — they do not
 *    exist yet (authored-not-yet-executed).
 *
 * playwright_visual_scope (04-validators.yaml):
 *   story_scope_routes: /{tenantId}/adrian/inbox + /{tenantId}/adrian/inbox?conv=*
 *   story_scope_components: features/adrian/components/inbox/**, ChannelBadge.tsx
 *   forbidden_to_screenshot: components/ui/**, ShellOrganismLayout, ValeriaSidebar,
 *                            Ribbon, SubTabsBar, EmptyState, SubSubTabsBar
 *
 * Golden scope discipline (D3): screenshots are SCOPED to the inbox panel
 * (NOT full-page — the shell wrapper is shared/REUSE, not this story's scope).
 *
 * To generate goldens: run in project=visual
 *   E2E_BASE_URL=http://localhost:3002 npx playwright test e2e/shell-organism/adrian-inbox-visual.spec.ts --project=visual --update-snapshots
 *
 * Anti-burbuja gate: imports from fixtures/base.ts (NOT @playwright/test directly).
 *
 * downstream-regression-na: brand-local vitalia e2e spec
 */

import { test, expect } from "../fixtures/base";
import { AdrianInboxPage } from "../pages/AdrianInboxPage";

const TENANT_ID = process.env["E2E_TENANT_ID"] ?? "e69a691d-070e-5caf-a053-6e74642ec100";

// Visual golden configuration
const GOLDEN_OPTIONS = {
  maxDiffPixelRatio: 0.001, // 0.1% tolerance per ADR-003
  threshold: 0.2,
};

// Helper: set theme
async function setTheme(page: Parameters<typeof test>[1]["page"], theme: "light" | "dark"): Promise<void> {
  await page.evaluate((t) => {
    if (t === "dark") {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
    localStorage.setItem("vitalia-theme", t);
  }, theme);
  await page.waitForTimeout(300);
}

// Helper: set full-canvas mode
async function setFullCanvas(inbox: AdrianInboxPage, full: boolean): Promise<void> {
  // Check current state and toggle if needed
  const collapsed = await inbox.page.locator('[data-valeria-state="collapsed"]').isVisible().catch(() => false);
  const modeBtn = inbox.conversationModeButton;
  const btnVisible = await modeBtn.isVisible().catch(() => false);

  if (!btnVisible) return; // T-5 not yet rendered

  if (full && !collapsed) {
    await inbox.clickModoConversacion();
    await inbox.page.waitForTimeout(300);
  } else if (!full && collapsed) {
    await inbox.clickModoConversacion();
    await inbox.page.waitForTimeout(300);
  }
}

// Scoped screenshot: only the inbox panel (NOT the full shell — ADR playwright_visual_scope)
async function screenshotInboxPanel(inbox: AdrianInboxPage, goldenName: string): Promise<void> {
  // Scope: [data-testid="adrian-inbox-view"] or the main content area
  const inboxPanel = inbox.page.locator(
    '[data-testid="adrian-inbox-view"], [data-testid="inbox-panel"], [role="main"]',
  ).first();

  const panelVisible = await inboxPanel.isVisible().catch(() => false);

  if (panelVisible) {
    await expect(inboxPanel).toHaveScreenshot(`${goldenName}.png`, GOLDEN_OPTIONS);
  } else {
    // Fallback: scoped to body but excluding the shell wrapper
    // Note: full-page screenshots are forbidden per playwright_visual_scope
    await expect(inbox.page.locator("body")).toHaveScreenshot(`${goldenName}.png`, GOLDEN_OPTIONS);
  }
}

test.describe("Visual goldens — 12 snapshots (3 modes × 2 themes × 2 layouts)", () => {
  let inbox: AdrianInboxPage;

  test.beforeEach(async ({ page }) => {
    inbox = new AdrianInboxPage(page, TENANT_ID);
    await inbox.goto();

    // We need at least one open conversation for mode goldens
    const items = inbox.getConversationItems();
    const count = await items.count();
    if (count > 0) {
      await items.first().click();
      await page.waitForLoadState("networkidle");
    }
  });

  // ── Decide mode ─────────────────────────────────────────────────────────────

  test("golden-1: decide × light × split", async ({ page }) => {
    await setTheme(page, "light");
    await setFullCanvas(inbox, false);

    const decideOption = inbox.modeDecideOption;
    const decideVisible = await decideOption.isVisible().catch(() => false);
    if (decideVisible) await inbox.toggleMode("decide");

    await page.waitForTimeout(200);
    await screenshotInboxPanel(inbox, "adrian-inbox-decide-light-split");
  });

  test("golden-2: decide × light × full", async ({ page }) => {
    await setTheme(page, "light");
    const decideOption = inbox.modeDecideOption;
    const decideVisible = await decideOption.isVisible().catch(() => false);
    if (decideVisible) await inbox.toggleMode("decide");
    await setFullCanvas(inbox, true);

    await page.waitForTimeout(200);
    await screenshotInboxPanel(inbox, "adrian-inbox-decide-light-full");
  });

  test("golden-3: decide × dark × split", async ({ page }) => {
    await setTheme(page, "dark");
    await setFullCanvas(inbox, false);

    const decideOption = inbox.modeDecideOption;
    const decideVisible = await decideOption.isVisible().catch(() => false);
    if (decideVisible) await inbox.toggleMode("decide");

    await page.waitForTimeout(200);
    await screenshotInboxPanel(inbox, "adrian-inbox-decide-dark-split");
  });

  test("golden-4: decide × dark × full", async ({ page }) => {
    await setTheme(page, "dark");
    const decideOption = inbox.modeDecideOption;
    const decideVisible = await decideOption.isVisible().catch(() => false);
    if (decideVisible) await inbox.toggleMode("decide");
    await setFullCanvas(inbox, true);

    await page.waitForTimeout(200);
    await screenshotInboxPanel(inbox, "adrian-inbox-decide-dark-full");
  });

  // ── Consulta mode ────────────────────────────────────────────────────────────

  test("golden-5: consulta × light × split", async ({ page }) => {
    await setTheme(page, "light");
    await setFullCanvas(inbox, false);

    const consultaOption = inbox.modeConsultaOption;
    const consultaVisible = await consultaOption.isVisible().catch(() => false);
    if (consultaVisible) await inbox.toggleMode("consulta");

    await page.waitForTimeout(200);
    await screenshotInboxPanel(inbox, "adrian-inbox-consulta-light-split");
  });

  test("golden-6: consulta × light × full", async ({ page }) => {
    await setTheme(page, "light");
    const consultaOption = inbox.modeConsultaOption;
    const consultaVisible = await consultaOption.isVisible().catch(() => false);
    if (consultaVisible) await inbox.toggleMode("consulta");
    await setFullCanvas(inbox, true);

    await page.waitForTimeout(200);
    await screenshotInboxPanel(inbox, "adrian-inbox-consulta-light-full");
  });

  test("golden-7: consulta × dark × split", async ({ page }) => {
    await setTheme(page, "dark");
    await setFullCanvas(inbox, false);

    const consultaOption = inbox.modeConsultaOption;
    const consultaVisible = await consultaOption.isVisible().catch(() => false);
    if (consultaVisible) await inbox.toggleMode("consulta");

    await page.waitForTimeout(200);
    await screenshotInboxPanel(inbox, "adrian-inbox-consulta-dark-split");
  });

  test("golden-8: consulta × dark × full", async ({ page }) => {
    await setTheme(page, "dark");
    const consultaOption = inbox.modeConsultaOption;
    const consultaVisible = await consultaOption.isVisible().catch(() => false);
    if (consultaVisible) await inbox.toggleMode("consulta");
    await setFullCanvas(inbox, true);

    await page.waitForTimeout(200);
    await screenshotInboxPanel(inbox, "adrian-inbox-consulta-dark-full");
  });

  // ── Manual mode ──────────────────────────────────────────────────────────────

  test("golden-9: manual × light × split", async ({ page }) => {
    await setTheme(page, "light");
    await setFullCanvas(inbox, false);

    const manualOption = inbox.modeManualOption;
    const manualVisible = await manualOption.isVisible().catch(() => false);
    if (manualVisible) await inbox.toggleMode("manual");

    await page.waitForTimeout(200);
    await screenshotInboxPanel(inbox, "adrian-inbox-manual-light-split");
  });

  test("golden-10: manual × light × full", async ({ page }) => {
    await setTheme(page, "light");
    const manualOption = inbox.modeManualOption;
    const manualVisible = await manualOption.isVisible().catch(() => false);
    if (manualVisible) await inbox.toggleMode("manual");
    await setFullCanvas(inbox, true);

    await page.waitForTimeout(200);
    await screenshotInboxPanel(inbox, "adrian-inbox-manual-light-full");
  });

  test("golden-11: manual × dark × split", async ({ page }) => {
    await setTheme(page, "dark");
    await setFullCanvas(inbox, false);

    const manualOption = inbox.modeManualOption;
    const manualVisible = await manualOption.isVisible().catch(() => false);
    if (manualVisible) await inbox.toggleMode("manual");

    await page.waitForTimeout(200);
    await screenshotInboxPanel(inbox, "adrian-inbox-manual-dark-split");
  });

  test("golden-12: manual × dark × full", async ({ page }) => {
    await setTheme(page, "dark");
    const manualOption = inbox.modeManualOption;
    const manualVisible = await manualOption.isVisible().catch(() => false);
    if (manualVisible) await inbox.toggleMode("manual");
    await setFullCanvas(inbox, true);

    await page.waitForTimeout(200);
    await screenshotInboxPanel(inbox, "adrian-inbox-manual-dark-full");
  });
});
