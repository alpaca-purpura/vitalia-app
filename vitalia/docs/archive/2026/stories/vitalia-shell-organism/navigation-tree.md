<!-- voseo-allowed: internal navigation tree spec for shell-organism -->

# Navigation Tree — Vitalia Shell-Organism

> **Status:** SSoT ratificado · **Fecha:** 2026-05-22 · **Versión:** 1.0
> **Reemplaza:** versiones previas en edición humana
> **Cementa:** estructura completa shell-organism cementada en `00-session-baseline.md` (17 decisiones Q1-Q7 + sub-Qs)

---

## § 1 — JSON Tree

```json
{
  "shell": {
    "version": "1.0",
    "ratified_at": "2026-05-22",
    "paradigm": "agentic-50-50",
    "topbar": {
      "type": "thin",
      "height": "48px",
      "elements": [
        { "id": "logo", "type": "LogoMark", "position": "left" },
        { "id": "theme-toggle", "type": "ThemeToggle", "position": "right" },
        { "id": "tenant-switcher", "type": "TenantSwitcher", "position": "right" }
      ]
    },
    "modes": {
      "agentic": { "default": true, "split": "50/50", "valeria_state": "rail" },
      "web": { "split": "rail-only/100%", "valeria_state": "collapsed" }
    },
    "panels": {
      "left": {
        "id": "valeria-sidebar",
        "width": "50%",
        "subgrid": "rail-or-history | chat",
        "components": ["ValeriaRail", "ValeriaHistory", "ValeriaChat"],
        "states": ["collapsed", "rail", "full"],
        "default_state": "rail",
        "keyboard": { "C": "collapsed", "R": "rail", "F": "full", "N": "new-conv", "Esc": "close", "Cmd+K": "focus-composer" }
      },
      "right": {
        "id": "app-content",
        "width": "50%",
        "subgrid": "ribbon | sub-tabs | content",
        "components": ["Ribbon", "SubTabsBar", "ContentArea"]
      }
    },
    "tabs": [
      {
        "id": "lisa",
        "label": "Mi Clínica",
        "role": "Lisa",
        "color": "#00D084",
        "color_token": "--agent-lisa",
        "avatar": "/agents/lisa/thumbnail.png",
        "default_subtab": "marca",
        "subtabs": [
          {
            "id": "marca",
            "label": "Marca",
            "icon": "🏥",
            "description": "Identidad · Voz y tono · Landing & presencia",
            "phase2_story": "vitalia-fase2-lisa-marca",
            "reuse": "brand_studio shipped (adapt salud)",
            "n3_dyn": []
          },
          {
            "id": "doctores",
            "label": "Doctores",
            "icon": "👨‍⚕️",
            "description": "CRUD perfiles personal-branding doctor",
            "phase2_story": "vitalia-fase2-lisa-doctores",
            "reuse": "patients+staff models shipped",
            "n3_dyn": [
              { "id": "perfil-doctor", "path": "[doctor-id]", "description": "Workspace detalle doctor: bio + horarios + servicios + KPIs" }
            ]
          },
          {
            "id": "servicios",
            "label": "Servicios",
            "icon": "🩺",
            "description": "Toggle Catálogo | Escalera de valor",
            "phase2_story": "vitalia-fase2-lisa-servicios",
            "reuse": "treatments shipped + NEW canvas escalera",
            "toggle_views": ["catalogo", "escalera"],
            "n3_dyn": [
              { "id": "tratamiento", "path": "[treatment-id]", "description": "Detalle tratamiento CRUD" },
              { "id": "ladder-slot", "path": "ladder/[slot-id]", "description": "Detalle slot escalera (rol + treatment_ref + pricing override + cta_copy)" }
            ]
          },
          {
            "id": "compliance",
            "label": "Compliance",
            "icon": "🛡️",
            "description": "Semáforo HIPAA-lite + política retención + reportes",
            "phase2_story": "vitalia-fase2-lisa-compliance",
            "reuse": "medical-compliance shipped",
            "links_to": ["config/avanzado#raw-log"]
          }
        ]
      },
      {
        "id": "lucas",
        "label": "Atraer",
        "role": "Lucas",
        "color": "#111111",
        "color_token": "--agent-lucas",
        "avatar": "/agents/lucas/thumbnail.png",
        "default_subtab": "lanzar",
        "model": "ciclo-temporal-v2",
        "subtabs": [
          {
            "id": "lanzar",
            "label": "Lanzar",
            "icon": "🚀",
            "description": "Nueva campaña · Quick-post · Borradores · Pendientes aprobación",
            "phase2_story": "vitalia-fase2-lucas-lanzar",
            "reuse": "NEW workspace P4 campaign",
            "n3_dyn": [
              { "id": "nueva-campana", "path": "nueva", "description": "Wizard adaptivo paga/orgánica" },
              { "id": "borrador", "path": "borradores/[draft-id]", "description": "Editor borrador campaña" }
            ]
          },
          {
            "id": "envuelo",
            "label": "En vuelo",
            "icon": "📡",
            "description": "Campañas activas · Posts programados · Performance live",
            "phase2_story": "vitalia-fase2-lucas-envuelo",
            "reuse": "NEW",
            "n3_dyn": [
              { "id": "campana-activa", "path": "campana/[campaign-id]", "description": "Workspace detalle: live KPIs + creatividades + ajustes" },
              { "id": "post-programado", "path": "post/[post-id]", "description": "Preview + edit + cancel post" }
            ]
          },
          {
            "id": "recursos",
            "label": "Recursos",
            "icon": "📚",
            "description": "Biblioteca creatividades · Copy reusable · Generador IA · Importados · Solicitudes Mateo",
            "phase2_story": "vitalia-fase2-lucas-recursos",
            "reuse": "marketing module shipped + Mateo assistant cards",
            "mateo_integration": true,
            "n3_dyn": [
              { "id": "asset", "path": "assets/[asset-id]", "description": "Detalle creatividad" }
            ]
          },
          {
            "id": "resultados",
            "label": "Resultados",
            "icon": "📈",
            "description": "Embudo Bowtie izq · Comparativa canal · Histórico · Post-mortem",
            "phase2_story": "vitalia-fase2-lucas-resultados",
            "reuse": "analytics shipped + bowtie funnel shipped",
            "n3_dyn": [
              { "id": "post-mortem", "path": "campana/[campaign-id]/post-mortem", "description": "Análisis cerrada: qué funcionó / qué no + recomendación próxima iteración" }
            ]
          },
          {
            "id": "mercado",
            "label": "Mercado",
            "icon": "🌍",
            "description": "Tendencias rubro · Hashtags · Competencia · Sugerencias Lucas",
            "phase2_story": "vitalia-fase2-lucas-mercado",
            "reuse": "NEW (trends mining)"
          }
        ]
      },
      {
        "id": "adrian",
        "label": "Vender",
        "role": "Adrián",
        "color": "#01b2f8",
        "color_token": "--agent-adrian",
        "avatar": "/agents/adrian/thumbnail.png",
        "default_subtab": "inbox",
        "subtabs": [
          {
            "id": "inbox",
            "label": "Inbox",
            "icon": "💬",
            "description": "Conversaciones cross-canal · 3-modos · Activity stream",
            "phase2_story": "vitalia-fase2-adrian-inbox",
            "reuse": "inbox+sales_agent shipped",
            "paradigm": "3-modos-decide-consulta-manual",
            "n3_dyn": [
              { "id": "conversation", "path": "[conv-id]", "description": "Thread completo + ContactSidebar PHI masked + Activity stream" }
            ]
          },
          {
            "id": "embudo",
            "label": "Embudo",
            "icon": "🎯",
            "description": "Toggle Kanban | Lista CRM · 6 stages dental",
            "phase2_story": "vitalia-fase2-adrian-embudo",
            "reuse": "REFACTOR slice-1-pipeline + nicolify closer-studio",
            "toggle_views": ["kanban", "lista"],
            "stages_default_vertical": ["interesado", "calificando", "considerando", "listo", "reservado", "decidio-no"],
            "stages_customizable_per_vertical": true,
            "n3_dyn": [
              { "id": "lead-detail", "path": "[lead-id]", "description": "Lead workspace: datos + historial conv + propuestas + score + time-in-stage + tools registry" }
            ]
          },
          {
            "id": "outbound",
            "label": "Outbound",
            "icon": "📣",
            "description": "Campañas a leads · 5 templates Meta-approved",
            "phase2_story": "vitalia-fase2-adrian-outbound",
            "reuse": "fidelización + 5 templates Meta-approved shipped",
            "audience": "leads-pre-paciente",
            "n3_dyn": [
              { "id": "campana-outbound", "path": "campana/[campaign-id]", "description": "Wizard 3 pasos: segmento + template + schedule" }
            ]
          },
          {
            "id": "propuestas",
            "label": "Propuestas",
            "icon": "💼",
            "description": "Opt-in dental/estética · Planes pago · Firma digital",
            "phase2_story": "vitalia-fase2-adrian-propuestas",
            "reuse": "NEW + Stripe/MP shipped",
            "opt_in_per_vertical": { "dental": true, "estetica": true, "psicologia": false, "psiquiatria": false },
            "n3_dyn": [
              { "id": "propuesta", "path": "[proposal-id]", "description": "Workspace propuesta: tratamientos + plan pago + términos + firma + estado pagos + trazabilidad" }
            ]
          }
        ]
      },
      {
        "id": "valeria",
        "label": "Operar",
        "role": "Valeria",
        "color": "#7b2d91",
        "color_token": "--agent-valeria",
        "avatar": "/agents/valeria/thumbnail.png",
        "default_subtab": "agenda",
        "dual_role": "tab_operar + chat_persistente_shell",
        "subtabs": [
          {
            "id": "agenda",
            "label": "Agenda",
            "icon": "📆",
            "description": "Calendario + drawer slot · Subform Cobrar saldo inline",
            "phase2_story": "vitalia-fase2-valeria-agenda",
            "reuse": "REFACTOR slice-1-agenda + scheduling+booking shipped",
            "views": ["dia", "semana", "mes"],
            "slot_statuses": ["pagado", "deposito", "sin-pago", "no-show"],
            "slot_origins": ["walk-in", "telefono", "proactiva-adrian"],
            "service_blockers": ["vitalia-payment-adapter-mvp", "vitalia-fiscal-emission-pe"],
            "presets_filtered": ["hoy", "por-confirmar-manana", "re-agendar-pendientes", "no-shows-del-dia"],
            "n3_dyn": [
              { "id": "slot-drawer", "trigger": "click slot", "description": "Drawer inline: paciente PHI masked + turno + Cobrar saldo subform fiscal + acciones" },
              { "id": "crear-cita", "trigger": "click Crear cita", "options": ["walk-in", "telefono"] }
            ]
          },
          {
            "id": "pacientes",
            "label": "Pacientes",
            "icon": "👥",
            "description": "Directorio + ficha + Tratamientos activos",
            "phase2_story": "vitalia-fase2-valeria-pacientes",
            "reuse": "patients+crm shipped",
            "segments": ["todos", "deudores", "tratamientos-activos"],
            "n3_dyn": [
              { "id": "ficha-paciente", "path": "[patient-id]", "description": "Workspace: datos + historial citas + tratamientos + estado cuenta + etiquetas" },
              { "id": "nuevo-paciente", "trigger": "click + Nuevo paciente", "description": "Form rápido alta" }
            ]
          }
        ]
      },
      {
        "id": "camila",
        "label": "Mantener",
        "role": "Camila",
        "color": "#180d95",
        "color_token": "--agent-camila",
        "avatar": "/agents/camila/thumbnail.png",
        "default_subtab": "voz",
        "paradigm": "3-modos-decide-consulta-manual + 12-triggers-ssot",
        "valeria_centric": true,
        "subtabs": [
          {
            "id": "voz",
            "label": "Voz del paciente",
            "icon": "🎤",
            "description": "Entrante + Curaduría + Activos vivos (UN flujo)",
            "phase2_story": "vitalia-fase2-camila-voz",
            "reuse": "fidelización+NPS shipped",
            "sub_views": ["entrante", "en-curaduria", "activos-vivos"],
            "triggers_ssot": [
              "nps-9-10", "nps-7-8", "nps-0-6",
              "resena-4-plus", "resena-3", "resena-menor-3",
              "mencion-positiva", "mencion-negativa",
              "dormant-60d", "fin-tratamiento", "mantenimiento-vence-30d",
              "promotor-sin-referir-14d", "cumpleanos",
              "propuesta-sin-firmar-7d", "imagen-testimonio"
            ]
          },
          {
            "id": "reactivar",
            "label": "Reactivar",
            "icon": "🪃",
            "description": "Audience PACIENTES en riesgo · churn defense · 5 listas dinámicas",
            "phase2_story": "vitalia-fase2-camila-reactivar",
            "reuse": "sales_agent reengagement_tool shipped + fidelización",
            "audience": "pacientes-existentes-post-revenue",
            "listas_dinamicas": [
              "sin-actividad-60-90-180d",
              "fin-tratamiento-sin-recall",
              "mantenimiento-por-vencer",
              "propuesta-sin-firmar",
              "detractor-nps-pendiente"
            ]
          },
          {
            "id": "multiplicar",
            "label": "Multiplicar",
            "icon": "🤝",
            "description": "Audience PROMOTORES · referidos + advocacy growth",
            "phase2_story": "vitalia-fase2-camila-multiplicar",
            "reuse": "referrals_leaderboard MUDAR de Lucas→Camila (P1 atomic ownership)",
            "audience": "promotores-growth-via-existentes",
            "listas_dinamicas": ["promotor-sin-referir", "cumpleanos-mes", "aniversario-cliente"],
            "auto_triggers": ["nps-promotor-14d", "cumpleanos", "resena-5-estrellas"]
          },
          {
            "id": "reputacion",
            "label": "Reputación",
            "icon": "📊",
            "description": "Panorama estratégico cross-canal (planned)",
            "phase2_story": "vitalia-fase2-camila-reputacion",
            "reuse": "NEW (planned)",
            "status": "scaffold-fase2-mvp"
          }
        ]
      },
      {
        "id": "config",
        "label": "Configurar",
        "role": "Admin",
        "color": "#64748b",
        "color_token": "--agent-config",
        "icon": "⚙️",
        "no_agent_face": true,
        "default_subtab": "cuenta",
        "filosofia": "panel-dueno-uso-1-2x-mes · Valeria-hace-todo-conceptualmente · UI-es-espejo-visual",
        "subtabs": [
          {
            "id": "cuenta",
            "label": "Mi cuenta",
            "icon": "🏢",
            "description": "Info clínica + Plan Luana + Equipo",
            "phase2_story": "vitalia-fase2-config-cuenta",
            "reuse": "iam shipped + brand.yaml",
            "sections": ["info-clinica", "plan-facturacion-luana", "equipo-clinica-rbac"]
          },
          {
            "id": "conexiones",
            "label": "Conexiones",
            "icon": "🔌",
            "description": "HUB integraciones · 6 categorías · OAuth flows",
            "phase2_story": "vitalia-fase2-config-conexiones",
            "reuse": "connections shipped + nicolify HUB pattern",
            "categorias": [
              "marketing-publicidad",
              "mensajeria-atencion",
              "pagos-facturacion",
              "calendarios-externos",
              "presencia-online",
              "integraciones-tecnicas"
            ],
            "n3_dyn": [
              { "id": "provider-detail", "path": "[provider-id]", "description": "Drawer detalle: OAuth + health + permisos + config + actividad + desconectar" }
            ]
          },
          {
            "id": "avanzado",
            "label": "Avanzado",
            "icon": "🔬",
            "description": "Reglas + Raw audit log + LLM keys + Flags + API + Import/Export + Danger zone",
            "phase2_story": "vitalia-fase2-config-avanzado",
            "reuse": "NEW",
            "sections": [
              "reglas-politicas",
              "registro-tecnico-raw",
              "llm-keys-byo",
              "feature-flags",
              "api-tokens-webhooks",
              "import-export",
              "zona-peligrosa"
            ]
          }
        ]
      }
    ],
    "transversal": {
      "mateo": {
        "id": "mateo",
        "role": "diseñador",
        "color": "#fee209",
        "no_tab": true,
        "appearances": [
          { "context": "lisa.marca.landing", "description": "Assistant card asiste diseño landing" },
          { "context": "lucas.recursos", "description": "Solicitudes Mateo queue diseño gráfico" }
        ]
      }
    },
    "cross_shell_notifications": {
      "type": "bell-icon-topbar",
      "owner": "all-agents",
      "description": "Recomendaciones cross-agente viven en bell icon TopBar (modelo Facebook/Linear/GitHub). Click → deep-link al átomo donde tomar acción.",
      "status": "fase-2-final (postponed)"
    }
  }
}
```

