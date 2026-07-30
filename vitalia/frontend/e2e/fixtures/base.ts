/**
 * base.ts — Runtime-error gate (Critical Rule #37 §3 · gate anti-burbuja)
 *
 * Convierte el harness de "verde si la request fue 200" a "verde si el cliente
 * NO vio ningún error". Atrapa lo que `GET 200` oculta porque ocurre en el
 * cliente DESPUÉS de la hidratación:
 *   - la burbuja roja de Next.js  → page.on('pageerror')   (excepción JS no atrapada)
 *   - errores de React / hidratación → page.on('console')  (HYDRATION_ERROR_PATTERNS)
 *   - 4xx/5xx en /api/ que la UI traga en un catch → page.on('response')
 *   - el overlay de error de Next en el DOM → expect(nextjs-portal).toHaveCount(0)
 *
 * Diferencia clave con `auth.fixture.ts::collectConsoleErrors` (legacy): ese
 * IGNORA "Hydration"/"500"/"404" (los swallowea). Acá esos DEBEN fallar. La
 * allowlist es TIGHT (solo ruido de infra no-accionable) y solo shrink.
 *
 * Uso en specs nuevos:
 *   import { test, expect } from '../fixtures/base';
 *
 * Composición con auth (futuro, al migrar specs autenticados):
 *   import { mergeTests } from '@playwright/test';
 *   import { test as runtimeGate } from '../fixtures/base';
 *   import { test as authed } from '../auth.fixture';
 *   export const test = mergeTests(runtimeGate, authed);
 *
 * Opt-out cuando un test ejerce un error a propósito:
 *   test.use({ failOnRuntimeError: false });
 */
import { test as base, expect } from "@playwright/test";
import type { Page } from "@playwright/test";

// Allowlist TIGHT — solo ruido de infra no-accionable. NO incluye hydration / 5xx
// / 404 (esos DEBEN fallar el gate). Agregar entradas requiere justificación
// (ratchet: shrink-only).
const CONSOLE_ERROR_ALLOWLIST: RegExp[] = [
  /ClerkJS/i,
  /clerk\.com/i,
  /Could not parse CSS/i,
  /Download the React DevTools/i,
  // 401 = redirect de auth esperado en rutas gated (no es un bug de runtime)
  /Failed to load resource: the server responded with a status of 401/i,
  // SC-12 (n3-directory-disabled): tests deliberadamente navegan a UUIDs falsos
  // (00000000-0000-0000-0000-000000000000) para verificar que el shell muestra
  // 404/redirect. El API 404 de ese recurso fake ES la verificación esperada.
  // QUIRÚRGICO: solo el all-zeros UUID (el propio test lo provoca).
  /404.*\/(doctors|leads)\/00000000-0000-0000-0000-000000000000/i,
];

// SC-12 allowlist para failedApi: requests que el propio test genera a propósito
// (navegación a UUID fake all-zeros — el 404 es la verificación esperada).
const FAILED_API_ALLOWLIST: RegExp[] = [
  /\/00000000-0000-0000-0000-000000000000/,
];

// Errores de hidratación React/Next SSR — insidiosos: la UI se ve igual, status
// 200, pero el DOM quedó inconsistente. SIEMPRE fallan el gate.
const HYDRATION_ERROR_PATTERNS: RegExp[] = [
  /hydration failed because the server rendered html didn't match the client/i,
  /hydration completed but contains mismatches/i,
  /there was an error while hydrating/i,
  /did not expect server html to contain/i,
  /text content does not match server-rendered html/i,
];

export type RuntimeErrorFixtures = {
  /** Apagar el gate para tests que ejercen un error a propósito. */
  failOnRuntimeError: boolean;
};

export type RuntimeErrorCollections = {
  pageErrors: string[];
  consoleErrors: string[];
  hydrationErrors: string[];
  failedApi: string[];
};

/** Adjunta los 4 colectores a una página. Devuelve las colecciones (vivas). */
export function attachRuntimeErrorGuards(page: Page): RuntimeErrorCollections {
  const c: RuntimeErrorCollections = {
    pageErrors: [],
    consoleErrors: [],
    hydrationErrors: [],
    failedApi: [],
  };
  page.on("pageerror", (err) => {
    c.pageErrors.push(`${err.name}: ${err.message}`);
  });
  page.on("console", (msg) => {
    if (msg.type() !== "error") return;
    const text = msg.text();
    if (HYDRATION_ERROR_PATTERNS.some((p) => p.test(text))) {
      c.hydrationErrors.push(text);
      return;
    }
    // T-V2 fix-loop: el allowlist se evalúa sobre el string COMPUESTO (text + URL).
    // "Failed to load resource" del browser NO incluye la URL en msg.text() — viene
    // en msg.location(); sin componer, patrones con path (ej. SC-12 all-zeros UUID)
    // jamás matchean.
    const loc = msg.location();
    const composed = `${text} @ ${loc.url}:${loc.lineNumber}`;
    if (!CONSOLE_ERROR_ALLOWLIST.some((re) => re.test(composed))) {
      c.consoleErrors.push(composed);
    }
  });
  page.on("response", (r) => {
    if (r.status() >= 400 && /\/api\//.test(r.url())) {
      if (!FAILED_API_ALLOWLIST.some((re) => re.test(r.url()))) {
        c.failedApi.push(`${r.request().method()} ${r.url()} → ${r.status()}`);
      }
    }
  });
  return c;
}

