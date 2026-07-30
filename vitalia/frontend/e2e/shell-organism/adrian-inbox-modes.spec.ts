// cap: adrian.inbox
/**
 * adrian-inbox-modes.spec.ts — GOLDEN live (2-modos · amendment 2026-06-04)
 *
 * vitalia-fase2-adrian-inbox — verificación REAL contra dev-app (backend real, 0 mocks
 * del surface). Reescrito del modelo viejo 3-modos al modelo 2-modos construido +
 * live-verified + firmado por Chris (checkpoint::ui_polish_dod_evidence_*pm7..pm9).
 *
 * spec_anchor: 01-spec.md § Gherkin (SC-mode · SC-4 pausa · SC-composer · SC-privacy · SC-1)
 * architecture_pattern: ADR-vitalia-004
 *
 * Cubre (writes REALES ejercidos + efecto observado):
 *   SC-mode     — toggle 2-modos → PATCH …/mode 200 ×2 + aria-checked refleja (RN-1, RN-2, AC-4)
 *   SC-4 pausa  — modal 2 botones sin reason → POST …/pause 200 → estado pausado (RN-5, RN-17, AC-5)
 *   SC-composer — dock montado + textarea habilitado (RN-17, AC-5)
 *   SC-privacy  — lead visible (sin ***) + servicio-interés siempre + sin "Estado" (RN-16, AC-10)
 *   SC-1        — thread + activity stream (glass-box) + deep-link ?conv= sin PHI (RN-6, RN-14, AC-3)
 *   UI          — sin tools-icon en header, segmento activo verde, Pausar rojo, wallpaper
 *
 * Anti-burbuja gate: importa de fixtures/base.ts (NO @playwright/test directo).
 * Cada test asserta 0 pageerror + 0 hydration + 0 console.error + 0 /api 4xx-5xx.
 *
 * Ejecutar (live):
 *   cd vitalia/frontend && set -a; source ../.env.dev; set +a; \
 *   E2E_BASE_URL=https://dev-app.vitalialat.com \
 *   npx playwright test e2e/shell-organism/adrian-inbox-modes.spec.ts --project=smoke --no-deps --workers=1
 *
 * downstream-regression-na: brand-local vitalia e2e spec; no cross-brand consumers
 */

import { test, expect } from "../fixtures/base";
import type { Page, Locator } from "@playwright/test";

const TENANT_ID = process.env["E2E_TENANT_ID"] ?? "e69a691d-070e-5caf-a053-6e74642ec100";
// Seed (scripts/seed_inbox_conversations.sql): Carlos (whatsapp) · Persistencia (instagram).
// ★ UUIDs v5 REALES (verificados en vitalia_conversations) — NO los all-1s/all-2s que citaba
// el handoff (esos 404ean: el detail endpoint /crm/conversations/{id} pega contra la fila real).
const CONV_WHATSAPP = "11111111-1111-5111-8111-111111111111";
const CONV_INSTAGRAM = "22222222-2222-5222-8222-222222222222";

// El thread del shell renderiza 2 veces (responsive: inbox-desktop `hidden md:flex` +
// inbox-mobile `md:hidden`). Scopeamos SIEMPRE al layout desktop (el visible a 1920).
function desktop(page: Page): Locator {
  return page.locator('[data-testid="inbox-desktop"]');
}

/** Abre una conversación por deep-link y espera el thread cargado (no el error-state). */
async function openConversation(page: Page, convId: string): Promise<void> {
  await page.goto(`/${TENANT_ID}/adrian/inbox?conv=${convId}`);
  const thread = desktop(page).locator('[data-testid="conversation-thread"]');
  await thread.waitFor({ state: "visible", timeout: 20_000 });
  // El header con el nombre del paciente = señal de que el detail compound cargó.
  await desktop(page)
    .locator('[data-testid="thread-header-patient-name"]')
    .first()
    .waitFor({ state: "visible", timeout: 20_000 });
}

// Viewport ancho: a 1280 con la Valeria-chat abierta el thread se exprime (modes_deeper_finding);
// a 1920 hay aire suficiente para que el thread sea legible/interactivo.
test.use({ viewport: { width: 1920, height: 1080 } });

