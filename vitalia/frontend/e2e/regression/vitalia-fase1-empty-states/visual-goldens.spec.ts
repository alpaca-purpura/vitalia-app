/**
 * visual-goldens.spec.ts — ~70 visual golden tests (F1-S10 empty-states ratchet)
 *
 * F1-S10 vitalia-fase1-empty-states — T-11 (TESTS-ONLY · production_code: false)
 *
 * ITER-1: Goldens generated with `--update-snapshots --project=visual`.
 * Ratification: pending_chris_visual_ratify — stack required for live generation.
 * Per shell-mockup-per-component.md protocol — goldens against 7 ratified HTML mockups:
 *   vitalia/docs/product/stories/vitalia-fase1-empty-states/mockups/
 *     empty-states-grid.html
 *     lisa-servicios-placeholder.html
 *     adrian-embudo-placeholder.html
 *     adrian-inbox-placeholder.html
 *     camila-voz-placeholder.html
 *     valeria-agenda-placeholder.html
 *     config-conexiones-placeholder.html
 *
 * Coverage:
 *   A. 22 sub-tabs × light + dark = 44 PNG
 *      Crop: [data-testid="subtab-content"] area only (NO Ribbon/TopBar/Valeria)
 *      Naming: {agent}-{subtab}-{light|dark}.png
 *
 *   B. Adrián Inbox takeover states = 6 PNG (3 states × light + dark)
 *      adrian-inbox-state-A-light.png    (chip 🤖 + botón Tomar visible)
 *      adrian-inbox-state-A-dark.png
 *      adrian-inbox-state-B-light.png    (TakeoverBanner visible + MessageInput enabled)
 *      adrian-inbox-state-B-dark.png
 *      adrian-inbox-sidebar-closed-light.png  (grid col-3 = 0)
 *      adrian-inbox-sidebar-closed-dark.png
 *
 *   C. Responsive breakpoints × 6 special placeholders = ~18 PNG
 *      mobile (375x812) / tablet (768x1024) / desktop (1280x900) = 3 viewports
 *      6 specials: lisa-servicios · adrian-embudo · adrian-inbox · valeria-agenda · camila-voz · config-conexiones
 *      Naming: {placeholder}-{mobile|tablet|desktop}.png
 *
 * Visual project config (playwright.config.ts):
 *   snapshotPathTemplate: "e2e/__screenshots__/{testFilePath}/{arg}{ext}"
 *   maxDiffPixelRatio: 0.001 (0.1% tolerance) — A and B sections
 *   maxDiffPixelRatio: 0.005 — C responsive section (minor anti-aliasing cross-viewport)
 *   animations: "disabled"
 *   caret: "hide"
 *
 * Generation command (pending live generation — stack required):
 *   cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
 *     npx playwright test --project=visual \
 *     e2e/regression/vitalia-fase1-empty-states/visual-goldens.spec.ts \
 *     --update-snapshots
 *
 * Compare command (after goldens generated):
 *   cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
 *     npx playwright test --project=visual \
 *     e2e/regression/vitalia-fase1-empty-states/visual-goldens.spec.ts
 *
 * pending_chris_visual_ratify: true — goldens pending live generation + Chris review.
 * Goldens output: e2e/__screenshots__/regression/vitalia-fase1-empty-states/visual-goldens.spec.ts/
 *
 * downstream-regression-na: brand-local E2E visual spec; no cross-brand consumers
 */

import { expect } from "@playwright/test";
import { test } from "../../fixtures/empty-states.fixture";
import { ShellOrganismPage } from "../../pages/ShellOrganismPage";
import { AdrianInboxPage } from "../../pages/AdrianInboxPage";
import { ValeriaAgendaPage } from "../../pages/ValeriaAgendaPage";

// ---------------------------------------------------------------------------
// Viewports
// ---------------------------------------------------------------------------

const DESKTOP_VIEWPORT = { width: 1280, height: 900 };
const TABLET_VIEWPORT = { width: 768, height: 1024 };
const MOBILE_VIEWPORT = { width: 375, height: 812 };

// ---------------------------------------------------------------------------
// 22 sub-tabs inventory (from RIBBON_SUBTABS SSoT — agent-catalog.ts)
// Mateo excluded (transversal agent — empty array per SSoT).
// ---------------------------------------------------------------------------

