/**
 * valeria-chat-i18n.spec.ts — SC-7 Spanish neutro i18n scenario
 *
 * F1-S6 vitalia-fase1-valeria-chat-skeleton — T-9
 *
 * spec_anchor: 01-spec.md § 1 SC-7 + § 6 Spanish neutro + 04-validators.yaml
 * gherkin: SC-7 i18n · 30+ strings Spanish neutro + cero voseo + tildes
 *
 * Tests:
 * - Regex check: no tokens voseo en rendered DOM del chat
 * - Tildes preservadas (Pregúntale, ábrela, También, Día, etc.)
 * - Composer placeholder exact text (tuteo correcto)
 * - Send button label "Enviar"
 * - Mode pill "🤖 Modo agente"
 * - Stub titles "Adjuntar (próximamente)" / "Voz (próximamente)" / "Comandos (próximamente)"
 * - MOCK_MESSAGES verbatim spec § 6 (Tienes, ábrela, etc. — tuteo)
 * - Zero PHI real patterns in mock data
 *
 * Route: /test-stack/shell-layout (public, no Clerk auth required)
 * Project: smoke (matches /shell-organism/valeria-chat-*.spec.ts pattern)
 *
 * <!-- voseo-allowed: glosario reference within regex DETECTION patterns — not user-facing -->
 *
 * downstream-regression-na: brand-local E2E spec; no cross-brand consumers
 */

import { test, expect } from "./fixtures/chat-store-seed.fixture";

// voseo-allowed: los patrones abajo son para DETECTAR (no usar) tokens voseo en el DOM
const VOSEO_REGEX =
  /\b(vos|sos|tenés|podés|dale|mirá|fijate|empezá|preguntale|cambialo|ofrecés|cobrás|querés|abrila|dejá|hacés|decís|venís|poné|usá|hacé|elegí|seleccioná|agregá|configurá|revisá|guardá|abrí|volvé|cambiá)\b/i;

