// cap: adrian.inbox
/**
 * AdrianInboxPage — POM for Adrián Inbox (3-pane shell + 3-modos + nudge + Valeria-collapse).
 *
 * vitalia-fase2-adrian-inbox — T-6
 * Extends: F1-S10 vitalia-fase1-empty-states (legacy placeholder locators preserved for compat)
 *
 * Covers SC-1..SC-10 from 01-spec.md:
 *   SC-1  happy: Decide mode + tool-calls + Valeria reacciona
 *   SC-2  Consulta: human edits draft before send
 *   SC-3  PHI firewall redirect (ComplianceService blocks clinical data on WhatsApp)
 *   SC-4  Concurrent mode-change / takeover (OCC 409)
 *   SC-5  "Modo conversación" collapses Valeria to full canvas
 *   SC-6  Nudge to stalled active conversation
 *   SC-7  Empty state (no convs / no filter results)
 *   SC-8  Network failure loading thread
 *   SC-9  Accessibility (tab order, aria-current/selected, Esc)
 *   SC-10 Cross-tenant blocked + Spanish neutro
 *
 * Route: /{tenantId}/adrian/inbox  (shell-organism RSC · ADR-vitalia-004)
 *
 * downstream-regression-na: brand-local vitalia e2e POM; no cross-brand consumers
 */

import type { Page, Locator } from "@playwright/test";
import { expect } from "@playwright/test";

export class AdrianInboxPage {
  readonly page: Page;
  readonly tenantId: string;

  // ── Main 3-pane layout ────────────────────────────────────────────────────
  readonly conversationList: Locator;
  readonly threadSection: Locator;
  readonly contactSidebar: Locator;
  readonly activityStream: Locator;

  // ── Conversation list controls ────────────────────────────────────────────
  readonly searchInput: Locator;
  readonly filterChips: Locator;

  // ── 3-modos toggle (SegmentedControl — NOT Shadcn Tabs) ───────────────────
  readonly modeToggle: Locator;
  readonly modeDecideOption: Locator;     // 🤖 Adrián decide
  readonly modeConsultaOption: Locator;   // 🤝 Adrián consulta
  readonly modeManualOption: Locator;     // 👤 Yo escribo

  // ── Takeover UX ───────────────────────────────────────────────────────────
  readonly takeControlButton: Locator;
  readonly returnControlButton: Locator;
  readonly takeoverBanner: Locator;
  readonly autonomyBanner: Locator;

  // ── Consulta draft controls ───────────────────────────────────────────────
  readonly consultaBanner: Locator;
  readonly approveButton: Locator;
  readonly editDraftButton: Locator;
  readonly discardDraftButton: Locator;

  // ── Agent state indicators ────────────────────────────────────────────────
  readonly typingIndicator: Locator;
  readonly agentFailedBanner: Locator;

  // ── Full-canvas toggle (RN-11/RN-12) ─────────────────────────────────────
  readonly conversationModeButton: Locator;

  // ── Composer ──────────────────────────────────────────────────────────────
  readonly composerInput: Locator;
  readonly sendButton: Locator;

  // ── 2-modos amendment (★ 2026-06-04): composer dock + pause modal + sidebar ──
  /** Dock al pie del thread (estado pausa + botón Pausar + composer). */
  readonly composerDock: Locator;
  /** Textarea real dentro del dock (MessageInput no tiene data-testid). */
  readonly dockTextarea: Locator;
  readonly pauseAdrianButton: Locator;
  readonly pauseModal: Locator;
  readonly pauseModal60: Locator;
  readonly pauseModalPermanent: Locator;
  readonly pauseModalCancel: Locator;
  /** ContactSidebar — leads visibles + servicio de interés + cerrar. */
  readonly contactServiceInterest: Locator;
  readonly contactSidebarClose: Locator;
  readonly threadHeaderPatientName: Locator;

