// cap: shell-organism.shell-vitalia
// story-origin: hotfix visual review (2026-05-29) — inspección real autenticada
/**
 * shell-visual-check.spec.ts — inspección visual REAL (autenticada, sin mock) del shell.
 * Objetivo: (1) confirmar que el label "AppPanelSlot" ya NO aparece encima del contenido,
 * (2) capturar el estado real del layout/splitter para revisión.
 * Run: cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
 *      npx playwright test e2e/regression/shell-visual-check/ --project=smoke
 */
import { test, expect } from "@playwright/test";
import fs from "fs";

const T = "e69a691d-070e-5caf-a053-6e74642ec100";
// UPDATED: paradigm-map-zones T-6 (2026-05-30) — valeria/agenda → mateo/agenda
const ROUTES = ["mateo/agenda", "lisa/marca/identidad"];

test.beforeAll(() => {
  fs.mkdirSync("_shots", { recursive: true });
});

for (const route of ROUTES) {
  test(`shell visual @ ${route}`, async ({ page }) => {
    await page.goto(`/${T}/${route}`, { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(3000);
    const slug = route.replace(/\//g, "_");
    await page.screenshot({ path: `_shots/${slug}.png`, fullPage: false });

    // Bug #1: el placeholder "AppPanelSlot · F1-S10" NO debe estar visible
    const appPanelSlotText = await page.getByText(/AppPanelSlot/i).count();
    console.log(`[${route}] AppPanelSlot-text-count=${appPanelSlotText}`);
    expect(appPanelSlotText, "label placeholder AppPanelSlot no debe renderizarse").toBe(0);
  });
}
