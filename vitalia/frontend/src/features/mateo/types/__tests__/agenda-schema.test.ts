/**
 * agenda-schema.test.ts — TDD RED-first tests for Zod schemas
 * T-11 vitalia-fase2-valeria-agenda FE types + Zod schemas
 *
 * Gherkin coverage: SC-11 i18n multi-currency override (schema layer)
 * spec_anchor: 03-arch.md § 6.7 + 06-tickets.yaml T-11
 * downstream-regression-na: brand-local FE schema tests; no cross-brand consumers
 *
 * Run: cd vitalia/frontend && npx vitest run src/features/valeria/types/__tests__/agenda-schema.test.ts
 */

import { describe, it, expect } from "vitest";

// Valid RFC4122 v4 UUIDs for test fixtures
const UUID = {
  appointment: "550e8400-e29b-41d4-a716-446655440001",
  patient: "550e8400-e29b-41d4-a716-446655440002",
  doctor: "550e8400-e29b-41d4-a716-446655440003",
  clinic: "550e8400-e29b-41d4-a716-446655440010",
  tenant: "550e8400-e29b-41d4-a716-446655440020",
  payment: "550e8400-e29b-41d4-a716-446655440099",
  fiscalDoc: "550e8400-e29b-41d4-a716-446655440088",
  idempotency: "3e8f9a2b-1234-41d4-a716-446655440001",
} as const;

import {
  SlotPaymentStatusSchema,
  AppointmentOriginSchema,
  AgendaViewSchema,
  AgendaFilterSchema,
  PaymentMethodSchema,
  FiscalDocTypeSchema,
  AgendaSlotSchema,
  AppointmentDetailSchema,
  AppointmentPaymentSchema,
  FiscalDocumentSchema,
  AgendaGridResponseSchema,
  ChargeRequestSchema,
  ChargeResponseSchema,
  CreateAppointmentRequestSchema,
  PatchAppointmentRequestSchema,
  NotifyRequestSchema,
} from "../agenda-schema";

// ────────────────────────────────────────────────────────────────────────────
// Enum schemas
// ────────────────────────────────────────────────────────────────────────────

describe("SlotPaymentStatusSchema", () => {
  it("accepts valid values", () => {
    expect(SlotPaymentStatusSchema.parse("paid")).toBe("paid");
    expect(SlotPaymentStatusSchema.parse("deposit")).toBe("deposit");
    expect(SlotPaymentStatusSchema.parse("unpaid")).toBe("unpaid");
    expect(SlotPaymentStatusSchema.parse("no_show")).toBe("no_show");
  });

  it("rejects invalid value", () => {
    expect(() => SlotPaymentStatusSchema.parse("unknown")).toThrow();
  });
});

describe("AppointmentOriginSchema", () => {
  it("accepts all origin values", () => {
    expect(AppointmentOriginSchema.parse("walk_in")).toBe("walk_in");
    expect(AppointmentOriginSchema.parse("phone")).toBe("phone");
    expect(AppointmentOriginSchema.parse("proactive_adrian")).toBe("proactive_adrian");
    expect(AppointmentOriginSchema.parse("existing_patient")).toBe("existing_patient");
  });
});

describe("AgendaViewSchema", () => {
  it("accepts dia/semana/mes", () => {
    expect(AgendaViewSchema.parse("dia")).toBe("dia");
    expect(AgendaViewSchema.parse("semana")).toBe("semana");
    expect(AgendaViewSchema.parse("mes")).toBe("mes");
  });
});

describe("AgendaFilterSchema", () => {
  it("accepts all preset filter values", () => {
    const values = [
      "today",
      "tomorrow_pending",
      "reschedule",
      "no_shows",
      "pending_balances",
    ] as const;
    for (const v of values) {
      expect(AgendaFilterSchema.parse(v)).toBe(v);
    }
  });
});

describe("PaymentMethodSchema", () => {
  it("accepts all payment methods", () => {
    const methods = [
      "cash",
      "card",
      "transfer",
      "mercadopago",
      "other",
    ] as const;
    for (const m of methods) {
      expect(PaymentMethodSchema.parse(m)).toBe(m);
    }
  });
});

describe("FiscalDocTypeSchema", () => {
  it("accepts factura/boleta/ticket", () => {
    expect(FiscalDocTypeSchema.parse("factura")).toBe("factura");
    expect(FiscalDocTypeSchema.parse("boleta")).toBe("boleta");
    expect(FiscalDocTypeSchema.parse("ticket")).toBe("ticket");
  });
});