const ALL_SUBTABS: readonly { agent: string; subtab: string }[] = [
  // lisa: 4 sub-tabs
  { agent: "lisa", subtab: "marca" },
  { agent: "lisa", subtab: "doctores" },
  { agent: "lisa", subtab: "servicios" },
  { agent: "lisa", subtab: "compliance" },
  // lucas: 5 sub-tabs
  { agent: "lucas", subtab: "lanzar" },
  { agent: "lucas", subtab: "envuelo" },
  { agent: "lucas", subtab: "recursos" },
  { agent: "lucas", subtab: "resultados" },
  { agent: "lucas", subtab: "mercado" },
  // adrian: 4 sub-tabs
  { agent: "adrian", subtab: "inbox" },
  { agent: "adrian", subtab: "embudo" },
  { agent: "adrian", subtab: "outbound" },
  { agent: "adrian", subtab: "propuestas" },
  // valeria: 2 sub-tabs
  { agent: "valeria", subtab: "agenda" },
  { agent: "valeria", subtab: "pacientes" },
  // camila: 4 sub-tabs
  { agent: "camila", subtab: "voz" },
  { agent: "camila", subtab: "reactivar" },
  { agent: "camila", subtab: "multiplicar" },
  { agent: "camila", subtab: "reputacion" },
  // config: 3 sub-tabs
  { agent: "config", subtab: "cuenta" },
  { agent: "config", subtab: "conexiones" },
  { agent: "config", subtab: "avanzado" },
] as const;

// ---------------------------------------------------------------------------
// § A — 22 sub-tabs × light theme (22 PNG)
// Crops: [data-testid="subtab-content-{agent}-{subtab}"] area only.
// Does NOT include Ribbon, TopBar, or ValeriaSidebar.
// ---------------------------------------------------------------------------

test.describe("visual goldens — 22 sub-tabs light theme (F1-S10)", () => {
  test.use({ viewport: DESKTOP_VIEWPORT });

  for (const { agent, subtab } of ALL_SUBTABS) {
    test(`${agent}/${subtab} light desktop`, async ({
      shellPage,
      tenantId,
    }) => {
      const shell = new ShellOrganismPage(shellPage, tenantId);
      await shell.goto(agent, subtab);

      // Wait for subtab content to mount
      const contentLocator = shellPage
        .locator(`[data-testid="subtab-content-${agent}-${subtab}"]`)
        .first();
      await expect(contentLocator).toBeVisible({ timeout: 15_000 });
      await shellPage.waitForTimeout(200); // Allow CSS transitions + active state to settle

      await expect(contentLocator).toHaveScreenshot(
        `${agent}-${subtab}-light.png`,
        {
          maxDiffPixelRatio: 0.001,
        },
      );
    });
  }
});

// ---------------------------------------------------------------------------
// § A (dark) — 22 sub-tabs × dark theme (22 PNG)
// ---------------------------------------------------------------------------

test.describe("visual goldens — 22 sub-tabs dark theme (F1-S10)", () => {
  test.use({ viewport: DESKTOP_VIEWPORT });

  for (const { agent, subtab } of ALL_SUBTABS) {
    test(`${agent}/${subtab} dark desktop`, async ({
      darkShellPage,
      tenantId,
    }) => {
      const shell = new ShellOrganismPage(darkShellPage, tenantId);
      await shell.goto(agent, subtab);

      const contentLocator = darkShellPage.locator(
        `[data-testid="subtab-content-${agent}-${subtab}"]`,
      );
      await expect(contentLocator).toBeVisible({ timeout: 15_000 });
      await darkShellPage.waitForTimeout(200);

      await expect(contentLocator).toHaveScreenshot(
        `${agent}-${subtab}-dark.png`,
        {
          maxDiffPixelRatio: 0.001,
        },
      );
    });
  }
});

// ---------------------------------------------------------------------------
// § B — Adrián Inbox takeover states (6 PNG: 3 states × light + dark)
// Mockup baseline: mockups/adrian-inbox-placeholder.html
// Validators: val-fe-visual-inbox-state-A-adrian · val-fe-visual-inbox-state-B-human
//             val-fe-visual-inbox-sidebar-closed
// ---------------------------------------------------------------------------

