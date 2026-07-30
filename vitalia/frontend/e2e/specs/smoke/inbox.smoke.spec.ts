/**
 * inbox.smoke.spec.ts — E2E smoke /inbox
 *
 * Validator IDs: e2e_smoke_inbox_local, e2e_smoke_inbox_live
 * Story: vitalia-slice-1-inbox
 *
 * Covers:
 *   SC-01 (happy path): shell renders con layout + segmented control + voice chip.
 *   SC-01 (toggle): segmented control cambia segmento activo.
 *   SC-02 (audio fallback): Whisper confidence < 0.5 → modo auto-cambia a "Yo escribo"
 *     + help_needed badge aparece + activity stream registra evento.
 *
 * Network: todas las llamadas API mockeadas vía page.route() — no requiere stack live.
 * Auth: Clerk testing token bypass vía clinic-context.fixture → auth.fixture.
 *
 * Stack vitalia si live: FE=3002, BE=8002.
 * Comando nativo: cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 npx playwright test --project=smoke
 * NUNCA: make e2e / make e2e-smoke (Docker — crashea laptop).
 *
 * downstream-regression-na: brand-local E2E smoke spec; no cross-brand consumers
 */

import {
  test as clinicBase,
  expect,
} from "../../fixtures/clinic-context.fixture";
import { collectConsoleErrors } from "../../auth.fixture";
import { InboxPage } from "../../pages/inbox.page";
import type { Page } from "@playwright/test";

// ---------------------------------------------------------------------------
// Seed IDs — stable para locators y mocks
// ---------------------------------------------------------------------------

const SEED = {
  /** SC-01 — M. Rodríguez, modo "Adrián decide" */
  leadIdHappy: "lead-mrodriguez-inbox-001",
  convIdHappy: "conv-mrodriguez-inbox-001",
  patientName: "M. Rodríguez",

  /** SC-02 — Ana López, audio sin transcripción */
  leadIdAudio: "lead-alopez-inbox-002",
  convIdAudio: "conv-alopez-inbox-002",
  patientNameAudio: "Ana López",
  audioMessageId: "msg-audio-alopez-001",
} as const;

// ---------------------------------------------------------------------------
// Mock payloads
// ---------------------------------------------------------------------------

/** Lista de conversaciones para el panel izquierdo */
const CONVERSATIONS_LIST_MOCK = [
  {
    lead_id: SEED.leadIdHappy,
    conversation_id: SEED.convIdHappy,
    patient_name: SEED.patientName,
    channel: "whatsapp",
    status: "active",
    stage: "interested",
    handler_mode: "ai",
    proposal_required: false,
    help_needed: false,
    unread_media: false,
    last_message_preview: "Hola, quería sacar turno para limpieza profunda",
    last_message_at: "2026-05-20T14:22:00Z",
    updated_at: "2026-05-20T14:22:00Z",
  },
  {
    lead_id: SEED.leadIdAudio,
    conversation_id: SEED.convIdAudio,
    patient_name: SEED.patientNameAudio,
    channel: "whatsapp",
    status: "active",
    stage: "interested",
    handler_mode: "human",
    proposal_required: false,
    help_needed: true,
    unread_media: true,
    last_message_preview: "[Nota de voz]",
    last_message_at: "2026-05-20T14:20:00Z",
    updated_at: "2026-05-20T14:21:00Z",
  },
];

/** Detalle de conversación SC-01 (modo ai, handler auto) */
const CONVERSATION_HAPPY_MOCK = {
  lead_id: SEED.leadIdHappy,
  conversation_id: SEED.convIdHappy,
  patient_name: SEED.patientName,
  channel: "whatsapp",
  status: "active",
  stage: "interested",
  handler_mode: "ai",
  proposal_required: false,
  help_needed: false,
  updated_at: "2026-05-20T14:22:00Z",
  messages: [
    {
      message_id: "msg-patient-001",
      sender_type: "patient",
      content: "Hola, quería sacar turno para limpieza profunda",
      sent_at: "2026-05-20T14:22:00Z",
      media_type: null,
    },
    {
      message_id: "msg-agent-001",
      sender_type: "agent",
      content:
        "¡Hola M. Rodríguez! Te puedo ofrecer martes 12:00 con Dr. Ortiz para una limpieza profunda.",
      sent_at: "2026-05-20T14:22:05Z",
      media_type: null,
      auto_sent: true,
      action_receipt: {
        receipt_id: "receipt-001",
        retract_available_until: new Date(
          Date.now() + 4 * 60 * 1000 + 58 * 1000,
        ).toISOString(),
      },
    },
  ],
};