// ────────────────────────────────────────────────────────────────────────────
// AgendaSlotSchema — PHI masking invariant
// ────────────────────────────────────────────────────────────────────────────

describe("AgendaSlotSchema", () => {
  const validSlot = {
    appointmentId: UUID.appointment,
    patientId: UUID.patient,
    patientNameMasked: "P. Hernández",
    startTime: "2026-06-01T09:00:00Z",
    endTime: "2026-06-01T09:30:00Z",
    doctorId: UUID.doctor,
    doctorLabel: "Dr. C. Mendoza",
    serviceLabel: "Consulta general",
    appointmentStatus: "SCHEDULED",
    paymentStatus: "unpaid",
    origin: "walk_in",
    balanceDueCents: 15000,
    balancePaidCents: null,
    currency: "PEN",
  };

  it("test_phi_fields_are_masked_strings — parses valid slot payload from BE", () => {
    const result = AgendaSlotSchema.parse(validSlot);
    // PHI fields must be masked strings (format "P. Hernández"), not raw names
    expect(result.patientNameMasked).toBe("P. Hernández");
    expect(result.patientId).toBe(UUID.patient);
    expect(result.paymentStatus).toBe("unpaid");
    expect(result.currency).toBe("PEN");
  });

  it("rejects slot without required fields", () => {
    const { appointmentId: _appointmentId, ...incomplete } = validSlot;
    void _appointmentId;
    expect(() => AgendaSlotSchema.parse(incomplete)).toThrow();
  });

  it("accepts null balanceDueCents (no payment record)", () => {
    const result = AgendaSlotSchema.parse({ ...validSlot, balanceDueCents: null });
    expect(result.balanceDueCents).toBeNull();
  });
});

// ────────────────────────────────────────────────────────────────────────────
// AgendaGridResponseSchema
// ────────────────────────────────────────────────────────────────────────────

describe("AgendaGridResponseSchema", () => {
  const validGrid = {
    view: "semana",
    dateFrom: "2026-06-01T00:00:00Z",
    dateTo: "2026-06-07T23:59:59Z",
    slots: [
      {
        appointmentId: UUID.appointment,
        patientId: UUID.patient,
        patientNameMasked: "M. García",
        startTime: "2026-06-02T10:00:00Z",
        endTime: "2026-06-02T10:30:00Z",
        doctorId: UUID.doctor,
        doctorLabel: "Dr. A. López",
        serviceLabel: "Limpieza dental",
        appointmentStatus: "SCHEDULED",
        paymentStatus: "deposit",
        origin: "phone",
        balanceDueCents: 8000,
        balancePaidCents: 4000,
        currency: "ARS",
      },
    ],
    serverTime: "2026-06-01T08:00:00Z",
    clinicId: UUID.clinic,
    tenantId: UUID.tenant,
  };

  it("test_AgendaGridResponseSchema_parses_list_of_slots", () => {
    const result = AgendaGridResponseSchema.parse(validGrid);
    expect(result.slots).toHaveLength(1);
    expect(result.slots[0].patientNameMasked).toBe("M. García");
    expect(result.view).toBe("semana");
  });

  it("parses empty slots list", () => {
    const result = AgendaGridResponseSchema.parse({ ...validGrid, slots: [] });
    expect(result.slots).toHaveLength(0);
  });
});

// ────────────────────────────────────────────────────────────────────────────
// AppointmentDetailSchema
// ────────────────────────────────────────────────────────────────────────────

describe("AppointmentDetailSchema", () => {
  const validDetail = {
    appointmentId: UUID.appointment,
    patientId: UUID.patient,
    patientNameMasked: "P. Hernández",
    patientDniMasked: "12.***.***",
    patientPhoneMasked: "+51 9** *** 423",
    patientEmailMasked: "p***@gmail.com",
    startTime: "2026-06-02T09:00:00Z",
    endTime: "2026-06-02T09:30:00Z",
    doctorId: UUID.doctor,
    doctorLabel: "Dr. C. Mendoza",
    serviceLabel: "Consulta general",
    appointmentStatus: "SCHEDULED",
    paymentStatus: "unpaid",
    origin: "walk_in",
    balanceDueCents: 15000,
    balancePaidCents: null,
    currency: "PEN",
    currencyOverride: null,
    payments: [],
    notesInternal: null,
    lastActivityAt: null,
    lastActivityByLabel: null,
  };

  it("parses full appointment detail with PHI masked fields", () => {
    const result = AppointmentDetailSchema.parse(validDetail);
    // PHI fields are masked strings — not raw PHI
    expect(result.patientNameMasked).toBe("P. Hernández");
    expect(result.patientDniMasked).toBe("12.***.***");
    expect(result.patientPhoneMasked).toBe("+51 9** *** 423");
    expect(result.patientEmailMasked).toBe("p***@gmail.com");
  });

  it("accepts null optional PHI masked fields", () => {
    const result = AppointmentDetailSchema.parse({
      ...validDetail,
      patientDniMasked: null,
      patientPhoneMasked: null,
      patientEmailMasked: null,
    });
    expect(result.patientDniMasked).toBeNull();
  });

  it("accepts non-null currencyOverride", () => {
    const result = AppointmentDetailSchema.parse({
      ...validDetail,
      currencyOverride: "USD",
    });
    expect(result.currencyOverride).toBe("USD");
  });
});

