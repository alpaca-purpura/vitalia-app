// cap: crm.adrian-embudo
// story-origin: vitalia-fase2-adrian-embudo
/**
 * embudo.ts — MSW handlers for Embudo API endpoints.
 * T-FE-2 vitalia-fase2-adrian-embudo
 *
 * Includes:
 *   - GET /api/v1/crm/board — board with dataset canónico (§spec 11 leads dental PEN)
 *   - PATCH /api/v1/crm/leads/:id/stage — 200/409/422 variants
 *   - GET /api/v1/crm/frozen — frozen leads list
 *   - POST /api/v1/crm/leads/:id/reservado-side-effect — stub (RN-5)
 *
 * PHI-safe mock data: no real names/emails/phones.
 * Spanish neutro LatAm names.
 * Dataset canónico from 01-spec.md § Dataset canónico (PEN, dental vitalia).
 *
 * downstream-regression-na: brand-local vitalia FE mocks
 * spec_anchor: 03-arch-fe.md § MSW
 */
import { http, HttpResponse, delay } from "msw";
import type { BoardResponse, FrozenListResponse, LeadCardDTO } from "../../features/adrian/types/embudo.types";

const BASE = "http://localhost:8002";
const CRM = `${BASE}/api/v1/crm`;

// ── Mock dataset canónico (§ spec — 11 leads dental PEN + 2 frozen) ──────────

const NOW = "2026-06-03T10:00:00Z";

const makeLead = (
  id: string,
  name: string,
  stage: LeadCardDTO["stage"],
  score: number,
  temperature: LeadCardDTO["temperature"],
  channel: string,
  value: number,
  signals: string[],
  stageEnteredAt: string,
  operatedBy: "agent" | "human" = "agent",
  depositStatus: LeadCardDTO["depositStatus"] = null,
): LeadCardDTO => ({
  id,
  tenantId: "e69a691d-070e-5caf-a053-6e74642ec100",
  name,
  stage,
  stageEnteredAt,
  score,
  temperature,
  operatedBy,
  channel,
  estimatedValue: value,
  currency: "PEN",
  buyingSignals: signals,
  isFrozen: false,
  frozenReason: null,
  depositStatus,
  closureReason: null,
  reactivationCohortAt: null,
  serviceInterest: "Ortodoncia",
  assignedDoctorId: null,
  version: 1,
  isBlacklisted: false,
  lastActivityDescription: "Adrián saludó",
  lastActivityAt: NOW,
});

// Dataset canónico §spec
const LEADS: LeadCardDTO[] = [
  makeLead("lead-001", "María G███", "interesado", 48, "warm", "whatsapp", 7000, ["pregunto_precio"], "2026-06-01T10:00:00Z"),
  makeLead("lead-002", "Carlos P███", "interesado", 33, "cold", "instagram", 4000, [], "2026-05-25T10:00:00Z"),
  makeLead("lead-003", "Sofía R███", "interesado", 41, "warm", "meta", 12000, ["pregunto_precio"], "2026-05-29T10:00:00Z"),
  makeLead("lead-004", "Ana V███", "calificando", 64, "warm", "whatsapp", 8000, ["urgencia", "presupuesto_ok"], "2026-06-03T09:00:00Z"),
  makeLead("lead-005", "Pedro M███", "calificando", 52, "warm", "whatsapp", 6000, [], "2026-06-03T02:00:00Z", "human"),
  makeLead("lead-006", "JP Méndez███", "consulta_agendada", 71, "hot", "whatsapp", 11000, [], "2026-06-02T10:00:00Z"),
  makeLead("lead-007", "Rosa V███", "plan_presentado", 78, "hot", "referido", 12000, [], "2026-05-11T10:00:00Z"),
  makeLead("lead-008", "Camila B███", "reservado", 0, null, "whatsapp", 8000, [], "2026-05-30T10:00:00Z", "agent", "received"),
  makeLead("lead-009", "Mateo L███", "reservado", 0, null, "web", 7000, [], "2026-05-31T10:00:00Z", "agent", "pending"),
];