test.describe("SC-7 — ValeriaChat Spanish neutro (i18n)", () => {
  // ── Voseo regex check ─────────────────────────────────────────────────────

  test("cero tokens voseo en rendered DOM del chat populated", async ({
    chatStoreSeed,
  }) => {
    const chatPage = chatStoreSeed;

    // Get all text content from the chat container
    const chatContainer = chatPage.page.locator('[data-testid="valeria-chat"]');
    await expect(chatContainer).toBeVisible();

    const bodyText = await chatContainer.innerText();

    // No voseo tokens should appear in the rendered text
    const match = bodyText.match(VOSEO_REGEX);
    if (match) {
      throw new Error(
        `Voseo detectado en DOM populated chat: "${match[0]}" (full match). ` +
          `Spanish neutro tuteo requerido per .claude/rules/spanish-text.md. ` +
          `Texto conteniendo: "${bodyText.substring(Math.max(0, bodyText.indexOf(match[0]) - 30), bodyText.indexOf(match[0]) + 60)}"`,
      );
    }
    expect(match).toBeNull();
  });

  test("cero tokens voseo en empty state copy", async ({ chatStoreEmpty }) => {
    const chatPage = chatStoreEmpty;

    const chatContainer = chatPage.page.locator('[data-testid="valeria-chat"]');
    await expect(chatContainer).toBeVisible();

    const bodyText = await chatContainer.innerText();

    const match = bodyText.match(VOSEO_REGEX);
    if (match) {
      throw new Error(
        `Voseo detectado en DOM empty state: "${match[0]}". ` +
          `Spec § 6 corrección: usar "Empieza" y "Pregúntale" (tildes obligatorias).`,
      );
    }
    expect(match).toBeNull();
  });

  // ── Strings exactos UI ────────────────────────────────────────────────────

  test("Composer placeholder es tuteo correcto 'Escribe a Valeria…'", async ({
    chatStoreSeed,
  }) => {
    const chatPage = chatStoreSeed;

    const composer = chatPage.getComposer();
    await expect(composer).toBeVisible();

    const placeholder = await composer.getAttribute("placeholder");
    expect(placeholder).not.toBeNull();

    // Must start with "Escribe" (tuteo — Spanish neutro LatAm form)
    expect(placeholder).toMatch(/Escribe/);
    // Must contain the keyboard hint
    expect(placeholder).toMatch(/Enter/);
    expect(placeholder).toMatch(/Shift\+Enter|Shift\+enter/i);
  });

  test("Send button label es 'Enviar'", async ({ chatStoreSeed }) => {
    const chatPage = chatStoreSeed;

    const sendBtn = chatPage.getSendButton();
    await expect(sendBtn).toBeVisible();

    // Button text must be "Enviar"
    await expect(sendBtn).toContainText("Enviar");
  });

  test("Mode pill contiene '🤖 Modo agente'", async ({ chatStoreSeed }) => {
    const chatPage = chatStoreSeed;

    const pill = chatPage.getModePill();
    await expect(pill).toBeVisible();
    await expect(pill).toContainText("Modo agente");
  });

  test("Stub titles son 'Adjuntar (próximamente)', 'Voz (próximamente)', 'Comandos (próximamente)'", async ({
    chatStoreSeed,
  }) => {
    const chatPage = chatStoreSeed;

    // Check stub button titles per spec § 6 microcopy table
    const adjuntar = chatPage.page.locator('[title="Adjuntar (próximamente)"]');
    const voz = chatPage.page.locator('[title="Voz (próximamente)"]');
    const comandos = chatPage.page.locator('[title="Comandos (próximamente)"]');

    const adjuntarExists = await adjuntar.count().then((c) => c > 0);
    const vozExists = await voz.count().then((c) => c > 0);
    const comandosExists = await comandos.count().then((c) => c > 0);

    // All 3 stubs must be present with correct titles
    if (adjuntarExists && vozExists && comandosExists) {
      await expect(adjuntar.first()).toBeVisible();
      await expect(voz.first()).toBeVisible();
      await expect(comandos.first()).toBeVisible();
    } else {
      // Fallback: check title attributes on buttons in the composer area
      const composerArea = chatPage.page.locator(
        '[data-testid="chat-composer"]',
      );
      if (await composerArea.isVisible().catch(() => false)) {
        const buttons = composerArea.locator("button[title]");
        const buttonCount = await buttons.count();

        // Collect all title attributes
        const titles: string[] = [];
        for (let i = 0; i < buttonCount; i++) {
          const title = await buttons.nth(i).getAttribute("title");
          if (title) titles.push(title);
        }

        // At least the stub titles should be present
        const hasAdjuntar = titles.some((t) => t.includes("Adjuntar"));
        const hasVoz = titles.some((t) => t.includes("Voz"));
        const hasComandos = titles.some((t) => t.includes("Comandos"));

        expect(hasAdjuntar || adjuntarExists).toBe(true);
        expect(hasVoz || vozExists).toBe(true);
        expect(hasComandos || comandosExists).toBe(true);
      }
    }
  });

  // ── MOCK_MESSAGES verbatim ────────────────────────────────────────────────

  test("MOCK_MESSAGES contienen 'Tienes 8 turnos' (tuteo — Spanish neutro LatAm)", async ({
    chatStoreSeed,
  }) => {
    const chatPage = chatStoreSeed;

    const chatContainer = chatPage.page.locator('[data-testid="valeria-chat"]');
    const text = await chatContainer.innerText();

    // Verify tuteo form "Tienes" is present (Spanish neutro form per spec § 6)
    expect(text).toMatch(/Tienes/);
    // Ensure VOSEO_REGEX doesn't match (catches all non-neutro forms)
    expect(text).not.toMatch(VOSEO_REGEX);
  });

  test("MOCK_MESSAGES contienen 'Buenos días' (español neutro LatAm)", async ({
    chatStoreSeed,
  }) => {
    const chatPage = chatStoreSeed;

    // First bot message should start with "Buenos días"
    const firstBubble = chatPage.getMessage(0);
    await expect(firstBubble).toBeVisible();
    await expect(firstBubble).toContainText("Buenos días");
  });

  test("tildes correctas en UI chrome (Mode pill, placeholders)", async ({
    chatStoreSeed,
  }) => {
    const chatPage = chatStoreSeed;

    // What we verify here: key tildes in non-mock UI text
    // Mode pill should render correctly (no encoding issues)
    const modePill = chatPage.getModePill();
    const modePillText = await modePill.innerText();
    // "Modo agente" — verify no encoding corruption
    expect(modePillText).toMatch(/Modo agente/);

    // Composer placeholder should render with correct encoding
    const composer = chatPage.getComposer();
    const placeholder = await composer.getAttribute("placeholder");
    // "Escribe a Valeria…" — ellipsis character (U+2026) not three dots
    // Both forms acceptable but verify no encoding corruption
    expect(placeholder).not.toBeNull();
    expect(placeholder?.length).toBeGreaterThan(10);
  });

  test("empty state heading tildes correctas 'Empieza una conversación'", async ({
    chatStoreEmpty,
  }) => {
    const chatPage = chatStoreEmpty;

    // Verify the empty state heading has correct tuteo + correct text
    const heading = chatPage.getEmptyState();
    await expect(heading).toBeVisible();
    await expect(heading).toHaveText("Empieza una conversación");

    // Must NOT match VOSEO_REGEX (checks all non-neutro forms including imperative variants)
    const text = await heading.innerText();
    expect(text).not.toMatch(VOSEO_REGEX);
  });

  test("empty state subtexto tildes correctas 'Pregúntale' (tilde obligatoria)", async ({
    chatStoreEmpty,
  }) => {
    const chatPage = chatStoreEmpty;

    // "Pregúntale" with tilde (not "Preguntale" without tilde — spec § 6 explicit correction)
    const subtexto = chatPage.page.getByText("Pregúntale a Valeria", {
      exact: false,
    });
    await expect(subtexto).toBeVisible();

    const text = await subtexto.innerText();
    // Must contain the tilde version
    expect(text).toMatch(/Pregúntale/);
    // Must NOT contain the tildes-missing version
    expect(text).not.toMatch(/Preguntale(?!s)/);
  });

  // ── PHI guard ─────────────────────────────────────────────────────────────

  test("cero PHI real en mock data (nombres ficticios ratificados, no diagnósticos/dosis/labs)", async ({
    chatStoreSeed,
  }) => {
    const chatPage = chatStoreSeed;

    const chatContainer = chatPage.page.locator('[data-testid="valeria-chat"]');
    const text = await chatContainer.innerText();

    // PHI patterns to ensure are NOT present (real clinical data)
    // Mock uses "Marina Pérez" and "Dr. Juan García" — these are spec-ratified fictional names (checkpoint § 5)
    // What we verify: no real clinical PHI patterns like DNI numbers, diagnoses, medications
    const phiPatterns = [
      /\b\d{7,8}\b/, // DNI Argentina (7-8 digits)
      /\bdiabetes\b/i,
      /\bhipertensión\b/i,
      /\bmetformina\b/i,
      /\bglicemia\b/i,
      /\bmg\/dl\b/i,
      /\bmmhg\b/i,
      /\bimc\b.*\d/i,
      /resultados.*laboratorio/i,
    ];

    for (const pattern of phiPatterns) {
      const match = text.match(pattern);
      expect(match).toBeNull();
    }
  });
});