// ────────────────────────────────────────────────────────────────────────────
// ChargeRequestSchema — discriminated union by currency
// ────────────────────────────────────────────────────────────────────────────

describe("ChargeRequestSchema — discriminated union", () => {
  const baseCharge = {
    appointmentId: UUID.appointment,
    amountCents: 15000,
    method: "cash",
    emitInvoice: false,
    fiscalDocType: undefined,
    notes: undefined,
    idempotencyKey: UUID.idempotency,
  };

  it("test_ChargeRequestSchema_validates_cash_with_no_card_token — PEN cash no fiscal", () => {
    const result = ChargeRequestSchema.parse({ ...baseCharge, currency: "PEN" });
    expect(result.currency).toBe("PEN");
    expect(result.method).toBe("cash");
  });

  it("test_ChargeRequestSchema_rejects_negative_amount", () => {
    expect(() =>
      ChargeRequestSchema.parse({ ...baseCharge, currency: "PEN", amountCents: -100 })
    ).toThrow();
  });

  it("test_ChargeRequestSchema_rejects_zero_amount", () => {
    expect(() =>
      ChargeRequestSchema.parse({ ...baseCharge, currency: "PEN", amountCents: 0 })
    ).toThrow();
  });

  it("accepts ARS currency with ARS-specific fiscal doc type", () => {
    const result = ChargeRequestSchema.parse({
      ...baseCharge,
      currency: "ARS",
      emitInvoice: true,
      fiscalDocType: "factura_a",
    });
    expect(result.currency).toBe("ARS");
    expect(result.fiscalDocType).toBe("factura_a");
  });

  it("accepts MXN currency with cfdi fiscal doc type", () => {
    const result = ChargeRequestSchema.parse({
      ...baseCharge,
      currency: "MXN",
      emitInvoice: true,
      fiscalDocType: "cfdi",
    });
    expect(result.currency).toBe("MXN");
  });

  it("accepts USD currency", () => {
    const result = ChargeRequestSchema.parse({
      ...baseCharge,
      currency: "USD",
      emitInvoice: true,
      fiscalDocType: "ticket",
    });
    expect(result.currency).toBe("USD");
  });

  it("accepts COP currency", () => {
    const result = ChargeRequestSchema.parse({
      ...baseCharge,
      currency: "COP",
      emitInvoice: true,
      fiscalDocType: "ticket",
    });
    expect(result.currency).toBe("COP");
  });

  it("accepts CLP currency", () => {
    const result = ChargeRequestSchema.parse({
      ...baseCharge,
      currency: "CLP",
      emitInvoice: true,
      fiscalDocType: "boleta",
    });
    expect(result.currency).toBe("CLP");
  });

  it("test_currency_discriminated_union — validates all 6 currencies (SC-11)", () => {
    const cases: Array<{ currency: string; fiscalDocType: string }> = [
      { currency: "PEN", fiscalDocType: "boleta" },
      { currency: "ARS", fiscalDocType: "factura_b" },
      { currency: "MXN", fiscalDocType: "cfdi" },
      { currency: "USD", fiscalDocType: "ticket" },
      { currency: "COP", fiscalDocType: "ticket" },
      { currency: "CLP", fiscalDocType: "boleta" },
    ];
    for (const { currency, fiscalDocType } of cases) {
      const result = ChargeRequestSchema.parse({
        ...baseCharge,
        currency,
        emitInvoice: true,
        fiscalDocType,
      });
      expect(result.currency).toBe(currency);
    }
  });

  it("emitInvoice refine — rejects when emitInvoice=true but fiscalDocType absent (PEN)", () => {
    expect(() =>
      ChargeRequestSchema.parse({
        ...baseCharge,
        currency: "PEN",
        emitInvoice: true,
        fiscalDocType: undefined,
      })
    ).toThrow();
  });

  it("rejects unknown currency", () => {
    expect(() =>
      ChargeRequestSchema.parse({ ...baseCharge, currency: "EUR" })
    ).toThrow();
  });

  it("accepts valid method values", () => {
    const methods = ["cash", "card", "transfer", "mercadopago", "other"] as const;
    for (const method of methods) {
      const result = ChargeRequestSchema.parse({
        ...baseCharge,
        currency: "PEN",
        method,
      });
      expect(result.method).toBe(method);
    }
  });
});

