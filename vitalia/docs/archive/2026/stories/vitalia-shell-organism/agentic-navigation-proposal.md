<!-- voseo-allowed: internal architecture exploration and design proposal, partial obsolete after revision -->

# Vitalia — Propuesta de árbol agéntico (Empleados IA)

> **Cambio de paradigma:** dejamos atrás la metáfora "studios" / "módulos" y adoptamos **empleados IA** como organizadores de primer nivel. La clínica contrata un equipo virtual; cada miembro tiene rol, color, foto y un dominio del negocio. El menú es ese equipo.
>
> **Fecha:** 2026-05-21
> **Versión:** 1.0 propuesta inicial — abierta a edición manual por Chris (formato lego)
> **Insumos:** `vitalia-feature-inventory.md` + `nicolify-feature-inventory.md` + brief agentes (5 PNGs en `/home/chalreme/Trabajo/Vitalia/agentes/`) + brand.yaml

---

## 0. Decisiones de plataforma (resolver primero)

### 0.1 Dónde viven las imágenes de los agentes (R2 vs servidor)

**Recomiendo R2 Cloudflare** — los 5 agentes son **assets de plataforma** (no del tenant), pero R2 es la opción correcta igualmente. Razones:

| Criterio | R2 (recomendado) | Servidor / `frontend/public` |
|---|---|---|
| Egress cost | **Gratis** (única razón ya gana) | Incluido pero compite con SSR | 
| CDN edge | Global automático vía Cloudflare | Vercel/Vps depende del host |
| Cache invalidation | Headers + Workers on-the-fly | Build-time stale |
| Image optimization | Cloudflare Images / transform on demand (resize, AVIF, WebP) | Next.js Image OK pero re-deploys cada cambio |
| Workflow para crear nuevo agente | Subir 1 PNG → URL inmediata | Commit + redeploy |
| Compartir cross-brands futuras | Idem URL desde nicolify/comunify | Mirror manual |

**Bucket propuesto:**

```
luana-assets-platform                  ← NUEVO bucket R2 (assets plataforma)
└── agents/
    ├── valeria/
    │   ├── thumbnail.png              (300x300 cuadrado)
    │   ├── full.png                   (1024x* transparente)
    │   ├── thumbnail-32.webp          (autogen)
    │   ├── thumbnail-64.webp
    │   ├── thumbnail-128.webp
    │   └── full-512.webp
    ├── adrian/   ...
    ├── lucas/    ...
    ├── camila/   ...
    ├── mateo/    ...
    └── lisa/     ...                  ← (si se ratifica como agente 6º)

luana-assets-tenants                   ← bucket existente (assets per-tenant)
└── tenant-{id}/...
```

URL pattern: `https://assets.luana.app/agents/valeria/thumbnail-64.webp`

**Acción concreta** (cuando ratifiques): script `scripts/r2/upload-platform-agents.sh` que toma `/home/chalreme/Trabajo/Vitalia/agentes/**/*.png` y los sube a R2 con prefix correcto + genera webp variants.

### 0.2 Tenant switcher siempre visible

**Ubicación propuesta:** esquina superior derecha del shell (top-bar), antes del avatar Clerk. Componente nuevo `<TenantSwitcher />` con dropdown que muestra:
- Tenants donde el user tiene acceso
- Branding (logo/color) del tenant activo
- Atajo "Ver todos los tenants" para super-admin
- Mantiene path al cambiar (`/inbox` en tenant A → `/inbox` en tenant B)

### 0.3 Toggle claro/oscuro

**Ubicación propuesta:** dropdown bajo el avatar Clerk (junto a Cerrar sesión). Componente `<ThemeToggle />` con 3 estados: `light` / `dark` / `system`. Persistido en localStorage + sincronizado a `tenant_user_preferences.theme`.

### 0.4 Modo agéntico (vista por defecto)

Layout 50/50 (ya prototipado en `dual-mode-shell.html`):

```
┌────────────────────────────────────────────────────────────────────┐
│ TopBar: [Logo Vitalia] [TenantSwitcher▾] ········· [🔍] [🌓] [👤▾] │
├──────────────────────────────┬─────────────────────────────────────┤
│ Chat con Valeria (50%)       │ Tabs agentes (6) - panel agente     │
│                              │ 🟣Lisa 🖤Lucas 🔵Adrián 🟣Valeria  │
│ ┌──────────────────────────┐ │ 🟦Camila 🟡Mateo                    │
│ │ Historial (colapsado ◀▶) │ ├─────────────────────────────────────┤
│ ├──────────────────────────┤ │ Sub-tabs nivel 2 del agente activo  │
│ │ Conversación actual      │ │ • Tratamientos • Doctores • etc.    │
│ │                          │ ├─────────────────────────────────────┤
│ │ Mensajes...              │ │ Contenido nivel 3 (átomo actual)    │
│ │                          │ │ Mini-ribbon contextual del átomo    │
│ │ [Input + 📎 + 🎙]        │ │ ↑ siguiente paciente ↓ anterior     │
│ └──────────────────────────┘ │                                     │
└──────────────────────────────┴─────────────────────────────────────┘
```

**Vista web pura:** alternativa para sesiones largas (operadores que quieren ver más datos). El chat colapsa a rail derecho 64px con FAB para reabrir. URLs deep-link iguales en ambos modos.

---

## 1. Mapeo de agentes → módulos (top-level del menú)

⚠️ **CONFLICTO DETECTADO Y A RATIFICAR** ⚠️

Tu brief listó **5 agentes** (Valeria/Adrián/Lucas/Camila/Mateo) pero asignaste **6 módulos** introduciendo el nombre **"Lisa"** para "Mi Clínica" — y simultáneamente diste a Valeria el módulo "Operar" cuando su rol descrito calza exacto con "Mi Clínica" (brand + offer ladder).

**Opciones (elige cuando edites el doc):**

| Opción | Mi Clínica | Operar | Configurar | Total agentes |
|---|---|---|---|---|
| **A — Lisa nueva (6ª agente)** | 🆕 Lisa (crear PNG + rol formal) | Valeria | Mateo | 6 |
| **B — Valeria dual-role (5 agentes)** | Valeria (foco marca/oferta) | Valeria (foco operación) | Mateo | 5 (Valeria 2 sombreros) |
| **C — Valeria solo Mi Clínica + nuevo agente Operar** | Valeria | 🆕 Otro (¿Marina? ¿Sofía?) | Mateo | 6 (uno nuevo) |
| **D — Tu propuesta original verbatim** | Lisa | Valeria | (sin asignar) | 6 (con Mateo libre) |