const MOCK_BOARD: BoardResponse = {
  columns: [
    {
      stage: "interesado",
      label: "Interesado",
      count: 3,
      sumValue: 23000,
      currency: "PEN",
      overSlaCount: 1,
      leads: LEADS.filter((l) => l.stage === "interesado"),
    },
    {
      stage: "calificando",
      label: "Calificando",
      count: 2,
      sumValue: 14000,
      currency: "PEN",
      overSlaCount: 0,
      leads: LEADS.filter((l) => l.stage === "calificando"),
    },
    {
      stage: "consulta_agendada",
      label: "Consulta agendada",
      count: 1,
      sumValue: 11000,
      currency: "PEN",
      overSlaCount: 0,
      leads: LEADS.filter((l) => l.stage === "consulta_agendada"),
    },
    {
      stage: "plan_presentado",
      label: "Plan presentado",
      count: 1,
      sumValue: 12000,
      currency: "PEN",
      overSlaCount: 1,
      leads: LEADS.filter((l) => l.stage === "plan_presentado"),
    },
    {
      stage: "reservado",
      label: "Reservado",
      count: 2,
      sumValue: 15000,
      currency: "PEN",
      overSlaCount: 0,
      leads: LEADS.filter((l) => l.stage === "reservado"),
    },
  ],
  kpis: {
    totalActive: 9,
    adrianCount: 8,
    humanCount: 1,
    hotCount: 2,
    warmCount: 5,
    coldCount: 2,
    avgScore: 56,
    depositRate: 0.18,
    frozenCount: 2,
  },
};

// ── Frozen dataset ────────────────────────────────────────────────────────────

const MOCK_FROZEN: FrozenListResponse = {
  recienCongelados: [
    {
      id: "lead-010",
      tenantId: "e69a691d-070e-5caf-a053-6e74642ec100",
      name: "Lucía R███",
      lastStage: "calificando",
      frozenReason: "inactividad_lead",
      frozenAt: "2026-05-28T10:00:00Z",
      channel: "whatsapp",
      score: 32,
      closureReason: null,
      reactivationCohortAt: null,
    },
    {
      id: "lead-011",
      tenantId: "e69a691d-070e-5caf-a053-6e74642ec100",
      name: "Diego F███",
      lastStage: "plan_presentado",
      frozenReason: "sin_respuesta_presupuesto",
      frozenAt: "2026-05-20T10:00:00Z",
      channel: "meta",
      score: 55,
      closureReason: null,
      reactivationCohortAt: null,
    },
  ],
  decidioNo: [
    {
      id: "lead-012",
      tenantId: "e69a691d-070e-5caf-a053-6e74642ec100",
      name: "Iván S███",
      lastStage: "plan_presentado",
      frozenReason: null,
      frozenAt: null,
      channel: null,
      score: null,
      closureReason: "precio",
      reactivationCohortAt: "2026-08-28T10:00:00Z",
    },
  ],
};

// ── MSW Handlers ──────────────────────────────────────────────────────────────

