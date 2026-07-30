// cap: clinics.lisa.doctores
// story-origin: vitalia-fase2-lisa-doctores
/**
 * bug7-r3-d2-drag-create.spec.ts — D-2: drag-create clon Google Calendar.
 *
 * BUG (G round-2, Chris): "se ha malogrado la creación de bloque arrastrando
 * el mouse — no se seleccionan las celdas y sale el popup solo".
 *
 * Target GCal:
 *   - arrastrar pinta el rango EN VIVO (highlight celdas)
 *   - soltar abre el editor con ESE rango (no 1 hora default)
 *   - click simple (sin drag) crea draft de 1 hora en esa celda
 *
 * RED first contra stack real (FE:3002 + BE:8002, sin mocks del surface).
 *
 * WORK-ORDER-bug7-round3.md § D-2
 */

import { test, expect } from "../../fixtures/authed-runtime";
import {
  gotoHorarios,
  dragWithoutRelease,
  clickCell,
} from "./bug7-helpers";

test.describe("bug7 r3 · D-2 — drag-create Google Calendar", () => {
  test("drag sáb 09→11: pinta el rango en vivo y abre popover 09:00–12:00", async ({
    page,
  }) => {
    await gotoHorarios(page);

    // Drag down from 09 to 11 WITHOUT releasing
    await dragWithoutRelease(page, 5, 9, 11);

    // Mid-drag: las 3 celdas del rango deben estar pintadas (highlight live).
    // El highlight (bg-agent-lisa-soft) se aplica al DIV PADRE del DroppableCell.
    const highlighted = await page.evaluate(() => {
      return [9, 10, 11].map((h) => {
        const cell = document.querySelector(`[data-testid="cell-5-${h}"]`);
        const parent = cell?.parentElement;
        return parent?.className.includes("bg-agent-lisa-soft") ?? false;
      });
    });
    expect(
      highlighted,
      `Durante el drag las celdas 09/10/11 deben pintarse — got [${highlighted.join(", ")}] (D-2: "no se seleccionan las celdas")`,
    ).toEqual([true, true, true]);

    await page.screenshot({ path: "/tmp/bug7-r3-d2-mid-drag.png" });

    // Release → popover con el rango arrastrado
    await page.mouse.up();
    await expect(page.getByTestId("bloque-popover")).toBeVisible();
    await expect(
      page.locator("#startTime"),
      "popover debe abrir con startTime = inicio del drag (09:00)",
    ).toHaveValue("09:00");
    await expect(
      page.locator("#endTime"),
      "popover debe abrir con endTime = fin del drag (12:00), no 1 hora default",
    ).toHaveValue("12:00");

    // Cancelar — este test no escribe
    await page.keyboard.press("Escape");
    await expect(page.getByTestId("bloque-popover")).toBeHidden();
  });

  test("drag inverso sáb 14→12 (hacia arriba): rango normalizado 12:00–15:00", async ({
    page,
  }) => {
    await gotoHorarios(page);

    await dragWithoutRelease(page, 5, 14, 12);
    await page.mouse.up();

    await expect(page.getByTestId("bloque-popover")).toBeVisible();
    await expect(page.locator("#startTime")).toHaveValue("12:00");
    await expect(page.locator("#endTime")).toHaveValue("15:00");

    await page.keyboard.press("Escape");
  });

  test("click simple (sin drag) abre popover con 1 hora en esa celda", async ({
    page,
  }) => {
    await gotoHorarios(page);

    await clickCell(page, 5, 16);

    await expect(page.locator("#startTime")).toHaveValue("16:00");
    await expect(page.locator("#endTime")).toHaveValue("17:00");

    await page.keyboard.press("Escape");
  });

  test("drag ATRAVESANDO un bloque existente: el rango sigue creciendo (modo de rotura de Chris)", async ({
    page,
  }) => {
    // El doctor demo tiene bloques L/M/J por la mañana (p.ej. lunes 08:00-13:00).
    // Pre-fix: el overlay del bloque (pointer-events-auto) tapaba los
    // mouseenter/mouseup de las celdas → al arrastrar desde una celda vacía
    // hacia/sobre el bloque "no se seleccionan las celdas y sale el popup solo"
    // (el click aterrizaba en el bloque → popover de EDICIÓN).
    // GCal: el drag iniciado en celda vacía atraviesa eventos existentes.
    await gotoHorarios(page);

    // Los bloques existentes del doctor demo (lun 08-13 + lun/mar/jue 09-14)
    // están anclados a su created_at (2026-06-12) → proyectan desde la semana
    // SIGUIENTE. Navegamos allí para tener la mañana del lunes cubierta.
    await page.getByTestId("week-nav-next").click();
    await expect(
      page.getByTestId(/^block-/).first(),
      "precondición: la semana siguiente debe tener bloques existentes pintados",
    ).toBeVisible({ timeout: 10_000 });

    // Drag lunes 15:00 → 11:00 (hacia arriba): las celdas 14..11 están
    // CUBIERTAS por los bloques existentes — pre-fix el gesto moría ahí.
    await dragWithoutRelease(page, 0, 15, 11);
    await page.mouse.up();

    await expect(
      page.getByTestId("bloque-popover"),
      "el popover de CREACIÓN debe abrir (no el de edición del bloque existente)",
    ).toBeVisible();
    await expect(page.getByRole("dialog").locator("h3")).toHaveText(
      "Nuevo bloque",
    );
    await expect(
      page.locator("#startTime"),
      "el rango debe incluir las horas cubiertas por el bloque existente",
    ).toHaveValue("11:00");
    await expect(page.locator("#endTime")).toHaveValue("16:00");

    await page.keyboard.press("Escape");
  });
});
