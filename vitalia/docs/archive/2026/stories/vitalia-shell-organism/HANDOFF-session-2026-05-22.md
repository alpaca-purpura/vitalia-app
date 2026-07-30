<!-- voseo-allowed: internal handoff documentation for session continuation -->

# HANDOFF — Sesión /pm-vitalia 2026-05-22 (planning shell-organism)

> **Snapshot final · Contexto al 55% antes de cierre · Chris pidió pasar a nueva conversación**

---

## ✅ Lo que se completó esta sesión (Tasks 1-6 de 14)

| Task | Output |
|---|---|
| #1 — Design Contract | `vitalia/docs/architecture/SHELL-DESIGN-CONTRACT.md` (33,561 bytes · 13 secciones · atomic design layers · tokens · stores · routing · a11y · testing strategy) |
| #2 — Template story detallado | `vitalia/docs/specs/templates/01-spec-shell-template.md` (18,342 bytes · 14 secciones · 9 Gherkin scenarios tipo · checklist zero deuda) |
| #3 — Cierre shell-organism story | `navigation-tree.md` (JSON tree completo) · `checkpoint.md` (state=done design-story) · `07-merge.md` (5 secciones cementadas adaptadas) |
| #4 — Refactor outcome master + brand checkpoint | `outcomes/vitalia-mvp-ui-foundation.md` (REFACTOR v2.0 contenedor Fase 1+2) · `product/checkpoint.md` MODIFY |
| #5 — Story F1-S0 stack-stability | `stories/vitalia-fase1-stack-stability/checkpoint.md` (detallado: Shadcn install + Tailwind v4 verify + .vt-* deprecation plan) |
| #6 — 10 stories Fase 1 átomos | 10 checkpoints creados con scope + AC + Gherkins + deliverables (cada uno cita Design Contract + template como SSoT) |

**Archivos creados/modificados:** 19 (15 NEW · 4 MODIFY)

**Stories Fase 1 (11 checkpoints listos):**

```
F1-S0  vitalia-fase1-stack-stability         (blocker hard de toda Fase 1)
F1-S1  vitalia-fase1-design-tokens-theme     (CSS vars + ThemeProvider + ThemeToggle)
F1-S2  vitalia-fase1-topbar-global           (TopBar thin 48px + LogoMark)
F1-S3  vitalia-fase1-tenant-switcher         (REUSE 95% nicolify pattern)
F1-S4  vitalia-fase1-shell-layout-5050       (grid 50/50 + route group nuevo)
F1-S5  vitalia-fase1-valeria-rail-history    (TRANSPONER copilot Nicolify)
F1-S6  vitalia-fase1-valeria-chat-skeleton   (chat structure mock + 6 mensajes)
F1-S7  vitalia-fase1-ribbon-6-tabs           (5 agentes + Configurar)
F1-S8  vitalia-fase1-sub-tabs-line2          (sub-tabs dinámicas per agente)
F1-S9  vitalia-fase1-routing-shell           (App Router pages + 404 + redirects)
F1-S10 vitalia-fase1-empty-states            (22 sub-tab placeholders + 6 especiales mockup parity)
```

---

## ⏳ Lo que falta (Tasks 7-14 — para nueva conversación)

| Task | Stories | Estimado tokens nueva sesión |
|---|---|---|
| #7 — 6 stories F2 Valeria + Adrián | F2-S1..F2-S6 | ~30k |
| #8 — 4 stories F2 Lisa | F2-S7..F2-S10 | ~20k |
| #9 — 4 stories F2 Camila | F2-S11..F2-S14 | ~20k |
| #10 — 5 stories F2 Lucas | F2-S15..F2-S19 | ~25k |
| #11 — 3 stories F2 Configurar | F2-S20..F2-S22 | ~15k |
| #12 — Refactor 2 stories + drop 1 | slice-1-agenda → fase2-valeria-agenda · slice-1-pipeline → fase2-adrian-embudo · slice-1-marketing-integration → DROPPED | ~10k |
| #13 — Service-stories laterales | Update checkpoints payment-adapter-mvp + fiscal-emission-pe con deps cruzadas a Fase 2 | ~5k |
| #14 — Regen BACKLOG + handoff final | `python scripts/generate_backlog.py --brand vitalia` + recomendación próximo paso | ~5k |