Mi **recomendación = Opción A** (Lisa nueva). Razón: separar el rol de "estratega de marca/portafolio comercial" (Lisa, perfil ejecutivo-consultora) del rol de "coordinadora de operación día-a-día" (Valeria, perfil asistente clínica). Son trabajos mentales muy distintos y el usuario se beneficia de hablar con la persona correcta.

A continuación armo el árbol con **Opción A** asumida. Si eliges otra, solo renombras la tab top-level — el contenido del árbol no cambia.

### Mapa final asumido

| Agente | Color | Módulo (tab top-level) | Foco | Imagen |
|---|---|---|---|---|
| **Lisa** | `#7b2d91` (púrpura) | **Mi Clínica** | Marca + oferta comercial + escalera de valor + equipo médico + compliance | (pendiente diseñar) |
| **Lucas** | `#111111` (negro) | **Atraer** | Growth + campañas + atribución + contenido + tendencias | `agents/lucas/` |
| **Adrián** | `#01b2f8` (cian) | **Vender** | CRM + inbox + cualificación + cierre + reservas prepagadas | `agents/adrian/` |
| **Valeria** | `#7b2d91` (púrpura — ¿conflicto con Lisa? cambiar) | **Operar** | Agenda diaria + atención paciente + tratamientos en curso + tareas | `agents/valeria/` |
| **Camila** | `#180d95` (azul-violeta profundo) | **Mantener** | Post-venta + seguimiento + NPS + reactivación + comunidad + referidos | `agents/camila/` |
| **Mateo** | `#fee209` (amarillo) | **Configurar** | Sistema + tenant + conexiones + apariencia + integraciones + tecnología | `agents/mateo/` |

> **Nota color:** Lisa y Valeria ambos `#7b2d91` provoca confusión visual en las tabs. Recomiendo cambiar uno. Propuesta: Lisa `#7b2d91` (púrpura ejecutivo) / Valeria `#10b981` (verde clínico — color de bienestar/salud) o cualquier paleta que prefieras al diseñar a Lisa.

---

## 2. Árbol completo (máximo 3 niveles, hojas dinámicas marcadas)

Convención lectura:

- **N1** = tab top-level (agente)
- **N2** = sub-sección (rail/tabs internos del agente)
- **N3** = vista hoja (página accesible desde menú directo)
- **N3-dyn** = vista hoja accesible vía deep-link / selección de item (NO está en el menú — se llega por click desde una lista en N3)
- 🧱 = componente lego (origen: nicolify | vitalia existing | nuevo)
- 🤖 = acción que Valeria-chat puede ejecutar autónoma desde WhatsApp/voz

---

### 🟣 N1 — Mi Clínica (Lisa)

> "Soy Lisa. Te ayudo a armar una marca que enamore y una cartera de tratamientos que crezca con cada paciente."

#### N2.1 — Identidad de marca

| N3 | Descripción | 🧱 Componentes lego |
|---|---|---|
| Identidad básica | Nombre comercial, razón social, slogan, propósito, especialidad principal (dental/estética/psicología/wellness) | 🧱 nicolify `bs-identity` + vitalia `BrandStudioSectionClient` |
| Visuales | Logo (light/dark/icon), paleta, tipografías, fotos de fachada/consultorio | 🧱 nicolify `bs-visuals` |
| Contacto público | Teléfono, WhatsApp Business, email, dirección, horarios, mapa, redes sociales | 🧱 vitalia `bs-contact` |
| Historia & misión | Por qué empezamos, misión médica, valores. Lo que la clínica defiende | 🧱 nicolify `bs-story` (adaptado — no narrativa StoryBrand completa) |

🤖 Valeria puede: "Cambia el horario del sábado a 9-13" / "Sube esta foto como logo nueva" / "Actualiza el WhatsApp comercial a +51 999 999 999"

#### N2.2 — Doctores y equipo

| N3 | Descripción | 🧱 Componentes lego |
|---|---|---|
| Lista de doctores | Tabla con foto, nombre, especialidad, colegiatura, idiomas. Botón "Invitar doctor". | 🧱 nicolify `bs-team` + vitalia `DoctorAvatarPicker` |
| Especialidades & servicios atendidos | Mapa doctor → tratamientos que ofrece. Drive del flow "asignar doctor a booking". | 🧱 nuevo — derivado del team + offer mapping |
| **N3-dyn** Detalle doctor | Ficha profesional: bio larga, credenciales (PDFs colegiatura), foto profesional, calendario disponibilidad, NPS personal, pacientes activos | 🧱 nicolify `bs-team/instance/[id]` + vitalia `AppointmentsCalendarClient` scoped |

🤖 Valeria puede: "Agrega a la Dra. María Castro como ortodoncista, su WhatsApp es +51..." / "Pausa la agenda del Dr. Pedro la próxima semana"

#### N2.3 — Tratamientos & servicios (offer ladder médico)

> 🔬 **Escalera de valor clínico** — Metodología propuesta adaptada a sector salud/belleza/wellness (sintetiza Treatment Value Pyramid odontológica + Care Continuum estética + Patient Journey ladder medical general).

**5 niveles de la escalera:**

```
   ╲                                                    ╱
    ╲ Nivel 5: Programa integral premium (high-ticket) ╱
     ╲ Ej: "Sonrisa de por vida" 12 meses              ╱
      ╲ Bundle blanqueamiento + ortodoncia + control  ╱
       ╲────────────────────────────────────────────╱
        ╲ Nivel 4: Plan de mantenimiento recurrente╱
         ╲ Ej: Membresía dental anual              ╱
          ╲ Membresía facial trimestral           ╱
           ╲────────────────────────────────────╱
            ╲ Nivel 3: Plan de tratamiento     ╱
             ╲ multi-sesión (paquete)         ╱
              ╲ Ej: 4 limpiezas / 6 IPL      ╱
               ╲────────────────────────── ╱
                ╲ Nivel 2: Tratamiento     ╱
                 ╲ puntual (core service) ╱
                  ╲ Ej: Limpieza simple  ╱
                   ╲────────────────── ╱
                    ╲ Nivel 1: Consulta╱
                     ╲ inicial         ╱
                      ╲ (lead magnet)  ╱
                       ╲ Ej: Evaluación gratis o $20  ╱
                        ╲──────────────────────────╱
```

Cada tratamiento creado en el sistema se mapea a UNO de estos 5 niveles. La maximización de CLTV es la métrica reina (mover paciente de N1 → N5 a lo largo del tiempo).

