// cap: scheduling.mateo-agenda
// story-origin: TBD
/**
 * agenda.types.ts — FE TypeScript types for Valeria Agenda feature.
 * T-11 vitalia-fase2-valeria-agenda
 *
 * Mirrors Pydantic DTOs (camelCase) from:
 *   - vitalia/backend/src/modules/vitalia/scheduling/api/dtos/agenda_dtos.py
 *   - vitalia/backend/src/modules/vitalia/payments/api/dtos/charge_dtos.py
 *   - vitalia/backend/src/modules/vitalia/fiscal/api/dtos/emit_dtos.py
 *
 * HIPAA-lite invariant: PHI fields are ALWAYS masked strings on the server.
 *   - patientNameMasked: "P. Hernández" (first initial + last name)
 *   - patientDniMasked: "12.***.***" (first 2 digits + masked)
 *   - patientPhoneMasked: "+51 9** *** 423" (prefix + masked)
 *   - patientEmailMasked: "p***@gmail.com" (initial + masked)
 * Frontend NEVER receives raw PHI. These are opaque masked strings only.
 *
 * ISO 8601 datetimes as string (no Date objects — avoids hydration mismatch).
 * Currency uses ISO 4217 (PEN, ARS, MXN, USD, COP, CLP).
 *
 * Named exports only — NO default exports (FSD-Lite boundary enforcement).
 * downstream-regression-na: brand-local FE types; no cross-brand consumers
 * spec_anchor: 03-arch.md § 2.2 + § 4.1..4.4 + 06-tickets.yaml T-11
 */

// ────────────────────────────────────────────────────────────────────────────
// Discriminated union literals
// ────────────────────────────────────────────────────────────────────────────

/** Payment status for a slot — drives border color in grid. */
export type SlotPaymentStatus = "paid" | "deposit" | "unpaid" | "no_show";

/** Source/channel of appointment booking. */
export type AppointmentOrigin =
  | "walk_in"
  | "phone"
  | "proactive_adrian"
  | "existing_patient";

/** Calendar view mode — persisted in URL. */
export type AgendaView = "dia" | "semana" | "mes";

/** Preset filter chip — drives agenda grid filtering. */
export type AgendaFilter =
  | "today"
  | "tomorrow_pending"
  | "reschedule"
  | "no_shows"
  | "pending_balances";

/** Payment method for cobrar saldo subform. Maps to BE method enum. */
export type PaymentMethod =
  | "cash"
  | "card"
  | "transfer"
  | "mercadopago"
  | "other";

/** Fiscal document type — values vary by currency/country. */
export type FiscalDocType = "factura" | "boleta" | "ticket";

// ────────────────────────────────────────────────────────────────────────────
// Slot + Grid types (agenda_dtos.py mirror)
// ────────────────────────────────────────────────────────────────────────────

/**
 * AgendaSlot — single appointment cell in the calendar grid.
 * Mirrors AgendaSlotDTO (PHI masked server-side).
 */
export interface AgendaSlot {
  /** Opaque UUID — used only to fetch detail drawer. */
  appointmentId: string;
  /** Opaque UUID — used for drawer fetch. NOT displayed directly. */
  patientId: string;
  /**
   * PHI-masked patient name. Format: "P. Hernández"
   * First initial + space + last name (server applies masking).
   * NEVER contains raw patient.name.
   */
  patientNameMasked: string;
  /** ISO 8601 start datetime (tz-aware from BE). */
  startTime: string;
  /** ISO 8601 end datetime. */
  endTime: string;
  /** Doctor UUID (opaque). */
  doctorId: string;
  /** Doctor display label, e.g. "Dr. C. Mendoza". NO PHI. */
  doctorLabel: string;
  /** Service display label, e.g. "Limpieza dental". */
  serviceLabel: string;
  /** Appointment status string. Values: SCHEDULED|CANCELLED|COMPLETED|NO_SHOW */
  appointmentStatus: string;
  /** Payment status drives slot border color. */
  paymentStatus: SlotPaymentStatus;
  /** Origin badge icon source. */
  origin: AppointmentOrigin;
  /** Cents owed (null = no payment record yet). */
  balanceDueCents: number | null;
  /** Cents already paid (null = no payment record). */
  balancePaidCents: number | null;
  /** ISO 4217 currency code. */
  currency: string;
}

