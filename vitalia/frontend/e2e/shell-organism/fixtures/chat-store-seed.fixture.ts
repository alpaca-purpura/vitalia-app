/**
 * chat-store-seed.fixture.ts — Playwright fixtures para ValeriaChat E2E suite
 *
 * F1-S6 vitalia-fase1-valeria-chat-skeleton — T-7
 *
 * spec_anchor: 04-validators.yaml § fixtures_required[0] · 03-arch.md § 3.2
 *
 * Provee tres fixtures base:
 * - chatPage: ValeriaChatPage POM instance (no seed — caller decide qué semilla usar)
 * - chatStoreSeed: POM pre-seeded con MOCK_MESSAGES (6 mensajes, IDs estables '1'..'6')
 * - chatStoreEmpty: POM pre-seeded con [] (empty state)
 *
 * Patrón: extend base `test` de Playwright (no depende de auth.fixture —
 * la ruta `/test-stack/shell-layout` es pública, sin Clerk). Si en el futuro
 * algún spec necesita auth, componer con auth.fixture explícitamente.
 *
 * Seed mechanism:
 * - `page.addInitScript` corre ANTES de que los scripts de la página inicialicen
 * - chat-store.ts lee `window.__chatStoreSeed__` en non-prod y lo usa para
 *   hidratar los mensajes iniciales en lugar de MOCK_MESSAGES
 * - Permite control determinístico del estado inicial sin tocar el store en runtime
 *
 * Spanish neutro LatAm: strings en user-facing content de MOCK_MESSAGES.
 * Esta fixture solo orquesta seed — no contiene strings UI directos.
 *
 * downstream-regression-na: brand-local E2E fixture; no cross-brand consumers
 */

import { test as base } from "@playwright/test";
import type { ChatMessage } from "../../../src/stores/chat-store";
import { MOCK_MESSAGES } from "../../../src/components/shared/shell-organism/_mock-messages";
import { ValeriaChatPage } from "../poms/valeria-chat-page.pom";

// ---------------------------------------------------------------------------
// Fixture type definitions
// ---------------------------------------------------------------------------

interface ChatFixtures {
  /**
   * ValeriaChatPage POM instance sin seed pre-aplicado.
   * Caller puede invocar seedChatStore() / seedChatStoreEmpty() antes de goto().
   */
  chatPage: ValeriaChatPage;

  /**
   * ValeriaChatPage POM pre-seeded con MOCK_MESSAGES (6 mensajes, IDs '1'..'6').
   * Lista determinística — garantiza snapshots Playwright estables.
   * Fixture ya navega a la ruta y espera que el chat sea visible.
   */
  chatStoreSeed: ValeriaChatPage;

  /**
   * ValeriaChatPage POM pre-seeded con [] (array vacío).
   * Renderiza empty state: "Empieza una conversación".
   * Fixture ya navega a la ruta y espera que el chat sea visible.
   */
  chatStoreEmpty: ValeriaChatPage;
}

// ---------------------------------------------------------------------------
// Fixture implementations
// ---------------------------------------------------------------------------

export const test = base.extend<ChatFixtures>({
  /**
   * chatPage — POM sin seed.
   * No navega — caller controla seed + goto().
   */
  chatPage: async ({ page }, use) => {
    const pom = new ValeriaChatPage(page);
    await use(pom);
  },

  /**
   * chatStoreSeed — POM pre-seeded con MOCK_MESSAGES.
   * Seed se aplica via addInitScript ANTES de la navegación.
   * Fixture navega y espera visibilidad del chat.
   */
  chatStoreSeed: async ({ page }, use) => {
    const pom = new ValeriaChatPage(page);
    // addInitScript DEBE llamarse antes de goto()
    await pom.seedChatStore(MOCK_MESSAGES as unknown as ChatMessage[]);
    await pom.goto();
    await use(pom);
  },

  /**
   * chatStoreEmpty — POM pre-seeded con array vacío.
   * Fixture navega y espera visibilidad del chat.
   */
  chatStoreEmpty: async ({ page }, use) => {
    const pom = new ValeriaChatPage(page);
    // addInitScript DEBE llamarse antes de goto()
    await pom.seedChatStoreEmpty();
    await pom.goto();
    await use(pom);
  },
});

// Re-export expect for convenience in spec files
export { expect } from "@playwright/test";