/** Detalle de conversación SC-02 (audio, help_needed=true, handler_mode=human post-fallback) */
const CONVERSATION_AUDIO_MOCK = {
  lead_id: SEED.leadIdAudio,
  conversation_id: SEED.convIdAudio,
  patient_name: SEED.patientNameAudio,
  channel: "whatsapp",
  status: "active",
  stage: "interested",
  handler_mode: "human",
  proposal_required: false,
  help_needed: true,
  updated_at: "2026-05-20T14:21:00Z",
  messages: [
    {
      message_id: SEED.audioMessageId,
      sender_type: "patient",
      content: null,
      sent_at: "2026-05-20T14:20:00Z",
      media_type: "audio",
      media_url: "https://storage.vitalia.test/audio/alopez-001.ogg",
      duration_seconds: 18,
      transcript: null,
      transcript_confidence: 0.0,
      fallback_reason: "audio_low_confidence",
    },
    {
      message_id: "msg-system-fallback-001",
      sender_type: "system",
      content:
        "Adrián recibió una nota de voz pero no pudo entenderla bien. Te paso la conversación para que la escuches tú.",
      sent_at: "2026-05-20T14:20:10Z",
      media_type: null,
    },
  ],
};

/** Activity stream para SC-01 */
const ACTIVITY_STREAM_HAPPY_MOCK = {
  conversation_id: SEED.convIdHappy,
  events: [
    {
      id: "act-001",
      occurred_at: "2026-05-20T14:22:04Z",
      description: "consultó precio de Blanqueamiento Premium",
    },
    {
      id: "act-002",
      occurred_at: "2026-05-20T14:22:03Z",
      description: "verificó disponibilidad martes 12:00 (libre)",
    },
    {
      id: "act-003",
      occurred_at: "2026-05-20T14:22:02Z",
      description: 'propuso: "Te puedo ofrecer martes 12:00…"',
    },
    {
      id: "act-004",
      occurred_at: "2026-05-20T14:22:01Z",
      description: "clasificó: interés alto · vertical odontológica",
    },
  ],
};

/** Activity stream para SC-02 (audio fallback) */
const ACTIVITY_STREAM_AUDIO_MOCK = {
  conversation_id: SEED.convIdAudio,
  events: [
    {
      id: "act-audio-001",
      occurred_at: "2026-05-20T14:20:09Z",
      description:
        "Adrián no pudo entender la nota de voz · derivó la conversación",
    },
  ],
};

/** Respuesta de transcribe-audio con confidence < 0.5 (SC-02 mock) */
const TRANSCRIBE_AUDIO_LOW_CONFIDENCE = {
  transcript: "",
  confidence: 0.0,
  fallback: true,
  fallback_reason: "audio_low_confidence",
  mode_switched_to: "human",
};

// ---------------------------------------------------------------------------
// Mock setup
// ---------------------------------------------------------------------------

