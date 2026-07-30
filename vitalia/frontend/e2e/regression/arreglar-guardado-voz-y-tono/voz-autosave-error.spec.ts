/**
 * voz-autosave-error.spec.ts — SC-5 Network failure: badge error state (error injection)
 *
 * Gherkin scenario: autosave-error-muestra-badge
 *
 * Given:  Owner en Voz y tono; el PATCH /personality responde 503 (falla inyectada)
 * When:   Cambia arquetipo y dispara autosave
 * Then:   Badge muestra estado 'error' · UI no crashea · el usuario puede reintentar
 *
 * NOTA: este spec INYECTA una falla 503 en el PATCH (error-path deliberado), NO
 * mockea el backend-bajo-prueba happy-path. El GET /personality va al backend
 * REAL (las cards hidratan con datos reales). Como ejerce un error a propósito,
 * el gate anti-burbuja se apaga con `failOnRuntimeError: false`.
 *
 * Transporte honesto (auth + forwarding GET → :8002 + base.ts) se compone desde
 * `real-backend-forward.fixture`; el spec registra el 503 en PATCH con prioridad
 * (las rutas registradas en el test corren ANTES que el forwarding del fixture)
 * y usa `route.fallback()` en los métodos que no inyecta, para que GET forwardee.
 *
 * Run:
 *   cd vitalia/frontend
 *   E2E_BASE_URL=http://localhost:3002 npx playwright test --project=smoke \
 *     e2e/regression/arreglar-guardado-voz-y-tono/voz-autosave-error.spec.ts
 *
 * downstream-regression-na: brand-local vitalia e2e spec arreglar-guardado-voz-y-tono
 *
 * @see e2e/fixtures/real-backend-forward.fixture.ts
 * @see 06-tickets.yaml T-1 deliverable 6
 * @see 01-spec.md § autosave-error-muestra-badge
 */

import {
  test as authTest,
  expect,
  TENANT_ID,
} from "../../fixtures/real-backend-forward.fixture";
import type { Route } from "@playwright/test";
import { VozTonoSectionPom } from "./poms/voz-tono-section.pom";

// El gate anti-burbuja se apaga para toda la suite: estos tests ejercen un error
// (503 inyectado + 4xx/5xx en /api/) a propósito.
authTest.use({ failOnRuntimeError: false });

// ---------------------------------------------------------------------------
// Helper: inject 503 on PATCH personality; GET (y demás) → backend real.
// route.fallback() delega al siguiente handler (el forwarding del fixture).
// ---------------------------------------------------------------------------

async function injectPersonalityPatch503(page: import("@playwright/test").Page): Promise<void> {
  await page.route(
    "**/api/v1/lisa/marca/personality",
    async (route: Route) => {
      if (route.request().method() === "PATCH") {
        await route.fulfill({
          status: 503,
          contentType: "application/json",
          body: JSON.stringify({ detail: "Service Unavailable" }),
        });
      } else {
        // GET (y otros) → delegar al forwarding del fixture → backend real.
        await route.fallback();
      }
    },
  );
}

/** Wait until voz-y-tono renders the interactive section root. */
async function waitForVozTonoInteractive(
  page: import("@playwright/test").Page,
  timeoutMs = 20_000,
): Promise<void> {
  await page
    .locator('[data-testid="voz-tono-section-root"]')
    .first()
    .waitFor({ state: "visible", timeout: timeoutMs });
}

// ---------------------------------------------------------------------------
// Test suite — SC-5 network failure / error state
// ---------------------------------------------------------------------------

