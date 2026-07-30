// cap: crm.adrian-embudo
// story-origin: vitalia-fase2-adrian-embudo
/**
 * LeadWorkspacePage.ts — POM for Lead Workspace (Resumen + Historial views).
 *
 * vitalia-fase2-adrian-embudo — T-E2E-1
 * Covers:
 *   SC-detalle  deep-link /resumen URL + EntitySubNavBar + Datos+Score blocks
 *   SC-deeplink refresh /historial renders
 *   F-6         lead page URL-owned 2 vistas (RN-16)
 *   RN-2        PHI firewall — no datos clínicos in timeline
 *
 * Routes:
 *   /{tenantId}/adrian/embudo/{leadId}/resumen
 *   /{tenantId}/adrian/embudo/{leadId}/historial
 *
 * downstream-regression-na: brand-local vitalia E2E POM
 * spec_anchor: 04-validators.yaml § poms_required
 */

import type { Page, Locator } from "@playwright/test";
import { expect } from "@playwright/test";

export class LeadWorkspacePage {
  readonly page: Page;
  readonly tenantId: string;
  readonly leadId: string;

  // ── EntitySubNavBar (workspace mode) ──────────────────────────────────────
  readonly entitySubNavBar: Locator;
  readonly backToEmbudoLink: Locator;
  readonly leadNameBreadcrumb: Locator;
  readonly resumenTab: Locator;
  readonly historialTab: Locator;

  // ── Resumen view ────────────────────────────────────────────────────────────
  readonly resumenView: Locator;
  readonly datosBlock: Locator;
  readonly scoreBlock: Locator;
  readonly scoreDonut: Locator;
  readonly autonomyBlock: Locator;
  readonly agentStatusBlock: Locator;
  readonly tomarControlButton: Locator;

  // ── Score glass-box breakdown ──────────────────────────────────────────────
  readonly scoreBreakdown: Locator;

  // ── Historial view ──────────────────────────────────────────────────────────
  readonly historialView: Locator;
  readonly timelineEvents: Locator;
  readonly inboxDeepLink: Locator;

  // ── States ─────────────────────────────────────────────────────────────────
  readonly loadingSkeleton: Locator;
  readonly errorState: Locator;
  readonly notFoundState: Locator;

  constructor(page: Page, tenantId: string, leadId: string) {
    this.page = page;
    this.tenantId = tenantId;
    this.leadId = leadId;

    // EntitySubNavBar (workspace mode — reuse from shell-organism)
    this.entitySubNavBar = page
      .locator(
        '[data-testid="entity-sub-nav-bar"], [aria-label*="Navegación de lead"]',
      )
      .first();
    this.backToEmbudoLink = page
      .locator('[aria-label*="Embudo"], [data-testid="back-to-embudo"]')
      .first();
    this.leadNameBreadcrumb = page
      .locator('[data-testid="lead-name-breadcrumb"]')
      .first();
    this.resumenTab = page
      .locator('[data-testid="entity-leaf-resumen"], [aria-label*="Resumen"], [data-testid="tab-resumen"]')
      .first();
    this.historialTab = page
      .locator('[data-testid="entity-leaf-historial"], [aria-label*="Historial"], [data-testid="tab-historial"]')
      .first();

    // Resumen view
    this.resumenView = page
      .locator('[data-testid="resumen-view"]')
      .first();
    this.datosBlock = page
      .locator('[data-testid="datos-block"], [aria-labelledby="bloque-datos"], section:has(h2:has-text("Datos del lead"))')
      .first();
    this.scoreBlock = page
      .locator('[data-testid="score-block"], [data-testid="score-breakdown"]')
      .first();
    // ResumenView uses ScoreBreakdown (not ScoreDonut); score-donut exists in LeadCard (kanban)
    this.scoreDonut = page
      .locator('[data-testid="score-donut"], [data-testid="score-breakdown"]')
      .first();
    this.autonomyBlock = page
      .locator(
        '[data-testid="autonomy-block"], [aria-label*="autonomía"]',
      )
      .first();
    this.agentStatusBlock = page
      .locator(
        '[data-testid="agent-status-block"], [aria-label*="Adrián"]',
      )
      .first();
    this.tomarControlButton = page
      .locator(
        '[data-testid="tomar-control"], button[aria-label*="Tomar control"]',
      )
      .first();

    // Score breakdown
    this.scoreBreakdown = page
      .locator('[data-testid="score-breakdown"]')
      .first();

    // Historial view
    this.historialView = page
      .locator('[data-testid="historial-view"]')
      .first();
    this.timelineEvents = page.locator('[data-testid^="timeline-event-"]');
    this.inboxDeepLink = page
      .locator(
        '[data-testid="inbox-deep-link"], a[aria-label*="Inbox"], a[href*="inbox"]',
      )
      .first();

    // States
    this.loadingSkeleton = page
      .locator('[data-testid="lead-workspace-skeleton"], [aria-busy="true"]')
      .first();
    this.errorState = page
      .locator('[data-testid="lead-workspace-error"]')
      .first();
    this.notFoundState = page
      .locator('[data-testid="lead-not-found"], [role="alert"]')
      .filter({ hasText: /no encontrado|404/i })
      .first();
  }

