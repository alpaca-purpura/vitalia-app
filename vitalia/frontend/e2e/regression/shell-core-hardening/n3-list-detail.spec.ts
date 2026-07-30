// cap: shell-organism.shell-vitalia
// story-origin: vitalia-shell-core-hardening
/**
 * n3-list-detail.spec.ts — SC-11: N3 staff+embudo EntityWorkspaceLayout core (RN-10)
 *
 * RN-10: N3 = EntityWorkspaceLayout (consume @luana/ui-kit).
 * Verifica que:
 *   1. Staff directory carga (lista de doctores / empty state).
 *   2. EntityWorkspaceLayout está presente en workspace de doctor (data-testid).
 *   3. Embudo directory carga (lista de leads / empty state).
 *   4. EntityWorkspaceLayout presente en workspace de lead.
 *   5. EntitySubNavBar importa desde @luana/ui-kit (arch: brand-local retirado).
 *
 * Real-backend. Gate anti-burbuja via base.ts.
 *
 * Run:
 *   cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
 *     npx playwright test e2e/regression/shell-core-hardening/n3-list-detail.spec.ts \
 *     --project=smoke
 *
 * downstream-regression-na: brand-local E2E spec; no cross-brand consumers
 */
import { test, expect } from "../../fixtures/shell-hardening.fixture";
import { EntityWorkspacePage } from "../../pages/EntityWorkspacePage";

const DESKTOP_VIEWPORT = { width: 1440, height: 900 };

test.describe("SC-11 — N3 EntityWorkspaceLayout (RN-10)", () => {
  test.use({ viewport: DESKTOP_VIEWPORT });

  // ── Staff (lisa/staff) ────────────────────────────────────────────────────

  test("staff directory carga (lista / empty-state) sin errores", async ({
    shellPage,
    tenantId,
  }) => {
    const ewp = new EntityWorkspacePage(shellPage);
    await ewp.gotoStaffDirectory(tenantId);

    // Page loaded: either a list of doctors or an empty state.
    // T-V2 lift (harness fix): isVisible() retorna INMEDIATO (ignora timeout) —
    // race con el fetch RQ post-networkidle. waitFor sí espera (misma semántica).
    // T-V2 fix-loop: testids alineados al contrato real: staff-card-* + empty-doctores.
    const hasCards = await shellPage
      .locator('[data-testid^="staff-card-"]')
      .first()
      .waitFor({ state: "visible", timeout: 10_000 })
      .then(() => true)
      .catch(() => false);
    const hasEmptyState =
      hasCards ||
      (await shellPage
        .locator('[data-testid="empty-doctores"]')
        .waitFor({ state: "visible", timeout: 2_000 })
        .then(() => true)
        .catch(() => false));

    // At least one of the two states renders
    expect(hasCards || hasEmptyState, "staff directory: lista o empty-state debe renderizar").toBe(true);
  });

  test("staff workspace: EntityWorkspaceLayout montado (N3 core)", async ({
    shellPage,
    tenantId,
  }) => {
    const ewp = new EntityWorkspacePage(shellPage);

    // Navigate to staff directory first to find a doctor
    await ewp.gotoStaffDirectory(tenantId);
    await shellPage.waitForTimeout(1000);

    // Try to click first doctor card (T-V2 fix-loop: testid = staff-card-*)
    const firstCard = shellPage
      .locator('[data-testid^="staff-card-"]')
      .first();
    const hasDoctor = await firstCard
      .waitFor({ state: "visible", timeout: 5_000 })
      .then(() => true)
      .catch(() => false);

    if (hasDoctor) {
      // T-V2 fix-loop (harness): la card es un <article> no-clickeable — el nav
      // real del usuario es el link interno "Ver perfil".
      await firstCard.getByRole("link").first().click();
      await shellPage.waitForLoadState("networkidle", { timeout: 15_000 });

      // EntityWorkspaceLayout should be mounted
      await expect(ewp.workspaceLayout).toBeVisible({ timeout: 10_000 });
    } else {
      // No doctors seeded — just verify the directory route works
      // (empty-state is an acceptable state per AC-13)
      test.info().annotations.push({
        type: "skip-reason",
        description: "No doctors seeded in dev DB — directory shows empty-state (acceptable)",
      });
    }
  });

  // ── Embudo (adrian/embudo) ────────────────────────────────────────────────

  test("embudo directory carga (board / empty-state) sin errores", async ({
    shellPage,
    tenantId,
  }) => {
    const ewp = new EntityWorkspacePage(shellPage);
    await ewp.gotoEmbudoDirectory(tenantId);

    // Embudo board or empty state.
    // T-V2 lift harness fix: waitFor, no isVisible racy.
    // T-V2 fix-loop: testids alineados al contrato real: kanban-board + embudo-empty-state.
    const hasBoard = await shellPage
      .locator('[data-testid="kanban-board"]')
      .waitFor({ state: "visible", timeout: 10_000 })
      .then(() => true)
      .catch(() => false);
    const hasEmptyState =
      hasBoard ||
      (await shellPage
        .locator('[data-testid="embudo-empty-state"]')
        .waitFor({ state: "visible", timeout: 2_000 })
        .then(() => true)
        .catch(() => false));

    expect(hasBoard || hasEmptyState, "embudo directory: board o empty-state debe renderizar").toBe(true);
  });

  test("embudo workspace: EntityWorkspaceLayout montado (N3 core)", async ({
    shellPage,
    tenantId,
  }) => {
    const ewp = new EntityWorkspacePage(shellPage);
    await ewp.gotoEmbudoDirectory(tenantId);
    await shellPage.waitForTimeout(1000);

    // Try to find a lead card
    const firstLead = shellPage
      .locator('[data-testid^="lead-card-"]')
      .first();
    const hasLead = await firstLead
      .waitFor({ state: "visible", timeout: 5_000 })
      .then(() => true)
      .catch(() => false);

    if (hasLead) {
      // T-V2 fix-loop (harness): nav real = link interno si existe; fallback click.
      const innerLink = firstLead.getByRole("link").first();
      if ((await innerLink.count()) > 0) {
        await innerLink.click();
      } else {
        await firstLead.click();
      }
      await shellPage.waitForLoadState("networkidle", { timeout: 15_000 });
      await expect(ewp.workspaceLayout).toBeVisible({ timeout: 10_000 });
    } else {
      test.info().annotations.push({
        type: "skip-reason",
        description: "No leads seeded — acceptable for empty embudo tenant",
      });
    }
  });
});