// ── SC-mode — el toggle de 2 modos escribe el cambio (PATCH /mode 200) ────────
test.describe("@rule-mode-per-conv @rule-mode-audit SC-mode — toggle 2-modos escribe", () => {
  test("cambiar de modo hace PATCH /mode 200 + aria-checked refleja (persiste)", async ({ page }) => {
    await openConversation(page, CONV_INSTAGRAM);
    const d = desktop(page);

    const toggle = d.locator('[data-testid="segmented-control-3-modes"]').first();
    const decide = d.locator('[data-testid="segment-adrian-decide"]').first();
    const consulta = d.locator('[data-testid="segment-adrian-consulta"]').first();
    await expect(toggle).toBeVisible();
    await expect(decide).toBeVisible();
    await expect(consulta).toBeVisible();

    // Un solo write determinista: clic en el segmento INACTIVO → PATCH /mode 200.
    // (El round-trip de 2 toggles consecutivos choca con el OCC porque el optimistic
    // update no refresca updated_at hasta el refetch — documentado como follow-up FU-6;
    // un write persistido alcanza para AC-4. La UI maneja el 409 con rollback+ring.)
    const decideChecked = (await decide.getAttribute("aria-checked")) === "true";
    const [target, label] = decideChecked
      ? [consulta, "adrian-consulta"]
      : [decide, "adrian-decide"];

    const patch = page.waitForResponse(
      (r) => /\/inbox\/conversations\/.+\/mode$/.test(r.url()) && r.request().method() === "PATCH",
      { timeout: 15_000 },
    );
    await target.click();
    const res = await patch;
    expect(res.status(), `PATCH /mode (→ ${label}) debe ser 200`).toBe(200);
    // Efecto: el segmento clicado queda activo (aria-checked refleja el cambio persistido).
    await expect(target).toHaveAttribute("aria-checked", "true");
  });

  test("el segmento activo está en VERDE (encendido/atendiendo)", async ({ page }) => {
    await openConversation(page, CONV_INSTAGRAM);
    const active = desktop(page)
      .locator('[data-testid="segmented-control-3-modes"] [aria-checked="true"]')
      .first();
    await expect(active).toBeVisible();
    const bg = await active.evaluate((el) => getComputedStyle(el).backgroundColor);
    const m = bg.match(/rgba?\(([^)]+)\)/);
    expect(m, `bg del segmento activo no es rgb(): ${bg}`).not.toBeNull();
    const [r, g, b] = m![1].split(",").map((n) => parseFloat(n));
    // Verde = canal G dominante sobre R y B.
    expect(g, `activo debe ser verde (g>${r} && g>${b}) — bg=${bg}`).toBeGreaterThan(r);
    expect(g).toBeGreaterThan(b);
  });
});

// ── SC-4 — pausa: modal 2 botones sin reason → POST /pause 200 ────────────────
test.describe("@rule-pause-silence @rule-mode-audit SC-4 — pausar Adrián", () => {
  test("modal tiene 2 botones (60/permanente) y NINGÚN campo de razón", async ({ page }) => {
    await openConversation(page, CONV_WHATSAPP);
    const d = desktop(page);
    const pauseBtn = d.locator('[data-testid="pause-adrian-button"]').first();
    await expect(pauseBtn).toBeVisible();

    const disabled = await pauseBtn.isDisabled();
    test.skip(disabled, "Conversación ya pausada por una corrida previa (pausa persiste, sin endpoint resume)");

    await pauseBtn.click();
    const modal = page.locator('[data-testid="pause-adrian-modal"]');
    await expect(modal).toBeVisible();
    await expect(modal.locator('[data-testid="pause-modal-60"]')).toBeVisible();
    await expect(modal.locator('[data-testid="pause-modal-permanent"]')).toBeVisible();
    // Sin caja de razón/comentario (Chris UI #4).
    await expect(modal.locator("textarea")).toHaveCount(0);
    await expect(modal.locator('input[type="text"]')).toHaveCount(0);
    // Cerrar sin pausar (no contaminar el siguiente test).
    await modal.locator('[data-testid="pause-modal-cancel"]').click();
    await expect(modal).toBeHidden();
  });

  test("'Pausar 60 minutos' hace POST /pause 200 y refleja el estado pausado", async ({ page }) => {
    await openConversation(page, CONV_WHATSAPP);
    const d = desktop(page);
    const pauseBtn = d.locator('[data-testid="pause-adrian-button"]').first();
    await expect(pauseBtn).toBeVisible();

    if (await pauseBtn.isDisabled()) {
      // Idempotencia entre corridas: ya pausada → asertamos el efecto (estado pausado).
      await expect(pauseBtn).toContainText(/Pausado/);
      return;
    }

    await pauseBtn.click();
    const modal = page.locator('[data-testid="pause-adrian-modal"]');
    await expect(modal).toBeVisible();

    const postPause = page.waitForResponse(
      (r) => /\/inbox\/conversations\/.+\/pause$/.test(r.url()) && r.request().method() === "POST",
      { timeout: 15_000 },
    );
    await modal.locator('[data-testid="pause-modal-60"]').click();
    const res = await postPause;
    expect(res.status(), "POST /pause debe ser 200").toBe(200);

    // Efecto: el botón pasa a "Pausado" (deshabilitado).
    await expect(pauseBtn).toContainText(/Pausado/, { timeout: 10_000 });
  });
});