/**
 * AgendaGridResponse — response from GET /api/v1/scheduling/agenda/grid.
 * Mirrors AgendaGridResponseDTO.
 */
export interface AgendaGridResponse {
  /** View mode resolved by BE. */
  view: AgendaView;
  /** ISO 8601 range start. */
  dateFrom: string;
  /** ISO 8601 range end. */
  dateTo: string;
  /** Ordered list of slots for the requested view + date. */
  slots: AgendaSlot[];
  /** ISO 8601 server-side timestamp for FreshnessIndicator. */
  serverTime: string;
  /** Clinic UUID (dual filter scope). */
  clinicId: string;
  /** Tenant UUID. */
  tenantId: string;
}

// ────────────────────────────────────────────────────────────────────────────
// Appointment Detail types (drawer)
// ────────────────────────────────────────────────────────────────────────────

/**
 * AppointmentPayment — individual payment record.
 * Mirrors AppointmentPaymentDTO.
 */
export interface AppointmentPayment {
  paymentId: string;
  amountCents: number;
  currency: string;
  method: string;
  /** URL to fiscal document PDF (null if not emitted). */
  fiscalDocUrl: string | null;
  /** Fiscal doc type identifier (null if not emitted). */
  fiscalDocType: string | null;
  /** ISO 8601 creation timestamp. */
  createdAt: string;
  /** Staff display label who registered the payment. NO PHI. */
  createdByLabel: string | null;
}

/**
 * Appointment — full detail for drawer panel.
 * Mirrors AppointmentDetailDTO.
 *
 * All PHI fields are masked server-side:
 *   - patientNameMasked: "P. Hernández"
 *   - patientDniMasked: "12.***.***"
 *   - patientPhoneMasked: "+51 9** *** 423"
 *   - patientEmailMasked: "p***@gmail.com"
 */
export interface Appointment {
  appointmentId: string;
  patientId: string;
  /** HIPAA-masked. "P. Hernández" format. */
  patientNameMasked: string;
  /** HIPAA-masked DNI. "12.***.***" format. Null if not registered. */
  patientDniMasked: string | null;
  /** HIPAA-masked phone. "+51 9** *** 423" format. Null if not registered. */
  patientPhoneMasked: string | null;
  /** HIPAA-masked email. "p***@gmail.com" format. Null if not registered. */
  patientEmailMasked: string | null;
  startTime: string;
  endTime: string;
  doctorId: string;
  doctorLabel: string;
  serviceLabel: string;
  appointmentStatus: string;
  paymentStatus: SlotPaymentStatus;
  origin: AppointmentOrigin;
  balanceDueCents: number | null;
  balancePaidCents: number | null;
  /** Tenant default currency (ISO 4217). */
  currency: string;
  /**
   * Per-transaction currency override (ISO 4217).
   * Used when clinic AR serves tourist in USD. Null = use tenant default.
   */
  currencyOverride: string | null;
  /** Payment records for this appointment. */
  payments: AppointmentPayment[];
  /** Internal staff notes — NO clinical PHI. */
  notesInternal: string | null;
  /** ISO 8601 timestamp of last status change. */
  lastActivityAt: string | null;
  /** Staff display label of last actor. NO PHI. */
  lastActivityByLabel: string | null;
}

// ────────────────────────────────────────────────────────────────────────────
// Fiscal document types
// ────────────────────────────────────────────────────────────────────────────

/**
 * FiscalDocument — fiscal emission result.
 * Mirrors FiscalEmitResponseDTO.
 */
export interface FiscalDocument {
  fiscalDocId: string;
  appointmentPaymentId: string;
  docType: string;
  docNumber: string | null;
  docUrl: string | null;
  status: "emitted" | "pending" | "failed";
  errorMessage: string | null;
  createdAt: string;
}