/**
 * Aserta que el DIÁLOGO de error de Next.js dev NO está en el DOM.
 *
 * ⚠️ `<nextjs-portal>` SIEMPRE existe en `next dev` (hostea el dev-indicator +
 * toasts) — NO es señal de error. El error real es el DIÁLOGO modal dentro del
 * portal: `[data-nextjs-dialog]` / `[data-nextjs-error-overlay]`. Detectamos ESO.
 */
export async function expectNoNextErrorOverlay(page: Page): Promise<void> {
  const errorDialog = page.locator(
    "[data-nextjs-dialog], [data-nextjs-error-overlay], nextjs-portal [role='alertdialog']",
  );
  await expect(
    errorDialog,
    "El diálogo de error de Next.js (la burbuja roja) está en el DOM",
  ).toHaveCount(0);
}

/** Aserta que ninguna colección tiene errores. Llamar al final del test. */
export function assertNoRuntimeErrors(c: RuntimeErrorCollections): void {
  expect(
    c.pageErrors,
    `Excepciones JS no atrapadas (la burbuja de Next): ${c.pageErrors.join(" | ")}`,
  ).toEqual([]);
  expect(
    c.hydrationErrors,
    `Errores de hidratación React/SSR: ${c.hydrationErrors.join(" | ")}`,
  ).toEqual([]);
  expect(
    c.consoleErrors,
    `console.error en el browser: ${c.consoleErrors.join(" | ")}`,
  ).toEqual([]);
  expect(
    c.failedApi,
    `Respuestas /api/ 4xx-5xx que la UI pudo haber tragado: ${c.failedApi.join(" | ")}`,
  ).toEqual([]);
}

/**
 * Test extendido con el gate anti-burbuja activo por defecto. Cada test colecta
 * errores durante toda su vida y asserta vacío al teardown.
 */
export const test = base.extend<RuntimeErrorFixtures>({
  failOnRuntimeError: [true, { option: true }],
  page: async ({ page, failOnRuntimeError }, use) => {
    const collected = attachRuntimeErrorGuards(page);
    await use(page);
    if (!failOnRuntimeError) return;
    if (!page.isClosed()) {
      await expectNoNextErrorOverlay(page);
    }
    assertNoRuntimeErrors(collected);
  },
});

/**
 * Gate de render-sanity (HB-68): aserta que el SHELL montó con contenido REAL
 * antes de correr axe / `toHaveScreenshot` / aserciones de contraste.
 *
 * El bug origen: varios runs "verdes" del hardening escaneaban un shell COLGADO
 * (DOM "Cargando" casi vacío por el flake next16-softnav) → axe reportaba
 * 0-violations sobre nada + asserts imposibles pasaban PASS sobre un DOM
 * desmontado. Un `axe` verde sobre un shell vacío es un FALSO NEGATIVO.
 *
 * Llamá `assertShellMounted(page)` INMEDIATAMENTE antes de cualquier axe/visual:
 *   await page.goto(ruta);
 *   await assertShellMounted(page);   // ← gate
 *   const a = await new AxeBuilder({ page }).analyze();
 *
 * Falla RUIDOSO (no silencioso) si: el root del shell no existe · el área de
 * contenido no tiene hijos · sigue visible el estado "Cargando".
 */
export async function assertShellMounted(page: Page): Promise<void> {
  // 1. El shell CLIENTE del kit (@luana/ui-kit ShellLayout) DEBE estar montado Y
  //    reconciliado: <main id="main-content" data-shell-ready="true">. La SSR
  //    skeleton es aria-label="Cargando" SIN data-shell-ready → no matchea, así
  //    que esto espera al cliente real (anti falso-negativo HB-68).
  //    Reemplaza el viejo div[aria-label="Interfaz principal Vitalia"] del AppShell
  //    pre-migración a @luana/ui-kit (shell/AppShell.tsx MUERTO; ShellLayoutWire T-V1).
  // Timeout holgado: el cliente es dynamic({ssr:false}) y en `next dev` la PRIMERA
  // carga de una ruta compila on-demand (>5s en frío). Es un wait-for, resuelve
  // apenas reconcilia — no penaliza el caso warm. (Probado: dsr="true" ~10s en frío.)
  await expect(
    page.locator('main#main-content[data-shell-ready="true"]'),
    "Shell no montado — el cliente del kit no reconcilió (data-shell-ready≠true; ¿shell colgado?)",
  ).toHaveCount(1, { timeout: 20000 });

  // 2. El área de contenido (#main-content) DEBE existir con ≥1 hijo real
  const main = page.locator("main#main-content");
  await expect(main, "#main-content no está en el DOM").toHaveCount(1);
  await expect(
    main.locator("> *").first(),
    "#main-content sin hijos — shell colgado/vacío, axe/visual escanearían la nada",
  ).toBeAttached();

  // 3. El estado "Cargando" NO debe estar visible (sino el shell sigue cargando)
  const loading = page.locator("text=/Cargando/i").first();
  const stillLoading = await loading.isVisible().catch(() => false);
  expect(
    stillLoading,
    'Shell aún en estado "Cargando" — esperá el contenido real antes de axe/visual',
  ).toBe(false);
}

export { expect };
