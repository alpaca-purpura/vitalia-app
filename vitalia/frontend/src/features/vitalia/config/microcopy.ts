// cap: shell-organism.shell-vitalia
// story-origin: TBD
/**
 * microcopy.ts — SSoT for all vitalia user-facing strings.
 * Source: 01-spec.md § 8 (immutable). Spanish neutro LatAm.
 * NO voseo (tenés/podés/hacés/mirá...). Tuteo (tú/tienes/puedes).
 *
 * @architecture-group vitalia-ui-strings
 */

// ── § 8.1 Onboarding ──────────────────────────────────────────────────────────

export const MICROCOPY_ONBOARDING = {
  title: "Bienvenida a Vitalia",
  subtitle: "Cuéntanos sobre tu clínica",
  sectionTitle: "Perfil de la clínica",

  fields: {
    clinicName: "Nombre de la clínica",
    clinicType: "Tipo de clínica",
    country: "País",
    city: "Ciudad",
  },

  cta: {
    next: "Siguiente",
    back: "Atrás",
  },

  errors: {
    required: "Este campo es requerido",
    clinicNameTaken: "Este nombre ya está usado en Vitalia. Prueba otro.",
  },

  clinicTypes: {
    dental: {
      label: "Dental",
      hint: "Implantes, ortodoncia, limpiezas",
    },
    psychology: {
      label: "Psicología",
      hint: "Terapia individual, pareja, infanto-juvenil",
    },
    psychiatry: {
      label: "Psiquiatría",
      hint: "Tratamiento médico, prescripción",
    },
    wellness: {
      label: "Wellness",
      hint: "Kinesiología, nutrición, otro",
    },
  },
} as const;

// ── § 8.2 Brand Studio ────────────────────────────────────────────────────────

export const MICROCOPY_BRAND_STUDIO = {
  title: "Brand Studio",
  subtitle: "Cómo se ve tu clínica",

  sections: {
    identity: "Identidad",
    contact: "Contacto",
    medicalTeam: "Equipo médico",
    testimonials: "Testimonios",
  },

  autosave: {
    saving: "Guardando...",
    saved: "Guardado hace {N} seg",
    error: "Error guardando.",
    retry: "Reintentar.",
  },

  empty: {
    title: "Tu Brand Studio está vacío",
    cta: "Empezar con identidad",
  },
} as const;

// ── § 8.3 Offer Wizard ────────────────────────────────────────────────────────

export const MICROCOPY_OFFER_WIZARD = {
  title: "Nueva oferta",

  steps: {
    serviceType: "Tipo de servicio",
    targetPatient: "Para qué paciente",
    price: "Precio",
    consent: "Consentimiento",
    durationAndDoctor: "Duración y profesional",
  },

  prepay: {
    label: "Requiere prepago",
    fullPayment: "Pago completo antes de la cita",
    partialDeposit: "Depósito parcial",
  },

  publish: {
    cta: "Publicar oferta",
    successTitle: "Oferta publicada",
    successBody: "Tu oferta ya está visible para pacientes.",
  },
} as const;

// ── § 8.4 Booking ─────────────────────────────────────────────────────────────

export const MICROCOPY_BOOKING = {
  title: "Agenda tu cita",

  availability: {
    available: "Disponible",
    busy: "Ocupado",
  },

  consent: {
    title: "Consentimiento informado",
    scrollInstruction: "Lee y desplaza hasta el final",
    accept: "Acepto los términos",
    signaturePrompt: "Firma con tu nombre completo",
  },

  payment: {
    cta: "Paga tu depósito",
    confirmed: "Cita confirmada",
    failed: "Pago no procesado",
    retry: "Reintentar pago",
  },
} as const;

// ── § 8.5 Treatment Followup ──────────────────────────────────────────────────

export const MICROCOPY_TREATMENT = {
  title: "Seguimiento de tratamiento",
  planTitle: "Plan de tratamiento — {treatment_name}",

  adherence: {
    label: "Adherencia",
    done: "Hecho",
    pending: "Pendiente",
  },

  actions: {
    takeConversation: "Tomar conversación",
    sendConsent: "Enviar consentimiento",
    viewAuditLog: "Ver audit log paciente",
  },

  alerts: {
    symptomsReported:
      "Atención: el paciente reportó síntomas. Intervención manual requerida.",
  },

  milestones: {
    d0: "Día 0",
    d5: "Día 5",
    d14: "Día 14",
    d90: "Día 90",
  },
} as const;

// ── § 8.6 Compliance ──────────────────────────────────────────────────────────

export const MICROCOPY_COMPLIANCE = {
  title: "Cumplimiento HIPAA-lite",
  subtitle: "Audit log para registro legal",

  stats: {
    totalEvents: "Total eventos",
    critical: "Críticos",
    blocked: "Bloqueados",
  },

  export: {
    cta: "Exportar CSV",
    preparing: "Preparando CSV...",
    ready: "Descarga lista",
  },

  eventTypes: {
    pii_detected: "PII detectado en input",
    consent_requested: "Consentimiento solicitado",
    consent_signed: "Consentimiento firmado",
    security_escalation: "Escalación de seguridad",
    prompt_injection_blocked: "Prompt injection bloqueado",
    cross_tenant_blocked: "Intento cross-tenant bloqueado",
  },
} as const;

// ── § Medical Disclaimer ──────────────────────────────────────────────────────

export const MICROCOPY_DISCLAIMER = {
  default:
    "Esto no reemplaza consulta médica profesional. Ante emergencias, comunícate con tu médico.",
  treatment:
    "La información de este tratamiento es solo para seguimiento. Ante dudas, consulta a tu médico.",
  offer:
    "Esta oferta incluye servicios médicos. Consulta las condiciones con el profesional asignado.",
} as const;

// voseo-allowed: comentario interno cita glosario voseo (strings reales son tuteo), no user-facing
