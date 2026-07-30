// cap: scheduling.mateo-agenda
// story-origin: vitalia-fase2-s1-TBD
/**
 * telemetry.ts — Telemetría UX para Valeria Agenda (growth_studio_event).
 *
 * PII-safe por diseño (HIPAA-lite overlay):
 *   - NUNCA incluye patient.name, patient.dni, patient.email ni ningún campo PHI.
 *   - Solo acepta IDs hash (appointment_id_hash, patient_id_hash) y buckets semánticos.
 *   - Si el payload contiene campos PHI conocidos, son strippeados antes del POST.
 *
 * Fire-and-forget: trackEvent NUNCA lanza error al caller.
 *   - Fallos de red o errores 4xx/5xx se logean en console.warn y se ignoran.
 *   - Telemetría es auxiliar — no bloquea el flujo principal de la UI.
 *
 * Endpoint: POST /api/telemetry/growth-studio-event
 * Tabla destino BE: growth_studio_event (brand-local, per 03-arch A4)
 *
 * Refs:
 *   - CONTEXT-BRIEF § 3 (7 event types)
 *   - vitalia/.claude/rules/hipaa-lite.md (PHI fields SSoT)
 *   - .claude/rules/tenant-isolation.md
 */

import { z } from "zod";
import { fetchClient } from "@/lib/api/fetchClient";

// ── 1. Event type enum (7 canónicos per 03-arch § telemetry) ──────────────────

/**
 * Tipos de evento críticos del funnel Valeria Agenda.
 * Mapean 1:1 a `growth_studio_event.event_type` (BE).
 */
export const TrackEventType = {
  /** Usuario abre el tab Agenda (por primera vez o regresa) */
  AGENDA_VIEWED: "agenda_viewed",
  /** Usuario hace click en un slot para abrir el drawer de detalle */
  SLOT_DRAWER_OPENED: "slot_drawer_opened",
  /** Usuario inicia el flujo de cobrar saldo (click botón Cobrar) */
  CHARGE_INITIATED: "charge_initiated",
  /** El cobro se completó exitosamente (payment_adapter OK) */
  CHARGE_SUCCEEDED: "charge_succeeded",
  /** El cobro falló (payment_adapter error o red) */
  CHARGE_FAILED: "charge_failed",
  /** Se emitió un comprobante fiscal (fiscal_emit OK) */
  INVOICE_EMITTED: "invoice_emitted",
  /** Se envió un recordatorio al paciente (notify OK) */
  REMINDER_SENT: "reminder_sent",
} as const;

export type TrackEventType = (typeof TrackEventType)[keyof typeof TrackEventType];

// ── 2. PHI fields blocklist (HIPAA-lite SSoT) ─────────────────────────────────

/**
 * Campos PHI prohibidos en payload de telemetría.
 * Fuente: vitalia/.claude/rules/hipaa-lite.md § PHI fields canónicos.
 */
const PHI_BLOCKED_KEYS: ReadonlySet<string> = new Set([
  "patient_name",
  "patient_dni",
  "patient_cuit",
  "patient_date_of_birth",
  "patient_phone",
  "patient_email",
  "patient_address",
  "diagnosis",
  "treatment_plan",
  "medication",
  "dosage",
  "allergies",
  "symptoms",
  "medical_notes",
  "lab_results",
  "vital_signs",
  "imaging_url",
  "xray_filename",
  "ultrasound_report",
  "previous_treatments",
  "family_history",
  "surgical_history",
  // Variantes con prefijo raw_ que podrían llegar por error
  "name",
  "dni",
  "email",
  "phone",
]);

/**
 * Sanitiza el payload eliminando cualquier campo PHI conocido.
 * Operación shallow (no recursiva) — los campos PHI nunca deberían estar anidados en telemetría.
 */
function sanitizePayload(payload: Record<string, unknown>): Record<string, unknown> {
  const clean: Record<string, unknown> = {};
  for (const [key, value] of Object.entries(payload)) {
    if (!PHI_BLOCKED_KEYS.has(key)) {
      clean[key] = value;
    }
  }
  return clean;
}

// ── 3. Zod schema para validación de payload ──────────────────────────────────

/**
 * Schema Zod para el body completo del evento de telemetría.
 * Solo acepta campos permitidos (sin PHI).
 *
 * El payload es un record genérico: la validación está en el sanitizer.
 * Los IDs deben ser hash/UUIDs, nunca texto plano identificable.
 */
export const telemetryEventSchema = z.object({
  event_type: z.enum([
    TrackEventType.AGENDA_VIEWED,
    TrackEventType.SLOT_DRAWER_OPENED,
    TrackEventType.CHARGE_INITIATED,
    TrackEventType.CHARGE_SUCCEEDED,
    TrackEventType.CHARGE_FAILED,
    TrackEventType.INVOICE_EMITTED,
    TrackEventType.REMINDER_SENT,
  ]),
  occurred_at: z.string().datetime(),
  payload: z.record(z.string(), z.unknown()),
});

export type TelemetryEvent = z.infer<typeof telemetryEventSchema>;

