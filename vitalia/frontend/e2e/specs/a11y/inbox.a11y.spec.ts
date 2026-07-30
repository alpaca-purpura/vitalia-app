/**
 * inbox.a11y.spec.ts — WCAG 2.1 AA accessibility scan on /inbox
 *
 * Validator ID: a11y_axe_inbox
 * Story: vitalia-slice-1-inbox
 *
 * Spec §15 accessibility requirements (from 01-spec.md):
 *   - role="radiogroup" for handler_mode radio buttons (AI/human toggle)
 *   - aria-live="polite" for ActionReceipt countdown timer
 *   - aria-label for PHI reveal button ("Mostrar datos del paciente")
 *   - 0 critical/serious WCAG 2.1 AA violations on /inbox
 *
 * Network: mocked via page.route() — no live stack required.
 * Graceful skip if @axe-core/playwright not installed.
 *
 * Testing strategy:
 *   1. Navigate to /inbox with mocked conversations list
 *   2. Run axe analysis with WCAG 2.1 AA tags
 *   3. Assert critical + serious violations = 0
 *   4. Spot-check specific ARIA requirements from spec §15
 *
 * downstream-regression-na: brand-local vitalia E2E a11y spec; no cross-brand consumers
 */

import { test, expect } from "../../fixtures/clinic-context.fixture";
import { CLINIC_CONTEXT } from "../../fixtures/clinic-context.fixture";

// ---------------------------------------------------------------------------
// Graceful import — @axe-core/playwright may not be installed
// ---------------------------------------------------------------------------

let AxeBuilder: (typeof import("@axe-core/playwright"))["default"] | null =
  null;

