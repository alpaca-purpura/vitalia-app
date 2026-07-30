/**
 * inbox.page.ts — Page Object Model para /inbox
 *
 * Validator IDs: e2e_smoke_inbox_local, e2e_smoke_inbox_live
 * Story: vitalia-slice-1-inbox
 *
 * Locators: data-testid first (ARIA como fallback).
 * Sin assertions en métodos POM — solo acciones + locators.
 *
 * downstream-regression-na: brand-local E2E POM; no cross-brand consumers
 */

import type { Page, Locator } from "@playwright/test";

/** Segmented control mode values (mapping a SegmentedModeValue) */
export type InboxSegmentValue =
  | "adrian-decide"
  | "adrian-consulta"
  | "yo-escribo";

/** Tab activa del layout */
export type InboxTabKey = "conversations" | "contact" | "activity";

// ---------------------------------------------------------------------------
// InboxPage — POM
// ---------------------------------------------------------------------------

export class InboxPage {
  readonly page: Page;

  // ── Layout principal ──────────────────────────────────────────────────────
  readonly inboxLayout: Locator;
  readonly conversationListPanel: Locator;
  readonly conversationThreadPanel: Locator;
  readonly contactSidebarPanel: Locator;

  // ── Lista de conversaciones ───────────────────────────────────────────────
  readonly conversationListEmpty: Locator;
  readonly conversationListPlaceholder: Locator;

  // ── Hilo (ThreadHeader + ThreadBody) ─────────────────────────────────────
  readonly threadPlaceholder: Locator;
  readonly conversationThread: Locator;
  readonly messagesList: Locator;
  readonly threadHeader: Locator;
  readonly threadHeaderPatientName: Locator;
  readonly threadHeaderChannel: Locator;

  // ── Segmented control modos Adrián ───────────────────────────────────────
  readonly segmentedControl: Locator;

  // ── Voice Style Chip ─────────────────────────────────────────────────────
  readonly voiceStyleChip: Locator;

  // ── Activity Stream ───────────────────────────────────────────────────────
  readonly agentActivityStream: Locator;
  readonly activityStreamToggle: Locator;
  readonly activityEventList: Locator;

  // ── Acciones de hilo ─────────────────────────────────────────────────────
  readonly pauseAdrianButton: Locator;
  readonly toolsSheetTrigger: Locator;
  readonly contactSidebarToggle: Locator;
  readonly pauseAdrianModal: Locator;

  // ── Contact sidebar ───────────────────────────────────────────────────────
  readonly contactSidebarPlaceholder: Locator;
  readonly inboxContactSidebar: Locator;

  constructor(page: Page) {
    this.page = page;

    // Layout
    this.inboxLayout = page.getByTestId("inbox-layout");
    this.conversationListPanel = page.getByTestId("conversation-list-panel");
    this.conversationThreadPanel = page.getByTestId(
      "conversation-thread-panel",
    );
    this.contactSidebarPanel = page.getByTestId("contact-sidebar-panel");

    // Lista conversaciones
    this.conversationListEmpty = page.getByTestId(
      "conversation-list-empty-wrapper",
    );
    this.conversationListPlaceholder = page.getByTestId(
      "conversation-list-placeholder",
    );

    // Hilo
    this.threadPlaceholder = page.getByTestId("thread-placeholder");
    this.conversationThread = page.getByTestId("conversation-thread");
    this.messagesList = page.getByTestId("messages-list");
    this.threadHeader = page.getByTestId("thread-header");
    this.threadHeaderPatientName = page.getByTestId(
      "thread-header-patient-name",
    );
    this.threadHeaderChannel = page.getByTestId("thread-header-channel");

    // Segmented control
    this.segmentedControl = page.getByTestId("segmented-control-3-modes");

    // Voice style chip
    this.voiceStyleChip = page.getByTestId("voice-style-chip");

    // Activity stream
    this.agentActivityStream = page.getByTestId("agent-activity-stream");
    this.activityStreamToggle = page.getByTestId("activity-stream-toggle");
    this.activityEventList = page.getByTestId("activity-event-list");

    // Acciones
    this.pauseAdrianButton = page.getByTestId("pause-adrian-button");
    this.toolsSheetTrigger = page.getByTestId("tools-sheet-trigger");
    this.contactSidebarToggle = page.getByTestId("contact-sidebar-toggle");
    this.pauseAdrianModal = page.getByTestId("pause-adrian-modal");

    // Sidebar
    this.contactSidebarPlaceholder = page.getByTestId(
      "contact-sidebar-placeholder",
    );
    this.inboxContactSidebar = page.getByTestId("inbox-contact-sidebar");
  }

  // ── Navegación ────────────────────────────────────────────────────────────

  /** Navega a /inbox */
  async goto(): Promise<void> {
    await this.page.goto("/inbox");
  }

  /** Navega a /inbox con conversación específica abierta */
  async gotoWithConversation(leadId: string): Promise<void> {
    await this.page.goto(`/inbox?lead=${leadId}`);
  }

  /** Espera a que el layout principal sea visible */
  async waitForReady(): Promise<void> {
    await this.inboxLayout.waitFor({ state: "visible" });
  }

  /** Espera a que el hilo de conversación sea visible (tras seleccionar lead) */
  async waitForThreadReady(): Promise<void> {
    await this.conversationThread.waitFor({ state: "visible" });
    await this.messagesList.waitFor({ state: "visible" });
  }

  // ── Selectors de conversación ─────────────────────────────────────────────

  /** Locator para un item de conversación por leadId */
  conversationItem(leadId: string): Locator {
    return this.page.getByTestId(`conversation-item-${leadId}`);
  }

  /** Locator para un message bubble por messageId */
  messageBubble(messageId: string): Locator {
    return this.page.getByTestId(`message-bubble-${messageId}`);
  }

  /** Locator para el badge de "ayuda necesaria" en un item de conversación */
  helpNeededBadge(leadId: string): Locator {
    return this.conversationItem(leadId).getByTestId("help-needed-badge");
  }

  /** Locator para el badge de media no leída en un item de conversación */
  unreadMediaBadge(leadId: string): Locator {
    return this.conversationItem(leadId).getByTestId("unread-media-badge");
  }

  /** Locator para el chip de etapa de un item de conversación */
  stageChip(leadId: string): Locator {
    return this.conversationItem(leadId).getByTestId("stage-chip");
  }

  // ── Segmented control ─────────────────────────────────────────────────────

  /** Locator para un segmento específico del control de 3 modos */
  segment(value: InboxSegmentValue): Locator {
    return this.page.getByTestId(`segment-${value}`);
  }

  /** Hace clic en un segmento del control de modos */
  async clickSegment(value: InboxSegmentValue): Promise<void> {
    await this.segment(value).click();
  }

  /** Retorna el segmento actualmente marcado como aria-checked="true" */
  activeSegment(): Locator {
    return this.segmentedControl.locator('[aria-checked="true"]');
  }

  // ── Activity stream ───────────────────────────────────────────────────────

  /** Abre/cierra el activity stream toggle */
  async toggleActivityStream(): Promise<void> {
    await this.activityStreamToggle.click();
  }

  /** Locator para un evento específico del activity stream por texto parcial */
  activityEvent(textMatch: string | RegExp): Locator {
    return this.activityEventList.getByText(textMatch);
  }

  // ── Modal de pausa ────────────────────────────────────────────────────────

  /** Abre el modal de confirmación para pausar a Adrián */
  async openPauseModal(): Promise<void> {
    await this.pauseAdrianButton.click();
  }
}
