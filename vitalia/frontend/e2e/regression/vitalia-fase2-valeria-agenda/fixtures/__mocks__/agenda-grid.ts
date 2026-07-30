/**
 * agenda-grid.ts — MSW mock helper for agenda grid API
 *
 * Intercepts GET /api/v1/scheduling/agenda/grid** and returns
 * predefined fixture data. Used by spec files that need a calendar
 * grid pre-populated without a running backend.
 *
 * Scenarios:
 *   "with_seed"   — 3 appointments including sampleSlot (status=deposit)
 *   "empty"       — zero appointments (empty-state SC-8)
 *   "large"       — 240 slots (virtualization SC-9)
 *   "tenant_b"    — different tenantId + clinic (tenant-switch SC-3)
 *
 * IMPORTANT: mocks are scoped per page (page.route). Call clearAgendaGridMock
 * to unregister after test to avoid cross-test contamination.
 *
 * downstream-regression-na: brand-local vitalia E2E mock helper F2-S1
 *
 * @see valeria-agenda-cobro.spec.ts — consumer
 * @see 04-validators.yaml § creation_order step 1
 */

import type { Page } from "@playwright/test";
import { VALERIA_AGENDA_FIXTURE } from "../valeria-agenda.fixture";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type AgendaGridScenario =
  | "with_seed"
  | "empty"
  | "large"
  | "tenant_b"
  | "network_error";

export interface AppointmentSlotData {
  appointmentId: string;
  tenantId: string;
  clinicId: string;
  patientMaskedName: string;
  service: string;
  startTime: string;
  endTime: string;
  paymentStatus: "pending" | "deposit" | "paid" | "cancelled";
  origin: "walk-in" | "telefono" | "referido";
  currency: string;
  totalAmount: number;
  depositAmount: number | null;
  balanceAmount: number;
  balanceVersion: number;
}

// ---------------------------------------------------------------------------
// Fixture builders
// ---------------------------------------------------------------------------

const { tenantId, clinicId, sampleSlot } = VALERIA_AGENDA_FIXTURE;

function buildSeedSlots(): AppointmentSlotData[] {
  return [
    {
      appointmentId: sampleSlot.appointmentId,
      tenantId,
      clinicId,
      patientMaskedName: sampleSlot.patientMaskedName,
      service: "Limpieza dental",
      startTime: "2026-06-10T10:00:00-05:00",
      endTime: "2026-06-10T11:00:00-05:00",
      paymentStatus: "deposit",
      origin: "walk-in",
      currency: "PEN",
      totalAmount: 150,
      depositAmount: 70,
      balanceAmount: 80,
      balanceVersion: 1,
    },
    {
      appointmentId: "apt-seed-002",
      tenantId,
      clinicId,
      patientMaskedName: "M. Torres",
      service: "Consulta general",
      startTime: "2026-06-10T11:30:00-05:00",
      endTime: "2026-06-10T12:00:00-05:00",
      paymentStatus: "paid",
      origin: "telefono",
      currency: "PEN",
      totalAmount: 80,
      depositAmount: null,
      balanceAmount: 0,
      balanceVersion: 2,
    },
    {
      appointmentId: "apt-seed-003",
      tenantId,
      clinicId,
      patientMaskedName: "R. Castillo",
      service: "Radiografía",
      startTime: "2026-06-10T14:00:00-05:00",
      endTime: "2026-06-10T14:30:00-05:00",
      paymentStatus: "pending",
      origin: "walk-in",
      currency: "PEN",
      totalAmount: 120,
      depositAmount: null,
      balanceAmount: 120,
      balanceVersion: 1,
    },
  ];
}

