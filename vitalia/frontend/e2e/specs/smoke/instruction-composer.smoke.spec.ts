// cap: adrian.inbox
/**
 * instruction-composer.smoke.spec.ts — E2E smoke for composer instruction mode (V-VIS-1)
 *
 * Validator ID: V-VIS-1
 * Story: vitalia-fase2-adrian-canal-inbound T-FE-1
 *
 * Covers:
 *   SC-8 (instruction): composer shows '🤖 Instrucción a Adrián' label in decide mode.
 *   SC-8 (send): POST /instruction request made with correct payload.
 *   RN-14 (paused): handler_mode=human → direct mode composer (no instruction label).
 *
 * Network: API calls mocked via page.route() — no stack live required.
 * Auth: Clerk testing token bypass via clinic-context.fixture → auth.fixture.
 *
 * playwright_visual_scope:
 *   routes:       /{tenantId}/adrian/inbox
 *   touchable:    features/adrian/components/inbox/composer/
 *   forbidden:    shell-organism/*, other sub-tabs
 *
 * Comando nativo:
 *   cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 npx playwright test --project=smoke --grep="instruction"
 * NUNCA: make e2e / make e2e-smoke (Docker — crashea)
 *
 * downstream-regression-na: brand-local E2E smoke; no cross-brand consumers
 */

import {
  test as clinicBase,
  expect,
} from "../../fixtures/clinic-context.fixture";
import { collectConsoleErrors } from "../../auth.fixture";

// ── Seed IDs ─────────────────────────────────────────────────────────────────

const SEED = {
  convIdDecide: "conv-instruction-test-001",
  convIdPaused: "conv-instruction-paused-001",
  tenantId: "tenant-vitalia-test",
} as const;

// ── Mock factory ─────────────────────────────────────────────────────────────

function makeConversationPayload(handlerMode: "ai" | "human") {
  return {
    conversation: {
      id: handlerMode === "ai" ? SEED.convIdDecide : SEED.convIdPaused,
      tenant_id: SEED.tenantId,
      clinic_id: "clinic-test-001",
      lead_id: "lead-test-001",
      patient_id: null,
      channel: "telegram",
      status: "active",
      handler_mode: handlerMode,
      proposal_required: false,
      pause_until: null,
      help_needed: false,
      help_needed_reason: null,
      unread_media_count: 0,
      last_message_at: "2026-06-21T10:00:00Z",
      last_message_preview: "Hola, quiero información",
      messages_count: 1,
      stage_decision: null,
      linked_offer_id: null,
      updated_at: "2026-06-21T10:00:00Z",
    },
    lead: {
      id: "lead-test-001",
      tenant_id: SEED.tenantId,
      display_name: "Test Lead",
      email: null,
      phone: "+99 0 1234 5678",
      channel: "telegram",
      stage_decision: null,
    },
    messages: [
      {
        id: "msg-001",
        conversation_id: handlerMode === "ai" ? SEED.convIdDecide : SEED.convIdPaused,
        sender_type: "patient",
        sender_user_id: null,
        body_text: "Hola, quiero información",
        media_kind: null,
        media_url: null,
        media_duration_s: null,
        transcription_text: null,
        transcription_confidence: null,
        retracted_at: null,
        retract_succeeded: null,
        handler_mode: handlerMode,
        sent_at: "2026-06-21T10:00:00Z",
        action_receipt_expires_at: null,
      },
    ],
    action_receipts: [],
    tools_state: null,
  };
}

function makeConversationList(handlerMode: "ai" | "human") {
  return [
    {
      id: handlerMode === "ai" ? SEED.convIdDecide : SEED.convIdPaused,
      lead_id: "lead-test-001",
      display_name: "Test Lead",
      last_message_preview: "Hola, quiero información",
      last_message_at: "2026-06-21T10:00:00Z",
      channel: "telegram",
      handler_mode: handlerMode,
      status: "active",
      help_needed: false,
      unread_media_count: 0,
    },
  ];
}

// ── Tests ─────────────────────────────────────────────────────────────────────

