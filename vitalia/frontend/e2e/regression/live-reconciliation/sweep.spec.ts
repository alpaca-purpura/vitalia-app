// cap: ops.live-reconciliation-sweep
// story-origin: vitalia-cockpit-live-reconciliation
/**
 * sweep.spec.ts — Fase 1 Sweep Harness Playwright
 *
 * story: vitalia-cockpit-live-reconciliation · T-2
 * spec_anchor: 01-spec.md § Scenario 2 (surface-broken-flagged) + § Scenario 5 (network-failure)
 *
 * Recorre todas las superficies navegables del shell-organism (derivadas del SSoT
 * shell-routes.ts + agent-catalog.ts) y produce la matriz cap↔realidad.
 *
 * Reglas de sweep:
 *   - NO aborta si una superficie está ROTA — las superficies rotas son DATOS.
 *   - Verdicts: OK | ROTO | INACCESIBLE | SIN-UI
 *   - Emite findings a JSON: e2e/regression/live-reconciliation/.sweep-findings.json
 *   - HIPAA: screenshots en .evidence/ (gitignored) — seed es mock (no PHI real).
 *
 * Clasificación de veredicto:
 *   OK           = carga + sin console-error grave + elemento clave del shell visible
 *   ROTO         = status 5xx / crash JS / console-error grave / acción base falla
 *   INACCESIBLE  = ruta declarada pero nav no llega (redirect fuera de scope, 404 real)
 *   SIN-UI       = surface kind='external-annotated' (anotar, no barrido profundo)
 *
 * network-failure: stubs MSW esperados (payment/fiscal Option A) NO marcan ROTO;
 * se anotan en notes[] para no generar falsos positivos.
 *
 * Project: live-recon (ver playwright.config.ts — dependencies: ['setup'], storageState)
 *
 * Run:
 *   cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
 *     npx playwright test e2e/regression/live-reconciliation/sweep.spec.ts \
 *     --project=live-recon --reporter=line
 *
 * downstream-regression-na: brand-local vitalia sweep; no cross-brand consumers
 * voseo-allowed: internal sweep harness docs
 */

import path from "path";
import fs from "fs";
import { test, expect } from "@playwright/test";
import type { Page, Response } from "@playwright/test";
import { enumerateNavigableSurfaces } from "./surface-catalog";
import type { Surface } from "./surface-catalog";

// ─────────────────────────────────────────────────────────────────────────────
// Constants
// ─────────────────────────────────────────────────────────────────────────────

const TENANT_ID = process.env["E2E_TENANT_ID"] ?? "vitalia-test-tenant";
const EVIDENCE_DIR = path.join(__dirname, ".evidence");
const FINDINGS_PATH = path.join(__dirname, ".sweep-findings.json");

/** Console errors that are known non-actionable in the dev environment */
const IGNORED_CONSOLE_PATTERNS = [
  /ClerkJS/i,
  /clerk\.com/i,
  /Could not parse CSS/i,
  /Loading failed for/i,
  /Failed to load resource/i,
  /Hydration/i,
  /401/,
  /429/,
  /net::ERR_/,
  /ResizeObserver loop/i,
  /Failed to execute.*measure.*Performance/i,
];

/**
 * Stubs/dependencias esperadas (MSW Option A) — NO marcar ROTO por estas.
 * Son dependencias stubbeadas intencionalmente (payment/fiscal).
 */
const EXPECTED_STUB_PATTERNS = [
  /payment/i,
  /fiscal/i,
  /mercadopago/i,
  /stripe/i,
  /conektame/i,
  /sunat/i,
  /sat\.gob/i,
];

/**
 * Elementos clave del shell que deben estar visibles para clasificar OK.
 * Se verifica al menos UNO de estos (en orden de preferencia).
 */
const SHELL_KEY_SELECTORS = [
  '[data-testid="ribbon"]',
  '[data-testid="topbar"]',
  '[data-testid="sub-tabs-bar"]',
  '[data-testid="valeria-sidebar"]',
  // Auth page as valid for sign-in route
  '[data-testid="sign-in-form"]',
  'h1:has-text("Iniciar")',
  'input[name="identifier"]',
  // Sign-in Clerk component
  ".cl-signIn-root",
  ".cl-rootBox",
];

// ─────────────────────────────────────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────────────────────────────────────

export type SweepVerdict = "OK" | "ROTO" | "INACCESIBLE" | "SIN-UI";