function buildLargeSlots(): AppointmentSlotData[] {
  const slots: AppointmentSlotData[] = [];
  const surnames = ["García", "López", "Martínez", "Rodríguez", "Sánchez"];
  const services = ["Consulta", "Limpieza", "Extracción", "Radiografía", "Control"];

  for (let i = 0; i < 240; i++) {
    const hour = 8 + Math.floor(i / 16);
    const minute = (i % 16) * 3;
    const paddedHour = String(hour).padStart(2, "0");
    const paddedMin = String(minute).padStart(2, "0");
    const initial = String.fromCharCode(65 + (i % 26));
    const surname = surnames[i % surnames.length];

    slots.push({
      appointmentId: `apt-large-${String(i).padStart(3, "0")}`,
      tenantId,
      clinicId,
      patientMaskedName: `${initial}. ${surname}`,
      service: services[i % services.length],
      startTime: `2026-06-10T${paddedHour}:${paddedMin}:00-05:00`,
      endTime: `2026-06-10T${paddedHour}:${paddedMin}:00-05:00`,
      paymentStatus: i % 3 === 0 ? "paid" : i % 3 === 1 ? "deposit" : "pending",
      origin: "walk-in",
      currency: "PEN",
      totalAmount: 80 + (i % 5) * 20,
      depositAmount: i % 3 === 1 ? 50 : null,
      balanceAmount: i % 3 === 0 ? 0 : 80 + (i % 5) * 20,
      balanceVersion: 1,
    });
  }
  return slots;
}

function buildTenantBSlots(): AppointmentSlotData[] {
  return [
    {
      appointmentId: "apt-tenant-b-001",
      tenantId: "clinica-esperanza-ar-test",
      clinicId: "clinic-esp-001",
      patientMaskedName: "L. Fernández",
      service: "Consulta",
      startTime: "2026-06-10T09:00:00-03:00",
      endTime: "2026-06-10T09:30:00-03:00",
      paymentStatus: "pending",
      origin: "referido",
      currency: "ARS",
      totalAmount: 8500,
      depositAmount: null,
      balanceAmount: 8500,
      balanceVersion: 1,
    },
  ];
}

// ---------------------------------------------------------------------------
// API response shape
// ---------------------------------------------------------------------------

function buildGridResponse(slots: AppointmentSlotData[]) {
  return {
    items: slots,
    total: slots.length,
    page: 1,
    per_page: slots.length || 20,
    view: "semana",
    range_start: "2026-06-09T00:00:00-05:00",
    range_end: "2026-06-15T23:59:59-05:00",
    freshness_at: new Date().toISOString(),
  };
}

// ---------------------------------------------------------------------------
// Mock setup / teardown
// ---------------------------------------------------------------------------

/**
 * Register page.route() intercept for the agenda grid endpoint.
 * Scoped to the provided page — no global contamination.
 *
 * @param page - Playwright Page instance
 * @param scenario - which dataset to return
 */
export async function setupAgendaGridMock(
  page: Page,
  scenario: AgendaGridScenario,
): Promise<void> {
  await page.route("**/api/v1/scheduling/agenda/grid**", (route) => {
    if (scenario === "network_error") {
      route.abort("failed").catch(() => undefined);
      return;
    }

    let slots: AppointmentSlotData[];
    switch (scenario) {
      case "with_seed":
        slots = buildSeedSlots();
        break;
      case "empty":
        slots = [];
        break;
      case "large":
        slots = buildLargeSlots();
        break;
      case "tenant_b":
        slots = buildTenantBSlots();
        break;
      default:
        slots = buildSeedSlots();
    }

    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(buildGridResponse(slots)),
    }).catch(() => undefined);
  });
}

/**
 * Unregister all agenda grid route mocks from the page.
 * Call in test.afterEach for proper isolation.
 */
export async function clearAgendaGridMock(page: Page): Promise<void> {
  await page.unrouteAll({ behavior: "ignoreErrors" });
}

/**
 * Update the payment status of a slot in the mock.
 * Simulates optimistic update: replaces grid response with modified slot status.
 * Call AFTER setupAgendaGridMock to override the running mock.
 */
export async function updateSlotPaymentStatusMock(
  page: Page,
  appointmentId: string,
  newStatus: AppointmentSlotData["paymentStatus"],
): Promise<void> {
  const slots = buildSeedSlots().map((s) =>
    s.appointmentId === appointmentId
      ? { ...s, paymentStatus: newStatus, balanceAmount: 0 }
      : s,
  );

  await page.route("**/api/v1/scheduling/agenda/grid**", (route) => {
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(buildGridResponse(slots)),
    }).catch(() => undefined);
  });
}
