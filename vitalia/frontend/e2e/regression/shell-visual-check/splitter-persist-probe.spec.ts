// cap: shell-organism.shell-vitalia
// story-origin: hotfix visual review (2026-05-29) — probe persistencia/stale layout
import { test, expect } from "@playwright/test";

const T = "e69a691d-070e-5caf-a053-6e74642ec100";

test("probe: dump localStorage del shell + ¿layout stale below-min sobrevive el reload?", async ({
  page,
}) => {
  // UPDATED: paradigm-map-zones T-6 (2026-05-30) — route migrated to mateo/agenda
  await page.goto(`/${T}/mateo/agenda`, { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(3000);

  // 1. Dump localStorage keys actuales (hallar key de rrp + zustand)
  const dump = await page.evaluate(() => {
    const out: Record<string, string> = {};
    for (let i = 0; i < localStorage.length; i++) {
      const k = localStorage.key(i)!;
      out[k] = (localStorage.getItem(k) ?? "").slice(0, 200);
    }
    return out;
  });
  console.log("=== localStorage keys ===");
  for (const [k, v] of Object.entries(dump)) console.log(`KEY: ${k}  =>  ${v}`);

  // 2. Inyectar layout STALE below-min (Valeria 12%) en TODAS las keys candidatas + reload
  await page.evaluate(() => {
    for (let i = 0; i < localStorage.length; i++) {
      const k = localStorage.key(i)!;
      if (/panel|split|layout|resizable/i.test(k)) {
        localStorage.setItem(
          k,
          JSON.stringify({ "valeria-panel": 12, "app-panel": 88 }),
        );
      }
    }
  });
  await page.reload({ waitUntil: "domcontentloaded" });
  await page.waitForTimeout(3500);

  const sep = page.locator('[aria-label="Redimensionar paneles"]').first();
  const box = await sep.boundingBox();
  console.log("=== separator.x tras reload con layout stale 12% ===", box?.x);
  // Guard: el snap-up (Fix A) DEBE corregir un layout stale below-min en el reload
  // (escenario hydration-race que el código fue diseñado para manejar). Verificado robusto 2026-05-29.
  expect(
    box?.x ?? 0,
    `Layout stale 12% NO fue corregido por el snap-up (separator.x=${box?.x}). Regresión del min en hidratación.`,
  ).toBeGreaterThanOrEqual(560);
});
