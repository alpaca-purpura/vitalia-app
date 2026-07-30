/**
 * sub-tabs-i18n.spec.ts — SC-9 i18n · Spanish neutro LatAm microcopy + tildes
 *
 * F1-S8 vitalia-fase1-sub-tabs-line2 — T-6
 *
 * Gherkin: 01-spec.md § Gherkin SC-9
 *
 * Verifica que todos los nav aria-labels y sub-tab labels son Spanish neutro LatAm
 * con tildes correctas (Adrián, Reputación, Configuración).
 *
 * gherkin_coverage:
 *   - SC-9: 6 nav aria-labels Spanish neutro + tildes
 *   - SC-9-labels: 22 sub-tab labels verbatim in DOM
 *
 * downstream-regression-na: brand-local E2E spec; no cross-brand consumers
 */

import { expect } from "@playwright/test";
import { test } from "../../fixtures/shell-theme.fixture";
import { SubTabsBarPage } from "./poms/sub-tabs-bar-page.pom";

const DESKTOP_VIEWPORT = { width: 1280, height: 800 };
const TENANT_ID = process.env["E2E_TENANT_ID"] ?? "vitalia-test-tenant";

// Expected aria-labels per agent (Spanish neutro + tildes correctas)
const ARIA_LABELS: Record<string, string> = {
  lisa: "Sub-secciones Lisa",
  lucas: "Sub-secciones Lucas",
  adrian: "Sub-secciones Adrián", // tilde en Adrián
  valeria: "Sub-secciones Valeria",
  camila: "Sub-secciones Camila",
  config: "Sub-secciones Configuración", // tilde en Configuración
};

// Expected sub-tab labels verbatim (22 total)
const EXPECTED_LABELS: Record<string, string[]> = {
  lisa: ["Marca", "Doctores", "Servicios", "Compliance"],
  lucas: ["Lanzar", "En vuelo", "Recursos", "Resultados", "Mercado"],
  adrian: ["Inbox", "Embudo", "Outbound", "Propuestas"],
  valeria: ["Agenda", "Pacientes"],
  camila: ["Voz del paciente", "Reactivar", "Multiplicar", "Reputación"], // tilde Reputación
  config: ["Mi cuenta", "Conexiones", "Avanzado"],
};

test.describe("SC-9 — nav aria-labels Spanish neutro LatAm + tildes correctas", () => {
  test.use({ viewport: DESKTOP_VIEWPORT });

  for (const [agent, expectedLabel] of Object.entries(ARIA_LABELS)) {
    const subtab =
      {
        lisa: "marca",
        lucas: "lanzar",
        adrian: "inbox",
        valeria: "agenda",
        camila: "voz",
        config: "cuenta",
      }[agent] ?? "default";

    test(`aria-label for ${agent} → "${expectedLabel}"`, async ({
      shellPage,
    }) => {
      const pom = new SubTabsBarPage(shellPage);

      await pom.goto({ tenantId: TENANT_ID, agent, subtab });

      const ariaLabel = await pom.getAriaLabel();
      expect(ariaLabel).toBe(expectedLabel);
    });
  }
});

test.describe("SC-9 — sub-tab labels verbatim Spanish neutro LatAm", () => {
  test.use({ viewport: DESKTOP_VIEWPORT });

  for (const [agent, expectedLabels] of Object.entries(EXPECTED_LABELS)) {
    const subtab =
      {
        lisa: "marca",
        lucas: "lanzar",
        adrian: "inbox",
        valeria: "agenda",
        camila: "voz",
        config: "cuenta",
      }[agent] ?? "default";

    test(`${agent} labels verbatim: ${JSON.stringify(expectedLabels)}`, async ({
      shellPage,
    }) => {
      const pom = new SubTabsBarPage(shellPage);

      await pom.goto({ tenantId: TENANT_ID, agent, subtab });

      expect(await pom.isPresent()).toBe(true);

      // Get all sub-tab text content in order
      const allTabs = pom.getAllSubTabs();
      const count = await allTabs.count();
      expect(count).toBe(expectedLabels.length);

      for (let i = 0; i < count; i++) {
        const tab = allTabs.nth(i);
        // Each sub-tab has an emoji span (aria-hidden) + a label span
        // textContent returns both; we get the label span specifically
        const labelSpan = tab.locator("span:not([aria-hidden])");
        const labelText = await labelSpan.textContent();
        expect(labelText?.trim()).toBe(expectedLabels[i]);
      }
    });
  }
});

test.describe("SC-9 — tildes correctas en UI (Adrián, Reputación, Configuración)", () => {
  test.use({ viewport: DESKTOP_VIEWPORT });

  test("Adrián aria-label contiene tilde (Adrián no Adrián with missing accent)", async ({
    shellPage,
  }) => {
    const pom = new SubTabsBarPage(shellPage);
    await pom.goto({ tenantId: TENANT_ID, agent: "adrian", subtab: "inbox" });
    const ariaLabel = await pom.getAriaLabel();
    // Must have ó (U+00F3), not plain 'o'
    expect(ariaLabel).toContain("Adrián");
    expect(ariaLabel).not.toContain("Adrian\n"); // no bare Adrian without accent
  });

  test("Reputación label contiene tilde (Reputación no Reputacion)", async ({
    shellPage,
  }) => {
    const pom = new SubTabsBarPage(shellPage);
    await pom.goto({ tenantId: TENANT_ID, agent: "camila", subtab: "voz" });
    const reputacionLabel = pom
      .getSubTabsBar()
      .locator('[data-testid="sub-tab-reputacion"]')
      .locator("span:not([aria-hidden])");
    const text = await reputacionLabel.textContent();
    expect(text?.trim()).toBe("Reputación");
    // Verify tilde ó (not plain 'o')
    expect(text).toContain("ó");
  });

  test("Configuración aria-label contiene tilde (Configuración no Configuracion)", async ({
    shellPage,
  }) => {
    const pom = new SubTabsBarPage(shellPage);
    await pom.goto({ tenantId: TENANT_ID, agent: "config", subtab: "cuenta" });
    const ariaLabel = await pom.getAriaLabel();
    expect(ariaLabel).toBe("Sub-secciones Configuración");
    expect(ariaLabel).toContain("ó");
  });
});
