// cap: plataforma-tecnica.shell
/**
 * Resizer matrix — TODOS los casos de estados × resizer del shell (Chris 2026-06-11:
 * "genera todos los casos posibles, mueve el resizer, en cualquier escenario siempre
 * debe verse bien todo").
 *
 * Cubre los 3 bugs live-fixed 2026-06-11:
 *  - Colapso runtime inerte (props collapsible/collapsedSize capturadas en mount →
 *    key-remount + rAF retry-until-collapsed contra la persistencia del Group).
 *  - collapsedSize en unidades px (number=px en v4; stripPct era 3.4px, no 44px).
 *  - RN-7 push REAL del historial (antes robaba 260px al chat; ahora ensancha el panel).
 *
 * Real-backend (sin mocks del shell). Importa base.ts (anti-burbuja).
 */
import { expect, test } from "../../fixtures/shell-hardening.fixture";

const VIEW = { width: 1280, height: 800 };

const valeriaW = async (page: import("@playwright/test").Page) =>
  page.evaluate(() => {
    const handle = document.getElementById("shell-handle");
    const el = handle?.previousElementSibling;
    if (el) return Math.round(el.getBoundingClientRect().width);
    // estado A: seam oculto — medir el primer hijo del Group (panel Valeria)
    const strip = document.querySelector('[aria-label*="Abrir a Valeria"]');
    const panel = strip?.closest("[data-panel],[id*='valeria' i]") ?? strip?.parentElement?.parentElement;
    return panel ? Math.round(panel.getBoundingClientRect().width) : null;
  });

const noOverflowX = async (page: import("@playwright/test").Page) =>
  page.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth);

const dragHandle = async (page: import("@playwright/test").Page, dx: number) => {
  const box = await page.locator("#shell-handle").boundingBox();
  if (!box) throw new Error("seam #shell-handle no visible");
  await page.mouse.move(box.x + box.width / 2, box.y + 350);
  await page.mouse.down();
  await page.mouse.move(box.x + box.width / 2 + dx, box.y + 350, { steps: 14 });
  await page.mouse.up();
  await page.waitForTimeout(700);
};