---

## § 2 — Counts cementados

| Capa | Cantidad |
|---|---|
| Tabs top-level | 6 (5 agentes + 1 Configurar) |
| Sub-tabs totales | 22 (Lisa 4 · Lucas 5 · Adrián 4 · Valeria 2 · Camila 4 · Configurar 3) |
| Agente transversal sin tab | 1 (Mateo) |
| N3-dyn workspaces | ~18 (detalles paciente · doctor · campaña · post · slot · etc.) |

---

## § 3 — Reglas de navegación

| Caso | Comportamiento |
|---|---|
| Usuario no autenticado | Clerk middleware → `/sign-in` |
| Usuario autenticado sin tenant | `/select-tenant` (placeholder, no en MVP) |
| URL `/{tenant}/(shell-organism)` (sin agente) | Redirect `/{tenant}/(shell-organism)/lisa/marca` (default home) |
| URL `/{tenant}/(shell-organism)/{agent}` (sin subtab) | Redirect a `default_subtab` del agente per § 1 |
| URL `/{tenant}/(shell-organism)/{agent-invalido}/...` | 404 `not-found.tsx` con CTA volver |
| URL `/{tenant}/(shell-organism)/{agent}/{subtab-invalido}` | 404 idem |
| Navegación vía chat Valeria | Deep-link directo a la sub-tab + opcional indicador "vía Valeria" en breadcrumb |
| Navegación manual click ribbon | URL update + active state |
| Cambio tenant | Hard redirect preservando agent + subtab actual |

