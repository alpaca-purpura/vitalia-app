// cap: onboarding.clinic-onboarding-3step
// story-origin: TBD
/**
 * copy.ts — Onboarding wizard microcopy SSoT
 *
 * ALL user-facing strings for the wizard onboarding feature.
 * Spanish neutro LatAm tuteo. PROHIBIDO voseo.
 *
 * Rules per .claude/rules/spanish-text.md:
 *   - Tuteo (tú, tienes, puedes, etc.) — NOT voseo
 *   - Tildes, ñ, ¿, ¡ correct
 *   - No regional markers (MX/CO/PE/CL/AR)
 *
 * downstream-regression-na: brand-local FE copy; no cross-brand consumers
 */

/** Wizard wizard-onboarding copy namespace */
export const WIZARD_COPY = {
  // ---------------------------------------------------------------------------
  // Top bar
  // ---------------------------------------------------------------------------
  topBar: {
    logoAlt: "Vitalia",
    title: "Configuración de tu clínica",
    subtitle: "Asistente de bienvenida",
    closeButton: "Cerrar asistente",
    slotCounterLabel: (confirmed: number, total: number) =>
      `${confirmed} de ${total} datos confirmados`,
  },

  // ---------------------------------------------------------------------------
  // Close warning modal
  // ---------------------------------------------------------------------------
  closeModal: {
    title: "¿Deseas cerrar el asistente?",
    description:
      "Tu progreso se guarda automáticamente. Puedes continuar la configuración cuando quieras.",
    cancelButton: "Continuar configurando",
    confirmButton: "Cerrar por ahora",
  },

  // ---------------------------------------------------------------------------
  // Slot tracker
  // ---------------------------------------------------------------------------
  slotTracker: {
    sectionLabel: "Datos de tu clínica",
    confirmedPrefix: "✓",
    pendingPrefix: "○",
    statusConfirmed: "Confirmado",
    statusPending: "Pendiente",
    statusOptional: "Opcional",
    emptyState: "Comenzaremos a identificar los datos de tu clínica.",
  },

  // ---------------------------------------------------------------------------
  // Mode selector (URL / Document / Audio)
  // ---------------------------------------------------------------------------
  modeSelector: {
    label: "¿Cómo prefieres compartir la información?",
    options: {
      url: {
        label: "Desde tu sitio web",
        description: "Ingresa la URL de tu clínica o redes sociales",
        icon: "Globe",
      },
      document: {
        label: "Subir documento",
        description: "PDF, Word o imagen con datos de tu clínica",
        icon: "FileText",
      },
      audio: {
        label: "Por audio",
        description: "Cuéntanos sobre tu clínica",
        icon: "Mic",
        disabledTooltip: "Disponible próximamente",
      },
    },
    continueButton: "Continuar",
  },

  // ---------------------------------------------------------------------------
  // Chat thread
  // ---------------------------------------------------------------------------
  chat: {
    assistantName: "Valeria",
    assistantAvatarAlt: "Valeria — asistente de Vitalia",
    userLabel: "Tú",
    inputPlaceholder: "Escribe aquí tu respuesta...",
    sendButton: "Enviar",
    backButton: "← Atrás",
    skipButton: "Completar con datos predeterminados",
    typingIndicatorLabel: "Valeria está escribiendo",
    emptyState: "Valeria iniciará la conversación en un momento.",
    urlInputLabel: "URL de tu sitio web o redes sociales",
    urlInputPlaceholder: "https://www.miclinica.com",
    urlSubmitButton: "Analizar",
    urlProcessing: "Analizando tu sitio...",
    bonusNluLabel: "Información encontrada automáticamente",
    bonusNluSublabel: "Estos datos fueron detectados en tu contenido",
  },

  // ---------------------------------------------------------------------------
  // Slot confirm inline
  // ---------------------------------------------------------------------------
  slotConfirm: {
    promptPrefix: "Encontré este dato:",
    editLabel: "Editar",
    confirmButton: "Confirmar",
    rejectButton: "No es correcto",
    editInputLabel: "Corrección",
    editSaveButton: "Guardar corrección",
    editCancelButton: "Cancelar",
    confirmedBadge: "Confirmado",
  },

  // ---------------------------------------------------------------------------
  // Live preview panel
  // ---------------------------------------------------------------------------
  livePreview: {
    panelTitle: "Vista previa en vivo",
    panelSubtitle: "Así lucirá tu identidad de marca",
    whatsAppTitle: "Así escribe tu agente",
    whatsAppSubtitle: "Mensaje de bienvenida por WhatsApp",
    landingTitle: "Portada de tu sitio",
    landingCtaDefault: "Reservar consulta",
    loadingText: "Actualizando vista previa...",
    emptyState: "La vista previa aparece cuando confirmes tus primeros datos.",
    costLabel: "costo estimado",
    modelLabel: "modelo",
  },

  // ---------------------------------------------------------------------------
  // Completion transition
  // ---------------------------------------------------------------------------
  completion: {
    headline: "¡Tu clínica está configurada!",
    subheadline: "Vitalia ya conoce tu identidad de marca.",
    bodyText:
      "Tu agente inteligente está listo para atender pacientes con tu voz y estilo.",
    ctaButton: "Ir al panel principal",
    ctaButtonLoading: "Preparando tu panel...",
    confettiAlt: "Celebración",
  },

  // ---------------------------------------------------------------------------
  // Error states
  // ---------------------------------------------------------------------------
  errors: {
    loadDraftFailed:
      "No pudimos cargar tu sesión. Por favor, recarga la página.",
    extractFailed:
      "No pudimos analizar el contenido. Intenta con otra URL o escribe los datos manualmente.",
    confirmSlotFailed:
      "No pudimos guardar este dato. Por favor, intenta nuevamente.",
    simulateFailed: "No pudimos generar la vista previa en este momento.",
    completeFailed:
      "Hubo un error al finalizar la configuración. Tus datos están guardados.",
    sessionExpired:
      "Tu sesión expiró. Tus datos se guardaron — puedes continuar desde donde lo dejaste.",
    urlInvalid:
      "Por favor, ingresa una URL válida (debe comenzar con https://).",
    retryButton: "Intentar nuevamente",
    genericError: "Algo salió mal. Por favor, intenta de nuevo.",
  },

  // ---------------------------------------------------------------------------
  // Loading states
  // ---------------------------------------------------------------------------
  loading: {
    initializingWizard: "Iniciando asistente...",
    loadingDraft: "Cargando tu sesión...",
    extracting: "Analizando el contenido...",
    simulating: "Generando vista previa...",
    completing: "Finalizando tu configuración...",
  },

  // ---------------------------------------------------------------------------
  // Accessibility labels
  // ---------------------------------------------------------------------------
  a11y: {
    wizardRegionLabel: "Asistente de configuración de clínica",
    chatRegionLabel: "Conversación con Valeria",
    previewRegionLabel: "Vista previa en vivo",
    slotTrackerLabel: "Estado de los datos de tu clínica",
    progressLabel: (pct: number) => `Progreso: ${pct}%`,
    messageFromAssistant: (text: string) => `Valeria dice: ${text}`,
    messageFromUser: (text: string) => `Tú escribiste: ${text}`,
    closeDialogTitle: "Confirmación para cerrar asistente",
  },
} as const;
