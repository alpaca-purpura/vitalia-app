// cap: clinics.lisa.doctores
// story-origin: vitalia-fase2-lisa-doctores
/**
 * AvailabilityCalendarPage.ts — Playwright POM for doctor horarios calendar.
 *
 * Covers: week navigation, 24h toggle, drag-to-create, BloquePopover, delete block.
 *
 * Used by T-E2E specs for:
 *   - SC-1 (weekly block + fecha-fin)
 *   - SC-1b (biweekly + N iterations)
 *   - SC-1c (week nav + one-off)
 *   - SC-1d (delete block)
 *   - SC-3b (delete block with confirmed appointment)
 *   - V-FN-1, V-FN-2, V-FN-3, V-FN-4, V-FN-7
 *
 * T-FE-3 vitalia-fase2-lisa-doctores
 * spec_anchor: 04-validators.yaml § POM fixtures + 01-spec.md § SC-1/SC-1b/SC-1c/SC-1d/SC-3b
 *
 * Note: the dual-mount workaround (.filter({visible:true})) was removed on
 * T-FIX-2 (2026-06-01) — vitalia-shell-dual-mount-a11y-fix (c9d2bd31) fixed
 * the shell to render a single `[data-testid="app-panel-slot"]` per viewport.
 * BloquePopover is a Radix popover (portal) — kept page-level.
 */

import type { Page, Locator } from "@playwright/test";

export class AvailabilityCalendarPage {
  readonly page: Page;

  /** Visible app-panel-slot — root for all panel-scoped locators (B2 fix). */
  readonly panelRoot: Locator;

  // Calendar container
  readonly calendar: Locator;
  readonly calendarSkeleton: Locator;

  // Week navigation
  readonly prevWeekButton: Locator;
  readonly nextWeekButton: Locator;
  readonly weekLabel: Locator;

  // 24h toggle
  readonly toggle24h: Locator;

  // Grid: day columns (0=Mon..6=Sun)
  readonly dayColumns: Locator;

  // Hour cells
  readonly hourLabels: Locator;

  // Blocks (use getBlockById for specific block)
  readonly allBlocks: Locator;

  // BloquePopover — Radix portal (page-level, single instance)
  readonly bloquePopover: Locator;
  readonly bloquePopoverTitle: Locator;
  readonly startTimeInput: Locator;
  readonly endTimeInput: Locator;
  readonly freqSelect: Locator;
  readonly endConditionSelect: Locator;
  readonly endDateInput: Locator;
  readonly occurrencesInput: Locator;
  readonly specificDateInput: Locator;
  readonly saveBlockButton: Locator;
  readonly cancelBlockButton: Locator;
  readonly deleteBlockButton: Locator;

  // Delete warning dialog (SC-3b)
  readonly deleteWarningDialog: Locator;
  readonly confirmDeleteButton: Locator;
  readonly cancelDeleteButton: Locator;

  constructor(page: Page) {
    this.page = page;

    // Single app-panel-slot (vitalia-shell-dual-mount-a11y-fix resolved double-mount).
    this.panelRoot = page.getByTestId("app-panel-slot");

    // Calendar container — panel-scoped
    this.calendar = this.panelRoot.getByTestId("availability-calendar");
    this.calendarSkeleton = this.panelRoot.getByTestId("calendar-skeleton");

    // Week navigation — panel-scoped
    this.prevWeekButton = this.panelRoot.getByTestId("week-nav-prev");
    this.nextWeekButton = this.panelRoot.getByTestId("week-nav-next");
    this.weekLabel = this.panelRoot.locator(
      '[data-testid="availability-calendar"] span.font-medium',
    );

    // 24h toggle — panel-scoped
    this.toggle24h = this.panelRoot.getByTestId("toggle-24h");

    // Grid — panel-scoped
    this.dayColumns = this.panelRoot.getByTestId(/^day-col-\d+$/);
    this.hourLabels = this.panelRoot.getByTestId(/^hour-label-\d+$/);

    // Blocks — panel-scoped
    this.allBlocks = this.panelRoot.getByTestId(/^block-/);

    // BloquePopover — Radix portal (page-level, single instance, outside app-panel-slot)
    this.bloquePopover = page.getByTestId("bloque-popover");
    this.bloquePopoverTitle = this.bloquePopover.locator("h3");
    this.startTimeInput = page.locator("#startTime");
    this.endTimeInput = page.locator("#endTime");
    this.freqSelect = page.locator('[id="freq"]').first();
    this.endConditionSelect = page.locator('[id="endConditionKind"]').first();
    this.endDateInput = page.locator("#endDate");
    this.occurrencesInput = page.locator("#occurrences");
    this.specificDateInput = page.locator("#specificDate");
    this.saveBlockButton = this.bloquePopover.locator('button[type="submit"]');
    this.cancelBlockButton = this.bloquePopover.locator(
      'button:has-text("Cancelar")',
    );
    this.deleteBlockButton = page.getByTestId("btn-delete-block");

    // Delete warning dialog (SC-3b) — page-level dialog
    this.deleteWarningDialog = page.locator('[role="dialog"]').last();
    this.confirmDeleteButton = this.deleteWarningDialog.locator(
      'button:has-text("Sí, eliminar")',
    );
    this.cancelDeleteButton = this.deleteWarningDialog.locator(
      'button:has-text("Cancelar")',
    );
  }