**Total stories Fase 2 a generar:** 22 stories + 3 refactor/drops = **25 archivos checkpoint nuevos/cambiados**

---

## 📋 Estado del backlog Vitalia post-cierre Fase 1 planning

| Layer | Cantidad |
|---|---|
| **Fase 1 — átomos shell (state=idea, listos para /po-ux refining)** | **11** |
| Fase 2 — sub-tabs activas (pending generación Task #7-#11) | 22 |
| Service-stories laterales (refining → ready cuando Fase 2 lo necesite) | 2 |
| Stories refactor pending (Task #12) | 2 |
| Stories drop pending (Task #12) | 1 |
| Total backlog new/changed esta sesión | 38 |

---

## 🚨 Decisiones técnicas cementadas Chris 2026-05-22 (recordar siempre)

| # | Decisión | Implicancia |
|---|---|---|
| D1 | Shadcn UI install AHORA | F1-S0 ejecuta `npx shadcn@latest init` |
| D2 | Deprecar `.vt-*` utility classes COMPLETO | 150+ classes migran progresivamente · F1-S0 define plan |
| D3 | Route group paralelo `(shell-organism)/` | Coexiste con `(dashboard)/` viejo hasta Fase 2 completa |
| D4 | Verificar Tailwind v4 empíricamente | F1-S0 incluye `make dev-vitalia` + browser visual check |
| D5 | Atomic design strict | átomos · moléculas · organismos · templates · pages |
| D6 | Cada componente requiere Playwright golden visual + funcional test | Zero deuda técnica desde origen |

---

## 🎯 Directiva Chris explícita (citar verbatim cuando duda)

> "Si o si debe haber un tenant_switcher visible · debe haber un switcher claro-oscuro · vamos a priorizar la vista Agentic · historial colapsado y con opción de abrirse (transpuesta copilot Nicolify) · ribbon expansible 2 líneas"
>
> "Detallista en cada átomo, molécula · tomate todo el tiempo necesario · no perder foco durante la elaboración · revisar lo que ya existe en vitalia, core, y código antiguo /home/chalreme/Documentos/ap_sales_agent para no empezar de cero · siempre verificar con playwright funcional + visual contra el mockup · estricto en proceso para no crear deuda técnica · reutilizar en la medida de lo posible siempre que sea técnicamente bien hecho"

---

## 🧠 Inventarios producidos (no volver a recorrer en nueva sesión — citar)

Resultados de 4 Agent Explore en paralelo durante esta sesión:

### Vitalia frontend (ya shipped)
- Stack: Next.js 16.2.3 · React 19.2.3 · Tailwind 4.1 ✅ operativo · TypeScript 5.9.3
- Shadcn: **NO instalado** (sistema custom `.vt-*`)
- Deps: `@clerk/nextjs`, `@tanstack/react-query`, `zustand`, `zod`, `nuqs`, `lucide-react`
- Routes: `(dashboard)/page`, `/appointments`, `/bookings/[id]`, `/brand-studio/[section]`, `/fidelizacion`, `/medical-compliance`, `/offers/...`, `/patients/...`, `/treatments/...`, `(app)/inbox/page`, etc.
- Features shipped: `vitalia`, `dashboard`, `inbox`, `fidelizacion`, `marketing`, `onboarding`, `crm-shared`, `marketing-shared`
- Shell actual: `AppShell + Sidebar 240px + TopBar 56px + CopilotRail` (paradigma viejo)
- Tokens: `globals.css` con vars `--vitalia-cian #01B2F8`, `--vitalia-purpura #7B2D91`, etc. (3 ya match agentes, falta `--agent-lisa #00D084` + `--agent-lucas #111111`)
- Test infra: Vitest + Playwright projects `smoke/a11y/mobile/visual` + Storybook

### Nicolify frontend (patterns reusables)
- **CopilotSidebar 80% transponible**: 3 estados grid `[chat][rail]` → invertir a `[rail][chat]` para Valeria · keyboard C/R/F/N/Esc/Cmd+K · ShellMutex context · mobile drawer pattern
- **TenantSwitcher 95% reusable**: solo cambiar storage key + redirect path
- **Z-Index tokens 100% copiable**: `nicolify/frontend/src/lib/tokens/z-index.ts`
- **Closer Studio (Pipeline) 70% reusable**: `ConversationPipelineBoard` con @dnd-kit/core
- **Connections HUB pattern reusable**: provider grid + drawer detalle
- **Shadcn primitives en Nicolify**: 44 componentes en `src/components/ui/` (referencia para qué instalar)
- **fetchClient pattern**: REUSE 100% para Vitalia con cambio key `X-Tenant-ID`

### Legacy `/home/chalreme/Documentos/ap_sales_agent`
- Stack: Next.js 16 + FastAPI · vertical sales NO medical
- **Modelos médicos:** NO EXISTE (Vitalia construye sus propios)
- **Sales agent LangGraph architecture:** ya migrado a `core/luana-core-sales-agent`
- **Recomendación final:** descartar para shell-organism · solo referencia para sales_agent (ya en core engine)

### Engine `core/luana-core-*`
- TODOS los packages son **Python-only** · NO hay TS bindings core
- Vitalia FE consume vía REST API + WebSocket
- `core/luana-core-ui` (ADR-008) **proposed**, NO implementado todavía
- Packages relevantes BE: `iam` (tenants) · `platform` (TenantLocale + utils) · `channels` (format_for_channel) · `copilot` · `observability` (PHI sanitize) · `compliance` (channel guards) · `offer-studio` (treatments + LadderSlot)

---

## 🔧 Recomendación pre-cierre (Chris debe ejecutar)

**Commit + push antes de cerrar sesión** para preservar todo el planning producido:

```bash
WS=$(git rev-parse --show-toplevel)
cd ${WS}

# Verify status primero
git status --short

# Stage por nombre exacto (NUNCA git add -A)
git add vitalia/docs/architecture/SHELL-DESIGN-CONTRACT.md
git add vitalia/docs/specs/templates/01-spec-shell-template.md
git add vitalia/docs/product/checkpoint.md
git add vitalia/docs/product/outcomes/vitalia-mvp-ui-foundation.md
git add vitalia/docs/product/stories/vitalia-shell-organism/
git add vitalia/docs/product/stories/vitalia-fase1-*

# Commit
git commit -m "$(cat <<'EOF'
docs(vitalia): /pm-vitalia planning sesión 2026-05-22 — Fase 1 backlog completa

Tasks 1-6 de 14 completas. Shell-organism story cerrada (design-story planning).
Outcome master refactorizado contenedor Fase 1 + Fase 2 (38 stories total).

Artefactos:
- SHELL-DESIGN-CONTRACT.md: atomic design layers + tokens + stores + routing + a11y + testing
- 01-spec-shell-template.md: template historia detallada 14 secciones + 9 Gherkin scenarios tipo
- shell-organism: navigation-tree.md JSON + checkpoint state=done + 07-merge.md
- outcome vitalia-mvp-ui-foundation v2.0
- 11 stories Fase 1 átomos: F1-S0..F1-S10 con scope + AC + Gherkins + deliverables

Pending (nueva conversación):
- Tasks 7-14: 22 stories Fase 2 + 3 refactor/drops + 2 service-stories update + handoff

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"

git push origin wip/vitalia
```

(O usar `/commit-push` skill para delegar a Haiku worker.)

---

## 📥 Prompt copy-paste para retomar en NUEVA conversación

Pegá EXACTAMENTE esto en la próxima sesión Claude Code (Opus 4.7 recomendado · /pm-vitalia activa automáticamente):

```text
Retomo /pm-vitalia desde sesión 2026-05-22 (planning shell-organism). Branch: wip/vitalia.

LEE EXACTAMENTE EN ESTE ORDEN:

1. vitalia/docs/product/stories/vitalia-shell-organism/HANDOFF-session-2026-05-22.md
   ↑ HANDOFF maestro · estado tasks 1-6 done + tasks 7-14 pending · inventarios producidos · decisiones cementadas D1-D6 · directiva Chris

2. vitalia/docs/architecture/SHELL-DESIGN-CONTRACT.md
   ↑ SSoT atomic design · TODA story Fase 2 cita este doc

3. vitalia/docs/specs/templates/01-spec-shell-template.md
   ↑ Template detallado 14 secciones · usar para todas las stories Fase 2

4. vitalia/docs/product/outcomes/vitalia-mvp-ui-foundation.md
   ↑ Outcome master v2.0 con backlog Fase 1+2 completo

5. (Solo si necesitás contexto extra):
   - vitalia/docs/product/checkpoint.md (brand checkpoint global)
   - vitalia/docs/product/stories/vitalia-shell-organism/navigation-tree.md (JSON tree 22 sub-tabs)
   - vitalia/docs/product/stories/vitalia-shell-organism/00-session-baseline.md (17 decisiones Q1-Q7)
   - vitalia/docs/product/stories/vitalia-shell-organism/mockups/dual-mode-shell.html (mockup visual SSoT)

ESTADO:
- Tasks 1-6 done (Design Contract + Template + Cierre shell-organism + outcome refactor + 11 stories Fase 1)
- Tasks 7-14 pending: 22 stories Fase 2 + 3 refactor/drops + 2 service-stories update + handoff

TU MISIÓN INMEDIATA:
Continuar generación de stories Fase 2 con el mismo nivel de detalle que Fase 1.

Orden recomendado:
- Task #7 (6 stories Valeria + Adrián — primer valor end-to-end)
- Task #8 (4 stories Lisa)
- Task #9 (4 stories Camila)
- Task #10 (5 stories Lucas)
- Task #11 (3 stories Configurar)
- Task #12 (refactor 2 + drop 1)
- Task #13 (service-stories update)
- Task #14 (regen BACKLOG + handoff final)

REGLAS NO NEGOCIABLES (re-citar verbatim):
- Cada story usa el template 01-spec-shell-template.md con scope + Atomic design layers + Reuse Map + Gherkin scenarios + Visual Goldens + AC + zero-deuda checklist + dependencies
- TODA story cita Design Contract como SSoT (NO re-explica tokens/atomic design)
- REUSE máximo (Nicolify CopilotSidebar transponer · TenantSwitcher 95% · Closer Studio Kanban · Connections HUB · etc.)
- Playwright visual golden contra mockup HTML obligatorio
- Spanish neutro LatAm (excepto sales_agent voz tenant)
- NO crear nada que ya exista (consultar inventarios en HANDOFF Task §inventarios producidos)

ARRANCA: TaskList para ver estado actual, después in_progress Task #7 + generar las 6 stories Valeria+Adrián (F2-S1 a F2-S6) en bloque. Después check-in con Chris.

NO PIDAS APROBACIÓN para arrancar — Chris ya ratificó plan completo.
```

---

## Resumen ejecutivo

| Métrica | Valor |
|---|---|
| Stories Fase 1 listas para refining | **11** ✅ |
| Stories Fase 2 pending generación | **22** |
| Refactor/drops pending | **3** |
| Service-stories update pending | **2** |
| Artifacts cementados (Design Contract + Template + Cierre + Outcome) | **6** ✅ |
| Archivos producidos esta sesión | **19** (15 NEW · 4 MODIFY) |
| Decisiones técnicas ratificadas | **D1-D6** ✅ |
| Próximo skill recommended | `/pm-vitalia` (Task #7 onwards) |
| Modelo recomendado nueva sesión | Opus 4.7 (1M context) — calidad mantenida |

**Visión norte:** "Como una secretaria real." Vitalia shell-organism agéntico con 5 empleados-IA (Lisa · Lucas · Adrián · Valeria · Camila) + Configurar admin, panel Valeria chat persistente 50% izq + panel App 50% der con ribbon 6 tabs.
