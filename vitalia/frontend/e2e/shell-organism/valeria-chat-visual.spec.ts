/**
 * valeria-chat-visual.spec.ts — Visual golden snapshots (4 PNGs)
 *
 * F1-S6 vitalia-fase1-valeria-chat-skeleton — T-9
 *
 * spec_anchor: 01-spec.md § 12 visual gate · 04-validators.yaml § visual
 * gherkin: (visual) 4 PNG snapshots populated/empty × light/dark @ 1280×800
 *
 * Visual matrix:
 *   1. valeria-chat-populated-light — 6 MOCK_MESSAGES + light theme
 *   2. valeria-chat-populated-dark  — 6 MOCK_MESSAGES + dark theme
 *   3. valeria-chat-empty-light     — messages=[] + light theme
 *   4. valeria-chat-empty-dark      — messages=[] + dark theme
 *
 * Golden generation (first run ONLY):
 *   cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
 *     npx playwright test --project=visual --update-snapshots \
 *     e2e/shell-organism/valeria-chat-visual.spec.ts
 *
 * Subsequent runs validate pixel diff (maxDiffPixelRatio: 0.01 — 1% tolerance).
 *
 * PRE-CONDITION (per 06-tickets.yaml T-9 notes):
 * Chris must validate the side-by-side comparison (React component vs
 * valeria-chat-sample.html mockup) BEFORE running --update-snapshots.
 * Ratchet enforced: once goldens are generated and committed, any
 * modification requires explicit Chris re-ratification.
 *
 * Route: /test-stack/shell-layout (public, no Clerk auth required)
 * Viewport: 1280×800 canonical desktop (per spec § 13 deliverables matrix)
 *
 * NOTE: This spec requires the `--project=visual` flag to use
 * snapshotPathTemplate and maxDiffPixelRatio from playwright.config.ts.
 * Without the visual project config, toHaveScreenshot() may look in
 * the wrong path for baseline PNGs.
 *
 * Run: E2E_BASE_URL=http://localhost:3002 npx playwright test \
 *      --project=visual e2e/shell-organism/valeria-chat-visual.spec.ts
 *
 * downstream-regression-na: brand-local visual goldens; no cross-brand consumers
 */

import { test, expect } from "@playwright/test";
import type { ChatMessage } from "../../../src/stores/chat-store";
import { ValeriaChatPage } from "./poms/valeria-chat-page.pom";

// ── MOCK_MESSAGES inline (SSoT: src/components/shared/shell-organism/_mock-messages.ts) ──
// Duplicated here because Playwright's Node process cannot `require()` TypeScript source files
// with path aliases (e.g. @/lib/...) at test-collection time. The fixture uses the same data
// but loads via the extended test mechanism which handles TS transpilation differently.
// Keep in sync with _mock-messages.ts — changes there must be reflected here.
// spec_anchor: 01-spec.md § 5.3 · 03-arch.md § 2.6 · 06-tickets.yaml T-9 visual matrix
const MOCK_MESSAGES: ChatMessage[] = [
  {
    id: "1",
    role: "bot",
    agent: "valeria",
    content:
      "¡Buenos días! Tienes 8 turnos hoy y 3 pacientes esperando confirmar mañana. ¿Por dónde empezamos?",
    time: "09:01",
  },
  {
    id: "2",
    role: "user",
    content: "¿Cómo están las reseñas Google esta semana?",
    time: "09:02",
  },
  {
    id: "3",
    role: "delegate",
    fromAgent: "valeria",
    toAgent: "camila",
    delegateMode: "Mantener",
  },
  {
    id: "4",
    role: "bot",
    agent: "camila",
    content:
      "Esta semana ingresaron +3 reseñas Google (2 de 5★ y 1 de 4★). El score subió de 4.6 a 4.7. Hay una reseña destacable de Marina Pérez sobre Dr. Juan García que sugiero pinear en landing. ¿La abro?",
    time: "09:02",
  },
  {
    id: "5",
    role: "user",
    content: "Sí, ábrela.",
    time: "09:03",
  },
  {
    id: "6",
    role: "thinking",
    agent: "camila",
    content: "Camila está abriendo Voz del paciente…",
  },
];

// Canonical desktop viewport for golden snapshots (spec § 13 deliverables matrix)
const GOLDEN_VIEWPORT = { width: 1280, height: 800 };

// Helper to ensure light theme state before screenshot
async function ensureLightTheme(chatPage: ValeriaChatPage): Promise<void> {
  await chatPage.page.evaluate(() => {
    document.documentElement.classList.remove("dark");
    localStorage.setItem("vitalia-theme", "light");
  });
  // Wait for theme application
  await chatPage.page.waitForTimeout(200);
}

// Helper to ensure dark theme state before screenshot
async function ensureDarkTheme(chatPage: ValeriaChatPage): Promise<void> {
  await chatPage.page.evaluate(() => {
    document.documentElement.classList.add("dark");
    localStorage.setItem("vitalia-theme", "dark");
  });
  await chatPage.page.waitForTimeout(200);
}

// Helper to disable animations for deterministic screenshots
async function disableAnimations(chatPage: ValeriaChatPage): Promise<void> {
  await chatPage.page.addStyleTag({
    content: `
      *, *::before, *::after {
        animation-duration: 0s !important;
        animation-delay: 0s !important;
        transition-duration: 0s !important;
        transition-delay: 0s !important;
      }
    `,
  });
}