export const embudoHandlers = [
  // GET /board
  http.get(`${CRM}/board`, async () => {
    await delay(80);
    return HttpResponse.json(MOCK_BOARD);
  }),

  // GET /frozen
  http.get(`${CRM}/frozen`, async () => {
    await delay(80);
    return HttpResponse.json(MOCK_FROZEN);
  }),

  // PATCH /leads/:id/stage — normal 200
  http.patch(`${CRM}/leads/:id/stage`, async ({ request, params }) => {
    await delay(120);
    const body = (await request.json()) as {
      to_stage: string;
      version: number;
      reason?: string | null;
    };
    const leadId = params.id as string;

    // Simulate 409 for specific test lead
    if (leadId === "lead-conflict-409") {
      return HttpResponse.json(
        { detail: "Conflicto de versión. El lead fue actualizado por otra persona." },
        { status: 409 },
      );
    }

    // Simulate 422 for reservado jump
    if (body.to_stage === "reservado") {
      return HttpResponse.json(
        { detail: "No se puede pasar directamente a Reservado.", allowed_next: ["consulta_agendada", "decidio_no"] },
        { status: 422 },
      );
    }

    const lead = LEADS.find((l) => l.id === leadId);
    return HttpResponse.json({
      lead: { ...(lead ?? LEADS[0]), stage: body.to_stage, version: (body.version ?? 1) + 1 },
      transition: {
        id: `trans-${Date.now()}`,
        fromStage: lead?.stage ?? "interesado",
        toStage: body.to_stage,
        triggeredBy: "manual_override",
        reason: body.reason ?? null,
        occurredAt: NOW,
        actorUserId: null,
      },
    });
  }),

  // POST /leads/:id/reservado-side-effect (STUB — RN-5)
  http.post(`${CRM}/leads/:id/reservado-side-effect`, async ({ params }) => {
    await delay(100);
    const leadId = params.id as string;
    const lead = LEADS.find((l) => l.id === leadId);
    return HttpResponse.json({
      ...(lead ?? LEADS[0]),
      depositStatus: "pending",
    });
  }),


  // GET /leads/:id/detail (T-FE-3 — LeadWorkspace/ResumenView)
  http.get(`${CRM}/leads/:id/detail`, async ({ params }) => {
    await delay(80);
    const leadId = params.id as string;
    const lead = LEADS.find((l) => l.id === leadId);
    if (!lead) {
      return HttpResponse.json({ detail: "Lead no encontrado" }, { status: 404 });
    }
    return HttpResponse.json({
      lead,
      scoreBreakdown: [
        { label: "Preguntó precio", delta: 25, icon: null },
        { label: "Respondió rápido", delta: 15, icon: null },
        { label: "Campaña pagada", delta: 10, icon: null },
        { label: "Sin agendar 2d", delta: -2, icon: null },
      ],
      autonomy: {
        canDo: ["mover etapa", "agendar", "enviar info"],
        needsApproval: ["cobrar", "descuentos", "clínico"],
        currentMode: "autonomous",
      },
    });
  }),

  // GET /leads/:id/transitions (T-FE-3 — HistorialView)
  http.get(`${CRM}/leads/:id/transitions`, async ({ params }) => {
    await delay(80);
    const leadId = params.id as string;
    const lead = LEADS.find((l) => l.id === leadId);
    if (!lead) {
      return HttpResponse.json({ detail: "Lead no encontrado" }, { status: 404 });
    }
    return HttpResponse.json({
      events: [
        {
          id: "ev-001",
          kind: "stage_move",
          actor: "agent",
          descriptionEs: `Adrián movió a ${lead.stage}`,
          occurredAt: lead.stageEnteredAt ?? NOW,
        },
        {
          id: "ev-002",
          kind: "message",
          actor: "lead",
          descriptionEs: "Preguntó por el precio del tratamiento",
          occurredAt: "2026-06-02T10:00:00Z",
        },
        {
          id: "ev-003",
          kind: "info_sent",
          actor: "agent",
          descriptionEs: "Adrián envió información del tratamiento",
          occurredAt: "2026-06-02T10:05:00Z",
        },
      ],
    });
  }),

  // POST /leads/:id/diagnose (T-FE-3 — RecuperarView)
  http.post(`${CRM}/leads/:id/diagnose`, async ({ params }) => {
    await delay(200);
    const leadId = params.id as string;
    return HttpResponse.json({
      leadId,
      recommendation: "El lead mostró interés pero no respondió al presupuesto. Sugerimos ofrecer una opción de financiación.",
      urgency: "medium" as const,
      suggestedAction: "Enviar link de financiación + testimonios de pacientes",
    });
  }),

  // POST /leads/:id/reactivate (T-FE-3 — RecuperarView)
  http.post(`${CRM}/leads/:id/reactivate`, async ({ params }) => {
    await delay(150);
    const leadId = params.id as string;
    const frozenLead = [
      ...MOCK_FROZEN.recienCongelados,
      ...MOCK_FROZEN.decidioNo,
    ].find((l) => l.id === leadId);
    return HttpResponse.json({
      id: leadId,
      tenantId: "e69a691d-070e-5caf-a053-6e74642ec100",
      name: frozenLead?.name ?? "Lead R███",
      stage: frozenLead?.lastStage ?? "calificando",
      isFrozen: false,
      frozenReason: null,
      score: frozenLead?.score ?? 30,
      version: 2,
    });
  }),

  // POST /leads (create — for use-create-lead T-FE-3)

  http.post(`${CRM}/leads`, async ({ request }) => {
    await delay(150);
    const body = (await request.json()) as { name?: string; channel?: string };
    return HttpResponse.json(
      {
        id: `lead-new-${Date.now()}`,
        tenantId: "e69a691d-070e-5caf-a053-6e74642ec100",
        name: body.name ?? "Nuevo Lead",
        stage: "interesado",
        score: 10,
        temperature: "cold",
        operatedBy: "agent",
        channel: body.channel ?? "web",
        estimatedValue: null,
        currency: "PEN",
        buyingSignals: [],
        isFrozen: false,
        frozenReason: null,
        depositStatus: null,
        version: 1,
        stageEnteredAt: NOW,
      },
      { status: 201 },
    );
  }),
];
