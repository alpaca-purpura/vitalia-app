// cap: crm.adrian-embudo
// story-origin: vitalia-fase2-adrian-embudo
/**
 * recuperar-live.spec.ts — Live-verify contra dev-app real (DoD Critical Rule #37).
 *
 * vitalia-fase2-adrian-embudo — B1 (recuperar crash · Next-16 soft-nav)
 *
 * ★ HONESTY MANDATE: corre contra el backend REAL (sin MSW). El gate anti-burbuja
 *   (base.ts) captura cualquier pageerror — incluido "Rendered more hooks than
 *   during the previous render" (el crash B1).
 *
 * Scenarios:
 *   R-1 (REPRO B1) — soft-nav board → Recuperar vía el chip KPI "frozen-kpi-badge"
 *       (Next <Link>), repetido en loop para amplificar el flake ~40% de
 *       "Rendered more hooks". Assert RecuperarView (o empty/error) renderiza
 *       SIN burbuja Next.
 *   R-2 (control) — hard-nav directo a /adrian/recuperar. Per learning
 *       2026-06-03, la nav dura NO trippea el bug → debe pasar siempre.
 *
 * Gate anti-burbuja: importa base.ts (pageerror / console.error / /api/ 4xx-5xx /
 * Next overlay) — NO importa @playwright/test directamente.
 *
 * Auth: storageState playwright/.clerk/user.json (Clerk JWT dr.demo@vitalialat.com)
 *       + setupClerkTestingToken (bypass bot-detection).
 *
 * Run:
 *   cd vitalia/frontend && set -a; source ../.env.dev; set +a
 *   E2E_BASE_URL=https://dev-app.vitalialat.com \
 *   npx playwright test e2e/regression/vitalia-fase2-adrian-embudo/recuperar-live.spec.ts \
 *   --project=smoke --timeout=120000
 *
 * downstream-regression-na: brand-local vitalia live-verify; no cross-brand consumers
 * spec_anchor: B1 vitalia-fase2-adrian-embudo · learning 2026-06-03-next16-softnav-redirect
 */

import { test, expect } from "../../fixtures/base";
import path from "path";
import fs from "fs";

const TENANT_ID =
  process.env["E2E_TENANT_ID"] ?? "e69a691d-070e-5caf-a053-6e74642ec100";
const STORAGE_STATE = path.join(
  __dirname,
  "../../../playwright/.clerk/user.json",
);
const SCREENSHOT_DIR = path.join(__dirname, "screenshots");

function storageStateExists(): boolean {
  return fs.existsSync(STORAGE_STATE);
}

test.describe("vitalia-fase2-adrian-embudo — recuperar live-verify (B1, DoD #37)", () => {
  test.use({
    storageState: storageStateExists() ? STORAGE_STATE : undefined,
    viewport: { width: 1440, height: 900 },
  });

  test.beforeEach(async ({ page }) => {
    try {
      const { setupClerkTestingToken } = await import(
        "@clerk/testing/playwright"
      ).catch(() => ({ setupClerkTestingToken: null }));
      if (setupClerkTestingToken) {
        await setupClerkTestingToken({ page });
      }
    } catch {
      // storageState JWT may suffice
    }
  });

  // ── R-1 — REPRO B1: soft-nav board → Recuperar (looped) ─────────────────────

  test("R-1: click chip 'frozen' (hard-nav) → Recuperar monta SIN hang del shell", async ({
    page,
  }) => {
    const boardUrl = `/${TENANT_ID}/adrian/embudo`;

    // Loop el flujo EXACTO que Chris ejerce: board → click chip "congelados".
    // Tras el fix B1 el chip es <a> (hard-nav) → reload completo → el shell
    // ssr:false monta limpio (SSR skeleton → client mount), sin el "Rendered more
    // hooks" del soft-nav. Cada iter arranca con un goto duro al board (no goBack:
    // el back es OTRA transición soft-nav del shell, fuera del scope de este fix).
    for (let i = 0; i < 5; i++) {
      await page.goto(boardUrl);
      await page.waitForLoadState("networkidle");

      const frozenChip = page.locator('[data-testid="frozen-kpi-badge"]').first();
      await expect(
        frozenChip,
        `Iter ${i}: el chip 'congelados' (frozen-kpi-badge) debe estar en el board`,
      ).toBeVisible({ timeout: 10000 });

      await frozenChip.click();

      await page.waitForURL(`**/adrian/recuperar`, { timeout: 15000 });
      await page.waitForLoadState("networkidle").catch(() => {});

      // Recuperar debe montar (no "Cargando shell" colgado, no error page).
      const ok =
        (await page.locator('[data-testid="recuperar-view"]').isVisible({ timeout: 15000 }).catch(() => false)) ||
        (await page.locator('[data-testid="recuperar-empty"]').isVisible().catch(() => false)) ||
        (await page.locator('[role="alert"]').isVisible().catch(() => false));

      expect(
        ok,
        `Iter ${i}: RecuperarView no montó tras click del chip. ` +
          "Si quedó en 'Cargando shell' → el shell ssr:false colgó (B1 NO resuelto por el hard-nav).",
      ).toBe(true);
    }

    await fs.promises.mkdir(SCREENSHOT_DIR, { recursive: true });
    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, "R-1-recuperar-after-hardnav.png"),
      fullPage: false,
    });
    // base.ts teardown asserts: 0 pageerror (incl. "Rendered more hooks"), 0 Next overlay.
  });

  // ── R-2 — control: hard-nav directo ─────────────────────────────────────────

  test("R-2: hard-nav directo a /recuperar renderiza limpio", async ({
    page,
  }) => {
    await page.goto(`/${TENANT_ID}/adrian/recuperar`);
    await page.waitForLoadState("networkidle");

    const ok =
      (await page.locator('[data-testid="recuperar-view"]').isVisible().catch(() => false)) ||
      (await page.locator('[data-testid="recuperar-empty"]').isVisible().catch(() => false)) ||
      (await page.locator('[role="alert"]').isVisible().catch(() => false));

    expect(ok, "Recuperar (hard-nav) debe renderizar una vista válida.").toBe(true);
  });
});
