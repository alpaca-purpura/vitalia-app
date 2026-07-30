// # voseo-allowed: this file contains voseo strings ONLY as regex patterns to DETECT violations in the UI
/**
 * ribbon-i18n.spec.ts — SC-8 i18n · Spanish neutro LatAm + tildes correctas
 *
 * F1-S7 vitalia-fase1-ribbon-6-tabs — T-5
 *
 * Gherkin: 01-spec.md § Gherkin SC-8
 *
 * Given: Ribbon renderizado con 6 tabs (5 agentes + ConfigTab)
 * When:  se leen los textos visibles del ribbon
 * Then:  los 11 strings user-facing son exactamente los especificados
 * And:   NO hay strings con voseo (formas verbales AR: tenés/podés/mirá/etc.)
 * And:   tildes y eñes son correctas (Mi Clínica, Configurar, etc.)
 * And:   NO hay placeholders en inglés (TODO/undefined/null/placeholder)
 *
 * gherkin_coverage:
 *   - SC-8-1: 11 strings verbatim verificados en ribbon
 *   - SC-8-2: cero matches de regex voseo en texto visible ribbon
 *   - SC-8-3: tildes presentes en strings que las requieren
 *
 * Note: magic comment voseo-allowed at file top — regex patterns here are
 * DETECTORS of voseo violations, not voseo text themselves.
 *
 * downstream-regression-na: brand-local E2E spec; no cross-brand consumers
 */

import { expect } from "@playwright/test";
import { test } from "../../fixtures/shell-theme.fixture";
import { RibbonPage } from "./poms/ribbon-page.pom";

const DESKTOP_VIEWPORT = { width: 1280, height: 800 };
const TENANT_ID = process.env["E2E_TENANT_ID"] ?? "vitalia-test-tenant";

/**
 * Expected tab labels per 01-spec.md § 3 Agent catalog + Design Contract
 * SSoT: vitalia/frontend/src/lib/agent-catalog.ts :: tabLabel field
 * UPDATED: paradigm-map-zones T-6 (2026-05-30) — Valeria removed from ribbon (sidebar only v1.2).
 *   Mateo (Operar) added. ConfigTab label → "Plataforma" (was "Configurar").
 */
const EXPECTED_TAB_LABELS = {
  lisa: "Mi Clínica",
  mateo: "Atender", // v1.3 (2026-06-22): renamed from "Operar" (no surgical connotation)
  adrian: "Vender",
  lucas: "Atraer",
  camila: "Mantener",
  config: "Plataforma",
} as const;

/**
 * Voseo regex patterns — these are DETECTION patterns, not actual voseo usage.
 * The UI should NOT contain any of these forms.
 * See .claude/rules/spanish-text.md § R2 glosario
 */
const VOSEO_PATTERNS = [
  /\btenés\b/i,
  /\bpodés\b/i,
  /\bquerés\b/i,
  /\bsabés\b/i,
  /\bhacés\b/i,
  /\bvenís\b/i,
  /\bdecís\b/i,
  /\bmirá\b/i,
  /\bdejá\b/i,
  /\bponé\b/i,
  /\busá\b/i,
  /\bhacé\b/i,
  /\belegí\b/i,
  /\bagregá\b/i,
  /\bconfigurá\b/i,
  /\brevisá\b/i,
  /\bguardá\b/i,
  /\babrí\b/i,
  /\bvolvé\b/i,
  /\bcambiá\b/i,
  /\bsos\b/i,
  /\bvos\b/i,
];

/**
 * English placeholder patterns that should NOT appear in UI
 */
const ENGLISH_PLACEHOLDER_PATTERNS = [
  /\bTODO\b/,
  /\bundefined\b/,
  /\bnull\b/,
  /\bplaceholder\b/i,
  /\bfixme\b/i,
];

