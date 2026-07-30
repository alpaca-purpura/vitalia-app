// cap: __skip__
// story-origin: TBD
/**
 * agenda-handlers.ts — Fetch mock handlers for Valeria Agenda API endpoints.
 * T-12 vitalia-fase2-valeria-agenda
 *
 * NOTE: MSW is not installed as a dependency. These handlers use vi.fn() mocking
 * patterns compatible with Vitest. Import and use in test files via mockFetch().
 *
 * Handlers cover:
 *   - GET /api/v1/scheduling/agenda/grid → AgendaGridResponseDTO
 *   - GET /api/v1/scheduling/agenda/aggregates → AgendaAggregatesResponse
 *   - GET /api/v1/scheduling/appointments/:id → AppointmentDetailDTO
 *   - POST /api/v1/scheduling/appointments → created appointment
 *   - PATCH /api/v1/scheduling/appointments/:id → patched appointment
 *   - POST /api/v1/payments/charge → ChargeResponseDTO
 *   - POST /api/v1/fiscal/emit → FiscalDocument
 *   - POST /api/v1/notify/reminder → SendNotificationResponse
 *
 * Scenario support:
 *   - SC-4: cross-clinic 403 response
 *   - SC-5: race condition (idempotency key reuse → 409)
 *
 * downstream-regression-na: brand-local test utilities; no cross-brand consumers
 * spec_anchor: 06-tickets.yaml T-12 (A4)
 */

import type { AgendaGridResponseDTO } from "../../../features/mateo/types/agenda-schema";
import type { Appointment } from "../../../features/mateo/types/agenda.types";

// ── Mock data fixtures ─────────────────────────────────────────────────────────

export const MOCK_TENANT_ID = "tenant-clinic-pe-001";
export const MOCK_CLINIC_ID = "clinic-lima-001";
export const MOCK_APPOINTMENT_ID = "appt-uuid-001";
export const MOCK_PAYMENT_ID = "payment-uuid-001";

export const MOCK_AGENDA_GRID: AgendaGridResponseDTO = {
  view: "semana",
  dateFrom: "2026-05-25",
  dateTo: "2026-05-31",
  slots: [
    {
      appointmentId: MOCK_APPOINTMENT_ID,
      patientId: "patient-uuid-001",
      patientNameMasked: "M. García",
      startTime: "2026-05-26T09:00:00-05:00",
      endTime: "2026-05-26T10:00:00-05:00",
      doctorId: "doctor-uuid-001",
      doctorLabel: "Dr. C. Mendoza",
      serviceLabel: "Consulta general",
      appointmentStatus: "SCHEDULED",
      paymentStatus: "unpaid",
      origin: "walk_in",
      balanceDueCents: 12000,
      balancePaidCents: 0,
      currency: "PEN",
    },
  ],
  serverTime: "2026-05-26T12:00:00Z",
  clinicId: MOCK_CLINIC_ID,
  tenantId: MOCK_TENANT_ID,
};

export const MOCK_APPOINTMENT_DETAIL: Appointment = {
  appointmentId: MOCK_APPOINTMENT_ID,
  patientId: "patient-uuid-001",
  patientNameMasked: "M. García",
  patientDniMasked: "71.***.***",
  patientPhoneMasked: "+51 9** *** 501",
  patientEmailMasked: "m***@gmail.com",
  startTime: "2026-05-26T09:00:00-05:00",
  endTime: "2026-05-26T10:00:00-05:00",
  doctorId: "doctor-uuid-001",
  doctorLabel: "Dr. C. Mendoza",
  serviceLabel: "Consulta general",
  appointmentStatus: "SCHEDULED",
  paymentStatus: "unpaid",
  origin: "walk_in",
  balanceDueCents: 12000,
  balancePaidCents: 0,
  currency: "PEN",
  currencyOverride: null,
  payments: [],
  notesInternal: null,
  lastActivityAt: null,
  lastActivityByLabel: null,
};

export const MOCK_CHARGE_RESPONSE = {
  paymentId: MOCK_PAYMENT_ID,
  appointmentId: MOCK_APPOINTMENT_ID,
  amountCents: 12000,
  currency: "PEN",
  method: "cash",
  status: "success",
  fiscalDocUrl: null,
  fiscalDocType: null,
  createdAt: "2026-05-26T12:30:00Z",
};

export const MOCK_FISCAL_DOCUMENT = {
  fiscalDocId: "fiscal-uuid-001",
  appointmentPaymentId: MOCK_PAYMENT_ID,
  docType: "boleta",
  docNumber: "B001-00000123",
  docUrl: "https://vitalia-fiscal.example.com/boleta/B001-00000123.pdf",
  status: "emitted" as const,
  errorMessage: null,
  createdAt: "2026-05-26T12:31:00Z",
};

export const MOCK_REMINDER_RESPONSE = {
  messageId: "msg-uuid-001",
  channel: "whatsapp",
  sentAt: "2026-05-26T13:00:00Z",
};

// ── Request URL matchers ───────────────────────────────────────────────────────

export function isAgendaGridUrl(url: string): boolean {
  return url.includes("/api/v1/scheduling/agenda/grid");
}

