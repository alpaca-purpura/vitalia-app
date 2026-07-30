// cap: scheduling.mateo-agenda
/**
 * normalize-agenda.ts — FE shim for the agenda grid response.
 *
 * The grid BE (`GET /scheduling/agenda/grid`) returns snake_case keys + engine enum values
 * (`appointment_status`, `payment_status: "succeeded"`, `origin: "telefono"`), while the FE
 * DTO expects camelCase + English unions (`startTime`, `paymentStatus: "paid"`, `origin:
 * "phone"`). The mismatch was masked for months by (a) an always-empty appointments table
 * (empty grid → no field access) and (b) MSW mocks that returned camelCase. It surfaced the
 * first time the grid carried real rows: every cell read `undefined` → the calendar rendered
 * blank. This maps the real wire shape into the DTO the components consume.
 *
 * Idempotent: already-camelCase input (emptyGrid fallback + MSW mocks) passes through unchanged
 * (each field falls back to its camelCase alias), so the existing FE test suite stays green.
 *
 * ponytail: temporary shim. Proper fix = align the BE AgendaGridResponseDTO to camelCase +
 * derive SlotPaymentStatus, resolve doctor/service/patient labels, and emit real balances
 * server-side. Tracked: story vitalia-scheduling-mateo-review (eje B).
 */
import type {
  AgendaGridResponse,
  AgendaSlot,
  Appointment,
  AppointmentOrigin,
  AppointmentPayment,
  SlotPaymentStatus,
} from "../types/agenda.types";

type Raw = Record<string, unknown>;

function asRecord(value: unknown): Raw {
  return value && typeof value === "object" ? (value as Raw) : {};
}

function firstString(...values: unknown[]): string | undefined {
  for (const v of values) if (typeof v === "string") return v;
  return undefined;
}

function firstIntOrNull(...values: unknown[]): number | null {
  for (const v of values) if (typeof v === "number") return v;
  return null;
}

/** BE origin enum (walk_in/telefono/proactivo_adrian/portal/sales_agent) → FE origin union. */
const ORIGIN_MAP: Record<string, AppointmentOrigin> = {
  walk_in: "walk_in",
  telefono: "phone",
  phone: "phone",
  proactivo_adrian: "proactive_adrian",
  proactive_adrian: "proactive_adrian",
  sales_agent: "proactive_adrian",
  portal: "existing_patient",
  existing_patient: "existing_patient",
};

/**
 * Derive the FE SlotPaymentStatus (paid|deposit|unpaid|no_show) from the BE row.
 * NO_SHOW status dominates the color. Otherwise best-effort from payment_status — the BE
 * balance_*_cents fields are unreliable today (review story eje B), so a "succeeded" payment
 * defaults to "paid" unless a positive paid balance with a remaining due is present (deposit).
 */
function toSlotPaymentStatus(raw: Raw): SlotPaymentStatus {
  const status = firstString(raw.appointment_status, raw.appointmentStatus) ?? "";
  if (status === "NO_SHOW") return "no_show";

  const pay = firstString(raw.payment_status, raw.paymentStatus) ?? "";
  if (pay === "paid" || pay === "pagado") return "paid";
  if (pay === "deposit" || pay === "deposito") return "deposit";
  if (pay === "unpaid" || pay === "sin_pago" || pay === "not_initiated") return "unpaid";
  if (pay === "no_show") return "no_show";
  if (pay === "succeeded") {
    const due = firstIntOrNull(raw.balance_due_cents, raw.balanceDueCents);
    const paid = firstIntOrNull(raw.balance_paid_cents, raw.balancePaidCents);
    if (paid !== null && paid > 0 && due !== null && due > 0) return "deposit";
    return "paid";
  }
  return "unpaid";
}

function normalizeSlot(input: unknown): AgendaSlot {
  const raw = asRecord(input);
  return {
    appointmentId: firstString(raw.appointment_id, raw.appointmentId) ?? "",
    patientId: firstString(raw.patient_id, raw.patientId) ?? "",
    patientNameMasked: firstString(raw.patient_name_masked, raw.patientNameMasked) ?? "—",
    startTime: firstString(raw.start_time, raw.startTime) ?? "",
    endTime: firstString(raw.end_time, raw.endTime) ?? "",
    doctorId: firstString(raw.doctor_id, raw.doctorId) ?? "",
    doctorLabel: firstString(raw.doctor_label, raw.doctorLabel) ?? "—",
    serviceLabel: firstString(raw.service_label, raw.serviceLabel) ?? "—",
    appointmentStatus: firstString(raw.appointment_status, raw.appointmentStatus) ?? "",
    paymentStatus: toSlotPaymentStatus(raw),
    origin: ORIGIN_MAP[firstString(raw.origin) ?? ""] ?? "walk_in",
    balanceDueCents: firstIntOrNull(raw.balance_due_cents, raw.balanceDueCents),
    balancePaidCents: firstIntOrNull(raw.balance_paid_cents, raw.balancePaidCents),
    currency: firstString(raw.currency) ?? "USD",
  };
}