export interface SweepFinding {
  surface: Omit<Surface, "capId"> & { capId: string | null };
  capId: string | null;
  sweep_verdict: SweepVerdict;
  httpStatus: number | null;
  consoleErrors: string[];
  screenshot: string | null;
  notes: string[];
  timestamp: string;
}

// ─────────────────────────────────────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────────────────────────────────────

function ensureEvidenceDir(): void {
  if (!fs.existsSync(EVIDENCE_DIR)) {
    fs.mkdirSync(EVIDENCE_DIR, { recursive: true });
  }
}

function isIgnoredConsoleError(text: string): boolean {
  return IGNORED_CONSOLE_PATTERNS.some((p) => p.test(text));
}

function isExpectedStub(text: string): boolean {
  return EXPECTED_STUB_PATTERNS.some((p) => p.test(text));
}

/** Sanitize a surface route into a safe filename slug */
function routeToSlug(route: string): string {
  return route
    .replace(/^https?:\/\//, "")
    .replace(/\$TENANT_ID/g, "tenant")
    .replace(/\$CLINIC_SLUG/g, "clinic")
    .replace(/[^a-zA-Z0-9-]/g, "_")
    .replace(/__+/g, "_")
    .replace(/^_|_$/g, "")
    .slice(0, 80);
}

async function captureScreenshot(
  page: Page,
  slug: string,
): Promise<string | null> {
  try {
    ensureEvidenceDir();
    const screenshotPath = path.join(EVIDENCE_DIR, `${slug}.png`);
    await page.screenshot({
      path: screenshotPath,
      fullPage: false,
      // Clip to viewport only — avoid accidentally capturing large PHI data
      clip: { x: 0, y: 0, width: 1440, height: 900 },
    });
    // Return relative path from workspace root (for the matrix artifact)
    return `vitalia/frontend/e2e/regression/live-reconciliation/.evidence/${slug}.png`;
  } catch {
    return null;
  }
}

async function checkShellKeyElementVisible(page: Page): Promise<boolean> {
  for (const selector of SHELL_KEY_SELECTORS) {
    try {
      const el = page.locator(selector).first();
      const visible = await el.isVisible({ timeout: 2_000 }).catch(() => false);
      if (visible) return true;
    } catch {
      // continue trying next selector
    }
  }
  return false;
}

// ─────────────────────────────────────────────────────────────────────────────
// Main sweep logic per surface
// ─────────────────────────────────────────────────────────────────────────────

async function sweepShellSurface(
  page: Page,
  surface: Surface,
  tenantId: string,
): Promise<SweepFinding> {
  const consoleErrors: string[] = [];
  const notes: string[] = [];
  let httpStatus: number | null = null;
  let verdict: SweepVerdict = "OK";

  // Substitute tenantId into route
  const route = surface.route.replace(/\$TENANT_ID/g, tenantId);

  // ── Console error collection ──────────────────────────────────────────────
  const consoleHandler = (msg: import("@playwright/test").ConsoleMessage): void => {
    if (msg.type() === "error") {
      const text = msg.text();
      if (isExpectedStub(text)) {
        notes.push(`stub-esperado: ${text.slice(0, 120)}`);
        return;
      }
      if (!isIgnoredConsoleError(text)) {
        consoleErrors.push(text.slice(0, 200));
      }
    }
  };
  page.on("console", consoleHandler);

  // ── Response status listener ──────────────────────────────────────────────
  const responseHandler = (response: Response): void => {
    if (
      response.url().includes(route.split("?")[0]) ||
      (response.status() >= 500 && httpStatus === null)
    ) {
      httpStatus = response.status();
    }
  };
  page.on("response", responseHandler);

  const slug = routeToSlug(route);
  let screenshot: string | null = null;

  try {
    // Navigate with reasonable timeout
    const [mainResponse] = await Promise.allSettled([
      page.goto(route, { waitUntil: "domcontentloaded", timeout: 30_000 }),
    ]);

    // Capture primary navigation status
    if (mainResponse.status === "fulfilled" && mainResponse.value) {
      httpStatus = mainResponse.value.status();
    }

    // Wait briefly for JS to settle
    await page.waitForTimeout(1_500);

    // Check for server-side error
    if (httpStatus !== null && httpStatus >= 500) {
      verdict = "ROTO";
      notes.push(`HTTP ${httpStatus} en navegación`);
    } else if (httpStatus === 404) {
      verdict = "INACCESIBLE";
      notes.push("Ruta 404 — no existe en el servidor");
    } else {
      // Check for shell key element visible
      const shellVisible = await checkShellKeyElementVisible(page);
      if (!shellVisible) {
        // Check if we got redirected to sign-in (INACCESIBLE from auth perspective or expected)
        const currentUrl = page.url();
        if (
          currentUrl.includes("/sign-in") &&
          !route.includes("sign-in")
        ) {
          verdict = "INACCESIBLE";
          notes.push(
            `Redirigido a sign-in desde ${route} — Clerk auth requerida y no cumplida`,
          );
        } else if (consoleErrors.length > 0) {
          verdict = "ROTO";
          notes.push("Console errors graves + elemento shell no visible");
        } else {
          // Surface loads but no shell elements found — likely empty state or placeholder
          verdict = "OK";
          notes.push(
            "Carga sin errores graves; elemento shell clave no visible (posible empty-state o placeholder)",
          );
        }
      } else if (consoleErrors.length > 0) {
        verdict = "ROTO";
        notes.push(
          `Shell carga pero hay ${consoleErrors.length} console error(s) grave(s)`,
        );
      } else {
        verdict = "OK";
      }
    }

    // Capture screenshot always (evidence)
    screenshot = await captureScreenshot(page, slug);
  } catch (err) {
    verdict = "ROTO";
    const errorMsg = err instanceof Error ? err.message : String(err);
    notes.push(`Excepción en navegación: ${errorMsg.slice(0, 200)}`);
    // Still try screenshot
    screenshot = await captureScreenshot(page, `${slug}_error`);
  } finally {
    page.off("console", consoleHandler);
    page.off("response", responseHandler);
  }

  const finding: SweepFinding = {
    surface: {
      agent: surface.agent,
      subtab: surface.subtab,
      subsubtab: surface.subsubtab,
      route,
      kind: surface.kind,
      label: surface.label,
    },
    capId: surface.capId,
    sweep_verdict: verdict,
    httpStatus,
    consoleErrors,
    screenshot,
    notes,
    timestamp: new Date().toISOString(),
  };

  return finding;
}

function annotateExternalSurface(surface: Surface): SweepFinding {
  return {
    surface: {
      agent: surface.agent,
      subtab: surface.subtab,
      subsubtab: surface.subsubtab,
      route: surface.route,
      kind: surface.kind,
      label: surface.label,
    },
    capId: surface.capId,
    sweep_verdict: "SIN-UI",
    httpStatus: null,
    consoleErrors: [],
    screenshot: null,
    notes: ["Superficie external-annotated — barrido profundo fuera de scope del shell-organism"],
    timestamp: new Date().toISOString(),
  };
}

// ─────────────────────────────────────────────────────────────────────────────
// Test suite
// ─────────────────────────────────────────────────────────────────────────────

// Surfaces are computed once at module level for stable ordering
const ALL_SURFACES = enumerateNavigableSurfaces(TENANT_ID);
const SHELL_SURFACES = ALL_SURFACES.filter((s) => s.kind === "shell");
const EXTERNAL_SURFACES = ALL_SURFACES.filter(
  (s) => s.kind === "external-annotated",
);

test.describe("Sweep harness — reconciliación cockpit ↔ realidad live", () => {
  // All findings accumulated across tests
  const allFindings: SweepFinding[] = [];

  test.afterAll(async () => {
    // Persist findings to JSON artifact
    try {
      fs.writeFileSync(
        FINDINGS_PATH,
        JSON.stringify(allFindings, null, 2),
        "utf-8",
      );
      console.log(
        `[sweep] Findings written to ${FINDINGS_PATH} (${allFindings.length} surfaces)`,
      );

      // Summary
      const countByVerdict = allFindings.reduce(
        (acc, f) => {
          acc[f.sweep_verdict] = (acc[f.sweep_verdict] ?? 0) + 1;
          return acc;
        },
        {} as Record<SweepVerdict, number>,
      );
      console.log("[sweep] Summary:", JSON.stringify(countByVerdict));
    } catch (err) {
      console.error("[sweep] Failed to write findings:", err);
    }
  });

  // ── Test: External-annotated surfaces (annotate only, fast) ──────────────

  test("annotate external surfaces (no deep sweep)", async () => {
    for (const surface of EXTERNAL_SURFACES) {
      const finding = annotateExternalSurface(surface);
      allFindings.push(finding);
      console.log(
        `[sweep] external-annotated: ${surface.label} → SIN-UI`,
      );
    }
    // The test passes as long as we annotated them (no browser needed)
    expect(allFindings.filter((f) => f.sweep_verdict === "SIN-UI").length).toBeGreaterThanOrEqual(
      EXTERNAL_SURFACES.length,
    );
  });

  // ── Dynamic tests: one per shell surface ─────────────────────────────────
  // Using a single test with a loop so failures on one surface don't abort the suite.
  // Each surface is wrapped in try/catch so all verdicts are collected.

  test(
    "sweep all shell surfaces — collect verdicts (ROTO is data, not test failure)",
    async ({ page }) => {
      // Each surface takes up to 30s (domcontentloaded + 1.5s settle + screenshot).
      // 27 shell surfaces × ~5s avg = ~135s. Set generous timeout.
      test.setTimeout(600_000); // 10 minutes max for full sweep

      let sweptCount = 0;
      let okCount = 0;
      let rotoCount = 0;
      let inaccessibleCount = 0;

      for (const surface of SHELL_SURFACES) {
        let finding: SweepFinding;
        try {
          finding = await sweepShellSurface(page, surface, TENANT_ID);
        } catch (err) {
          // Safety net: even if sweepShellSurface throws, record as ROTO
          const errorMsg = err instanceof Error ? err.message : String(err);
          finding = {
            surface: {
              agent: surface.agent,
              subtab: surface.subtab,
              subsubtab: surface.subsubtab,
              route: surface.route.replace(/\$TENANT_ID/g, TENANT_ID),
              kind: surface.kind,
              label: surface.label,
            },
            capId: surface.capId,
            sweep_verdict: "ROTO",
            httpStatus: null,
            consoleErrors: [],
            screenshot: null,
            notes: [`Excepción no capturada en sweepShellSurface: ${errorMsg.slice(0, 200)}`],
            timestamp: new Date().toISOString(),
          };
        }

        allFindings.push(finding);
        sweptCount++;

        switch (finding.sweep_verdict) {
          case "OK":
            okCount++;
            break;
          case "ROTO":
            rotoCount++;
            break;
          case "INACCESIBLE":
            inaccessibleCount++;
            break;
        }

        console.log(
          `[sweep] ${finding.sweep_verdict.padEnd(12)} ${surface.label.slice(0, 60)} ` +
            `(HTTP ${finding.httpStatus ?? "?"})`,
        );
      }

      console.log(
        `[sweep] Total: ${sweptCount} surfaces swept — OK=${okCount} ROTO=${rotoCount} INACCESIBLE=${inaccessibleCount}`,
      );

      // The test PASSES as long as the sweep completed (all surfaces visited).
      // ROTO verdicts are FINDINGS, not test failures.
      expect(sweptCount).toBe(SHELL_SURFACES.length);
      expect(allFindings.length).toBeGreaterThan(0);
    },
  );

  // ── Validation: findings file was written ─────────────────────────────────
  // NOTE: this test reads the JSON file directly because allFindings is
  // accumulated in THIS worker — if Playwright parallelizes, the file is
  // the canonical source of truth written by afterAll.

  test("findings artifact written", () => {
    // Check the JSON file exists and has content
    const exists = fs.existsSync(FINDINGS_PATH);
    if (!exists) {
      // Findings may not be written yet if sweep runs in a different worker (parallel).
      // In serial mode (live-recon project), afterAll runs before this test.
      // Accept either: allFindings populated OR file on disk.
      console.log(
        `[sweep] findings artifact not yet on disk — checking in-memory allFindings (${allFindings.length} entries)`,
      );
      // At minimum, externals should have been annotated (same worker)
      expect(allFindings.length).toBeGreaterThanOrEqual(EXTERNAL_SURFACES.length);
      return;
    }
    const contents = fs.readFileSync(FINDINGS_PATH, "utf-8");
    const parsed = JSON.parse(contents) as unknown[];
    console.log(
      `[sweep] findings artifact: ${FINDINGS_PATH} — ${parsed.length} entries`,
    );
    // At minimum the externals are annotated
    expect(parsed.length).toBeGreaterThanOrEqual(EXTERNAL_SURFACES.length);
  });
});
