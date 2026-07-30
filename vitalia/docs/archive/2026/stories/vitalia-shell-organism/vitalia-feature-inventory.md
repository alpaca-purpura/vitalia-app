# Vitalia — Inventario completo de funcionalidades actuales

> **Propósito:** snapshot exhaustivo de TODO lo construido en `vitalia/` hoy (frontend + backend + capabilities + brand config) para informar el rediseño del shell (story `vitalia-shell-organism`). Espejo del documento `nicolify-feature-inventory.md` pero para vitalia.
>
> **Fuente verificada (paths exactos):**
> - Sidebar real: `vitalia/frontend/src/components/shared/shell/Sidebar.tsx::DEFAULT_NAV_ITEMS`
> - Routes: `vitalia/frontend/src/app/(dashboard)/**/page.tsx`
> - Features FE: `vitalia/frontend/src/features/{vitalia,inbox,marketing,fidelizacion,onboarding,dashboard,crm-shared,marketing-shared}/`
> - Brand config: `vitalia/config/brand.yaml`
> - Capabilities catalog (R32 inventory): `vitalia/docs/product/capabilities/**/*.yaml` (59 entries todas `status: live`)
> - Backend modules: `vitalia/backend/src/modules/vitalia/{admin,agentic,audit,clinics,compliance,connections,copilot,crm,fidelizacion,iam,inbox,marketing,payment,sales_agent,_shared}/`
>
> **Fecha snapshot:** 2026-05-21.
>
> **Formato:** JSON-in-MD igual que `navigation-tree.md` y `nicolify-feature-inventory.md`, con `description` + `use_cases` expandidos en cada hoja terminal.
>
> **Convención status:**
> - `shipped` — construido, vivo, **enlazado en sidebar**
> - `shipped_orphan` — código y route shippeados pero **NO enlazados en sidebar** (el bug origen del caso 2026-05-21: marketing/inbox/fidelización/brand-studio/offers/compliance están aquí)
> - `partial` — UI parcial o features behind flag
> - `defer_11bis` — explícitamente diferido a story 11.bis (multi-site UI, insurance integration, wellness deep)
> - `not_started` — no existe (gap vs nicolify)

## Resumen ejecutivo — el bug que motivó el shell-organism

```
Sidebar actual (6 items hardcoded en Sidebar.tsx::DEFAULT_NAV_ITEMS):
  • Inicio           → /dashboard            ✅ shipped
  • Pacientes        → /dashboard/patients   ❌ ENLACE ROTO (real route: /patients)
  • Agenda           → /dashboard/schedule   ❌ ENLACE ROTO (real route: /appointments)
  • Tratamientos     → /dashboard/treatments ❌ ENLACE ROTO (real route: /treatments)
  • Pagos            → /dashboard/payments   ❌ ENLACE ROTO (no existe la route)
  • Copiloto         → /dashboard/copilot    ❌ ENLACE ROTO (no existe la route)

Routes shippeadas pero NO en sidebar (ORPHANS — invisibles al usuario):
  • /                       Inicio dashboard
  • /appointments           Agenda
  • /patients               Pacientes
  • /treatments             Tratamientos
  • /bookings               Bookings (lista + detail)
  • /offers                 Catálogo de servicios médicos (Offer Studio)
  • /offers/new             Wizard nueva oferta médica
  • /brand-studio           Brand Studio (4 secciones medical-flavor)
  • /marketing              Bowtie funnel 5 stages + Lucas recommendations
  • /fidelizacion           5 tabs (multisesión, seguimiento, mantenimiento, ausencia, NPS)
  • /medical-compliance     Compliance audit log + stats
  • /inbox                  Adrián inbox (3 modos: decide/consulta/yo-escribo)
  • /onboarding/wizard      Valeria wizard agéntico

Routes públicas (sin auth):
  • /public/[clinic-slug]            Landing pública per-clínica
  • /public/[clinic-slug]/booking    Booking widget embed público
```

**Conclusión:** vitalia tiene ~13 superficies funcionales shippeadas pero el sidebar solo lista 6 con enlaces que apuntan a paths inexistentes. El usuario que entra al dashboard ve menú roto. **Esto es exactamente lo que necesita resolver `vitalia-shell-organism`** + la story `vitalia-slice-1-marketing-integration` (que hoy está `state: idea`).

---

## Resumen por área (status snapshot)

| Área | Routes shipped | Capabilities catalogadas | Estado sidebar | Owner módulo |
|---|---|---|---|---|
| Dashboard inicio | 1 | 1 (welcome-state) | ✅ visible (link OK) | dashboard |
| Pacientes | 2 (list + detail) | 2 (nps-tracking + records) | ❌ orphan (link roto) | crm + patients |
| Agenda / Citas | 1 (appointments) | — | ❌ orphan (link roto) | inbox / agenda |
| Bookings (reservas prepagadas) | 2 (list + detail) | 2 (booking-widget + advisory-locks) | ❌ orphan (no link) | booking |
| Tratamientos | 3 (list + detail + followup) | 1 (treatment-followup-workflow) | ❌ orphan (link roto) | treatments |
| Brand Studio (médico) | 2 (root + section) | 1 (brand-studio-medical-sections) | ❌ orphan (no link) | brand_studio |
| Offer Studio (médico) | 3 (list + new + detail) | 1 (medical-services-offer-preset) | ❌ orphan (no link) | offer_studio |
| Marketing (Bowtie + Lucas) | 1 (root) | 4 (bowtie, attribution, lucas-rec, referrals) | ❌ orphan (no link) | marketing |
| Fidelización | 1 (root + 5 tabs) | — (parte de marketing/sales_agent) | ❌ orphan (no link) | fidelizacion |
| Inbox (Adrián) | 1 (root) | 5 (3-tools, reengagement, inbox-handler, guardrails, state-overlay) | ❌ orphan (no link) | inbox + sales_agent |
| Compliance HIPAA-lite | 1 (medical-compliance) | 3 (compliance-audit, hipaa-stack, wpp-templates) | ❌ orphan (no link) | compliance |
| Connections | — (no UI todavía) | 2 (oauth-meta-google, registries-medical) | ❌ no UI | connections |
| Pagos | — (no UI todavía) | 1 (payment-gateways-latam-recurring) | ❌ link roto sin UI | payment |
| Public landing | 2 (clinic + booking) | 1 (public-clinic-landing) | n/a (pública) | public_landing |
| Onboarding | 1 (wizard) | 2 (3step + wizard-brand-studio) | redirect post-signup | onboarding |
| Auth (Clerk) | 2 (sign-in/up) | 2 (clerk-middleware + sign-pages) | n/a | auth |
| Admin (Streamlit, no FE Next) | — | 5 (streamlit-service + 4 CRUDs) | n/a (servicio separado) | admin |
| Copilot (Valeria) | — (no FE rail todavía) | 4 (inbox-tools, medical-kb, pdf-extractors, valeria-wizard) | ❌ link roto sin UI | copilot |
| Observability + ops | — (infra) | 4 (api-health, otel-sentry, callback-subclasses, k8s-admin) | n/a | observability + ops |
| Tests + fixtures | — (infra) | 3 (playwright-smoke, 3-clinic-fixture, eval-goldens) | n/a | tests + fixtures |
| Platform foundation | — (infra) | 3 (design-tokens, migrations-slice-1, extension-sdk-medical) | n/a | platform |
| Workers (cron) | — (infra) | 1 (idempotent-arq-scaffold) | n/a | workers |
| IAM / RBAC | — (infra) | 2 (iam-scaffold + luana-core-adoption) | n/a | iam |
| Audit | — (infra) | 1 (audit-writer-ssot) | n/a | audit |