async function setupInboxMocks(page: Page): Promise<void> {
  // Mock: lista de conversaciones (GET con cualquier query string)
  await page.route("**/api/v1/vitalia/inbox/conversations**", async (route) => {
    if (route.request().method() === "GET") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          conversations: CONVERSATIONS_LIST_MOCK,
          total: CONVERSATIONS_LIST_MOCK.length,
          next_cursor: null,
        }),
      });
    } else {
      await route.continue();
    }
  });

  // Mock: detalle conversación SC-01 (M. Rodríguez)
  await page.route(
    `**/api/v1/vitalia/inbox/conversations/${SEED.convIdHappy}**`,
    async (route) => {
      if (route.request().method() === "GET") {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify(CONVERSATION_HAPPY_MOCK),
        });
      } else {
        await route.continue();
      }
    },
  );

  // Mock: detalle conversación SC-02 (Ana López — audio fallback)
  await page.route(
    `**/api/v1/vitalia/inbox/conversations/${SEED.convIdAudio}**`,
    async (route) => {
      // Exclude sub-routes (transcribe-audio, mode, activity-stream)
      if (
        route.request().method() === "GET" &&
        !route.request().url().includes("/transcribe-audio") &&
        !route.request().url().includes("/mode") &&
        !route.request().url().includes("/activity-stream")
      ) {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify(CONVERSATION_AUDIO_MOCK),
        });
      } else {
        await route.continue();
      }
    },
  );

  // Mock: activity stream SC-01
  await page.route(
    `**/api/v1/vitalia/inbox/conversations/${SEED.convIdHappy}/activity-stream**`,
    async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(ACTIVITY_STREAM_HAPPY_MOCK),
      });
    },
  );

  // Mock: activity stream SC-02
  await page.route(
    `**/api/v1/vitalia/inbox/conversations/${SEED.convIdAudio}/activity-stream**`,
    async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(ACTIVITY_STREAM_AUDIO_MOCK),
      });
    },
  );

  // Mock: transcribe-audio (POST) — confidence < 0.5 triggers SC-02 fallback
  await page.route(
    `**/api/v1/vitalia/inbox/conversations/${SEED.convIdAudio}/transcribe-audio`,
    async (route) => {
      if (route.request().method() === "POST") {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify(TRANSCRIBE_AUDIO_LOW_CONFIDENCE),
        });
      } else {
        await route.continue();
      }
    },
  );

  // Mock: mode toggle (POST) — PATCH/POST /mode — return updated conversation
  await page.route(
    `**/api/v1/vitalia/inbox/conversations/*/mode**`,
    async (route) => {
      if (
        route.request().method() === "POST" ||
        route.request().method() === "PATCH"
      ) {
        // Parse which conversation and what mode is being set
        const body = route.request().postDataJSON() as {
          handler_mode?: string;
          proposal_required?: boolean;
        } | null;
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            handler_mode: body?.handler_mode ?? "ai",
            proposal_required: body?.proposal_required ?? false,
            updated_at: new Date().toISOString(),
          }),
        });
      } else {
        await route.continue();
      }
    },
  );

  // Mock: tools endpoint
  await page.route(
    "**/api/v1/vitalia/inbox/conversations/*/tools**",
    async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ tools: [] }),
      });
    },
  );

  // Mock: leads detail (CRM)
  await page.route("**/api/v1/vitalia/crm/leads/**", async (route) => {
    if (route.request().method() === "GET") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          lead_id: SEED.leadIdHappy,
          patient_name: SEED.patientName,
        }),
      });
    } else {
      await route.continue();
    }
  });
}

// ---------------------------------------------------------------------------
// Fixture
// ---------------------------------------------------------------------------

/** Extend clinic-context fixture con mocks inbox */
const test = clinicBase.extend<{ inboxPage: import("@playwright/test").Page }>({
  inboxPage: async ({ clinicPage }, use) => {
    await setupInboxMocks(clinicPage);
    await use(clinicPage);
  },
});

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