| N3 | Descripción | 🧱 Componentes lego |
|---|---|---|
| Catálogo de tratamientos | Grid de servicios con filtros por nivel, especialidad, doctor, estado (activo/draft) | 🧱 vitalia `/offers` list + medical filters |
| Escalera de valor | Vista visual de los 5 niveles con cobertura del tenant (cuántos tratamientos hay en cada nivel + gaps) | 🧱 NUEVO — diseño piramidal interactivo |
| Bundles & promociones | Combinar varios tratamientos en paquete (ej. "Programa Sonrisa Premium") | 🧱 NUEVO + adaptado de nicolify `os-editor/value_stack` |
| Recursos & assets compartidos | Imágenes pre/post, videos explicativos, PDFs informativos reutilizables cross-tratamientos | 🧱 nicolify `os-assets` + vitalia `PatientMedicalPdfUpload` |
| **N3-dyn** Crear/editar tratamiento (wizard) | Wizard medical_services con: identidad servicio, nivel ladder, duración sesión, sesiones requeridas, doctor responsable, precio, requiere consent, descripción, fotos pre/post | 🧱 vitalia `MedicalServicesOfferWizardSteps` + `OfferWizardClient` + `ConsentSignatureModal` |
| **N3-dyn** Detalle tratamiento | Vista resumen + métricas (cuántos vendidos, NPS, conversión booking, doctor) + tabs editor/promos/landing | 🧱 vitalia `/offers/[id]` adaptado |

🤖 Valeria puede: "Crea un servicio nuevo: limpieza dental, 30 min, $45 PEN" / "Sube el plan integral 'Sonrisa Total' como nivel 5, incluye ortodoncia + blanqueamiento + 3 controles" / "Cuáles servicios no tengo en nivel 4? Sugiéreme ideas"

#### N2.4 — Testimonios & casos pre/post

| N3 | Descripción | 🧱 Componentes lego |
|---|---|---|
| Testimonios texto/video | Repositorio con foto autor, cita, rating, tratamiento asociado. Curaduría para landing | 🧱 nicolify `bs-testimonials` + vitalia testimonials section |
| Casos pre/post (galería médica) | Imágenes antes/después con **consent gating obligatorio**. Filtros por tratamiento + doctor + paciente anonimizado | 🧱 nuevo — específico vertical médico, requiere `ConsentSignatureModal` lock |
| **N3-dyn** Detalle testimonio | Edit ficha, ver permisos publicación, expiración consent | 🧱 nicolify `bs-testimonials/instance/[id]` |

🤖 Valeria puede: "Pide testimonio a la paciente Ana Pérez post-tratamiento ortodóncico" / "Marca el caso de Luis como NO publicable, ya no quiere que aparezca"

#### N2.5 — Compliance & legal (PHI HIPAA-lite)

| N3 | Descripción | 🧱 Componentes lego |
|---|---|---|
| Consentimientos firmados | Lista de consents per paciente per tratamiento, estado (vigente/expirado/revocado), descarga PDF | 🧱 vitalia `ConsentSignatureModal` historial + nuevo grid |
| Audit log HIPAA-lite | Quién accedió a qué PHI, cuándo, desde dónde. Filtros + export CSV | 🧱 vitalia `/medical-compliance` `CompliancePageClient` + `ComplianceEventRow` |
| Templates WhatsApp Meta-approved | Registry de 5 templates aprobados con `requires_marketing_opt_in` flag | 🧱 vitalia `whatsapp-template-registry` |
| Política & términos | Términos, privacidad, política reembolso, declaraciones HIPAA-lite. Para footer landings | 🧱 nicolify `bs-legal` |

🤖 Valeria puede: "Genérale el consentimiento de blanqueamiento a Pedro Ramírez antes de su cita del viernes" / "Qué pacientes tienen consentimientos expirados?"

#### N2.6 — Landing pública (preview & publish)

| N3 | Descripción | 🧱 Componentes lego |
|---|---|---|
| Preview landing | Vista preview tal como verá el paciente. URL pública `app.vitalialat.com/clinica-slug`. Botón publicar | 🧱 vitalia `/public/[clinic-slug]` + nicolify `os-detail/landing` |
| Configurar widget booking | Snippet JS embebible en sitio externo del cliente, configuración estilos | 🧱 vitalia `booking-widget-embed` |
| Reseñas Google/Yelp | Pull de reseñas externas para mostrar en landing pública | 🧱 NUEVO — Lucas overlap (¿mover a Mantener?) |

---

### 🖤 N1 — Atraer (Lucas)

> "Soy Lucas. Transformo desconocidos en pacientes interesados. Vivo en TikTok, IG, Google y SEO. Si está pasando algo viral, yo lo detecto antes."

#### N2.1 — Embudo de atracción (top of bowtie)

| N3 | Descripción | 🧱 Componentes lego |
|---|---|---|
| Mapa de atracción | Visual SVG bowtie izquierda: 3 etapas (Atracción → Calificación → Reserva). KPI hero por etapa. Selector período (7d/30d/90d) | 🧱 vitalia `MarketingBowtieSVG` + `MarketingLayout` (PARTIDO en 2: top-side aquí, post-side en Camila) |
| Performance por canal | Comparativa Meta vs Google vs TikTok vs orgánico. CPM, CPC, CTR, leads cualificados, costo por lead | 🧱 vitalia `ChannelBreakdownRow` + nicolify `gs-channel` |
| Recomendaciones de Lucas | Cola de acciones priorizadas: pausar canal X, lanzar campaña Y, ajustar audiencia Z. Approve/reject/undo | 🧱 vitalia `LucasStageRecommendationsCard` + `LucasApprovalModal` + `LucasUndoChip` |
| Tendencias del rubro | Feed de tendencias virales actuales en salud/belleza (Lucas las trae). Inspiración para creativos | 🧱 NUEVO — Lucas mining trends |

🤖 Valeria coordina con Lucas: "Lucas, qué canal está rindiendo mejor este mes?" / "Pausá Meta Ads, está caro" / "Sugiere 3 ideas de contenido para esta semana"

#### N2.2 — Campañas de atracción

| N3 | Descripción | 🧱 Componentes lego |
|---|---|---|
| Lista de campañas activas | Tabla con plataforma, presupuesto, leads generados, costo por lead, ROAS, estado (activa/pausada/finalizada) | 🧱 vitalia `marketing` adaptado + nicolify `gs-campanas` |
| Lanzar campaña nueva | Wizard: objetivo (atracción/branding/engagement) → plataforma (Meta/Google/TikTok) → audiencia → creatividad → presupuesto → schedule → review | 🧱 NUEVO — wizard cross-canal con Lucas asistente |
| Biblioteca de creatividades | Pool de assets (videos, imágenes, copy) reutilizables. Tagged por tipo (testimonio, antes/después, educativo, oferta) | 🧱 NUEVO + reusable de Mi Clínica § casos pre/post |
| **N3-dyn** Detalle campaña | KPIs en tiempo real, breakdown placement (FB feed vs IG reels vs TikTok for you), gestión lifecycle, A/B variants | 🧱 nicolify `gs-channel/[channelSlug]` adaptado + vitalia `CampaignDetailClient` |

