// cap: patients.nps-tracking
// story-origin: TBD
/**
 * ReEngagementCard — Storybook stories.
 *
 * Covers:
 *   - All 4 pattern variants (multi_session, follow_up, maintenance, absence)
 *   - All 5 urgency levels (critical, alert, near, waiting, up_to_date)
 *   - Actions enabled vs disabled
 *   - Absence card with marketing opt-out warning
 *
 * useCurrentUser + useTenantLocale use Clerk's `useUser`/`useOrganization`,
 * which in Storybook (@storybook/nextjs) gracefully return empty/undefined
 * and the hooks fall back to vitalia defaults (ARS / Buenos Aires).
 *
 * downstream-regression-na: vitalia-local Storybook artifact — no cross-brand consumers.
 */

import type { Meta, StoryObj } from "@storybook/nextjs";
import { fn } from "storybook/test";
import { ReEngagementCard } from "./ReEngagementCard";
import type { PatternRow, AbsenceData } from "../types/re-engagement";

// ──────────────────────────────────────────────────────────────────────────────
// Fixture helpers
// ──────────────────────────────────────────────────────────────────────────────

const ALL_ACTIONS_ENABLED = (): PatternRow["acciones"] => [
  { id: "send_reminder", enabled: true, disabledReason: null },
  { id: "suggest_slots", enabled: true, disabledReason: null },
  { id: "pause_patient", enabled: true, disabledReason: null },
  { id: "open_conversation", enabled: true, disabledReason: null },
  { id: "call_manually", enabled: true, disabledReason: null },
];

const MULTI_SESSION_ROW: PatternRow = {
  reEngagementEventId: "evt-ms-1",
  patientId: "pat-001",
  patientName: "María González",
  pattern: "multi_session",
  urgency: "alert",
  patternData: {
    kind: "multi_session",
    offerLabel: "Pack Kinesiología 10 sesiones",
    sessionsCompleted: 4,
    sessionsExpected: 10,
    gapDays: 18,
    lastSessionDate: "2025-04-20T10:00:00-03:00",
    doctorName: "Rodríguez",
  },
  acciones: ALL_ACTIONS_ENABLED(),
};

const FOLLOW_UP_ROW: PatternRow = {
  reEngagementEventId: "evt-fu-1",
  patientId: "pat-002",
  patientName: "Carlos Pereira",
  pattern: "follow_up",
  urgency: "critical",
  patternData: {
    kind: "follow_up",
    doctorName: "García",
    followUpRequestedDuration: "3 meses",
    followUpSetAt: "2025-02-01T00:00:00-03:00",
    followUpDueAt: "2025-05-01T00:00:00-03:00",
    daysUntilDue: -12,
    followUpReason: "Control post-operatorio rodilla",
  },
  acciones: ALL_ACTIONS_ENABLED(),
};

const MAINTENANCE_ROW: PatternRow = {
  reEngagementEventId: "evt-mt-1",
  patientId: "pat-003",
  patientName: "Ana Sánchez",
  pattern: "maintenance",
  urgency: "near",
  patternData: {
    kind: "maintenance",
    offerLabel: "Limpieza dental profunda",
    cadenceLabel: "Cada 6 meses",
    lastServiceDate: "2024-11-15T09:00:00-03:00",
    monthsSinceLast: 6,
    nextRecommendedDate: "2025-05-15T09:00:00-03:00",
    daysUntilDue: 8,
  },
  acciones: ALL_ACTIONS_ENABLED(),
};

const ABSENCE_ROW: PatternRow = {
  reEngagementEventId: "evt-ab-1",
  patientId: "pat-004",
  patientName: "Roberto Méndez",
  pattern: "absence",
  urgency: "waiting",
  patternData: {
    kind: "absence",
    lastAppointmentDate: "2024-09-10T11:00:00-03:00",
    monthsInactive: 8,
    lifetimeAppointments: 23,
    lifetimeValueCents: 145000,
    currency: "ARS",
    lastDoctorName: "Fernández",
    marketingOptIn: true,
  },
  acciones: ALL_ACTIONS_ENABLED(),
};

