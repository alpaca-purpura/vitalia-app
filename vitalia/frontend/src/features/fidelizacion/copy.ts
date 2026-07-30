// cap: patients.nps-tracking
// story-origin: TBD
/**
 * copy.ts — FIDELIZACION_COPY constants.
 *
 * Spanish neutro LatAm — tuteo (tú) only.
 * Per .claude/rules/spanish-text.md — see glosario voseo→neutro for full conversion table.
 *   - Tildes + ñ + apertura ¿/¡ correct
 *
 * All user-facing strings live here per test_no_hardcoded_strings.test.ts constraint.
 *
 * downstream-regression-na: brand-local FE copy; no cross-brand consumers
 */

export const FIDELIZACION_COPY = {
  page: {
    title: "Seguimiento y fidelización",
    description:
      "Gestiona el seguimiento activo de tus pacientes y las acciones de reactivación.",
    loadingText: "Cargando seguimiento...",
    errorText: "No pudimos cargar el seguimiento. Intenta de nuevo.",
    errorRetryButton: "Intentar de nuevo",
  },

  kpis: {
    patientsInFollowup: {
      label: "En seguimiento activo",
      ariaLabel: (n: number) => `${n} pacientes en seguimiento activo`,
    },
    nearAbandonment: {
      label: "Cerca de abandonar",
      ariaLabel: (n: number) => `${n} pacientes cerca de abandonar`,
    },
    returnRate: {
      label: "Tasa de retorno",
      ariaLabel: (r: number) => `Tasa de retorno: ${Math.round(r * 100)}%`,
    },
    reEngaged: {
      label: "Reactivados este período",
      ariaLabel: (n: number) => `${n} pacientes reactivados este período`,
    },
    npsAverage: {
      label: "NPS promedio",
      ariaLabel: (n: number) => `NPS promedio: ${n.toFixed(1)}`,
    },
    trend: {
      up: "↑",
      down: "↓",
      neutral: "→",
      vsLastPeriod: "vs. período anterior",
    },
  },

  tabs: {
    multisession: "Multisesión",
    followup: "Seguimiento médico",
    maintenance: "Mantenimiento",
    absence: "Ausencia",
    nps: "NPS",
  },

  period: {
    label: "Período",
    "7d": "Últimos 7 días",
    "30d": "Últimos 30 días",
    "90d": "Últimos 90 días",
  },

  urgency: {
    critical: "Crítico",
    alert: "Alerta",
    near: "Próximo",
    waiting: "En espera",
    up_to_date: "Al día",
    ariaLabel: (level: string) => `Urgencia: ${level}`,
  },

  empty: {
    multisession: "¡Todos los pacientes están al día con sus sesiones! ✓",
    followup: "No hay seguimientos pendientes en este período.",
    maintenance: "No hay pacientes que requieran mantenimiento ahora.",
    absence: "No hay pacientes con ausencia prolongada en este período.",
    nps: "No hay respuestas de NPS en este período.",
  },

  actions: {
    send_reminder: "Recordatorio Adrián",
    suggest_slots: "Sugerir turnos",
    pause_patient: "Pausar seguimiento",
    mark_external: "Marcó externo",
    mark_no_continue: "No continúa",
    open_conversation: "Ver conversación",
    call_manually: "Llamada manual",
  },

  multi_session_card: {
    sessionsProgress: (completed: number, expected: number) =>
      `${completed} de ${expected} sesiones`,
    lastSession: "Última sesión",
    gap: (days: number) => `Sin actividad hace ${days} días`,
    doctor: "Dr./Dra.",
  },

  follow_up_card: {
    followUpDue: "Seguimiento vencido",
    followUpIn: (days: number) =>
      days >= 0
        ? `Vence en ${days} días`
        : `Venció hace ${Math.abs(days)} días`,
    reason: "Motivo",
    doctor: "Dr./Dra.",
  },

  maintenance_card: {
    lastService: "Último servicio",
    nextRecommended: "Próximo recomendado",
    monthsSince: (months: number) => `Hace ${months} meses`,
    daysUntil: (days: number) =>
      days >= 0 ? `En ${days} días` : `Venció hace ${Math.abs(days)} días`,
  },

  absence_card: {
    lastAppointment: "Última consulta",
    monthsInactive: (months: number) => `${months} meses inactivo`,
    lifetimeAppointments: (n: number) => `${n} consultas históricas`,
    lifetimeValue: "Valor histórico",
    noMarketing: "El paciente no aceptó comunicaciones de marketing",
  },

  modals: {
    confirmTemplate: {
      title: "Confirmar recordatorio",
      description:
        "Adrián enviará el siguiente mensaje por WhatsApp al paciente.",
      preview: "Vista previa del mensaje",
      cancel: "Cancelar",
      confirm: "Enviar recordatorio",
      sending: "Enviando...",
      successToast: "Recordatorio enviado correctamente.",
      errorToast: "No pudimos enviar el recordatorio. Intenta de nuevo.",
    },

    pausePatient: {
      title: "Pausar seguimiento",
      description:
        "El paciente no recibirá recordatorios automáticos durante el período seleccionado.",
      durationLabel: "Duración de la pausa",
      durationOptions: {
        "7": "7 días",
        "30": "30 días",
        custom: "Personalizado",
      },
      reasonLabel: "Motivo (opcional)",
      reasonPlaceholder: "Ej.: viaje, cirugía programada...",
      cancel: "Cancelar",
      confirm: "Pausar seguimiento",
      successToast: "Seguimiento pausado correctamente.",
    },

    manualCall: {
      title: "Registrar llamada",
      notesLabel: "Notas de la llamada",
      notesPlaceholder: "Escribe aquí lo que hablaron...",
      outcomeLabel: "Resultado de la llamada",
      outcomeOptions: {
        reached: "Contacté al paciente",
        voicemail: "Dejé mensaje de voz",
        no_answer: "No contestó",
      },
      cancel: "Cancelar",
      confirm: "Registrar llamada",
      successToast: "Llamada registrada correctamente.",
    },

    suggestSlots: {
      title: "Sugerir turnos disponibles",
      description: "Selecciona hasta 3 turnos para enviarle al paciente.",
      noSlots: "No hay turnos disponibles en los próximos 14 días.",
      cancel: "Cancelar",
      confirm: "Enviar sugerencias",
      successToast: "Sugerencias enviadas correctamente.",
    },
  },

  activity: {
    streamTitle: "Actividad reciente",
    template_sent: "Recordatorio enviado",
    response_received: "Respuesta recibida",
    appointment_booked: "Turno confirmado",
    patient_paused: "Seguimiento pausado",
    manual_call_logged: "Llamada registrada",
  },

  accessibility: {
    cardExpand: "Expandir tarjeta de paciente",
    cardCollapse: "Colapsar tarjeta de paciente",
    filtersPanel: "Panel de filtros",
    tabsNav: "Navegación de pestañas de seguimiento",
    kpisRegion: "Indicadores clave de seguimiento",
    activityFooter: "Actividad reciente de seguimiento",
    closeModal: "Cerrar",
    disabledActionTooltip: (reason: string) => `No disponible: ${reason}`,
  },

  errors: {
    notAuthenticated: "No autenticado. Por favor, inicia sesión de nuevo.",
    networkError: "Error de conexión. Verifica tu internet.",
    generic: "Algo salió mal. Intenta de nuevo.",
    phiAccessDenied:
      "No tienes permisos para ver esta información de pacientes.",
  },
} as const;

export type FidelizacionCopy = typeof FIDELIZACION_COPY;