🤖 Valeria + Lucas: "Lanza campaña de blanqueamiento dental, $300 USD, Meta + Google, audiencia LatAm 25-45" / "Cuánto llevamos gastado este mes en ads?"

#### N2.3 — Contenido orgánico & redes

| N3 | Descripción | 🧱 Componentes lego |
|---|---|---|
| Calendar de contenido | Vista calendario con posts programados/publicados cross-canal (IG/TikTok/FB/YouTube/blog) | 🧱 NUEVO — content calendar (referencias content-hunter skill) |
| Generador de creativos (IA) | Lucas genera ideas de posts adaptados a tendencias actuales + voz de marca. Output: copy + sugerencia visual | 🧱 NUEVO — Lucas content tool |
| Programador multi-canal | Schedule + publish a IG/FB/TikTok desde una vista (usa connections) | 🧱 NUEVO + connections WhatsApp Business overlap |
| Hashtags & SEO local | Recomendaciones de hashtags + keywords SEO local por tipo de clínica + ciudad | 🧱 NUEVO — Lucas SEO module |

🤖 Valeria + Lucas: "Genera 3 ideas para reels esta semana sobre ortodoncia invisible" / "Publica este antes/después en IG y TikTok mañana 10am"

#### N2.4 — Conexiones publicitarias

| N3 | Descripción | 🧱 Componentes lego |
|---|---|---|
| Meta Business (FB + IG + Ads) | Conexión OAuth, pixel, audiencias custom, sync conversions API | 🧱 vitalia `oauth-meta-google-ads` + nicolify `cfg-conexiones meta` |
| Google Ads + Analytics | OAuth Google Workspace, GA4 events, Ads campaigns sync | 🧱 vitalia `oauth-meta-google-ads` (Google part) |
| TikTok Ads | OAuth + ads manager sync | 🧱 NUEVO |
| YouTube | Canal stats + subscribers + nuevos videos | 🧱 nicolify `youtube` provider |

> 📌 Nota: Las conexiones "operativas" (WhatsApp Business, pagos, Google Calendar) NO viven aquí — viven en **Configurar (Mateo)**. Aquí solo las conexiones específicamente publicitarias.

---

### 🔵 N1 — Vender (Adrián)

> "Soy Adrián. Convierto interesados en pacientes. Cualifico, persuado, cierro. Manejo WhatsApp, IG, mail y web. Si hay un lead en el inbox, ya lo estoy atendiendo."

#### N2.1 — Inbox (conversaciones)

| N3 | Descripción | 🧱 Componentes lego |
|---|---|---|
| Inbox unificado | Lista de conversaciones cross-canal (WhatsApp/IG/Mail/Web). Filtros multi: canal, status, stage, ayuda-pide, audio/imagen sin abrir, período. Search | 🧱 vitalia `InboxLayout` + `ConversationListPanel` + `FilterChips` (TODA la feature ya existe) |
| Vista con sub-componentes activos | El inbox lleva embebido: `SegmentedControl3Modes` (Adrián decide/consulta/yo-escribo), `AdrianToolsSheet`, `PauseAdrianButton`, `ProactiveOutboundModal`, `ContactSidebar` | 🧱 vitalia inbox completo |
| **N3-dyn** Conversación abierta | Thread con bubble + voice + image analysis + composer + voice + attach. ContactSidebar paciente in-context | 🧱 vitalia `ConversationThread` + `ImageAnalysisCard` + `VoiceMessagePlayer` |

🤖 Valeria coordina con Adrián: "Adrián, ese paciente nuevo del WhatsApp, agéndale consulta inicial el martes 3pm" / "Pausa Adrián en la conversación de María, yo le escribo"

#### N2.2 — Pipeline (kanban + leads)

| N3 | Descripción | 🧱 Componentes lego |
|---|---|---|
| Tablero pipeline | Kanban por stage médico: `interesado` → `considerando` → `listo_para_reservar` → `reservado` → `cita_asistida` → `decidido_no`. Cards arrastrables | 🧱 nicolify `cs-studio/pipeline` adaptado (renombrar stages medical) |
| Lista de leads/contactos | CRM scoped a leads (NO pacientes activos — eso vive en Operar). Score, lifecycle stage, tag, último contacto | 🧱 vitalia `crm-shared` + nicolify `cs-contactos` |
| Segmentos guardados | "Leads warming últimos 30d", "Pacientes que pidieron blanqueamiento", etc. | 🧱 nicolify `crm-hub` `CreateSegmentDialog` |
| **N3-dyn** Detalle contacto/lead | Timeline cross-canal, score con drivers, intentos contacto, próxima acción Adrián | 🧱 nicolify `crm-hub` `ContactDetailContent` |

🤖 Valeria + Adrián: "Cuántos leads warming tengo de blanqueamiento?" / "Mueve a Pedro al stage 'listo para reservar'"

#### N2.3 — Reservas prepagadas

| N3 | Descripción | 🧱 Componentes lego |
|---|---|---|
| Lista de reservas | Estado: pending_deposit / confirmed / cancelled / no_show. Filtros doctor/tratamiento/fecha | 🧱 vitalia `/bookings` |
| Calificación automática (reglas) | Reglas de scoring que aplica Adrián: medical fit + intent + ability-to-pay + canal | 🧱 NUEVO — visualizador reglas (motor ya existe en backend) |
| Outbound proactivo (broadcast) | Disparar template WhatsApp Meta-approved a segmento (warming, re-engagement, etc.) | 🧱 vitalia `ProactiveOutboundModal` |
| **N3-dyn** Detalle reserva | Estado pago + advisory lock + paciente + tratamiento + doctor + acciones (confirmar manual / cancelar + refund) | 🧱 vitalia `/bookings/[id]` |

🤖 Valeria + Adrián: "Cuántas reservas tengo confirmadas para mañana?" / "Cancela la reserva de Juan Pérez, devuelve el depósito" / "Manda recordatorio a todos los que tienen cita esta semana"

#### N2.4 — Atribución y origen

| N3 | Descripción | 🧱 Componentes lego |
|---|---|---|
| Matriz 4 orígenes | Heatmap origen × KPI (reservas, conversion, ingreso, ticket promedio). Origins: `sales_agent` · `walk_in` · `phone_manual` · `proactive_outbound` | 🧱 vitalia `AttributionMatrixWidget` (mover desde marketing layout actual) |
| Drilldown por origen | Para cada origen, ver leads que generó, conversión, fuentes específicas | 🧱 NUEVO |
| Reporte ROI por canal de venta | Cruce Atraer (gasto canal) × Vender (cierres por canal) = ROAS real | 🧱 NUEVO — coordinación Lucas+Adrián data |

