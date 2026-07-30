// cap: public_landing.public-clinic-landing
// story-origin: TBD
import type { Meta, StoryObj } from "@storybook/nextjs";
import { LucasRecommendationDetailModal } from "./LucasRecommendationDetailModal";
import type { LucasRecommendation } from "../types/lucas-recommendation";

/**
 * LucasRecommendationDetailModal — full-detail view of a Lucas recommendation.
 * SC-MK-01: click card → detail modal.
 * States: open (status=open) · approved (status=approved) · denied 403 (recepcion role).
 */
const meta: Meta<typeof LucasRecommendationDetailModal> = {
  title: "Marketing/LucasRecommendationDetailModal",
  component: LucasRecommendationDetailModal,
  tags: ["autodocs"],
  parameters: {
    backgrounds: { default: "vitalia-bg" },
    layout: "fullscreen",
  },
  args: {
    onClose: () => {},
    onApprove: () => {},
    onReject: () => {},
  },
};
export default meta;

type Story = StoryObj<typeof LucasRecommendationDetailModal>;

const openRec: LucasRecommendation = {
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
    periodo: "7 días",
    tendencia: "positiva",
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

const approvedRec: LucasRecommendation = {
  ...openRec,
  id: "rec-002",
  status: "approved",
  approvedByUserId: "user-admin-001",
  approvedAt: new Date(Date.now() - 10 * 60_000).toISOString(),
  undoUntil: new Date(Date.now() + 5 * 60_000).toISOString(),
};

const rejectedRec: LucasRecommendation = {
  ...openRec,
  id: "rec-003",
  status: "rejected",
  approvedByUserId: null,
  approvedAt: null,
  undoUntil: null,
};

const expiredRec: LucasRecommendation = {
  ...openRec,
  id: "rec-004",
  status: "expired",
};

/** Modal abierto con rec en estado open — Aprobar / Rechazar visibles */
export const Open: Story = {
  args: {
    rec: openRec,
    userRole: "admin_clinic",
  },
  name: "Estado open — acciones disponibles",
};

/** Recomendación ya aprobada — sin acciones, muestra audit trail */
export const Approved: Story = {
  args: {
    rec: approvedRec,
    userRole: "admin_clinic",
  },
  name: "Estado approved — solo lectura con audit",
};

/** Recomendación rechazada */
export const Rejected: Story = {
  args: {
    rec: rejectedRec,
    userRole: "admin_clinic",
  },
  name: "Estado rejected",
};

/** Recomendación expirada */
export const Expired: Story = {
  args: {
    rec: expiredRec,
    userRole: "admin_clinic",
  },
  name: "Estado expired",
};

/** RBAC: rol recepcion — botón Aprobar deshabilitado con tooltip */
export const RecepcionDenied: Story = {
  args: {
    rec: openRec,
    userRole: "recepcion",
  },
  name: "Recepción — sin permiso de aprobación (SC-MK-04)",
};

/** Sin rationale ni payload — muestra mensaje vacío */
export const NoAnalysisData: Story = {
  args: {
    rec: {
      ...openRec,
      id: "rec-005",
      rationaleJson: {},
      actionPayloadJson: null,
      confidencePct: null,
      projectedImpactText: null,
    },
    userRole: "doctor",
  },
  name: "Sin datos de análisis",
};
