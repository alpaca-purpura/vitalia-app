# Nicolify — Inventario completo de funcionalidades

> **Propósito:** snapshot exhaustivo de todo lo construido en `nicolify/frontend/` + sidebar real (`AppSidebar.tsx`) para informar el rediseño del shell de vitalia (story `vitalia-shell-organism`).
>
> **Fuente verificada:** `nicolify/frontend/src/components/shared/layout/AppSidebar.tsx::getNavItems()` + section-slugs.ts de cada studio + provider registry connections + section-catalog settings + features/ subdirs.
>
> **Fecha snapshot:** 2026-05-21.
>
> **Formato:** JSON-in-MD igual que `navigation-tree.md` pero con `description` + `use_cases` expandidos en cada hoja terminal. Jerarquía respeta el orden REAL del sidebar de nicolify (5 entradas top-level + copilot rail + features transversales).
>
> **Convención status:**
> - `shipped` — construido y vivo en producción nicolify
> - `partial` — UI presente con stubs o gaps funcionales
> - `mock` — solo data mockeada o página placeholder

## Resumen ejecutivo

| Top-level | Children visibles sidebar | Sub-secciones internas | Estado |
|---|---|---|---|
| 1. Brand Studio | 0 (entrada directa a `/identity`) | 10 sections (NavRail interno) + Equipo + Testimonios + Bóveda autoridad + Personas detail | shipped |
| 2. Offer Studio | 0 (entrada directa) | 21 section keys + editor + ediciones + ventas + landing + campaigns + assets | shipped |
| 3. Growth Studio | 5 (stages) | 5 stages × N canales + dashboard ejecutivo + campañas + strategy canvas | shipped |
| 4. Closer Studio (Sales) | 4 (Studio/Contactos/Campañas/Inscripciones) | Inbox + Pipeline + Frozen + Calendario disponibilidad + Detalle conversación | shipped |
| 5. Configuración | 2 (General/Conexiones) | 8 settings sections (3 grupos) + 12 connection providers | shipped |
| Copilot (lateral, no menu) | n/a | Rail+Sidebar+Composer+Cards+History+FAB+Procedimientos+Plan | shipped |
| Auditoría (oculta, dev) | 0 | TraceInspector + ChatTimeline + NodeDetails + UserList | shipped (admin) |
| Admin (oculta, super-admin) | 0 | TenantsList | shipped (admin) |
| Onboarding | 0 | Wizard 7 pasos + paywall | shipped |

---

## JSON tree exhaustivo

