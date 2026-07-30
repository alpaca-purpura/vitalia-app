<!-- voseo-allowed: internal handoff documentation for session continuation, architecture exploration -->

# Handoff — Sesión vitalia-shell-organism

> **Fecha snapshot:** 2026-05-21
> **Estado:** Diseño 100% cementado · pendientes 3 artefactos finales (mockup + nav-tree + handoff /pm-vitalia)
> **Branch:** `wip/vitalia` (no rotar — mismo canónico)
> **Context burned previa sesión:** ~45% (450k/1M tokens Opus 4.7)
> **Modelo recomendado para retomar:** Opus 4.7 (1M context) — fresh start

---

## Prompt copy-paste para retomar (nueva conversación)

```
Estoy retomando la sesión vitalia-shell-organism (rediseño agéntico Vitalia + Valeria-secretaria).
Branch actual: wip/vitalia.

Lee EXACTAMENTE en este orden:

1. vitalia/docs/product/stories/vitalia-shell-organism/00-session-baseline.md
   ↑ ES EL DOC MAESTRO. Contiene: visión norte, principios P1-P5 cementados,
   set de 5 agentes-cara + Configurar + Mateo transversal, decisiones Q1-Q7
   TODAS cerradas (17 decisiones cementadas), sub-estructuras completas en § 11
   para cada agente (Lisa 4 sub-tabs · Lucas 5 cols ciclo v2 · Adrián 4 sub-tabs
   · Valeria 2 sub-tabs · Camila v3 4 sub-tabs · Configurar 3 sub-tabs).

2. vitalia/docs/product/stories/vitalia-shell-organism/HANDOFF-next-session.md
   ↑ ESTE doc — punto de retoma exacto + lo aprendido + próximos pasos

3. (Solo si necesitás referencias):
   - vitalia-feature-inventory.md (qué hay shippeado en vitalia hoy)
   - nicolify-feature-inventory.md (REUSE base UX patterns)
   - mockups/dual-mode-shell.html (estética agéntica base — VOY A REFIT)
   - /home/chalreme/Trabajo/Vitalia/Prototipos/{inbox,pipeline,agenda}.html
     (mockups ratificados v1 Batch 2/3 — REUSE patterns)

Estado del trabajo:
- TODAS las preguntas de diseño cerradas (Q1-Q7 + 17 sub-decisiones)
- Estructura completa cementada (5 agentes-cara + Configurar + Mateo transversal)
- Paradigma agéntico Camila completo (3-modos + 12 triggers SSoT + reglas configurables)
- Pendientes: 3 artefactos finales
   1. Task #8 — Re-armar mockup dual-mode-shell.html (refit minimal opción A)
   2. Task #9 — Reemplazar navigation-tree.md con árbol JSON final
   3. Task #10 — Handoff /pm-vitalia regenerar historias afectadas

ARRANCA POR TASK #8 (refit mockup dual-mode-shell.html opción A — minimal):
- Mantener concept original (modo web vs modo agéntico, split 50/50)
- Mantener átomo abierto actual (Dr. Juan García) como contenido placeholder
- CAMBIAR solo el ribbon: tabs reales 5 agentes + Configurar con colores oficiales:
   · 🟢 Lisa #00D084 (Mi Clínica)
   · 🖤 Lucas #111111 (Atraer)
   · 🔵 Adrián #01b2f8 (Vender)
   · 🟣 Valeria #7b2d91 (Operar)
   · 🟦 Camila #180d95 (Mantener)
   · ⚙️ Configurar (ícono genérico, sin color agente)
- Fotos PNG locales: vitalia/frontend/public/agents/{lisa,lucas,adrian,valeria,camila}/thumbnail.png
- Mateo NO va como tab (transversal sin tab — confirmado Q1.b)

Reglas de la sesión (recordatorio):
- UNA pregunta a la vez (Chris no acepta lotes)
- Cementar cada decisión en 00-session-baseline.md ANTES de pasar a siguiente
- Backend DDD + Frontend FSD NO se rearman según agentes (P5 cementado)
- Conexiones SIEMPRE en Configurar con <RequireConnection> inline (P3)
- Recomendaciones cross-shell van al bell icon TopBar (P2)
- Atomic ownership: cada átomo UN dueño semántico (P1)
- Mateo transversal sin tab (Q1.b)
- Valeria es la cara universal del shell (chat persistente + tab dual "Operar")

Modelo recomendado: Opus 4.7 (1M context) — la sesión anterior burned 45% solo en
cementar decisiones, arrancamos fresh con todo cementado para los 3 artefactos finales.
```

