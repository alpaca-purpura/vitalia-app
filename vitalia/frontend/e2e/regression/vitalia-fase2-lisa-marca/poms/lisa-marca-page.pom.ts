/**
 * lisa-marca-page.pom.ts — LisaMarcaPage POM
 *
 * Top-level shell page object for the lisa/marca sub-tab.
 * Provides navigation helpers + SubSubTabsBar interaction.
 *
 * N3-static routing: /{tenantId}/lisa/marca/{identidad|voz-y-tono|presencia}
 * SubSubTabsBar data-testids: shell-subsubtabs-bar + individual tab buttons.
 *
 * No assertions in POM methods (assertions live in spec files).
 *
 * downstream-regression-na: brand-local vitalia e2e POM F2-S7
 *
 * @see 04-validators.yaml § test_construction_plan step 5
 */

import { expect } from "@playwright/test";
import type { Page, Locator } from "@playwright/test";

export class LisaMarcaPage {
  readonly page: Page;
  readonly tenantId: string;

  // ---------------------------------------------------------------------------
  // Shell layout locators
  // ---------------------------------------------------------------------------

  /** SubSubTabsBar container (N3-static navigation header) */
  readonly subsubtabsBar: Locator;

  /** Individual sub-sub-tab navigation links */
  readonly tabIdentidad: Locator;
  readonly tabVozYTono: Locator;
  readonly tabPresencia: Locator;

  // ---------------------------------------------------------------------------
  // Shell organism locators
  // ---------------------------------------------------------------------------

  /** Main content area of the marca sub-tab */
  readonly marcaContent: Locator;

  /** Autosave badge indicator (shows "Guardando..." / "Guardado" / error) */
  readonly autosaveBadge: Locator;

  /** Loading skeleton (shown while initial data loads) */
  readonly loadingSkeleton: Locator;

  /** Error boundary fallback */
  readonly errorBoundaryFallback: Locator;

  // ---------------------------------------------------------------------------
  // Constructor
  // ---------------------------------------------------------------------------

  constructor(page: Page, tenantId: string) {
    this.page = page;
    this.tenantId = tenantId;

    // Phantom-testid fix (estabilizar-harness-e2e-lisa-marca): los testids reales
    // del componente SubSubTabsBar son `sub-sub-tabs-bar` + `sub-sub-tab-{id}` (con
    // aria-current="page" en el activo). Los POMs apuntaban a `shell-subsubtabs-bar`
    // + `subsubtab-link-{id}` (fantasmas que el mock enmascaraba).
    this.subsubtabsBar = page.locator('[data-testid="sub-sub-tabs-bar"]');

    this.tabIdentidad = page.locator('[data-testid="sub-sub-tab-identidad"]');
    this.tabVozYTono = page.locator('[data-testid="sub-sub-tab-voz-y-tono"]');
    this.tabPresencia = page.locator('[data-testid="sub-sub-tab-presencia"]');

    // Phantom-testid fix (estabilizar-harness-e2e-lisa-marca): el page NUNCA renderizó
    // `lisa-marca-content` (data-testid fantasma que el mock enmascaraba). El contenido
    // cargado es el root del subsubtab activo. Unión de los 3 roots reales (web-first).
    this.marcaContent = page.locator(
      '[data-testid="identidad-view"], [data-testid="voz-tono-section-root"], [data-testid="presencia-view"]',
    );

    this.autosaveBadge = page.locator('[data-testid="autosave-badge"]');

    this.loadingSkeleton = page.locator(
      '[data-testid="lisa-marca-loading-skeleton"]',
    );

    this.errorBoundaryFallback = page.locator(
      '[data-testid="error-boundary-fallback"]',
    );
  }

  // ---------------------------------------------------------------------------
  // Navigation helpers
  // ---------------------------------------------------------------------------

  /**
   * Navigate directly to a sub-sub-tab route.
   * Waits for domcontentloaded.
   */
  async navigateToSubsubtab(
    subsubtab: "identidad" | "voz-y-tono" | "presencia",
  ): Promise<void> {
    await this.page.goto(`/${this.tenantId}/lisa/marca/${subsubtab}`);
    await this.page.waitForLoadState("domcontentloaded");
  }