  // ── Navigation ──────────────────────────────────────────────────────────────

  async gotoResumen(): Promise<void> {
    await this.page.goto(
      `/${this.tenantId}/adrian/embudo/${this.leadId}/resumen`,
    );
    await this.page.waitForLoadState("networkidle");
  }

  async gotoHistorial(): Promise<void> {
    await this.page.goto(
      `/${this.tenantId}/adrian/embudo/${this.leadId}/historial`,
    );
    await this.page.waitForLoadState("networkidle");
  }

  // ── Tab navigation ──────────────────────────────────────────────────────────

  async clickResumenTab(): Promise<void> {
    await this.resumenTab.click();
    await this.page.waitForURL(`**/${this.leadId}/resumen`);
  }

  async clickHistorialTab(): Promise<void> {
    await this.historialTab.click();
    await this.page.waitForURL(`**/${this.leadId}/historial`);
  }

  async clickBackToEmbudo(): Promise<void> {
    await this.backToEmbudoLink.click();
    await this.page.waitForURL(`**/embudo**`);
  }

  // ── State assertions ────────────────────────────────────────────────────────

  async waitForResumenLoaded(): Promise<void> {
    await this.resumenView.waitFor({ state: "visible", timeout: 12_000 });
  }

  async waitForHistorialLoaded(): Promise<void> {
    await this.historialView.waitFor({ state: "visible", timeout: 12_000 });
  }

  async expectResumenView(): Promise<void> {
    await expect(this.page).toHaveURL(
      new RegExp(`/${this.leadId}/resumen`),
    );
    await expect(this.resumenView).toBeVisible();
  }

  async expectHistorialView(): Promise<void> {
    await expect(this.page).toHaveURL(
      new RegExp(`/${this.leadId}/historial`),
    );
    await expect(this.historialView).toBeVisible();
  }

  async expectEntitySubNavBarVisible(): Promise<void> {
    await expect(this.entitySubNavBar).toBeVisible();
  }

  async expectTablistRole(): Promise<void> {
    // EntitySubNavBar must have role=tablist (SC-10 a11y)
    const tablist = this.page.locator('[role="tablist"]').first();
    await expect(tablist).toBeVisible();
  }

  async expectDatosBlockVisible(): Promise<void> {
    await expect(this.datosBlock).toBeVisible();
  }

  async expectScoreDonutVisible(): Promise<void> {
    await expect(this.scoreDonut).toBeVisible();
  }

  async expectScoreNumberVisible(): Promise<void> {
    // Score must have a numeric value visible — not just color (a11y RN-2).
    // ScoreBreakdown renders the score as a large number span (text-2xl font-bold).
    const scoreNum = this.page.locator('[data-testid="score-breakdown"] span.tabular-nums').first();
    const scoreText = this.page.locator('[aria-label*="Puntuación"]').first();
    await expect(scoreNum.or(scoreText)).toBeVisible();
  }

  async expectNoPhiDataInHistorial(): Promise<void> {
    // RN-2 firewall: historial must NOT render clinical data
    await expect(this.historialView).not.toContainText(
      /diagnóstico|tratamiento|expediente|historia clínica/i,
    );
  }

  async expectNoPhiInUrl(): Promise<void> {
    const url = this.page.url();
    // leadId must be UUID format — no names in URL
    expect(url).not.toMatch(/nombre|paciente|dni|email/i);
    expect(url).toMatch(/[0-9a-f-]{36}|lead-\d+/i);
  }

  async expectInboxDeepLinkVisible(): Promise<void> {
    await expect(this.inboxDeepLink).toBeVisible();
  }
}
