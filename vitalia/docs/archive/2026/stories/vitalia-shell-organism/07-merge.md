# Merge artifact — vitalia/vitalia-shell-organism

> **Brand:** vitalia
> **Tipo:** design-story (planning-only, NO produce código)
> **Merged at:** 2026-05-22
> **Commit (squash-merge):** TBD (commit final del task tracker shell-organism — incluirá este 07-merge + git mv archive R2)
> **Auditor:** N/A — design-story ratificada por Chris (mockup visual + decisiones)

---

## § 1 — Decisiones cementadas (sustituye Gherkin verification matrix)

> Esta sección reemplaza el `§ 1 Gherkin verification matrix` del template estándar 07-merge porque la story es planning-only. En lugar de tests pasados, listamos las decisiones que se cementaron y dónde viven.

### Decisiones de paradigma (17 — ver `00-session-baseline.md` § 5)

| # | Pregunta | Decisión | Path SSoT |
|---|---|---|---|
| Q1 | ¿Mateo a Configurar? | NO — Configurar es ícono genérico admin | baseline § 5 |
| Q1.b | ¿Qué pasa con Mateo? | Transversal sin tab (landing + diseño gráfico futuro) | baseline § 5 + navigation-tree § 1 `transversal` |
| Q2 | Reseñas Google/Yelp ¿Camila o Lisa? | Camila dueña TODO relación-cliente | navigation-tree Camila |
| Q3 | Menciones redes ¿Camila o Lucas? | Camila (marca) + Lucas (mercado) | navigation-tree |
| Q4 | Calendario contenido orgánico ¿Lucas o tab nueva? | Lucas unificado (paga + orgánica) | navigation-tree Lucas |
| Q4.b | Subestructura Lucas v1 vs v2 | v2 ciclo-temporal (Lanzar/En vuelo/Recursos/Resultados/Mercado) | navigation-tree Lucas `model: ciclo-temporal-v2` |
| Q-valeria-macro | Universo Valeria | 2 sub-tabs (Agenda · Pacientes) sin Caja ERP | navigation-tree Valeria |
| Q-doctores | ¿Dónde viven los doctores? | Lisa Mi Clínica (asset semi-estático) | navigation-tree Lisa.doctores |
| Q5 | Pagos en recepción | Eliminar sub-tab Caja — cobro 100% inline slot agenda | navigation-tree Valeria.agenda + anti-creep § 4 |
| Q6 | Audit log HIPAA | Híbrido suave: Lisa Compliance dashboard + Configurar raw log | navigation-tree Lisa.compliance + Configurar.avanzado |
| Q-mi-clinica | Estructura macro Lisa | 4 sub-tabs (Marca · Doctores · Servicios · Compliance) | navigation-tree Lisa |
| Q-servicios-vs-ladder | ¿Catálogo y Escalera separadas? | NO — una sub-tab Servicios con toggle | navigation-tree Lisa.servicios |
| Q-vender-macro | Estructura macro Adrián | 4 sub-tabs (Inbox · Embudo · Outbound · Propuestas opt-in) | navigation-tree Adrián |
| Q-mantener-macro | Estructura macro Camila inicial | (post-refit v3) | superseded by Q-camila-v3 |
| Q-camila-v3 | Refit Camila | 4 sub-tabs (Voz · Reactivar · Multiplicar · Reputación) | navigation-tree Camila |
| Q-configurar-macro | Estructura Configurar | 3 sub-tabs (Mi cuenta · Conexiones · Avanzado) | navigation-tree Configurar |
| Q7 | Modelo cross-agente | Opción A — modelo propio per agente según naturaleza | Design Contract § 3 |
| Q-camila-agente-ops | Cómo opera Camila como agente IA | 3-modos + 12 triggers SSoT + reglas configurables | navigation-tree Camila + 00-baseline § 11 |

### Decisiones técnicas ratificadas (5 — sesión 2026-05-22)

| # | Decisión | Implicancia | Path SSoT |
|---|---|---|---|
| D1 | Instalar Shadcn UI ahora en `vitalia/frontend/` | F1-S0 ejecuta `npx shadcn@latest init` | Design Contract § 4 |
| D2 | Deprecar `.vt-*` utility classes COMPLETO | Migration story dedicada al final Fase 2 | Design Contract § 5.3 |
| D3 | Migration path = route group paralelo `(shell-organism)/` | Coexiste con `(dashboard)/` viejo | Design Contract § 7 |
| D4 | Verificar Tailwind v4 empíricamente | F1-S0 incluye `make dev-vitalia` + browser visual check | Design Contract § 1 D4 |
| D5 | Atomic design strict | Átomos · moléculas · organismos · templates · pages | Design Contract § 2 |

---

## § 2 — Playwright E2E run (sustituye con: Verificación visual mockup)

> Esta sección reemplaza el `§ 2 Playwright E2E run` del template estándar 07-merge porque la story es planning-only. En lugar de specs E2E, listamos la verificación visual del mockup HTML.

**Verificación mockup HTML (ratificación Chris 2026-05-22):**

```bash
WS=$(git rev-parse --show-toplevel)
xdg-open ${WS}/vitalia/docs/product/stories/vitalia-shell-organism/mockups/dual-mode-shell.html
```

**Funcionalidades verificadas por Chris (visual + interacción):**

