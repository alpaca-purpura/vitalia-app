// cap: clinics.lisa.doctores
// story-origin: vitalia-fase2-lisa-doctores
/**
 * ui-design-audit.spec.ts — DIAGNOSTIC ONLY (NOT a golden, NOT a gate).
 * Captura las 5 superficies de Lisa→Staff (directorio · crear modal · perfil · horarios · servicios)
 * en light mode + extrae la paleta de color real usada para cuantificar el "muy blanco y negro".
 * Throwaway: se borra tras el audit de diseño UI (no se commitea).
 * Run: E2E_BASE_URL=http://localhost:3002 npx playwright test \
 *   e2e/regression/vitalia-fase2-lisa-doctores/ui-design-audit.spec.ts --project=smoke
 */
import { test, expect } from "../../auth.fixture";

const TENANT =
  process.env["E2E_TENANT_ID"] ?? "e69a691d-070e-5caf-a053-6e74642ec100";
const DIR = "test-results/ui-audit";

async function palette(page: import("@playwright/test").Page, label: string) {
  const colors = await page.evaluate(() => {
    const seen = new Map<string, number>();
    const els = Array.from(document.querySelectorAll("body *")).slice(0, 6000);
    for (const el of els) {
      const s = getComputedStyle(el);
      for (const c of [s.color, s.backgroundColor, s.borderTopColor]) {
        if (c && c !== "rgba(0, 0, 0, 0)" && c !== "transparent") {
          seen.set(c, (seen.get(c) ?? 0) + 1);
        }
      }
    }
    return Array.from(seen.entries())
      .sort((a, b) => b[1] - a[1])
      .map(([c, n]) => `${c} ×${n}`);
  });
  // eslint-disable-next-line no-console
  console.log(`PALETTE[${label}]=` + JSON.stringify(colors));
}

test("UI DESIGN AUDIT: capture Lisa/Staff surfaces (light)", async ({
  authedPage,
}) => {
  test.setTimeout(150_000);
  await authedPage.setViewportSize({ width: 1512, height: 950 });

  authedPage.on("response", (res) => {
    const u = res.url();
    if (u.includes("/clinics/doctors") || u.includes("/availability")) {
      // eslint-disable-next-line no-console
      console.log(`NET ${res.status()} ${u.replace(/https?:\/\/[^/]+/, "")}`);
    }
  });

  // 1 — Directorio
  await authedPage.goto(`/${TENANT}/lisa/staff`, {
    waitUntil: "domcontentloaded",
  });
  await authedPage.waitForTimeout(4500);
  await authedPage.screenshot({
    path: `${DIR}/01-directorio.png`,
    fullPage: true,
  });
  await palette(authedPage, "directorio");

  // 2 — Crear modal
  const nuevo = authedPage
    .getByRole("button", { name: /nuevo|agregar|crear|integrante|doctor/i })
    .first();
  if ((await nuevo.count()) > 0) {
    await nuevo.click().catch(() => {});
    await authedPage.waitForTimeout(1800);
    await authedPage.screenshot({
      path: `${DIR}/02-crear-modal.png`,
      fullPage: true,
    });
    await authedPage.keyboard.press("Escape").catch(() => {});
    await authedPage.waitForTimeout(600);
  }

  // 3 — Perfil (abrir primer doctor del directorio)
  const link = authedPage.locator('a[href*="/lisa/staff/"]').first();
  let base = "";
  if ((await link.count()) > 0) {
    const href = (await link.getAttribute("href")) ?? "";
    // strip trailing tab segment to get workspace base
    base = href.replace(/\/(perfil|horarios|servicios)\/?$/, "");
    await authedPage.goto(`${base}/perfil`, { waitUntil: "domcontentloaded" });
    await authedPage.waitForTimeout(4000);
    await authedPage.screenshot({
      path: `${DIR}/03-perfil.png`,
      fullPage: true,
    });
    await palette(authedPage, "perfil");

    // 4 — Horarios
    await authedPage.goto(`${base}/horarios`, {
      waitUntil: "domcontentloaded",
    });
    await authedPage.waitForTimeout(4000);
    await authedPage.screenshot({
      path: `${DIR}/04-horarios.png`,
      fullPage: true,
    });

    // 5 — Servicios
    await authedPage.goto(`${base}/servicios`, {
      waitUntil: "domcontentloaded",
    });
    await authedPage.waitForTimeout(4000);
    await authedPage.screenshot({
      path: `${DIR}/05-servicios.png`,
      fullPage: true,
    });
  } else {
    // eslint-disable-next-line no-console
    console.log("NO_DOCTOR_LINK_FOUND — directorio vacío o selector distinto");
  }

  // eslint-disable-next-line no-console
  console.log("AUDIT_DONE base=" + base);
});

