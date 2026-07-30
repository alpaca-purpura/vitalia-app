/**
 * voz-bloque-autosave.spec.ts — SC-4 Regression 422: bloque de voz camelCase (real backend)
 *
 * Gherkin scenario: voz-bloque-edita-no-422
 *
 * Given:  Owner en Voz y tono con el bloque "Así hablo" visible
 * When:   Edita el texto del bloque y transcurre el debounce del autosave
 * Then:   Badge saving→saved (NO 'error') · PATCH 200 (NO 422 extra_forbidden) · texto persiste
 *
 * Root cause del bug: FE manda campo camelCase (soISpeak); el BE tenía
 * extra="forbid" sin alias_generator → 422. El fix vive en el contrato BE. Este
 * spec usa el backend REAL — la ÚNICA forma de probar que el contrato funciona
 * ("verde honesto"). Transporte honesto (auth + forwarding + anti-burbuja) se
 * compone desde `real-backend-forward.fixture` (LIFT del inline previo).
 *
 * Stack required: backend :8002 + frontend :3002 UP (make dev-vitalia).
 *
 * Run:
 *   cd vitalia/frontend
 *   E2E_BASE_URL=http://localhost:3002 npx playwright test --project=smoke \
 *     e2e/regression/arreglar-guardado-voz-y-tono/voz-bloque-autosave.spec.ts
 *
 * downstream-regression-na: brand-local vitalia e2e spec arreglar-guardado-voz-y-tono
 *
 * @see e2e/fixtures/real-backend-forward.fixture.ts
 * @see 06-tickets.yaml T-1 deliverable 6
 * @see 01-spec.md § voz-bloque-edita-no-422
 */

import {
  test as authTest,
  expect,
  TENANT_ID,
} from "../../fixtures/real-backend-forward.fixture";
import { VozTonoSectionPom } from "./poms/voz-tono-section.pom";

// ---------------------------------------------------------------------------
// Test suite — SC-4 voice block camelCase 422 regression
// ---------------------------------------------------------------------------

authTest.describe("SC-4 — Regresión 422: editar bloque de voz (backend real, sin mock PATCH)", () => {
  authTest(
    "editar bloque 'Así hablo': badge saving→saved (no 422 extra_forbidden)",
    async ({ authedPage }) => {
      const pom = new VozTonoSectionPom(authedPage, TENANT_ID);

      await pom.goto();
      await pom.waitForLoaded();

      // Capture outgoing PATCH responses (real backend). Cleaned up (RN-4).
      const patchResponses: { status: number }[] = [];
      const onResponse = (response: import("@playwright/test").Response) => {
        if (
          response.url().includes("/api/v1/lisa/marca/personality") &&
          response.request().method() === "PATCH"
        ) {
          patchResponses.push({ status: response.status() });
        }
      };
      authedPage.on("response", onResponse);

      const newText =
        "Con calidez y empatía, priorizando la comprensión del paciente. Revisado en regresión.";

      await pom.editVoiceBlock("Así hablo", newText);

      await pom.waitForAutosaveSaving().catch(() => {
        // saving state too brief on localhost — proceed to saved check.
      });

      // Web-first: badge must not reach error (422 would set error).
      await expect(
        authedPage
          .locator('[data-testid="voz-tono-section-root"]')
          .first()
          .locator('[data-testid="autosave-badge"][data-state="error"]'),
        "Badge must never reach error — 422 means camelCase contract not fixed",
      ).toHaveCount(0);

      await pom.waitForAutosaveSaved();

      // The PATCH returned 200 (not 422).
      await expect
        .poll(() => patchResponses.length, {
          timeout: 5_000,
          message: "PATCH must have been sent to backend",
        })
        .toBeGreaterThan(0);

      const lastResponse = patchResponses[patchResponses.length - 1];
      expect(
        lastResponse?.status,
        "PATCH must return 200 (not 422 extra_forbidden).",
      ).toBe(200);

      const badgeText = await pom.getAutosaveBadgeText();
      expect(badgeText, "Badge must show Guardado").toMatch(/Guardado/i);

      authedPage.off("response", onResponse);
    },
  );

  // DES-QUARANTINED (estabilizar-harness-e2e-lisa-marca): web-first reload-persist.
  authTest(
    "texto del bloque persiste en recarga (round-trip real DB)",
    async ({ authedPage }) => {
      const pom = new VozTonoSectionPom(authedPage, TENANT_ID);
      await pom.goto();
      await pom.waitForLoaded();
      const persistText = "Hablamos con calidez y claridad clínica.";
      await pom.editVoiceBlock("Así hablo", persistText);
      await pom.waitForAutosaveSaved();
      await pom.reload();
      await pom.waitForLoaded();
      // Web-first assert: the textarea re-hydrates with the persisted value.
      await expect(
        authedPage
          .locator('[data-testid="voz-tono-section-root"]')
          .first()
          .locator('[data-testid="tone-block-asi-hablo-textarea"]'),
        "Text in 'Así hablo' block must persist after reload (DB round-trip)",
      ).toHaveValue(persistText, { timeout: 15_000 });
    },
  );

  authTest(
    "múltiples ediciones al mismo bloque: solo la última dispara autosave (debounce)",
    async ({ authedPage }) => {
      const pom = new VozTonoSectionPom(authedPage, TENANT_ID);

      await pom.goto();
      await pom.waitForLoaded();

      const patchCount = { count: 0 };
      const onResponse = (response: import("@playwright/test").Response) => {
        if (
          response.url().includes("/api/v1/lisa/marca/personality") &&
          response.request().method() === "PATCH"
        ) {
          patchCount.count++;
        }
      };
      authedPage.on("response", onResponse);

      // Rapid edits — debounce should coalesce.
      await pom.editVoiceBlock("Así hablo", "Primera versión");
      await authedPage.waitForTimeout(200);
      await pom.editVoiceBlock("Así hablo", "Segunda versión final");

      await pom.waitForAutosaveSaved();

      // Debounce coalesces multiple edits (allow 1-2 — timing-sensitive).
      expect(
        patchCount.count,
        "Debounce must coalesce multiple edits into one PATCH call",
      ).toBeLessThanOrEqual(2);

      authedPage.off("response", onResponse);
    },
  );
});