🤖 Valeria + Adrián: "De dónde vinieron las 12 reservas de este mes?" / "Cuál origen me da pacientes que vuelven más?"

---

### 🟣 N1 — Operar (Valeria)

> "Soy Valeria. Coordino tu día. Veo la agenda, las tareas, los pacientes que entran y salen. Si algo se mueve, yo aviso. Soy la que te conecta con todo el equipo."

> 🔁 **Rol dual:** Valeria es además la **chat principal del lado izquierdo** (siempre visible). Cuando hablas con ella, **ella delega a Lisa/Lucas/Adrián/Camila/Mateo según corresponda** (router agéntico interno). Pero tiene su propio dominio: operación diaria.

#### N2.1 — Agenda del día / semana

| N3 | Descripción | 🧱 Componentes lego |
|---|---|---|
| Vista hoy | Citas de hoy en timeline + slots libres + alertas (no-show, llegó tarde, espera) | 🧱 vitalia `AppointmentsCalendarClient` mode=today |
| Vista semana | Calendario semanal multi-doctor con disponibilidad | 🧱 vitalia `AppointmentsCalendarClient` mode=week |
| Vista mes/calendario completo | Calendario tradicional con eventos | 🧱 vitalia `AppointmentsCalendarClient` mode=month |
| Configurar disponibilidad | Por doctor: working hours, buffer entre citas, días no laborables, vacaciones | 🧱 nicolify `cfg-agenda` settings adaptado |

🤖 Valeria autónoma: "Cuántas citas tengo hoy?" / "Hay slot libre el jueves 4pm con Dra. Castro?" / "Reagenda la cita de Juan del miércoles al viernes misma hora"

#### N2.2 — Pacientes activos (en consulta)

> Distinción importante: aquí vive el paciente **en relación clínica activa**. Los **leads** (aún no pacientes) viven en Vender/Adrián.

| N3 | Descripción | 🧱 Componentes lego |
|---|---|---|
| Lista pacientes activos | Filtros por clínica, doctor asignado, estado (en seguimiento, en mantenimiento, en pausa) | 🧱 vitalia `PatientListTable` |
| Próximos check-ins | Pacientes que llegan en próxima hora con alerta + acceso ficha | 🧱 NUEVO + integración agenda |
| **N3-dyn** Detalle paciente | Ficha completa: identidad, historial médico, tratamientos en curso, citas próximas/pasadas, PDFs subidos, NPS, audit PHI access. Dual-filter HIPAA enforced | 🧱 vitalia `PatientDetailPanel` + `PatientMedicalPdfUpload` + `TreatmentTimeline` |

🤖 Valeria autónoma: "Muéstrame la ficha de Ana Pérez" / "Sube este PDF a la ficha de Pedro" / "Cuándo fue la última cita de Luis?"

#### N2.3 — Tratamientos en curso

| N3 | Descripción | 🧱 Componentes lego |
|---|---|---|
| Tratamientos activos | Lista multi-sesión en progreso. Próxima sesión, sesiones completadas, doctor, paciente | 🧱 vitalia `TreatmentListTable` |
| Pacientes en pausa o riesgo | Detectar pacientes que se han salteado sesiones (alerta + acción re-engagement) | 🧱 NUEVO — coordinar con Camila |
| **N3-dyn** Detalle tratamiento | `TreatmentTimeline` con milestones, sesiones completadas/pendientes, notas clínicas, ajustar plan | 🧱 vitalia `/treatments/[id]` + `TreatmentTimeline` |
| **N3-dyn** Followup post-tratamiento | Workflow 24h/72h/7d/30d post-completion. Templates de seguimiento | 🧱 vitalia `/treatments/[id]/followup` |

🤖 Valeria autónoma: "Qué pacientes terminan tratamiento esta semana?" / "Pedro se saltó su 4ta sesión, ¿qué hacemos?" → escala a Camila

#### N2.4 — Tareas del equipo

| N3 | Descripción | 🧱 Componentes lego |
|---|---|---|
| Tareas pendientes (por hacer) | Lista priorizada cross-equipo: pedir consent, llamar paciente, subir PDF, autorizar refund, etc. Asignación por rol | 🧱 NUEVO — task system simple |
| Recordatorios cross-equipo | "Recordar al Dr. revisar lab de Pedro antes del viernes" | 🧱 NUEVO |
| Notas internas (notas del día) | Bitácora compartida entre equipo (no PHI — operacional) | 🧱 NUEVO |

🤖 Valeria autónoma: "Agrega tarea: llamar a María hoy en la tarde para confirmar cita" / "Qué tengo pendiente hoy?"

#### N2.5 — Check-in / Check-out (operación física)

> Funcionalidad nueva pensada para recepcionistas / asistentes.

| N3 | Descripción | 🧱 Componentes lego |
|---|---|---|
| Check-in del día | Lista de citas con botón "llegó" / "no vino" / "tarde X min". Updates timeline | 🧱 NUEVO — vista operación recepción |
| Check-out + próximo paso | Al salir paciente: agendar próxima cita, cobrar saldo, entregar instrucciones, pedir review/NPS | 🧱 NUEVO — flow post-cita |
| Pagos en recepción | Cobro presencial (POS o transferencia) vinculado a booking | 🧱 NUEVO — pagos vinculados a backend payment gateways |

🤖 Valeria autónoma: "Acabo de atender a Carla, agéndale el control en 30 días" / "Marca como no-show a Roberto, intentá reagendar"

---

### 🟦 N1 — Mantener (Camila)

> "Soy Camila. Me ocupo de lo que pasa cuando el paciente sale por la puerta. Que vuelva, que recomiende, que esté feliz. Vigilo redes, NPS, ausencias. Si alguien se está alejando, lo detecto y reactivo."

#### N2.1 — Embudo post-revenue (bottom of bowtie)

| N3 | Descripción | 🧱 Componentes lego |
|---|---|---|
| Mapa bowtie post | Visual SVG bowtie derecha: 2 etapas (Adopción → Expansión). KPI hero CLTV, retention rate, referrals | 🧱 vitalia `MarketingBowtieSVG` (parte derecha) |
| Cohortes retention | Pacientes por mes de primera visita, % retención mes 3/6/12, NPS por cohorte | 🧱 NUEVO — cohort analysis dashboard |
| CLTV dashboard | LTV promedio por tipo de tratamiento, por canal de adquisición, por doctor | 🧱 NUEVO — métrica reina de Camila |

🤖 Valeria + Camila: "Cuál es mi CLTV este trimestre?" / "Cuál cohorte está retenniendo mejor?"

