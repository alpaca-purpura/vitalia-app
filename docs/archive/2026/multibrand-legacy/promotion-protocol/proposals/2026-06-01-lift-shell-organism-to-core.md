---
proposal_id: 2026-06-01-lift-shell-organism-to-core
state: migrated                # proposed | under_review | accepted | rejected | migrated
opened_date: 2026-06-01
opened_by: /pm-luana
ratified_by: Chris             # dirección 2026-06-01 + APPROVED formal del lift 2026-06-06 (target reconciliado → @luana/ui-kit). Ejecución gated tras 4 stories abiertas
ratified_date: 2026-06-06
migrated_date: 2026-06-11
migrated_story: docs/archive/2026/stories/platform-lift-shell-chrome-ui-kit/   # cadena autónoma ratificada Chris 2026-06-11
migrated_semver: "0.4.0"       # minor additivo (organism/shell nuevo; exports previos intactos; deps react-resizable-panels+zustand)
lift_summary: >-
  Chrome shell-organism completo (30+ componentes) liftado a core/@luana/ui-kit/src/organism/shell/
  brand-agnostic (props+CSS vars: supervisorName/agentCatalog/getAgentClasses/testIds/slots;
  createShellStore factory SSR-safe vía @luana/hooks con migrate inyectable). Vitalia consume vía
  ShellLayoutWire (chrome local BORRADO, suite e2e 84/85+fixme + resizer-matrix 7/7 contra el kit);
  nicolify CONVERGE (máquina legacy luanaState retirada, 30 archivos, 514/514) — mirror cross-brand
  MUERTO (basename-scan chrome = 0, allowlist → ∅). Comunify/lupulo: opt-in futuro (kit listo).
  Evidencia: docs/archive/2026/stories/platform-lift-shell-chrome-ui-kit/{07-merge.md,CHECKPOINTS.md}.

# Origen — mirror cross-brand CONCRETO (ya no preventive)
origin_learnings:
  - vitalia/docs/learnings/2026-05-22-shell-mockup-per-component-protocol.md
origin_brands: [vitalia, nicolify]   # vitalia construyó el shell-organism; nicolify lo portó verbatim re-temizado

# Target
target_package: core/@luana/ui-kit          # reconciliado 2026-06-06: luana-core-ui NO existe; el package UI real es @luana/ui-kit (sin organism layer aún). umbrella: 2026-05-21-luana-core-ui-extraction
target_module: src/components/organism/shell/   # ShellOrganismLayout + Ribbon + SubTabsBar + SubSubTabsBar + ValeriaSidebar/Rail + AppPanelSlot + shell-routes helpers
target_ep: null              # TS UI (copy-paste shadcn-style), no Python EP

# Impact assessment
semver_bump: minor           # nuevo organism layer dentro de core-ui (0.x)
breaking_change: false       # brands opt-in / retrofit
brands_affected_consumers: [vitalia, nicolify, comunify, lupulo]
brands_at_risk_regression: [vitalia, nicolify]   # ambos tienen el shell shipped → arch test downstream obligatorio

# Lift plan
lift_estimated_effort: "1-2 semanas (organism layer grande: layout + ribbon + subtabs + sidebar + routing helpers + re-theming hooks)"
lift_owner: /dev-team
arch_test_downstream_required: true   # R3 — correr e2e/vitest de vitalia + nicolify post-lift
migration_notes_required: true        # ambos brands deben re-wire a core (no es package nuevo vacío)

# Parent / relacionados
parent_proposal: 2026-05-21-luana-core-ui-extraction   # umbrella UI; organism/shell estaba DEFERRED "pending Chris agentic idea"
unblocked_by: docs/architecture/luana-platform/PARADIGM.md   # 2026-05-30 cementó el modelo agéntico (la "idea pending" del parent)
related_adr: docs/architecture/luana-platform/ADR-008-luana-core-ui-shadcn-cli-pattern.md
---

## /pm-luana review (under_review · 2026-06-06)

**Recomendación: ACCEPT** — mirror cross-brand CONCRETO confirmado (vitalia + nicolify ambos shippearon el shell; nicolify es copia independiente verbatim re-temizada). Dirección ya ratificada por Chris 2026-06-01. Caso canónico de `anti-duplication.md`.

⚠️ **Corrección de target (verify 2026-06-06):** `core/luana-core-ui` **NO existe**. El package UI real es **`core/@luana/ui-kit`** (TS namespace) y aún SIN capa `organism/`. El lift debe apuntar a `core/@luana/ui-kit/src/components/organism/shell/`, no a `luana-core-ui`. Mismo drift en el parent (ui-extraction).

**Secuencia:** depende del parent `2026-05-21-luana-core-ui-extraction` (umbrella). Ratificar ambos juntos; el shell se ejecuta DESPUÉS de que el umbrella consolide el organism layer en `@luana/ui-kit`.