**Total:** 59 capabilities catalogadas en R32 inventory, todas `status: live`.

---

## JSON tree exhaustivo

```json
{
  "brand": "vitalia",
  "schema_version": "1.0",
  "snapshot_date": "2026-05-21",
  "source": {
    "sidebar": "vitalia/frontend/src/components/shared/shell/Sidebar.tsx::DEFAULT_NAV_ITEMS",
    "routes": "vitalia/frontend/src/app/(dashboard)/**/page.tsx",
    "capabilities": "vitalia/docs/product/capabilities/**/*.yaml (59 entries)",
    "brand_config": "vitalia/config/brand.yaml"
  },
  "brand_config_snapshot": {
    "compliance_level": "hipaa_lite",
    "voice_cloning": false,
    "multi_language_ui": false,
    "default_booking_deposit_percent": 30,
    "supported_countries_currencies": { "AR": "ARS", "CL": "CLP", "MX": "MXN", "CO": "COP", "PE": "PEN", "BR": "BRL", "US": "USD" },
    "payment_gateways": ["mercadopago", "stripe_connect", "tokenized_recurring"],
    "medical_kb_packs": ["dental_v1", "psychology_v1", "psychiatry_v1"],
    "plan_tiers": {
      "solo_doctor": { "price_usd_monthly": 49, "max_doctors": 1 },
      "clinic": { "price_usd_monthly": 199, "max_doctors": 10 },
      "multi_site": { "price_usd_monthly": 599, "max_doctors": 50, "ui_defer": "story_11_bis" }
    },
    "sales_agent_archetype_default": "warm_close",
    "sales_agent_channels": ["whatsapp_business", "manychat_instagram", "email_async", "web_chat"],
    "brand_studio_enabled_sections": ["identity", "contact", "team", "testimonials"],
    "brand_studio_disabled_sections": ["story", "strategy", "positioning", "narrative", "personality", "communication", "authority_vault"],
    "offer_studio_preset_pack": "medical_services_v1"
  },
  "current_sidebar_actual": {
    "implementation": "vitalia/frontend/src/components/shared/shell/Sidebar.tsx::DEFAULT_NAV_ITEMS",
    "items_count": 6,
    "items": [
      { "label": "Inicio", "href": "/dashboard", "link_status": "OK", "real_route": "/" },
      { "label": "Pacientes", "href": "/dashboard/patients", "link_status": "BROKEN", "real_route": "/patients" },
      { "label": "Agenda", "href": "/dashboard/schedule", "link_status": "BROKEN", "real_route": "/appointments" },
      { "label": "Tratamientos", "href": "/dashboard/treatments", "link_status": "BROKEN", "real_route": "/treatments" },
      { "label": "Pagos", "href": "/dashboard/payments", "link_status": "BROKEN", "real_route": "(no existe)" },
      { "label": "Copiloto", "href": "/dashboard/copilot", "link_status": "BROKEN", "real_route": "(no existe — Valeria sin UI rail)" }
    ],
    "bug_note": "Sidebar.tsx hardcodea hrefs con prefijo '/dashboard/' pero las routes reales NO están bajo ese segmento. 5 de 6 enlaces apuntan a 404. Story vitalia-shell-organism debe resolver."
  },
  "tree": [
    {
      "id": "inicio",
      "label": "Inicio (Dashboard)",
      "icon": "Home",
      "route": "/",
      "status": "shipped",
      "capability_id": "vitalia-dashboard-welcome-state",
      "description": "Página landing del dashboard autenticado. Welcome state inicial post-login con CTAs hacia onboarding (si incompleto) o resumen rápido (si completo). Hoy es vista minimal — destino futuro: KPIs hero + agenda hoy + tareas pendientes + alertas.",
      "use_cases": [
        "Pulso diario del clínico (apenas inicia sesión)",
        "Entry point post-onboarding completed",
        "CTAs para reanudar wizard si incompleto"
      ]
    },
    {
      "id": "agenda",
      "label": "Agenda / Citas",
      "icon": "CalendarClock",
      "route": "/appointments",
      "status": "shipped_orphan",
      "description": "Calendario de citas + appointments del clínico. Componente `AppointmentsCalendarClient`. Vista de operación diaria — qué tengo hoy, qué tengo esta semana.",
      "use_cases": [
        "Ver agenda del día (operación clínica)",
        "Reagendar cita arrastrable",
        "Detectar slot libre para vender",
        "Sync con Adrián cuando el agente reserva nuevos slots"
      ]
    },
    {
      "id": "pacientes",
      "label": "Pacientes",
      "icon": "Users",
      "route": "/patients",
      "status": "shipped_orphan",
      "description": "CRM médico vertical-specific. Lista master de pacientes con filtros + detail panel por paciente con timeline médico + medical PDF upload + NPS tracking.",
      "use_cases": [
        "Encontrar ficha de un paciente rápidamente",
        "Ver historial de tratamientos cross-citas",
        "Subir PDFs médicos (estudios, recetas, lab results) — extractor automático Valeria",
        "Tracking NPS post-tratamiento para detectar pacientes insatisfechos"
      ],
      "children": [
        {
          "id": "pacientes-list",
          "label": "Lista de pacientes",
          "route": "/patients",
          "capability_id": "vitalia-patients-patient-records-medical-history",
          "description": "Tabla de pacientes (`PatientListTable`) con filtros por clínica activa, búsqueda por nombre/DNI, columnas: estado (activo/inactivo/seguimiento), última visita, próxima cita, score NPS."
        },
        {
          "id": "pacientes-detail",
          "label": "Detalle de paciente",
          "route": "/patients/[id]",
          "capability_id": "vitalia-patients-patient-records-medical-history",
          "description": "PatientDetailPanel: datos demográficos, historial médico, lista tratamientos en curso/históricos, citas próximas/pasadas, PDFs subidos (con extracción Valeria), score NPS, audit trail acciones sobre PHI. Dual-filter HIPAA enforced (tenant + clinic)."
        },
        {
          "id": "pacientes-nps",
          "label": "NPS tracking (transversal)",
          "capability_id": "vitalia-patients-nps-tracking",
          "description": "Sub-feature integrado en patient-detail + fidelización-tab-NPS. Captura NPS post-tratamiento via canal WhatsApp template `nps_post_tratamiento.json`, calcula NPS promedio, identifica detractores para re-engagement."
        }
      ]
    },
    {
      "id": "tratamientos",
      "label": "Tratamientos",
      "icon": "Stethoscope",
      "route": "/treatments",
      "status": "shipped_orphan",
      "description": "Gestión de tratamientos en curso (sesiones múltiples, follow-up post-procedimiento). Lista + detail + workflow followup dedicado. Componente `TreatmentTimeline` con milestones.",
      "use_cases": [
        "Ver paciente con sesiones pendientes (multisesión: ortodoncia 12 sesiones, blanqueamiento 4 sesiones, etc.)",
        "Disparar workflow followup post-cirugía/post-procedimiento",
        "Auditar adherencia (paciente que se perdió la sesión 5 de 8)",
        "Cerrar tratamiento + NPS automation"
      ],
      "children": [
        {
          "id": "treatments-list",
          "label": "Lista de tratamientos",
          "route": "/treatments",
          "description": "`TreatmentListTable` filtrable por estado (active/paused/completed/abandoned), tipo (multisession/single/maintenance), paciente, doctor."
        },
        {
          "id": "treatments-detail",
          "label": "Detalle de tratamiento",
          "route": "/treatments/[id]",
          "description": "TreatmentTimeline con `MilestoneName` enum: kickoff → sessions → checkpoints → completion → followup window → close. Cada milestone = entidad con estado + fecha + notas + assigned doctor."
        },
        {
          "id": "treatments-followup",
          "label": "Workflow followup",
          "route": "/treatments/[id]/followup",
          "capability_id": "vitalia-treatments-treatment-followup-workflow",
          "description": "Página dedicada al workflow de seguimiento post-tratamiento. Disparado por `TreatmentFollowupWorkflow` (backend). Ventana 24h/72h/7d/30d post-completion. Envía template `recordatorio_control_doctor.json` automaticamente."
        }
      ]
    },
    {
      "id": "bookings",
      "label": "Reservas (Bookings)",
      "icon": "Calendar",
      "route": "/bookings",
      "status": "shipped_orphan",
      "description": "Reservas prepagadas (30% advance deposit default per `brand.yaml`). Distinta de Appointments (citas asistencia confirmada). Bookings tiene advisory-locks anti-double-book.",
      "use_cases": [
        "Ver reservas pendientes (esperando depósito)",
        "Confirmar booking cuando llega pago via gateway",
        "Cancelar booking + refund según política",
        "Convertir booking a appointment al confirmar"
      ],
      "children": [
        {
          "id": "bookings-list",
          "label": "Lista reservas",
          "route": "/bookings",
          "capability_id": "vitalia-booking-prepaid-booking-advisory-locks",
          "description": "Lista de bookings con estado (pending_deposit/confirmed/cancelled/no_show)."
        },
        {
          "id": "bookings-detail",
          "label": "Detalle reserva",
          "route": "/bookings/[id]",
          "description": "Detail con tracking de pago (gateway + estado + monto + moneda según country), advisory_lock acquired_at + expires_at, paciente vinculado, oferta vinculada."
        },
        {
          "id": "bookings-widget",
          "label": "Booking widget (embebible)",
          "capability_id": "vitalia-booking-booking-widget-embed",
          "description": "Widget JavaScript embebible en sitio externo de la clínica que dispara el flow de booking prepaid sin requerir migración del sitio. Configurable per clinic."
        }
      ]
    },
    {
      "id": "marketing",
      "label": "Marketing (Bowtie + Lucas)",
      "icon": "Megaphone",
      "route": "/marketing",
      "status": "shipped_orphan",
      "description": "Equivalente conceptual a Growth Studio de nicolify pero adaptado a embudo médico Bowtie de 5 stages (pre-revenue + post-revenue). Lucas es el agente analista que vigila el funnel + emite recomendaciones priorizadas + ejecuta acciones aprobadas por el usuario.",
      "use_cases": [
        "Pulso semanal del embudo del clínico",
        "Detectar dónde se cae la conversión (atracción → calificación → reserva → adopción → expansión)",
        "Aprobar recomendaciones de Lucas (pausar canal sin ROI, lanzar campaña a stage X, conectar canal nuevo)",
        "Comparar canales (Meta Ads vs Google Ads vs orgánico)",
        "Ver attribution multi-origen (4 fuentes: agente, walk-in, teléfono, outbound proactivo)",
        "Identificar pacientes evangelistas para programa referral"
      ],
      "children": [
        {
          "id": "mk-bowtie",
          "label": "Bowtie funnel 5 stages",
          "icon": "Activity",
          "capability_id": "vitalia-marketing-bowtie-funnel-5-stages",
          "description": "SVG pixel-invariante del embudo Bowtie. SSoT en `BowtieStage` enum + `MarketingLayout` orchestrator. Cada stage es tab con sub-widgets. Period selector (7d/30d/90d).",
          "stages": [
            { "id": "attraction", "label": "Atracción", "description": "Top-of-funnel: tráfico + impresiones + leads new. Canales: Meta Ads (FB/IG), Google Ads, SEO orgánico, referrals warm." },
            { "id": "qualification", "label": "Calificación", "description": "Mid-funnel: cualificación de leads. Score por medical fit + intent + ability-to-pay. Adrián auto-cualifica via conversación." },
            { "id": "reservation", "label": "Reserva", "description": "Bottom-of-funnel pre-revenue: booking prepaid creada. AttributionMatrix 4 origins se muestra DENTRO este stage." },
            { "id": "adoption", "label": "Adopción", "description": "Post-revenue stage 1: paciente asiste a primera sesión + completa tratamiento inicial. Activación clínica." },
            { "id": "expansion", "label": "Expansión", "description": "Post-revenue stage 2: paciente repite tratamiento, recomienda (referral), sube a maintenance plan, etc. ReferralsWidget se muestra DENTRO este stage." }
          ]
        },
        {
          "id": "mk-attribution",
          "label": "Attribution matrix 4 origins (dentro Reserva stage)",
          "capability_id": "vitalia-marketing-attribution-matrix-4-origins",
          "description": "Heatmap 4 origins × N KPIs (reservas, conversion rate, ingreso, ticket promedio). Origins: `sales_agent` (Adrián), `walk_in` (puerta), `phone_manual` (recepción), `proactive_outbound` (campaña broadcast). Snapshot freshness ≤4h via Lucas cron.",
          "endpoint": "GET /api/v1/vitalia/marketing/attribution-matrix"
        },
        {
          "id": "mk-lucas-rec",
          "label": "Lucas recommendations",
          "capability_id": "vitalia-marketing-lucas-stage-recommendations",
          "description": "Sidebar/panel con cards de recomendaciones priorizadas por Lucas. Cada card tiene: `LucasStageRecommendationsCard` + approve/reject/undo + expiration timer + detail modal (LucasRecommendationDetailModal).",
          "actions": [
            "approve → Lucas ejecuta acción en nombre del usuario (con `LucasApprovalModal` confirm)",
            "reject → Lucas registra rejection reason (con `LucasRejectModal` selector)",
            "undo → Reversion window con `LucasUndoChip` timer visible"
          ]
        },
        {
          "id": "mk-referrals",
          "label": "Referrals leaderboard (dentro Expansión stage)",
          "capability_id": "vitalia-marketing-referrals-leaderboard",
          "description": "ReferralsWidget: leaderboard top-N pacientes evangelistas con referrals enviados / signed_up / converted. Estados: OPEN · SHARED · SIGNED_UP · CONVERTED · EXPIRED."
        },
        {
          "id": "mk-channel-wizard",
          "label": "Channel connection wizard",
          "description": "ChannelConnectionWizard modal para conectar canal nuevo (Meta, Google Ads) desde la vista marketing — short-circuit del settings/connections aún no en UI."
        },
        {
          "id": "mk-activity-footer",
          "label": "Marketing activity footer",
          "description": "MarketingActivityFooter persistente — pulso de Lucas (último análisis, próxima ejecución cron, recommendations pendientes)."
        }
      ]
    },
    {
      "id": "fidelizacion",
      "label": "Fidelización (Retention)",
      "icon": "Heart",
      "route": "/fidelizacion",
      "status": "shipped_orphan",
      "description": "Sistema de retención + re-engagement post-tratamiento (no existe equivalente directo en nicolify). 5 tabs covering ciclo completo de retención médica: multisesión activa → seguimiento médico → mantenimiento → ausencia → NPS.",
      "use_cases": [
        "Detectar pacientes a punto de abandonar (5 sesiones de 10 sin asistir)",
        "Disparar re-engagement automation a pacientes ausentes >90d",
        "Invitar a plan de mantenimiento post-tratamiento exitoso",
        "Recordatorio control médico (post-cirugía 30d/60d/90d)",
        "NPS automation + identificar detractores"
      ],
      "children": [
        {
          "id": "fid-multisesion",
          "label": "Multisesión",
          "tab": "multisession",
          "description": "MultiSessionTab: pacientes en tratamientos multi-sesión activos. KPI hero: en seguimiento activo · cerca de abandonar · tasa de retorno. Componente ReEngagementCard con suggest slots."
        },
        {
          "id": "fid-followup",
          "label": "Seguimiento médico",
          "tab": "followup",
          "description": "FollowUpTab: workflow post-cirugía/post-procedimiento (24h/72h/7d/30d). Template WhatsApp `recordatorio_control_doctor.json`."
        },
        {
          "id": "fid-maintenance",
          "label": "Mantenimiento",
          "tab": "maintenance",
          "description": "MaintenanceTab: pacientes con tratamiento completado pero candidatos a mantenimiento (limpieza dental anual, control psicológico trimestral, etc.). Template `invitacion_mantenimiento.json`."
        },
        {
          "id": "fid-ausencia",
          "label": "Ausencia",
          "tab": "absence",
          "description": "AbsenceTab: pacientes sin actividad >X días configurable. Re-engagement automation con `re_engagement_ausencia.json`. ContactSidebar dedicada (ReEngagementContactSidebar)."
        },
        {
          "id": "fid-nps",
          "label": "NPS",
          "tab": "nps",
          "description": "NPSResumenTab: NPS promedio + distribución (promotores/pasivos/detractores) + NPSRowCompact por paciente. Template `nps_post_tratamiento.json`."
        },
        {
          "id": "fid-actions",
          "label": "Acciones disponibles (cross-tab)",
          "description": "ConfirmTemplateModal (revisar WhatsApp template antes enviar), SuggestSlotsModal (proponer slots concretos al paciente), PausePatientModal (pausar follow-up del paciente sin perder histórico), ManualCallLoggedModal (loggear llamada manual fuera del agente)."
        }
      ]
    },
    {
      "id": "inbox",
      "label": "Inbox (Adrián workspace)",
      "icon": "MessageSquare",
      "route": "/inbox",
      "status": "shipped_orphan",
      "description": "Equivalente al Closer Studio Inbox de nicolify pero scoped a sales_agent vertical-médico (Adrián). 3 modos operativos cementados como SegmentedControl3Modes: `Adrián decide` (automático), `Adrián consulta` (pregunta antes ejecutar), `Yo escribo` (operador toma control). Inbox unificado WhatsApp + Instagram + Email + Web Chat.",
      "use_cases": [
        "Triage conversaciones (qué necesita mi atención)",
        "Tomar control conversación cuando Adrián escala (`Adrián pide ayuda` chip)",
        "Pausar Adrián para una conversación específica",
        "Disparar broadcast proactivo a segmento (ProactiveOutboundModal)",
        "Ver actividad agéntica en stream (AgentActivityStream)",
        "Analizar imagen subida por paciente (ImageAnalysisCard — Lucas vision)",
        "Reproducir nota de voz (VoiceMessagePlayer)"
      ],
      "children": [
        {
          "id": "inbox-modes",
          "label": "3 modos Adrián",
          "description": "SegmentedControl3Modes: ADRIAN_DECIDE (autonomy alta), ADRIAN_CONSULTA (asks before tool execution), YO_ESCRIBO (human-only)."
        },
        {
          "id": "inbox-filters",
          "label": "Filtros multi-dimensión",
          "description": "FilterChips: channel (WhatsApp/IG/Email) + status (active/waitingDeposit/npsPending/closed) + stage (interested/considering/readyToBook/decidedNo) + helpNeeded + unreadMedia + period (today/yesterday/week/month) + search."
        },
        {
          "id": "inbox-tools-sheet",
          "label": "Adrián tools sheet",
          "capability_id": "vitalia-sales_agent-adrian-3-tools-mvp",
          "description": "AdrianToolsSheet: 3 tools MVP slice 1: `prepaid_payment_check`, `treatment_followup_check`, `medical_consent_request`, `appointment_reschedule_with_doctor`."
        },
        {
          "id": "inbox-proactive-outbound",
          "label": "Proactive outbound",
          "capability_id": "vitalia-sales_agent-adrian-reengagement-tool",
          "description": "ProactiveOutboundModal: gate compliance (`requires_marketing_opt_in` check), template selector (5 WhatsApp templates Meta-approved), bulk a segmento + safety preview."
        },
        {
          "id": "inbox-contact-sidebar",
          "label": "Contact sidebar (paciente actual)",
          "description": "ContactSidebar: ficha paciente in-context: identidad + tratamientos en curso + score + lifecycle + tags + ahora también referrals + NPS."
        },
        {
          "id": "inbox-conversation-thread",
          "label": "Conversation thread (Bubble + Voice + Image)",
          "description": "ConversationThread con MessageBubble + VoiceMessagePlayer + ImageAnalysisCard. Composer area con ComposerAttachButton + ComposerVoiceButton."
        },
        {
          "id": "inbox-state-overlay",
          "label": "State overlay LangGraph (backend)",
          "capability_id": "vitalia-sales_agent-state-overlay-langgraph",
          "description": "Overlay del LangGraph state vitalia-specific: PHI fields scrubbed, dual filter clinic_id, medical guardrails post-state hook."
        },
        {
          "id": "inbox-pause-adrian",
          "label": "Pausar Adrián",
          "description": "PauseAdrianButton + PauseAdrianConfirmModal: detener loop agéntico en una conversación específica (toma control humano sin perder contexto)."
        },
        {
          "id": "inbox-receipt-undo",
          "label": "Action receipt undo",
          "description": "ActionReceiptUndoChip: cada tool execution genera receipt con ventana undo configurable."
        }
      ]
    },
    {
      "id": "brand-studio",
      "label": "Brand Studio (Medical Simplified)",
      "icon": "Building2",
      "route": "/brand-studio",
      "status": "shipped_orphan",
      "description": "Brand Studio simplificado vertical-médico — SOLO 4 secciones habilitadas en `brand.yaml::brand_studio.enabled_sections`. Las 7 disabled (story/strategy/positioning/narrative/personality/communication/authority_vault) están explícitamente OFF porque clínicas operacionales no necesitan ese nivel de elaboración narrativa.",
      "use_cases": [
        "Onboarding inicial: completar identidad mínima",
        "Subir logo + foto consultorios",
        "Cargar equipo de doctores + bio profesional + credenciales",
        "Cargar testimonios + casos pre/post para landings",
        "Datos contacto + horarios para mostrar en booking público"
      ],
      "children": [
        {
          "id": "bs-identity",
          "label": "Identidad",
          "section_slug": "identity",
          "route": "/brand-studio/identity",
          "description": "Datos fundamentales clínica: nombre comercial, nombre legal, slogan/lema, tagline médico, idioma operación, country (drives currency)."
        },
        {
          "id": "bs-contact",
          "label": "Contacto",
          "section_slug": "contact",
          "route": "/brand-studio/contact",
          "description": "Teléfono + WhatsApp Business + email + dirección + horario atención + mapa Google Maps embed."
        },
        {
          "id": "bs-team",
          "label": "Equipo (doctores)",
          "section_slug": "team",
          "route": "/brand-studio/team",
          "description": "Lista de doctores/profesionales. Cada miembro: nombre + foto avatar + cédula profesional/colegio + especialidades + bio + años experiencia + idiomas. Reusable en offer-studio (asignar doctor a tratamiento)."
        },
        {
          "id": "bs-testimonials",
          "label": "Testimonios",
          "section_slug": "testimonials",
          "route": "/brand-studio/testimonials",
          "description": "Repositorio testimonios de pacientes. Cada testimonio: foto antes/después (consent obligatorio para imágenes), texto, rating, tratamiento asociado, fecha. Para landing pública + sales discovery."
        }
      ],
      "disabled_sections_in_brand_yaml": [
        "story (narrativa origen marca — no aplica clínica)",
        "strategy (lead magnets / value-level / ladder — diferente para servicios médicos)",
        "positioning (UVP framework B2B — clínica usa marketing local diferente)",
        "narrative (StoryBrand framework — exceso para vertical médica)",
        "personality (Jung archetype — sales_agent usa archetype fijo `warm_close`)",
        "communication (assets cross-canal — vertical médica usa templates registry)",
        "authority_vault (premios/prensa — diferido a futura iteración premium)"
      ]
    },
    {
      "id": "offer-studio",
      "label": "Offer Studio (Medical Services)",
      "icon": "Briefcase",
      "route": "/offers",
      "status": "shipped_orphan",
      "description": "Offer Studio vertical-médico — usa preset_pack `medical_services_v1`. Wizard de creación específico para servicios médicos con consent gating + medical PDF upload.",
      "use_cases": [
        "Crear servicio nuevo (ej. limpieza dental, blanqueamiento, terapia psicológica online, evaluación psiquiátrica)",
        "Configurar pricing per moneda según country (PE/AR/CO/MX/CL/BR/US)",
        "Asignar doctor responsable del servicio",
        "Definir si requiere consent signature (consent_signature_modal pre-booking)",
        "Subir PDF descripción técnica del servicio (auto-extract Valeria)"
      ],
      "children": [
        {
          "id": "os-list",
          "label": "Catálogo de servicios médicos",
          "route": "/offers",
          "description": "Lista de offers tipo medical_services. Filtros por estado, doctor, especialidad."
        },
        {
          "id": "os-new",
          "label": "Wizard nueva oferta médica",
          "route": "/offers/new",
          "capability_id": "vitalia-offer_studio-medical-services-offer-preset",
          "description": "MedicalServicesOfferWizardSteps + OfferWizardClient. Wizard multi-step específico medical (vs wizard genérico nicolify): datos servicio + duración sesión + sesiones requeridas + precio + doctor asignado + consent required + PDF upload extractor.",
          "components": [
            "ClinicTypePicker (selector tipo clínica del tenant — dental/psychology/psychiatry/wellness)",
            "MedicalServicesOfferWizardSteps (5-7 pasos)",
            "ConsentSignatureModal (si requires_consent_when_offer_marks)",
            "PatientMedicalPdfUpload (drag&drop con Valeria extraction)",
            "DoctorAvatarPicker (asignar doctor del team)",
            "MedicalDisclaimerBanner (legal disclaimer obligatorio)"
          ]
        },
        {
          "id": "os-detail",
          "label": "Detalle servicio",
          "route": "/offers/[id]",
          "description": "Editor de la oferta médica. Form-runtime con secciones específicas medical_services preset (NO las 21 de nicolify generic)."
        }
      ]
    },
    {
      "id": "compliance",
      "label": "Compliance HIPAA-lite",
      "icon": "ShieldCheck",
      "route": "/medical-compliance",
      "status": "shipped_orphan",
      "description": "Dashboard de compliance médico vertical-vitalia. Audit log read-only + stats + filtros + export CSV. Cumple obligaciones Ley 25.326 (AR), LGPD (BR), Ley 1581 (CO), Ley 19.628 (CL), Ley 29733 (PE) + best-practices HIPAA §164.312 referenciadas (sin BAA full).",
      "use_cases": [
        "Auditoría compliance officer per-mes",
        "Detectar accesos sospechosos a PHI (mismo user + N pacientes en 5min)",
        "Export CSV para reportes regulatorios",
        "Tracking de consent signatures por paciente",
        "Verificar dual-filter tenant + clinic enforcement"
      ],
      "children": [
        {
          "id": "comp-stats",
          "label": "Compliance stats cards",
          "capability_id": "vitalia-compliance-compliance-hipaa-lite-audit",
          "description": "ComplianceStatsCards: # accesos PHI período, # consent signatures, # PHI exports, # blocked channel sends, # retention sweeps."
        },
        {
          "id": "comp-events-list",
          "label": "Lista eventos compliance",
          "description": "ComplianceEventRow tabla con severity badge (info/warning/critical), action, user, resource_type, resource_id, timestamp, from_ip."
        },
        {
          "id": "comp-csv-export",
          "label": "Export CSV",
          "description": "generateCsvBlob: download filtered events para reporte regulatorio."
        },
        {
          "id": "comp-hipaa-stack",
          "label": "HIPAA-lite defensive stack (transversal)",
          "capability_id": "vitalia-compliance-hipaa-lite-defensive-stack",
          "description": "Stack defensivo invisible al usuario pero activo en backend: dual filter decorator (tenant + clinic), pgcrypto encryption columns PHI, audit log sync write, sanitize_payload en traces con perfil hipaa_lite, channel guard `ComplianceService.validate_outbound_message`."
        },
        {
          "id": "comp-wpp-templates",
          "label": "WhatsApp template registry (5 templates Meta-approved)",
          "capability_id": "vitalia-compliance-whatsapp-template-registry",
          "templates": [
            { "slug": "recordatorio_proxima_sesion", "kind": "UTILITY", "requires_marketing_opt_in": false, "description": "Recordatorio próxima sesión tratamiento multi-sesión." },
            { "slug": "re_engagement_ausencia", "kind": "MARKETING", "requires_marketing_opt_in": true, "description": "Re-engagement paciente ausente. Gate compliance: si NO opt-in marketing → BLOCKED." },
            { "slug": "nps_post_tratamiento", "kind": "UTILITY", "requires_marketing_opt_in": false, "description": "NPS automation post-tratamiento exitoso." },
            { "slug": "recordatorio_control_doctor", "kind": "UTILITY", "requires_marketing_opt_in": false, "description": "Control médico post-cirugía/post-procedimiento (24h/72h/7d/30d)." },
            { "slug": "invitacion_mantenimiento", "kind": "MARKETING", "requires_marketing_opt_in": true, "description": "Invitación plan mantenimiento post-tratamiento completado." }
          ]
        }
      ]
    },
    {
      "id": "onboarding-wizard",
      "label": "Onboarding wizard (Valeria agéntica)",
      "icon": "Sparkles",
      "route": "/onboarding/wizard",
      "status": "shipped",
      "description": "Wizard agéntico conversacional con Valeria (copilot vertical-médico). 3 pasos canónicos + WizardChatThread + slot tracking. Es el ÚNICO entry point post-signup hasta que el shell-organism se complete.",
      "use_cases": [
        "Nueva clínica completa setup en <30 min via conversación con Valeria",
        "Preview live de landing + WhatsApp mientras se configura",
        "Slot tracker visible (cuántos datos faltan)",
        "Mode selector (full wizard / express / manual)"
      ],
      "children": [
        {
          "id": "onb-step-1",
          "label": "Paso 1 — Identidad clínica",
          "component": "OnboardingStep1Client",
          "capability_id": "vitalia-onboarding-clinic-onboarding-3step",
          "description": "Nombre clínica + tipo clínica (dental/psychology/psychiatry/wellness) + country + currency."
        },
        {
          "id": "onb-step-2",
          "label": "Paso 2 — Equipo + Servicios",
          "component": "OnboardingStep2Client",
          "description": "Doctores principales + servicios mínimos viables para primera landing."
        },
        {
          "id": "onb-step-3",
          "label": "Paso 3 — Activación canales",
          "component": "OnboardingStep3Client",
          "description": "WhatsApp Business + payment gateway (mercadopago/stripe) + landing URL."
        },
        {
          "id": "onb-valeria-chat",
          "label": "Valeria chat thread",
          "capability_id": "vitalia-copilot-valeria-wizard-onboarding-agentic",
          "description": "WizardChatThread: conversación agéntica con Valeria que rellena slots progresivamente. SlotConfirmInline + SlotTrackerSticky persisten visibles el progreso."
        },
        {
          "id": "onb-live-previews",
          "label": "Previews live mientras configuras",
          "description": "LiveLandingSnippetPreview + LiveWhatsAppPreview muestran resultado real conforme se completan slots."
        },
        {
          "id": "onb-close-warning",
          "label": "Close warning modal",
          "description": "CloseSetupWarningModal: confirma cerrar sin guardar (slots transitorios)."
        }
      ]
    }
  ],
  "hidden_or_no_ui_yet": [
    {
      "id": "copilot-valeria-no-rail",
      "label": "Copilot Valeria (NO UI rail aún)",
      "status": "shipped_backend_only",
      "description": "Backend Valeria operativo: medical KB RAG (3 packs: dental, psychology, psychiatry), medical PDF extractors, medical safety guardrails. PERO no existe UI rail/FAB integrado al shell — solo se invoca dentro del wizard onboarding. Gap mayor que `vitalia-shell-organism` debe resolver.",
      "capability_ids": [
        "vitalia-copilot-medical-kb-rag",
        "vitalia-copilot-medical-pdf-extractors",
        "vitalia-copilot-inbox-tools-extensions",
        "vitalia-agentic-medical-safety-guardrails",
        "vitalia-agentic-medical-agentic-tools"
      ]
    },
    {
      "id": "connections-no-ui",
      "label": "Connections (NO UI hub aún)",
      "status": "shipped_backend_only",
      "description": "Backend OAuth Meta + Google Ads operativo, registries medical-vertical operativos. PERO no existe Hub Connections con cards visuales como nicolify. Hoy se conecta via ChannelConnectionWizard inline desde Marketing.",
      "capability_ids": [
        "vitalia-connections-oauth-meta-google-ads",
        "vitalia-connections-registries-medical-vertical"
      ]
    },
    {
      "id": "payment-no-ui",
      "label": "Pagos (NO UI dedicada aún)",
      "status": "shipped_backend_only",
      "description": "Backend payment gateways operativo (mercadopago + stripe_connect + tokenized_recurring para installments medical packages). PERO no existe UI dedicada de configuración + monitoreo + refunds. Link 'Pagos' del sidebar apunta a route inexistente.",
      "capability_id": "vitalia-payment-payment-gateways-latam-recurring"
    },
    {
      "id": "settings-no-ui",
      "label": "Configuración general (NO UI dedicada aún)",
      "status": "not_started",
      "description": "Settings de tenant (locale, plan, equipo interno con roles RBAC, LLM keys, webhooks) NO tienen UI todavía. Today solo brand-studio + onboarding-wizard cubren parte del setup."
    },
    {
      "id": "admin-streamlit-separate",
      "label": "Admin Streamlit (servicio separado, no Next.js)",
      "status": "shipped",
      "deployment": "k8s deployment separado",
      "capability_id": "vitalia-admin-admin-streamlit-service",
      "description": "Panel super-admin Luana en Streamlit (no Next.js). Hostea CRUD tenants + users + clinics. Acceso restringido staff Luana. Ver `vitalia/backend/src/modules/vitalia/admin/`.",
      "capabilities_sublist": [
        "vitalia-admin-tenants-crud",
        "vitalia-admin-users-crud",
        "vitalia-admin-clinics-crud",
        "vitalia-admin-streamlit-tenants-users",
        "vitalia-ops-k8s-admin-deployment"
      ]
    },
    {
      "id": "auth-clerk",
      "label": "Auth Clerk (sign-in / sign-up)",
      "status": "shipped",
      "routes": ["/sign-in/[[...rest]]", "/sign-up/[[...rest]]"],
      "capability_ids": ["vitalia-auth-clerk-middleware", "vitalia-auth-sign-in-sign-up-pages"],
      "description": "Clerk auth pages themed. Sign-up dispara redirect a `/onboarding/wizard`. Sign-in dispara redirect a `/dashboard` (Inicio)."
    },
    {
      "id": "public-landing",
      "label": "Landing pública per-clínica",
      "status": "shipped",
      "routes": ["/public/[clinic-slug]", "/public/[clinic-slug]/booking"],
      "capability_id": "vitalia-public_landing-public-clinic-landing",
      "description": "Landings públicas sin auth: `/public/{slug}` (página marketing) + `/public/{slug}/booking` (widget booking embebido). Slug per-clinic. Backend renderiza con datos brand-studio + offer-studio + booking-widget."
    },
    {
      "id": "marketing-root-route",
      "label": "/marketing (legacy route fuera dashboard)",
      "status": "shipped",
      "description": "Route `/marketing` (sin layout dashboard) — duplicado vs `/marketing` dentro `(dashboard)/`. Posiblemente legacy o landing especial. Pendiente investigar y consolidar."
    }
  ],
  "agentic_layer": {
    "lucas": {
      "role": "Analista marketing — vigila el bowtie funnel + emite recomendaciones priorizadas + ejecuta acciones aprobadas",
      "capability_ids": [
        "vitalia-agentic-lucas-daily-analysis",
        "vitalia-agentic-lucas-recommendation-tool",
        "vitalia-marketing-lucas-stage-recommendations"
      ],
      "backend_location": "vitalia/backend/src/modules/vitalia/agentic/lucas/",
      "cron": "Daily — analiza last 24h + 7d trend + emite recommendations stage-by-stage",
      "ui_surface": "Cards in /marketing page + activity footer"
    },
    "adrian": {
      "role": "Sales agent vertical-médico — conduce conversaciones de cualificación + booking + objection handling",
      "capability_ids": [
        "vitalia-sales_agent-adrian-3-tools-mvp",
        "vitalia-sales_agent-adrian-reengagement-tool",
        "vitalia-sales_agent-inbox-handler-mode-occ",
        "vitalia-sales_agent-medical-guardrails",
        "vitalia-sales_agent-state-overlay-langgraph"
      ],
      "backend_location": "vitalia/backend/src/modules/vitalia/sales_agent/",
      "personality_archetype": "warm_close (default per brand.yaml)",
      "channels": ["whatsapp_business", "manychat_instagram", "email_async", "web_chat"],
      "tools_mvp": ["prepaid_payment_check", "treatment_followup_check", "medical_consent_request", "appointment_reschedule_with_doctor"],
      "guardrails": ["medical_safety_no_diagnosis", "medical_safety_no_prescription", "medical_disclaimer_required", "prompt_injection_block"],
      "ui_surface": "/inbox page + ContactSidebar everywhere"
    },
    "valeria": {
      "role": "Copilot médico — extractor info + asistente onboarding + KB médico RAG",
      "capability_ids": [
        "vitalia-copilot-valeria-wizard-onboarding-agentic",
        "vitalia-copilot-medical-kb-rag",
        "vitalia-copilot-medical-pdf-extractors",
        "vitalia-copilot-inbox-tools-extensions"
      ],
      "backend_location": "vitalia/backend/src/modules/vitalia/copilot/",
      "knowledge_packs": ["medical_kb_dental_v1", "medical_kb_psychology_v1", "medical_kb_psychiatry_v1"],
      "ui_surface": "Wizard onboarding ONLY (NO rail/FAB integrado al shell todavía — gap shell-organism)"
    },
    "eval_goldens": {
      "capability_id": "vitalia-agentic-eval-goldens-slice-1",
      "description": "Goldens dataset slice 1 + eval simulator para validar Adrián fidelity vs voz tenant + medical guardrails."
    }
  },
  "infrastructure_layer": {
    "observability": [
      { "id": "api-health-endpoint", "description": "/api/health endpoint con dependency checks (DB, Redis, Qdrant)." },
      { "id": "otel-sentry-graceful-degradation", "description": "OpenTelemetry + Sentry con graceful degradation (no crash si telemetry caída)." },
      { "id": "vitalia-callback-subclasses", "description": "Callback handler subclases vitalia-specific (PHI sanitization)." }
    ],
    "audit": [
      { "id": "audit-writer-ssot", "description": "Audit log writer con sync write antes response — SSoT cross-módulo." }
    ],
    "platform": [
      { "id": "design-tokens-foundation", "description": "Design tokens vt-* CSS classes en globals.css (sin hsl literals en TSX)." },
      { "id": "migrations-slice-1-schema", "description": "Alembic migrations slice 1 — schema completo PHI tables + booking + treatments + marketing + crm + iam." },
      { "id": "vertical-medical-extension-sdk", "description": "Extension SDK vertical-medical: brand extension + EP-N registries + medical preset packs." }
    ],
    "workers": [
      { "id": "idempotent-cron-arq-scaffold", "description": "Arq workers idempotent scaffold para: Lucas daily analysis, channel_metrics_sync_meta, channel_metrics_sync_google, treatment_followup_workflow, phi_retention_sweep, consent_expiration_check." }
    ],
    "iam": [
      { "id": "iam-scaffold-slice-1", "description": "RBAC scaffold: roles doctor/nurse/admin_clinic/marketing/sales/patient + decorators @require_phi_access." },
      { "id": "luana-core-adoption", "description": "Adopción luana-core-iam package en vitalia (no rebuild)." }
    ],
    "crm": [
      { "id": "crm-scaffold-slice-1", "description": "CRM scaffold per-vertical-medical: contact entity + lifecycle stage + score + tag + segment." },
      { "id": "crm-consent-optout", "description": "Consent management + opt-out flow per channel (marketing vs transactional)." }
    ],
    "clinics": [
      { "id": "clinics-brand-extension", "description": "Clinic entity como brand extension (multi-clinic per tenant)." },
      { "id": "hipaa-dual-filter-decorator", "description": "Decorator @require_dual_filter(tenant_id, clinic_id) enforced en TODOS endpoints PHI." }
    ],
    "fixtures": [
      { "id": "3-clinic-fixture-latam", "description": "Fixture canónico cross-test: 3 clínicas LatAm (PE-dental + AR-psychology + CO-psychiatry) con pacientes + tratamientos + bookings + conversaciones realistas para eval + dev + demo." }
    ],
    "tests": [
      { "id": "playwright-smoke-suite", "description": "Smoke suite Playwright cubriendo flujos críticos vitalia (signup → wizard → primer paciente → primer booking)." }
    ]
  }
}
```

