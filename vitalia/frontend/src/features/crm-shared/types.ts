// cap: crm.adrian-embudo
// story-origin: vitalia-fase2-adrian-embudo
/**
 * crm-shared/types.ts — Shared CRM type contracts (PRODUCER · Ola 1+).
 *
 * T-FE-1 vitalia-fase2-adrian-embudo (2026-06-03): EXTEND Lead with funnel fields.
 *   + LeadFunnelStage (6-stage dental funnel, replaces flat LeadStage for embudo)
 *   + LeadTemperature, LeadOperatedBy, BuyingSignal, DepositStatus types
 *   + Lead interface extended with stage/score/temperature/operatedBy/channel/...
 *   + Lead.stage is now the funnel stage (camelCase mirror of BE LeadResponse)
 *
 * Consumed by: features/adrian/embudo · features/crm-shared (existing inbox hooks).
 * camelCase per 03-arch-fe.md § 5 (mirrors Pydantic DTOs, ISO 8601 as string).
 * PHI fields: name, phone, email. Funnel fields = plaintext NO-PHI.
 *
 * HIPAA-lite: all PHI fields MUST be rendered via <PiiMaskedSpan>.
 * FE never stores PHI in localStorage/sessionStorage.
 * Lead is non-PHI (marketing prospect) — single tenant_id filter, no clinic_id required for funnel.
 *
 * downstream-regression-na: brand-local FE types; no cross-brand consumers.
 */

/**
 * LeadFunnelStage — 6-stage dental funnel (vitalia-local, brand-vertical specific).
 * Mirrors Pydantic `stage` field in LeadResponse (camelCase rename from snake_case values).
 * Values match BE domain/funnel_machine.py STAGE_MACHINE keys.
 */
export type LeadFunnelStage =
  | "interesado"
  | "calificando"
  | "consulta_agendada"
  | "plan_presentado"
  | "reservado"
  | "decidio_no";

/**
 * LeadStage — legacy CRM stage enum (inbox back-compat).
 * Mirrors Pydantic LeadStage enum as it existed pre-embudo.
 * Used by ConversationItem, InboxConvList and other inbox consumers.
 * NOT extended with funnel stages to preserve exhaustive Record<LeadStage, ...> usages.
 * For the new 6-stage dental funnel, use `LeadFunnelStage` directly.
 */
export type LeadStage =
  | "interesado"
  | "calificando"
  | "considerando"
  | "listo"
  | "reservado_deposito"
  | "decidio_no";

/** Lead attribution source */
export type LeadOrigin =
  | "sales_agent"
  | "walk_in"
  | "phone_manual"
  | "proactive_outbound";

// ── Funnel field types (T-FE-1 vitalia-fase2-adrian-embudo) ─────────────────

/** Lead temperature classification from glass-box scorer. */
export type LeadTemperature = "hot" | "warm" | "cold";

/**
 * Who currently operates this lead's conversation.
 * Mirrors BE `operated_by` field (agent | human).
 */
export type LeadOperatedBy = "agent" | "human";

/**
 * Buying signal detected by Adrián (sales agent).
 * Subset of intent signals; open-ended string for extensibility.
 */
export type BuyingSignal =
  | "pregunto_precio"
  | "urgencia"
  | "presupuesto_ok"
  | "agenda_solicitada"
  | string;

/**
 * Deposit payment status (stub MSW in this story; real via payment-adapter-mvp).
 * Mirrors BE `deposit_status` field.
 */
export type DepositStatus = "pending" | "received";

/**
 * Freeze reason code — why a lead was moved to Recuperar.
 * Mirrors BE `frozen_reason` field values.
 */
export type FrozenReason =
  | "inactividad_lead"
  | "sin_respuesta_presupuesto"
  | "agente_trabado"
  | string;

/**
 * Lead — mirrors Pydantic LeadResponse (EXTENDED with funnel fields, T-FE-1).
 *
 * PHI fields: name, phone, email (wrap with PiiMaskedSpan + RequireRole).
 * Non-PHI funnel fields: stage, score, temperature, channel, etc. — plaintext.
 * Funnel Lead = marketing prospect; single tenant_id filter (no clinic_id required).
 *
 * Note: `clinic_id` is kept for back-compat with existing inbox hooks.
 * Funnel queries ONLY use tenant_id (Lead is non-PHI per hipaa-lite.md).
 */
