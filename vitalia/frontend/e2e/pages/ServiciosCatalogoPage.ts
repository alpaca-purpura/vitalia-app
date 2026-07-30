// cap: lisa.servicios
// story-origin: vitalia-fase2-lisa-servicios T-8
/**
 * ServiciosCatalogoPage.ts — POM for Lisa → Servicios directory (N3 pattern).
 *
 * Route: /{tenantId}/lisa/servicios
 *
 * Covers:
 *   - Catálogo grid (EntityInfoCard per servicio)
 *   - Escalera tab (Rung grouping)
 *   - Filter bar: search + status toggle
 *   - "Nuevo servicio" CTA → BibliotecaPicker modal
 *   - Empty state for each rung
 *
 * downstream-regression-na: brand-local vitalia E2E POM; no cross-brand consumers
 */

import type { Page, Locator } from "@playwright/test";

export class ServiciosCatalogoPage {
  readonly page: Page;

  /** Root container for the Servicios directory */
  readonly catalogoRoot: Locator;

  /** "Nuevo servicio" button that opens BibliotecaPicker */
  readonly nuevoServicioBtn: Locator;

  /** Search input in the filter bar */
  readonly searchInput: Locator;

  /** Status filter toggle (Activos / Todos) */
  readonly statusFilter: Locator;

  /** Grid of EntityInfoCard items */
  readonly servicioCards: Locator;

  /** Empty state placeholder */
  readonly emptyState: Locator;

  /** BibliotecaPicker modal (appears after nuevoServicioBtn click) */
  readonly bibliotecaPicker: Locator;

  constructor(page: Page) {
    this.page = page;
    this.catalogoRoot = page.getByTestId("servicios-catalogo");
    this.nuevoServicioBtn = page.getByRole("button", { name: /Nuevo servicio/i });
    this.searchInput = page.getByRole("searchbox");
    this.statusFilter = page.getByRole("button", { name: /Activos|Todos/i });
    this.servicioCards = page.locator('[data-testid^="entity-info-card-"]');
    this.emptyState = page.getByTestId("servicios-empty");
    this.bibliotecaPicker = page.getByRole("dialog", { name: /Nuevo servicio/i });
  }

  // ── Navigation ──────────────────────────────────────────────────────────────

  async goto(tenantId: string): Promise<void> {
    await this.page.goto(`/${tenantId}/lisa/servicios`);
    await this.page.waitForLoadState("networkidle", { timeout: 30_000 });
  }

  // ── Catálogo helpers ────────────────────────────────────────────────────────

  async getServicioCount(): Promise<number> {
    return await this.servicioCards.count();
  }

  async clickServicio(publicName: string): Promise<void> {
    const card = this.page.locator('[data-testid^="entity-info-card-"]', {
      hasText: publicName,
    });
    await card.click();
    await this.page.waitForLoadState("networkidle", { timeout: 20_000 });
  }

  async searchForServicio(query: string): Promise<void> {
    await this.searchInput.fill(query);
    // Debounce: wait for React Query to re-fetch
    await this.page.waitForTimeout(400);
    await this.page.waitForLoadState("networkidle", { timeout: 10_000 });
  }

  // ── Nuevo servicio flow ─────────────────────────────────────────────────────

  async openNuevoServicio(): Promise<void> {
    await this.nuevoServicioBtn.click();
    await this.bibliotecaPicker.waitFor({ state: "visible", timeout: 10_000 });
  }

  async selectLibraryMode(): Promise<void> {
    const tab = this.page.getByRole("button", { name: /Buscar en la biblioteca/i });
    await tab.click();
  }

  async selectCustomMode(): Promise<void> {
    const tab = this.page.getByRole("button", { name: /Personalizado/i });
    await tab.click();
  }

  async fillCustomServicioName(name: string): Promise<void> {
    const nameInput = this.page.getByLabel("Nombre del servicio");
    await nameInput.fill(name);
  }

  async submitCustomServicio(): Promise<void> {
    const submitBtn = this.page.getByRole("button", { name: /Crear y configurar/i });
    await submitBtn.click();
  }

  // ── Escalera tab ────────────────────────────────────────────────────────────

  async clickEscaleraTab(): Promise<void> {
    const tab = this.page.getByRole("tab", { name: /Escalera/i });
    await tab.click();
    await this.page.waitForLoadState("networkidle", { timeout: 10_000 });
  }

  // ── Assertions ──────────────────────────────────────────────────────────────

  async isVisible(): Promise<boolean> {
    try {
      await this.catalogoRoot.waitFor({ state: "visible", timeout: 5_000 });
      return true;
    } catch {
      return false;
    }
  }

  async waitForCards(): Promise<void> {
    await this.page.waitForFunction(
      () => document.querySelectorAll('[data-testid^="entity-info-card-"]').length > 0,
      { timeout: 15_000 }
    );
  }
}
