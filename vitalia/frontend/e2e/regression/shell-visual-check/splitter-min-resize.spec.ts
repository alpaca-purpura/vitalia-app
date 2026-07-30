// cap: shell-organism.shell-vitalia
// story-origin: hotfix visual review (2026-05-29) — regresión resize min splitter
/**
 * splitter-min-resize.spec.ts — verifica que arrastrar el splitter a tope-izquierda
 * NO encoge el panel de Valeria por debajo de su mínimo (580px full / 360px rail).
 * "Esto lo habíamos resuelto y ya no funciona" (Chris). Test REAL autenticado, sin mock.
 */
import { test, expect } from "@playwright/test";

const T = "e69a691d-070e-5caf-a053-6e74642ec100";

test("arrastrar splitter a tope-izq respeta el min del panel Valeria (no colapsa el chat)", async ({
  page,
}) => {
  // UPDATED: paradigm-map-zones T-6 (2026-05-30) — route migrated to mateo/agenda
  await page.goto(`/${T}/mateo/agenda`, { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(3500);

  const sep = page.locator('[aria-label="Redimensionar paneles"]').first();
  await expect(sep).toBeVisible();

  const before = await sep.boundingBox();
  console.log("separator.x ANTES:", before?.x);

  // Drag el handle lo más a la izquierda posible
  const cx = (before?.x ?? 0) + (before?.width ?? 0) / 2;
  const cy = (before?.y ?? 0) + (before?.height ?? 0) / 2;
  await page.mouse.move(cx, cy);
  await page.mouse.down();
  await page.mouse.move(20, cy, { steps: 25 });
  await page.mouse.up();
  await page.waitForTimeout(800);

  const after = await sep.boundingBox();
  console.log("separator.x DESPUES (drag tope-izq):", after?.x);
  // separator.x ≈ ancho del panel Valeria. Min full=580, rail=360. Toleramos 560.
  expect(
    after?.x ?? 0,
    `El panel Valeria colapsó a ${after?.x}px (< min). El resize min está roto.`,
  ).toBeGreaterThanOrEqual(560);
});

test("arrastrar splitter a tope-DER respeta el min del panel app (contenedores derecha no colapsan)", async ({
  page,
}) => {
  // UPDATED: paradigm-map-zones T-6 (2026-05-30) — route migrated to mateo/agenda
  await page.goto(`/${T}/mateo/agenda`, { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(3500);

  const vw = page.viewportSize()?.width ?? 1280;
  const sep = page.locator('[aria-label="Redimensionar paneles"]').first();
  await expect(sep).toBeVisible();
  const before = await sep.boundingBox();
  console.log("viewport:", vw, "separator.x ANTES:", before?.x);

  const cx = (before?.x ?? 0) + (before?.width ?? 0) / 2;
  const cy = (before?.y ?? 0) + (before?.height ?? 0) / 2;
  await page.mouse.move(cx, cy);
  await page.mouse.down();
  await page.mouse.move(vw - 20, cy, { steps: 25 });
  await page.mouse.up();
  await page.waitForTimeout(800);

  const after = await sep.boundingBox();
  const appWidth = vw - (after?.x ?? 0);
  console.log("separator.x DESPUES (drag tope-der):", after?.x, "→ ancho app:", appWidth);
  // ancho panel app = vw - separator.x. Min app = 480px. Toleramos 460.
  expect(
    appWidth,
    `El panel app (derecha) colapsó a ${appWidth}px (< min 480). El resize min está roto.`,
  ).toBeGreaterThanOrEqual(460);
});
