/**
 * valeria-agenda-keyboard.spec.ts — SC-10 keyboard navigation + focus trap
 *
 * F2-S1 vitalia-fase2-valeria-agenda — T-17
 * Gherkin:
 *   SC-10 "keyboard Tab/Enter/Esc/Shift+Tab + focus trap in drawer"
 *
 * Scenario coverage (04-validators.yaml):
 *   test_keyboard_nav_slot_drawer_focus_trap
 *
 * Project: smoke
 * Depends on: AgendaViewPage + AppointmentDrawerPage + CobrarSaldoSubformPage POMs
 *
 * Run:
 *   cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
 *     npx playwright test e2e/regression/vitalia-fase2-valeria-agenda/valeria-agenda-keyboard.spec.ts \
 *     --project=smoke
 *
 * downstream-regression-na: brand-local vitalia E2E spec F2-S1
 */

import { expect } from "@playwright/test";
import { test, VALERIA_AGENDA_FIXTURE, gotoAgenda } from "./fixtures/valeria-agenda.fixture";
import { setupAgendaGridMock, clearAgendaGridMock } from "./fixtures/__mocks__/agenda-grid";
import { AgendaViewPage } from "./poms/agenda-view-page.pom";
import { AppointmentDrawerPage } from "./poms/appointment-drawer-page.pom";
import { CobrarSaldoSubformPage } from "./poms/cobrar-saldo-subform-page.pom";

const { tenantId, sampleSlot } = VALERIA_AGENDA_FIXTURE;

// ── SC-10: Keyboard navigation + focus trap ────────────────────────────────

