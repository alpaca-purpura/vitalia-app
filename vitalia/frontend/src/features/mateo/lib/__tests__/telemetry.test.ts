/**
 * telemetry.test.ts — Tests para vitalia/features/mateo/lib/telemetry.ts
 *
 * TDD RED→GREEN: tests actualizados al contrato tenant-aware (fetchClient).
 * Cubre: TrackEventType enum, trackEvent PII-safe, tenant headers (Authorization +
 *        X-Tenant-ID), skip-sin-auth, error handling (non-blocking).
 *
 * Contrato nuevo (vitalia-fase2-adrian-inbox · telemetry-404 fix):
 *   trackEvent(eventType, payload, auth) usa `fetchClient` (NO `fetch` crudo) →
 *   inyecta Authorization + X-Tenant-ID + X-Clinic-ID. Sin token/tenant → skip (no POST).
 *
 * HIPAA-lite: verifica que PHI (patient.name, DNI) NUNCA aparezca en payload.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { TrackEventType, trackEvent, type TelemetryAuth } from "../telemetry";

// ── Mock global fetch (fetchClient lo usa por debajo) ───────────────────────────
const mockFetch = vi.fn();

const AUTH: TelemetryAuth = {
  token: "test-jwt-token",
  tenantId: "tenant-123",
  clinicId: "clinic-456",
};

beforeEach(() => {
  vi.stubGlobal("fetch", mockFetch);
  mockFetch.mockResolvedValue({
    ok: true,
    status: 202,
    json: async () => ({ accepted: true }),
  } as Response);
});

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

// ── 1. TrackEventType enum ─────────────────────────────────────────────────────

describe("TrackEventType enum", () => {
  it("debe exportar 7 event types canónicos", () => {
    expect(TrackEventType.AGENDA_VIEWED).toBe("agenda_viewed");
    expect(TrackEventType.SLOT_DRAWER_OPENED).toBe("slot_drawer_opened");
    expect(TrackEventType.CHARGE_INITIATED).toBe("charge_initiated");
    expect(TrackEventType.CHARGE_SUCCEEDED).toBe("charge_succeeded");
    expect(TrackEventType.CHARGE_FAILED).toBe("charge_failed");
    expect(TrackEventType.INVOICE_EMITTED).toBe("invoice_emitted");
    expect(TrackEventType.REMINDER_SENT).toBe("reminder_sent");
  });

  it("debe tener exactamente 7 valores", () => {
    const values = Object.values(TrackEventType);
    expect(values).toHaveLength(7);
  });
});

// ── 2. trackEvent — happy path ─────────────────────────────────────────────────

describe("trackEvent — happy path", () => {
  it("debe hacer POST a /api/telemetry/growth-studio-event", async () => {
    await trackEvent(TrackEventType.AGENDA_VIEWED, { view_mode: "semana" }, AUTH);

    expect(mockFetch).toHaveBeenCalledOnce();
    const [url, init] = mockFetch.mock.calls[0] as [string, RequestInit];
    expect(url).toBe("/api/telemetry/growth-studio-event");
    expect(init.method).toBe("POST");
  });

  it("debe inyectar Authorization + X-Tenant-ID (tenant-aware vía fetchClient)", async () => {
    await trackEvent(TrackEventType.AGENDA_VIEWED, { view_mode: "semana" }, AUTH);

    const [, init] = mockFetch.mock.calls[0] as [string, RequestInit];
    const headers = init.headers as Record<string, string>;
    expect(headers["Authorization"]).toBe("Bearer test-jwt-token");
    expect(headers["X-Tenant-ID"]).toBe("tenant-123");
    expect(headers["X-Clinic-ID"]).toBe("clinic-456");
    expect(headers["Content-Type"]).toBe("application/json");
  });

  it("debe incluir event_type en el cuerpo JSON", async () => {
    await trackEvent(TrackEventType.SLOT_DRAWER_OPENED, { appointment_id_hash: "abc123" }, AUTH);

    const [, init] = mockFetch.mock.calls[0] as [string, RequestInit];
    const body = JSON.parse(init.body as string);
    expect(body.event_type).toBe("slot_drawer_opened");
  });

  it("debe incluir timestamp ISO 8601 en el cuerpo", async () => {
    await trackEvent(TrackEventType.CHARGE_INITIATED, { idempotency_key: "idem-uuid-123" }, AUTH);

    const [, init] = mockFetch.mock.calls[0] as [string, RequestInit];
    const body = JSON.parse(init.body as string);
    expect(body.occurred_at).toBeDefined();
    expect(new Date(body.occurred_at).toString()).not.toBe("Invalid Date");
  });

  it("debe pasar el payload al cuerpo JSON", async () => {
    const payload = { appointment_id_hash: "hash-abc", payment_bucket: "saldo" };
    await trackEvent(TrackEventType.CHARGE_SUCCEEDED, payload, AUTH);

    const [, init] = mockFetch.mock.calls[0] as [string, RequestInit];
    const body = JSON.parse(init.body as string);
    expect(body.payload).toMatchObject(payload);
  });
});

// ── 3. Skip sin auth (fire-forget — evita 401/404) ──────────────────────────────

describe("trackEvent — skip sin auth", () => {
  it("NO debe hacer POST si falta el token", async () => {
    await trackEvent(TrackEventType.AGENDA_VIEWED, { view_mode: "semana" }, {
      token: null,
      tenantId: "tenant-123",
    });
    expect(mockFetch).not.toHaveBeenCalled();
  });

  it("NO debe hacer POST si falta el tenantId", async () => {
    await trackEvent(TrackEventType.AGENDA_VIEWED, { view_mode: "semana" }, {
      token: "tk",
      tenantId: null,
    });
    expect(mockFetch).not.toHaveBeenCalled();
  });

  it("NO debe hacer POST si falta el clinicId (endpoint clinic-scoped → evita 422)", async () => {
    await trackEvent(TrackEventType.AGENDA_VIEWED, { view_mode: "semana" }, {
      token: "tk",
      tenantId: "tenant-123",
      clinicId: null,
    });
    expect(mockFetch).not.toHaveBeenCalled();
  });
});

// ── 4. PII safety — HIPAA-lite ─────────────────────────────────────────────────

describe("trackEvent — PII safety (HIPAA-lite)", () => {
  it("NO debe incluir patient_name en el payload enviado", async () => {
    const unsafePayload: Record<string, unknown> = {
      appointment_id_hash: "hash-123",
      patient_name: "María González",
    };

    await trackEvent(TrackEventType.SLOT_DRAWER_OPENED, unsafePayload, AUTH);

    const [, init] = mockFetch.mock.calls[0] as [string, RequestInit];
    const body = JSON.parse(init.body as string);
    const bodyStr = JSON.stringify(body);

    expect(bodyStr).not.toContain("María González");
    expect(body.payload).not.toHaveProperty("patient_name");
    expect(body.payload).toHaveProperty("appointment_id_hash", "hash-123");
  });

  it("NO debe incluir patient_dni en el payload enviado", async () => {
    const unsafePayload: Record<string, unknown> = {
      appointment_id_hash: "hash-456",
      patient_dni: "12345678",
    };

    await trackEvent(TrackEventType.INVOICE_EMITTED, unsafePayload, AUTH);

    const [, init] = mockFetch.mock.calls[0] as [string, RequestInit];
    const body = JSON.parse(init.body as string);
    const bodyStr = JSON.stringify(body);

    expect(bodyStr).not.toContain("12345678");
    expect(body.payload).not.toHaveProperty("patient_dni");
  });

  it("NO debe incluir diagnosis en el payload enviado", async () => {
    const unsafePayload: Record<string, unknown> = {
      appointment_id_hash: "hash-789",
      diagnosis: "Hipertensión arterial grado II",
    };

    await trackEvent(TrackEventType.SLOT_DRAWER_OPENED, unsafePayload, AUTH);

    const [, init] = mockFetch.mock.calls[0] as [string, RequestInit];
    const body = JSON.parse(init.body as string);

    expect(body.payload).not.toHaveProperty("diagnosis");
    expect(body.payload).toHaveProperty("appointment_id_hash");
  });
});

// ── 5. Error handling — non-blocking ──────────────────────────────────────────

describe("trackEvent — error handling (non-blocking)", () => {
  it("NO debe lanzar error si fetch falla (fire-and-forget)", async () => {
    mockFetch.mockRejectedValueOnce(new Error("Network error"));

    await expect(
      trackEvent(TrackEventType.REMINDER_SENT, { appointment_id_hash: "hash-789" }, AUTH),
    ).resolves.not.toThrow();
  });

  it("NO debe lanzar error si la respuesta es 4xx", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 422,
      statusText: "Unprocessable Entity",
      json: async () => ({}),
    } as Response);

    await expect(
      trackEvent(TrackEventType.CHARGE_FAILED, { error_bucket: "payment_declined" }, AUTH),
    ).resolves.not.toThrow();
  });

  it("NO debe lanzar error si la respuesta es 5xx", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      statusText: "Internal Server Error",
      json: async () => ({}),
    } as Response);

    await expect(
      trackEvent(TrackEventType.AGENDA_VIEWED, { view_mode: "mes" }, AUTH),
    ).resolves.not.toThrow();
  });
});

// ── 6. trackEvent returns void (fire-and-forget) ───────────────────────────────

describe("trackEvent — return type", () => {
  it("debe retornar Promise<void>", async () => {
    const result = await trackEvent(TrackEventType.AGENDA_VIEWED, {}, AUTH);
    expect(result).toBeUndefined();
  });
});