  // ── Nudge (RN-13) ─────────────────────────────────────────────────────────
  readonly nudgeButton: Locator;
  readonly nudgeConfirmButton: Locator;
  readonly nudgeToast: Locator;

  // ── Tool-calls / glass-box (RN-6) ─────────────────────────────────────────
  readonly toolCallCards: Locator;

  // ── Empty / error states ──────────────────────────────────────────────────
  readonly emptyState: Locator;
  readonly errorBanner: Locator;
  readonly retryButton: Locator;

  // ── Legacy compat (F1-S10 placeholder — preserved for existing specs) ─────
  /** @deprecated use modeToggle for 3-modos */
  readonly globalModeToggle: Locator;
  /** @deprecated use modeDecideOption chip instead */
  readonly adrianModeChip: Locator;
  readonly closeSidebarButton: Locator;
  readonly sidebarContainer: Locator;

  constructor(page: Page, tenantId: string) {
    this.page = page;
    this.tenantId = tenantId;

    // 3-pane layout
    this.conversationList = page.locator('[role="listbox"][aria-label="Conversaciones"]');
    this.threadSection = page.locator('section[aria-label*="Conversación con"]');
    this.contactSidebar = page.locator("[data-sidebar]").locator("aside").last();
    this.activityStream = page.locator('[data-testid="agent-activity-stream"]');

    // Conversation list controls
    this.searchInput = page.locator('[data-testid="inbox-search"], [placeholder*="Buscar"]').first();
    this.filterChips = page.locator('[data-testid="inbox-filter-chips"]');

    // 3-modos toggle (spec: SegmentedControl, NOT Shadcn Tabs — ADR-vitalia-004 §1).
    // Real DOM: ModeToggle = role="radiogroup" data-testid="segmented-control-3-modes"
    // with options data-testid="segment-{adrian-decide|adrian-consulta|yo-escribo}".
    this.modeToggle = page.locator('[data-testid="segmented-control-3-modes"]');
    this.modeDecideOption = page.locator('[data-testid="segment-adrian-decide"]').first();
    this.modeConsultaOption = page.locator('[data-testid="segment-adrian-consulta"]').first();
    this.modeManualOption = page.locator('[data-testid="segment-yo-escribo"]').first();

    // Takeover UX
    this.takeControlButton = page.locator(
      '[aria-label="Tomar el control de esta conversación · Adrián pausará aquí"], [data-testid="take-control-button"]',
    ).first();
    this.returnControlButton = page.locator(
      '[aria-label="Devolver el control a Adrián en esta conversación"], [data-testid="return-control-button"]',
    ).first();
    this.takeoverBanner = page
      .locator('[role="alert"], [role="status"]')
      .filter({ hasText: /Adrián|Devolver/ });
    this.autonomyBanner = page.locator('[data-testid="autonomy-banner"]');

    // Consulta draft controls
    this.consultaBanner = page.locator('[data-testid="consulta-banner"]').first();
    this.approveButton = page.locator('button[data-testid="approve-draft"]').first();
    this.editDraftButton = page.locator('button[data-testid="edit-draft"]').first();
    this.discardDraftButton = page.locator('button[data-testid="discard-draft"]').first();

    // Agent state
    this.typingIndicator = page.locator('[data-testid="typing-indicator"]');
    this.agentFailedBanner = page.locator('[data-testid="agent-failed-banner"]');

    // Full-canvas toggle (RN-12)
    this.conversationModeButton = page.locator(
      '[data-testid="conversation-mode-button"], [aria-label*="Modo conversación"]',
    ).first();

    // Composer
    this.composerInput = page.locator(
      '[data-testid="composer-input"], textarea[aria-label*="Mensaje"], [placeholder*="Escribir"]',
    ).first();
    this.sendButton = page.locator(
      '[data-testid="composer-send"], button[aria-label*="Enviar"]',
    ).first();

    // Nudge (RN-13)
    this.nudgeButton = page.locator(
      '[data-testid="nudge-button"], button[aria-label*="empujón"], button[aria-label*="Dar empujón"]',
    ).first();
    this.nudgeConfirmButton = page.locator(
      '[data-testid="nudge-confirm"], button[aria-label*="Confirmar empujón"]',
    ).first();
    this.nudgeToast = page.locator('[role="status"]').filter({ hasText: /Empujón enviado/ }).first();

    // 2-modos amendment: composer dock + pause modal + sidebar (real DOM testids)
    this.composerDock = page.locator('[data-testid="thread-composer-dock"]').first();
    this.dockTextarea = this.composerDock.locator("textarea").first();
    this.pauseAdrianButton = page.locator('[data-testid="pause-adrian-button"]').first();
    this.pauseModal = page.locator('[data-testid="pause-adrian-modal"]');
    this.pauseModal60 = page.locator('[data-testid="pause-modal-60"]');
    this.pauseModalPermanent = page.locator('[data-testid="pause-modal-permanent"]');
    this.pauseModalCancel = page.locator('[data-testid="pause-modal-cancel"]');
    this.contactServiceInterest = page.locator('[data-testid="contact-service-interest"]').first();
    this.contactSidebarClose = page.locator('[data-testid="contact-sidebar-close"]').first();
    this.threadHeaderPatientName = page.locator('[data-testid="thread-header-patient-name"]').first();

    // Tool-calls (RN-6)
    this.toolCallCards = page.locator('[data-testid^="tool-call-card"]');

    // Empty / error
    this.emptyState = page.locator('[data-testid="inbox-empty-state"]');
    // InboxThread renders the error state with data-testid="conversation-thread-error"
    // (role="alert"). The old "thread-error-banner" id matched no component → errorBanner
    // never resolved (broke SC-10 :43 + states spec error assertions).
    // InboxThread renders TWICE (responsive: inbox-desktop `hidden md:flex` + inbox-mobile
    // `md:hidden`) → scope to the desktop layout (the visible one at Playwright's viewport)
    // to avoid a strict-mode 2-element match.
    this.errorBanner = page.locator(
      '[data-testid="inbox-desktop"] [data-testid="conversation-thread-error"]',
    );
    this.retryButton = page.locator('button[data-testid="thread-retry"]').first();

    // Legacy compat (preserve F1-S10 placeholder locators)
    this.globalModeToggle = page.locator('[data-testid="inbox-global-mode-toggle"]');
    this.adrianModeChip = page.locator('[aria-label="Adrián está manejando esta conversación"]');
    this.closeSidebarButton = page.locator('[aria-label="Cerrar panel de detalles"]');
    this.sidebarContainer = page.locator("[data-sidebar]").first();
  }