authTest.describe("SC-5 — Network failure: badge muestra error (503 inyectado en PATCH)", () => {
  // DES-QUARANTINED (estabilizar-harness-e2e-lisa-marca): el error-path se asserta
  // web-first (waitForAutosaveError + toBeVisible) sobre el GET real hidratado.
  authTest(
    "PATCH personality 503 → badge 'error', UI no crashea",
    async ({ authedPage }) => {
      const pom = new VozTonoSectionPom(authedPage, TENANT_ID);

      await injectPersonalityPatch503(authedPage);

      await pom.goto();
      await waitForVozTonoInteractive(authedPage);

      // Switch to a target different from current to force the PATCH (→ 503).
      const initial = await pom.getSelectedArchetype();
      const target = initial === "sage" ? "healer" : "sage";
      await pom.selectArchetype(target);

      // Web-first: badge reaches error after the 503.
      await pom.waitForAutosaveError();

      // UI did not crash — archetype selector remains visible.
      await expect(
        authedPage
          .locator('[data-testid="voz-tono-section-root"]')
          .first()
          .locator('[data-testid="archetype-selector"]'),
        "UI must not crash after autosave error — archetype selector must remain",
      ).toBeVisible();

      // Error boundary must NOT be visible (graceful error, only badge).
      await expect(
        authedPage.locator('[data-testid="error-boundary-fallback"]'),
        "Error boundary must NOT appear for autosave error (only badge)",
      ).toHaveCount(0);

      // Badge text shows error copy (Spanish neutro).
      const badgeText = await pom.getAutosaveBadgeText();
      expect(
        badgeText,
        "Badge must show error copy in Spanish neutro",
      ).toMatch(/no se pudo guardar|error|reintenta/i);
    },
  );

  // DES-QUARANTINED: retry path — tras error, el próximo cambio re-dispara autosave.
  authTest(
    "tras error, el próximo cambio re-dispara el autosave (reintento posible)",
    async ({ authedPage }) => {
      const pom = new VozTonoSectionPom(authedPage, TENANT_ID);

      // Phase 1: PATCH → 503.
      await injectPersonalityPatch503(authedPage);
      await pom.goto();
      await waitForVozTonoInteractive(authedPage);

      const initial = await pom.getSelectedArchetype();
      const firstTarget = initial === "sage" ? "healer" : "sage";
      await pom.selectArchetype(firstTarget);
      await pom.waitForAutosaveError();

      // Phase 2: clear the 503 route → PATCH forwards to the real backend.
      await authedPage.unroute("**/api/v1/lisa/marca/personality");

      // A new change re-triggers autosave; the real PATCH now succeeds.
      const secondTarget = firstTarget === "sage" ? "healer" : "sage";
      await pom.selectArchetype(secondTarget);
      await pom.waitForAutosaveSaved();
    },
  );

  // DES-QUARANTINED: UI stays interactive during/after the autosave error.
  authTest(
    "UI permanece interactiva durante y después de error de autosave",
    async ({ authedPage }) => {
      const pom = new VozTonoSectionPom(authedPage, TENANT_ID);

      await injectPersonalityPatch503(authedPage);
      await pom.goto();
      await waitForVozTonoInteractive(authedPage);

      const initial = await pom.getSelectedArchetype();
      const target = initial === "sage" ? "healer" : "sage";
      await pom.selectArchetype(target);
      await pom.waitForAutosaveError();

      // Assert interactivity via stable elements (section root + badge + textarea).
      const sectionFirst = authedPage
        .locator('[data-testid="voz-tono-section-root"]')
        .first();
      await expect(
        sectionFirst,
        "Section root must remain visible after error (UI no crasheó)",
      ).toBeVisible();

      await expect(
        authedPage.locator('[data-testid="autosave-badge"]').first(),
        "Autosave badge must remain visible (error surfaced gracefully)",
      ).toBeVisible();

      const voiceTextarea = sectionFirst
        .locator('[data-testid="tone-block-asi-hablo-textarea"]')
        .first();
      await expect(
        voiceTextarea,
        "Voice block textarea must remain editable after autosave error",
      ).toBeEditable();

      await expect(
        authedPage.locator('[data-testid="error-boundary-fallback"]'),
        "Error boundary must NOT appear for autosave error (only badge)",
      ).toHaveCount(0);
    },
  );
});