#### N2.2 — Seguimiento post-tratamiento

| N3 | Descripción | 🧱 Componentes lego |
|---|---|---|
| Pacientes en ventana followup | 24h / 72h / 7d / 30d post-completion. Templates `recordatorio_control_doctor.json` | 🧱 vitalia `fid-followup` tab (existente) |
| Pacientes multi-sesión activa | Tracking de sesiones consumidas vs plan. Detectar "cerca de abandonar" | 🧱 vitalia `fid-multisesion` tab (existente) |
| Mantenimiento (membresías) | Pacientes con tratamiento completado candidatos a plan recurrente | 🧱 vitalia `fid-maintenance` tab (existente) — invitación template `invitacion_mantenimiento.json` |
| Acciones cross-tab | `ConfirmTemplateModal`, `SuggestSlotsModal`, `PausePatientModal`, `ManualCallLoggedModal` | 🧱 vitalia fidelización components |

🤖 Valeria + Camila: "Manda followup a los 3 pacientes que cerraron ortodoncia esta semana" / "Quién está cerca de abandonar?" / "Invita a María al plan de mantenimiento anual"

#### N2.3 — Ausencia y re-engagement

| N3 | Descripción | 🧱 Componentes lego |
|---|---|---|
| Pacientes ausentes | Lista filtrada por antigüedad ausencia (30/60/90/180d). Última actividad + tratamientos pasados | 🧱 vitalia `fid-ausencia` tab |
| Campañas de reactivación | Lanzar broadcast a segmento ausente. Template `re_engagement_ausencia.json` con marketing opt-in gate | 🧱 vitalia `ReEngagementCard` + `ReEngagementContactSidebar` |
| Historial de reactivaciones | Quién respondió, quién no, qué fórmula funciona mejor | 🧱 NUEVO |

🤖 Valeria + Camila: "Activa una campaña de re-engagement a pacientes ausentes hace 60+ días que se hicieron blanqueamiento" / "Cuántos volvieron?"

#### N2.4 — NPS y satisfacción

| N3 | Descripción | 🧱 Componentes lego |
|---|---|---|
| NPS dashboard | NPS promedio + distribución (promotores/pasivos/detractores) + tendencia + filtros (doctor, tratamiento, período) | 🧱 vitalia `fid-nps` tab + `NPSRowCompact` |
| Detractores (alerta crítica) | Lista paciente-by-paciente de NPS bajo. Asignar acción de recuperación (Adrián llama, Doctor escribe) | 🧱 NUEVO — wired to alerts system |
| Promotores (oportunidad referidos) | Lista NPS alto + CTA "invitar a programa referidos" | 🧱 NUEVO + connects to N2.5 |
| Templates NPS | Template `nps_post_tratamiento.json` schedule + condiciones de envío | 🧱 vitalia `whatsapp-template-registry` |

🤖 Valeria + Camila: "Qué pacientes detractores tengo este mes?" / "Cuál doctor tiene el mejor NPS?" / "Manda NPS a todos los que cerraron este mes"

#### N2.5 — Referidos & comunidad

| N3 | Descripción | 🧱 Componentes lego |
|---|---|---|
| Leaderboard referidos | Top pacientes evangelistas. Referrals enviados / signed_up / converted / expirados | 🧱 vitalia `ReferralsWidget` (existente) |
| Programa de referidos (config) | Reglas de recompensa: descuento, sesión extra, crédito. Por nivel de la escalera | 🧱 NUEVO — config layer |
| Reseñas Google/Yelp/Doctolib | Monitor menciones + invitación a dejar reseña post-cita exitosa | 🧱 NUEVO + Camila scraping |
| Menciones redes sociales | Monitor menciones marca en IG/TikTok/FB. Alerta sentimiento negativo | 🧱 NUEVO — Camila monitoring (puede pedir ayuda a Lucas) |

🤖 Valeria + Camila: "Cuántos referidos generó Ana este trimestre?" / "Apareció alguna mención mala en redes esta semana?" / "Pide reseña Google a los promotores de este mes"

---

### 🟡 N1 — Configurar (Mateo)

> "Soy Mateo. Hago que todo funcione. Conexiones, integraciones, llaves, monedas, temas. Si algo técnico no anda, llámame. También diseño cómo se ve y cómo se siente todo."

#### N2.1 — Cuenta y tenant

| N3 | Descripción | 🧱 Componentes lego |
|---|---|---|
| Tenant actual | Datos del tenant (clínica): nombre legal, RUC/CUIT/NIF, dirección fiscal, país, moneda principal, plan activo | 🧱 nicolify `cfg-general` adaptado |
| Plan & facturación | Tier actual (solo_doctor/clinic/multi_site), próximo billing, historia facturación, upgrade/downgrade | 🧱 NUEVO + vitalia plan_tiers |
| Perfil personal | Datos del usuario actual (yo): nombre, foto, email, MFA. Wrapper UserButton Clerk | 🧱 nicolify `cfg-perfil` |
| Multi-site (multi-clínica) | Para tier multi_site: gestionar sedes adicionales del mismo tenant (defer 11.bis) | 🧱 NUEVO defer story 11.bis |

#### N2.2 — Equipo Luana (usuarios del sistema)

| N3 | Descripción | 🧱 Componentes lego |
|---|---|---|
| Lista de usuarios | Miembros que acceden al dashboard (no doctores — eso vive en Mi Clínica). Roles: owner/admin_clinic/doctor/nurse/marketing/sales/viewer | 🧱 nicolify `cfg-equipo` adaptado |
| Roles & permisos (RBAC) | Matriz roles × accesos. Quién ve PHI, quién puede refundear, quién publica landings | 🧱 NUEVO + vitalia `iam-scaffold` |
| Invitaciones pendientes | Lista de emails invitados que no aceptaron + revocar acceso | 🧱 NUEVO |

🤖 Valeria + Mateo: "Invitá a recepcion@clinica.com con rol nurse" / "Quitá el acceso a Roberto, ya no trabaja aquí"

#### N2.3 — Locale y monedas

| N3 | Descripción | 🧱 Componentes lego |
|---|---|---|
| Idioma y región | Español neutro LatAm (único hoy). País operación drives compliance + moneda | 🧱 vitalia brand.yaml locale |
| Monedas aceptadas | Por país: PE→PEN, AR→ARS, CL→CLP, MX→MXN, CO→COP, BR→BRL, US→USD. Multi-currency en multi_site tier | 🧱 nicolify `master-data` rules |
| Timezone | Default por país, override per-clinica si multi-site | 🧱 vitalia locale VO |

#### N2.4 — Conexiones (integraciones operativas)