---

## Comparación final vitalia ↔ nicolify (estado 2026-05-21)

### Funcionalidades EXCLUSIVAS vitalia (no existen en nicolify)

1. **HIPAA-lite compliance stack** — dual filter tenant+clinic, audit log sync, pgcrypto, sanitization perfil hipaa_lite, channel guard
2. **Bookings prepagados con advisory locks** — 30% deposit default, anti-double-book SQL-level
3. **Patient entity + medical records** — ficha médica con timeline + PHI dual filter + PDF medical upload
4. **Clinic entity** — multi-clinic per tenant + clinic_id dual filter
5. **Bowtie funnel 5 stages** — adaptado vertical médico (vs Growth Studio 5-stages generic de nicolify)
6. **Attribution matrix 4 origins** — sales_agent + walk_in + phone_manual + proactive_outbound
7. **Lucas daily analysis cron** — agente analista que emite recommendations approve/reject/undo
8. **Referrals leaderboard** — paciente-a-paciente referral tracking
9. **WhatsApp template registry compliance médico** — 5 templates Meta-approved con `requires_marketing_opt_in` gate
10. **Medical safety guardrails** — no_diagnosis, no_prescription, disclaimer_required
11. **Medical agentic tools** — prepaid_payment_check, treatment_followup_check, medical_consent_request, appointment_reschedule_with_doctor
12. **Medical PDF extractors** — Valeria auto-extrae estudios médicos / recetas / lab results
13. **Medical KB RAG packs** — 3 packs (dental + psychology + psychiatry)
14. **3-clinic LatAm fixture canónica** (PE/AR/CO)
15. **Public clinic landing** (`/public/[clinic-slug]`) — sin auth, embebible
16. **Booking widget embebible** (`/public/[clinic-slug]/booking`) — externo sin migrar sitio
17. **Wizard onboarding 3-step agéntico** — Valeria conversacional con live previews
18. **Personality archetype warm_close** — preset sales_agent vertical-médico
19. **5-tab fidelización system** — multisesión, seguimiento médico, mantenimiento, ausencia, NPS
20. **Treatment followup workflow** — automation 24h/72h/7d/30d post-procedimiento
21. **3 modos Adrián** — decide / consulta / yo-escribo (SegmentedControl3Modes)
22. **Inbox modes con tools-sheet vertical-médico** (AdrianToolsSheet con 4 tools MVP)
23. **Consent signature modal** — captura consentimiento informado pre-booking
24. **Streamlit admin panel separado** — k8s deployment dedicado
25. **State overlay LangGraph vitalia** — PHI scrubbing + clinic_id filter + medical guardrails post-state