**Para ratificar (Chris):** APPROVED formal del lift execution (1-2 sem `/dev-team`, arch-test downstream vitalia+nicolify obligatorio, migration notes). Al APPROVED → `accepted` + outcome platform + stories consumer.

---

## 1. Patrón a promover

El **shell-organism agéntico** (TopBar + Ribbon de agentes + SubTabsBar/SubSubTabsBar N3 + ValeriaSidebar/Rail + AppPanelSlot + splitter resizable + helpers de routing `shell-routes.ts`, `extractAgentFromPath`, `extractSubtabFromPath`, `SubTabMeta`, `AGENT_CATALOG`/`AGENT_RIBBON_ORDER`). Es el wrapper de navegación que encarna el Paradigma de 3 zonas (Agentes/Plataforma/Infra) — `PARADIGM.md`.

El parent `2026-05-21-luana-core-ui-extraction` dejó el **organism layer DEFERRED** ("PATTERN PENDING REVIEW con Chris antes de cementar shell/navigation"). Esa idea **ya está cementada** en `PARADIGM.md` (2026-05-30). Y el mirror que en 2026-05-21 "no existía todavía" **ya es concreto**: vitalia construyó el shell completo y **nicolify lo portó verbatim re-temizado** (design intent del rebuild nicolify — skill `nicolify-design-system`).

## 2. Por qué cross-brand (mirror CONCRETO, evidencia 2026-06-01)

| Brand | Estado | Evidencia |
|---|---|---|
| vitalia | ✅ shipped (origen) | `vitalia/frontend/src/components/shared/shell-organism/` + `lib/shell-routes.ts` + `lib/agent-catalog.ts` |
| nicolify | ✅ shipped (port verbatim re-temizado) | `nicolify/frontend/src/components/shared/shell-organism/` + `lib/routing/shell-routes.ts` — ShellOrganismLayout ×7, SubTabsBar ×10, SubTab ×14, Ribbon ×18, useShellStore ×12, AGENT_CATALOG ×13 (NO importa de vitalia — copia independiente) |
| comunify | candidato | shell pendiente; heredaría de core |
| lupulo | candidato | idem |

Es **exactamente** el caso de `.claude/rules/anti-duplication.md`: "dos brands replican mismo patrón → lift a core". El propio arch-test de vitalia (`test-no-cross-brand-shell-mirror.test.ts` línea 111-112) ya lo anticipa: *"if a second brand adopts a similar pattern, escalate to /pm-luana for promotion to core/@luana/... (LIFT CANDIDATE documented)."*

## 3. Tensión que resuelve (gate roto hoy)

`vitalia/frontend/src/__tests__/architecture/test-no-cross-brand-shell-mirror.test.ts` es **zero-tolerance por NOMBRE**: falla si cualquier símbolo del shell vitalia aparece en otra brand. Con el port deliberado de nicolify, falla (~23 vitest fails, **pre-existente en origin/main**). La premisa del test ("ninguna otra brand tendrá shell") quedó obsoleta cuando el rebuild nicolify adoptó el shell por diseño.

**Generalización a producir en el lift:** parametrizar lo brand-specific (agent catalog, tokens/colores, voz Valeria→supervisor-name, copy) de modo que el wrapper viva en core y cada brand inyecte su catálogo + theme. El `AGENT_CATALOG` y los nombres `Valeria*` se vuelven props/config, no hardcode.

## 4. Acción inmediata ratificada por Chris (2026-06-01)

Dirección ratificada: **lift a core + ajustar el arch-test** (NO renombrar en nicolify — sería cosmético y ocultaría el mirror real).

- **Interim (vitalia FE, vía builder):** ajustar `test-no-cross-brand-shell-mirror.test.ts` para que (a) siga detectando IMPORTS cross-brand reales (la pollution de verdad — vitalia↔nicolify NO se importan, confirmado), y (b) trate el set de símbolos del shell-organism como **mirror sancionado conocido** (ratchet allowlist) que apunta a esta proposal, fallando solo ante mirrors NUEVOS no sancionados. Esto desbloquea los ~23 vitest honestamente sin perder la protección anti-mirror para casos nuevos.
- **Lift completo (esta proposal, post APPROVED formal):** `/dev-team` extrae el organism a `core/luana-core-ui` + re-wire vitalia + nicolify + arch-test downstream + migration notes.

## 5. Estado / próximos pasos

- `state: proposed`. Chris ratificó la DIRECCIÓN; falta APPROVED formal del lift execution (es esfuerzo 1-2 semanas → planificar como story/outcome platform, no inline).
- Interim test-adjust: handoff `/pm-vitalia` → builder-frontend (tracked en checkpoint de la sesión 2026-06-01).
- Al APPROVED → mover a `accepted` + abrir outcome platform + stories consumer vitalia/nicolify.

## Estado post vitalia-shell-core-hardening (2026-06-10)