> ⚠️ Distinción: las conexiones publicitarias (Meta Ads / Google Ads / TikTok Ads) viven en **Atraer (Lucas)**. Aquí solo lo operativo: WhatsApp Business, pagos, calendario, herramientas.

| N3 | Descripción | 🧱 Componentes lego |
|---|---|---|
| WhatsApp Business | OAuth Meta Business, número verificado, templates Meta-approved, opt-in tracking | 🧱 nicolify `whatsapp` provider + vitalia template registry |
| Google Workspace | Gmail (transaccional), Google Calendar (sync agenda) | 🧱 nicolify `google-workspace` + `gmail` + `google-calendar` |
| Pagos | MercadoPago + Stripe Connect + tokenized recurring (paquetes + installments) | 🧱 vitalia `payment-gateways-latam-recurring` |
| ManyChat / Telegram (chatbots auxiliares) | Para flujos no-core | 🧱 nicolify providers |
| Web widget embebible | Snippet JS para sitio externo del cliente (booking widget) | 🧱 vitalia `booking-widget-embed` |
| **N3-dyn** Detalle conexión | Estado, último sync, credentials refresh, troubleshoot | 🧱 nicolify `cfg-conexiones detail` adaptado per-provider |

🤖 Valeria + Mateo: "Conectá el WhatsApp Business de la clínica" / "Hay algún canal caído?" / "Cuándo expira el token de Google Calendar?"

#### N2.5 — Apariencia (white-label & brand kit del dashboard)

| N3 | Descripción | 🧱 Componentes lego |
|---|---|---|
| Tema claro/oscuro | Toggle global persistido. Light/Dark/System | 🧱 NUEVO — `<ThemeToggle />` |
| Branding del dashboard | Logo + favicon + paleta del tenant en el shell (header) | 🧱 NUEVO — derivado de Mi Clínica visuales |
| Subdominio custom | clinica.luana.app o custom domain (clinica.com) con auto-DNS + cert | 🧱 nicolify `tenant_domains` |

#### N2.6 — Avanzado (developers)

| N3 | Descripción | 🧱 Componentes lego |
|---|---|---|
| Webhooks | Hacia sistemas externos (Zapier/Make/CRM cliente). Eventos disponibles + URL + secret + log | 🧱 nicolify `cfg-webhooks` |
| LLM API Keys (BYO) | BYO Anthropic / OpenAI / DeepSeek / Kimi keys si el tenant prefiere usar sus créditos | 🧱 nicolify `cfg-llm-keys` |
| Audit log técnico | Diferente del audit log compliance (HIPAA — vive en Mi Clínica). Aquí: errores, sync failures, retries | 🧱 vitalia `vitalia-callback-subclasses` (parte) |
| API explorer | Para devs que integran con nuestra API. Auth, docs, sandbox | 🧱 NUEVO — defer 11.bis |

🤖 Valeria + Mateo: "Mateo, ¿el webhook a Zapier está funcionando?" / "Cambia mi API key de Anthropic, te paso la nueva"

---

## 3. Capa transversal (NO van en menú — viven en el shell)

| Componente | Ubicación | Descripción |
|---|---|---|
| **Chat con Valeria** | Panel izquierdo 50% en modo agéntico (siempre visible) | Conversación con la coordinadora general. Valeria ROUTEA internamente al agente correcto (Lisa/Adrián/Lucas/Camila/Mateo) según el pedido del usuario. |
| **Historial conversaciones** | Sidebar colapsable dentro del panel chat (clon del CopilotSidebar de nicolify) | Conversaciones pasadas + crear nueva + buscar |
| **Tenant Switcher** | TopBar esquina superior derecha | Cambiar tenant manteniendo path |
| **Theme Toggle (claro/oscuro)** | TopBar bajo avatar Clerk | 3 estados: light/dark/system |
| **Avatar Clerk + dropdown** | TopBar esquina derecha | Profile, sign-out, preferencias |
| **Notificaciones (bell icon)** | TopBar | Centro de notificaciones: jobs largos, conexiones caídas, alertas Camila (detractor), recomendaciones Lucas pending |
| **Search global** | TopBar | Buscar paciente, tratamiento, cita por ID/nombre |
| **Active jobs poller** | Footer del chat panel (cuando hay jobs largos corriendo) | Lucas analizando trends, Mateo sincronizando, Camila enviando broadcast → progreso visible |
| **Breadcrumb del átomo activo** | TopBar contenido derecho (cuando estoy en N3) | Ej: "Mi Clínica > Tratamientos > Ortodoncia invisible" con flechas ↑↓ ←→ navegación entre átomos hermanos |

---

## 4. ¿Cómo manipula Valeria-chat todo el sistema? (R6 — visión WhatsApp)

**El sistema completo es operable desde la conversación con Valeria.** Cada acción que el usuario puede hacer con click, también puede pedirla en lenguaje natural. Esto habilita el futuro "WhatsApp del dueño" — el dueño NO ve el dashboard, le habla a Valeria por WhatsApp.

### Catálogo de acciones que Valeria entiende (ejemplos representativos)

> Esta lista NO es exhaustiva — es el contrato de capabilities mínimas de Valeria para que la metáfora "controla todo" sea real.

**Mi Clínica (Lisa):**
- "Crea un servicio nuevo: limpieza dental, $45 PEN, 30 min, nivel 2 escalera"
- "Sube esta foto como antes/después del Dr. García"
- "Cambia el horario del sábado a 9-13"
- "¿Tengo cobertura completa en la escalera de valor? ¿Qué nivel falta?"

**Atraer (Lucas):**
- "Pausa la campaña de Meta del blanqueamiento — me sale muy cara"
- "Lanza una campaña de ortodoncia, $200 USD, audiencia mujeres 25-45 LatAm"
- "Genera 3 ideas de reels esta semana"
- "¿Cuánto llevo gastado en ads este mes?"

**Vender (Adrián):**
- "¿Cuántas reservas confirmadas tengo para mañana?"
- "Mandá recordatorio a todos los que tienen cita esta semana"
- "Pausa Adrián en la conversación de María, le respondo yo"
- "¿De dónde vienen las reservas del mes?"

**Operar (Valeria misma):**
- "¿Cuántas citas tengo hoy?"
- "Reagenda Juan del miércoles al viernes 3pm"
- "Sube este PDF a la ficha de Pedro"
- "Hay slot libre el jueves 4pm con la Dra. Castro?"

**Mantener (Camila):**
- "¿Quién está cerca de abandonar?"
- "Mandá NPS a los 5 pacientes que cerraron esta semana"
- "Activa re-engagement a pacientes ausentes hace 60+ días"
- "¿Cuál es mi NPS este mes?"

**Configurar (Mateo):**
- "¿El WhatsApp Business está conectado?"
- "Invitá a recepcion@clinica.com con rol nurse"
- "Cambiá el tema a oscuro"
- "¿Hay algún canal caído?"