  // ── Navigation ─────────────────────────────────────────────────────────────

  async goto(): Promise<void> {
    await this.page.goto(`/${this.tenantId}/adrian/inbox`);
    await this.page.waitForLoadState("networkidle");
  }

  async gotoWithConversation(convId: string): Promise<void> {
    await this.page.goto(`/${this.tenantId}/adrian/inbox?conv=${convId}`);
    await this.page.waitForLoadState("networkidle");
  }

  // ── Conversation list ──────────────────────────────────────────────────────

  async openConversation(displayName: string): Promise<void> {
    await this.page
      .locator(`[aria-label*="Conversación con ${displayName}"]`)
      .first()
      .click();
    await this.page.waitForSelector('[aria-live="polite"]', { state: "visible" });
  }

  /** @deprecated use openConversation */
  async clickConversation(displayName: string): Promise<void> {
    return this.openConversation(displayName);
  }

  getConversationItems(): Locator {
    // Real DOM: InboxConvList renders role="listbox" aria-label="Conversaciones"
    // with each ConversationItem as [data-testid="conversation-item"] role="option".
    return this.page.locator('[data-testid="conversation-item"]');
  }

  async searchConversations(query: string): Promise<void> {
    await this.searchInput.fill(query);
  }

  getYouChip(): Locator {
    return this.page.locator(
      'span[title="Tomaste el control · Adrián pausado en esta conversación"]',
    );
  }

