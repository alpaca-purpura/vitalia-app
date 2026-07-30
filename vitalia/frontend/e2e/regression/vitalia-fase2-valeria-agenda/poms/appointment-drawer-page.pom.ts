/**
 * appointment-drawer-page.pom.ts — AppointmentDrawerPage POM
 *
 * Page Object Model for the appointment detail drawer (Sheet).
 * Encapsulates locators + actions for the right-side drawer.
 *
 * Methods per 04-validators.yaml test_construction_plan step 6:
 *   open, close, getAccordion, getCobrarSaldoButton, resize,
 *   getStaleBanner, getDisabledVerFichaTooltip
 *
 * Drawer spec: 440-640px width, localStorage persist, 5 acordeones
 * (Turno + Pago expanded default, resto collapsed).
 *
 * ARIA: role="dialog", aria-modal="true", aria-labelledby="appointment-drawer-title"
 *
 * No assertions in POM methods — only actions + locators.
 *
 * downstream-regression-na: brand-local vitalia E2E POM F2-S1
 *
 * @see 04-validators.yaml § poms_required[1]: AppointmentDrawerPage
 * @see 03-arch.md § 4 (drawer spec)
 * @see SC-1 drawer interaction flow
 */

import type { Page, Locator } from "@playwright/test";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type DrawerAccordion =
  | "turno"
  | "pago"
  | "notas"
  | "historial"
  | "acciones";

// ---------------------------------------------------------------------------
// AppointmentDrawerPage POM
// ---------------------------------------------------------------------------

export class AppointmentDrawerPage {
  readonly page: Page;

  // ── Drawer container ──────────────────────────────────────────────────────

  /** The Sheet/drawer panel */
  readonly panel: Locator;
  /** Drawer title heading */
  readonly title: Locator;
  /** Close button (X) */
  readonly closeButton: Locator;
  /** Resize handle */
  readonly resizeHandle: Locator;
  /** Stale banner ("Este turno fue actualizado...") */
  readonly staleBanner: Locator;
  /** "Ver ficha" link (disabled in Fase 2) */
  readonly verFichaLink: Locator;
  /** "Cobrar saldo" button inside Pago accordion */
  readonly cobrarSaldoButton: Locator;
  /** "Cancelar" action button */
  readonly cancelarButton: Locator;
  /** "No show" action button */
  readonly noShowButton: Locator;
  /** Confirmation dialog */
  readonly confirmDialog: Locator;
  /** Confirm action button inside dialog */
  readonly confirmButton: Locator;

  constructor(page: Page) {
    this.page = page;

    this.panel = page.locator('[role="dialog"][data-testid="appointment-drawer"]');
    this.title = page.locator('[data-testid="appointment-drawer-title"]');
    this.closeButton = page.locator('[data-testid="appointment-drawer-close"]');
    this.resizeHandle = page.locator('[data-testid="drawer-resize-handle"]');
    this.staleBanner = page.locator('[data-testid="drawer-stale-banner"]');
    this.verFichaLink = page.locator('[data-testid="drawer-ver-ficha"]');
    this.cobrarSaldoButton = page.locator(
      '[data-testid="drawer-cobrar-saldo-btn"]',
    );
    this.cancelarButton = page.locator('[data-testid="drawer-cancelar-btn"]');
    this.noShowButton = page.locator('[data-testid="drawer-no-show-btn"]');
    this.confirmDialog = page.locator('[data-testid="drawer-confirm-dialog"]');
    this.confirmButton = page.locator('[data-testid="drawer-confirm-ok-btn"]');
  }

  // ── Open / close ──────────────────────────────────────────────────────────

  /**
   * Wait for the drawer to open (become visible + accessible).
   * Panel must have role="dialog" + aria-modal="true".
   */
  async waitForOpen(): Promise<void> {
    await this.panel.waitFor({ state: "visible", timeout: 10_000 });
    await this.page.waitForSelector('[aria-modal="true"]', { timeout: 5_000 });
  }

  /**
   * Close the drawer by clicking the X button.
   * Waits for drawer to become hidden.
   */
  async close(): Promise<void> {
    await this.closeButton.click();
    await this.panel.waitFor({ state: "hidden", timeout: 5_000 });
  }