### Mecánica técnica subyacente (R7 — para arquitectos)

- Valeria es un **router LangGraph** que detecta intent y delega a la subagentic node correspondiente (Lisa/Lucas/Adrián/Camila/Mateo each = subagent con su propia LangGraph subgraph + tools).
- Cada acción del menú/web tiene su tool-equivalente registrada. Si Lisa tiene un botón "crear tratamiento", existe `create_treatment_tool` que ejecuta exactamente lo mismo.
- El panel derecho **refleja en tiempo real** lo que Valeria está haciendo (si Valeria está editando un tratamiento, el panel derecho se abre automáticamente en la vista de ese tratamiento — efecto "ver al asistente trabajar").
- Cuando Valeria necesita confirmación, lanza modal en el panel derecho (no en el chat) — UX cementada en el inbox de Adrián con `AdrianToolsSheet`.

---

## 5. Resumen mecánico — cómo se "rompe" un componente nicolify (lego pattern)

Ejemplo concreto del CopilotRail de nicolify (lo más complejo) → cómo se traslada a vitalia:

| nicolify component | nicolify location | vitalia destination | rol |
|---|---|---|---|
| `CopilotFAB` | `nicolify/frontend/.../copilot/CopilotFAB.tsx` | **NO se usa** (vista agéntica es default) | obsoleto en paradigm agéntico |
| `CopilotRail` | `nicolify/frontend/.../copilot/CopilotRail.tsx` | Panel izquierdo 50% siempre visible | **Lift a `core/luana-core-ui/`** (ADR-008) |
| `CopilotSidebar` (historial) | `nicolify/.../CopilotSidebar.tsx` | Sidebar colapsable DENTRO del rail izquierdo | lift core-ui |
| `CopilotChatPanel` | `nicolify/.../CopilotChatPanel.tsx` | Panel central del rail (donde van mensajes) | lift core-ui |
| `composer (MessageInput)` | `nicolify/.../composer/` | Footer rail (input usuario) | lift core-ui |
| `cards (PlanCard, ProcedureProgress)` | `nicolify/.../cards/` | Mensajes ricos dentro del chat | lift core-ui |
| `NavigationCard` (lleva al usuario a una vista) | `nicolify/.../messages/NavigationCard.tsx` | **Crucial:** disparador del panel derecho | lift core-ui |
| `ActiveJobsPoller` | `nicolify/.../ActiveJobsPoller.tsx` | Footer del rail (jobs largos) | lift core-ui |
| `ContextChips` | `nicolify/.../ContextChips.tsx` | Header del rail (qué átomo está viendo el usuario ahora) | lift core-ui |

**Patrón general:** todo átomo nicolify se cataloga primero, se lifta a `core/luana-core-ui/` si es transversal (mayoría), se importa en vitalia, se aplica el `vt-*` theme via CSS variables. Custom de vitalia (médico): se queda en `vitalia/frontend/src/components/`.

---

## 6. Backlog implícito (orden de implementación sugerido)

Cuando este árbol se ratifique, salen N stories. Orden de batch propuesto:

| Batch | Stories | Por qué primero |
|---|---|---|
| **B1** Shell foundation | shell-organism (este árbol) · luana-core-ui bootstrap · vitalia-tailwind-v4 fix | Sin shell no se ve nada |
| **B2** Valeria-as-router | LangGraph router subagentes · tools wiring (1 tool por feature reusada) · sync panel derecho con chat | Es el USP del producto |
| **B3** Mi Clínica | Treatment ladder UI · catálogo medical adaptado · doctores extended · compliance dashboard | Onboarding day-1 |
| **B4** Atraer | Wizard campañas multi-canal · Lucas trends · creative library · attribution feed | Genera nuevos pacientes (revenue driver) |
| **B5** Vender | Pipeline kanban medical · attribution matrix reubicada · scoring rules viewer · outbound proactivo polish | Cierre del funnel |
| **B6** Operar | Vista hoy/semana/mes · check-in/check-out · tareas equipo · pagos recepción | Operación diaria viable |
| **B7** Mantener | Cohort retention · referrals program config · monitoreo redes · CLTV dashboard | Maximizar LTV (último mile) |
| **B8** Configurar | Roles & permisos · multi-site UI (defer 11.bis) · webhooks · API explorer (defer 11.bis) | Setup avanzado / B2B enterprise |

---

## 7. Decisiones / preguntas pendientes para ratificar

1. **¿Lisa nueva agente o Valeria dual-role?** (sección 1 § conflicto). Mi recomendación: **Opción A** (Lisa nueva, 6 agentes en total).
2. **¿Mateo se queda con Configurar?** (consistencia con su rol "tecnología y diseño basado en IA"). Mi recomendación: **sí**.
3. **¿Color Lisa vs Valeria?** Ambos púrpura colisiona. Propuesta: Lisa `#7b2d91` púrpura ejecutivo / Valeria `#10b981` verde clínico.
4. **¿Reseñas Google/Yelp van en Mantener (Camila monitor) o Mi Clínica (Lisa social proof)?** Mi recomendación: **Camila** (es monitoreo continuo, no curaduría estática).
5. **¿Menciones redes sociales van en Mantener (Camila) o Atraer (Lucas)?** Estado actual = ambigüedad. Mi recomendación: **Camila monitor + Lucas response/inspiración** (cross-agent coordination natural).
6. **¿"Calendario de contenido" en Atraer (Lucas) o nueva tab "Publicar"?** Mi recomendación: queda en Atraer/Lucas (publicación es activación de atracción).
7. **¿"Pagos en recepción" en Operar (Valeria/Adrián) o Configurar (Mateo)?** Hoy lo puse en Operar porque es transaccional diario. Configurar solo aloja la conexión del gateway. ¿Confirmás?
8. **¿"Audit log HIPAA" en Mi Clínica/Lisa o Configurar/Mateo?** Hoy en Lisa porque es contractual del servicio médico (no técnico). Configurar tiene su propio audit técnico. ¿Confirmás partición?
9. **¿Crear Lisa visual (PNG cuadrado + transparente) o esperar ratificación de Opción A primero?**
10. **R2 setup: ¿lanzo bucket `luana-assets-platform` ahora o esperamos a integrar Lisa?**

---

## 8. Versionamiento

| Versión | Fecha | Cambio |
|---|---|---|
| 1.0 | 2026-05-21 | Propuesta inicial del árbol agéntico 6 top-level (5 agentes + 1 config). Fuentes: vitalia-feature-inventory.md + nicolify-feature-inventory.md + brief agentes + brand.yaml. Sin ratificar — listo para edición humana modular. |