test.describe("visual goldens — Adrián Inbox takeover state A (F1-S10)", () => {
  test.use({ viewport: DESKTOP_VIEWPORT });

  test("adrian-inbox state A (Adrián maneja) light", async ({
    shellPage,
    tenantId,
  }) => {
    const inbox = new AdrianInboxPage(shellPage, tenantId);
    await inbox.goto();

    // Assert state A is active (default) — chip + takeover button visible
    await expect(inbox.adrianModeChip).toBeVisible({ timeout: 10_000 });
    await expect(inbox.takeControlButton).toBeVisible();
    await shellPage.waitForTimeout(200);

    // Capture full inbox 3-col area
    const inboxContainer = shellPage
      .locator('[data-testid="subtab-content-adrian-inbox"]')
      .first();
    await expect(inboxContainer).toBeVisible();
    await expect(inboxContainer).toHaveScreenshot(
      "adrian-inbox-state-A-light.png",
      {
        maxDiffPixelRatio: 0.001,
      },
    );
  });

  test("adrian-inbox state A (Adrián maneja) dark", async ({
    darkShellPage,
    tenantId,
  }) => {
    const inbox = new AdrianInboxPage(darkShellPage, tenantId);
    await inbox.goto();

    await expect(inbox.adrianModeChip).toBeVisible({ timeout: 10_000 });
    await expect(inbox.takeControlButton).toBeVisible();
    await darkShellPage.waitForTimeout(200);

    const inboxContainer = darkShellPage.locator(
      '[data-testid="subtab-content-adrian-inbox"]',
    );
    await expect(inboxContainer).toBeVisible();
    await expect(inboxContainer).toHaveScreenshot(
      "adrian-inbox-state-A-dark.png",
      {
        maxDiffPixelRatio: 0.001,
      },
    );
  });
});

test.describe("visual goldens — Adrián Inbox takeover state B (F1-S10)", () => {
  test.use({ viewport: DESKTOP_VIEWPORT });

  test("adrian-inbox state B (usuario en control · banner amarillo) light", async ({
    shellPage,
    tenantId,
  }) => {
    const inbox = new AdrianInboxPage(shellPage, tenantId);
    await inbox.goto();

    // Transition A → B
    await expect(inbox.takeControlButton).toBeVisible({ timeout: 10_000 });
    await inbox.takeControl();
    // State B: TakeoverBanner visible + MessageInput enabled
    await expect(inbox.returnControlButton).toBeVisible({ timeout: 5_000 });
    await shellPage.waitForTimeout(200);

    const inboxContainer = shellPage
      .locator('[data-testid="subtab-content-adrian-inbox"]')
      .first();
    await expect(inboxContainer).toBeVisible();
    await expect(inboxContainer).toHaveScreenshot(
      "adrian-inbox-state-B-light.png",
      {
        maxDiffPixelRatio: 0.001,
      },
    );
  });

  test("adrian-inbox state B (usuario en control · banner amarillo) dark", async ({
    darkShellPage,
    tenantId,
  }) => {
    const inbox = new AdrianInboxPage(darkShellPage, tenantId);
    await inbox.goto();

    await expect(inbox.takeControlButton).toBeVisible({ timeout: 10_000 });
    await inbox.takeControl();
    await expect(inbox.returnControlButton).toBeVisible({ timeout: 5_000 });
    await darkShellPage.waitForTimeout(200);

    const inboxContainer = darkShellPage.locator(
      '[data-testid="subtab-content-adrian-inbox"]',
    );
    await expect(inboxContainer).toBeVisible();
    await expect(inboxContainer).toHaveScreenshot(
      "adrian-inbox-state-B-dark.png",
      {
        maxDiffPixelRatio: 0.001,
      },
    );
  });
});