function normalizePayment(input: unknown): AppointmentPayment {
  const raw = asRecord(input);
  return {
    paymentId: firstString(raw.payment_id, raw.paymentId) ?? "",
    amountCents: firstIntOrNull(raw.amount_cents, raw.amountCents) ?? 0,
    currency: firstString(raw.currency) ?? "USD",
    method: firstString(raw.method) ?? "",
    fiscalDocUrl: firstString(raw.fiscal_doc_url, raw.fiscalDocUrl) ?? null,
    fiscalDocType: firstString(raw.fiscal_doc_type, raw.fiscalDocType) ?? null,
    createdAt: firstString(raw.created_at, raw.createdAt) ?? "",
    createdByLabel: firstString(raw.created_by_label, raw.createdByLabel) ?? null,
  };
}

/** Map the raw appointment-detail response (snake_case BE or camelCase mock) → the FE Appointment shape. */
export function normalizeAppointmentDetail(input: unknown): Appointment {
  const raw = asRecord(input);
  const payments = Array.isArray(raw.payments) ? raw.payments.map(normalizePayment) : [];
  return {
    appointmentId: firstString(raw.appointment_id, raw.appointmentId) ?? "",
    patientId: firstString(raw.patient_id, raw.patientId) ?? "",
    patientNameMasked: firstString(raw.patient_name_masked, raw.patientNameMasked) ?? "—",
    patientDniMasked: firstString(raw.patient_dni_masked, raw.patientDniMasked) ?? null,
    patientPhoneMasked: firstString(raw.patient_phone_masked, raw.patientPhoneMasked) ?? null,
    patientEmailMasked: firstString(raw.patient_email_masked, raw.patientEmailMasked) ?? null,
    startTime: firstString(raw.start_time, raw.startTime) ?? "",
    endTime: firstString(raw.end_time, raw.endTime) ?? "",
    doctorId: firstString(raw.doctor_id, raw.doctorId) ?? "",
    doctorLabel: firstString(raw.doctor_label, raw.doctorLabel) ?? "—",
    serviceLabel: firstString(raw.service_label, raw.serviceLabel) ?? "—",
    appointmentStatus: firstString(raw.appointment_status, raw.appointmentStatus) ?? "",
    paymentStatus: toSlotPaymentStatus(raw),
    origin: ORIGIN_MAP[firstString(raw.origin) ?? ""] ?? "walk_in",
    balanceDueCents: firstIntOrNull(raw.balance_due_cents, raw.balanceDueCents),
    balancePaidCents: firstIntOrNull(raw.balance_paid_cents, raw.balancePaidCents),
    currency: firstString(raw.currency) ?? "USD",
    currencyOverride: firstString(raw.currency_override, raw.currencyOverride) ?? null,
    payments,
    notesInternal: firstString(raw.notes_internal, raw.notesInternal) ?? null,
    lastActivityAt: firstString(raw.last_activity_at, raw.lastActivityAt) ?? null,
    lastActivityByLabel: firstString(raw.last_activity_by_label, raw.lastActivityByLabel) ?? null,
  };
}

/** Map the raw grid response (snake_case BE or camelCase mock) → the FE DTO shape. */
export function normalizeAgendaGridResponse(input: unknown): AgendaGridResponse {
  const raw = asRecord(input);
  const slots = Array.isArray(raw.slots) ? raw.slots.map(normalizeSlot) : [];
  return {
    view: (firstString(raw.view) as AgendaGridResponse["view"]) ?? "semana",
    dateFrom: firstString(raw.date_from, raw.dateFrom) ?? "",
    dateTo: firstString(raw.date_to, raw.dateTo) ?? "",
    slots,
    serverTime: firstString(raw.server_time, raw.serverTime) ?? "",
    clinicId: firstString(raw.clinic_id, raw.clinicId) ?? "",
    tenantId: firstString(raw.tenant_id, raw.tenantId) ?? "",
  };
}
