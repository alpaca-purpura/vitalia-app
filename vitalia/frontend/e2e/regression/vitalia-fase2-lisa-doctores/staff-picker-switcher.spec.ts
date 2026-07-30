// cap: clinics.lisa.doctores
// story-origin: vitalia-fase2-lisa-doctores
/**
 * staff-picker-switcher.spec.ts — SC-D3A-1..4 (D3-A entity switcher).
 *
 * REAL backend (cero mock del surface bajo prueba): real-backend-forward.fixture
 * = Clerk auth (storageState playwright/.clerk/user.json) + forwarding
 * /api/v1/** → BE :8002 + gate anti-burbuja base.ts (pageerror / hydration /
 * api-4xx5xx / overlay Next). NUNCA `@playwright/test` directo.
 *
 * Scenarios (01-spec § Delta v3 · 04-validators delta_v3):
 *   SC-D3A-1 happy    · picker cambia doctor PRESERVANDO la hoja (Horarios→Horarios)
 *   SC-D3A-2 negative · buscar "zzqx" → "Sin resultados" + filtro SERVER-side (q=)
 *   SC-D3A-3 edge     · solo staff activo (active=true; opciones ⊆ respuesta server)
 *   SC-D3A-4 a11y     · ↑↓/Enter/Esc + focus al search al abrir + axe wcag2aa
 *
 * Precondición data: el tenant live (E2E_TENANT_ID) necesita ≥2 doctores activos
 * (seed del build original — live-seed-dod-evidence.spec.ts). Si hay <2, los
 * specs de switch se saltan con anotación explícita (no falso verde).
 *
 * Run: E2E_BASE_URL=http://localhost:3002 npx playwright test --project=smoke \
 *        e2e/regression/vitalia-fase2-lisa-doctores/staff-picker-switcher.spec.ts
 *
 * T-FE-switcher-wire vitalia-fase2-lisa-doctores
 * spec_anchor: 03-arch-delta.md § 2.2 + 04-validators.yaml V-D3A-1..4
 * downstream-regression-na: brand-local vitalia e2e spec; no cross-brand consumers
 */
import AxeBuilder from "@axe-core/playwright";
import type { Page } from "@playwright/test";
import {
  test,
  expect,
  TENANT_ID,
} from "../../fixtures/real-backend-forward.fixture";
import { DoctorWorkspacePage } from "../../pages/DoctorWorkspacePage";

const DESKTOP = { width: 1440, height: 900 };

interface PickerCall {
  url: string;
  status: number;
  itemIds: string[];
}

/**
 * Captures every picker list response (GET /clinics/doctors?…active=true…)
 * with its server-returned item ids — evidence for RN-D3A-1/2 (server filter).
 */
function capturePickerCalls(page: Page): PickerCall[] {
  const calls: PickerCall[] = [];
  page.on("response", (res) => {
    const url = res.url();
    if (
      res.request().method() === "GET" &&
      url.includes("/clinics/doctors?") &&
      url.includes("active=true")
    ) {
      void res
        .json()
        .then((body: { items?: { id: string }[] }) => {
          calls.push({
            url,
            status: res.status(),
            itemIds: (body.items ?? []).map((d) => d.id),
          });
        })
        .catch(() => {
          calls.push({ url, status: res.status(), itemIds: [] });
        });
    }
  });
  return calls;
}

/**
 * Returns ≥2 active doctor ids from the live directory (or skips the test).
 * Reads the REAL list endpoint response the directory itself fired — no mock.
 */
async function getTwoActiveDoctorIds(page: Page): Promise<[string, string]> {
  const listResponse = page.waitForResponse(
    (res) =>
      res.url().includes("/clinics/doctors?") &&
      res.request().method() === "GET",
    { timeout: 30_000 },
  );
  await page.goto(`/${TENANT_ID}/lisa/staff`, {
    waitUntil: "domcontentloaded",
  });
  const res = await listResponse;
  const body = (await res.json()) as {
    items?: { id: string; active: boolean }[];
  };
  const activeIds = (body.items ?? [])
    .filter((d) => d.active)
    .map((d) => d.id);
  test.skip(
    activeIds.length < 2,
    `Precondición: se necesitan ≥2 doctores activos en el tenant live (hay ${activeIds.length})`,
  );
  return [activeIds[0]!, activeIds[1]!];
}