### Funcionalidades de nicolify NO presentes en vitalia (gaps)

1. **AppSidebar coherente con 5 top-level + collapse + tooltips + mobile sheet** — vitalia tiene Sidebar.tsx con enlaces rotos
2. **Tenant switcher** — vitalia single-tenant por clínica hoy (multi-clinic existe pero NO tenant switching UI)
3. **Copilot rail + FAB persistente** — Valeria existe backend pero sin UI integrada al shell
4. **Brand Studio 10 secciones completas** — vitalia solo 4 (identity/contact/team/testimonials) — by design por simplificación medical
5. **Offer Studio 21 secciones** — vitalia tiene preset medical_services_v1 ≠ 21 generic
6. **Ediciones de oferta** (cohort abril/agosto) — no aplica directamente vertical médico
7. **Growth Studio 5 stages cross-vertical** — vitalia tiene Bowtie 5 stages medical
8. **Closer Studio Inbox/Pipeline/Frozen tabs** — vitalia tiene Inbox dedicado pero NO Pipeline ni Frozen explícitos
9. **CRM hub contactos + segmentación + score + bulk campañas** — vitalia tiene Patients (vertical-médico) en su lugar
10. **Settings 8 sections (3 grupos)** — vitalia no tiene Settings UI todavía
11. **Connections hub 12 providers** — vitalia tiene OAuth backend pero no Hub UI
12. **Audit panel con TraceInspector visual** — vitalia tiene audit log compliance pero no LangGraph trace UI
13. **Authority Vault (premios/prensa)** — disabled explícito en brand.yaml
14. **Narrativa StoryBrand** — disabled explícito en brand.yaml
15. **Múltiples buyer personas detail page** — vitalia no expone esto en UI hoy