  async expectHumanHandledConversationVisible(displayName: string): Promise<void> {
    await expect(
      this.page.locator(`[aria-label*="Conversación con ${displayName}"]`).first(),
    ).toBeVisible();
    await expect(this.getYouChip().first()).toBeVisible();
  }

  // ── Mode toggle (3-modos) ──────────────────────────────────────────────────

  async toggleMode(mode: "decide" | "consulta" | "manual"): Promise<void> {
    const map = { decide: this.modeDecideOption, consulta: this.modeConsultaOption, manual: this.modeManualOption };
    await map[mode].click();
  }

  async takeControl(): Promise<void> {
    await this.takeControlButton.click();
  }

  async returnControl(): Promise<void> {
    await this.returnControlButton.click();
  }

  // ── Consulta draft ─────────────────────────────────────────────────────────

  async approveDraft(): Promise<void> {
    await this.approveButton.click();
  }

  async editDraft(newText: string): Promise<void> {
    await this.editDraftButton.click();
    await this.composerInput.clear();
    await this.composerInput.fill(newText);
    await this.sendButton.click();
  }

  async discardDraft(): Promise<void> {
    await this.discardDraftButton.click();
  }

  // ── Composer ──────────────────────────────────────────────────────────────

  async sendMessage(text: string): Promise<void> {
    await this.composerInput.fill(text);
    await this.sendButton.click();
  }

  // ── Full-canvas (modo conversación · RN-11/12) ────────────────────────────

  async clickModoConversacion(): Promise<void> {
    await this.conversationModeButton.click();
  }

  async expectValeriaCollapsed(): Promise<void> {
    const valeriaPanel = this.page.locator('[data-valeria-state="collapsed"]');
    await expect(valeriaPanel).toBeVisible();
  }

  async expectValeriaExpanded(): Promise<void> {
    const valeriaPanel = this.page.locator('[data-valeria-state="rail"], [data-valeria-state="full"]');
    await expect(valeriaPanel).toBeVisible();
  }

  // ── Nudge (RN-13) ─────────────────────────────────────────────────────────

  async clickNudge(): Promise<void> {
    await this.nudgeButton.click();
  }

  async confirmNudge(): Promise<void> {
    await this.nudgeConfirmButton.click();
  }

  async expectNudgeSuccess(): Promise<void> {
    await expect(this.nudgeToast).toBeVisible({ timeout: 5000 });
  }

  // ── Activity stream ────────────────────────────────────────────────────────

  getActivityStream(): Locator {
    return this.activityStream;
  }

  getActivityEvents(): Locator {
    return this.activityStream.locator('[data-testid^="activity-event"]');
  }

  async expectActivityContains(text: string): Promise<void> {
    await expect(this.activityStream).toContainText(text);
  }

  // ── Tool-calls (RN-6) ─────────────────────────────────────────────────────

  getToolCallCards(): Locator {
    return this.toolCallCards;
  }

  async expandToolCallCard(index: number): Promise<void> {
    await this.toolCallCards.nth(index).click();
  }

  // ── State assertions ───────────────────────────────────────────────────────

  // ★ 2-modos: ModeToggle es role="radiogroup"/role="radio" → aria-CHECKED (no -selected).
  async expectDecideMode(): Promise<void> {
    await expect(this.modeDecideOption).toHaveAttribute("aria-checked", "true");
  }

  async expectConsultaMode(): Promise<void> {
    await expect(this.modeConsultaOption).toHaveAttribute("aria-checked", "true");
  }

  /** @deprecated 2-modos: "manual" ya no es un modo (es Pausar). Locator no matchea. */
  async expectManualMode(): Promise<void> {
    await expect(this.modeManualOption).toHaveAttribute("aria-checked", "true");
  }