test.describe("visual goldens — Adrián Inbox sidebar closed (F1-S10)", () => {
  test.use({ viewport: DESKTOP_VIEWPORT });

  test("adrian-inbox sidebar closed (grid col-3 = 0) light", async ({
    shellPage,
    tenantId,
  }) => {
    const inbox = new AdrianInboxPage(shellPage, tenantId);
    await inbox.goto();

    // Close the sidebar
    await expect(inbox.closeSidebarButton).toBeVisible({ timeout: 10_000 });
    await inbox.closeSidebar();
    // Sidebar should collapse col-3 to 0
    await expect(
      shellPage.locator('[data-sidebar="closed"]').first(),
    ).toBeVisible({
      timeout: 5_000,
    });
    await shellPage.waitForTimeout(200);

    const inboxContainer = shellPage
      .locator('[data-testid="subtab-content-adrian-inbox"]')
      .first();
    await expect(inboxContainer).toBeVisible();
    await expect(inboxContainer).toHaveScreenshot(
      "adrian-inbox-sidebar-closed-light.png",
      { maxDiffPixelRatio: 0.001 },
    );
  });

  test("adrian-inbox sidebar closed (grid col-3 = 0) dark", async ({
    darkShellPage,
    tenantId,
  }) => {
    const inbox = new AdrianInboxPage(darkShellPage, tenantId);
    await inbox.goto();

    await expect(inbox.closeSidebarButton).toBeVisible({ timeout: 10_000 });
    await inbox.closeSidebar();
    await expect(
      darkShellPage.locator('[data-sidebar="closed"]').first(),
    ).toBeVisible({
      timeout: 5_000,
    });
    await darkShellPage.waitForTimeout(200);

    const inboxContainer = darkShellPage.locator(
      '[data-testid="subtab-content-adrian-inbox"]',
    );
    await expect(inboxContainer).toBeVisible();
    await expect(inboxContainer).toHaveScreenshot(
      "adrian-inbox-sidebar-closed-dark.png",
      { maxDiffPixelRatio: 0.001 },
    );
  });
});

// ---------------------------------------------------------------------------
// § C — Responsive breakpoints × 6 special placeholders (~18 PNG)
// Tolerance: 0.005 (allow minor anti-aliasing differences cross-viewport)
// 6 specials: lisa-servicios · adrian-embudo · adrian-inbox · valeria-agenda ·
//             camila-voz · config-conexiones
// ---------------------------------------------------------------------------

// Helper type for special placeholder spec
interface SpecialPlaceholder {
  agent: string;
  subtab: string;
  slug: string;
}

const SPECIAL_PLACEHOLDERS: readonly SpecialPlaceholder[] = [
  { agent: "lisa", subtab: "servicios", slug: "lisa-servicios" },
  { agent: "adrian", subtab: "embudo", slug: "adrian-embudo" },
  { agent: "adrian", subtab: "inbox", slug: "adrian-inbox" },
  { agent: "valeria", subtab: "agenda", slug: "valeria-agenda" },
  { agent: "camila", subtab: "voz", slug: "camila-voz" },
  { agent: "config", subtab: "conexiones", slug: "config-conexiones" },
] as const;

// ── § C1 — Mobile 375x812 ────────────────────────────────────────────────────

test.describe("visual goldens — responsive mobile 375x812 · 6 specials (F1-S10)", () => {
  test.use({ viewport: MOBILE_VIEWPORT });

  for (const { agent, subtab, slug } of SPECIAL_PLACEHOLDERS) {
    test(`${slug} mobile 375`, async ({ shellPage, tenantId }) => {
      const shell = new ShellOrganismPage(shellPage, tenantId);
      await shell.goto(agent, subtab);

      const contentLocator = shellPage
        .locator(`[data-testid="subtab-content-${agent}-${subtab}"]`)
        .first();
      await expect(contentLocator).toBeVisible({ timeout: 15_000 });
      await shellPage.waitForTimeout(300); // Extra settle time for mobile reflow

      await expect(contentLocator).toHaveScreenshot(`${slug}-mobile.png`, {
        maxDiffPixelRatio: 0.005,
      });
    });
  }
});

// ── § C2 — Tablet 768x1024 ──────────────────────────────────────────────────