export function isAgendaAggregatesUrl(url: string): boolean {
  return url.includes("/api/v1/scheduling/agenda/aggregates");
}

export function isAppointmentDetailUrl(url: string): boolean {
  return (
    url.includes("/api/v1/scheduling/appointments/") &&
    !url.endsWith("/api/v1/scheduling/appointments")
  );
}

export function isCreateAppointmentUrl(url: string): boolean {
  return url === "/api/v1/scheduling/appointments";
}

export function isPatchAppointmentUrl(url: string): boolean {
  return (
    url.includes("/api/v1/scheduling/appointments/") &&
    !url.endsWith("/api/v1/scheduling/appointments")
  );
}

export function isChargeUrl(url: string): boolean {
  return url.includes("/api/v1/payments/charge");
}

export function isFiscalEmitUrl(url: string): boolean {
  return url.includes("/api/v1/fiscal/emit");
}

export function isNotifyUrl(url: string): boolean {
  return url.includes("/api/v1/notify/reminder");
}

// ── Mock fetch handler factory ─────────────────────────────────────────────────

export interface MockFetchOptions {
  /** Scenario: "happy_path" | "cross_clinic_403" | "race_condition_409" */
  scenario?: "happy_path" | "cross_clinic_403" | "race_condition_409";
  /** Custom response overrides per endpoint */
  overrides?: {
    grid?: Partial<AgendaGridResponseDTO>;
    charge?: Record<string, unknown>;
    fiscal?: Record<string, unknown>;
  };
}

/**
 * Creates a vi.fn() mock for global.fetch that responds to agenda API endpoints.
 *
 * Usage in tests:
 *   global.fetch = createAgendaMockFetch({ scenario: "happy_path" });
 *
 * Covers SC-4 (cross-clinic 403) and SC-5 (race condition 409) scenarios.
 */
export function createAgendaMockFetch(
  options: MockFetchOptions = {},
): typeof global.fetch {
  const { scenario = "happy_path", overrides } = options;

  return vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = typeof input === "string" ? input : input.toString();
    const method = init?.method ?? "GET";

    // SC-4: Cross-clinic 403 scenario
    if (scenario === "cross_clinic_403") {
      return new Response(
        JSON.stringify({ detail: "Acceso no autorizado a esta clínica" }),
        { status: 403, headers: { "Content-Type": "application/json" } },
      );
    }

    // SC-5: Race condition / idempotency key reuse
    if (scenario === "race_condition_409" && isChargeUrl(url)) {
      return new Response(
        JSON.stringify({ detail: "Pago duplicado detectado" }),
        { status: 409, headers: { "Content-Type": "application/json" } },
      );
    }

    // Happy path routing
    if (method === "GET" && isAgendaGridUrl(url)) {
      const grid = { ...MOCK_AGENDA_GRID, ...overrides?.grid };
      return new Response(JSON.stringify(grid), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    }

    if (method === "GET" && isAgendaAggregatesUrl(url)) {
      return new Response(
        JSON.stringify({
          totalSlots: 1,
          pendingPayment: 1,
          totalRevenueCents: 0,
          currency: "PEN",
          noShows: 0,
          dateFrom: "2026-05-25",
          dateTo: "2026-05-31",
        }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      );
    }

    if (method === "GET" && isAppointmentDetailUrl(url)) {
      return new Response(JSON.stringify(MOCK_APPOINTMENT_DETAIL), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    }

    if (method === "POST" && isCreateAppointmentUrl(url)) {
      return new Response(JSON.stringify(MOCK_APPOINTMENT_DETAIL), {
        status: 201,
        headers: { "Content-Type": "application/json" },
      });
    }

    if (method === "PATCH" && isPatchAppointmentUrl(url)) {
      return new Response(
        JSON.stringify({ ...MOCK_APPOINTMENT_DETAIL, appointmentStatus: "COMPLETED" }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      );
    }

    if (method === "POST" && isChargeUrl(url)) {
      const charge = { ...MOCK_CHARGE_RESPONSE, ...overrides?.charge };
      return new Response(JSON.stringify(charge), {
        status: 201,
        headers: { "Content-Type": "application/json" },
      });
    }

    if (method === "POST" && isFiscalEmitUrl(url)) {
      const fiscal = { ...MOCK_FISCAL_DOCUMENT, ...overrides?.fiscal };
      return new Response(JSON.stringify(fiscal), {
        status: 201,
        headers: { "Content-Type": "application/json" },
      });
    }

    if (method === "POST" && isNotifyUrl(url)) {
      return new Response(JSON.stringify(MOCK_REMINDER_RESPONSE), {
        status: 201,
        headers: { "Content-Type": "application/json" },
      });
    }

    // Telemetry — always 200 (fire-and-forget)
    if (url.includes("/api/telemetry/")) {
      return new Response(JSON.stringify({ ok: true }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    }

    // Unhandled URL — fail explicitly in tests
    throw new Error(`[agenda-handlers] Unhandled mock fetch: ${method} ${url}`);
  }) as typeof global.fetch;
}