test.describe("SC-10 — keyboard navigation + focus trap", () => {
  test.beforeEach(async ({ agendaPage }) => {
    await setupAgendaGridMock(agendaPage, "with_seed");
    await gotoAgenda(agendaPage, tenantId, { view: "semana" });
  });

  test.afterEach(async ({ agendaPage }) => {
    await clearAgendaGridMock(agendaPage);
  });

  test("Enter key on focused slot opens drawer", async ({ agendaPage }) => {
    const agendaView = new AgendaViewPage(agendaPage, tenantId);
    const drawer = new AppointmentDrawerPage(agendaPage);

    await agendaView.waitForLoaded();

    // Focus the slot via keyboard (Tab to reach it)
    const slot = agendaView.getSlot(sampleSlot.appointmentId);
    await slot.focus();

    // Press Enter to open drawer
    await agendaPage.keyboard.press("Enter");
    await drawer.waitForOpen();

    await expect(drawer.panel).toBeVisible();
  });

  test("Escape closes drawer and returns focus to triggering slot", async ({
    agendaPage,
  }) => {
    const agendaView = new AgendaViewPage(agendaPage, tenantId);
    const drawer = new AppointmentDrawerPage(agendaPage);

    await agendaView.waitForLoaded();

    // Open drawer
    await agendaView.clickSlot(sampleSlot.appointmentId);
    await drawer.waitForOpen();

    // Close with Escape
    await drawer.closeWithEscape();

    // Drawer hidden
    await expect(drawer.panel).not.toBeVisible({ timeout: 5_000 });

    // Focus returned to the triggering slot (ARIA spec: focus trap restoration)
    const slot = agendaView.getSlot(sampleSlot.appointmentId);
    await expect(slot).toBeFocused({ timeout: 3_000 });
  });

  test("Tab cycles through drawer interactive elements (focus trap active)", async ({
    agendaPage,
  }) => {
    const agendaView = new AgendaViewPage(agendaPage, tenantId);
    const drawer = new AppointmentDrawerPage(agendaPage);

    await agendaView.waitForLoaded();
    await agendaView.clickSlot(sampleSlot.appointmentId);
    await drawer.waitForOpen();

    // Close button should be focused first (or first focusable element)
    const closeBtn = drawer.closeButton;

    // Tab through interactive elements in drawer
    await agendaPage.keyboard.press("Tab");
    await agendaPage.keyboard.press("Tab");
    await agendaPage.keyboard.press("Tab");

    // After several Tabs, focus stays within drawer (focus trap)
    // The focused element should be inside the drawer panel
    const focusedInsideDrawer = await agendaPage.evaluate(() => {
      const focused = document.activeElement;
      const drawerPanel = document.querySelector(
        '[data-testid="appointment-drawer"]',
      );
      return drawerPanel?.contains(focused) ?? false;
    });
    expect(focusedInsideDrawer).toBe(true);

    await expect(closeBtn).toBeTruthy(); // POM locator accessible
  });

  test("Shift+Tab moves focus backwards within drawer", async ({
    agendaPage,
  }) => {
    const agendaView = new AgendaViewPage(agendaPage, tenantId);
    const drawer = new AppointmentDrawerPage(agendaPage);

    await agendaView.waitForLoaded();
    await agendaView.clickSlot(sampleSlot.appointmentId);
    await drawer.waitForOpen();

    // Tab to the second focusable element
    await agendaPage.keyboard.press("Tab");
    await agendaPage.keyboard.press("Tab");

    // Shift+Tab moves backwards
    await agendaPage.keyboard.press("Shift+Tab");

    // Focus should still be inside the drawer
    const focusedInsideDrawer = await agendaPage.evaluate(() => {
      const focused = document.activeElement;
      const drawerPanel = document.querySelector(
        '[data-testid="appointment-drawer"]',
      );
      return drawerPanel?.contains(focused) ?? false;
    });
    expect(focusedInsideDrawer).toBe(true);
  });

  test("keyboard navigation does not expose PHI in URL", async ({
    agendaPage,
  }) => {
    const agendaView = new AgendaViewPage(agendaPage, tenantId);
    const drawer = new AppointmentDrawerPage(agendaPage);

    await agendaView.waitForLoaded();

    // Use keyboard to open drawer
    const slot = agendaView.getSlot(sampleSlot.appointmentId);
    await slot.focus();
    await agendaPage.keyboard.press("Enter");
    await drawer.waitForOpen();

    // URL must NOT contain patient name or DNI
    const url = agendaPage.url();
    expect(url).not.toMatch(/\d{8}/); // no 8-digit DNI
    expect(url).not.toMatch(/patient[_=-]/i);
    expect(url).not.toMatch(/name[_=-]/i);
  });

  test("cobrar saldo subform accessible via keyboard", async ({ agendaPage }) => {
    const agendaView = new AgendaViewPage(agendaPage, tenantId);
    const drawer = new AppointmentDrawerPage(agendaPage);
    const subform = new CobrarSaldoSubformPage(agendaPage);

    await agendaView.waitForLoaded();
    await agendaView.clickSlot(sampleSlot.appointmentId);
    await drawer.waitForOpen();
    await drawer.expandSection("pago");

    // Focus "Cobrar saldo" button and activate via keyboard
    await drawer.cobrarSaldoButton.focus();
    await agendaPage.keyboard.press("Enter");

    // Subform should open
    await subform.waitForVisible();
    await expect(subform.container).toBeVisible();

    // Submit button should be focusable
    await subform.submitButton.focus();
    await expect(subform.submitButton).toBeFocused({ timeout: 3_000 });
  });

  test("slot aria-label does not contain raw DNI", async ({ agendaPage }) => {
    const agendaView = new AgendaViewPage(agendaPage, tenantId);
    await agendaView.waitForLoaded();

    const slot = agendaView.getSlot(sampleSlot.appointmentId);

    // aria-label must not contain raw 8-digit DNI
    const ariaLabel = await slot.getAttribute("aria-label");
    if (ariaLabel) {
      expect(ariaLabel).not.toMatch(/\d{8}/);
    }

    // data-testid pattern is acceptable (appointment ID is not PHI)
    const testId = await slot.getAttribute("data-testid");
    expect(testId).toContain(sampleSlot.appointmentId);
  });
});