test.describe("Visual goldens — ValeriaChat 4 PNG snapshots (1280×800)", () => {
  // ── Populated state × light ────────────────────────────────────────────────

  test("valeria-chat populated light golden (6 mensajes + light theme)", async ({
    page,
  }) => {
    const chatPage = new ValeriaChatPage(page);

    // Set viewport to canonical golden size
    await chatPage.setViewport(GOLDEN_VIEWPORT.width, GOLDEN_VIEWPORT.height);

    // Seed with MOCK_MESSAGES BEFORE navigation (addInitScript requirement)
    await chatPage.seedChatStore(MOCK_MESSAGES);

    // Set shell state to agentic/full + light theme before navigation
    await page.addInitScript(() => {
      localStorage.setItem(
        "vitalia-shell-state",
        JSON.stringify({
          state: { shellMode: "agentic", valeriaState: "full" },
          version: 0,
        }),
      );
      localStorage.setItem("vitalia-theme", "light");
    });

    await page.goto("/test-stack/shell-layout");
    await page
      .locator('[data-testid="valeria-chat"]')
      .waitFor({ state: "visible", timeout: 15_000 });

    // Ensure light mode + disable animations for deterministic PNG
    await ensureLightTheme(chatPage);
    await disableAnimations(chatPage);

    // Wait for all images and fonts to load
    await page.waitForLoadState("networkidle");

    // Take golden screenshot of the entire chat organism
    const chatContainer = page.locator('[data-testid="valeria-chat"]');
    await expect(chatContainer).toHaveScreenshot(
      "valeria-chat-populated-light-1280x800.png",
      {
        maxDiffPixelRatio: 0.01,
        animations: "disabled",
        caret: "hide",
      },
    );
  });

  // ── Populated state × dark ─────────────────────────────────────────────────

  test("valeria-chat populated dark golden (6 mensajes + dark theme)", async ({
    page,
  }) => {
    const chatPage = new ValeriaChatPage(page);

    await chatPage.setViewport(GOLDEN_VIEWPORT.width, GOLDEN_VIEWPORT.height);

    await chatPage.seedChatStore(MOCK_MESSAGES);

    // Set shell state to agentic/full + dark theme before navigation
    await page.addInitScript(() => {
      localStorage.setItem(
        "vitalia-shell-state",
        JSON.stringify({
          state: { shellMode: "agentic", valeriaState: "full" },
          version: 0,
        }),
      );
      localStorage.setItem("vitalia-theme", "dark");
    });

    await page.goto("/test-stack/shell-layout");
    await page
      .locator('[data-testid="valeria-chat"]')
      .waitFor({ state: "visible", timeout: 15_000 });

    // Ensure dark mode
    await ensureDarkTheme(chatPage);
    await disableAnimations(chatPage);
    await page.waitForLoadState("networkidle");

    const chatContainer = page.locator('[data-testid="valeria-chat"]');
    await expect(chatContainer).toHaveScreenshot(
      "valeria-chat-populated-dark-1280x800.png",
      {
        maxDiffPixelRatio: 0.01,
        animations: "disabled",
        caret: "hide",
      },
    );
  });

  // ── Empty state × light ────────────────────────────────────────────────────

  test("valeria-chat empty light golden (messages=[] + light theme)", async ({
    page,
  }) => {
    const chatPage = new ValeriaChatPage(page);

    await chatPage.setViewport(GOLDEN_VIEWPORT.width, GOLDEN_VIEWPORT.height);

    // Seed empty messages BEFORE navigation
    await chatPage.seedChatStoreEmpty();

    await page.addInitScript(() => {
      localStorage.setItem(
        "vitalia-shell-state",
        JSON.stringify({
          state: { shellMode: "agentic", valeriaState: "full" },
          version: 0,
        }),
      );
      localStorage.setItem("vitalia-theme", "light");
    });

    await page.goto("/test-stack/shell-layout");
    await page
      .locator('[data-testid="valeria-chat"]')
      .waitFor({ state: "visible", timeout: 15_000 });

    await ensureLightTheme(chatPage);
    await disableAnimations(chatPage);
    await page.waitForLoadState("networkidle");

    const chatContainer = page.locator('[data-testid="valeria-chat"]');
    await expect(chatContainer).toHaveScreenshot(
      "valeria-chat-empty-light-1280x800.png",
      {
        maxDiffPixelRatio: 0.01,
        animations: "disabled",
        caret: "hide",
      },
    );
  });

  // ── Empty state × dark ─────────────────────────────────────────────────────

  test("valeria-chat empty dark golden (messages=[] + dark theme)", async ({
    page,
  }) => {
    const chatPage = new ValeriaChatPage(page);

    await chatPage.setViewport(GOLDEN_VIEWPORT.width, GOLDEN_VIEWPORT.height);

    await chatPage.seedChatStoreEmpty();

    await page.addInitScript(() => {
      localStorage.setItem(
        "vitalia-shell-state",
        JSON.stringify({
          state: { shellMode: "agentic", valeriaState: "full" },
          version: 0,
        }),
      );
      localStorage.setItem("vitalia-theme", "dark");
    });

    await page.goto("/test-stack/shell-layout");
    await page
      .locator('[data-testid="valeria-chat"]')
      .waitFor({ state: "visible", timeout: 15_000 });

    await ensureDarkTheme(chatPage);
    await disableAnimations(chatPage);
    await page.waitForLoadState("networkidle");

    const chatContainer = page.locator('[data-testid="valeria-chat"]');
    await expect(chatContainer).toHaveScreenshot(
      "valeria-chat-empty-dark-1280x800.png",
      {
        maxDiffPixelRatio: 0.01,
        animations: "disabled",
        caret: "hide",
      },
    );
  });
});
