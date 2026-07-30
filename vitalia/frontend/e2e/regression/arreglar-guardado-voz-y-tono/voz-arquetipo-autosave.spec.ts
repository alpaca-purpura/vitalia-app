/**
 * voz-arquetipo-autosave.spec.ts — SC-1 Happy path: arquetipo autosave (real backend)
 *
 * Gherkin scenario: voz-arquetipo-autosave-persiste
 *
 * Given:  Owner autenticado en Lisa › Marca › Voz y tono
 * When:   Cambia arquetipo a 'Sage'; transcurre el debounce 600ms del autosave
 * Then:   Badge saving→saved (NUNCA 'error') · PATCH responde 200 · recarga persiste
 *
 * IMPORTANT: backend REAL (sin mock del backend-bajo-prueba). El forwarding +
 * auth + gate anti-burbuja se componen desde `real-backend-forward.fixture`
 * (LIFT del inline previo). El bug shippeó porque el test viejo mockeaba la API
 * → verde falso. Doctrina: "verificado = ejercer la acción real + observar el
 * efecto + leer logs" (test-design-doctrine.md § Verificación REAL ≠ "HTTP 200").
 *
 * Stack required: backend :8002 + frontend :3002 UP (make dev-vitalia).
 *
 * Run:
 *   cd vitalia/frontend
 *   E2E_BASE_URL=http://localhost:3002 npx playwright test --project=smoke \
 *     e2e/regression/arreglar-guardado-voz-y-tono/voz-arquetipo-autosave.spec.ts
 *
 * downstream-regression-na: brand-local vitalia e2e spec arreglar-guardado-voz-y-tono
 *
 * @see e2e/fixtures/real-backend-forward.fixture.ts (transporte honesto + anti-burbuja)
 * @see 06-tickets.yaml T-1 deliverable 6
 * @see 01-spec.md § voz-arquetipo-autosave-persiste
 */

import {
  test as authTest,
  expect,
  TENANT_ID,
} from "../../fixtures/real-backend-forward.fixture";
import { VozTonoSectionPom } from "./poms/voz-tono-section.pom";

// ---------------------------------------------------------------------------
// Test suite — SC-1 arquetipo autosave with real backend
// ---------------------------------------------------------------------------

authTest.describe("SC-1 — Arquetipo autosave (backend real, sin mock PATCH)", () => {
  authTest(
    "cambio de arquetipo a Sage: badge saving→saved, PATCH 200 (no 500)",
    async ({ authedPage }) => {
      const pom = new VozTonoSectionPom(authedPage, TENANT_ID);

      await pom.goto();
      await pom.waitForLoaded();

      // Capture outgoing PATCH responses — we do NOT mock them (real backend).
      const patchRequests: { status: number; body: Record<string, unknown> }[] =
        [];
      // Web-first capture via a typed listener; cleaned up at test end (RN-4).
      const onResponse = (response: import("@playwright/test").Response) => {
        if (
          response.url().includes("/api/v1/lisa/marca/personality") &&
          response.request().method() === "PATCH"
        ) {
          response
            .json()
            .then((body: unknown) => {
              patchRequests.push({
                status: response.status(),
                body: body as Record<string, unknown>,
              });
            })
            .catch(() => {
              // Non-JSON body (e.g. error page) — record status only.
              patchRequests.push({ status: response.status(), body: {} });
            });
        }
      };
      authedPage.on("response", onResponse);

      // Initial archetype is whatever the real DB has (varies per run). Switch
      // to a deterministically-different target so the change is observable.
      const initialArchetype = await pom.getSelectedArchetype();
      const archetypeToSelect = initialArchetype === "sage" ? "healer" : "sage";

      await pom.selectArchetype(archetypeToSelect);

      // Badge transitions saving → saved (NEVER error). saving may be too brief
      // on localhost; fall through to the saved web-first wait regardless.
      await pom.waitForAutosaveSaving().catch(() => {
        // saving state too brief on localhost — proceed to saved check.
      });

      // Web-first: badge must NOT reach error AND must reach saved.
      await expect(
        authedPage
          .locator('[data-testid="voz-tono-section-root"]')
          .first()
          .locator('[data-testid="autosave-badge"][data-state="error"]'),
        "Badge must never reach error state during a valid archetype change",
      ).toHaveCount(0);

      await pom.waitForAutosaveSaved();

      // PATCH was actually called on the real backend and returned 200.
      await expect
        .poll(() => patchRequests.length, {
          timeout: 5_000,
          message: "PATCH to personality must have been sent",
        })
        .toBeGreaterThan(0);

      const lastPatch = patchRequests[patchRequests.length - 1];
      expect(lastPatch?.status, "PATCH must return 200 (not 500)").toBe(200);
      expect(
        lastPatch?.body?.["archetype"],
        `PATCH body must include ${archetypeToSelect} archetype`,
      ).toBe(archetypeToSelect);

      const badgeText = await pom.getAutosaveBadgeText();
      expect(badgeText, "Badge text must show Guardado").toMatch(/Guardado/i);

      // Cleanup listener (RN-4 — no dangling page.on).
      authedPage.off("response", onResponse);
    },
  );

  // DES-QUARANTINED (estabilizar-harness-e2e-lisa-marca): la race de
  // auth-readiness de Clerk está resuelta (14af22b2 + retry:5). El reload-persist
  // ahora se asserta web-first (waitForSelectedArchetype) → determinista.
  authTest(
    "persiste en recarga (Sage) tras autosave (round-trip real DB)",
    async ({ authedPage }) => {
      const pom = new VozTonoSectionPom(authedPage, TENANT_ID);
      await pom.goto();
      await pom.waitForLoaded();
      // Switch to a target different from the current state to force a save.
      const initial = await pom.getSelectedArchetype();
      const target = initial === "sage" ? "healer" : "sage";
      await pom.selectArchetype(target);
      await pom.waitForAutosaveSaved();
      await pom.reload();
      await pom.waitForLoaded();
      // Web-first assert: the persisted archetype re-hydrates after reload.
      await pom.waitForSelectedArchetype(target);
    },
  );

  authTest(
    "badge no llega a estado 'error' durante cambio de arquetipo válido",
    async ({ authedPage }) => {
      const pom = new VozTonoSectionPom(authedPage, TENANT_ID);

      await pom.goto();
      await pom.waitForLoaded();

      const initial = await pom.getSelectedArchetype();
      const target = initial === "healer" ? "sage" : "healer";
      await pom.selectArchetype(target);
      await pom.waitForAutosaveSaved();

      // Web-first: at no point during the save cycle does the badge reach error.
      await expect(
        authedPage
          .locator('[data-testid="voz-tono-section-root"]')
          .first()
          .locator('[data-testid="autosave-badge"][data-state="error"]'),
        "Badge must never reach error state during a valid archetype change",
      ).toHaveCount(0);
    },
  );
});