export interface Lead {
  id: string;
  /** Tenant scope — used by fetchClient X-Tenant-ID auto-injection */
  tenant_id: string;
  /**
   * Clinic scope — HIPAA-lite dual filter (vitalia/.claude/rules/hipaa-lite.md).
   * Present for inbox back-compat; funnel queries use tenant_id only.
   */
  clinic_id: string;
  /** PHI: patient full name — MUST use <PiiMaskedSpan kind="name"> */
  name: string;
  /** PHI: patient phone — MUST use <PiiMaskedSpan kind="phone"> */
  phone: string | null;
  /** PHI: patient email — MUST use <PiiMaskedSpan kind="email"> */
  email: string | null;
  /**
   * Public profile picture URL from the messaging channel (WhatsApp/Instagram).
   * FE renders it as the contact "thumbnail"; falls back to a monogram when null.
   * TODO(BE): the inbox API does not populate this yet — the FE asks for it so the
   * wiring is ready the moment the BE exposes it (UI-AUDIT-2 #1).
   */
  avatar_url?: string | null;
  /** Current CRM stage (legacy flat stage for inbox back-compat) */
  stage: LeadStage;
  /** How lead entered the system */
  attribution: {
    origin: LeadOrigin;
    channel: string | null;
    attributed_at: string;
  };
  /** FK → vitalia_conversations.id (most recent) */
  last_conversation_id: string | null;
  created_at: string;
  updated_at: string;

  // ── Funnel fields (T-FE-1 — all optional for back-compat) ─────────────────

  /** ISO 8601 — when the lead entered its current stage. Used for time-in-stage SLA calc. */
  stage_entered_at?: string | null;

  /**
   * Glass-box score 0-100 (rule-based, no ML).
   * Computed server-side from recency + buying_signals + stage.
   */
  score?: number | null;

  /** Temperature classification derived from score + activity. */
  temperature?: LeadTemperature | null;

  /** Who currently operates this lead's conversation. */
  operated_by?: LeadOperatedBy | null;

  /**
   * Origin channel slug (e.g. "whatsapp", "instagram", "meta", "referido").
   * Consumed by ChannelBadge.
   */
  channel?: string | null;

  /** Service of interest (e.g. "Ortodoncia", "Blanqueamiento"). */
  service_interest?: string | null;

  /** FK → vitalia_staff.id (assigned doctor) */
  assigned_doctor_id?: string | null;

  /** Estimated deal value. Use formatMoney(value, currency). */
  estimated_value?: number | null;

  /**
   * Currency code (ISO 4217 — e.g. "PEN", "MXN", "COP").
   * Always included when estimated_value is set. NEVER hardcode "USD".
   * Fallback: useTenantLocale().currency (master-data.md).
   */
  currency?: string | null;

  /** Buying signals detected by Adrián during the conversation. */
  buying_signals?: BuyingSignal[];

  /** Whether the lead is frozen (in Recuperar view). */
  is_frozen?: boolean;

  /** Reason for freeze (set by auto-freeze rule or agent). */
  frozen_reason?: FrozenReason | null;

  /** ISO 8601 — when the lead was frozen. */
  frozen_at?: string | null;

  /** Reason for closing the lead (Decidió no). */
  closure_reason?: string | null;

  /** ISO 8601 — when Camila's 90-day reactivation cohort starts. */
  reactivation_cohort_at?: string | null;

  /**
   * Payment deposit status (stub MSW in this story).
   * Real value comes from payment-adapter-mvp webhook (RN-5).
   */
  deposit_status?: DepositStatus | null;

  /**
   * Optimistic lock version counter (positive integer).
   * Required for PATCH /stage to prevent concurrent override conflicts (SC-5).
   */
  version?: number;

  /** Blacklisted leads are excluded from all views including Recuperar. */
  is_blacklisted?: boolean;
}

/** Supported conversation channels */
export type ConversationChannel =
  | "whatsapp"
  | "instagram"
  | "facebook_messenger"
  | "web"
  | "walk_in"
  | "phone";

/** Conversation lifecycle status */
export type ConversationStatus = "active" | "paused" | "closed" | "archived";

/** Handler mode — who controls message sending */
export type HandlerMode = "ai" | "human";

/**
 * Conversation — mirrors Pydantic ConversationResponse.
 * Dual-filter enforced server-side: tenant_id + clinic_id.
 */
export interface Conversation {
  id: string;
  lead_id: string;
  /** Tenant scope */
  tenant_id: string;
  /** Clinic scope — HIPAA-lite dual filter */
  clinic_id: string;
  /** PHI: patient UUID (only ID, not name) — no PHI wrap needed */
  patient_id: string | null;
  channel: ConversationChannel;
  status: ConversationStatus;
  /** Current agent mode — drives SegmentedControl3Modes UI */
  handler_mode: HandlerMode;
  /** Adrián is waiting for operator to review proposal */
  proposal_required: boolean;
  /** ISO 8601 — Adrián paused until this time */
  pause_until: string | null;
  /** Operator help requested flag — 🔴 indicator in list */
  help_needed: boolean;
  help_needed_reason: string | null;
  /** Count for 📎 indicator in conversation list */
  unread_media_count: number;
  last_message_at: string;
  /** Preview shown in conversation list item */
  last_message_preview: string | null;
  messages_count: number;
  /** Adrián's stage recommendation */
  stage_decision: LeadStage | null;
  /** FK → offers.id (linked offer for context) */
  linked_offer_id: string | null;
  /** ISO 8601 — used as ETag for OCC (If-Match header) */
  updated_at: string;
}