  /**
   * Navigate to the horarios tab for a doctor.
   */
  async goto(tenantId: string, doctorId: string): Promise<void> {
    await this.page.goto(`/${tenantId}/lisa/staff/${doctorId}/horarios`);
    await this.calendar.waitFor({ state: "visible", timeout: 10_000 });
  }

  /**
   * Get a specific block by its ID (panel-scoped).
   */
  getBlock(blockId: string): Locator {
    return this.panelRoot.getByTestId(`block-${blockId}`);
  }

  /**
   * Get a day column (0=Monday, 6=Sunday) — panel-scoped.
   */
  getDayColumn(dayIndex: number): Locator {
    return this.panelRoot.getByTestId(`day-col-${dayIndex}`);
  }

  /**
   * Get a cell by day and hour (for interaction) — panel-scoped.
   */
  getCell(dayIndex: number, hour: number): Locator {
    return this.panelRoot.getByTestId(`cell-${dayIndex}-${hour}`);
  }

  /**
   * Navigate to next week.
   */
  async goToNextWeek(): Promise<void> {
    await this.nextWeekButton.click();
  }

  /**
   * Navigate to previous week.
   */
  async goToPrevWeek(): Promise<void> {
    await this.prevWeekButton.click();
  }

  /**
   * Toggle 24h view.
   */
  async toggle24hView(): Promise<void> {
    await this.toggle24h.click();
  }

  /**
   * Simulate drag-to-create: click drag from start cell to end cell on same day.
   * (Simplified: mousedown + mousemove + mouseup)
   */
  async dragToCreateBlock(
    dayIndex: number,
    startHour: number,
    endHour: number,
  ): Promise<void> {
    const startCell = this.getCell(dayIndex, startHour);
    const endCell = this.getCell(dayIndex, endHour);

    const startBox = await startCell.boundingBox();
    const endBox = await endCell.boundingBox();

    if (!startBox || !endBox) {
      throw new Error(
        `Could not find cells for day=${dayIndex} hours=${startHour}-${endHour}`,
      );
    }

    const startX = startBox.x + startBox.width / 2;
    const startY = startBox.y + startBox.height / 2;
    const endX = endBox.x + endBox.width / 2;
    const endY = endBox.y + endBox.height / 2;

    await this.page.mouse.move(startX, startY);
    await this.page.mouse.down();
    await this.page.mouse.move(endX, endY, { steps: 3 });
    await this.page.mouse.up();

    // Wait for popover
    await this.bloquePopover.waitFor({ state: "visible", timeout: 5_000 });
  }

  /**
   * Click on an existing block to open BloquePopover.
   */
  async clickBlock(blockId: string): Promise<void> {
    await this.getBlock(blockId).click();
    await this.bloquePopover.waitFor({ state: "visible", timeout: 5_000 });
  }

  /**
   * Fill BloquePopover for a weekly recurrent block with end_date.
   * (SC-1: drag mon 9-13 → popover repetir semanal + fecha-fin +8sem)
   */
  async fillWeeklyBlockWithEndDate(
    startTime: string,
    endTime: string,
    endDate: string,
  ): Promise<void> {
    // freq = weekly (default)
    // endConditionKind = end_date (default)
    await this.endDateInput.fill(endDate);
    await this.saveBlockButton.click();
  }

  /**
   * Fill BloquePopover for a biweekly block with N occurrences.
   * (SC-1b: quincenal + N=6)
   */
  async fillBiweeklyBlockWithOccurrences(occurrences: number): Promise<void> {
    // Select biweekly
    await this.freqSelect.selectOption("biweekly");
    // Select occurrences
    await this.endConditionSelect.selectOption("occurrences");
    await this.occurrencesInput.fill(String(occurrences));
    await this.saveBlockButton.click();
  }

  /**
   * Fill BloquePopover as one-off "Solo esta semana".
   * (SC-1c)
   */
  async fillOneOffBlock(): Promise<void> {
    await this.endConditionSelect.selectOption("open_ended");
    await this.saveBlockButton.click();
  }

  /**
   * Delete an existing block from its popover (SC-1d).
   */
  async deleteBlock(blockId: string): Promise<void> {
    await this.clickBlock(blockId);
    await this.deleteBlockButton.click();
    // If confirmation dialog appears, confirm
    const dialogVisible = await this.deleteWarningDialog
      .isVisible()
      .catch(() => false);
    if (dialogVisible) {
      await this.confirmDeleteButton.click();
    }
  }

  /**
   * Count visible blocks in the calendar (panel-scoped).
   */
  async getBlockCount(): Promise<number> {
    return this.allBlocks.count();
  }

  /**
   * Wait for block to appear in the calendar (panel-scoped).
   */
  async waitForBlock(blockId: string, timeout = 5_000): Promise<void> {
    await this.getBlock(blockId).waitFor({ state: "visible", timeout });
  }

  /**
   * Wait for block to disappear from the calendar (panel-scoped).
   */
  async waitForBlockGone(blockId: string, timeout = 5_000): Promise<void> {
    await this.getBlock(blockId).waitFor({ state: "hidden", timeout });
  }
}