```json
{
  "brand": "nicolify",
  "schema_version": "1.0",
  "snapshot_date": "2026-05-21",
  "source": "nicolify/frontend/src/components/shared/layout/AppSidebar.tsx::getNavItems()",
  "sidebar_top_level_count": 5,
  "transversal_layer": {
    "copilot": {
      "label": "Copilot lateral",
      "type": "shell_resident_rail",
      "trigger": "FAB siempre visible (esquina inferior derecha) + atajo teclado + auto-open en flujos",
      "subcomponents": [
        "CopilotFAB",
        "CopilotRail",
        "CopilotSidebar (grid switcher de chats)",
        "CopilotChatPanel",
        "CopilotChatHeader",
        "CopilotHistoryPanel",
        "composer (MessageInput + adjuntos)",
        "messages (UserMessage / AssistantMessage / NavigationCard)",
        "cards (PlanCard / ProcedureProgress / NudgeBanner / MutationUndoButton)",
        "blocks (rich content embebido en el chat)",
        "ActiveJobsPoller (jobs background largos)",
        "ContextChips + ContextRotBanner (qué entidad está viendo el agente)"
      ],
      "description": "Asistente conversacional persistente en todo el dashboard. Recibe contexto del path actual (qué sección/entidad está viendo el usuario), ejecuta procedimientos largos (extractor de brand, generación landing, follow-up campañas), navega al usuario con tarjetas accionables y mantiene historial cross-sesión.",
      "use_cases": [
        "Completar campos de Brand Studio por entrevista conversacional",
        "Extraer información de una URL/PDF y rellenar offer-studio",
        "Diagnosticar por qué una campaña no convierte",
        "Generar copy de email/WhatsApp en lote",
        "Disparar jobs largos (sync canales, regenerar embeddings) con barra de progreso embebida"
      ]
    },
    "tenant_switcher": {
      "label": "Switcher de tenant",
      "type": "shell_header_widget",
      "location": "header sidebar (top, sobre el avatar Clerk)",
      "description": "Selector dropdown para usuarios con acceso a múltiples tenants. Mantiene el path actual al cambiar (mismo studio + otro tenant)."
    },
    "user_button": {
      "label": "UserButton (Clerk)",
      "type": "shell_footer_widget",
      "location": "footer sidebar",
      "description": "Avatar + dropdown Clerk con: perfil, organización, sign-out, mode toggle (light/dark)."
    }
  },
  "tree": [
    {
      "id": "brand-studio",
      "label": "Brand Studio",
      "icon": "Building2",
      "route": "/[tenantId]/brand-studio/identity",
      "status": "shipped",
      "description": "Punto único de configuración de la marca del tenant. Layout Finder estilo macOS de 3 columnas (NavRail + sub-rail por sección + editor form-runtime). Cada sección expone fields auto-rellenables por Valeria (copilot extractor).",
      "use_cases": [
        "Onboarding inicial: completar identidad mínima viable para que sales_agent tenga voz",
        "Editar tono/voz post-launch cuando el negocio pivota",
        "Subir y reemplazar logo/paleta",
        "Cargar equipo + credenciales + testimonios para landing pública",
        "Definir buyer personas múltiples para segmentación de campañas"
      ],
      "children": [
        {
          "id": "bs-identity",
          "label": "Identidad",
          "icon": "Sparkles",
          "route": "/[tenantId]/brand-studio/identity",
          "status": "shipped",
          "description": "Datos fundamentales: nombre comercial, slogan, propósito, misión, visión, valores. Bloque inicial del onboarding.",
          "use_cases": ["Primer paso onboarding", "Re-brand", "Sincronizar con catálogo legal"]
        },
        {
          "id": "bs-estilo",
          "label": "Estilo de comunicación",
          "icon": "Mic",
          "route": "/[tenantId]/brand-studio/estilo",
          "status": "shipped",
          "description": "Voz y tono de marca: arquetipo Jung (12 arquetipos), 3-pilar engine (Carácter / Comunicación / Conexión), frases 'así hablo / así no hablo', emojis permitidos. SSoT que compila el bloque BRAND_VOICE del prompt slot 5 del sales_agent (cache prefix).",
          "use_cases": [
            "Configurar voseo/tuteo y mensajes regulares del agente",
            "Cambiar arquetipo cuando rebrandeas (ej. Magic→Sage)",
            "Bloquear léxico ofensivo o cliché por industria"
          ]
        },
        {
          "id": "bs-legal",
          "label": "Legal",
          "icon": "Scale",
          "route": "/[tenantId]/brand-studio/legal",
          "status": "shipped",
          "description": "Razón social, RUC/RFC/CUIT, dirección fiscal, términos y condiciones, política de privacidad, política de devoluciones. Se embebe en landings + emails transaccionales + footer.",
          "use_cases": ["Cumplimiento legal LatAm", "Datos para facturación electrónica", "Política de reembolso visible en checkout"]
        },
        {
          "id": "bs-visuals",
          "label": "Visuales",
          "icon": "Palette",
          "route": "/[tenantId]/brand-studio/visuals",
          "status": "shipped",
          "description": "Logo (light/dark/icon), paleta (primary/secondary/accent/foreground/background), tipografías (heading/body), grid/spacing baseline, imágenes de marca (hero/about/og:image).",
          "use_cases": ["Generar landing on-brand sin diseñador", "Asegurar consistencia visual cross-campañas", "Brand kit descargable para terceros"]
        },
        {
          "id": "bs-contact",
          "label": "Contacto",
          "icon": "Phone",
          "route": "/[tenantId]/brand-studio/contact",
          "status": "shipped",
          "description": "Datos públicos: WhatsApp comercial, email atención, dirección oficina, horarios, redes sociales (IG/FB/TikTok/YouTube/LinkedIn). Se sincroniza con landings + footer + sales_agent.",
          "use_cases": ["Bloque footer landings", "WhatsApp click-to-chat en CTAs", "Datos NAP para SEO local"]
        },
        {
          "id": "bs-methodology",
          "label": "Metodología",
          "icon": "BookOpen",
          "route": "/[tenantId]/brand-studio/methodology",
          "status": "shipped",
          "description": "Frameworks propietarios: metodología de trabajo, fases del proceso, pilares del método, diferenciadores técnicos. Carga sección Value Stack del offer-studio.",
          "use_cases": ["Diferenciar metodología propia vs competencia en landing", "Justificar precio premium", "Bloque 'cómo trabajamos' del sales_agent en discovery"]
        },
        {
          "id": "bs-story",
          "label": "Historia",
          "icon": "Scroll",
          "route": "/[tenantId]/brand-studio/story",
          "status": "shipped",
          "description": "Origin story de la marca: por qué empezamos, momento bisagra, dolor que vimos en el mercado, transformación que provocamos. Narrativa StoryBrand compatible.",
          "use_cases": ["Bloque About Us", "Newsletter de bienvenida", "Discurso del agente en early-funnel"]
        },
        {
          "id": "bs-positioning",
          "label": "Posicionamiento",
          "icon": "Target",
          "route": "/[tenantId]/brand-studio/positioning",
          "status": "shipped",
          "description": "UVP (unique value proposition), categoría de mercado (jobs-to-be-done), competidores directos/indirectos, why-us en 3 puntos, anti-positioning (lo que NO somos).",
          "use_cases": ["Headline landing", "Pitch del sales_agent vs objeción 'por qué tú y no X'", "Brief para campañas paid"]
        },
        {
          "id": "bs-narrative",
          "label": "Narrativa StoryBrand",
          "icon": "Drama",
          "route": "/[tenantId]/brand-studio/narrative",
          "status": "shipped",
          "description": "Framework StoryBrand de Donald Miller: hero (cliente) + problem (interno/externo/filosófico) + guide (tu marca) + plan (3 pasos) + call to action + success / failure stakes. Drives el copy de toda la landing y de los emails de nurturing.",
          "use_cases": ["Rewriter automático de landings", "Secuencia email de 5 toques", "Pitch deck B2B"]
        },
        {
          "id": "bs-communication-assets",
          "label": "Assets de comunicación",
          "icon": "FileText",
          "route": "/[tenantId]/brand-studio/communication-assets",
          "status": "shipped",
          "description": "Repositorio de assets reutilizables: bios cortas (Twitter/IG/LinkedIn), bios largas (web/pitch deck), bios corporativas, templates de respuestas frecuentes, scripts de objeciones comunes.",
          "use_cases": ["Generar firma email", "Bio para entrevistas/podcasts", "Templates FAQ atendidos por el agente"]
        },
        {
          "id": "bs-publico",
          "label": "Público objetivo",
          "icon": "Users",
          "route": "/[tenantId]/brand-studio/publico",
          "status": "shipped",
          "description": "Lista de buyer personas. Cada persona es entidad propia con sub-página detalle (`/publico/persona/[personaId]`) editable inline con autosave. Incluye: demografía, JTBD, dolores, miedos, sueños, objeciones, canales preferidos, fuentes de información.",
          "use_cases": ["Segmentar campañas paid por persona", "Adaptar voz del sales_agent según persona detectada", "Personalizar landings A/B por persona"]
        },
        {
          "id": "bs-team",
          "label": "Equipo",
          "icon": "UsersRound",
          "route": "/[tenantId]/brand-studio/team",
          "status": "shipped",
          "description": "Lista de miembros del equipo público. Cada miembro es entidad propia con sub-página (`/team/instance/[instanceId]`): foto, nombre, rol, bio, credenciales, links (LinkedIn/web), expertise tags. Drive directo del bloque 'Quiénes somos' de landings + about page + assignments en offers (instructor).",
          "use_cases": ["Bloque equipo en landing", "Asignar instructor a curso cohort_based", "Brief para periodistas/PR"]
        },
        {
          "id": "bs-testimonials",
          "label": "Testimonios",
          "icon": "MessageSquareQuote",
          "route": "/[tenantId]/brand-studio/testimonials",
          "status": "shipped",
          "description": "Repositorio cross-brand de testimonios (texto + foto + video + estrella). Cada testimonio es entidad con detail (`/testimonials/instance/[instanceId]`): autor, cargo, empresa, foto, cita, rating, link al case study, fecha, productos/servicios asociados. Reutilizable en cualquier landing.",
          "use_cases": ["Social proof landing", "Carousel testimonios en email", "Sales objection handler (cuando prospect dice 'no sé si funciona')"]
        },
        {
          "id": "bs-authority",
          "label": "Bóveda de autoridad",
          "icon": "ShieldCheck",
          "route": "/[tenantId]/brand-studio/authority",
          "status": "shipped",
          "description": "Repositorio de credenciales acumuladas: prensa, premios, certificaciones, casos publicados, menciones, podcasts, charlas, papers. Cada item es entidad con detail (`/authority/instance/[instanceId]`): título, tipo, fuente, link, fecha, screenshot/PDF. Genera el bloque 'Como visto en' + barras de logos.",
          "use_cases": ["Bloque autoridad landing premium", "PR kit para nuevos medios", "Diferenciar tier de precio (autoridad vs commodity)"]
        }
      ]
    },
    {
      "id": "offer-studio",
      "label": "Offer Studio",
      "icon": "Briefcase",
      "route": "/[tenantId]/offer-studio",
      "status": "shipped",
      "description": "Catálogo de ofertas + editor con 21 secciones por oferta. Cada oferta tiene archetype (COHORT_BASED_COURSE, PRODUCTIZED_SERVICE, SUBSCRIPTION_MEMBERSHIP, EVENT, COACHING_1ON1, etc.) que activa secciones específicas. Workspace de 3 vistas: lista de ofertas → detalle oferta → editor sección.",
      "use_cases": [
        "Crear/editar producto/servicio del tenant",
        "Generar landing automática on-brand vinculada a la oferta",
        "Versionar la oferta (ediciones: cohorte abril, cohorte agosto)",
        "Lanzar campaña de captación vinculada a una edición específica",
        "Reusar assets cross-edición (video pitch, instructor, FAQ)"
      ],
      "children": [
        {
          "id": "os-list",
          "label": "Catálogo de ofertas",
          "icon": "Grid3x3",
          "route": "/[tenantId]/offer-studio",
          "status": "shipped",
          "description": "Lista master de ofertas del tenant con filtros por estado (draft/live/archived), archetype, fecha modificación. Acción crear nueva oferta dispara wizard de archetype-picker.",
          "use_cases": ["Vista admin de catálogo", "Bulk archive/unarchive", "Búsqueda por nombre/SKU"]
        },
        {
          "id": "os-detail",
          "label": "Detalle de oferta",
          "icon": "FileText",
          "route": "/[tenantId]/offer-studio/offer/[id]",
          "status": "shipped",
          "description": "Vista resumen de una oferta + tabs internas (Editor / Ediciones / Ventas / Landing / Assets / Campaigns). Es el hub de todas las acciones sobre la oferta.",
          "use_cases": ["Overview rápido pre-lanzamiento", "Diagnosticar qué falta para ir live"]
        },
        {
          "id": "os-editor",
          "label": "Editor 21 secciones",
          "icon": "Pencil",
          "route": "/[tenantId]/offer-studio/offer/[id]/editor",
          "status": "shipped",
          "description": "NavRail finder de 21 section keys con auto-completado vía Valeria. Cada sección renderiza schema Pydantic v2 → form-runtime con autosave on-change.",
          "use_cases": [
            "Rellenar todas las dimensiones del producto antes de lanzar",
            "Mantener oferta sincronizada con cambios de precio o programa",
            "Auto-extracción desde PDF/URL existente"
          ],
          "leaves_21_sections": [
            { "slug": "identity", "label": "Identidad", "description": "Nombre comercial, SKU, descripción corta, descripción larga, idioma, formato (digital/presencial/híbrido), nivel (beginner/intermediate/advanced)." },
            { "slug": "strategy", "label": "Estrategia", "description": "Lead magnet (sí/no), tier-up offer, mecanismos de upsell/cross-sell, posicionamiento en ladder de la marca." },
            { "slug": "psychology", "label": "Psicología", "description": "Dolor antes / sueño después, transformación promised, miedos a desactivar, urgencia justificada (no fake-scarcity)." },
            { "slug": "promise", "label": "Promesa", "description": "Big idea / one-line promise + claims específicos medibles + frame del antes/después." },
            { "slug": "value_stack", "label": "Stack de valor", "description": "Listado bullet de qué incluye + valor monetario subjetivo de cada item + total stacked vs precio final." },
            { "slug": "instructors", "label": "Instructores", "description": "Asignar miembros del equipo a la oferta. Sub-página por instructor (`/editor/instructors/[instructorId]`) con bio adaptada al contexto del programa." },
            { "slug": "knowledge", "label": "Conocimiento", "description": "Lo que aprenderá / lo que sabrá hacer / lo que dominará. Niveles de competencia (Bloom)." },
            { "slug": "closing", "label": "Cierre", "description": "Garantía, política de reembolso, riesgo invertido, urgencia + escasez, CTAs primario/secundario." },
            { "slug": "product_details", "label": "Detalles de producto", "description": "Para PRODUCT archetype: dimensiones, materiales, peso, stock, variantes, SKU físico." },
            { "slug": "subscription_details", "label": "Detalles suscripción", "description": "Para SUBSCRIPTION archetype: ciclo (mensual/anual), trial, dunning, beneficios por nivel." },
            { "slug": "gallery", "label": "Galería", "description": "Imágenes hero + mockups + screenshots + behind-the-scenes. Drive de galería landing." },
            { "slug": "event_details", "label": "Detalles del evento", "description": "Para EVENT archetype: fecha, hora, sede física/url Zoom, agenda, sponsors." },
            { "slug": "pricing", "label": "Precios", "description": "Tiers (single/dual/triple), precios + moneda + impuesto inc/excl, cuotas, planes de pago, lifetime vs subscription, descuentos." },
            { "slug": "program_details", "label": "Detalles del programa", "description": "Para COURSE archetype: módulos + lecciones + duración + plataforma LMS, certificación, recursos descargables." },
            { "slug": "service_details", "label": "Detalles del servicio", "description": "Para SERVICE archetype: SLA, alcance, entregables, no-incluye, tiempo respuesta." },
            { "slug": "resources", "label": "Recursos", "description": "Bonos descargables, plantillas, comunidad acceso, soporte." },
            { "slug": "faq", "label": "Preguntas frecuentes", "description": "Lista de FAQ propia de la oferta con sub-página detalle (`/editor/faq/[faqId]`)." },
            { "slug": "testimonials", "label": "Testimonios oferta", "description": "Selección curada del repositorio brand-studio scoped a esta oferta. Sub-página detalle (`/editor/testimonials/[testimonialId]`)." },
            { "slug": "portfolio", "label": "Portafolio / casos", "description": "Casos publicables de uso real de la oferta con resultados medibles." },
            { "slug": "location", "label": "Ubicación", "description": "Para presencial: dirección, mapa embed, accesibilidad, parking, transporte." },
            { "slug": "platform_details", "label": "Detalles de plataforma", "description": "Para digital: plataforma (Teachable/Hotmart/Kajabi/propia), credenciales onboarding, link acceso post-compra." }
          ]
        },
        {
          "id": "os-editions",
          "label": "Ediciones",
          "icon": "Layers",
          "route": "/[tenantId]/offer-studio/offer/[id]/editions",
          "status": "shipped",
          "description": "Versiones de la oferta en el tiempo (cohorte abril 2026, cohorte agosto 2026, generación octubre 2026). Cada edición tiene fechas, capacidad, precio especial, landing propia, campaign propia, assets propios.",
          "use_cases": [
            "Lanzar 3 cohortes/año del mismo curso sin duplicar la oferta",
            "Sold out cohorte A → reabrir lista de espera B",
            "Comparar performance ventas A vs B"
          ],
          "leaves_per_edition": [
            { "slug": "[editionId]", "label": "Detalle edición", "description": "Resumen + estado (open/closed/sold_out) + métricas." },
            { "slug": "landing", "label": "Landing edición", "description": "Landing pública vinculada a esta edición (URL única, slug)." },
            { "slug": "ventas", "label": "Ventas edición", "description": "Métricas de ventas scoped a esta edición (visitas, conversión, ingreso, refund)." },
            { "slug": "campaigns", "label": "Campañas edición", "description": "Lista de campañas paid/orgánicas alimentando esta edición." },
            { "slug": "assets", "label": "Assets edición", "description": "Pieces visuales propias de la edición (variantes hero, copies A/B)." }
          ]
        },
        {
          "id": "os-ventas",
          "label": "Ventas oferta",
          "icon": "ShoppingBag",
          "route": "/[tenantId]/offer-studio/offer/[id]/ventas",
          "status": "shipped",
          "description": "Métricas agregadas cross-ediciones de la oferta: total enrollments, ingreso, refund rate, NPS, breakdown por canal."
        },
        {
          "id": "os-campaigns",
          "label": "Campañas oferta",
          "icon": "Megaphone",
          "route": "/[tenantId]/offer-studio/offer/[id]/campaigns",
          "status": "shipped",
          "description": "Lista de campañas asociadas a la oferta (cross-ediciones). Acceso al detail de cada campaña en growth-studio."
        },
        {
          "id": "os-assets",
          "label": "Assets oferta",
          "icon": "Image",
          "route": "/[tenantId]/offer-studio/offer/[id]/assets",
          "status": "shipped",
          "description": "Repositorio de assets propios de la oferta (cover, video pitch, OG image, infografías). Cross-ediciones."
        }
      ]
    },
    {
      "id": "growth-studio",
      "label": "Growth Studio",
      "icon": "Megaphone",
      "route": "/[tenantId]/growth-studio",
      "status": "shipped",
      "description": "Dashboard de métricas de growth y ejecución de campañas. Modelo de funnel de 5 stages (Atracción → Nutrición → Ventas → Adopción → Expansión) con métricas por canal y por stage. Cada stage tiene página propia + sub-página por canal + acción 'agregar canal' + detalle widget.",
      "use_cases": [
        "Dashboard ejecutivo CMO/founder",
        "Diagnosticar bottleneck del funnel (¿dónde se cae la conversión?)",
        "Comparar performance Meta Ads vs Google Ads vs orgánico",
        "Ejecutar campañas paid (lanzar/pausar/optimizar)",
        "Auditar attribution multi-touch",
        "Strategy canvas (mapa visual del funnel completo)"
      ],
      "children": [
        {
          "id": "gs-overview",
          "label": "Dashboard ejecutivo",
          "icon": "BarChart3",
          "route": "/[tenantId]/growth-studio",
          "status": "shipped",
          "description": "Vista resumen tier 0+1: KPIs principales del funnel (visitas, leads, ventas, MRR), tarjetas por stage con drilldown, banner conexión-health (canales caídos), strategy canvas mini.",
          "use_cases": ["Pulso diario rápido", "Sync con stakeholders", "Detectar canal caído"]
        },
        {
          "id": "gs-atraccion",
          "label": "Atracción",
          "icon": "Magnet",
          "route": "/[tenantId]/growth-studio/atraccion-captura",
          "status": "shipped",
          "description": "Stage 1: tráfico + impresiones + alcance + CTR. Canales típicos: Meta Ads (FB/IG), Google Ads, YouTube, TikTok, SEO orgánico, blog.",
          "use_cases": ["Comparar CPM/CPC por canal", "Optimizar mejor canal de Top-of-Funnel", "Detectar saturación creative"],
          "leaves_channels": [
            { "slug": "[channelSlug]", "label": "Detalle canal atracción", "description": "Métricas drilldown del canal: impresiones, CPM, CTR, click, costo. Widget de campaign panel para gestionar campañas paid." }
          ]
        },
        {
          "id": "gs-nutricion",
          "label": "Nutrición y oportunidad",
          "icon": "Sprout",
          "route": "/[tenantId]/growth-studio/nutricion-oportunidad",
          "status": "shipped",
          "description": "Stage 2: leads cualificados + opt-ins + open-rate email + WhatsApp engagement + warming. Canales típicos: MailerLite, ManyChat, WhatsApp, Telegram.",
          "use_cases": ["Optimizar secuencia email de bienvenida", "A/B subject lines", "Detectar canal de nurturing más alto rendimiento"],
          "leaves_channels": [
            { "slug": "[channelSlug]", "label": "Detalle canal nutrición", "description": "Open rate, CTR email, opt-out, replies WhatsApp, response time del agente." }
          ]
        },
        {
          "id": "gs-ventas",
          "label": "Ventas",
          "icon": "ShoppingCart",
          "route": "/[tenantId]/growth-studio/ventas",
          "status": "shipped",
          "description": "Stage 3: conversaciones cualificadas → propuestas → cierre. Métricas: close rate, AOV, sales cycle, win/loss, agentic-call-volume.",
          "use_cases": ["Forecast pipeline", "Optimizar prompt del sales_agent", "Detectar tipologías cliente que no convierten"],
          "leaves_channels": [
            { "slug": "[channelSlug]", "label": "Detalle canal ventas", "description": "Conversaciones → conversiones por canal con drilldown a Closer Studio." }
          ]
        },
        {
          "id": "gs-adopcion",
          "label": "Adopción",
          "icon": "UserCheck",
          "route": "/[tenantId]/growth-studio/adopcion",
          "status": "shipped",
          "description": "Stage 4: onboarding → activación → primer uso → retención early. Para SaaS: time-to-value, day-7-retention, feature adoption.",
          "use_cases": ["Detectar caída en onboarding", "Optimizar email day-0/1/3", "Identificar usuarios estancados"],
          "leaves_channels": [
            { "slug": "[channelSlug]", "label": "Detalle canal adopción", "description": "Funnels de activación + retención cohortes." }
          ]
        },
        {
          "id": "gs-expansion",
          "label": "Expansión y evangelización",
          "icon": "Rocket",
          "route": "/[tenantId]/growth-studio/expansion-evangelizacion",
          "status": "shipped",
          "description": "Stage 5: upsell + cross-sell + referrals + NPS + evangelistas. Loop de crecimiento orgánico.",
          "use_cases": ["Identificar evangelistas para programa referral", "Triggers upsell por uso", "Medir NPS por cohorte"],
          "leaves_channels": [
            { "slug": "[channelSlug]", "label": "Detalle canal expansión", "description": "Tasa de upsell, referrals enviados/aceptados, NPS por canal." }
          ]
        },
        {
          "id": "gs-campanas",
          "label": "Campañas",
          "icon": "Megaphone",
          "route": "/[tenantId]/growth-studio/campanas",
          "status": "shipped",
          "description": "Vista cross-stage de TODAS las campañas activas/pausadas/cerradas. Filtros por canal, oferta, estado, fecha.",
          "use_cases": ["Auditar gasto total ads", "Pausar campañas duplicadas", "Comparar campañas históricas mismo período año pasado"]
        },
        {
          "id": "gs-channel",
          "label": "Detalle canal (cross-stage)",
          "icon": "Cable",
          "route": "/[tenantId]/growth-studio/channel/[channelSlug]",
          "status": "shipped",
          "description": "Vista 360° de un canal específico (ej. Meta Ads) atravesando los 5 stages. Health del canal, todas sus campañas, todas sus métricas, todos sus assets.",
          "use_cases": ["Auditar Meta Ads end-to-end", "Decidir si pausar canal por bajo ROI", "Asignar presupuesto trimestral por canal"]
        }
      ]
    },
    {
      "id": "closer-studio",
      "label": "Closer Studio",
      "icon": "CalendarCheck",
      "route": "/[tenantId]/sales",
      "status": "shipped",
      "description": "Workspace de operación de ventas: inbox conversacional unificado (WhatsApp/IG/FB/web widget) + pipeline kanban + contactos CRM + campañas WhatsApp + inscripciones eventos. Es el 'centro de operaciones' del Adrián (sales_agent).",
      "use_cases": [
        "Operador humano interviniendo conversaciones del agente",
        "Vista pipeline para forecast",
        "CRM con segmentación + scoring",
        "Lanzar broadcast campaign WhatsApp post-aprobación template",
        "Gestionar inscripciones eventos (sold-out / waitlist)"
      ],
      "children": [
        {
          "id": "cs-studio",
          "label": "Studio (Inbox+Pipeline+Frozen)",
          "icon": "Headset",
          "route": "/[tenantId]/sales/studio/inbox",
          "status": "shipped",
          "description": "3 vistas tabuladas: Inbox (conversaciones activas), Pipeline (kanban por stage), Frozen (conversaciones pausadas). Operador puede tomar control de cualquier conversación del agente.",
          "use_cases": [
            "Tomar control conversación cuando agente escala (low confidence)",
            "Mover conversación a pipeline stage manualmente",
            "Congelar conversación sin perder contexto"
          ],
          "leaves_studio_views": [
            { "slug": "inbox", "label": "Inbox unificado", "description": "Lista de conversaciones cross-canal (WhatsApp/IG/FB/web) con filtros (unread, agente, asignado, oferta). Threading con MessageBubble + ContactSidebar (info contacto + lifecycle stage + score + campaign tag)." },
            { "slug": "pipeline", "label": "Pipeline kanban", "description": "Tablero por stage del funnel comercial (lead/qualified/proposal/negotiation/won/lost). Cards arrastrables. Para forecast." },
            { "slug": "frozen", "label": "Frozen", "description": "Conversaciones pausadas / archivadas / out-of-scope. Conserva contexto reactivable." }
          ]
        },
        {
          "id": "cs-contactos",
          "label": "Contactos (CRM hub)",
          "icon": "Users",
          "route": "/[tenantId]/sales/contactos",
          "status": "shipped",
          "description": "CRM unificado de contactos. Lista con filtros (canal, lifecycle stage, score, tag, segmento), bulk actions, segmentos guardados.",
          "use_cases": [
            "Construir segmento 'leads cualificados últimos 30d' para email broadcast",
            "Score scoring leads automático",
            "Identity merge cross-canal (mismo lead WhatsApp+email)",
            "Detail page del contacto con timeline cross-canal"
          ]
        },
        {
          "id": "cs-campanas",
          "label": "Campañas WhatsApp/Email",
          "icon": "Megaphone",
          "route": "/[tenantId]/sales/campanas/nuevo",
          "status": "shipped",
          "description": "Lanzar campaña outbound a segmentos del CRM. Plantillas pre-aprobadas WhatsApp Business API + emails masivos.",
          "use_cases": [
            "Broadcast 'reapertura inscripciones' a leads warming",
            "Sequence email re-engagement (90d sin abrir)",
            "Lifecycle campaign por stage"
          ],
          "leaves_campanas": [
            { "slug": "nuevo", "label": "Wizard nueva campaña", "description": "Wizard de 4 pasos: audience (segmento) → template (WhatsApp aprobado / email) → schedule (now/scheduled) → review + send." },
            { "slug": "[id]", "label": "Detalle campaña", "description": "Stats live (enviados/entregados/abiertos/respondidos/opt-out), gestionar lifecycle (start/pause/stop)." }
          ]
        },
        {
          "id": "cs-enrollments",
          "label": "Inscripciones",
          "icon": "ClipboardList",
          "route": "/[tenantId]/sales/enrollments",
          "status": "shipped",
          "badge": "NEW (expira 2026-10-17)",
          "description": "Tabla de inscripciones a eventos / cohortes / ediciones de cursos. Stado (confirmed/pending/refunded/no-show), bulk export, ticket QR.",
          "use_cases": ["Lista de asistentes evento", "Refund por no-show", "Re-engage waitlist al sold out"]
        },
        {
          "id": "cs-mock",
          "label": "Sales mock",
          "icon": "FlaskConical",
          "route": "/[tenantId]/sales/mock",
          "status": "mock",
          "description": "Vista demo con data mockeada para presentaciones / sales pitch. No tocar en prod."
        },
        {
          "id": "cs-agenda",
          "label": "Agenda (booking page)",
          "icon": "CalendarCheck",
          "route": "/[tenantId]/sales/page (root)",
          "status": "shipped",
          "description": "Calendario de disponibilidad del tenant + tipos de evento (Calendly-like). Genera link público (`/book/[slug]`) para que leads reserven discovery call/onboarding/consult.",
          "use_cases": [
            "Generar booking link para incluir en email/WhatsApp del agente",
            "Configurar disponibilidad recurrente",
            "Tipos de evento (discovery 15min / consult 30min / strategy 60min)"
          ]
        }
      ]
    },
    {
      "id": "configuracion",
      "label": "Configuración",
      "icon": "Settings",
      "route": "/[tenantId]/settings",
      "status": "shipped",
      "description": "Settings del tenant en 3 grupos (Principal / Ventas / Desarrolladores) + entry directa a Conexiones desde sidebar.",
      "children": [
        {
          "id": "cfg-general",
          "label": "General",
          "icon": "SlidersHorizontal",
          "route": "/[tenantId]/settings",
          "status": "shipped",
          "group": "principal",
          "description": "Datos del tenant: nombre legal, locale (timezone + currency + idioma), plan activo, retention policy, opciones globales.",
          "use_cases": ["Cambio moneda al expandir país", "Toggle features experimentales", "Configurar retention compliance"]
        },
        {
          "id": "cfg-perfil",
          "label": "Perfil personal",
          "icon": "User",
          "route": "/[tenantId]/settings/perfil",
          "status": "shipped",
          "group": "principal",
          "description": "Perfil del usuario actual: avatar, nombre, email, notificaciones, MFA. Wrapper sobre UserButton Clerk."
        },
        {
          "id": "cfg-equipo",
          "label": "Equipo",
          "icon": "Users",
          "route": "/[tenantId]/settings/equipo",
          "status": "shipped",
          "group": "principal",
          "description": "Miembros del tenant + roles (owner/admin/editor/viewer). Invitaciones email + revocación accesos.",
          "use_cases": ["Onboarding nuevo empleado", "Quitar acceso a ex-empleado", "Asignar rol editor a freelance"]
        },
        {
          "id": "cfg-perfil-negocio",
          "label": "Perfil de negocio",
          "icon": "Building2",
          "route": "/[tenantId]/settings/perfil-negocio",
          "status": "shipped",
          "group": "principal",
          "description": "Datos comerciales del negocio: industria, tipo de negocio, B2B/B2C/B2B2C, # empleados, # clientes activos, AOV típico. Feed para módulos de extraction y benchmarking."
        },
        {
          "id": "cfg-llm-keys",
          "label": "LLM API Keys",
          "icon": "Key",
          "route": "/[tenantId]/settings/llm-keys",
          "status": "shipped",
          "group": "principal",
          "description": "BYO keys para proveedores LLM (OpenAI/Anthropic/DeepSeek/Kimi/...) si el tenant prefiere usar sus créditos en vez del pool Luana. Routing automático.",
          "use_cases": ["Enterprise con compliance estricto", "Tenant con créditos LLM propios", "Test de modelo nuevo"]
        },
        {
          "id": "cfg-agenda",
          "label": "Agenda",
          "icon": "CalendarClock",
          "route": "/[tenantId]/settings/agenda",
          "status": "shipped",
          "group": "ventas",
          "description": "Configuración de disponibilidad cross-tipos de evento: buffer entre reuniones, anti-double-book, working hours, override días no laborables."
        },
        {
          "id": "cfg-pagos",
          "label": "Pagos",
          "icon": "CreditCard",
          "route": "/[tenantId]/settings/pagos",
          "status": "shipped",
          "group": "ventas",
          "description": "Pasarelas conectadas (Stripe / MercadoPago / Culqi / PayU / OpenPay), monedas activas, comisiones, checkout templates, refund policy.",
          "use_cases": ["Conectar Stripe LatAm para suscripciones", "Habilitar checkout MercadoPago AR", "Setear refund window por archetype"]
        },
        {
          "id": "cfg-webhooks",
          "label": "Webhooks",
          "icon": "Webhook",
          "route": "/[tenantId]/settings/webhooks",
          "status": "shipped",
          "group": "desarrolladores",
          "description": "Webhooks salientes hacia sistemas tenant (Zapier/Make/CRM externo). Eventos disponibles (enrollment.created, conversation.handoff, refund.issued, etc.), URL destino, secret HMAC, retry policy, log de últimos hits.",
          "use_cases": ["Sync con CRM externo del cliente", "Disparar Zapier desde eventos Luana", "Auditar fallas integración"]
        },
        {
          "id": "cfg-copilot-telegram",
          "label": "Copilot Telegram",
          "icon": "Send",
          "route": "/[tenantId]/settings/copilot/telegram",
          "status": "shipped",
          "group": "principal",
          "description": "Configurar bot Telegram personal del operador para chatear con Valeria (copilot) desde el móvil — operación remota del dashboard."
        },
        {
          "id": "cfg-conexiones",
          "label": "Conexiones (Hub)",
          "icon": "Cable",
          "route": "/[tenantId]/connections",
          "status": "shipped",
          "group": "principal",
          "description": "Hub de integraciones con 12 providers. Cada provider tiene detalle con OAuth/credenciales, status sincronización, configuración específica.",
          "use_cases": [
            "Onboarding integraciones día 1",
            "Refrescar token caducado",
            "Diagnosticar canal sin datos",
            "Activar/desactivar provider"
          ],
          "leaves_providers": [
            { "id": "meta", "label": "Meta Business Suite", "description": "Facebook + Instagram + Ads + Pixel + Conversions API. Ingesta de impresiones/CTR/conversiones + retargeting." },
            { "id": "shopify", "label": "Shopify", "description": "Sync productos + pedidos + analytics. Para clientes con tienda Shopify (no-vertical Retailly aún, pero usable hoy en nicolify B2B agencias)." },
            { "id": "whatsapp", "label": "WhatsApp Business API", "description": "Mensajería directa con clientes. Routing de mensajes al sales_agent. Templates pre-aprobadas para broadcast." },
            { "id": "google-workspace", "label": "Google Workspace", "description": "Gmail + Calendar + servicios Google. Auth única para todas las apps de Google del tenant." },
            { "id": "google-analytics", "label": "Google Analytics", "description": "Métricas web (GA4): sesiones, fuentes, conversiones, eventos custom." },
            { "id": "youtube", "label": "YouTube", "description": "Canal, videos, analytics, subscriber growth. Feed de canal evangelización + content marketing." },
            { "id": "manychat", "label": "ManyChat", "description": "Chatbots y automatización de mensajes (Messenger/IG)." },
            { "id": "telegram", "label": "Telegram", "description": "Bot de mensajería y notificaciones. Canal mobile del operador." },
            { "id": "mailerlite", "label": "MailerLite", "description": "Email marketing + newsletters + automations. Drive de nurturing." },
            { "id": "gmail", "label": "Gmail (envío)", "description": "Envío de correos transaccionales / personalizados desde la dirección del tenant." },
            { "id": "google-calendar", "label": "Google Calendar", "description": "Agenda y reuniones. Sync con booking page del Closer Studio." },
            { "id": "tiktok", "label": "TikTok", "description": "Videos cortos y ads. Status: coming_soon (placeholder)." },
            { "id": "webwidget", "label": "Web Widget", "description": "Chat widget embebible en el sitio web del tenant. Punto de captura de leads." }
          ]
        }
      ]
    }
  ],
  "hidden_top_level": [
    {
      "id": "audit",
      "label": "Auditoría (dev/admin)",
      "icon": "Activity",
      "route": "/[tenantId]/audit",
      "status": "shipped",
      "description": "Panel de observabilidad LangGraph: TraceInspector con timeline de tools invocados, ChatTimeline con turnos del agente, NodeDetailsPanel con prompts + completions + cost. UserList para filtrar trazas por usuario. Acceso restringido (admin/dev).",
      "use_cases": ["Debug por qué el agente devolvió respuesta extraña", "Investigar costo elevado de un turno", "Replay conversación completa para post-mortem"]
    },
    {
      "id": "admin-tenants",
      "label": "Admin tenants (super-admin)",
      "icon": "Shield",
      "route": "/[tenantId]/admin/tenants",
      "status": "shipped",
      "description": "Super-admin: lista de TODOS los tenants del sistema con búsqueda + acceso impersonate. Solo para staff Luana.",
      "use_cases": ["Soporte cliente", "Onboarding manual de tenant enterprise", "Auditoría compliance"]
    },
    {
      "id": "brand-settings-legacy",
      "label": "Brand settings (legacy)",
      "icon": "Settings",
      "route": "/[tenantId]/brand-settings",
      "status": "partial",
      "description": "Página legacy pre-Brand-Studio. Pendiente deprecar / migrar."
    },
    {
      "id": "avatars",
      "label": "Avatars editor",
      "icon": "ImagePlus",
      "route": "/[tenantId]/avatars/[id]/edit",
      "status": "shipped",
      "description": "Sub-página de edición de avatares de team members (escalable a futuro: avatares de personajes, productos, etc.)."
    },
    {
      "id": "onboarding",
      "label": "Onboarding wizard",
      "icon": "Sparkles",
      "route": "/[tenantId]/onboarding",
      "status": "shipped",
      "description": "Wizard inicial post-signup para nuevos tenants: crear tenant, configurar locale, completar brand mínimo, conectar primer canal, primer copilot job."
    },
    {
      "id": "preview",
      "label": "Preview landing pública",
      "icon": "Eye",
      "route": "/[tenantId]/preview",
      "status": "shipped",
      "description": "Vista previa de la landing pública del tenant antes de publicar al subdominio."
    },
    {
      "id": "book-public",
      "label": "Booking page público",
      "icon": "Calendar",
      "route": "/book/[slug]",
      "status": "shipped",
      "description": "Página pública de booking que ven los leads para reservar discovery call. Sin auth."
    },
    {
      "id": "visit-public",
      "label": "Visit (landing pública)",
      "icon": "Globe",
      "route": "/visit",
      "status": "shipped",
      "description": "Renderizado server-side de landings públicas del tenant. Sin auth."
    },
    {
      "id": "_public-landings",
      "label": "Landings públicas (raw)",
      "icon": "Globe",
      "route": "/_public",
      "status": "shipped",
      "description": "Bucket de routes públicas crudas para subdominios brand."
    },
    {
      "id": "playground",
      "label": "Playground (dev)",
      "icon": "FlaskConical",
      "route": "/playground",
      "status": "mock",
      "description": "Sandbox de componentes para desarrollo. No expuesto en prod."
    },
    {
      "id": "sign-in-sign-up",
      "label": "Sign-in / Sign-up (Clerk)",
      "icon": "LogIn",
      "route": "/sign-in /sign-up",
      "status": "shipped",
      "description": "Páginas Clerk auth. Sin custom UI más allá del themed."
    },
    {
      "id": "forbidden",
      "label": "Forbidden",
      "icon": "Ban",
      "route": "/forbidden",
      "status": "shipped",
      "description": "Página 403 cuando user no tiene acceso a un tenant."
    },
    {
      "id": "global-error-404",
      "label": "Errors (404/500)",
      "icon": "AlertCircle",
      "route": "/not-found.tsx /global-error.tsx",
      "status": "shipped",
      "description": "Páginas de error globales con branding."
    }
  ],
  "transversal_features_not_in_menu": {
    "notifications": {
      "components": ["NotificationCenter", "NotificationPanel", "NotificationCard"],
      "description": "Centro de notificaciones in-app (bell icon en header sidebar): jobs terminados, conexiones caídas, leads warming, campañas que requieren acción, errores tools.",
      "use_cases": ["Awareness async (no perderse jobs largos)", "Alertas operativas (canal X caído)"]
    },
    "tenant_domains": {
      "description": "Configurar custom subdomain del tenant (cliente.luana.app) o custom domain (cliente.com). Auto-DNS verification + cert.",
      "use_cases": ["White-label custom domain", "Subdominio profesional para landings"]
    },
    "tenant_profile": {
      "description": "Capa SSoT del perfil del tenant que alimenta locale, branding, plan, feature flags al resto de features."
    }
  }
}
```