test.describe("visual goldens — responsive tablet 768x1024 · 6 specials (F1-S10)", () => {
  test.use({ viewport: TABLET_VIEWPORT });

  for (const { agent, subtab, slug } of SPECIAL_PLACEHOLDERS) {
    test(`${slug} tablet 768`, async ({ shellPage, tenantId }) => {
      const shell = new ShellOrganismPage(shellPage, tenantId);
      await shell.goto(agent, subtab);

      const contentLocator = shellPage
        .locator(`[data-testid="subtab-content-${agent}-${subtab}"]`)
        .first();
      await expect(contentLocator).toBeVisible({ timeout: 15_000 });
      await shellPage.waitForTimeout(300);

      await expect(contentLocator).toHaveScreenshot(`${slug}-tablet.png`, {
        maxDiffPixelRatio: 0.005,
      });
    });
  }
});

// ── § C3 — Desktop 1280x900 (responsive baseline) ──────────────────────────

test.describe("visual goldens — responsive desktop 1280x900 · 6 specials (F1-S10)", () => {
  test.use({ viewport: DESKTOP_VIEWPORT });

  for (const { agent, subtab, slug } of SPECIAL_PLACEHOLDERS) {
    test(`${slug} desktop 1280`, async ({ shellPage, tenantId }) => {
      const shell = new ShellOrganismPage(shellPage, tenantId);
      await shell.goto(agent, subtab);

      const contentLocator = shellPage
        .locator(`[data-testid="subtab-content-${agent}-${subtab}"]`)
        .first();
      await expect(contentLocator).toBeVisible({ timeout: 15_000 });
      await shellPage.waitForTimeout(200);

      await expect(contentLocator).toHaveScreenshot(`${slug}-desktop.png`, {
        maxDiffPixelRatio: 0.001,
      });
    });
  }
});

// ---------------------------------------------------------------------------
// § D — Valeria Agenda week-default (additional validator golden)
// Validator: val-fe-visual-valeria-agenda-week-default
// Mockup baseline: mockups/valeria-agenda-placeholder.html
// ---------------------------------------------------------------------------

test.describe("visual goldens — Valeria Agenda week-default (F1-S10)", () => {
  test.use({ viewport: DESKTOP_VIEWPORT });

  test("valeria agenda week-default light 1280 (Lun 26 today + 10 slots + footer)", async ({
    shellPage,
    tenantId,
  }) => {
    const agenda = new ValeriaAgendaPage(shellPage, tenantId);
    await agenda.goto();

    // Full agenda structure must be visible
    await agenda.expectAgendaMounted();
    await shellPage.waitForTimeout(200);

    const agendaContainer = shellPage
      .locator('[data-testid="valeria-agenda-placeholder"]')
      .first();
    await expect(agendaContainer).toBeVisible();
    await expect(agendaContainer).toHaveScreenshot(
      "valeria-agenda-week-default-light.png",
      { maxDiffPixelRatio: 0.001 },
    );
  });

  test("valeria agenda week-default dark 1280", async ({
    darkShellPage,
    tenantId,
  }) => {
    const agenda = new ValeriaAgendaPage(darkShellPage, tenantId);
    await agenda.goto();

    await agenda.expectAgendaMounted();
    await darkShellPage.waitForTimeout(200);

    const agendaContainer = darkShellPage.locator(
      '[data-testid="valeria-agenda-placeholder"]',
    );
    await expect(agendaContainer).toBeVisible();
    await expect(agendaContainer).toHaveScreenshot(
      "valeria-agenda-week-default-dark.png",
      { maxDiffPixelRatio: 0.001 },
    );
  });
});

// ---------------------------------------------------------------------------
// § E — Lisa Servicios toggle state goldens (2 PNG)
// Validators: val-fe-visual-lisa-servicios-catalogo · val-fe-visual-lisa-servicios-escalera
// Mockup baseline: mockups/lisa-servicios-placeholder.html
// ---------------------------------------------------------------------------