test.describe("SC-8 — i18n Spanish neutro LatAm + tildes correctas", () => {
  test.use({ viewport: DESKTOP_VIEWPORT });

  test("SC-8-1 (UPDATED v1.2): strings verbatim en ribbon tabs (5 especialistas + Plataforma)", async ({
    shellPage,
  }) => {
    // UPDATED: paradigm-map-zones T-6 (2026-05-30)
    // v1.2: Mateo replaces Valeria in ribbon. ConfigTab label → "Plataforma".
    const pom = new RibbonPage(shellPage);

    await pom.goto({ tenantId: TENANT_ID, agent: "lisa", subtab: "marca" });

    // Verify agent tab labels (text content)
    for (const [slug, expectedLabel] of Object.entries(EXPECTED_TAB_LABELS)) {
      if (slug === "config") {
        // ConfigTab uses aria-label (icon-only button — text lives in Tooltip + aria-label)
        const ariaLabel = await pom.getConfigTab().getAttribute("aria-label");
        expect(
          ariaLabel,
          `ConfigTab aria-label should be "${expectedLabel}"`,
        ).toBe(expectedLabel);
      } else {
        const tab = pom.getTab(
          slug as "lisa" | "mateo" | "adrian" | "lucas" | "camila",
        );
        const text = await tab.textContent();
        expect(
          text,
          `Tab "${slug}" should contain label "${expectedLabel}"`,
        ).toContain(expectedLabel);
      }
    }
  });

  test("SC-8-2: cero matches de voseo en texto visible del ribbon", async ({
    shellPage,
  }) => {
    const pom = new RibbonPage(shellPage);

    await pom.goto({ tenantId: TENANT_ID, agent: "lisa", subtab: "marca" });

    // Get full text content of ribbon
    const ribbon = pom.getRibbon();
    const ribbonText = (await ribbon.textContent()) ?? "";

    // Check each voseo pattern against ribbon text
    const violations: string[] = [];
    for (const pattern of VOSEO_PATTERNS) {
      const match = ribbonText.match(pattern);
      if (match) {
        violations.push(
          `Voseo pattern "${pattern.source}" matched: "${match[0]}" in ribbon text`,
        );
      }
    }

    expect(
      violations,
      `Ribbon should have zero voseo violations:\n${violations.join("\n")}`,
    ).toHaveLength(0);
  });

  test("SC-8-3 (UPDATED v1.2): tildes presentes en 'Mi Clínica' y 'Plataforma'", async ({
    shellPage,
  }) => {
    // UPDATED: paradigm-map-zones T-6 (2026-05-30)
    // ConfigTab label → "Plataforma" (was "Configurar"). Mateo replaces Valeria.
    const pom = new RibbonPage(shellPage);

    await pom.goto({ tenantId: TENANT_ID, agent: "lisa", subtab: "marca" });

    // "Mi Clínica" — tilde en la 'i' de Clínica
    const lisaText = (await pom.getTab("lisa").textContent()) ?? "";
    expect(lisaText).toContain("Clínica"); // Must have tilde (not "Clinica")

    // "Plataforma" — ConfigTab is icon-only; label lives in aria-label (not textContent)
    const configAriaLabel =
      (await pom.getConfigTab().getAttribute("aria-label")) ?? "";
    expect(configAriaLabel).toBe("Plataforma");

    // Verify none of the tab labels have been corrupted/truncated (v1.2 ribbon order)
    expect(lisaText).toContain("Mi Clínica");
    expect(await pom.getTab("mateo").textContent()).toContain("Atender");
    expect(await pom.getTab("lucas").textContent()).toContain("Atraer");
    expect(await pom.getTab("adrian").textContent()).toContain("Vender");
    expect(await pom.getTab("camila").textContent()).toContain("Mantener");
  });

  test("SC-8-4: NO hay placeholders en inglés en el ribbon", async ({
    shellPage,
  }) => {
    const pom = new RibbonPage(shellPage);

    // UPDATED: use mateo/agenda (Valeria no longer a ribbon tab — v1.2)
    await pom.goto({ tenantId: TENANT_ID, agent: "mateo", subtab: "agenda" });

    // Get full ribbon text
    const ribbon = pom.getRibbon();
    const ribbonText = (await ribbon.textContent()) ?? "";

    // Check for English placeholders
    const placeholderViolations: string[] = [];
    for (const pattern of ENGLISH_PLACEHOLDER_PATTERNS) {
      const match = ribbonText.match(pattern);
      if (match) {
        placeholderViolations.push(
          `English placeholder "${pattern.source}" found: "${match[0]}"`,
        );
      }
    }

    expect(
      placeholderViolations,
      `Ribbon should have no English placeholders:\n${placeholderViolations.join("\n")}`,
    ).toHaveLength(0);
  });
});
