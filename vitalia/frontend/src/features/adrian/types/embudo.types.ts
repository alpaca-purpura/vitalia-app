// cap: crm.adrian-embudo
// story-origin: vitalia-fase2-adrian-embudo
/**
 * embudo.types.ts — TypeScript type contracts for Adrián Embudo (T-FE-2).
 *
 * camelCase mirror of Pydantic DTOs (03-arch-fe.md § 5).
 * ISO 8601 datetimes as string. Optional fields explicit.
 * Currency: NEVER hardcode 'USD'. Always string | null.
 *
 * Consumed by: AdrianEmbudoView, KanbanBoard, PipelineColumn, LeadCard,
 *              LeadsTable, EmbudoMetrics, hooks, store.
 *
 * downstream-regression-na: brand-local vitalia FE types; no cross-brand consumers
 * spec_anchor: 03-arch-fe.md § types + 03-arch.md § 5
 */

import type {
  Lead,
  LeadFunnelStage,
  LeadTemperature,
  BuyingSignal,
  FrozenReason,
} from "@/features/crm-shared/types";

export type { LeadFunnelStage, LeadTemperature, BuyingSignal, FrozenReason };

// ── Re-export Lead for convenience ────────────────────────────────────────────
export type { Lead };

// ── LeadCard DTO (projected from BE BoardColumn.leads) ────────────────────────

/**
 * LeadCardDTO — read-only projection of a Lead for the Kanban/List board.
 * Mirrors Pydantic LeadCardDTO (03-arch-be.md § 3).
 * PHI fields (name, phone, email) — wrap with PiiMaskedSpan at render time.
 */
export interface LeadCardDTO {
  id: string;
  tenantId: string;
  /** PHI: patient name — MUST use <PiiMaskedSpan kind="name"> */
  name: string;
  stage: LeadFunnelStage;
  /** ISO 8601 — when the lead entered its current stage */
  stageEnteredAt: string | null;
  score: number | null;
  temperature: LeadTemperature | null;
  operatedBy: "agent" | "human";
  channel: string | null;
  estimatedValue: number | null;
  /** ISO 4217 — NEVER hardcode 'USD'. Fallback: useTenantLocale().currency */
  currency: string | null;
  buyingSignals: BuyingSignal[];
  isFrozen: boolean;
  frozenReason: FrozenReason | null;
  depositStatus: "pending" | "received" | null;
  closureReason: string | null;
  reactivationCohortAt: string | null;
  serviceInterest: string | null;
  assignedDoctorId: string | null;
  /** Optimistic lock counter. Required for PATCH /stage (SC-5). */
  version: number;
  isBlacklisted: boolean;
  /** Last activity description (micro-log) */
  lastActivityDescription?: string | null;
  /** ISO 8601 — when last activity occurred */
  lastActivityAt?: string | null;
}

// ── KPIs ─────────────────────────────────────────────────────────────────────

/** KPI strip data (D.2 header) — mirrors Pydantic BoardKpis */
export interface BoardKpis {
  totalActive: number;
  adrianCount: number;
  humanCount: number;
  hotCount: number;
  warmCount: number;
  coldCount: number;
  avgScore: number;
  depositRate: number;
  frozenCount: number;
}

// ── BoardColumn ───────────────────────────────────────────────────────────────

/** A single column in the Kanban board */
export interface BoardColumn {
  stage: LeadFunnelStage;
  label: string;
  count: number;
  sumValue: number;
  /** ISO 4217 — NEVER hardcode 'USD' */
  currency: string | null;
  overSlaCount: number;
  leads: LeadCardDTO[];
}

// ── BoardResponse ─────────────────────────────────────────────────────────────

/** Full board API response — mirrors Pydantic BoardResponse */
export interface BoardResponse {
  columns: BoardColumn[];
  kpis: BoardKpis;
}

// ── StageTransitionPayload ────────────────────────────────────────────────────

/** Request payload for PATCH /crm/leads/{id}/stage */
export interface StageTransitionPayload {
  toStage: LeadFunnelStage;
  reason?: string | null;
  note?: string | null;
  version: number;
  triggeredBy?: "manual_override" | "agent" | "reactivation" | "auto_freeze";
}

// ── StageTransitionResponse ───────────────────────────────────────────────────

export interface TransitionDTO {
  id: string;
  fromStage: LeadFunnelStage | null;
  toStage: LeadFunnelStage;
  triggeredBy: string;
  reason: string | null;
  occurredAt: string;
  actorUserId: string | null;
}

