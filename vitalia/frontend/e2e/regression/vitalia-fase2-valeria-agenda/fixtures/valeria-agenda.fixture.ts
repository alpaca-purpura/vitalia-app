/**
 * valeria-agenda.fixture.ts — F2-S1 vitalia-fase2-valeria-agenda
 *
 * Fixture: tenant PE setup + Clerk auth (valeria_assistant role) + DB seed
 * appointments (N=20, clinic_id) + MSW worker setup.
 *
 * Usage in specs:
 *   import { test, expect } from '../fixtures/valeria-agenda.fixture';
 *
 * Tenant: clinica-sonrisa-pe (locale es-PE, currency PEN)
 * Role: valeria_assistant
 * Seed: 20 appointments with varied status + origin per clinic_id
 *
 * downstream-regression-na: brand-local vitalia e2e fixture F2-S1; no cross-brand consumers
 *
 * @see 04-validators.yaml § test_construction_plan step 1
 */

import path from "path";
import { test as base, expect } from "@playwright/test";
import type { Page, BrowserContext } from "@playwright/test";
import { setupClerkTestingToken } from "@clerk/testing/playwright";

// ---------------------------------------------------------------------------
// Tenant constants (PE — clinica-sonrisa-pe)
// ---------------------------------------------------------------------------

export const VALERIA_AGENDA_FIXTURE = {
  tenantId: process.env["SONRISA_TENANT_ID"] ?? "clinica-sonrisa-pe-test",
  tenantSlug: "clinica-sonrisa-pe",
  clinicId: process.env["SONRISA_CLINIC_ID"] ?? "clinic-sonrisa-pe-001",
  locale: "es-PE" as const,
  currency: "PEN" as const,
  timezone: "America/Lima" as const,
  country: "PE" as const,
  /** PHI-masked patient names (server-masked per HIPAA-lite) */
  patients: [
    { id: "pat-001", maskedName: "P. Hernández", service: "Limpieza dental" },
    { id: "pat-002", maskedName: "R. Gómez", service: "Consulta general" },
    { id: "pat-003", maskedName: "M. Torres", service: "Ortodoncia" },
  ],
  /** Appointment with pending balance for cobro tests */
  sampleSlot: {
    appointmentId: "apt-sonrisa-pe-001",
    patientMaskedName: "P. Hernández",
    service: "Limpieza dental",
    balancePen: 80,
    status: "deposit" as const,
    origin: "manual" as const,
  },
  /** Alternate tenant for tenant-switch SC-3 */
  tenantB: {
    tenantId: process.env["AURORA_TENANT_ID"] ?? "aurora-spa-mx-test",
    tenantSlug: "aurora-spa-mx",
    currency: "MXN" as const,
    locale: "es-MX" as const,
    timezone: "America/Mexico_City" as const,
  },
} as const;

// ---------------------------------------------------------------------------
// Storage state (Clerk testing token)
// ---------------------------------------------------------------------------

const STORAGE_STATE_PATH = path.join(
  __dirname,
  "../../../../playwright/.clerk/user.json",
);

// ---------------------------------------------------------------------------
// Mock appointment seed (20 slots, varied status + origin)
// MSW intercepts /api/v1/scheduling/agenda/grid — server returns this seed
// when docker stack is not running (Option A per 03-arch § 8.6)
// ---------------------------------------------------------------------------

type AppointmentStatus = "paid" | "deposit" | "unpaid" | "noshow";
type AppointmentOrigin = "manual" | "phone" | "agent";

interface SeedAppointment {
  id: string;
  tenantId: string;
  clinicId: string;
  patientMaskedName: string;
  service: string;
  date: string;
  startTime: string;
  durationMin: number;
  paymentStatus: AppointmentStatus;
  origin: AppointmentOrigin;
  balancePen: number;
  currencyOverride: string | null;
}

