/**
 * wizard-onboarding.smoke.spec.ts — V-WIZ-1 thru V-WIZ-5
 *
 * Smoke tests for /onboarding/wizard page (T-onboarding-6 FE feature).
 *
 * Per e2e-testing.md: native Playwright on Linux host. Port 3002 (vitalia).
 * Authentication via Clerk testing token (auth.fixture.ts).
 *
 * Tests: golden path + close modal + empty state resilience.
 *
 * Run:
 *   cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
 *     npx playwright test e2e/specs/vitalia/wizard-onboarding.smoke.spec.ts --project=smoke
 *
 * downstream-regression-na: brand-local E2E spec; no cross-brand consumers
 */

import { test, expect } from "../../auth.fixture";
import { WizardOnboardingPage } from "../../pages/wizard-onboarding.page";

// ─── Mock API responses ───────────────────────────────────────────────────────

async function setupWizardMocks(page: import("@playwright/test").Page) {
  // Mock: start draft
  await page.route("**/api/v1/vitalia/wizard/drafts", async (route) => {
    if (route.request().method() !== "POST") {
      await route.continue();
      return;
    }
    await route.fulfill({
      status: 201,
      contentType: "application/json",
      body: JSON.stringify({
        draftId: "smoke-draft-001",
        step: "greet",
        message:
          "Hola, soy Valeria, tu asistente de configuración. ¿Comenzamos?",
        mode: null,
      }),
    });
  });

  // Mock: get draft
  await page.route(
    "**/api/v1/vitalia/wizard/drafts/smoke-draft-001",
    async (route) => {
      if (route.request().method() !== "GET") {
        await route.continue();
        return;
      }
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          draftId: "smoke-draft-001",
          status: "active",
          step: "greet",
          mode: null,
          slots: [
            {
              slotId: "clinic_name",
              label: "Nombre de la clínica",
              status: "pending",
              value: null,
              required: true,
              source: null,
              order: 1,
            },
            {
              slotId: "specialty",
              label: "Especialidad",
              status: "pending",
              value: null,
              required: true,
              source: null,
              order: 2,
            },
          ],
          progress: { confirmed: 0, total: 2, requiredRemaining: 2 },
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
        }),
      });
    },
  );

  // Mock: SSE stream (returns done immediately to avoid hanging)
  await page.route(
    "**/api/v1/vitalia/wizard/drafts/smoke-draft-001/stream**",
    async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "text/event-stream",
        body: `data: {"type":"done"}\n\n`,
      });
    },
  );

  // Mock: extract context
  await page.route(
    "**/api/v1/vitalia/wizard/drafts/smoke-draft-001/extract",
    async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          extractedSlots: [
            {
              slotId: "clinic_name",
              label: "Nombre de la clínica",
              status: "pending_confirm",
              value: "Clínica Vitalia",
              required: true,
              source: "url",
              order: 1,
            },
          ],
          assistantMessage:
            "Encontré el nombre de tu clínica: Clínica Vitalia. ¿Es correcto?",
          nextStep: "confirm",
        }),
      });
    },
  );

  // Mock: confirm slot
  await page.route(
    "**/api/v1/vitalia/wizard/drafts/smoke-draft-001/slots/*/confirm",
    async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          slot: {
            slotId: "clinic_name",
            status: "confirmed",
            value: "Clínica Vitalia",
          },
          allSlotsConfirmed: false,
          assistantMessage: "Perfecto. ¿Cuál es la especialidad de tu clínica?",
        }),
      });
    },
  );

  // Mock: simulate voice
  await page.route(
    "**/api/v1/vitalia/wizard/drafts/smoke-draft-001/simulate",
    async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          sampleText: "Hola, con gusto te ayudo a agendar una consulta.",
          agentName: "Adrián",
          scenario: "greeting_inquiry",
          fromCache: false,
          landingSnippet: {
            clinicName: "Clínica Vitalia",
            specialty: "Medicina General",
            tagline: "Cuidamos tu salud de manera integral",
            ctaText: "Agenda tu cita",
          },
        }),
      });
    },
  );
}

// ─── Tests ───────────────────────────────────────────────────────────────────

test.describe("Wizard onboarding — smoke tests (V-WIZ-1..5)", () => {
  test("V-WIZ-1: wizard page renders correctly at /onboarding/wizard", async ({
    authedPage: page,
  }) => {
    await setupWizardMocks(page);
    const wizard = new WizardOnboardingPage(page);
    await wizard.goto();
    await wizard.isReady(15_000);

    // TopBar present
    await expect(wizard.topBarTitle).toBeVisible();

    // Close button visible
    await expect(wizard.closeButton).toBeVisible();

    // Chat section accessible
    await expect(page.getByRole("application")).toBeVisible();

    // No console errors
    const errors: string[] = [];
    page.on("console", (msg) => {
      if (msg.type() === "error") errors.push(msg.text());
    });

    // Wait for draft load
    await page.waitForTimeout(2_000);
    expect(errors.filter((e) => !e.includes("favicon"))).toHaveLength(0);
  });

  test("V-WIZ-2: wizard shows initial assistant greeting message", async ({
    authedPage: page,
  }) => {
    await setupWizardMocks(page);
    const wizard = new WizardOnboardingPage(page);
    await wizard.goto();
    await wizard.isReady(15_000);

    // Wait for chat to load
    await page.waitForTimeout(2_500);

    // Greeting message from Valeria
    await expect(
      page.getByText(/hola.*valeria/i).or(page.getByText(/comenzamos/i)),
    ).toBeVisible({ timeout: 10_000 });
  });

  test("V-WIZ-3: close modal opens and cancels correctly", async ({
    authedPage: page,
  }) => {
    await setupWizardMocks(page);
    const wizard = new WizardOnboardingPage(page);
    await wizard.goto();
    await wizard.isReady(15_000);

    // Open close modal
    await wizard.openCloseModal();
    await expect(wizard.closeModal).toBeVisible();
    await expect(page.getByText("¿Cerrar el asistente?")).toBeVisible();
    await expect(page.getByText(/avances se guardan/i)).toBeVisible();

    // Cancel — modal should close
    await wizard.cancelClose();
    await expect(wizard.closeModal).not.toBeVisible();
  });

  test("V-WIZ-4: Escape key closes the warning modal", async ({
    authedPage: page,
  }) => {
    await setupWizardMocks(page);
    const wizard = new WizardOnboardingPage(page);
    await wizard.goto();
    await wizard.isReady(15_000);

    // Open close modal
    await wizard.openCloseModal();
    await expect(wizard.closeModal).toBeVisible();

    // Press Escape
    await page.keyboard.press("Escape");
    await expect(wizard.closeModal).not.toBeVisible();
  });

  test("V-WIZ-5: live preview panel visible on desktop viewport", async ({
    authedPage: page,
  }) => {
    await page.setViewportSize({ width: 1280, height: 800 });
    await setupWizardMocks(page);
    const wizard = new WizardOnboardingPage(page);
    await wizard.goto();
    await wizard.isReady(15_000);

    // Right panel should be visible on desktop (md:flex)
    await expect(wizard.previewSection).toBeVisible({ timeout: 10_000 });
  });
});