### Gap crítico shell-organism

| Capa | Estado vitalia | Acción shell-organism |
|---|---|---|
| **Sidebar reconciliation** | 6 links, 5 rotos | Reescribir Sidebar.tsx con NAV_ITEMS reales del navigation-tree.md |
| **Marketing integration** | Shippeado orphan | Story `vitalia-slice-1-marketing-integration` (idea hoy) → ready |
| **Inbox integration** | Shippeado orphan | Incluir en navigation-tree → Operar → Inbox |
| **Fidelización integration** | Shippeado orphan | Incluir en navigation-tree → Crecer → Fidelización |
| **Compliance integration** | Shippeado orphan | Incluir en navigation-tree → Configurar → Compliance |
| **Brand Studio + Offer Studio integration** | Shippeado orphan | Incluir en navigation-tree → Identidad |
| **Patients/Treatments/Bookings integration** | Shippeado orphan con links rotos | Incluir en navigation-tree → Operar |
| **Valeria rail/FAB persistente** | Backend listo, sin UI | Patrón `CopilotRail` lift a `core/luana-core-ui/` |
| **Settings UI** | No existe | Crear settings shell (story Slice 2) |
| **Connections Hub UI** | No existe | Crear connections shell (story Slice 2) |
| **Pagos UI** | No existe | Crear payments shell (story Slice 2) |