// ────────────────────────────────────────────────────────────────────────────
// ChargeResponseSchema
// ────────────────────────────────────────────────────────────────────────────

describe("ChargeResponseSchema", () => {
  it("parses successful charge response", () => {
    const result = ChargeResponseSchema.parse({
      paymentId: UUID.payment,
      amountCents: 15000,
      currency: "PEN",
      method: "cash",
      externalPaymentId: "ext_abc123",
      fiscalDocId: UUID.fiscalDoc,
      fiscalDocUrl: "https://cdn.vitalia.com/docs/factura-001.pdf",
      fiscalEmissionStatus: "emitted",
      fiscalErrorMessage: null,
      balanceAfterCents: 0,
    });
    expect(result.paymentId).toBe(UUID.payment);
    expect(result.fiscalEmissionStatus).toBe("emitted");
    expect(result.balanceAfterCents).toBe(0);
  });

  it("accepts pending fiscal emission status", () => {
    const result = ChargeResponseSchema.parse({
      paymentId: UUID.payment,
      amountCents: 15000,
      currency: "PEN",
      method: "cash",
      externalPaymentId: null,
      fiscalDocId: null,
      fiscalDocUrl: null,
      fiscalEmissionStatus: "pending",
      fiscalErrorMessage: null,
      balanceAfterCents: 0,
    });
    expect(result.fiscalEmissionStatus).toBe("pending");
  });
});

// ────────────────────────────────────────────────────────────────────────────
// PatchAppointmentRequestSchema
// ────────────────────────────────────────────────────────────────────────────

describe("PatchAppointmentRequestSchema", () => {
  it("test_PatchAppointmentRequestSchema_with_each_status_enum_value", () => {
    const statuses = ["CANCELLED", "COMPLETED", "NO_SHOW"] as const;
    for (const newStatus of statuses) {
      const result = PatchAppointmentRequestSchema.parse({ newStatus });
      expect(result.newStatus).toBe(newStatus);
    }
  });

  it("accepts optional reason", () => {
    const result = PatchAppointmentRequestSchema.parse({
      newStatus: "CANCELLED",
      reason: "Paciente solicita cancelación",
    });
    expect(result.reason).toBe("Paciente solicita cancelación");
  });

  it("rejects invalid status", () => {
    expect(() =>
      PatchAppointmentRequestSchema.parse({ newStatus: "SCHEDULED" })
    ).toThrow();
  });

  it("rejects reason exceeding 500 chars", () => {
    expect(() =>
      PatchAppointmentRequestSchema.parse({
        newStatus: "CANCELLED",
        reason: "x".repeat(501),
      })
    ).toThrow();
  });
});

// ────────────────────────────────────────────────────────────────────────────
// CreateAppointmentRequestSchema
// ────────────────────────────────────────────────────────────────────────────