---

## Estado de la sesión 2026-05-21 (snapshot exhaustivo)

### Decisiones cementadas (17 — todas cerradas ✅)

| # | Pregunta | Decisión |
|---|---|---|
| Q1 | ¿Mateo a Configurar? | NO — Configurar es ícono genérico |
| Q1.b | ¿Qué pasa con Mateo? | Transversal sin tab (asiste landing + diseño futuro) |
| Q2 | Reseñas Google/Yelp ¿Camila o Lisa? | Camila dueña de TODO relación-cliente |
| Q3 | Menciones redes ¿Camila o Lucas? | Camila (marca) + Lucas (mercado) — separación cliente vs mercado |
| Q4 | Calendario contenido orgánico ¿Lucas o tab nueva? | Lucas unificado (paga + orgánica) |
| Q4.b | Subestructura Lucas v1 vs v2 | **v2 ciclo-temporal** (Lanzar / En vuelo / Recursos / Resultados / Mercado) |
| Q-valeria-macro | Universo Valeria | 2 sub-tabs (Agenda · Pacientes) sin Caja ERP |
| Q-doctores | ¿Dónde viven los doctores? | 🟢 Lisa Mi Clínica (asset semi-estático clínica) |
| Q5 | Pagos en recepción | Eliminar sub-tab Caja — cobro 100% inline en slot agenda |
| Q6 | Audit log HIPAA | Híbrido suave: Lisa Compliance dashboard + Configurar raw log |
| Q-mi-clinica | Estructura macro Lisa | 4 sub-tabs (Marca · Doctores · Servicios · Compliance) |
| Q-servicios-vs-ladder | ¿Catálogo y Escalera separadas? | NO — una sub-tab Servicios con toggle Catálogo \| Escalera |
| Q-vender-macro | Estructura macro Adrián | 4 sub-tabs (Inbox · Embudo · Outbound · Propuestas opt-in) |
| Q-mantener-macro | Estructura macro Camila inicial | 4 sub-tabs (Escucha · Pruebas sociales · Reactivar · Reputación) |
| Q-camila-v3 | Refit Camila | Fusión Escuchar+Curar en "Voz del paciente" + separar Reactivar (churn) y Multiplicar (growth) |
| Q-configurar-macro | Estructura Configurar | 3 sub-tabs (Mi cuenta · Conexiones · Avanzado) |
| Q7 | Modelo cross-agente | Opción A — modelo propio per agente según naturaleza del rol |
| Q-camila-agente-ops | Cómo opera Camila como agente IA | 3-modos extensible + 12 triggers SSoT + reglas configurables en Configurar |

### Estructura final cementada (vista 1-pantalla)