// ── 4. Allowed payload keys (documentación — no enforcement) ──────────────────

/**
 * Payload tipado para cada event type.
 * Todos los campos son opcionales — el caller provee lo que tiene disponible.
 * NUNCA incluir campos PHI — ver PHI_BLOCKED_KEYS arriba.
 */
export interface TelemetryPayload {
  /** UUID hash del tenant (no texto plano) */
  tenant_id?: string;
  /** UUID hash de la cita (no patient data) */
  appointment_id_hash?: string;
  /** Modo de vista de la agenda: "semana" | "dia" | "mes" */
  view_mode?: string;
  /** Filtro preseleccionado activo al ver la agenda */
  preset_filter?: string;
  /** Clave de idempotencia del cobro (UUID generado por cliente) */
  idempotency_key?: string;
  /** Bucket del método de pago: "efectivo" | "transferencia" | "tarjeta" */
  payment_bucket?: string;
  /** Bucket del error de cobro: "payment_declined" | "network" | "fiscal_fail" | "unknown" */
  error_bucket?: string;
  /** Tipo de documento fiscal emitido: "boleta" | "factura" | "ticket" */
  document_type?: string;
  /** Canal de recordatorio: "whatsapp" | "sms" | "email" */
  reminder_channel?: string;
  /** Origen del turno: "walk_in" | "telefono" | "adrian" (sin patient identity) */
  appointment_origin?: string;
}

// ── 5. trackEvent — main export ───────────────────────────────────────────────

/**
 * Contexto de autenticación tenant-aware para el POST de telemetría.
 *
 * El endpoint BE (`/api/telemetry/growth-studio-event`) es tenant-scoped: resuelve
 * y verifica la membresía vía ClinicResolver, así que el POST DEBE llevar token +
 * X-Tenant-ID (y X-Clinic-ID para el dual filter HIPAA-lite). Por eso `trackEvent`
 * ya NO usa `fetch` crudo (que iba sin headers → 404/401) sino `fetchClient`.
 *
 * Obtener en el caller (Client Component):
 *   - token: `useAuth().getToken()`
 *   - tenantId: `useTenantId()` o el `tenantId` de props
 *   - clinicId: `useClinicId()`
 */
export interface TelemetryAuth {
  /** Clerk JWT (`useAuth().getToken()`). Null mientras Clerk carga → se omite el evento. */
  token: string | null;
  /** Luana-core-iam tenant ID (X-Tenant-ID). Null → se omite el evento. */
  tenantId: string | null;
  /** Clinic ID (X-Clinic-ID, dual filter). Opcional. */
  clinicId?: string | null;
}

/**
 * Envía un evento de telemetría al endpoint growth-studio-event vía `fetchClient`.
 *
 * Garantías:
 * - Fire-and-forget: NUNCA lanza error al caller (auxiliar, no bloquea la UI).
 * - PII-safe: sanitiza el payload antes del POST (elimina campos PHI).
 * - Tenant-aware: `fetchClient` inyecta Authorization + X-Tenant-ID + X-Clinic-ID.
 * - Skip silencioso: si falta token o tenantId (Clerk aún cargando), NO hace el POST
 *   (evita 401/404 que ensuciarían la consola / dispararían el gate anti-burbuja).
 * - Timestamp ISO 8601 auto-generado en el cliente (server normaliza con su reloj).
 *
 * @param eventType - Tipo de evento (TrackEventType enum)
 * @param payload - Datos del evento (PII-free: solo IDs hash + buckets semánticos)
 * @param auth - Contexto tenant/auth (token + tenantId + clinicId)
 * @returns Promise<void> — siempre resuelve, nunca rechaza
 */
export async function trackEvent(
  eventType: TrackEventType,
  payload: TelemetryPayload | Record<string, unknown>,
  auth: TelemetryAuth,
): Promise<void> {
  // Fire-forget: sin auth resuelta (token + tenant + clinic) no hay POST.
  // El endpoint es clinic-scoped (dual filter) → sin clinicId el POST sería 422.
  // Telemetría es auxiliar: si el contexto aún no cargó, se omite el evento
  // (no 401/404/422, no ruido en consola, no trip del gate anti-burbuja).
  if (!auth.token || !auth.tenantId || !auth.clinicId) {
    return;
  }

  try {
    const sanitized = sanitizePayload(payload as Record<string, unknown>);

    const body: TelemetryEvent = {
      event_type: eventType,
      occurred_at: new Date().toISOString(),
      payload: sanitized,
    };

    await fetchClient<{ accepted: boolean }>("/api/telemetry/growth-studio-event", {
      method: "POST",
      token: auth.token,
      tenantId: auth.tenantId,
      clinicId: auth.clinicId ?? null,
      body: JSON.stringify(body),
    });
  } catch (err) {
    // Error de red / 4xx-5xx (fetchClient lanza ApiError) — log y silenciar.
    console.warn("[telemetry] Error al enviar evento de telemetría:", err, {
      event_type: eventType,
    });
  }
}