export function buildSeedAppointments(
  tenantId: string,
  clinicId: string,
  baseDate: string = "2026-06-09",
): SeedAppointment[] {
  const statuses: AppointmentStatus[] = [
    "paid",
    "deposit",
    "unpaid",
    "noshow",
  ];
  const origins: AppointmentOrigin[] = ["manual", "phone", "agent"];
  const services = [
    "Limpieza dental",
    "Consulta general",
    "Ortodoncia",
    "Implante",
    "Blanqueamiento",
  ];
  const patientNames = [
    "P. Hernández",
    "R. Gómez",
    "M. Torres",
    "A. López",
    "C. Ramírez",
  ];

  return Array.from({ length: 20 }, (_, i) => ({
    id: `apt-seed-${String(i + 1).padStart(3, "0")}`,
    tenantId,
    clinicId,
    patientMaskedName: patientNames[i % patientNames.length],
    service: services[i % services.length],
    date: baseDate,
    startTime: `${8 + Math.floor(i / 2)}:${i % 2 === 0 ? "00" : "30"}`,
    durationMin: 30,
    paymentStatus: statuses[i % statuses.length],
    origin: origins[i % origins.length],
    balancePen: [0, 80, 120, 0][i % 4],
    currencyOverride: i === 5 ? "USD" : null, // one turista appointment
  }));
}

// ---------------------------------------------------------------------------
// Fixture types
// ---------------------------------------------------------------------------

export type VaAgendaFixtures = {
  /** Authenticated page for valeria_assistant role (PE tenant) */
  agendaPage: Page;
  /** Authenticated BrowserContext (for multi-context SC-6 concurrent users) */
  agendaContext: BrowserContext;
  /** Fixture constants */
  fixture: typeof VALERIA_AGENDA_FIXTURE;
  /** Seed appointments (20 slots) */
  seedAppointments: SeedAppointment[];
};

// ---------------------------------------------------------------------------
// Base fixture — extend Playwright test with Clerk auth
// ---------------------------------------------------------------------------

export const test = base.extend<VaAgendaFixtures>({
  // eslint-disable-next-line no-empty-pattern
  fixture: async ({}, use) => {
    await use(VALERIA_AGENDA_FIXTURE);
  },

  // eslint-disable-next-line no-empty-pattern
  seedAppointments: async ({}, use) => {
    const appointments = buildSeedAppointments(
      VALERIA_AGENDA_FIXTURE.tenantId,
      VALERIA_AGENDA_FIXTURE.clinicId,
    );
    await use(appointments);
  },

  agendaContext: async ({ browser }, use) => {
    const context = await browser.newContext({
      storageState: STORAGE_STATE_PATH,
    });
    await use(context);
    await context.close();
  },

  agendaPage: async ({ agendaContext }, use) => {
    const page = await agendaContext.newPage();

    // Clerk testing token injection (per playwright-expert SSoT)
    await setupClerkTestingToken({ page });

    await use(page);
    await page.close();
  },
});

export { expect };

// ---------------------------------------------------------------------------
// Helper: navigate to agenda route
// ---------------------------------------------------------------------------

export async function gotoAgenda(
  page: Page,
  tenantId: string = VALERIA_AGENDA_FIXTURE.tenantId,
  params: {
    view?: string;
    date?: string;
    /** Extra query params (e.g. e2eRefetchMs for accelerated polling in CI) */
    extraParams?: Record<string, string>;
  } = {},
): Promise<void> {
  const searchParams = new URLSearchParams();
  if (params.view) searchParams.set("view", params.view);
  if (params.date) searchParams.set("date", params.date);
  if (params.extraParams) {
    for (const [key, value] of Object.entries(params.extraParams)) {
      searchParams.set(key, value);
    }
  }
  const qs = searchParams.toString() ? `?${searchParams.toString()}` : "";
  // UPDATED: paradigm-map-zones T-6 (2026-05-30) — route migrated to mateo/agenda.
  // Was: /${tenantId}/valeria/agenda${qs} (pre paradigm-map-zones T-5)
  await page.goto(`/${tenantId}/mateo/agenda${qs}`);
  await page.waitForLoadState("domcontentloaded");
}
