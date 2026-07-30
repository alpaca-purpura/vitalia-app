// cap: public_landing.public-clinic-landing
// story-origin: TBD
import type { Meta, StoryObj } from "@storybook/nextjs";
import { LucasApprovalModal } from "./LucasApprovalModal";
import type { LucasRecommendation } from "../types/lucas-recommendation";

/**
 * LucasApprovalModal — confirmation dialog before approving a Lucas recommendation.
 * SC-MK-01: approve → receipt + undo chip countdown.
 * SC-MK-04: recepcion role disabled + tooltip.
 * Two phases: "confirm" (review) → "approved" (receipt).
 */
const meta: Meta<typeof LucasApprovalModal> = {
  title: "Marketing/LucasApprovalModal",
  component: LucasApprovalModal,
  tags: ["autodocs"],
  parameters: {
    backgrounds: { default: "vitalia-bg" },
    layout: "fullscreen",
  },
  args: {
    onClose: () => {},
  },
};
export default meta;

type Story = StoryObj<typeof LucasApprovalModal>;

const mockRec: LucasRecommendation = {
  id: "rec-001",
  tenantId: "tenant-vitalia",
  clinicId: "clinic-001",
  stage: "attraction",
  recommendationKind: "increase_budget",
  title: "Aumentar presupuesto Meta Ads en 20%",
  body: "Los últimos 7 días muestran un CPL 18% por debajo del objetivo. Aumentar presupuesto maximizará el volumen de leads en la ventana de mayor conversión.",
  rationaleJson: {
    cpl_actual: "S/ 24",
    cpl_objetivo: "S/ 30",
    variacion: "-18%",
    recomendacion: "Aumentar budget 20%",
  },
  actionPayloadJson: {
    provider: "meta_ads",
    change_type: "budget_increase",
    percent: 20,
  },
  priority: 1,
  confidencePct: 87,
  projectedImpactText: "+14 leads estimados / semana",
  status: "open",
  approvedByUserId: null,
  approvedAt: null,
  undoUntil: null,
  expiresAt: new Date(Date.now() + 7 * 24 * 3600_000).toISOString(),
  createdAt: new Date(Date.now() - 2 * 3600_000).toISOString(),
};

/** Fase de revisión (confirm) — estado inicial del modal */
export const Review: Story = {
  args: {
    rec: mockRec,
    userRole: "admin_clinic",
  },
  name: "Fase 1 — Revisión (confirm)",
};

/** Rol recepcion — botón Aprobar deshabilitado */
export const RecepcionDenied: Story = {
  args: {
    rec: mockRec,
    userRole: "recepcion",
  },
  name: "Recepción — sin permiso para aprobar (SC-MK-04)",
};

/** Recomendación de baja prioridad con métricas parciales */
export const LowPriorityRec: Story = {
  args: {
    rec: {
      ...mockRec,
      id: "rec-005",
      priority: 5,
      title: "Revisar keywords negativas en Google Ads",
      confidencePct: null,
      projectedImpactText: null,
      actionPayloadJson: null,
    },
    userRole: "doctor",
  },
  name: "Rec sin métricas de impacto",
};
