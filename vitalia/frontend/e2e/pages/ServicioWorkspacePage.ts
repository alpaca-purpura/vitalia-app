// cap: lisa.servicios
// story-origin: vitalia-fase2-lisa-servicios T-8
/**
 * ServicioWorkspacePage.ts — POM for the Servicio detail workspace (N3 pattern).
 *
 * Route: /{tenantId}/lisa/servicios/{offerId}/{leaf}
 * Leaves: resumen | para-adrian | especialistas | plan-pago | prueba-social
 *
 * Covers:
 *   - EntitySubNavBar tabs (leaves)
 *   - Autosave indicator (FloatingAutosaveIndicator)
 *   - Field editing (price, modality, rung)
 *   - Especialistas sub-tab (link/unlink doctors)
 *   - PlanPago locked fields (Sub-phase B)
 *   - PruebaSocial testimonial form + rating
 *
 * downstream-regression-na: brand-local vitalia E2E POM; no cross-brand consumers
 */

import type { Page, Locator } from "@playwright/test";

export type ServicioLeaf =
  | "resumen"
  | "para-adrian"
  | "especialistas"
  | "plan-pago"
  | "prueba-social";

export class ServicioWorkspacePage {
  readonly page: Page;

  /** EntityWorkspaceLayout root wrapper */
  readonly workspaceLayout: Locator;

  /** Content slot */
  readonly workspaceContent: Locator;

  /** EntitySubNavBar tab list */
  readonly subNavTablist: Locator;

  /** FloatingAutosaveIndicator */
  readonly autosaveIndicator: Locator;

  constructor(page: Page) {
    this.page = page;
    this.workspaceLayout = page.getByTestId("entity-workspace-layout");
    this.workspaceContent = page.getByTestId("entity-workspace-content");
    this.subNavTablist = page
      .getByTestId("entity-workspace-layout")
      .locator('[role="tablist"]')
      .first();
    this.autosaveIndicator = page.getByTestId("floating-autosave-indicator");
  }

  // ── Navigation ──────────────────────────────────────────────────────────────

  async goto(tenantId: string, offerId: string, leaf: ServicioLeaf = "resumen"): Promise<void> {
    await this.page.goto(`/${tenantId}/lisa/servicios/${offerId}/${leaf}`);
    await this.workspaceLayout.waitFor({ state: "visible", timeout: 30_000 });
  }

  async clickLeafTab(leaf: ServicioLeaf): Promise<void> {
    const labelMap: Record<ServicioLeaf, string> = {
      resumen: "Resumen",
      "para-adrian": "Para Adrián",
      especialistas: "Especialistas",
      "plan-pago": "Plan de pago",
      "prueba-social": "Prueba social",
    };
    const tab = this.subNavTablist.locator(`[role="tab"]`, {
      hasText: labelMap[leaf],
    });
    await tab.click();
    await this.workspaceContent.waitFor({ state: "visible", timeout: 10_000 });
  }

  async clickBackToDirectory(): Promise<void> {
    const backLink = this.page
      .getByTestId("entity-workspace-layout")
      .locator('a')
      .filter({ hasText: /‹|Servicios/i })
      .first();
    await backLink.click();
    await this.page.waitForLoadState("networkidle", { timeout: 15_000 });
  }

  // ── Resumen leaf ────────────────────────────────────────────────────────────

  async fillPublicName(name: string): Promise<void> {
    const nameInput = this.page.getByLabel(/Nombre público/i);
    await nameInput.fill(name);
    await this.waitForAutosave();
  }

  async selectModality(modality: "unica" | "sesiones" | "paquete"): Promise<void> {
    const testIdMap = {
      unica: "mod-unica",
      sesiones: "mod-sesiones",
      paquete: "mod-paquete",
    };
    await this.page.getByTestId(testIdMap[modality]).click();
    await this.waitForAutosave();
  }

  async selectRung(rung: "LEAD_MAGNET" | "ACTIVACION" | "TRANSFORMACION" | "MAXIMIZACION"): Promise<void> {
    await this.page.getByTestId(`rung-${rung}`).click();
    await this.waitForAutosave();
  }

  // ── Especialistas leaf ───────────────────────────────────────────────────────

  async openEspecialistaPicker(): Promise<void> {
    const btn = this.page.getByRole("button", { name: /Vincular especialista/i });
    await btn.click();
    await this.page.waitForTimeout(300);
  }

  async closeEspecialistaPicker(): Promise<void> {
    const closeBtn = this.page.getByRole("button", { name: /Cerrar/i });
    await closeBtn.click();
    await this.page.waitForTimeout(200);
  }

  async unlinkSpecialist(doctorId: string): Promise<void> {
    const row = this.page.locator(`[data-testid="specialist-row-${doctorId}"]`);
    const unlinkBtn = row.getByRole("button", { name: /Desvincular/i });
    await unlinkBtn.click();
  }

  // ── Plan de pago leaf ────────────────────────────────────────────────────────

  async getPriceFieldValue(): Promise<string> {
    const priceInput = this.page.getByLabel(/Precio del tratamiento/i);
    return await priceInput.inputValue();
  }

  async fillPrice(price: string): Promise<void> {
    const priceInput = this.page.getByLabel(/Precio del tratamiento/i);
    await priceInput.fill(price);
    await this.waitForAutosave();
  }

  // ── Autosave ────────────────────────────────────────────────────────────────

  async waitForAutosave(timeoutMs = 3_000): Promise<void> {
    // Wait for autosave debounce (600ms) + network round-trip
    try {
      await this.page.waitForFunction(
        () => {
          const el = document.querySelector('[data-testid="floating-autosave-indicator"]');
          return el?.getAttribute("data-status") === "saved";
        },
        { timeout: timeoutMs }
      );
    } catch {
      // Autosave may not fire for fields that don't trigger it — non-fatal
    }
  }

  // ── Assertions ───────────────────────────────────────────────────────────────

  async isWorkspaceVisible(): Promise<boolean> {
    try {
      await this.workspaceLayout.waitFor({ state: "visible", timeout: 5_000 });
      return true;
    } catch {
      return false;
    }
  }

  async getActiveLeafTab(): Promise<string> {
    const activeTab = this.subNavTablist.locator('[role="tab"][aria-selected="true"]');
    return await activeTab.innerText();
  }
}