---

## Recordatorios para diseño shell-organism

1. **Reconciliar el sidebar primero.** Los enlaces actuales `/dashboard/{patients,schedule,treatments,payments,copilot}` apuntan a routes que NO existen. El usuario que entra al dashboard hoy ve 5/6 links rotos.
2. **Integrar marketing/inbox/fidelización/compliance al menu.** Son orphan-shipped — todo el trabajo backend+FE está hecho, falta el menu link.
3. **Decidir destino de Valeria rail.** Backend listo. Dos opciones: (a) lift `CopilotRail` desde nicolify a `core/luana-core-ui/` y vitalia consume, (b) implementar rail vitalia-specific. Recomendación → (a) — preventive lift per ADR-008.
4. **Confirmar agrupación 6 padres del `navigation-tree.md`.** Ejemplo de propuesta válida basada en este inventario:
   - **Inicio** → / (dashboard welcome state)
   - **Operar** → Inbox · Pacientes · Agenda · Bookings · Tratamientos · Fidelización
   - **Crecer** → Marketing (bowtie) · Ofertas (medical_services preset)
   - **Identidad** → Brand Studio (4 sections) · Landing pública preview
   - **Análisis** → Marketing dashboard ejecutivo · Compliance audit · Reportes regulatorios
   - **Configurar** → Equipo · Clínica · Conexiones · Pagos · Compliance settings · Plan & facturación · Webhooks
5. **Postpone** lo defer_11bis: multi-site UI, insurance integration, wellness deep coverage.
6. **NO incluir en menu** lo que es invisible (admin Streamlit separado, infra layer, agentic backend-only).

---

## Versionamiento

| Versión | Fecha | Cambio |
|---|---|---|
| 1.0 | 2026-05-21 | Snapshot inicial vitalia state pre-shell-organism. Fuente: 59 capabilities + Sidebar.tsx + 13 routes shipped + brand.yaml + features/. Espejo de `nicolify-feature-inventory.md`. |