  /**
   * Close the drawer by pressing Escape.
   * Per SC-10 spec: Esc closes drawer + returns focus to slot trigger.
   */
  async closeWithEscape(): Promise<void> {
    await this.page.keyboard.press("Escape");
    await this.panel.waitFor({ state: "hidden", timeout: 5_000 });
  }

  // ── Patient / appointment info ────────────────────────────────────────────

  /**
   * Get the patient name as rendered (PHI-masked, e.g. "P. Hernández").
   */
  async getPatientName(): Promise<string> {
    const el = this.page.locator('[data-testid="drawer-patient-name"]');
    return (await el.textContent()) ?? "";
  }

  /**
   * Get the payment status badge text.
   */
  async getPaymentStatus(): Promise<string> {
    const el = this.page.locator('[data-testid="drawer-payment-status"]');
    return (await el.textContent()) ?? "";
  }

  // ── Accordion controls ────────────────────────────────────────────────────

  /**
   * Get an accordion section by its slug.
   */
  getAccordion(section: DrawerAccordion): Locator {
    return this.page.locator(
      `[data-testid="drawer-accordion-${section}"]`,
    );
  }

  /**
   * Expand a collapsed accordion section by clicking its trigger.
   */
  async expandSection(section: DrawerAccordion): Promise<void> {
    const accordion = this.getAccordion(section);
    const trigger = accordion.locator('[data-testid="accordion-trigger"]');
    const content = accordion.locator('[data-testid="accordion-content"]');
    const isExpanded = await content.isVisible();
    if (!isExpanded) {
      await trigger.click();
      await content.waitFor({ state: "visible", timeout: 3_000 });
    }
  }

  // ── Cobrar saldo ──────────────────────────────────────────────────────────

  /**
   * Click the "Cobrar saldo" button to open the CobrarSaldoSubform.
   * The Pago accordion must be expanded first.
   */
  async clickCobrarSaldo(): Promise<void> {
    await this.cobrarSaldoButton.click();
  }

  // ── Actions (Cancelar / No show) ──────────────────────────────────────────

  /**
   * Click the "Cancelar" button and wait for the confirmation dialog.
   */
  async clickCancelar(): Promise<void> {
    await this.cancelarButton.click();
    await this.confirmDialog.waitFor({ state: "visible", timeout: 3_000 });
  }

  /**
   * Click the "No show" button and wait for the confirmation dialog.
   */
  async clickNoShow(): Promise<void> {
    await this.noShowButton.click();
    await this.confirmDialog.waitFor({ state: "visible", timeout: 3_000 });
  }

  /**
   * Confirm the current action dialog.
   */
  async confirmDialog_confirm(): Promise<void> {
    await this.confirmButton.click();
    await this.confirmDialog.waitFor({ state: "hidden", timeout: 3_000 });
  }

  // ── Stale banner ──────────────────────────────────────────────────────────

  /**
   * Get the stale data banner (visible when another user modified the slot).
   */
  getStaleBanner(): Locator {
    return this.staleBanner;
  }

  /**
   * Click "Recargar" inside the stale banner.
   */
  async clickRecargarInBanner(): Promise<void> {
    await this.staleBanner
      .locator('[data-testid="drawer-stale-reload-btn"]')
      .click();
  }

  // ── Ver ficha (disabled Fase 2) ────────────────────────────────────────────

  /**
   * Get the "Ver ficha" link (disabled + shows tooltip "Próximamente").
   */
  getDisabledVerFichaTooltip(): Locator {
    return this.page.locator('[data-testid="drawer-ver-ficha-tooltip"]');
  }

  // ── Resize ────────────────────────────────────────────────────────────────

  /**
   * Drag the resize handle by deltaX pixels.
   * Positive = expand, negative = shrink.
   */
  async resize(deltaX: number): Promise<void> {
    const handleBounds = await this.resizeHandle.boundingBox();
    if (!handleBounds) return;
    const startX = handleBounds.x + handleBounds.width / 2;
    const startY = handleBounds.y + handleBounds.height / 2;
    await this.page.mouse.move(startX, startY);
    await this.page.mouse.down();
    await this.page.mouse.move(startX + deltaX, startY, { steps: 10 });
    await this.page.mouse.up();
  }

  /**
   * Get the current width of the drawer panel in pixels.
   */
  async getWidth(): Promise<number> {
    const box = await this.panel.boundingBox();
    return box?.width ?? 0;
  }
}