  // ── Pausa (2-modos amendment) ──────────────────────────────────────────────

  /** Abre el modal de pausa (2 botones, sin reason). */
  async openPauseModal(): Promise<void> {
    await this.pauseAdrianButton.click();
    await this.pauseModal.waitFor({ state: "visible" });
  }

  /** Elige "Pausar 60 minutos" en el modal. */
  async choosePause60(): Promise<void> {
    await this.pauseModal60.click();
  }

  /** Elige "Pausar permanente" en el modal. */
  async choosePausePermanent(): Promise<void> {
    await this.pauseModalPermanent.click();
  }

  // ── Modo (2-modos amendment) ───────────────────────────────────────────────

  /** Selecciona un segmento de los 2 modos (decide/consulta) por su data-testid real. */
  async setMode(value: "adrian-decide" | "adrian-consulta"): Promise<void> {
    await this.page.locator(`[data-testid="segment-${value}"]`).first().click();
  }

  async expectEmptyState(): Promise<void> {
    await expect(this.emptyState).toBeVisible();
    await expect(this.emptyState).toContainText(/Aún no hay conversaciones|Sin resultados/);
  }

  async expectErrorState(): Promise<void> {
    await expect(this.errorBanner).toBeVisible();
    await expect(this.errorBanner).toContainText(/No pudimos cargar/);
    await expect(this.retryButton).toBeVisible();
  }

  async expectThreadVisible(): Promise<void> {
    await expect(
      this.page.locator('[aria-live="polite"][aria-label="Mensajes de la conversación"]'),
    ).toBeVisible();
  }

  async expectPhiRedirectMessage(): Promise<void> {
    // RN-7: PHI redirect — response must mention portal, must NOT include clinical data
    await expect(this.threadSection).toContainText(/portal/i);
    await expect(this.threadSection).not.toContainText(/diagnóstico|resultados clínicos|lab_results/i);
  }

  async expectNoPhiInUrl(): Promise<void> {
    const url = this.page.url();
    // RN-14: only ?conv={uuid} allowed — no patient names or clinical data in URL
    expect(url).not.toMatch(/nombre|dni|paciente|diagnostico|diagnosis/i);
    if (url.includes("conv=")) {
      expect(url).toMatch(/conv=[0-9a-f-]{36}/);
    }
  }

  async expectDeepLinkConversation(convId: string): Promise<void> {
    await expect(this.page).toHaveURL(new RegExp(`conv=${convId}`));
    await this.expectThreadVisible();
  }

  async expectGlobalModeToggleVisible(): Promise<void> {
    await expect(this.globalModeToggle).toBeVisible();
  }

  // ── Legacy compat assertions (F1-S10) ─────────────────────────────────────

  /** @deprecated use expectDecideMode + autonomyBanner */
  async expectStateA(): Promise<void> {
    await expect(this.adrianModeChip).toBeVisible();
    await expect(this.takeControlButton).toBeVisible();
    await expect(this.page.locator("text=🤖 Devolver a Adrián").first()).not.toBeVisible();
    await expect(this.page.locator('[placeholder*="Adrián decide automáticamente"]')).toBeVisible();
  }

  /** @deprecated use expectManualMode + takeoverBanner */
  async expectStateB(): Promise<void> {
    await expect(this.returnControlButton).toBeVisible();
    await expect(this.page.locator('[placeholder*="Escribir como tú"]')).toBeVisible();
    await expect(this.adrianModeChip).not.toBeVisible();
  }

  async closeSidebar(): Promise<void> {
    await this.closeSidebarButton.first().click();
  }

  async expectSidebarOpen(): Promise<void> {
    await expect(this.page.locator('[data-sidebar="open"]')).toBeVisible();
  }

  async expectSidebarClosed(): Promise<void> {
    await expect(this.page.locator('[data-sidebar="closed"]')).toBeVisible();
  }
}