---

## § 4 — Anti-creep documentado (qué NO entra al shell)

| Concepto | Razón de exclusión | Decisión cementada |
|---|---|---|
| Tab "Reportes financieros" propio | Vive en Lisa o TopBar (TBD) — no es agente | Q5 ratificado 2026-05-21 |
| Tab "Caja" estilo ERP en Valeria | Eliminada — cobro 100% inline en slot agenda | Q5 ratificado |
| Sub-tab "Notas médicas" en Valeria | Fuera scope — no es PMS | Q-valeria-macro |
| Sub-tab "Perfil doctor" en Valeria | Movido a Lisa Mi Clínica (asset semi-estático) | Q-doctores |
| Tab "Estado cuenta" en Valeria | Cohort filtro en directorio Pacientes "Deudores" | Q5 |
| Tab dedicada "Recomendaciones" | Vive en bell icon TopBar cross-agente | P2 |
| Tab "Conexiones" duplicada per agente | Centralizada en ⚙️ Configurar + `<RequireConnection>` inline | P3 |
| Tab "Mateo" | Mateo es transversal sin tab — asiste landing + diseño gráfico futuro | Q1.b |
| Sub-tab "Doctores" en Configurar | Vive en Lisa Mi Clínica | Q-doctores |
| Sub-tab "Identidad/Voz/Landing" en Configurar | Vive en Lisa Marca | Q-configurar-macro |
| Tabs "Catálogo" + "Escalera" separadas | Una sub-tab Servicios con toggle Catálogo\|Escalera | Q-servicios-vs-ladder |

---

## § 5 — Mapping per agente a stories Fase 2

> Cada sub-tab del § 1 cita su `phase2_story`. La generación de stories Fase 2 (Task #7-#11 del task tracker) materializa estos slugs.

| Agente | Sub-tabs | Stories Fase 2 totales |
|---|---|---|
| 🟢 Lisa | 4 | 4 stories (F2-S7..F2-S10) |
| 🖤 Lucas | 5 | 5 stories (F2-S15..F2-S19) |
| 🔵 Adrián | 4 | 4 stories (F2-S3..F2-S6) |
| 🟣 Valeria | 2 | 2 stories (F2-S1..F2-S2) |
| 🟦 Camila | 4 | 4 stories (F2-S11..F2-S14) |
| ⚙️ Configurar | 3 | 3 stories (F2-S20..F2-S22) |
| **Total** | **22** | **22** |

---

## § 6 — Versioning

| Versión | Fecha | Cambio |
|---|---|---|
| 0.1 | 2026-05-21 | Borrador inicial en edición humana Chris |
| **1.0** | **2026-05-22** | **Cementado post mockup HTML ratificado. JSON tree completo · counts · anti-creep · mapping stories** |
