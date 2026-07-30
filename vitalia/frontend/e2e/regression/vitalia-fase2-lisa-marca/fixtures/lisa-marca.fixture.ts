/**
 * lisa-marca.fixture.ts — F2-S7 vitalia-fase2-lisa-marca (HONEST · backend real)
 *
 * Fixture: Clerk authedAsOwner + tenant PE + **backend REAL** (NO mock del
 * backend-bajo-prueba). El `setupLisaMarcaMocks` que mockeaba
 * identity/visuals/personality/contact/trust-signals/voice-preview con
 * `route.fulfill` fue ELIMINADO — era la causa del verde falso (RN-1). Ahora
 * el transporte se compone desde `real-backend-forward.fixture` (auth +
 * forwarding a :8002 + gate anti-burbuja base.ts).
 *
 * Usage in specs:
 *   import { test, expect, LISA_MARCA_FIXTURE, gotoMarca } from './fixtures/lisa-marca.fixture';
 *
 * Tenant: clinica-salud-vitalia-pe (locale es-PE, currency PEN, country PE).
 * Role: brand_owner (admin_clinic). Seed real en DB (no canned) — los specs
 * usan round-trips reales y aserciones web-first tolerantes al estado de DB.
 *
 * downstream-regression-na: brand-local vitalia e2e fixture F2-S7; no cross-brand consumers
 *
 * @see 04-validators.yaml § test_construction_plan step 1, step 3
 * @see e2e/fixtures/real-backend-forward.fixture.ts (transporte honesto compartido)
 */

import type { Page } from "@playwright/test";
import {
  test as realBackendTest,
  expect,
  TENANT_ID,
  BACKEND_API_URL,
} from "../../../fixtures/real-backend-forward.fixture";

// ---------------------------------------------------------------------------
// Tenant constants (PE — clinica-salud-vitalia-pe)
//
// Estos valores son el SEED esperado del tenant de prueba (lo que la marca
// debería tener configurado). Se usan como valores esperados en aserciones de
// round-trip. NO se devuelven como mock — el browser real lee de la DB real.
// ---------------------------------------------------------------------------

export const LISA_MARCA_FIXTURE = {
  tenantId:
    process.env["E2E_TENANT_ID"] ??
    process.env["VITALIA_PE_TENANT_ID"] ??
    TENANT_ID,
  tenantSlug: "clinica-salud-vitalia-pe",
  clinicId:
    process.env["VITALIA_PE_CLINIC_ID"] ?? "clinic-salud-vitalia-pe-001",
  locale: "es-PE" as const,
  currency: "PEN" as const,
  timezone: "America/Lima" as const,
  country: "PE" as const,
  /** Seed brand identity */
  identity: {
    brandName: "Salud Vitalia",
    tagline: "Tu bienestar, nuestra misión",
    description: "Clínica médica integral con enfoque preventivo y humanizado.",
    clinicVertical: "medicina_general",
    primarySpecialties: ["medicina_general", "nutricion"],
  },
  /** Seed visuals */
  visuals: {
    logoUrl: null as string | null,
    primaryColor: "#2E7D32",
    secondaryColor: "#66BB6A",
    fontFamily: "Inter",
  },
  /** Seed personality (Caregiver archetype — salud default) */
  personality: {
    archetype: "caregiver" as const,
    toneBlocks: {
      openingHook:
        "En Salud Vitalia, cuidamos de ti con dedicación y expertise médico.",
      mainBody: "Nuestro equipo de profesionales trabaja con empatía.",
      closingCta: "Agenda tu consulta hoy y da el primer paso hacia tu salud.",
    },
    languageStyle: "formal_warm",
    prohibitedPhrases: [] as string[],
  },
  /** Seed contact */
  contact: {
    website: "https://saludvitalia.pe",
    instagram: "@saludvitalia",
    tiktok: null as string | null,
    googleBusiness: null as string | null,
    address: "Av. Javier Prado Este 2300, San Isidro, Lima",
    phone: "+51 1 234-5678",
  },
  /** Trust signals seed (PE hybrid catalog) */
  trustSignals: [
    {
      id: "ts-001",
      type: "certification",
      value: "Acreditación SUSALUD",
      displayOrder: 1,
    },
    {
      id: "ts-002",
      type: "award",
      value: "Premio Salud Digital 2025",
      displayOrder: 2,
    },
  ],
  /** Voice blocklist seed (PE defaults) */
  voiceBlocklist: [
    { id: "vb-001", phrase: "barato", severity: "warning" },
    { id: "vb-002", phrase: "descuento", severity: "warning" },
  ],
  /** Trust catalog (PE seed 8 entries) */
  trustCatalog: [
    { id: "tc-pe-001", label: "Acreditación SUSALUD", category: "regulatory" },
    { id: "tc-pe-002", label: "ISO 9001:2015", category: "certification" },
    { id: "tc-pe-003", label: "Premio Salud Digital", category: "award" },
    {
      id: "tc-pe-004",
      label: "Miembro SOMECO",
      category: "professional_association",
    },
    {
      id: "tc-pe-005",
      label: "Clínica Verificada MINSA",
      category: "regulatory",
    },
    { id: "tc-pe-006", label: "5 estrellas Google", category: "rating" },
    {
      id: "tc-pe-007",
      label: "NPS 85+ (últimos 6 meses)",
      category: "patient_satisfaction",
    },
    { id: "tc-pe-008", label: "Otra", category: "custom" },
  ],
  /** Alternate tenant for cross-tenant adversarial test */
  tenantB: {
    tenantId: process.env["VITALIA_MX_TENANT_ID"] ?? "clinica-salud-mx-test",
    tenantSlug: "clinica-salud-mx",
    clinicId:
      process.env["VITALIA_MX_CLINIC_ID"] ?? "clinic-salud-mx-001-intruder",
    country: "MX" as const,
  },
} as const;