```
Vitalia Shell-Organism — 6 tabs top-level + 1 transversal sin tab + Valeria chat persistente

┌──────────────────────────────────────────────────────────────────────────────┐
│ Ribbon: 🟢 Lisa · 🖤 Lucas · 🔵 Adrián · 🟣 Valeria · 🟦 Camila · ⚙️ Configurar │
└──────────────────────────────────────────────────────────────────────────────┘

🟢 Lisa (Mi Clínica) — 4 sub-tabs · espacial estratégico
├── 🏥 Marca de la clínica (Identidad + Voz/tono + Landing & presencia)
├── 👨‍⚕️ Doctores (CRUD perfiles personal-branding)
├── 🩺 Servicios (toggle 📋 Catálogo | 🪜 Escalera de valor)
└── 🛡️ Compliance HIPAA-lite (semáforo + política + reportes)

🖤 Lucas (Atraer) — 5 cols · ciclo-temporal v2
├── 🚀 Lanzar (Nueva campaña / Quick-post / Borradores / Pendientes aprobación)
├── 📡 En vuelo (Campañas activas / Posts programados / Performance live / Detalle dyn)
├── 📚 Recursos (Biblioteca creatividades / Copy reusable / Generador IA / Importados / Solicitudes Mateo)
├── 📈 Resultados (Embudo Bowtie izq / Comparativa canal / Histórico / Post-mortem)
└── 🌍 Mercado (Tendencias rubro / Hashtags / Competencia / Sugerencias Lucas)

🔵 Adrián (Vender) — 4 sub-tabs · espacial operativo
├── 💬 Inbox (3-modos: decide/consulta/manual + ConversationList + Thread + ContactSidebar + Activity Stream)
├── 🎯 Embudo (toggle 📋 Kanban dental 6 stages | 📑 Lista CRM)
├── 📣 Outbound (campañas a LEADS pre-paciente — 5 templates Meta-approved)
└── 💼 Propuestas y planes (opt-in dental/estética ON · psico/psiquiatría OFF)

🟣 Valeria (Operar) — 2 sub-tabs · espacial recepción + dual-role chat shell
├── 📆 Agenda (calendario + drawer slot con subform Cobrar saldo inline)
└── 👥 Pacientes (directorio + ficha + Tratamientos activos)

🟦 Camila (Mantener) — 4 sub-tabs · espacial post-revenue + paradigma agéntico 3-modos
├── 🎤 Voz del paciente (Entrante + En curaduría + Activos vivos · UN flujo)
├── 🪃 Reactivar (audience PACIENTES — churn defense + 5 listas dinámicas)
├── 🤝 Multiplicar (audience PROMOTORES — referidos + 3 listas growth)
└── 📊 Reputación (panorama estratégico cross-canal · planned)

⚙️ Configurar — 3 sub-tabs · sin cara agéntica
├── 🏢 Mi cuenta (Info clínica + Plan Luana + Equipo)
├── 🔌 Conexiones (HUB estilo nicolify · 6 categorías + drawer per provider)
└── 🔬 Avanzado (Reglas + Raw log + LLM keys + Flags + API + Import/Export + Danger zone)

🟡 Mateo (transversal sin tab) — asiste landing (sí o sí) + diseño gráfico futuro
🟣 Valeria — chat persistente shell-level + dueño habla con ella + delega a otros agentes
```

### Paradigma agéntico Camila cementado (también aplica conceptualmente a otros agentes IA)

**3-modos** (extensible patrón Adrián Inbox):
- 🤖 Decide (auto-procesa entrante según reglas)
- 💬 Consulta (sugiere + aprobación humana)
- ✍️ Manual (humano decide)

**12 triggers SSoT** cementados en § Camila baseline:
NPS 9-10 · NPS 7-8 · NPS 0-6 · Reseña ≥4⭐ · Reseña 3⭐ · Reseña <3⭐ · Mención positiva · Mención negativa · Dormant 60d · Fin tratamiento · Mantenimiento N4 vence ≤30d · Promotor sin referir +14d · Cumpleaños · Propuesta sin firmar >7d · Imagen testimonio

**Reglas** configurables en ⚙️ Configurar → Avanzado → Reglas Camila (defaults sensibles por vertical).

**Modelo Valeria-céntrico:** Dueño habla con Valeria por chat. Valeria delega a Camila/Lucas/Adrián. Paciente nunca ve "Camila" — solo mensajes desde la clínica.

---

## Lo que falta — 3 artefactos finales

### Task #8 — Re-armar mockup `dual-mode-shell.html` (refit minimal — pendiente ratificación opción A vs B vs C)

**Opción A (mi recomendación):** refit minimal — tabs reales en ribbon + colores oficiales + PNGs locales. Mantener átomo abierto (Dr. Juan García) como contenido placeholder. Rápido, valida contrato visual.

**Opción B:** intermedia — shell + landing view por agente (mockups parciales de Voz del paciente, Inbox, Pipeline, Agenda).

**Opción C:** full — un archivo HTML por agente. Diferido a historias formales.

### Task #9 — Reemplazar `navigation-tree.md` con árbol JSON final

Generar JSON-in-MD con árbol completo:
- 6 tabs top-level
- Sub-tabs cementadas per agente (incluye toggles, opt-ins, dyn workspaces)
- Hooks cross-agente
- Quedan fuera de cada tab (anti-creep documentados)

### Task #10 — Handoff a /pm-vitalia regenerar historias