const HANDLERS = {
  onSendReminder: fn(),
  onSuggestSlots: fn(),
  onPause: fn(),
  onMarkExternal: fn(),
  onMarkNoContinue: fn(),
  onLogManualCall: fn(),
  onOpenConversation: fn(),
};

const meta: Meta<typeof ReEngagementCard> = {
  title: "Features/Fidelizacion/ReEngagementCard",
  component: ReEngagementCard,
  tags: ["autodocs"],
  parameters: {
    backgrounds: { default: "vitalia-bg" },
    layout: "padded",
    nextjs: { appDirectory: true },
  },
  args: { ...HANDLERS },
  argTypes: {
    row: { control: false },
    className: { control: false },
    onSendReminder: { action: "sendReminder" },
    onSuggestSlots: { action: "suggestSlots" },
    onPause: { action: "pause" },
    onMarkExternal: { action: "markExternal" },
    onMarkNoContinue: { action: "markNoContinue" },
    onLogManualCall: { action: "logManualCall" },
    onOpenConversation: { action: "openConversation" },
  },
};

export default meta;

type Story = StoryObj<typeof ReEngagementCard>;

// ──────────────────────────────────────────────────────────────────────────────
// Pattern variants
// ──────────────────────────────────────────────────────────────────────────────

/** Patrón multisesión — urgencia alerta */
export const MultiSession: Story = {
  name: "Multisesión (alerta)",
  args: { row: MULTI_SESSION_ROW },
};

/** Patrón seguimiento — urgencia crítica, vencido hace 12 días */
export const FollowUp: Story = {
  name: "Seguimiento médico (crítico, vencido)",
  args: { row: FOLLOW_UP_ROW },
};

/** Patrón mantenimiento — próximo en 8 días */
export const Maintenance: Story = {
  name: "Mantenimiento (próximo)",
  args: { row: MAINTENANCE_ROW },
};

/** Patrón ausencia — en espera */
export const Absence: Story = {
  name: "Ausencia (en espera)",
  args: { row: ABSENCE_ROW },
};

// ──────────────────────────────────────────────────────────────────────────────
// Urgency levels showcase
// ──────────────────────────────────────────────────────────────────────────────

/** Urgencia crítica — borde rojo */
export const UrgencyCritical: Story = {
  name: "Urgencia: crítica",
  args: {
    row: {
      ...MULTI_SESSION_ROW,
      urgency: "critical",
      reEngagementEventId: "evt-critical",
    },
  },
};

/** Urgencia al día — borde verde */
export const UrgencyUpToDate: Story = {
  name: "Urgencia: al día",
  args: {
    row: {
      ...MULTI_SESSION_ROW,
      urgency: "up_to_date",
      reEngagementEventId: "evt-uptodate",
    },
  },
};

// ──────────────────────────────────────────────────────────────────────────────
// Acciones deshabilitadas — sin marketing opt-in
// ──────────────────────────────────────────────────────────────────────────────

/** Ausencia sin consentimiento marketing — acción enviar deshabilitada */
export const AbsenceNoMarketing: Story = {
  name: "Ausencia: sin marketing opt-in",
  args: {
    row: {
      ...ABSENCE_ROW,
      patternData: {
        ...(ABSENCE_ROW.patternData as AbsenceData),
        marketingOptIn: false,
      },
      acciones: [
        {
          id: "send_reminder",
          enabled: false,
          disabledReason: "Paciente no aceptó comunicaciones de marketing",
        },
        { id: "suggest_slots", enabled: true, disabledReason: null },
        { id: "pause_patient", enabled: true, disabledReason: null },
        { id: "open_conversation", enabled: true, disabledReason: null },
        { id: "call_manually", enabled: true, disabledReason: null },
      ],
      reEngagementEventId: "evt-no-marketing",
    } satisfies PatternRow,
  },
};