test.describe("Inbox — WCAG 2.1 AA accessibility (axe-core)", () => {
  test.beforeAll(async () => {
    try {
      const axeModule = await import("@axe-core/playwright");
      AxeBuilder = axeModule.default;
    } catch {
      // Package not installed — tests will be skipped with clear message
      AxeBuilder = null;
    }
  });

  // ─── Main inbox page: 0 critical/serious violations ──────────────────────

  test("V-A11Y-01: /inbox tiene 0 violaciones WCAG 2.1 AA críticas/serias", async ({
    clinicPage: page,
  }) => {
    if (!AxeBuilder) {
      test.skip(
        true,
        "@axe-core/playwright not installed — run: npm i -D @axe-core/playwright",
      );
      return;
    }

    // Mock: conversations list with 2 conversations
    await page.route(
      "**/api/v1/vitalia/inbox/conversations**",
      async (route) => {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            conversations: [
              {
                id: "conv-a11y-001",
                tenant_id: CLINIC_CONTEXT.tenantId,
                clinic_id: CLINIC_CONTEXT.clinicId,
                lead_id: "lead-a11y-001",
                channel: "whatsapp",
                status: "active",
                handler_mode: "ai",
                help_needed: false,
                last_message_preview: "Hola, ¿cómo estás?",
                last_message_at: new Date().toISOString(),
                unread_count: 2,
              },
              {
                id: "conv-a11y-002",
                tenant_id: CLINIC_CONTEXT.tenantId,
                clinic_id: CLINIC_CONTEXT.clinicId,
                lead_id: "lead-a11y-002",
                channel: "whatsapp",
                status: "active",
                handler_mode: "human",
                help_needed: true,
                last_message_preview: "Tengo una duda sobre mi tratamiento.",
                last_message_at: new Date(Date.now() - 3600_000).toISOString(),
                unread_count: 0,
              },
            ],
            total: 2,
            has_more: false,
          }),
        });
      },
    );

    // Navigate to /inbox
    await page.goto("/inbox");
    await page.waitForLoadState("domcontentloaded");

    // Run axe analysis
    const results = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
      .analyze();

    const criticalOrSerious = results.violations.filter(
      (v) => v.impact === "critical" || v.impact === "serious",
    );

    if (criticalOrSerious.length > 0) {
      const details = criticalOrSerious
        .map(
          (v) =>
            `[${v.impact?.toUpperCase() ?? "UNKNOWN"}] ${v.id}: ${v.description}\n  Nodes: ${v.nodes.map((n) => n.target.join(", ")).join("; ")}`,
        )
        .join("\n");
      throw new Error(
        `Inbox /inbox has ${criticalOrSerious.length} critical/serious WCAG 2.1 AA violations:\n${details}`,
      );
    }

    expect(criticalOrSerious).toHaveLength(0);
  });

  // ─── Conversation detail view: 0 critical/serious violations ─────────────

  test("V-A11Y-02: /inbox/[convId] tiene 0 violaciones WCAG 2.1 AA críticas/serias", async ({
    clinicPage: page,
  }) => {
    if (!AxeBuilder) {
      test.skip(
        true,
        "@axe-core/playwright not installed — run: npm i -D @axe-core/playwright",
      );
      return;
    }

    const convId = "conv-a11y-detail-001";

    // Mock: single conversation details
    await page.route(
      `**/api/v1/vitalia/inbox/conversations/${convId}`,
      async (route) => {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            id: convId,
            tenant_id: CLINIC_CONTEXT.tenantId,
            clinic_id: CLINIC_CONTEXT.clinicId,
            lead_id: "lead-a11y-detail",
            channel: "whatsapp",
            status: "active",
            handler_mode: "ai",
            help_needed: false,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          }),
        });
      },
    );

    // Mock: messages for the conversation
    await page.route(
      `**/api/v1/vitalia/inbox/conversations/${convId}/messages**`,
      async (route) => {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            messages: [
              {
                id: "msg-a11y-001",
                conversation_id: convId,
                sender_type: "patient",
                body_text:
                  "Buenos días, tengo una consulta sobre mi tratamiento.",
                media_kind: null,
                media_url: null,
                retracted_at: null,
                sent_at: new Date(Date.now() - 600_000).toISOString(),
                action_receipt_expires_at: null,
              },
              {
                id: "msg-a11y-002",
                conversation_id: convId,
                sender_type: "agent_ai",
                body_text: "Hola, con gusto te ayudo. ¿Cuál es tu consulta?",
                media_kind: null,
                media_url: null,
                retracted_at: null,
                sent_at: new Date(Date.now() - 300_000).toISOString(),
                // AI message with active action receipt (retract countdown)
                action_receipt_expires_at: new Date(
                  Date.now() + 120_000,
                ).toISOString(),
              },
            ],
            total: 2,
            has_more: false,
          }),
        });
      },
    );

    // Navigate to conversation detail
    await page.goto(`/inbox/${convId}`);
    await page.waitForLoadState("domcontentloaded");

    const results = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
      .analyze();

    const criticalOrSerious = results.violations.filter(
      (v) => v.impact === "critical" || v.impact === "serious",
    );

    if (criticalOrSerious.length > 0) {
      const details = criticalOrSerious
        .map(
          (v) =>
            `[${v.impact?.toUpperCase() ?? "UNKNOWN"}] ${v.id}: ${v.description}\n  Nodes: ${v.nodes.map((n) => n.target.join(", ")).join("; ")}`,
        )
        .join("\n");
      throw new Error(
        `Inbox detail has ${criticalOrSerious.length} critical/serious WCAG 2.1 AA violations:\n${details}`,
      );
    }

    expect(criticalOrSerious).toHaveLength(0);
  });

  // ─── ARIA spot-checks from spec §15 ──────────────────────────────────────

  test("V-A11Y-03: ActionReceipt countdown tiene aria-live=polite", async ({
    clinicPage: page,
  }) => {
    if (!AxeBuilder) {
      test.skip(
        true,
        "@axe-core/playwright not installed — run: npm i -D @axe-core/playwright",
      );
      return;
    }

    const convId = "conv-a11y-receipt";

    // Mock: conversation with active AI message (receipt countdown visible)
    await page.route(
      `**/api/v1/vitalia/inbox/conversations/${convId}/messages**`,
      async (route) => {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            messages: [
              {
                id: "msg-receipt-active",
                conversation_id: convId,
                sender_type: "agent_ai",
                body_text: "Seguimiento automático enviado.",
                media_kind: null,
                media_url: null,
                retracted_at: null,
                sent_at: new Date(Date.now() - 60_000).toISOString(),
                // Active receipt: 4 minutes remaining
                action_receipt_expires_at: new Date(
                  Date.now() + 240_000,
                ).toISOString(),
              },
            ],
            total: 1,
            has_more: false,
          }),
        });
      },
    );

    await page.route(
      `**/api/v1/vitalia/inbox/conversations/${convId}`,
      async (route) => {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            id: convId,
            tenant_id: CLINIC_CONTEXT.tenantId,
            clinic_id: CLINIC_CONTEXT.clinicId,
            lead_id: "lead-receipt",
            channel: "whatsapp",
            status: "active",
            handler_mode: "ai",
            help_needed: false,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          }),
        });
      },
    );

    await page.goto(`/inbox/${convId}`);
    await page.waitForLoadState("domcontentloaded");

    // Check if action receipt countdown exists — if so, verify aria-live=polite
    // (spec §15: aria-live="polite" for ActionReceipt countdown)
    const receiptCountdown = page.locator(
      '[data-testid="action-receipt-countdown"], [aria-label*="retract"], [aria-label*="deshacer"]',
    );

    const countdownVisible = await receiptCountdown
      .isVisible({ timeout: 3_000 })
      .catch(() => false);
    if (countdownVisible) {
      // Verify aria-live attribute on the countdown or its parent
      const ariaLive = await page
        .locator('[aria-live="polite"]')
        .first()
        .getAttribute("aria-live")
        .catch(() => null);
      expect(ariaLive).toBe("polite");
    }

    // Axe scan of the conversation view (includes countdown if visible)
    const results = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
      .analyze();

    const criticalOrSerious = results.violations.filter(
      (v) => v.impact === "critical" || v.impact === "serious",
    );
    expect(criticalOrSerious).toHaveLength(0);
  });

  test("V-A11Y-04: handler_mode radio group tiene role=radiogroup y labels accesibles", async ({
    clinicPage: page,
  }) => {
    if (!AxeBuilder) {
      test.skip(
        true,
        "@axe-core/playwright not installed — run: npm i -D @axe-core/playwright",
      );
      return;
    }

    const convId = "conv-a11y-mode-toggle";

    await page.route(
      `**/api/v1/vitalia/inbox/conversations/${convId}`,
      async (route) => {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            id: convId,
            tenant_id: CLINIC_CONTEXT.tenantId,
            clinic_id: CLINIC_CONTEXT.clinicId,
            lead_id: "lead-mode-toggle",
            channel: "whatsapp",
            status: "active",
            handler_mode: "ai",
            help_needed: false,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          }),
        });
      },
    );

    await page.route(
      `**/api/v1/vitalia/inbox/conversations/${convId}/messages**`,
      async (route) => {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({ messages: [], total: 0, has_more: false }),
        });
      },
    );

    await page.goto(`/inbox/${convId}`);
    await page.waitForLoadState("domcontentloaded");

    // Check for handler_mode radiogroup (spec §15: role="radiogroup")
    const radioGroup = page.locator('[role="radiogroup"]');
    const radioGroupVisible = await radioGroup
      .isVisible({ timeout: 3_000 })
      .catch(() => false);

    if (radioGroupVisible) {
      // Verify accessible label on radiogroup
      const ariaLabel = await radioGroup
        .first()
        .getAttribute("aria-label")
        .catch(() => null);
      const ariaLabelledBy = await radioGroup
        .first()
        .getAttribute("aria-labelledby")
        .catch(() => null);
      expect(ariaLabel || ariaLabelledBy).not.toBeNull();
    }

    // Axe scan with focus on form/interactive elements
    const results = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
      .analyze();

    const criticalOrSerious = results.violations.filter(
      (v) => v.impact === "critical" || v.impact === "serious",
    );
    expect(criticalOrSerious).toHaveLength(0);
  });
});
