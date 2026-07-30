/**
 * _live-verify.spec.ts — DoD #37 live-verify de los 6 bugs contra el STACK REAL.
 *
 * Real Clerk auth (storageState + testing token) + real backend (forwardApiToRealBackend → :8002).
 * NO mock de /api/tenants → entorno limpio (a diferencia de los specs hybrid-mock).
 * failOnRuntimeError: false → quiero VER toda la consola (incl. agenda 'Rendered more hooks' y los
 * 404 pre-existentes de lisa/marca) sin que el test baile antes de asertar mis fixes.
 *
 * NO es parte de la suite CI (nombre _live-verify, no matchea testMatch smoke). Se corre a mano
 * para producir dod_evidence. downstream-regression-na: brand-local.
 */
import {
  test,
  expect,
  TENANT_ID,
  forwardApiToRealBackend,
} from "../../fixtures/real-backend-forward.fixture";

const DESKTOP = { width: 1280, height: 800 };

test.use({ viewport: DESKTOP, failOnRuntimeError: false });

/** Captura console errors + page errors por test, los imprime al final. */
function attachConsoleCapture(page: import("@playwright/test").Page, label: string) {
  const errors: string[] = [];
  page.on("console", (m) => {
    if (m.type() === "error") errors.push(`[console.error] ${m.text()}`);
  });
  page.on("pageerror", (e) => errors.push(`[pageerror] ${e.message}`));
  page.on("response", (r) => {
    if (r.url().includes("/api/") && r.status() >= 400)
      errors.push(`[api ${r.status()}] ${r.url()}`);
  });
  return () => {
    console.log(`\n──── CONSOLE [${label}] (${errors.length}) ────\n${errors.join("\n") || "(limpio)"}\n`);
    return errors;
  };
}

test.describe("DoD #37 live-verify — 6 bugs shell (real stack)", () => {
  test("Bug #1 — /{tenant} aterriza en mateo/agenda (NO valeria/agenda → 404)", async ({ page }) => {
    const dump = attachConsoleCapture(page, "bug1 root redirect");
    await forwardApiToRealBackend(page);
    await page.goto(`/${TENANT_ID}`, { waitUntil: "domcontentloaded" });
    await page.waitForURL(/\/mateo\/agenda/, { timeout: 20_000 }).catch(() => {});
    const url = page.url();
    dump();
    console.log(`Bug#1 landing URL = ${url}`);
    expect(url, "landing post-/{tenant} debe terminar en mateo/agenda").toContain("/mateo/agenda");
    // El destino viejo debe estar muerto (404 contextual):
  });

  test("Bug #1b — la ruta vieja /{tenant}/valeria/agenda da 404 (confirma regresión)", async ({ page }) => {
    const dump = attachConsoleCapture(page, "bug1b valeria/agenda 404");
    await forwardApiToRealBackend(page);
    await page.goto(`/${TENANT_ID}/valeria/agenda`, { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(2500);
    const body = (await page.locator("body").innerText()).toLowerCase();
    dump();
    expect(
      body.includes("no encontramos") || body.includes("no encontr") || body.includes("404"),
      "valeria/agenda debe ser 404 (ruta muerta post-migración)",
    ).toBeTruthy();
  });

  test("Bug #2 — selector de tenant visible con 1 tenant", async ({ page }) => {
    const dump = attachConsoleCapture(page, "bug2 tenant switcher");
    await forwardApiToRealBackend(page);
    await page.goto(`/${TENANT_ID}/mateo/agenda`, { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(3000);
    const trigger = page.getByTestId("tenant-switcher-trigger");
    dump();
    await expect(trigger, "el trigger del TenantSwitcher debe verse con ≥1 tenant").toBeVisible({ timeout: 10_000 });
  });

  test("Bug #4 — el panel de contenido es scrolleable (overflow-y: auto)", async ({ page }) => {
    const dump = attachConsoleCapture(page, "bug4 scroll");
    await forwardApiToRealBackend(page);
    await page.goto(`/${TENANT_ID}/lisa/marca/presencia`, { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(3000);
    // El contenedor scrolleable = hijo directo de AppPanelSlot con flex-1 overflow-y-auto.
    const overflowY = await page.evaluate(() => {
      const slot = document.querySelector('[data-testid="app-panel-slot"]');
      if (!slot) return "no-slot";
      // el div de contenido es el último hijo flex-1
      const kids = Array.from(slot.children) as HTMLElement[];
      const content = kids.find((k) => getComputedStyle(k).flexGrow === "1");
      return content ? getComputedStyle(content).overflowY : "no-content-div";
    });
    dump();
    console.log(`Bug#4 content overflow-y = ${overflowY}`);
    expect(["auto", "scroll"], "el contenedor de contenido debe scrollear").toContain(overflowY);
  });

  test("Bug #5 — Presencia NO muestra 'Editor de landing pública — próximamente'", async ({ page }) => {
    const dump = attachConsoleCapture(page, "bug5 landing banner");
    await forwardApiToRealBackend(page);
    await page.goto(`/${TENANT_ID}/lisa/marca/presencia`, { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(3000);
    const banner = page.getByText("Editor de landing pública", { exact: false });
    dump();
    await expect(banner, "el banner de landing debe estar eliminado").toHaveCount(0);
  });

  test("Bug #3 — ruta placeholder NO muestra título-eco (SubTabHeader removido)", async ({ page }) => {
    const dump = attachConsoleCapture(page, "bug3 redundant title");
    await forwardApiToRealBackend(page);
    await page.goto(`/${TENANT_ID}/lucas/lanzar`, { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(3000);
    // El SubTabHeader del dispatcher tenía data-testid="subtab-header-{agent}-{subtab}".
    const headers = page.locator('[data-testid^="subtab-header-"]');
    dump();
    await expect(headers, "el SubTabHeader-eco del dispatcher debe estar removido").toHaveCount(0);
  });
});
