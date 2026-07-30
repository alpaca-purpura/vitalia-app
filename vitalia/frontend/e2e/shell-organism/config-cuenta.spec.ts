/**
 * cuenta.spec.ts — E2E spec for config/cuenta N3-static sub-tab (Mi cuenta)
 *
 * Story: vitalia-fase2-config-cuenta T-1
 * Validator IDs: e2e_config_cuenta_datos, e2e_config_cuenta_write
 *
 * Coverage:
 *   SC-01: datos tab renders — name, fiscal fields, specialties badges, read-only country/language
 *   SC-02: preferencias tab — currency/timezone selectors render
 *   SC-03: responsable tab — DPO section + link to seguridad
 *   SC-04: WRITE real — PATCH name → observe persisted value on reload (AC-6 live-verify)
 *
 * Network: REAL backend (no mock del surface bajo prueba).
 * Anti-burbuja: via real-backend-forward.fixture (composición base.ts runtime-gate).
 * Auth: Clerk testing token via real-backend-forward.fixture.
 *
 * Stack: FE=3002, BE=8002 (make dev-vitalia).
 * Comando: cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 npx playwright test specs/config/cuenta.spec.ts
 * NUNCA: make e2e (Docker).
 *
 * downstream-regression-na: brand-local vitalia E2E; no cross-brand consumers
 *
 * @see vitalia/docs/product/stories/vitalia-fase2-config-cuenta/03-arch.md § Test Surfaces
 * @see .claude/rules/definition-of-done-live-verify.md (critical rule #37)
 */

import { test, expect, TENANT_ID } from "../fixtures/real-backend-forward.fixture";

const BASE_URL = process.env["E2E_BASE_URL"] ?? "http://localhost:3002";

test.describe("config/cuenta — N3-static sub-tab (Mi cuenta)", () => {
  test.beforeEach(async ({ authedPage }) => {
    // Navigate to datos (default leaf) — edge redirect handles bare cuenta →datos
    await authedPage.goto(`${BASE_URL}/${TENANT_ID}/config/cuenta/datos`);
    await authedPage.waitForSelector('[data-testid="account-data-view"]', { timeout: 10_000 });
  });

  test("SC-01: datos tab renders editable fields + read-only badges", async ({
    authedPage,
  }) => {
    // Sub-sub-tab bar visible
    await expect(authedPage.getByTestId("sub-sub-tabs-bar")).toBeVisible();

    // 'datos' tab active
    await expect(authedPage.getByTestId("sub-sub-tab-datos")).toHaveAttribute(
      "aria-selected",
      "true",
    );

    // Name field editable
    await expect(authedPage.getByLabel(/Nombre comercial/i)).toBeVisible();

    // Read-only badges (país/idioma/tipo) — 3 instancias, basta la primera visible
    await expect(authedPage.getByText(/definido en el alta/i).first()).toBeVisible();

    // Specialties field
    await expect(authedPage.getByTestId("specialties-field")).toBeVisible();

    // Autosave indicator
    await expect(authedPage.getByTestId("autosave-indicator")).toBeVisible();

    // No runtime errors (anti-burbuja gate)
  });

  test("SC-02: preferencias tab — currency + timezone selectors", async ({
    authedPage,
  }) => {
    await authedPage.getByTestId("sub-sub-tab-preferencias").click();
    await authedPage.waitForURL(`**/config/cuenta/preferencias`);

    // Currency selector
    await expect(authedPage.getByTestId("currency-selector")).toBeVisible();
    // Timezone selector
    await expect(authedPage.getByTestId("timezone-select")).toBeVisible();
  });

  test("SC-03: responsable tab — DPO info + seguridad link", async ({
    authedPage,
  }) => {
    await authedPage.getByTestId("sub-sub-tab-responsable").click();
    await authedPage.waitForURL(`**/config/cuenta/responsable`);

    await expect(authedPage.getByTestId("responsible-view")).toBeVisible();
    // Link to seguridad exists
    await expect(authedPage.getByRole("link", { name: /seguridad/i })).toBeVisible();
  });

  test("SC-04 (WRITE real): PATCH name → persists across reload (AC-6)", async ({
    authedPage,
  }) => {
    const nameField = authedPage.getByLabel(/Nombre comercial/i);
    const original = await nameField.inputValue();

    // Edit field — autosave triggers in 600ms
    const testValue = `${original} (e2e-${Date.now()})`.slice(0, 80);
    await nameField.fill(testValue);

    // Wait for autosave cycle (debounce 600ms + network)
    await authedPage.getByTestId("autosave-indicator").waitFor();
    await authedPage.waitForFunction(() => {
      const el = document.querySelector('[data-testid="autosave-indicator"]');
      return el?.getAttribute("data-state") === "saved";
    }, { timeout: 5000 });

    // Reload — value must persist (not just in-memory state)
    await authedPage.reload();
    await authedPage.waitForSelector('[data-testid="account-data-view"]', { timeout: 10_000 });

    const reloaded = await authedPage.getByLabel(/Nombre comercial/i).inputValue();
    expect(reloaded).toBe(testValue);

    // Restore original
    await authedPage.getByLabel(/Nombre comercial/i).fill(original);
    await authedPage.waitForFunction(() => {
      const el = document.querySelector('[data-testid="autosave-indicator"]');
      return el?.getAttribute("data-state") === "saved";
    }, { timeout: 5000 });
  });
});