test.describe("visual goldens — Lisa Servicios toggle states (F1-S10)", () => {
  test.use({ viewport: DESKTOP_VIEWPORT });

  test("lisa-servicios catalogo state light 1280", async ({
    shellPage,
    tenantId,
  }) => {
    const shell = new ShellOrganismPage(shellPage, tenantId);
    await shell.goto("lisa", "servicios").first();

    const contentLocator = shellPage
      .locator('[data-testid="subtab-content-lisa-servicios"]')
      .first();
    await expect(contentLocator).toBeVisible({ timeout: 15_000 });

    // Default state is Catálogo — verify catalogo grid is present
    const catalogoGrid = shellPage
      .locator('[data-testid="catalogo-grid"]')
      .first();
    await expect(catalogoGrid).toBeVisible({ timeout: 5_000 });
    await shellPage.waitForTimeout(200);

    await expect(contentLocator).toHaveScreenshot(
      "lisa-servicios-catalogo-light.png",
      {
        maxDiffPixelRatio: 0.001,
      },
    );
  });

  test("lisa-servicios escalera state light 1280", async ({
    shellPage,
    tenantId,
  }) => {
    const shell = new ShellOrganismPage(shellPage, tenantId);
    await shell.goto("lisa", "servicios");

    const contentLocator = shellPage
      .locator('[data-testid="subtab-content-lisa-servicios"]')
      .first();
    await expect(contentLocator).toBeVisible({ timeout: 15_000 });

    // Click Escalera toggle
    const escaleraPill = shellPage
      .locator('[data-testid="servicios-toggle"]')
      .first()
      .locator("text=Escalera");
    await expect(escaleraPill).toBeVisible({ timeout: 5_000 });
    await escaleraPill.click();

    // Wait for escalera pane to mount
    await expect(
      shellPage.locator('[data-testid="pane-escalera"]').first(),
    ).toBeVisible({ timeout: 5_000 });
    await shellPage.waitForTimeout(200);

    await expect(contentLocator).toHaveScreenshot(
      "lisa-servicios-escalera-light.png",
      {
        maxDiffPixelRatio: 0.001,
      },
    );
  });
});

// ---------------------------------------------------------------------------
// § F — Adrián Embudo Kanban/Lista toggle state goldens (2 PNG)
// Validators: val-fe-visual-adrian-embudo-kanban · val-fe-visual-adrian-embudo-lista
// Mockup baseline: mockups/adrian-embudo-placeholder.html
// ---------------------------------------------------------------------------

test.describe("visual goldens — Adrián Embudo Kanban/Lista states (F1-S10)", () => {
  test.use({ viewport: DESKTOP_VIEWPORT });

  test("adrian-embudo kanban state light 1280 (6 cols)", async ({
    shellPage,
    tenantId,
  }) => {
    const shell = new ShellOrganismPage(shellPage, tenantId);
    await shell.goto("adrian", "embudo").first();

    const contentLocator = shellPage
      .locator('[data-testid="subtab-content-adrian-embudo"]')
      .first();
    await expect(contentLocator).toBeVisible({ timeout: 15_000 });

    // Default state is Kanban — verify kanban board present
    const kanbanBoard = shellPage
      .locator('[data-testid="kanban-board"]')
      .first();
    await expect(kanbanBoard).toBeVisible({ timeout: 5_000 });
    await shellPage.waitForTimeout(200);

    await expect(contentLocator).toHaveScreenshot(
      "adrian-embudo-kanban-light.png",
      {
        maxDiffPixelRatio: 0.001,
      },
    );
  });

  test("adrian-embudo lista state light 1280", async ({
    shellPage,
    tenantId,
  }) => {
    const shell = new ShellOrganismPage(shellPage, tenantId);
    await shell.goto("adrian", "embudo");

    const contentLocator = shellPage
      .locator('[data-testid="subtab-content-adrian-embudo"]')
      .first();
    await expect(contentLocator).toBeVisible({ timeout: 15_000 });

    // Click Lista toggle
    const listaPill = shellPage
      .locator('[data-testid="embudo-toggle"]')
      .first()
      .locator("text=Lista");
    await expect(listaPill).toBeVisible({ timeout: 5_000 });
    await listaPill.click();

    // Wait for lista view to mount
    await expect(
      shellPage.locator('[data-testid="pane-lista"]').first(),
    ).toBeVisible({
      timeout: 5_000,
    });
    await shellPage.waitForTimeout(200);

    await expect(contentLocator).toHaveScreenshot(
      "adrian-embudo-lista-light.png",
      {
        maxDiffPixelRatio: 0.001,
      },
    );
  });
});
