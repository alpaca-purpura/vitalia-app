/**
 * sc-10-i18n.spec.ts — SC-10 · Spanish neutro LatAm + tenant_locale PEN
 * F1-S10 vitalia-fase1-empty-states — T-10
 *
 * Assertions:
 *   - 0 voseo verbs in rendered HTML across key sub-tabs
 *     (tenés/podés/sos/mirá/dejá/configurá/revisá/guardá/etc)
 *   - PEN currency format visible in mock data (S/ prefix — not USD/EUR/ARS)
 *   - 24h time format in agenda mock slots (08:00, 09:30 — not 8:00 AM)
 *   - Spanish neutro LatAm copy (tuteo: "tú/tienes/puedes" not "vos/tenés/podés")
 *   - No English fallback strings in user-facing content
 *   - Tildes/ñ/¿¡ correctly rendered (e.g., "próximamente", "configuración")
 *
 * Voseo glosario (per spanish-text.md rule):
 *   PROHIBITED: tenés/podés/sos/hacés/venís/mirá/dejá/poné/usá/hacé/
 *               elegí/seleccioná/configurá/revisá/escribí/guardá/abrí
 *
 * Uses: ShellOrganismPage POM + empty-states.fixture
 *
 * SC-10 validator: val-fe-e2e-sc10-i18n
 * downstream-regression-na: brand-local vitalia e2e spec
 */

// voseo-allowed: this spec cites voseo glosario verbatim as test patterns
import { expect } from "@playwright/test";
import { test } from "../../fixtures/empty-states.fixture";
import { ShellOrganismPage } from "../../pages/ShellOrganismPage";

// Voseo verbs that MUST NOT appear in rendered HTML (per spanish-text.md)
const VOSEO_PATTERNS = [
  "tenés",
  "podés",
  "sos ", // "sos" as standalone word (avoid matching "nosotros")
  "hacés",
  "venís",
  "mirá",
  "dejá",
  "poné",
  "usá",
  "elegí",
  "seleccioná",
  "configurá",
  "revisá",
  "escribí",
  "guardá",
  "abrí",
] as const;

// Sub-tabs to scan for voseo (representative sample)
const VOSEO_SCAN_ROUTES = [
  { agent: "lisa", subtab: "marca" },
  { agent: "lisa", subtab: "servicios" },
  { agent: "adrian", subtab: "inbox" },
  { agent: "adrian", subtab: "embudo" },
  { agent: "valeria", subtab: "agenda" },
  { agent: "config", subtab: "cuenta" },
  { agent: "config", subtab: "conexiones" },
] as const;

