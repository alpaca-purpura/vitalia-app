// cap: clinics.lisa.doctores
// story-origin: vitalia-fase2-lisa-doctores
/**
 * bug7-r3-d1-save-button.spec.ts — D-1 + matriz #15: botón Guardar VISIBLE
 * y clickeable en ambos themes (claro + oscuro).
 *
 * BUG (G round-2): `bg-[--agent-lisa]` (BloquePopover.tsx:1015) es sintaxis
 * Tailwind v3 muerta en v4.1 → el botón no genera background-color → con
 * `text-black` queda invisible en dark y fantasma en light.
 *
 * RED first: computed backgroundColor del botón debe tener alpha > 0 y
 * diferenciarse del fondo del popover, en light Y dark.
 *
 * Real backend (authed-runtime): la página carga blocks/occurrences reales.
 *
 * WORK-ORDER-bug7-round3.md § D-1 · matriz #15
 */

import { test, expect } from "../../fixtures/authed-runtime";
import { gotoHorarios, clickCell } from "./bug7-helpers";

/** Parse CSS color → alpha (rgba/rgb/transparent). */
function alphaOf(color: string): number {
  if (color === "transparent") return 0;
  const m = color.match(/rgba?\(([^)]+)\)/);
  if (!m?.[1]) return 1;
  const parts = m[1].split(",").map((p) => parseFloat(p.trim()));
  return parts.length === 4 ? (parts[3] ?? 1) : 1;
}

test.describe("bug7 r3 · D-1 — botón Guardar visible en ambos themes", () => {
  test("light: background con alpha>0 y distinto del fondo del popover", async ({
    page,
  }) => {
    await gotoHorarios(page);
    await clickCell(page, 5, 16); // sábado 16:00 — celda libre

    const btn = page.getByTestId("btn-save-block");
    await expect(btn).toBeVisible();
    await expect(btn).toBeEnabled();

    const btnBg = await btn.evaluate(
      (el) => getComputedStyle(el).backgroundColor,
    );
    const popoverBg = await page
      .getByTestId("bloque-popover")
      .evaluate((el) => getComputedStyle(el).backgroundColor);

    expect(
      alphaOf(btnBg),
      `btn-save-block backgroundColor="${btnBg}" es transparente (D-1: bg-[--agent-lisa] roto en Tailwind v4)`,
    ).toBeGreaterThan(0);
    expect(
      btnBg,
      `btn-save-block background igual al fondo del popover ("${btnBg}") — botón invisible`,
    ).not.toBe(popoverBg);

    await page.screenshot({
      path: "/tmp/bug7-r3-d1-light.png",
      fullPage: false,
    });
  });

  test("dark: background con alpha>0 y distinto del fondo del popover", async ({
    page,
  }) => {
    await gotoHorarios(page);

    // Toggle a dark ANTES de abrir el popover (el backdrop tapa el topbar).
    await page.getByTestId("theme-toggle").click();
    await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");

    await clickCell(page, 5, 16);

    const btn = page.getByTestId("btn-save-block");
    await expect(btn).toBeVisible();

    const btnBg = await btn.evaluate(
      (el) => getComputedStyle(el).backgroundColor,
    );
    const popoverBg = await page
      .getByTestId("bloque-popover")
      .evaluate((el) => getComputedStyle(el).backgroundColor);

    expect(
      alphaOf(btnBg),
      `btn-save-block backgroundColor="${btnBg}" transparente en DARK (caso reportado por Chris: "el botón Guardar no existe")`,
    ).toBeGreaterThan(0);
    expect(btnBg).not.toBe(popoverBg);

    await page.screenshot({
      path: "/tmp/bug7-r3-d1-dark.png",
      fullPage: false,
    });
  });
});