export interface StageTransitionResponse {
  lead: LeadCardDTO;
  transition: TransitionDTO;
}

// ── LeadDetail ────────────────────────────────────────────────────────────────

/** Score breakdown factor (glass-box explanation) */
export interface ScoreFactor {
  label: string;
  delta: number; // positive = adds, negative = subtracts
  icon?: string | null;
}

/**
 * Autonomy info from the agent (RN-9).
 * Field names match the camelized BE `AutonomyInfo`
 * (crm/application/dto/lead_detail_dto.py :: operated_by/can/needs_ok).
 * Gated by test_fe_be_contract_parity.py so this never drifts again (HB-44).
 */
export interface AutonomyInfo {
  operatedBy: string;
  can: string[];
  needsOk: string[];
}

/**
 * LeadDetailLeadDTO — full lead data for the Resumen tab detail view.
 *
 * Mirrors BE `lead_dto.LeadResponse` (camelCase). Includes phone + email
 * (non-PHI marketing fields the sales rep needs to contact the lead).
 * LeadCardDTO (board projection) explicitly omits phone/email — the
 * contract-parity gate (test_fe_be_contract_parity.py) enforces FE⊆BE for
 * BOTH pairs independently.
 *
 * U2 fix (2026-06-04): replacing `LeadCardDTO` in LeadDetailResponse
 * with this mirror so ResumenView can show Nombre + Teléfono + Correo.
 * ContractPair(LeadResponse ↔ LeadDetailLeadDTO) registered in
 * vitalia/backend/tests/architecture/test_fe_be_contract_parity.py (U2/HB-44).
 */
export interface LeadDetailLeadDTO {
  id: string;
  tenantId: string;
  name: string;
  email: string | null;
  phone: string | null;
  source: string | null;
  status: string;
  createdAt: string; // ISO 8601
  stage: LeadFunnelStage;
  score: number | null;
  temperature: LeadTemperature | null;
  operatedBy: "agent" | "human";
  channel: string | null;
  estimatedValue: number | null;
  /** ISO 4217 — NEVER hardcode 'USD'. Fallback: useTenantLocale().currency */
  currency: string | null;
  serviceInterest: string | null;
  buyingSignals: BuyingSignal[];
  stageEnteredAt: string | null; // ISO 8601
  isFrozen: boolean;
  frozenReason: FrozenReason | null;
  depositStatus: "pending" | "received" | null;
  version: number;
  assignedDoctorId: string | null;
}

/** Full lead detail response (Resumen view) */
export interface LeadDetailResponse {
  /** U2: typed as LeadDetailLeadDTO (mirrors LeadResponse with email+phone) */
  lead: LeadDetailLeadDTO;
  scoreBreakdown: ScoreFactor[];
  autonomy: AutonomyInfo;
}

// ── Timeline ─────────────────────────────────────────────────────────────────

/** A single entry in the lead timeline (Historial view) */
export interface TimelineEntry {
  id: string;
  kind: "stage_move" | "message" | "info_sent" | "deposit" | "note" | "freeze" | "reactivation";
  actor: "agent" | "human" | "lead" | "system";
  descriptionEs: string;
  occurredAt: string; // ISO 8601
}

export interface TimelineResponse {
  events: TimelineEntry[];
}

// ── Frozen ────────────────────────────────────────────────────────────────────

export interface FrozenLeadDTO {
  id: string;
  tenantId: string;
  /** PHI: MUST use <PiiMaskedSpan> */
  name: string;
  lastStage: LeadFunnelStage;
  frozenReason: FrozenReason | null;
  frozenAt: string | null; // ISO 8601
  channel: string | null;
  score: number | null;
  closureReason: string | null;
  reactivationCohortAt: string | null;
}

export interface FrozenListResponse {
  recienCongelados: FrozenLeadDTO[];
  decidioNo: FrozenLeadDTO[];
}

export interface DiagnoseResponse {
  leadId: string;
  recommendation: string;
  urgency: "high" | "medium" | "low";
  suggestedAction: string;
}

// ── Board filters ─────────────────────────────────────────────────────────────

/** URL-stable filters for board RQ key (test_react_query_keys_convention) */
export interface BoardFilters {
  view?: "kanban" | "lista";
  sort?: "stage_age_desc" | "score_desc" | "value_desc" | "last_activity_desc";
  origin?: string | null;
  doctor?: string | null;
  stage?: LeadFunnelStage | null;
  search?: string | null;
  operatedBy?: "agent" | "human" | null;
  highlight?: string | null;
}