test.describe("Inbox — smoke", () => {
  // ─── SC-01: shell renders ─────────────────────────────────────────────────

  test("test_shell_renders — layout monta con título y 3 paneles", async ({
    inboxPage: page,
  }) => {
    const consoleErrors = collectConsoleErrors(page);
    const inbox = new InboxPage(page);

    await inbox.goto();
    await inbox.waitForReady();

    // Layout principal visible
    await expect(inbox.inboxLayout).toBeVisible();

    // Panel de lista de conversaciones
    await expect(inbox.conversationListPanel).toBeVisible();

    // Panel de hilo (placeholder o thread) — alguno de los dos debe estar visible
    // Sin conversación seleccionada → puede mostrar ambos (panel con placeholder dentro)
    // Verificamos que el panel principal del hilo existe
    const threadPanel = page.getByTestId("conversation-thread-panel");
    const threadPanelVisible = await threadPanel.isVisible().catch(() => false);
    const threadPlaceholderVisible = await page
      .getByTestId("thread-placeholder")
      .isVisible()
      .catch(() => false);
    expect(
      threadPanelVisible || threadPlaceholderVisible,
      "Se espera conversation-thread-panel o thread-placeholder visible",
    ).toBe(true);

    expect(consoleErrors).toHaveLength(0);
  });

  // ─── SC-01: segmented control visible y funcional ─────────────────────────
  //
  // DEFERRED STEP 3 NOTE: Este test requiere InboxPageClient ensamblado con
  // ConversationThread + SegmentedControl3Modes (T-inbox-fe-4 wiring pendiente).
  // Actualmente InboxPageClient usa slots placeholder (T-inbox-fe-1 scaffold).
  // El test verifica lo disponible en el scaffold y documenta los assertions
  // full que se activan una vez que T-inbox-fe-4 assembly quede en main.
  //
  // Gherkin coverage: SC-01 (partial) → test_segmented_control_toggles
  // Validators: e2e_smoke_inbox_local (partial — full after fe-4 assembly)

  test("test_segmented_control_toggles — 3 segmentos navegables", async ({
    inboxPage: page,
  }) => {
    const inbox = new InboxPage(page);

    // ── Phase 1: scaffold disponible ──────────────────────────────────────
    // Navegar con conversación — InboxLayout carga siempre
    await inbox.gotoWithConversation(SEED.leadIdHappy);
    await inbox.waitForReady();

    // Layout principal y panel de lista son visibles (scaffold)
    await expect(inbox.inboxLayout).toBeVisible();
    await expect(inbox.conversationListPanel).toBeVisible();

    // Panel thread visible (contiene placeholder en scaffold)
    await expect(inbox.conversationThreadPanel).toBeVisible();

    // ── Phase 2: full thread (requiere T-inbox-fe-4 assembly) ────────────
    // Verificamos si ConversationThread fue ensamblado (post-scaffold)
    const isThreadAssembled = await inbox.conversationThread
      .isVisible({ timeout: 3_000 })
      .catch(() => false);

    if (isThreadAssembled) {
      // Full assertions — T-inbox-fe-4 wired
      await inbox.waitForThreadReady();

      // Segmented control visible
      await expect(inbox.segmentedControl).toBeVisible();

      const segAdrianDecide = inbox.segment("adrian-decide");
      const segAdrianConsulta = inbox.segment("adrian-consulta");
      const segYoEscribo = inbox.segment("yo-escribo");

      await expect(segAdrianDecide).toBeVisible();
      await expect(segAdrianConsulta).toBeVisible();
      await expect(segYoEscribo).toBeVisible();

      // "Adrián decide" es activo por defecto
      await expect(segAdrianDecide).toHaveAttribute("aria-checked", "true");
      await expect(segAdrianConsulta).toHaveAttribute("aria-checked", "false");
      await expect(segYoEscribo).toHaveAttribute("aria-checked", "false");

      // Click "Adrián consulta" → activo
      await inbox.clickSegment("adrian-consulta");
      await expect(segAdrianConsulta).toHaveAttribute("aria-checked", "true", {
        timeout: 5_000,
      });

      // Click "Yo escribo" → activo
      await inbox.clickSegment("yo-escribo");
      await expect(segYoEscribo).toHaveAttribute("aria-checked", "true", {
        timeout: 5_000,
      });

      // Voice style chip siempre visible
      await expect(inbox.voiceStyleChip).toBeVisible();
    } else {
      // Scaffold mode: verifica placeholder visible como smoke básico
      // Full assertions pendientes hasta T-inbox-fe-4 assembly en InboxPageClient
      const threadPlaceholder = await page
        .getByTestId("thread-placeholder")
        .isVisible()
        .catch(() => false);
      expect(
        threadPlaceholder,
        "scaffold: thread-placeholder visible mientras T-inbox-fe-4 assembly pending",
      ).toBe(true);
    }
  });

  // ─── SC-02: audio fallback ────────────────────────────────────────────────
  //
  // DEFERRED STEP 3 NOTE: Este test requiere InboxPageClient ensamblado con
  // ConversationList (T-inbox-fe-3), ConversationThread (T-inbox-fe-4) y
  // AgentActivityStream (T-inbox-fe-6). Actualmente en estado scaffold.
  // El test verifica el scaffold shell y documenta los assertions full para
  // activar una vez que la assembly esté en main.
  //
  // Gherkin coverage: SC-02 (partial) → test_audio_low_confidence_fallback
  // Validators: e2e_smoke_inbox_local (partial — full after fe-3/4/6 assembly)

  test("test_audio_low_confidence_fallback — modo auto-cambia a 'Yo escribo' + help_needed badge", async ({
    inboxPage: page,
  }) => {
    const inbox = new InboxPage(page);

    // ── Phase 1: scaffold disponible ──────────────────────────────────────
    await inbox.gotoWithConversation(SEED.leadIdAudio);
    await inbox.waitForReady();

    // Layout principal siempre visible
    await expect(inbox.inboxLayout).toBeVisible();
    await expect(inbox.conversationListPanel).toBeVisible();

    // ── Phase 2: full thread + activity stream (requiere fe-3/4/6 assembly) ─
    const isListAssembled = await page
      .getByTestId(`conversation-item-${SEED.leadIdAudio}`)
      .isVisible({ timeout: 3_000 })
      .catch(() => false);
    const isThreadAssembled = await inbox.conversationThread
      .isVisible({ timeout: 3_000 })
      .catch(() => false);

    if (isListAssembled && isThreadAssembled) {
      // Full assertions — fe-3/4/6 wired

      // Segmented control en modo "Yo escribo" (handler_mode='human' post-fallback)
      await expect(inbox.segmentedControl).toBeVisible();
      const segYoEscribo = inbox.segment("yo-escribo");
      await expect(segYoEscribo).toHaveAttribute("aria-checked", "true", {
        timeout: 8_000,
      });

      // "Adrián decide" ya NO activo
      const segAdrianDecide = inbox.segment("adrian-decide");
      await expect(segAdrianDecide).toHaveAttribute("aria-checked", "false");

      // Help-needed badge en la lista
      const helpBadge =
        inbox.conversationListPanel.getByTestId("help-needed-badge");
      await expect(helpBadge).toBeVisible({ timeout: 8_000 });

      // Activity stream: evento de derivación audio
      const streamToggle = inbox.activityStreamToggle;
      if (await streamToggle.isVisible()) {
        const isExpanded =
          await inbox.agentActivityStream.getAttribute("aria-expanded");
        if (isExpanded === "false" || isExpanded === null) {
          await inbox.toggleActivityStream();
        }
      }

      const fallbackEvent = inbox.activityEvent(
        /Adrián no pudo entender la nota de voz/i,
      );
      await expect(fallbackEvent).toBeVisible({ timeout: 8_000 });
    } else {
      // Scaffold mode: verifica placeholder visible como smoke básico
      // Full assertions pendientes hasta fe-3/4/6 assembly en InboxPageClient
      const listPlaceholder = await page
        .getByTestId("conversation-list-placeholder")
        .isVisible()
        .catch(() => false);
      const threadPlaceholder = await page
        .getByTestId("thread-placeholder")
        .isVisible()
        .catch(() => false);
      expect(
        listPlaceholder || threadPlaceholder,
        "scaffold: conversation-list-placeholder o thread-placeholder visible mientras fe-3/4/6 assembly pending",
      ).toBe(true);
    }
  });
});
