// cap: lisa.servicios
// story-origin: vitalia-fase2-lisa-servicios T-8
/**
 * EscaleraPage.ts — POM for Lisa → Servicios → Escalera sub-tab.
 *
 * Route: /{tenantId}/lisa/servicios/escalera
 *
 * The Escalera view groups services into rung columns (LEAD_MAGNET, ACTIVACION,
 * TRANSFORMACION, MAXIMIZACION) and allows drag-and-drop reordering between rungs
 * via DnD Kit (keyboard a11y: Space to grab, arrows to move, Space/Enter to drop).
 *
 * downstream-regression-na: brand-local vitalia E2E POM; no cross-brand consumers
 */

import type { Page, Locator } from "@playwright/test";

export type RungSlug = "LEAD_MAGNET" | "ACTIVACION" | "TRANSFORMACION" | "MAXIMIZACION";

const RUNG_LABELS: Record<RungSlug, string> = {
  LEAD_MAGNET: "Lead Magnet",
  ACTIVACION: "Activación",
  TRANSFORMACION: "Transformación",
  MAXIMIZACION: "Maximización",
};

export class EscaleraPage {
  readonly page: Page;

  /** Root Escalera board container */
  readonly escaleraRoot: Locator;

  constructor(page: Page) {
    this.page = page;
    this.escaleraRoot = page.getByTestId("escalera-board");
  }

  // ── Navigation ──────────────────────────────────────────────────────────────

  async goto(tenantId: string): Promise<void> {
    await this.page.goto(`/${tenantId}/lisa/servicios/escalera`);
    await this.escaleraRoot.waitFor({ state: "visible", timeout: 30_000 });
  }

  // ── Column helpers ──────────────────────────────────────────────────────────

  /**
   * Get the column container for a given rung.
   */
  rungColumn(rung: RungSlug): Locator {
    return this.page.getByTestId(`escalera-column-${rung}`);
  }

  /**
   * Get service cards inside a rung column.
   */
  rungCards(rung: RungSlug): Locator {
    return this.rungColumn(rung).locator('[data-testid^="escalera-card-"]');
  }

  async getRungCardCount(rung: RungSlug): Promise<number> {
    return await this.rungCards(rung).count();
  }

  async getRungLabel(rung: RungSlug): Promise<string> {
    const header = this.rungColumn(rung).locator("h3, h2, [data-testid$='-label']").first();
    return await header.innerText();
  }

  // ── Drag helpers (visual — for goldens; real drag is brittle in Playwright) ─

  /**
   * Assert that a service name appears in a specific rung column.
   */
  async assertServiceInRung(serviceName: string, rung: RungSlug): Promise<void> {
    const col = this.rungColumn(rung);
    await col.locator(`text=${serviceName}`).waitFor({ state: "visible", timeout: 5_000 });
  }

  /**
   * Keyboard a11y: Space to pick up a card, Arrow key to move column, Space to drop.
   * Uses the DnD Kit keyboard sensor pattern.
   */
  async moveCardKeyboard(
    serviceName: string,
    direction: "ArrowLeft" | "ArrowRight"
  ): Promise<void> {
    // Find the draggable card
    const card = this.escaleraRoot.locator('[data-testid^="escalera-card-"]', {
      hasText: serviceName,
    });
    await card.focus();
    // Space to initiate drag
    await this.page.keyboard.press("Space");
    await this.page.waitForTimeout(100);
    // Arrow to change rung
    await this.page.keyboard.press(direction);
    await this.page.waitForTimeout(100);
    // Space to drop
    await this.page.keyboard.press("Space");
    await this.page.waitForTimeout(500); // Allow mutation to complete
  }

  // ── Empty state ──────────────────────────────────────────────────────────────

  async isRungEmpty(rung: RungSlug): Promise<boolean> {
    const count = await this.getRungCardCount(rung);
    return count === 0;
  }

  async getRungLabelText(rung: RungSlug): Promise<string> {
    return RUNG_LABELS[rung];
  }

  // ── Assertions ───────────────────────────────────────────────────────────────

  async isVisible(): Promise<boolean> {
    try {
      await this.escaleraRoot.waitFor({ state: "visible", timeout: 5_000 });
      return true;
    } catch {
      return false;
    }
  }

  async waitForBoard(): Promise<void> {
    await this.escaleraRoot.waitFor({ state: "visible", timeout: 20_000 });
    // Wait for at least one column to render
    await this.page.waitForFunction(
      () => document.querySelectorAll('[data-testid^="escalera-column-"]').length >= 4,
      { timeout: 15_000 }
    );
  }
}