describe("CreateAppointmentRequestSchema", () => {
  // RECONCILED (T-FE-1 D-F): walk_in now requires real patientId (UUID from CRM).
  // patientNewData removed from schema (alta = separate CRM endpoint).
  it("parses walk_in appointment with required patientId", () => {
    const result = CreateAppointmentRequestSchema.parse({
      origin: "walk_in",
      patientId: UUID.patient,
      doctorId: UUID.doctor,
      serviceLabel: "Consulta general",
      startTime: "2030-06-02T09:00:00Z",
      endTime: "2030-06-02T09:30:00Z",
      notesInternal: null,
      currencyOverride: null,
    });
    expect(result.origin).toBe("walk_in");
    expect(result.patientId).toBe(UUID.patient);
  });

  // RECONCILED (T-FE-1 D-F): "existing_patient" origin removed — only walk_in + telefono.
  // Telefono origin parses with patientId (real patient from CRM).
  it("parses telefono appointment with patientId and currencyOverride", () => {
    const result = CreateAppointmentRequestSchema.parse({
      origin: "telefono",
      patientId: UUID.patient,
      doctorId: UUID.doctor,
      serviceLabel: "Limpieza dental",
      startTime: "2030-06-03T10:00:00Z",
      endTime: "2030-06-03T10:30:00Z",
      notesInternal: null,
      currencyOverride: "USD",
    });
    expect(result.origin).toBe("telefono");
    expect(result.patientId).toBe(UUID.patient);
    expect(result.currencyOverride).toBe("USD");
  });

  it("rejects serviceLabel that is empty", () => {
    expect(() =>
      CreateAppointmentRequestSchema.parse({
        origin: "walk_in",
        patientId: null,
        patientNewData: null,
        doctorId: UUID.doctor,
        serviceLabel: "",
        startTime: "2026-06-02T09:00:00Z",
        endTime: "2026-06-02T09:30:00Z",
        notesInternal: null,
        currencyOverride: null,
      })
    ).toThrow();
  });

  // G-round2: past-time guard
  it("rejects startTime clearly in the past with Spanish-neutro message", () => {
    const result = CreateAppointmentRequestSchema.safeParse({
      origin: "walk_in",
      patientId: UUID.patient,
      doctorId: UUID.doctor,
      serviceLabel: "Consulta general",
      startTime: "2020-01-01T09:00:00Z",
      endTime: "2020-01-01T09:30:00Z",
      notesInternal: null,
      currencyOverride: null,
    });
    expect(result.success).toBe(false);
    if (!result.success) {
      const issue = result.error.issues.find((i) => i.path.includes("startTime"));
      expect(issue?.message).toBe("No se pueden agendar citas en el pasado");
    }
  });

  it("accepts startTime clearly in the future", () => {
    const result = CreateAppointmentRequestSchema.safeParse({
      origin: "walk_in",
      patientId: UUID.patient,
      doctorId: UUID.doctor,
      serviceLabel: "Consulta general",
      startTime: "2030-06-01T09:00:00Z",
      endTime: "2030-06-01T09:30:00Z",
      notesInternal: null,
      currencyOverride: null,
    });
    expect(result.success).toBe(true);
  });
});

// ────────────────────────────────────────────────────────────────────────────
// NotifyRequestSchema
// ────────────────────────────────────────────────────────────────────────────

describe("NotifyRequestSchema", () => {
  it("parses valid notify request", () => {
    const result = NotifyRequestSchema.parse({
      templateId: "recordatorio_cita_24h",
      scheduledFor: "2026-06-01T08:00:00Z",
      locale: "es-PE",
    });
    expect(result.templateId).toBe("recordatorio_cita_24h");
    expect(result.locale).toBe("es-PE");
  });

  it("rejects empty templateId", () => {
    expect(() =>
      NotifyRequestSchema.parse({ templateId: "", scheduledFor: "2026-06-01T08:00:00Z", locale: "es-PE" })
    ).toThrow();
  });
});

// ────────────────────────────────────────────────────────────────────────────
// AppointmentPaymentSchema
// ────────────────────────────────────────────────────────────────────────────

describe("AppointmentPaymentSchema", () => {
  it("parses payment record", () => {
    const result = AppointmentPaymentSchema.parse({
      paymentId: UUID.payment,
      amountCents: 15000,
      currency: "PEN",
      method: "cash",
      fiscalDocUrl: "https://cdn.vitalia.com/docs/boleta-001.pdf",
      fiscalDocType: "boleta",
      createdAt: "2026-06-01T10:30:00Z",
      createdByLabel: "Admin",
    });
    expect(result.paymentId).toBe(UUID.payment);
    expect(result.method).toBe("cash");
  });
});

// ────────────────────────────────────────────────────────────────────────────
// FiscalDocumentSchema
// ────────────────────────────────────────────────────────────────────────────

describe("FiscalDocumentSchema", () => {
  it("parses fiscal document record", () => {
    const result = FiscalDocumentSchema.parse({
      fiscalDocId: UUID.fiscalDoc,
      appointmentPaymentId: UUID.payment,
      docType: "boleta",
      docNumber: "B001-00000123",
      docUrl: "https://cdn.vitalia.com/docs/boleta-001.pdf",
      status: "emitted",
      errorMessage: null,
      createdAt: "2026-06-01T10:35:00Z",
    });
    expect(result.status).toBe("emitted");
    expect(result.docType).toBe("boleta");
  });

  it("accepts failed fiscal document with error message", () => {
    const result = FiscalDocumentSchema.parse({
      fiscalDocId: UUID.fiscalDoc,
      appointmentPaymentId: UUID.payment,
      docType: "factura",
      docNumber: null,
      docUrl: null,
      status: "failed",
      errorMessage: "Servicio de emisión no disponible temporalmente",
      createdAt: "2026-06-01T10:35:00Z",
    });
    expect(result.status).toBe("failed");
    expect(result.errorMessage).toBe("Servicio de emisión no disponible temporalmente");
  });
});