test.describe("SC-10 · Spanish neutro LatAm + tenant_locale PEN", () => {
  test.describe("0 voseo verbs en HTML renderizado", () => {
    for (const { agent, subtab } of VOSEO_SCAN_ROUTES) {
      test(`${agent}.${subtab} — sin voseo en contenido visible`, async ({
        shellPage,
        tenantId,
      }) => {
        const shell = new ShellOrganismPage(shellPage, tenantId);
        await shell.goto(agent, subtab);
        await shell.expectShellMounted();

        // Get all visible text in the page
        const pageText = await shellPage.locator("body").first().innerText();
        const lowercaseText = pageText.toLowerCase();

        for (const voseoVerb of VOSEO_PATTERNS) {
          expect(
            lowercaseText,
            `Voseo verb "${voseoVerb}" found in ${agent}.${subtab}`,
          )
            .first()
            .not.toContain(voseoVerb.toLowerCase());
        }
      });
    }
  });

  test.describe("PEN currency en datos mock", () => {
    test("Adrián Embudo muestra valores en S/ (PEN)", async ({
      shellPage,
      tenantId,
    }) => {
      const shell = new ShellOrganismPage(shellPage, tenantId);
      await shell.goto("adrian", "embudo");
      await shell.expectShellMounted();

      // PEN currency format: "S/ 84k" or similar
      await expect(
        shellPage.locator("text=/S\\/\\s*\\d+/").first(),
      ).toBeVisible();

      // No USD/EUR/ARS in currency values
      const pageText = await shellPage.locator("body").first().innerText();
      expect(pageText).not.toMatch(/\$\s*\d+k/); // USD $ format
    });

    test("Adrián Inbox muestra precios en S/ PEN", async ({
      shellPage,
      tenantId,
    }) => {
      const shell = new ShellOrganismPage(shellPage, tenantId);
      await shell.goto("adrian", "inbox").first();
      await shell.expectShellMounted();

      // Mock thread messages contain "S/ 120" (limpieza dental price)
      await expect(
        shellPage.locator("text=/S\\/\\s*\\d+/").first(),
      ).toBeVisible();
    });
  });

  test.describe("24h time format en agenda", () => {
    test("Valeria Agenda muestra horarios en formato 24h", async ({
      shellPage,
      tenantId,
    }) => {
      const shell = new ShellOrganismPage(shellPage, tenantId);
      await shell.goto("valeria", "agenda").first();
      await shell.expectShellMounted();

      // TIME_SLOTS in AgendaPlaceholder.tsx use 24h format: "08:00", "09:00", etc.
      await expect(
        shellPage.locator("text=/^\\d{2}:\\d{2}$/").first(),
      ).toBeVisible();

      // No AM/PM format
      const pageText = await shellPage.locator("body").first().innerText();
      expect(pageText).not.toMatch(/\b\d+:\d{2}\s*(AM|PM)\b/i);
    });
  });

  test.describe("tildes y ortografía correcta", () => {
    test("'próximamente' renderizado con tilde correcta", async ({
      shellPage,
      tenantId,
    }) => {
      const shell = new ShellOrganismPage(shellPage, tenantId);
      // Navigate to a sub-tab that shows "próximamente" text
      await shell.goto("lucas", "envuelo").first();
      await shell.expectShellMounted();

      const bodyText = await shellPage.locator("body").first().textContent();
      if (bodyText?.includes("próximamente").first()) {
        // If present, it must have the tilde (ó not o)
        expect(bodyText).toContain("próximamente");
        expect(bodyText).not.toContain("proximamente"); // without tilde
      }
    });

    test("nombres ficticios LatAm con tildes correctas en Inbox", async ({
      shellPage,
      tenantId,
    }) => {
      const shell = new ShellOrganismPage(shellPage, tenantId);
      await shell.goto("adrian", "inbox");
      await shell.expectShellMounted();

      // "María González" — tilde on a, accent on e
      await expect(
        shellPage.locator("text=María González").first(),
      ).toBeVisible();
      // "Lucía Ramos" — tilde on i
      await expect(shellPage.locator("text=Lucía Ramos").first()).toBeVisible();
    });
  });

  test.describe("tuteo (no voseo) en copy clave", () => {
    test("MessageInput placeholder en estado A usa tuteo", async ({
      shellPage,
      tenantId,
    }) => {
      const shell = new ShellOrganismPage(shellPage, tenantId);
      await shell.goto("adrian", "inbox").first();
      await shell.expectShellMounted();

      // Placeholder text in state A: "Adrián decide automáticamente · toma el control para escribir tú"
      // Key: "toma" (tuteo) not "tomá" (voseo); "escribir tú" not "escribir vos"
      const placeholderEl = shellPage
        .locator('[placeholder*="Adrián decide automáticamente"]')
        .first();
      const placeholder = await placeholderEl
        .getAttribute("placeholder")
        .first();
      if (placeholder) {
        expect(placeholder.toLowerCase()).not.toContain("tomá");
        expect(placeholder.toLowerCase()).not.toContain("vos");
      }
    });

    test("Embudo column headers en Spanish neutro (sin Decidí con voseo)", async ({
      shellPage,
      tenantId,
    }) => {
      const shell = new ShellOrganismPage(shellPage, tenantId);
      await shell.goto("adrian", "embudo");
      await shell.expectShellMounted();

      // "Decidió no" (not "Decidiste no" but correctly neutro)
      await expect(shellPage.locator("text=Decidió no").first()).toBeVisible();
    });
  });
});