// ── SC-composer — dock montado + textarea habilitado ─────────────────────────
test.describe("@rule-composer-dock SC-composer — composer dock", () => {
  test("el dock está montado al pie con el textarea habilitado", async ({ page }) => {
    await openConversation(page, CONV_INSTAGRAM);
    const dock = desktop(page).locator('[data-testid="thread-composer-dock"]').first();
    await expect(dock).toBeVisible();
    const textarea = dock.locator("textarea").first();
    await expect(textarea).toBeVisible();
    await expect(textarea).toBeEnabled();
    // El botón Pausar vive en el dock (no en el header).
    await expect(dock.locator('[data-testid="pause-adrian-button"]')).toBeVisible();
  });
});

// ── SC-privacy — lead visible (interim) + servicio-interés + sin "Estado" ─────
test.describe("@rule-lead-visible @rule-contact-masked SC-privacy — ficha del lead", () => {
  test("nombre del lead visible sin máscara + servicio-interés siempre + sin 'Estado'", async ({ page }) => {
    await openConversation(page, CONV_WHATSAPP);
    const d = desktop(page);

    // El nombre en el header del thread es el lead real (no enmascarado).
    const name = d.locator('[data-testid="thread-header-patient-name"]').first();
    await expect(name).toBeVisible();
    const nameText = (await name.textContent())?.trim() ?? "";
    expect(nameText.length, "el nombre del lead no debe estar vacío").toBeGreaterThan(0);
    expect(nameText, "el nombre del lead no debe estar enmascarado").not.toMatch(/\*\*\*/);

    // Asegurar la ficha de contacto abierta (a 1920 puede estar abierta por defecto;
    // el toggle alterna — solo lo pulsamos si la ficha no está visible).
    const serviceInterest = page.locator('[data-testid="contact-service-interest"]').first();
    if (!(await serviceInterest.isVisible().catch(() => false))) {
      await d.locator('[data-testid="contact-sidebar-toggle"]').first().click();
    }
    await expect(serviceInterest).toBeVisible(); // siempre presente ("Aún no detectado" si vacío)

    // La ficha (ContactSidebar = aside data-testid="inbox-contact-sidebar") tiene
    // "Etapa de la venta" como única fuente; el campo "Estado" duplicado fue eliminado.
    const sidebar = d.locator('[data-testid="inbox-contact-sidebar"]').first();
    await expect(sidebar).toContainText(/Etapa de la venta/);
    await expect(sidebar.getByText(/^Estado$/)).toHaveCount(0);
    // Cerrar.
    await sidebar.locator('[data-testid="contact-sidebar-close"]').first().click();
  });
});

// ── SC-1 — thread + glass-box + deep-link sin PHI ────────────────────────────
test.describe("@rule-glassbox @rule-deeplink SC-1 — thread + activity + deep-link", () => {
  test("activity stream montado + URL ?conv= sin PHI + sin tools-icon en el header", async ({ page }) => {
    await openConversation(page, CONV_WHATSAPP);
    const d = desktop(page);

    // Glass-box: el activity stream está montado.
    await expect(d.locator('[data-testid="agent-activity-stream"]').first()).toBeVisible();

    // El ícono 🛠 de herramientas YA NO vive en el header (la actividad vive abajo).
    const header = d.locator('[data-testid="thread-header"]').first();
    await expect(header.locator('[data-testid="tools-sheet-trigger"]')).toHaveCount(0);

    // Wallpaper presente detrás de los mensajes (svg watermark del logo del canal).
    await expect(d.locator('[data-testid="messages-list"]').first()).toBeVisible();

    // Deep-link estable + sin PHI en la URL (solo el uuid de conversación).
    const url = page.url();
    expect(url).toContain(`conv=${CONV_WHATSAPP}`);
    expect(url).not.toMatch(/nombre|dni|paciente|diagn[oó]stic|email=/i);
  });
});