Invocar `/pm-vitalia` con prompt que:
- Carga 00-session-baseline.md como SSoT funcional
- Identifica historias pre-paradigma que necesitan refit
- Genera nuevas historias de usuario alineadas al shell-organism
- Crea capabilities entries en `vitalia/docs/product/capabilities/`
- Actualiza BACKLOG.md (auto-gen)

---

## REUSE backend shipped (referencia rápida)

| Dominio | Path BE | Status FE |
|---|---|---|
| Inbox (cross-canal) | `vitalia/backend/src/modules/vitalia/inbox/` | ✅ shipped orphan |
| Sales agent (Adrián) | `vitalia/backend/src/modules/vitalia/sales_agent/` + `agentic/` | ✅ shipped (integrado inbox) |
| Fidelización (NPS + 5 templates Meta-approved) | `vitalia/backend/src/modules/vitalia/fidelizacion/` | ✅ shipped orphan |
| Referrals leaderboard | `vitalia/backend/src/modules/vitalia/marketing/referrals_leaderboard/` | ✅ shipped (en Lucas — mudar a Camila) |
| CRM Patients | `vitalia/backend/src/modules/vitalia/{crm,patients}/` | ✅ shipped orphan |
| Connections (9 OAuth providers) | `vitalia/backend/src/modules/vitalia/connections/` | ❌ NO Hub FE |
| IAM RBAC | `vitalia/backend/src/modules/vitalia/iam/` | ❌ NO Settings equipo FE |
| Compliance (HIPAA-lite audit) | `vitalia/backend/src/modules/vitalia/compliance/` | ✅ medical-compliance dashboard |
| Payment (MP + Stripe + cuotas) | `vitalia/backend/src/modules/vitalia/payment/` | ❌ UI faltante |
| Brand Studio simplificado 4 secciones | `vitalia/backend/src/modules/vitalia/brand_studio/` | ✅ shipped |
| Booking advisory locks + 30% deposit | `vitalia/backend/src/modules/vitalia/booking/` | ✅ shipped |
| Social proof (testimonios + casos pre/post) | `core/luana-core-social-proof/` | ✅ BE core / ❌ FE galería filtrable |

### Gaps planned (no shipped)

- Reseñas externas multi-source (Google My Business · Doctoralia · Yelp APIs)
- Menciones redes social listening (IG · TikTok · FB)
- Pipeline Kanban FE (solo mockup — REUSE base `nicolify/frontend/src/features/closer-studio/`)
- Settings shell cohesivo FE (REUSE base `nicolify/frontend/src/features/settings/` + `core/luana-core-ui/`)
- LLM keys BYO (REUSE nicolify `settings/llm-keys`)
- Camila AI archetype distinto a Adrián (ej. `relationship_keeper`) — BE reusa arquitectura sales_agent

---

## Mockups ratificados de referencia (no tocar — REUSE patterns)

| Mockup | Path | Patrones clave a preservar |
|---|---|---|
| `inbox.html` v1 Batch 2 | `/home/chalreme/Trabajo/Vitalia/Prototipos/inbox.html` | Segmented control 3-modos · ConversationList chips · ContactSidebar PHI masked · Activity Stream · Estados (success/empty/thinking/waiting-approval/failed) · Voice transcript · Image analysis · Revertir 4:32 |
| `pipeline.html` v1 Batch 3 | `/home/chalreme/Trabajo/Vitalia/Prototipos/pipeline.html` | 6 cols dental kanban · atribución agéntica visible Lucas/Adrián · card hover peek · funnel breakdown · @dnd-kit/core · "Decidió no" → re-engagement Camila |
| `agenda.html` v1 Batch 4 | `/home/chalreme/Trabajo/Vitalia/Prototipos/agenda.html` | Grilla calendario semana · 4 estados slot (PAGADO/depósito/SIN PAGO/NO-SHOW) · iconos origen (🚶📞✉) · drawer slot con subform Cobrar saldo + Capa 2 fiscal Nubefact |
| `dual-mode-shell.html` concept | `vitalia/docs/product/stories/vitalia-shell-organism/mockups/dual-mode-shell.html` | Split 50/50 web vs agéntico · ribbon Word-style en panel derecho · navegación direccional ↑↓←→ · URL bar siempre visible |

---

## Logros de la sesión