---

## Notas de diseño para `vitalia-shell-organism`

### Gaps reales entre nicolify y vitalia (estado snapshot 2026-05-21)

| Funcionalidad nicolify | Estado vitalia hoy | Acción shell-organism |
|---|---|---|
| AppSidebar 5-top-level + collapse + tooltips + mobile sheet | NO existe shell coherente | Lift a `core/luana-core-ui/` patrón `AppShell` |
| BrandStudioNavRail (FinderColumn 260px + sub-rail + chevron) | NO existe (vitalia tiene brand-studio stub) | Lift `FinderColumn` + `NavRail` primitivos a core-ui |
| Copilot rail + FAB persistente + ActiveJobsPoller | NO existe Valeria embebida en shell vitalia | Patrón `CopilotRail` core-ui + brand extension |
| TenantSwitcher | NO existe (vitalia es single-tenant por clínica hoy) | Postpone — agendar Slice 3 |
| Tab-style navigation interna (Studio: Inbox/Pipeline/Frozen) | NO existe en vitalia | Pattern `StudioTabs` core-ui |
| Lazy-loaded section pages | NO en vitalia (todo eager hoy) | Adoptar pattern factory `createSectionPage()` |

### Diferencias estructurales vitalia vs nicolify

Vitalia necesita **menos** entradas top-level (clínicas son operacionales, no studios creativos) pero **agrupaciones diferentes**:

