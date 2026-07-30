// cap: adrian.inbox
// story-origin: TBD
/**
 * copy.ts — Inbox microcopy SSoT (single-locale, tree-shakable).
 *
 * Spanish neutro LatAm — NO voseo (spanish-text.md § R2).
 * Cero strings hardcoded en JSX — todos los textos pasan por INBOX_COPY.
 * Arch fitness test_no_hardcoded_strings_inbox.test.ts enforces.
 *
 * Ratificado /po-ux v1 Batch 2 (01-spec-extract.md § 10).
 *
 * downstream-regression-na: brand-local FE copy; no cross-brand consumers
 */

export const INBOX_COPY = {
  pageTitle: "Inbox",

  /** ListEmptyState 4 variants */
  empty: {
    noConversations: {
      heading: "Aún no hay conversaciones",
      body: "Cuando lleguen pacientes interesados, Adrián los va a recibir con calidez. Puedes acompañar siempre.",
    },
    noHelpNeeded: {
      heading: "Adrián resuelve solo por ahora",
      body: "Si alguna conversación necesita tu mirada, va a aparecer aquí con un indicador rojo.",
    },
    noMediaUnread: {
      heading: "Sin audios o imágenes pendientes",
      body: "Cuando un paciente envíe una foto o nota de voz, la vas a ver aquí antes de que se enfríe.",
    },
    noResultsFilter: {
      heading: "Sin resultados para este filtro",
      body: "Limpia los filtros para volver a ver todas las conversaciones.",
      cta: "Limpiar filtros",
    },
  },

  /** Thread pane — empty states + day separators (UI-AUDIT #1/#3) */
  thread: {
    emptyHeading: "Aquí va a aparecer la conversación",
    emptyBody:
      "Cuando un paciente escriba, Adrián lo recibe y el hilo aparece aquí.",
    contactEmptyHeading: "Aquí va a aparecer la ficha del contacto",
    contactEmptyBody:
      "Vas a ver el nombre, el canal y el interés del paciente al abrir una conversación.",
    dayToday: "Hoy",
    dayYesterday: "Ayer",
    turnAdrian: "Adrián · Auto",
    turnYou: "Tú · Manual",
  },

  /** FilterChips labels */
  filters: {
    all: "Todas",
    channels: {
      whatsapp: "WhatsApp",
      instagram: "Instagram",
      telegram: "Telegram",
      tiktok: "TikTok",
      facebook: "Facebook",
      email: "Email",
    },
    status: {
      active: "Activa",
      waitingDeposit: "Esperando depósito",
      npsPending: "NPS pendiente",
      closed: "Cerradas",
    },
    helpNeeded: "Adrián pide ayuda",
    unreadMedia: "Audio/imagen sin abrir",
    moreFilters: "Más filtros",
    lessFilters: "Menos filtros",
    stage: {
      label: "Etapa",
      interested: "Interesado",
      considering: "Considerando",
      readyToBook: "Listo para reservar",
      decidedNo: "Decidió no",
    },
    mode: {
      label: "Modo Adrián",
      adrianDecide: "Adrián decide",
      adrianConsulta: "Adrián consulta",
      yoEscribo: "Yo escribo",
    },
    period: {
      label: "Período",
      today: "Hoy",
      yesterday: "Ayer",
      week: "Esta semana",
      month: "Este mes",
    },
    searchPlaceholder: "Buscar conversación…",
  },

  /** Segmented mode control (2 modos · Chris UI #3) */
  segmentedMode: {
    adrianDecide: "Adrián decide",
    adrianConsulta: "Adrián consulta",
    adrianDecideHint: "Adrián responde solo, automáticamente.",
    adrianConsultaHint: "Adrián redacta y tú apruebas antes de enviar.",
    ariaLabel: "Modo de atención",
  },

  /** Composer dock — pause status bar above the message box (Chris UI #3) */
  composerDock: {
    activeHint: "Adrián está atendiendo esta conversación",
    pausedHint: "Adrián pausado · escribes tú",
    pausedRemaining: "Adrián pausado · {minutes} min restantes",
  },

  /** Pause agent button + modal */
  pauseAgent: {
    button: "Pausar Adrián",
    buttonActive: "Adrián pausado",
    modalTitle: "Pausar a Adrián",
    modalBody:
      "Adrián deja de responder esta conversación y la atiendes tú. Elige por cuánto tiempo:",
    confirmPermanent: "Pausar permanente",
    confirm60: "Pausar 60 minutos",
    cancelCta: "Cancelar",
    toastSuccess: "Adrián pausado",
    resumeCta: "Reanudar Adrián",
    resumeToast: "Adrián vuelve a atender esta conversación",
  },

  /** Nudge (empujón 1:1 re-engagement) button + confirm */
  nudge: {
    button: "Dar empujón",
    ariaEnabled: "Dar empujón a esta conversación",
    ariaDisabled: "Dar empujón (no disponible para esta conversación)",
    titleEnabled: "Dar un empujón de reactivación al paciente",
    titleDisabled: "No disponible para conversaciones no activas",
    confirmTitle: "Confirmar empujón",
    confirmQuestion: "¿Dar un empujón?",
    confirmCta: "Dar empujón",
    sendingCta: "Enviando…",
    cancelCta: "Cancelar",
    toastSuccess: "Empujón enviado",
    toastError: "No se pudo enviar el empujón. Intenta de nuevo.",
  },

  /** Composer area */
  composer: {
    placeholder: {
      adrianDecide: "Escribe algo si quieres tomar la conversación…",
      adrianConsulta:
        "Adrián te sugiere esta respuesta… (puedes editarla antes de enviar)",
      yoEscribo: "Escribe tu mensaje a {patient_name}…",
      /** instruction mode — handler_mode=ai (decide), operator steers Adrián */
      instructionToAdrian:
        "Instrucción a Adrián (el paciente no la verá)…",
    },
    sendButtonAi: "Enviar como Adrián",
    sendButtonHuman: "Enviar",
    /** instruction mode send button label */
    sendButtonInstruction: "Dar instrucción",
    attachAriaLabel: "Adjuntar archivo",
    voiceAriaLabel: "Grabar nota de voz",
    recordingActive: "Grabando…",
    recordingStop: "Detener grabación",
  },

  /** Instruction mode (RN-13/14/SC-8) — operator instruction to Adrián */
  instruction: {
    /** Label shown in composer header when effectiveMode === 'instruction' */
    modeLabel: "🤖 Instrucción a Adrián",
    /** Hint below label */
    modeHint: "el paciente no la verá",
    /** Chip shown when an instruction is active for this conversation */
    chipPrefix: "🤖 Instrucción activa:",
    /** Chip clear button aria-label */
    chipClearAriaLabel: "Limpiar instrucción activa",
    /** Chip edit button aria-label */
    chipEditAriaLabel: "Editar instrucción activa",
    /** Toast on success */
    toastSuccess: "Instrucción enviada a Adrián",
    /** Toast on error */
    toastError: "No se pudo guardar la instrucción. Intenta de nuevo.",
    /** Aria live region for screen readers */
    ariaLiveSet: "Instrucción guardada para Adrián",
  },

  /** Multimedia messages */
  multimedia: {
    audioPlayer: {
      ariaLabel: "Nota de voz",
      transcript: "Transcripción:",
      transcriptFailed: "No se pudo transcribir esta nota de voz.",
      speedLabel: "Velocidad",
    },
    imagePlaceholder: {
      heading: "Imagen recibida",
      body: "El análisis de Adrián estará disponible en Slice 2.",
      ariaLabel: "Vista previa de imagen",
    },
    documentLabel: "Documento adjunto",
    stickerLabel: "Sticker",
  },

  /** Tools sheet */
  toolsSheet: {
    title: "Herramientas de Adrián",
    ariaLabel: "Panel de herramientas de Adrián",
    noTools: "No hay herramientas configuradas para esta conversación.",
    lastUsed: "Usado el {date}",
    neverUsed: "Sin usar todavía",
    statusEnabled: "Habilitada",
    statusDisabled: "Deshabilitada",
    hipaaGuardNote:
      "Deshabilitado — no se envían por WhatsApp (HIPAA-lite). Pídele al paciente que ingrese al portal seguro.",
    changeOfferCta: "Cambiar oferta vinculada",
    goToOfferStudio: "Ir a /offer-studio →",
  },

  /** Activity stream */
  activityStream: {
    title: "Actividad de Adrián",
    ariaLabel: "Actividad reciente de Adrián",
    expandAriaLabel: "Expandir actividad",
    collapseAriaLabel: "Contraer actividad",
    empty:
      "Aquí verás lo que hace Adrián: mensajes que envía, herramientas que usa y decisiones que toma.",
    loadMore: "Ver más actividad",
    eventKinds: {
      tool_call: "Usó herramienta",
      llm_call: "Procesó consulta",
      turn_start: "Comenzó turno",
      turn_end: "Terminó turno",
      proposal_generated: "Generó propuesta",
      mode_changed: "Cambió modo",
      message_sent: "Envió mensaje",
      message_retracted: "Revirtió mensaje",
      adrian_paused: "Adrián pausado",
      compliance_blocked: "Bloqueado por cumplimiento",
      nudge_sent: "Empujón enviado",
    },
  },

  /** Action receipt undo chip */
  actionReceipt: {
    revertCta: "Revertir",
    revertAriaLabel: "Revertir mensaje ({remaining})",
    modalTitle: "Revertir mensaje",
    modalBody:
      "Se va a solicitar al canal que elimine el mensaje. El texto vuelve al compositor para que lo puedas editar.",
    confirmCta: "Sí, revertir",
    cancelCta: "Cancelar",
    toastSuccess: "Mensaje revertido. El compositor tiene el texto original.",
    toastFailed:
      "No se pudo revertir en el canal. El mensaje fue marcado como erróneo en el registro.",
    expired: "Tiempo de reversión expirado",
  },

  /** Contact sidebar */
  contactSidebar: {
    ariaLabel: "Información del contacto",
    sectionContact: "Contacto",
    sectionStage: "Etapa de la venta",
    serviceInterest: "Servicio de interés",
    serviceInterestEmpty: "Aún no detectado",
    sectionOffer: "Oferta vinculada",
    sectionNpsHistory: "Historial NPS",
    revealField: "Revelar",
    noPhone: "Sin teléfono registrado",
    noEmail: "Sin correo registrado",
    noOffer: "Sin oferta vinculada",
    linkOffer: "Vincular oferta",
    npsEmpty: "Sin encuestas NPS todavía.",
    toggleOpen: "Abrir ficha de contacto",
    toggleClose: "Cerrar ficha de contacto",
  },

  /** Help needed banner */
  helpNeededBanner: {
    heading: "Adrián pide tu ayuda",
    body: "Revisa la conversación y toma el control cuando estés listo.",
    reasonLabel: "Razón:",
    dismissCta: "Entendido",
    takeover: "Tomar el control",
  },

  /** Proposal card banner (Adrián waiting approval) */
  proposalCardBanner: {
    heading: "Adrián tiene una propuesta lista",
    body: "Revísala y apruébala o edítala antes de enviar.",
    approveCta: "Aprobar y enviar",
    editCta: "Editar propuesta",
  },

  /** Proactive outbound modal */
  proactiveOutboundModal: {
    title: "Iniciar conversación proactiva",
    selectContact: "Seleccionar contacto",
    selectTemplate: "Seleccionar plantilla",
    preview: "Vista previa",
    confirmCta: "Enviar",
    cancelCta: "Cancelar",
    sentSuccess: "Conversación iniciada correctamente.",
  },

  /** Error states */
  errors: {
    loadConversations:
      "No se pudieron cargar las conversaciones. Intenta de nuevo.",
    loadThread: "No se pudo cargar la conversación. Intenta de nuevo.",
    sendMessage: "No se pudo enviar el mensaje. Intenta de nuevo.",
    sendConflict:
      "La conversación fue actualizada. Recarga para ver los cambios.",
    revertFailed: "No se pudo revertir en el canal. El mensaje quedó marcado.",
    generic: "Ocurrió un error inesperado. Intenta de nuevo.",
    retry: "Reintentar",
  },
} as const;

/** Type helper for INBOX_COPY leaf values */
export type InboxCopyKey = typeof INBOX_COPY;