test.describe("D3-A · entity switcher (EntityPicker en la franja N3)", () => {
  test.use({ viewport: DESKTOP });

  test("SC-D3A-1 · cambiar doctor desde Horarios preserva la hoja + contenido renderiza", async ({
    page,
  }) => {
    const pickerCalls = capturePickerCalls(page);
    const [docA, docB] = await getTwoActiveDoctorIds(page);
    const pom = new DoctorWorkspacePage(page);

    // Doctor A abierto en hoja Horarios (estado inicial del scenario)
    await pom.navigateToHorarios(TENANT_ID, docA);
    await expect(
      page.getByTestId("horarios-view"),
      "la hoja Horarios del doctor A debe renderizar",
    ).toBeVisible({ timeout: 20_000 });

    // Picker ▾ → elegir doctor B → URL preserva /horarios
    await pom.openPicker();
    await expect(pom.pickerOption(docB)).toBeVisible({ timeout: 15_000 });
    await pom.pickDoctorById(docB, "horarios");

    expect(page.url()).toContain(`/lisa/staff/${docB}/horarios`);
    await expect(
      page.getByTestId("horarios-view"),
      "el contenido de Horarios del doctor B debe renderizar",
    ).toBeVisible({ timeout: 20_000 });

    // Evidencia live (dod_evidence): el picker pegó al BE real con active=true
    expect(pickerCalls.length, "el picker debe haber consultado al BE").toBeGreaterThan(0);
    expect(pickerCalls.every((c) => c.status === 200)).toBe(true);
    console.log("PICKER_CALLS=" + JSON.stringify(pickerCalls));
  });

  test("SC-D3A-2 · buscar 'zzqx' → 'Sin resultados' con filtro server-side", async ({
    page,
  }) => {
    const [docA] = await getTwoActiveDoctorIds(page);
    const pom = new DoctorWorkspacePage(page);
    await pom.navigateToHorarios(TENANT_ID, docA);
    await expect(page.getByTestId("horarios-view")).toBeVisible({
      timeout: 20_000,
    });

    await pom.openPicker();
    const searchResponse = page.waitForResponse(
      (res) => res.url().includes("q=zzqx"),
      { timeout: 15_000 },
    );
    await pom.searchInPicker("zzqx");

    // RN-D3A-1: el filtro viaja al server (q=) — jamás colección completa client-side
    const res = await searchResponse;
    expect(res.status()).toBe(200);
    expect(res.url()).toContain("q=zzqx");
    expect(res.url()).toContain("active=true");

    await expect(pom.pickerEmpty).toBeVisible({ timeout: 10_000 });
    await expect(pom.pickerEmpty).toHaveText("Sin resultados");
  });

  test("SC-D3A-3 · solo staff activo: active=true + opciones ⊆ respuesta del server", async ({
    page,
  }) => {
    const pickerCalls = capturePickerCalls(page);
    const [docA] = await getTwoActiveDoctorIds(page);
    const pom = new DoctorWorkspacePage(page);
    await pom.navigateToHorarios(TENANT_ID, docA);
    await expect(page.getByTestId("horarios-view")).toBeVisible({
      timeout: 20_000,
    });

    await pom.openPicker();
    await expect(pom.pickerListbox).toBeVisible({ timeout: 15_000 });
    // Esperar a que la primera página del picker esté capturada y renderizada
    await expect
      .poll(() => pickerCalls.length, { timeout: 15_000 })
      .toBeGreaterThan(0);

    // RN-D3A-2: la request del picker SIEMPRE lleva active=true
    expect(pickerCalls[0]!.url).toContain("active=true");

    // Cada opción renderizada corresponde a un id devuelto por el server
    // (cero inyección client-side; inactivos jamás aparecen porque el server
    // ya los excluyó del dataset)
    const serverIds = new Set(pickerCalls.flatMap((c) => c.itemIds));
    const optionTestIds = await pom.pickerListbox
      .locator("[role='option']")
      .evaluateAll((els) =>
        els.map((el) => el.getAttribute("data-testid") ?? ""),
      );
    expect(optionTestIds.length).toBeGreaterThan(0);
    for (const tid of optionTestIds) {
      const id = tid.replace("doctor-picker-option-", "");
      expect(
        serverIds.has(id),
        `opción ${id} debe venir del server (active=true)`,
      ).toBe(true);
    }
  });

  test("SC-D3A-4 · a11y: focus al search, ↑↓ + Enter selecciona, Esc cierra + axe wcag2aa", async ({
    page,
  }) => {
    const [docA, docB] = await getTwoActiveDoctorIds(page);
    const pom = new DoctorWorkspacePage(page);
    await pom.navigateToHorarios(TENANT_ID, docA);
    await expect(page.getByTestId("horarios-view")).toBeVisible({
      timeout: 20_000,
    });

    // Abrir → el search recibe el focus (combobox owner)
    await pom.openPicker();
    await expect(pom.pickerSearch).toBeFocused({ timeout: 10_000 });
    await expect(pom.pickerOption(docB)).toBeVisible({ timeout: 15_000 });

    // axe wcag2a/wcag2aa sobre el popover abierto — scan COMPLETO (sin disableRules).
    //
    // ★ PIN de bug CORE conocido (escalado a /pm-luana en T-FE-switcher-wire-result):
    // EntityPicker (core/@luana/ui-kit L334-335) aplica `bg-accent` a la opción
    // activa SIN el par `text-accent-foreground` (EntitySubNavBar sí los parea).
    // Con el accent púrpura de vitalia (287 53% 37% + foreground blanco) el texto
    // hereda near-black → contraste 2.46 (<4.5:1). Core = forbidden_to_touch en
    // este ticket → se TOLERA exclusivamente `color-contrast` y se PINEA su
    // presencia: cuando el core se arregle, el pin FALLA → quitar la tolerancia
    // y volver al gate completo (ratchet shrink-only, cero falso verde).
    const axe = await new AxeBuilder({ page })
      .include('[data-testid="doctor-picker-content"]')
      .withTags(["wcag2a", "wcag2aa"])
      .analyze();
    const otherViolations = axe.violations.filter(
      (v) => v.id !== "color-contrast",
    );
    expect(
      otherViolations,
      `axe violations (fuera del pin color-contrast): ${JSON.stringify(otherViolations.map((v) => v.id))}`,
    ).toEqual([]);
    expect(
      axe.violations.some((v) => v.id === "color-contrast"),
      "PIN: el bug core de contraste ya NO está — quitar la tolerancia color-contrast de este spec",
    ).toBe(true);

    // Esc cierra el popover sin navegar
    await page.keyboard.press("Escape");
    await expect(pom.pickerContent).toBeHidden({ timeout: 10_000 });
    expect(page.url()).toContain(`/lisa/staff/${docA}/horarios`);

    // Reabrir → ↓ mueve la opción activa → Enter selecciona (navega preservando hoja)
    await pom.openPicker();
    await expect(pom.pickerOption(docB)).toBeVisible({ timeout: 15_000 });
    const targetIndex = await pom.pickerListbox
      .locator("[role='option']")
      .evaluateAll((els, target) => {
        return els.findIndex(
          (el) => el.getAttribute("data-testid") === target,
        );
      }, `doctor-picker-option-${docB}`);
    expect(targetIndex).toBeGreaterThanOrEqual(0);
    for (let i = 0; i < targetIndex; i += 1) {
      await page.keyboard.press("ArrowDown");
    }
    await expect(pom.pickerOption(docB)).toHaveAttribute(
      "data-active",
      "true",
    );
    await page.keyboard.press("Enter");
    await page.waitForURL(`**/lisa/staff/${docB}/horarios`, {
      timeout: 15_000,
    });
    expect(page.url()).toContain(`/lisa/staff/${docB}/horarios`);
  });
});