- [x] TopBar global thin: logo · theme toggle (🌗) · tenant switcher (🏥 Sonrisa Plena ▾)
- [x] Tenant switcher dropdown muestra 3 clínicas + "+ Agregar" + "⚙️ Administrar cuenta"
- [x] Theme toggle alterna light/dark con persistencia localStorage
- [x] Panel Valeria 50% izquierdo con grid interno [Rail/History] [Chat]
- [x] Rail 60px con 7 íconos (📂 ➕ 🔍 📌 ✅ 📝 ⏴) + tooltips al hover
- [x] History 280px expandida con buscador + grupos Hoy/Ayer/Esta semana + 8 conversaciones placeholder
- [x] Keyboard shortcuts: C (collapsed) · R (rail) · F (full) · N (alert nueva) · Esc (close)
- [x] Chat Valeria: header con avatar PNG + status + chip "🤖 Modo agente"
- [x] Chat messages: 5 mensajes ejemplo con delegación visible "→ delegando a 🟦 Camila"
- [x] Thinking dots animados durante streaming
- [x] Composer textarea + íconos (📎 🎙️ ⚡) + botón Enviar morado
- [x] Panel App 50% derecho con ribbon 6 tabs + sub-tabs línea 2 + contenido
- [x] Ribbon: 5 agentes con PNG thumbnails + label tab + nombre agente debajo + ⚙️ Configurar
- [x] Tab activa: border-bottom 3px color oficial agente + avatar con borde color
- [x] Sub-tabs línea 2 con tint color agente per sub-tab activa
- [x] Contenido tab activa: empty-states navegables + UI especial para Servicios (toggle Catálogo|Escalera), Embudo (Kanban 6 cols), Inbox (3-modos), Agenda (grilla semana + slot states), Conexiones (6 categorías)
- [x] Footer dev info con kbd hints

**Output verificación:** ✅ Chris confirmó "ME encantó!, por fin lo logramos!" 2026-05-22

---

## § 3 — Capabilities updated/created

> Esta story NO ship código → NO actualiza `capabilities/*.yaml`. Las capabilities se crearán/actualizarán en cada story Fase 1 + Fase 2 al merge respectivo.

NEW capability inventoriada como parte de Fase 1 (cuando merge):

- `shell.shell-organism-foundation` — al merge F1-S10 (último átomo Fase 1)
- `agent.{name}.{subtab}` — al merge cada story Fase 2 (×22)

---

## § 4 — Modules MD refreshed

> N/A — design-story. Modules refresh ocurre en cada story Fase 1/2 al merge.

---

## § 5 — How to verify (reproducible commands)

```bash
WS=$(git rev-parse --show-toplevel)

# 1. Mockup HTML ratificado (visual check humano)
xdg-open ${WS}/vitalia/docs/product/stories/vitalia-shell-organism/mockups/dual-mode-shell.html

# 2. Verificar artifacts producidos existen
ls ${WS}/vitalia/docs/architecture/SHELL-DESIGN-CONTRACT.md
ls ${WS}/vitalia/docs/specs/templates/01-spec-shell-template.md
ls ${WS}/vitalia/docs/product/stories/vitalia-shell-organism/{00-session-baseline,navigation-tree,checkpoint,07-merge}.md

# 3. Verificar backlog generado (24 stories nuevas)
ls ${WS}/vitalia/docs/product/stories/vitalia-fase1-* 2>/dev/null | wc -l    # esperado: 11
ls ${WS}/vitalia/docs/product/stories/vitalia-fase2-* 2>/dev/null | wc -l    # esperado: 22

# 4. Verificar outcome master refactorizado
cat ${WS}/vitalia/docs/product/outcomes/vitalia-mvp-ui-foundation.md | head -50

# 5. Verificar brand checkpoint refresh
cat ${WS}/vitalia/docs/product/checkpoint.md | head -30

# 6. Regen BACKLOG local (gitignored R3, solo render)
.venv/bin/python ${WS}/scripts/generate_backlog.py --brand vitalia
cat ${WS}/vitalia/docs/product/BACKLOG.md | head -80
```

**Expected:** todos los archivos existen + backlog renderiza 24+ stories nuevas agrupadas por estado.

---

## § 6 — Próximo paso recomendado

**Handoff a `/po-ux`** para arrancar refining de F1-S0 (`vitalia-fase1-stack-stability`) — primera story implementable. Esta story:
- Verifica Tailwind v4 runtime empíricamente
- Instala Shadcn UI (`npx shadcn@latest init`)
- Define plan deprecación `.vt-*` (incremental)

Una vez F1-S0 done, las stories F1-S1..F1-S10 pueden arrancar en paralelo según dependency map (ver outcome master `vitalia-mvp-ui-foundation.md`).

---

## § 7 — Lessons / Learnings

| Learning | Promotable cross-brand |
|---|---|
| Design-story como categoría legítima (planning-only sin código) merece template propio + bypass story-closure-gate auditor | candidate · todas las brands necesitan este tipo de session-output |
| Mockup HTML como source-of-truth visual (verificable con Playwright golden) ANTES de tocar código previene drift entre intención visual y resultado | candidate · pattern aplicable a cualquier brand redesign UX |
| Atomic design strict (átomos · moléculas · organismos · templates · pages) como contrato técnico de stories evita scope creep + facilita reuse cross-feature | candidate · ya existe en Nicolify pero no estaba cementado como rule cross-brand |
| Spawning Agent Explore en paralelo para inventario antes de planning saved ~hours de context burn + decisiones informed | candidate · pattern de Discovery Round 1 ya integrado en `/pm-luana` `/pm-{brand}` skills (pointer-first), pero el USO explícito de Explore antes de planning grandes es worth documenting |

Learnings a archivar en `vitalia/docs/learnings/2026-05-22-shell-organism-planning.md` post-cierre.

---

## § 8 — Closure metadata

- **state:** `done`
- **transitioned at:** 2026-05-22
- **next archive move:** pending hasta task #12 del task tracker (todos los downstreams generados)
- **archive path final:** `vitalia/docs/archive/2026/stories/vitalia-shell-organism/`