> Actualización de estado tras el cierre de `vitalia-shell-core-hardening` (8 tickets, branch wip/vitalia). No ejecuta el lift completo — documenta lo ya hecho y actualiza el roadmap de lift.

### Lo que ya vive en `@luana/ui-kit` (liftado en T-5)

| Componente | Versión kit | Commit | Consumers vitalia |
|---|---|---|---|
| `EntitySubNavBar` | 0.3.x | `a042e1df` (delete brand-local) · `d3b06b11` (activeLeaf prop) | `StaffWorkspaceShell` · `LeadWorkspace` · `NewLeadPage` |
| `EntityWorkspaceLayout` | 0.3.x | `8d62c958` | `StaffWorkspaceShell` · `LeadWorkspace` |

**Brand-local `components/shared/shell-organism/EntitySubNavBar.tsx` ELIMINADO** en T-5 (258 líneas). Arch test `test-no-cross-brand-shell-mirror.test.ts` 31/31 PASS verifica ausencia del mirror.

Prop `activeLeaf?: string | null` agregada al kit como override opcional (backward-compatible, commit `d3b06b11`).

### Chrome hardened — ready for lift evaluation

El chrome agéntico (TopBar + splitter + ValeriaSidebar + Ribbon + SubTabsBar) fue hardened en vitalia-shell-core-hardening. Estado post-hardening:

| Componente | Estado | E2E coverage | Notas lift |
|---|---|---|---|
| `ValeriaCollapsedStrip` | ✅ nuevo, brand-local | `e2e/regression/shell-core-hardening/valeria-strip.spec.ts` | Candidato lift con `ValeriaSidebar` |
| `ValeriaSidebar` (máquina nueva) | ✅ hardened | `valeria-states.spec.ts` 8/8 PASS | Requiere parametrizar agente-nombre |
| `ShellOrganismLayoutClient` | ✅ hardened | `resize-and-state.spec.ts` 8/8 PASS | Layout + splitter + breakpoints |
| `TopBarGlobal` (cluster fijo) | ✅ hardened | `topbar.spec.ts` | Chip eliminado, orden ThemeToggle→TenantSwitcher |
| `Ribbon` + `SubTabsBar` | sin cambio en hardening | previos | Parametrizar `AGENT_CATALOG` |

**Estado máquina Valeria hardened:** `valeriaOpen: 'closed'|'chat'` + `historyOpen: boolean` — `ShellMode`/`ValeriaState` RETIRADOS. El estado está probado con 52 E2E passing + 2 flaky-on-retry (theme-hydration timing, conocidos).

### Lo que requiere el lift completo (pendiente governance /pm-luana)

1. **Parametrización brand-specific:** `AGENT_CATALOG`, `AGENT_SUBTABS`, `AGENT_RIBBON_ORDER`, nombre "Valeria" → prop `supervisorName` configurable.
2. **Theming hook:** colores agente (`--agent-lisa`, etc.) como config inyectable por brand.
3. **Re-wire vitalia + nicolify** post-lift (migration notes obligatorias per proposal §lift_plan).
4. **Arch-test downstream:** e2e/vitest vitalia + nicolify post-lift (ver `arch_test_downstream_required: true`).
5. **Desbloquear:** parent proposal `2026-05-21-luana-core-ui-extraction` debe consolidar organism layer en `@luana/ui-kit` primero.

### Nicolify convergence (siguiente paso cross-brand)

Nicolify portó el shell verbatim re-temizado (evidencia en §2 de esta proposal). Tras el hardening de vitalia, los dos shells divergen en:
- Vitalia: máquina `valeriaOpen/historyOpen` (nueva) · Nicolify: máquina legacy `valeriaState` (vieja)
- Vitalia: `ValeriaCollapsedStrip` (nueva, 44px) · Nicolify: `ValeriaRail` equivalente

**Recomendación para /pm-luana:** sincronizar nicolify al modelo hardened de vitalia ANTES del lift para reducir divergencia. La convergencia es más barata ahora que post-lift (dos brands, dos re-wires).

## Referencias

- `.claude/rules/anti-duplication.md` — "dos brands replican → lift a core"
- `docs/promotion-protocol/proposals/2026-05-21-luana-core-ui-extraction.md` — umbrella (organism estaba DEFERRED)
- `docs/architecture/luana-platform/PARADIGM.md` — modelo agéntico cementado (la idea pending del parent)
- `vitalia/frontend/src/__tests__/architecture/test-no-cross-brand-shell-mirror.test.ts` — gate roto
- `.claude/skills/nicolify-design-system/SKILL.md` — "portar verbatim de Vitalia re-temizado" (design intent del mirror)
- `vitalia/docs/architecture/SHELL-DESIGN-CONTRACT.md` § v1.4 — chrome hardened SSoT
- `vitalia/docs/product/stories/vitalia-shell-core-hardening/T-{1..7}-result.md` — evidencia commits hardening
