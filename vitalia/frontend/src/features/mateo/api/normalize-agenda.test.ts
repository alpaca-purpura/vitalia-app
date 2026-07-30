// cap: scheduling.mateo-agenda
import { describe, it, expect } from "vitest";
import { normalizeAgendaGridResponse, normalizeAppointmentDetail } from "./normalize-agenda";

describe("normalizeAgendaGridResponse", () => {
  it("maps the real snake_case BE response → camelCase DTO + mapped enums", () => {
    const beWire = {
      view: "semana",
      date_from: "2026-06-15T00:00:00Z",
      date_to: "2026-06-21T23:59:59Z",
      server_time: "2026-06-21T08:00:00Z",
      clinic_id: "f035be5b-0ac4-5210-8fc3-395650ca2b83",
      tenant_id: "e69a691d-070e-5caf-a053-6e74642ec100",
      slots: [
        {
          appointment_id: "a1",
          patient_id: "p1",
          patient_name_masked: "M. López",
          start_time: "2026-06-15T14:00:00Z",
          end_time: "2026-06-15T14:30:00Z",
          doctor_id: "d1",
          doctor_label: "Dr. Rivas",
          service_label: "Limpieza",
          appointment_status: "NO_SHOW",
          payment_status: "succeeded",
          origin: "telefono",
          balance_due_cents: 80000,
          balance_paid_cents: null,
          currency: "MXN",
        },
        {
          appointment_id: "a2",
          patient_id: "p2",
          patient_name_masked: "J. Cruz",
          start_time: "2026-06-22T15:00:00Z",
          end_time: "2026-06-22T15:30:00Z",
          doctor_id: "d2",
          doctor_label: "Dra. García",
          service_label: "Control",
          appointment_status: "SCHEDULED",
          payment_status: "succeeded",
          origin: "proactivo_adrian",
          balance_due_cents: 0,
          balance_paid_cents: 150000,
          currency: "MXN",
        },
      ],
    };

    const dto = normalizeAgendaGridResponse(beWire);

    expect(dto.dateFrom).toBe("2026-06-15T00:00:00Z");
    expect(dto.clinicId).toBe("f035be5b-0ac4-5210-8fc3-395650ca2b83");
    expect(dto.slots).toHaveLength(2);

    // NO_SHOW dominates color; origin telefono → phone
    expect(dto.slots[0].startTime).toBe("2026-06-15T14:00:00Z");
    expect(dto.slots[0].paymentStatus).toBe("no_show");
    expect(dto.slots[0].origin).toBe("phone");
    expect(dto.slots[0].patientNameMasked).toBe("M. López");

    // succeeded + no remaining due → paid; origin proactivo_adrian → proactive_adrian
    expect(dto.slots[1].paymentStatus).toBe("paid");
    expect(dto.slots[1].origin).toBe("proactive_adrian");
  });

  it("is idempotent on already-camelCase input (MSW mocks / emptyGrid)", () => {
    const camel = {
      view: "semana",
      dateFrom: "2026-06-15T00:00:00Z",
      dateTo: "2026-06-21T23:59:59Z",
      serverTime: "2026-06-21T08:00:00Z",
      clinicId: "c",
      tenantId: "t",
      slots: [
        {
          appointmentId: "a1",
          patientId: "p1",
          patientNameMasked: "M. García",
          startTime: "2026-06-15T14:00:00Z",
          endTime: "2026-06-15T14:30:00Z",
          doctorId: "d1",
          doctorLabel: "Dr. X",
          serviceLabel: "Limpieza",
          appointmentStatus: "SCHEDULED",
          paymentStatus: "deposit",
          origin: "walk_in",
          balanceDueCents: 50000,
          balancePaidCents: 30000,
          currency: "PEN",
        },
      ],
    };

    const dto = normalizeAgendaGridResponse(camel);
    expect(dto.dateFrom).toBe("2026-06-15T00:00:00Z");
    expect(dto.slots[0].appointmentId).toBe("a1");
    expect(dto.slots[0].paymentStatus).toBe("deposit");
    expect(dto.slots[0].origin).toBe("walk_in");
  });

  it("returns empty slots for a malformed response", () => {
    expect(normalizeAgendaGridResponse(null).slots).toEqual([]);
    expect(normalizeAgendaGridResponse({ slots: "nope" }).slots).toEqual([]);
  });
});

describe("normalizeAppointmentDetail", () => {
  it("maps the snake_case detail response (incl payments id/amount rename) → Appointment", () => {
    const beWire = {
      appointment_id: "a1",
      patient_id: "p1",
      patient_name_masked: "M. López",
      patient_phone_masked: "+99 ** *** 11",
      start_time: "2026-06-15T14:00:00Z",
      end_time: "2026-06-15T14:30:00Z",
      doctor_id: "d1",
      doctor_label: "Ana García Mendoza",
      service_label: "Limpieza",
      appointment_status: "COMPLETED",
      payment_status: "succeeded",
      origin: "telefono",
      balance_due_cents: 0,
      balance_paid_cents: 80000,
      currency: "MXN",
      payments: [
        {
          payment_id: "pay1",
          amount_cents: 80000,
          currency: "MXN",
          method: "mercadopago",
          created_at: "2026-06-15T14:00:00Z",
        },
      ],
    };

    const appt = normalizeAppointmentDetail(beWire);

    expect(appt.appointmentId).toBe("a1");
    expect(appt.doctorLabel).toBe("Ana García Mendoza");
    expect(appt.origin).toBe("phone");
    expect(appt.payments).toHaveLength(1);
    expect(appt.payments[0].paymentId).toBe("pay1");
    expect(appt.payments[0].amountCents).toBe(80000);
  });
});
