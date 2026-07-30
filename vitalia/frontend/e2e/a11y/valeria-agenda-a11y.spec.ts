/**
 * valeria-agenda-a11y.spec.ts — axe-core wcag2aa agenda + drawer + subform
 *
 * F2-S1 vitalia-fase2-valeria-agenda — T-17
 * Gherkin:
 *   axe-core wcag2aa calendar + drawer + subform
 *
 * Scenario coverage (04-validators.yaml):
 *   test_a11y_wcag2aa_agenda_drawer_subform
 *
 * Project: a11y
 * Depends on: valeria-agenda-cobro.spec.ts (step 9) — shares fixture + POMs
 *
 * Scans:
 *   1. Calendar grid (week view, authenticated)
 *   2. Appointment drawer open
 *   3. CobrarSaldo subform expanded
 *
 * Run:
 *   cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
 *     npx playwright test e2e/a11y/valeria-agenda-a11y.spec.ts --project=a11y
 *
 * downstream-regression-na: brand-local vitalia E2E A11y spec F2-S1
 */

import AxeBuilder from "@axe-core/playwright";
import { expect } from "@playwright/test";
import { test, VALERIA_AGENDA_FIXTURE, gotoAgenda } from "../regression/vitalia-fase2-valeria-agenda/fixtures/valeria-agenda.fixture";
import { setupAgendaGridMock, clearAgendaGridMock } from "../regression/vitalia-fase2-valeria-agenda/fixtures/__mocks__/agenda-grid";
import { AgendaViewPage } from "../regression/vitalia-fase2-valeria-agenda/poms/agenda-view-page.pom";
import { AppointmentDrawerPage } from "../regression/vitalia-fase2-valeria-agenda/poms/appointment-drawer-page.pom";
import { CobrarSaldoSubformPage } from "../regression/vitalia-fase2-valeria-agenda/poms/cobrar-saldo-subform-page.pom";

const { tenantId, sampleSlot } = VALERIA_AGENDA_FIXTURE;

// ── A11y: WCAG 2.1 AA — calendar + drawer + subform ───────────────────────

test.describe("A11y — axe-core wcag2aa valeria agenda surfaces", () => {
  test.beforeEach(async ({ agendaPage }) => {
    await setupAgendaGridMock(agendaPage, "with_seed");
  });

  test.afterEach(async ({ agendaPage }) => {
    await clearAgendaGridMock(agendaPage);
  });

  test("calendar grid passes axe wcag2aa (no critical/serious violations)", async ({
    agendaPage,
  }) => {
    await gotoAgenda(agendaPage, tenantId, { view: "semana" });

    const agendaView = new AgendaViewPage(agendaPage, tenantId);
    await agendaView.waitForLoaded();

    const results = await new AxeBuilder({ page: agendaPage })
      .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
      .exclude("#__nextjs-toast-errors") // Next.js dev overlay
      .exclude("[data-testid='agenda-skeleton']")
      .analyze();

    const criticalOrSerious = results.violations.filter(
      (v) => v.impact === "critical" || v.impact === "serious",
    );

    expect(
      criticalOrSerious,
      `A11y violations on calendar grid:\n${criticalOrSerious.map((v) => `  [${v.impact}] ${v.id}: ${v.description}\n    Nodes: ${v.nodes.map((n) => n.target.join(" > ")).join(", ")}`).join("\n")}`,
    ).toHaveLength(0);
  });

  test("appointment drawer passes axe wcag2aa (modal role + aria-modal)", async ({
    agendaPage,
  }) => {
    await gotoAgenda(agendaPage, tenantId, { view: "semana" });

    const agendaView = new AgendaViewPage(agendaPage, tenantId);
    const drawer = new AppointmentDrawerPage(agendaPage);

    await agendaView.waitForLoaded();
    await agendaView.clickSlot(sampleSlot.appointmentId);
    await drawer.waitForOpen();

    const results = await new AxeBuilder({ page: agendaPage })
      .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
      .include('[data-testid="appointment-drawer"]')
      .analyze();

    const criticalOrSerious = results.violations.filter(
      (v) => v.impact === "critical" || v.impact === "serious",
    );

    expect(
      criticalOrSerious,
      `A11y violations in appointment drawer:\n${criticalOrSerious.map((v) => `  [${v.impact}] ${v.id}: ${v.description}`).join("\n")}`,
    ).toHaveLength(0);

    // Confirm ARIA attributes present
    await expect(drawer.panel).toHaveAttribute("role", "dialog");
    await expect(drawer.panel).toHaveAttribute("aria-modal", "true");
  });

  test("cobrar saldo subform passes axe wcag2aa (form labels + error roles)", async ({
    agendaPage,
  }) => {
    await gotoAgenda(agendaPage, tenantId, { view: "semana" });

    const agendaView = new AgendaViewPage(agendaPage, tenantId);
    const drawer = new AppointmentDrawerPage(agendaPage);
    const subform = new CobrarSaldoSubformPage(agendaPage);

    await agendaView.waitForLoaded();
    await agendaView.clickSlot(sampleSlot.appointmentId);
    await drawer.waitForOpen();
    await drawer.expandSection("pago");
    await drawer.clickCobrarSaldo();
    await subform.waitForVisible();

    const results = await new AxeBuilder({ page: agendaPage })
      .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
      .include('[data-testid="cobrar-saldo-subform"]')
      .analyze();

    const criticalOrSerious = results.violations.filter(
      (v) => v.impact === "critical" || v.impact === "serious",
    );

    expect(
      criticalOrSerious,
      `A11y violations in cobrar saldo subform:\n${criticalOrSerious.map((v) => `  [${v.impact}] ${v.id}: ${v.description}`).join("\n")}`,
    ).toHaveLength(0);
  });

  test("slot grid has no duplicate IDs (accessibility anti-pattern)", async ({
    agendaPage,
  }) => {
    await gotoAgenda(agendaPage, tenantId, { view: "semana" });

    const agendaView = new AgendaViewPage(agendaPage, tenantId);
    await agendaView.waitForLoaded();

    // Check for duplicate IDs in the grid (common with list rendering)
    const duplicates = await agendaPage.evaluate(() => {
      const ids = Array.from(document.querySelectorAll("[id]")).map(
        (el) => el.id,
      );
      const seen = new Set<string>();
      const dups: string[] = [];
      for (const id of ids) {
        if (seen.has(id)) dups.push(id);
        seen.add(id);
      }
      return dups;
    });

    expect(
      duplicates,
      `Duplicate IDs found in DOM: ${duplicates.join(", ")}`,
    ).toHaveLength(0);
  });

  test("drawer close button has accessible label", async ({ agendaPage }) => {
    await gotoAgenda(agendaPage, tenantId, { view: "semana" });

    const agendaView = new AgendaViewPage(agendaPage, tenantId);
    const drawer = new AppointmentDrawerPage(agendaPage);

    await agendaView.waitForLoaded();
    await agendaView.clickSlot(sampleSlot.appointmentId);
    await drawer.waitForOpen();

    // Close button must have accessible name
    const closeBtn = drawer.closeButton;
    const ariaLabel = await closeBtn.getAttribute("aria-label");
    const title = await closeBtn.getAttribute("title");
    const textContent = await closeBtn.textContent();

    const hasAccessibleName =
      (ariaLabel && ariaLabel.length > 0) ||
      (title && title.length > 0) ||
      (textContent && textContent.trim().length > 0);

    expect(hasAccessibleName).toBe(true);
  });
});