- Nicolify: Brand Studio + Offer Studio + Growth Studio + Closer Studio + Configuración (5)
- Vitalia (propuesta navigation-tree.md): Inicio + Operar + Crecer + Identidad + Análisis + Configurar (6)

La equivalencia conceptual:

| Nicolify | Vitalia equivalente |
|---|---|
| Brand Studio + Offer Studio | Identidad → Brand Studio + Catálogo de tratamientos |
| Growth Studio | Crecer → Marketing + Ofertas/promociones |
| Closer Studio Inbox | Operar → Inbox |
| Closer Studio Pipeline | Operar → Pipeline |
| Closer Studio Contactos | Operar → Pacientes (vertical-specific) |
| Growth Studio dashboard | Análisis → Dashboard ejecutivo + KPIs clínicos |
| Configuración | Configurar (paridad) |
| Inicio (NO existe explícito en nicolify, es `/`) | Inicio (explícito como entry vitalia) |

### Pendiente confirmar contigo

1. ¿La sección **Inscripciones** (eventos/cohortes) de nicolify tiene análogo en vitalia? (no parece — vitalia es citas médicas, no eventos).
2. ¿La sección **Ediciones** del offer-studio aplica a tratamientos médicos? (probablemente NO — un tratamiento no tiene "cohorte abril", pero podría tener "promoción quincena 1").
3. ¿Vitalia necesita **Authority Vault** (publicaciones + premios)? Sí muy probable para diferenciación clínica premium.
4. ¿**Bóveda de Testimonios** scoped por tratamiento? Sí, alta prioridad.
5. ¿**Buyer personas múltiples**? Vitalia hoy tiene 3-clinic-fixture-latam — múltiples personas por clínica es plausible (paciente joven estética + paciente tercera edad rehabilitación).

---

## Versionamiento

| Versión | Fecha | Cambio |
|---|---|---|
| 1.0 | 2026-05-21 | Snapshot inicial pre-shell-organism design. Fuente: AppSidebar.tsx + section-slugs.ts + provider-registry. |