export { BACKEND_API_URL, TENANT_ID };

// ---------------------------------------------------------------------------
// Fixture — HONEST: compose auth + real-backend forwarding + anti-burbuja.
//
// `marcaPage` / `marcaContext` are kept as aliases of the forwarded,
// authenticated `page` / its context so existing specs keep their public
// surface while hitting the REAL backend (no canned mock).
// ---------------------------------------------------------------------------

export type LisaMarcaFixtures = {
  /** Authenticated page (real backend forwarding + anti-burbuja gate) */
  marcaPage: Page;
  /** Authenticated BrowserContext (for multi-context concurrent-owners spec) */
  marcaContext: import("@playwright/test").BrowserContext;
  /** Fixture constants */
  fixture: typeof LISA_MARCA_FIXTURE;
};

export const test = realBackendTest.extend<LisaMarcaFixtures>({
  // eslint-disable-next-line no-empty-pattern -- Playwright fixture API requires the empty destructure
  fixture: async ({}, use) => {
    await use(LISA_MARCA_FIXTURE);
  },

  // The forwarded, authenticated page IS the marca page (real backend).
  marcaPage: async ({ page }, use) => {
    await use(page);
  },

  // Context of the forwarded page — used by specs that open a second page
  // in the SAME Clerk session (race-autosave). The second page does NOT get
  // the auto-forwarding fixture wiring, so specs call forwardApiToRealBackend
  // on it explicitly (see helper export below).
  marcaContext: async ({ page }, use) => {
    await use(page.context());
  },
});

export { expect };

// Re-export the forwarding helper so specs that spin up extra pages in the
// same context (race-autosave, concurrent-owners) can wire them to the real BE.
export { forwardApiToRealBackend } from "../../../fixtures/real-backend-forward.fixture";

// ---------------------------------------------------------------------------
// Helper: navigate to lisa/marca route (N3-static sub-sub-tab)
// ---------------------------------------------------------------------------

export type LisaMarcaSubsubtab = "identidad" | "voz-y-tono" | "presencia";

export async function gotoMarca(
  page: Page,
  tenantId: string = LISA_MARCA_FIXTURE.tenantId,
  subsubtab: LisaMarcaSubsubtab = "identidad",
): Promise<void> {
  await page.goto(`/${tenantId}/lisa/marca/${subsubtab}`);
  await page.waitForLoadState("domcontentloaded");
}