clinicBase.describe("V-VIS-1 — Composer instruction mode", () => {
  clinicBase(
    "shows 🤖 Instrucción a Adrián label when handler_mode=ai (decide)",
    async ({ page, tenantId }) => {
      const errors = collectConsoleErrors(page);

      // Mock conversation list + detail
      await page.route("**/api/v1/vitalia/inbox/conversations*", async (route) => {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify(makeConversationList("ai")),
        });
      });

      await page.route(
        `**/api/v1/vitalia/inbox/conversations/${SEED.convIdDecide}*`,
        async (route) => {
          await route.fulfill({
            status: 200,
            contentType: "application/json",
            body: JSON.stringify(makeConversationPayload("ai")),
          });
        },
      );

      // Navigate to inbox
      await page.goto(`/${tenantId}/adrian/inbox?conv=${SEED.convIdDecide}`);
      await page.waitForLoadState("networkidle");

      // V-VIS-1: instruction mode label must be visible
      await expect(
        page.getByRole("note", { name: "🤖 Instrucción a Adrián" }),
      ).toBeVisible();

      // Textarea should have instruction placeholder
      await expect(
        page.getByRole("textbox"),
      ).toHaveAttribute(
        "placeholder",
        "Instrucción a Adrián (el paciente no la verá)…",
      );

      // Send button should say "Dar instrucción"
      await expect(
        page.getByRole("button", { name: "Dar instrucción" }),
      ).toBeVisible();

      // No console errors
      expect(errors).toHaveLength(0);
    },
  );

  clinicBase(
    "direct mode shown when handler_mode=human (Adrián paused) — RN-14",
    async ({ page, tenantId }) => {
      const errors = collectConsoleErrors(page);

      await page.route("**/api/v1/vitalia/inbox/conversations*", async (route) => {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify(makeConversationList("human")),
        });
      });

      await page.route(
        `**/api/v1/vitalia/inbox/conversations/${SEED.convIdPaused}*`,
        async (route) => {
          await route.fulfill({
            status: 200,
            contentType: "application/json",
            body: JSON.stringify(makeConversationPayload("human")),
          });
        },
      );

      await page.goto(`/${tenantId}/adrian/inbox?conv=${SEED.convIdPaused}`);
      await page.waitForLoadState("networkidle");

      // Instruction label must NOT appear in direct mode
      await expect(
        page.getByRole("note", { name: "🤖 Instrucción a Adrián" }),
      ).not.toBeVisible();

      // Send button should say "Enviar" (direct to lead)
      await expect(
        page.getByRole("button", { name: "Enviar" }),
      ).toBeVisible();

      expect(errors).toHaveLength(0);
    },
  );

  clinicBase(
    "POST /instruction called with correct payload on send — SC-8",
    async ({ page, tenantId }) => {
      let instructionPostBody: Record<string, unknown> | null = null;

      await page.route("**/api/v1/vitalia/inbox/conversations*", async (route) => {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify(makeConversationList("ai")),
        });
      });

      await page.route(
        `**/api/v1/vitalia/inbox/conversations/${SEED.convIdDecide}*`,
        async (route) => {
          // Intercept instruction POST
          if (route.request().method() === "POST" && route.request().url().includes("/instruction")) {
            instructionPostBody = route.request().postDataJSON() as Record<string, unknown>;
            await route.fulfill({
              status: 200,
              contentType: "application/json",
              body: JSON.stringify({
                conversationId: SEED.convIdDecide,
                instructionActive: true,
                updatedAt: "2026-06-21T10:05:00Z",
              }),
            });
          } else {
            await route.fulfill({
              status: 200,
              contentType: "application/json",
              body: JSON.stringify(makeConversationPayload("ai")),
            });
          }
        },
      );

      await page.goto(`/${tenantId}/adrian/inbox?conv=${SEED.convIdDecide}`);
      await page.waitForLoadState("networkidle");

      // Type instruction and send
      const textarea = page.getByRole("textbox");
      await textarea.fill("Ofrécele 10% de descuento por ser referido");

      await page.getByRole("button", { name: "Dar instrucción" }).click();

      // Wait for POST to be captured
      await page.waitForTimeout(500);

      // Verify payload (lead NEVER receives — no body_text sent to channel)
      expect(instructionPostBody).not.toBeNull();
      expect(instructionPostBody).toMatchObject({
        instruction: "Ofrécele 10% de descuento por ser referido",
      });
    },
  );
});