test.describe("resizer-matrix — estados × drag siempre se ve bien", () => {
  test.use({ viewport: VIEW });

  test.beforeEach(async ({ page, tenantId }) => {
    await page.goto(`/${tenantId}/adrian/inbox`);
    await page.waitForSelector('[data-shell-ready="true"]', { timeout: 30000 });
    await page.evaluate(() => {
      localStorage.removeItem("vitalia-shell-state");
      for (const k of Object.keys(localStorage))
        if (k.includes("shell") || k.includes("layout")) localStorage.removeItem(k);
    });
    await page.reload();
    await page.waitForSelector('[data-shell-ready="true"]', { timeout: 30000 });
    await page.waitForTimeout(800);
  });

  test("drags en B: crece · clamp 320 (no colapsa) · sigue vivo", async ({ page }) => {
    const w0 = await valeriaW(page);
    expect(w0).toBeGreaterThan(350); // 30% fresh
    await dragHandle(page, 200);
    expect(await valeriaW(page)).toBeGreaterThan(500);
    await dragHandle(page, -600);
    const clamped = await valeriaW(page);
    expect(clamped).toBeGreaterThanOrEqual(290); // RN-8: clamp, NUNCA colapso por drag (RN-9)
    expect(clamped).toBeLessThanOrEqual(360);
    // ★ Ronda Chris 2026-06-11 (000.png): al mínimo, el CONTENIDO del chat re-wrappea
    // — nada sobresale del box (antes: columna grid implícita `auto` trackeaba al
    // contenido → mensajes/composer renderizados a 604px y RECORTADOS).
    const overhang = await page.evaluate(() => {
      const chat = document.querySelector('[data-testid="valeria-chat"]');
      if (!chat) return -1;
      const cb = chat.getBoundingClientRect();
      let worst = 0;
      chat.querySelectorAll("*").forEach((el) => {
        const r = el.getBoundingClientRect();
        if (r.width > 0) worst = Math.max(worst, Math.round(r.right - cb.right));
      });
      return worst;
    });
    expect(overhang).toBeLessThanOrEqual(2); // SIN RECORTE (wrap real)
    await dragHandle(page, 60);
    expect(await valeriaW(page)).toBeGreaterThanOrEqual(340); // drag vivo post-clamp
    expect(await noOverflowX(page)).toBe(true);
  });

  test("colapso RUNTIME → strip 44 sin gap · seam oculto · reabrir + resize vivo", async ({ page }) => {
    await page.locator('[aria-label*="Colapsar a Valeria"]').first().click();
    await page.waitForTimeout(1200);
    const collapsed = await valeriaW(page);
    expect(collapsed).not.toBeNull();
    expect(collapsed!).toBeLessThanOrEqual(60); // GAP MUERTO (bug live 2026-06-11)
    await expect(page.locator("#shell-handle")).toBeHidden(); // RN-9: sin drag en A
    await expect(page.locator('[aria-label*="Abrir a Valeria"]').first()).toBeVisible();
    // reabrir por avatar
    await page.locator('[aria-label*="Abrir a Valeria"]').first().click();
    await page.waitForTimeout(1200);
    const reopened = await valeriaW(page);
    expect(reopened!).toBeGreaterThanOrEqual(290);
    await expect(page.locator("#shell-handle")).toBeVisible();
    // resize VIVO post-ciclo (bug live: drag muerto tras colapsar/reabrir)
    await dragHandle(page, 120);
    expect((await valeriaW(page))!).toBeGreaterThanOrEqual(reopened! + 60);
  });

  test("historial EMPUJA (RN-7 real): chat conserva ancho · drags en C · colapso desde C", async ({ page }) => {
    const wB = await valeriaW(page);
    await page.locator('[aria-label*="Mostrar historial"]').first().click();
    await page.waitForTimeout(1100);
    const wC = await valeriaW(page);
    // push REAL: el panel se ensancha ~260px (el historial NO roba del chat)
    expect(wC!).toBeGreaterThanOrEqual(wB! + 200);
    expect(await noOverflowX(page)).toBe(true);
    // drag en C funciona
    await dragHandle(page, 150);
    expect((await valeriaW(page))!).toBeGreaterThanOrEqual(wC! + 80);
    // drag below min en C clampa al min EFECTIVO (chat-min + historial 280 — ronda
    // Chris 2026-06-11 001.png: antes clampeaba al min de B y el historial se comía
    // el chat hasta ~60px)
    await dragHandle(page, -700);
    expect((await valeriaW(page))!).toBeGreaterThanOrEqual(560); // ~318 chat + 280 hist
    expect(await noOverflowX(page)).toBe(true);
    // colapsar DESDE C → A (historial también cierra, RN-5) → reabrir = B chat-only
    await page.locator('[aria-label*="Colapsar a Valeria"]').first().click();
    await page.waitForTimeout(1200);
    expect((await valeriaW(page))!).toBeLessThanOrEqual(60);
    await page.locator('[aria-label*="Abrir a Valeria"]').first().click();
    await page.waitForTimeout(1200);
    const back = await valeriaW(page);
    expect(back!).toBeGreaterThanOrEqual(290);
    await expect(page.locator('[aria-label*="Ocultar historial"]')).toHaveCount(0); // RN-5: no restaura
  });

  test("persistencia: ancho custom + estado A sobreviven reload sin gap", async ({ page }) => {
    await dragHandle(page, 180);
    const custom = await valeriaW(page);
    await page.reload();
    await page.waitForSelector('[data-shell-ready="true"]', { timeout: 30000 });
    await page.waitForTimeout(900);
    expect(Math.abs((await valeriaW(page))! - custom!)).toBeLessThanOrEqual(25); // RN-4/RN-11
    // estado A persiste como strip (no gap) tras reload
    await page.locator('[aria-label*="Colapsar a Valeria"]').first().click();
    await page.waitForTimeout(900);
    await page.reload();
    await page.waitForSelector('[data-shell-ready="true"]', { timeout: 30000 });
    await page.waitForTimeout(900);
    expect((await valeriaW(page))!).toBeLessThanOrEqual(60);
    await expect(page.locator('[aria-label*="Abrir a Valeria"]').first()).toBeVisible();
  });

  test("viewports: 1100 clamp · 800 drawer · round-trip 1280 — nunca overflow ni gap", async ({ page }) => {
    await page.setViewportSize({ width: 1100, height: 800 });
    await page.waitForTimeout(1200);
    expect((await valeriaW(page))!).toBeGreaterThanOrEqual(280); // clamp 320 zona [1024,1280)
    expect(await noOverflowX(page)).toBe(true);
    await page.setViewportSize({ width: 800, height: 800 });
    await page.waitForTimeout(1200);
    const mobile = await valeriaW(page);
    expect(mobile === null || mobile <= 10).toBe(true); // inline muere <1024 (drawer)
    expect(await noOverflowX(page)).toBe(true);
    await page.setViewportSize(VIEW);
    await page.waitForTimeout(1500);
    expect((await valeriaW(page))!).toBeGreaterThanOrEqual(290); // round-trip sano
    expect(await noOverflowX(page)).toBe(true);
  });
});