✅ Convergencia con benchmarks industria 2026 (Square / Jane / Cliniko / Pabau / Boulevard / PatientNow / Aesthetix / Birdeye / BoomCloud / Kangaroo)
✅ Eliminación Caja ERP-style (cobro 100% inline en agenda)
✅ Atomic ownership P1 cementado cross-agente (referidos mudan de Lucas → Camila)
✅ Modelo datos Servicios + Escalera (TreatmentEntity + LadderSlot n:m)
✅ Paradigma agéntico explícito Camila (3-modos + 12 triggers SSoT + reglas configurables)
✅ Distinción Adrián Outbound (leads) vs Camila Reactivar (pacientes existentes)
✅ HIPAA-lite suavizado (no es centro UX, es check-mark)
✅ Configurar simplificado a 3 sub-tabs (Valeria-céntrico — UI es espejo, no camino principal)
✅ Modelo cross-agente híbrido formal (Q7 Opción A — cada agente modelo propio según naturaleza)

---

## Reglas operativas no negociables (cementadas P1-P5)

| Principio | Cementado |
|---|---|
| **P1** | Atomic ownership — cada átomo tiene UN dueño semántico; otros agentes consumen read-only |
| **P2** | Recomendaciones cross-agente → bell icon TopBar (no sub-tab dedicada) |
| **P3** | Conexiones SIEMPRE en Configurar con `<RequireConnection>` inline |
| **P4** | Campañas son workspaces, no formularios (brief + audiencia + creatividades + copy + materiales + aprobación + performance + post-mortem) |
| **P5** | Backend DDD + Frontend FSD NO se rearman según agentes — metáfora agéntica = UI + UX + marketing, no estructura filesystem |

---

## Verificación próxima sesión

Antes de empezar, verificá:

```bash
cd /home/chalreme/Proyectos/luana-vitalia
git status --short
git branch --show-current   # debe ser wip/vitalia
git log --oneline -3

ls vitalia/docs/product/stories/vitalia-shell-organism/
# Debe incluir: 00-session-baseline.md (~1700 lines), HANDOFF-next-session.md (este doc),
# navigation-tree.md (a reemplazar), agentic-navigation-proposal.md (parcial obsoleto),
# vitalia-feature-inventory.md, nicolify-feature-inventory.md, mockups/dual-mode-shell.html

ls vitalia/frontend/public/agents/
# Debe incluir: lisa/ lucas/ adrian/ valeria/ camila/ mateo/ (cada uno con thumbnail.png + full.png/jpeg)
```

Si Chris quiere abrir mockup actual en browser para refresco visual:
```bash
xdg-open vitalia/docs/product/stories/vitalia-shell-organism/mockups/dual-mode-shell.html
```

---

## Recomendación post-handoff (consideración Chris)

**Antes de cerrar sesión actual:** considerá hacer commit-push del trabajo:

```bash
# Opción 1 — delegar a Haiku worker (recomendado por volume de docs)
# Usar /commit-push con plan verbatim:
#   - Stage: vitalia/docs/product/stories/vitalia-shell-organism/{00-session-baseline.md,HANDOFF-next-session.md}
#   - Commit message: "docs(vitalia): shell-organism sesión 2026-05-21 — 17 decisiones cementadas + handoff"

# Opción 2 — manual rápido
cd /home/chalreme/Proyectos/luana-vitalia
git add vitalia/docs/product/stories/vitalia-shell-organism/00-session-baseline.md
git add vitalia/docs/product/stories/vitalia-shell-organism/HANDOFF-next-session.md
git status --short   # verificar antes commit
git commit -m "$(cat <<'EOF'
docs(vitalia): shell-organism sesión 2026-05-21 — 17 decisiones cementadas + handoff

Cementa estructura completa shell-organism agéntico:
- 5 agentes-cara (Lisa/Lucas/Adrián/Valeria/Camila) + Configurar + Mateo transversal
- Sub-estructuras finales por agente con modelo propio (Lucas v2 ciclo · resto espacial)
- Paradigma agéntico Camila (3-modos + 12 triggers SSoT + reglas configurables)
- 17 decisiones de diseño cerradas (Q1-Q7 + sub-Qs)

HANDOFF-next-session.md contiene prompt copy-paste para retomar nueva conversación
arrancando por refit mockup dual-mode-shell.html opción A.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
git push origin wip/vitalia
```

Después de commit-push, podés cerrar esta sesión con tranquilidad.