test("AUTOSAVE floating live-verify: perfil idle + saving→saved + marca", async ({
  authedPage,
}) => {
  test.setTimeout(140_000);
  await authedPage.setViewportSize({ width: 1512, height: 950 });

  // Reach a doctor perfil
  await authedPage.goto(`/${TENANT}/lisa/staff`, {
    waitUntil: "domcontentloaded",
  });
  await authedPage.waitForTimeout(4000);
  const href =
    (await authedPage.locator('a[href*="/lisa/staff/"]').first().getAttribute("href")) ??
    "";
  const base = href.replace(/\/(perfil|horarios|servicios)\/?$/, "");
  await authedPage.goto(`${base}/perfil`, { waitUntil: "domcontentloaded" });
  await authedPage.waitForTimeout(4000);

  const indicator = authedPage.getByTestId("autosave-indicator");
  await indicator.waitFor({ state: "visible", timeout: 10_000 });
  const idleState = await indicator.getAttribute("data-state");
  // viewport (not fullPage) screenshot → sticky pill shows pinned bottom-center
  await authedPage.screenshot({ path: `${DIR}/08-perfil-autosave-idle.png` });
  // eslint-disable-next-line no-console
  console.log("PERFIL_INDICATOR_IDLE_STATE=" + idleState);

  // Trigger a real autosave (edit años de experiencia) → saving → saved
  const years = authedPage.locator("#yearsExperience");
  await years.fill("7");
  await authedPage.waitForTimeout(2500); // debounce 600ms + PATCH + status
  const afterState = await indicator.getAttribute("data-state");
  await authedPage.screenshot({ path: `${DIR}/09-perfil-autosave-saved.png` });
  // eslint-disable-next-line no-console
  console.log("PERFIL_INDICATOR_AFTER_EDIT_STATE=" + afterState);

  // Always-visible requirement: indicator present in both states
  expect(await indicator.count()).toBeGreaterThan(0);
  // After a real edit it must have left idle (saving or saved)
  expect(["saving", "saved", "dirty"]).toContain(afterState);

  // marca/identidad — same floating standard
  await authedPage.goto(`/${TENANT}/lisa/marca/identidad`, {
    waitUntil: "domcontentloaded",
  });
  await authedPage.waitForTimeout(4500);
  const marcaIndicator = authedPage.getByTestId("autosave-indicator");
  await marcaIndicator.waitFor({ state: "visible", timeout: 10_000 });
  await authedPage.screenshot({ path: `${DIR}/10-marca-autosave.png` });
  // eslint-disable-next-line no-console
  console.log("MARCA_INDICATOR_PRESENT=" + (await marcaIndicator.count()));
  expect(await marcaIndicator.count()).toBeGreaterThan(0);
});

test("SEARCH live-verify: typing filters the directory via BE ?q=", async ({
  authedPage,
}) => {
  test.setTimeout(120_000);
  await authedPage.setViewportSize({ width: 1512, height: 950 });

  const qCalls: { status: number; q: string | null }[] = [];
  authedPage.on("response", (res) => {
    if (res.url().includes("/clinics/doctors?")) {
      const u = new URL(res.url());
      qCalls.push({ status: res.status(), q: u.searchParams.get("q") });
    }
  });

  await authedPage.goto(`/${TENANT}/lisa/staff`, {
    waitUntil: "domcontentloaded",
  });
  await authedPage.waitForTimeout(4000);

  const cardsBefore = await authedPage.locator('[data-testid^="staff-card-"]').count();
  // eslint-disable-next-line no-console
  console.log("CARDS_BEFORE=" + cardsBefore);

  // Type a search that should match exactly one seeded doctor (Ana Garcia Mendoza)
  await authedPage.getByTestId("input-buscar").fill("Ana");
  await authedPage.waitForTimeout(3500); // refetch + render

  const cardsAfter = await authedPage.locator('[data-testid^="staff-card-"]').count();
  await authedPage.screenshot({ path: `${DIR}/06-search-ana.png`, fullPage: true });
  // eslint-disable-next-line no-console
  console.log("CARDS_AFTER_ANA=" + cardsAfter);
  // eslint-disable-next-line no-console
  console.log("Q_CALLS=" + JSON.stringify(qCalls));

  // Hard assertions: BE was hit with q=Ana AND the grid shrank.
  expect(qCalls.some((c) => c.q === "Ana" && c.status === 200)).toBe(true);
  expect(cardsAfter).toBeLessThan(cardsBefore);
  expect(cardsAfter).toBeGreaterThan(0);

  // No-match search → empty state (0 cards)
  await authedPage.getByTestId("input-buscar").fill("zzqxnomatch");
  await authedPage.waitForTimeout(3000);
  const cardsNoMatch = await authedPage.locator('[data-testid^="staff-card-"]').count();
  await authedPage.screenshot({ path: `${DIR}/07-search-nomatch.png`, fullPage: true });
  // eslint-disable-next-line no-console
  console.log("CARDS_NOMATCH=" + cardsNoMatch);
  expect(cardsNoMatch).toBe(0);
});
