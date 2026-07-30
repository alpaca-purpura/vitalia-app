// cap: public_landing.public-clinic-landing
// story-origin: TBD
/**
 * MARKETING_COPY — Spanish neutro LatAm (tuteo, no voseo)
 * All user-facing strings for the marketing feature.
 * downstream-regression-na: brand-local FE copy; no cross-brand consumers
 */

export const MARKETING_COPY = {
  /** Page title and navigation */
  pageTitle: "Marketing",
  pageSubtitle: "Visión integral de tu embudo y recomendaciones de Lucas",

  /** Bowtie funnel labels */
  bowtie: {
    title: "Embudo de conversión",
    periodLabel: "Período",
    overallConversion: "Conversión total",
    roiLabel: "ROI",
    ltvLabel: "LTV promedio",
    lastSync: "Última sincronización",
    neverSynced: "Sin sincronización aún",
    loadingMessage: "Cargando embudo...",
    emptyMessage: "No hay datos de embudo para este período.",
    errorMessage: "No se pudo cargar el embudo. Intenta de nuevo.",
  },

  /** Stage labels (bowtie tabs) */
  stages: {
    attraction: "Atracción",
    qualification: "Calificación",
    reservation: "Reserva",
    adoption: "Adopción",
    expansion: "Expansión",
  },

  /** Period selector */
  periods: {
    "7d": "Últimos 7 días",
    "30d": "Últimos 30 días",
    "90d": "Últimos 90 días",
  },

  /** Lucas recommendations */
  recommendations: {
    title: "Recomendaciones de Lucas",
    subtitle: "Acciones priorizadas para mejorar tu embudo",
    approveButton: "Aprobar",
    rejectButton: "Rechazar",
    undoButton: "Deshacer",
    undoTimerLabel: "Puedes deshacer hasta",
    emptyMessage: "No hay recomendaciones activas en este momento.",
    errorMessage: "No se pudieron cargar las recomendaciones.",
    loadingMessage: "Cargando recomendaciones...",
    approvalConfirmTitle: "¿Confirmas la aprobación?",
    approvalConfirmDescription:
      "Al aprobar, Lucas ejecutará esta acción en tu nombre.",
    approvalConfirmButton: "Sí, aprobar",
    approvalCancelButton: "Cancelar",
    approvedBadge: "Aprobada",
    rejectedBadge: "Rechazada",
    expiredBadge: "Expirada",
    undoneBadge: "Deshecha",
    confidenceLabel: "Confianza",
    priorityLabel: "Prioridad",
    impactLabel: "Impacto proyectado",
  },

  /** Reject reasons */
  rejectReasons: {
    not_priority: "No es prioridad ahora",
    already_doing: "Ya lo estamos haciendo",
    data_wrong: "Los datos son incorrectos",
    too_risky: "Es demasiado arriesgado",
    other: "Otro motivo",
  },

  /** Channel integrations */
  channels: {
    title: "Canales conectados",
    subtitle: "Estado de sincronización de tus plataformas de publicidad",
    syncButton: "Sincronizar ahora",
    connectButton: "Conectar canal",
    syncingLabel: "Sincronizando...",
    lastSyncLabel: "Última sincronización",
    lastSuccessLabel: "Último éxito",
    errorLabel: "Último error",
    disconnectedMessage:
      "Canal desconectado. Reconecta para ver datos actualizados.",
    idleStatus: "Sin actividad",
    runningStatus: "Sincronizando",
    errorStatus: "Error",
    disconnectedStatus: "Desconectado",
    providers: {
      meta_ads: "Meta Ads",
      google_ads: "Google Ads",
    },
    noMetrics: "No hay métricas disponibles para este período.",
    loadingMessage: "Cargando datos del canal...",
    errorMessage: "No se pudo cargar la información del canal.",
  },

  /** Attribution matrix */
  attribution: {
    title: "Matriz de atribución",
    subtitle: "Origen de tus leads y su conversión por etapa",
    originLabel: "Origen",
    totalLabel: "Total",
    leadsLabel: "Leads",
    qualifiedLabel: "Calificados",
    convListoLabel: "Conv. Listo",
    reservationsLabel: "Reservas",
    adoptionLabel: "Adopción",
    valueLabel: "Valor",
    origins: {
      sales_agent: "Agente de ventas",
      walk_in: "Visita directa",
      phone_manual: "Teléfono (manual)",
      proactive_outbound: "Outbound proactivo",
      total: "Total",
    },
    emptyMessage: "No hay datos de atribución para este período.",
    errorMessage: "No se pudo cargar la matriz de atribución.",
    loadingMessage: "Cargando atribución...",
  },

  /** Referrals */
  referrals: {
    title: "Referidos",
    subtitle: "Pacientes que recomiendan tu clínica",
    totalReferrals: "Total de referidos",
    convRateLabel: "Tasa de conversión",
    avgLtvLabel: "LTV promedio por referidor",
    topReferrersTitle: "Principales referidores",
    referralsCountLabel: "Referidos",
    totalValueLabel: "Valor generado",
    emptyMessage: "No hay datos de referidos para este período.",
    errorMessage: "No se pudieron cargar los referidos.",
    loadingMessage: "Cargando referidos...",
    /** HIPAA: never display patient name — only anonymized ID */
    referrerLabel: "Referidor (ID anónimo)",
  },

  /** Connection wizard */
  connectionWizard: {
    title: "Conectar canal de publicidad",
    subtitle: "Selecciona el canal que deseas integrar",
    authorizeButton: "Autorizar acceso",
    cancelButton: "Cancelar",
    successTitle: "¡Canal conectado!",
    successMessage: "Tu canal ha sido conectado correctamente.",
    errorTitle: "Error al conectar",
    errorMessage: "No se pudo conectar el canal. Intenta de nuevo.",
  },

  /** General UI */
  ui: {
    retry: "Reintentar",
    loading: "Cargando...",
    noData: "Sin datos",
    close: "Cerrar",
    cancel: "Cancelar",
    confirm: "Confirmar",
  },
} as const;