  /**
   * Navigate to identidad sub-sub-tab via SubSubTabsBar click.
   */
  async clickTabIdentidad(): Promise<void> {
    await this.tabIdentidad.click();
    await this.page.waitForLoadState("domcontentloaded");
  }

  /**
   * Navigate to voz-y-tono sub-sub-tab via SubSubTabsBar click.
   */
  async clickTabVozYTono(): Promise<void> {
    await this.tabVozYTono.click();
    await this.page.waitForLoadState("domcontentloaded");
  }

  /**
   * Navigate to presencia sub-sub-tab via SubSubTabsBar click.
   */
  async clickTabPresencia(): Promise<void> {
    await this.tabPresencia.click();
    await this.page.waitForLoadState("domcontentloaded");
  }

  // ---------------------------------------------------------------------------
  // State inspection helpers
  // ---------------------------------------------------------------------------

  /**
   * Returns the currently active sub-sub-tab slug from SubSubTabsBar.
   * Reads aria-current="page" attribute (ONCE-READ — diagnostics only).
   *
   * ⚠️ Para aserciones determinísticas usar `waitForActiveSubsubtab`.
   */
  async getActiveSubsubtab(): Promise<string | null> {
    const activeTab = this.subsubtabsBar.locator('[aria-current="page"]');
    const count = await activeTab.count();
    if (count === 0) return null;
    // El id vive en el testid `sub-sub-tab-{id}` (no en un `data-subsubtab`).
    const testid = await activeTab.first().getAttribute("data-testid");
    return testid?.replace(/^sub-sub-tab-/, "") ?? null;
  }

  /**
   * Web-first wait: asserts the SubSubTabsBar marks the given sub-sub-tab as
   * active (`data-subsubtab=<slug>` with `aria-current="page"`), re-checking
   * until met or timeout. Reemplaza el once-read de `getActiveSubsubtab` en las
   * aserciones (determinismo, RN-3).
   */
  async waitForActiveSubsubtab(
    subsubtab: "identidad" | "voz-y-tono" | "presencia",
    timeoutMs = 15_000,
  ): Promise<void> {
    const activeTab = this.subsubtabsBar.locator(
      `[data-testid="sub-sub-tab-${subsubtab}"][aria-current="page"]`,
    );
    await expect(activeTab).toBeVisible({ timeout: timeoutMs });
  }

  /**
   * Returns the autosave badge text content.
   * Null if badge not visible.
   */
  async getAutosaveBadgeText(): Promise<string | null> {
    const visible = await this.autosaveBadge.isVisible();
    if (!visible) return null;
    return this.autosaveBadge.textContent();
  }

  /**
   * Waits until the page content is fully loaded (skeleton gone, content visible).
   * Timeout defaults to 15s (aligned with playwright.config.ts actionTimeout).
   */
  async waitForLoaded(timeoutMs: number = 15_000): Promise<void> {
    await this.loadingSkeleton.waitFor({
      state: "hidden",
      timeout: timeoutMs,
    });
    await this.marcaContent.waitFor({
      state: "visible",
      timeout: timeoutMs,
    });
  }

  /**
   * Waits until autosave badge shows "Guardado" (success state).
   */
  async waitForAutosaveSuccess(timeoutMs: number = 10_000): Promise<void> {
    await this.page
      .locator('[data-testid="autosave-badge"][data-state="saved"]')
      .waitFor({ state: "visible", timeout: timeoutMs });
  }

  /**
   * Waits until autosave badge shows saving state.
   */
  async waitForAutosaveSaving(timeoutMs: number = 10_000): Promise<void> {
    await this.page
      .locator('[data-testid="autosave-badge"][data-state="saving"]')
      .waitFor({ state: "visible", timeout: timeoutMs });
  }

  /**
   * Waits until autosave badge shows error state.
   */
  async waitForAutosaveError(timeoutMs: number = 10_000): Promise<void> {
    await this.page
      .locator('[data-testid="autosave-badge"][data-state="error"]')
      .waitFor({ state: "visible", timeout: timeoutMs });
  }

  /**
   * Checks whether the error boundary fallback is displayed.
   */
  async isErrorBoundaryVisible(): Promise<boolean> {
    return this.errorBoundaryFallback.isVisible();
  }
}
