---
name: architect
description: "Architect orchestrator Luana v4 — lee 01-spec.md (+02-design-agentic.md si agentic) en stories state=refined, spawna architect-orchestrator full-stack y produce el READY PACKAGE (03-arch.md + 04-validators.yaml + 05-guidelines.md + 06-tickets.yaml), cierra refined→ready."
when_to_use: "Activa cuando user dice: '/architect', 'diseñemos la arq', 'tickets', 'qué tickets salen', 'arquitectura técnica', 'cómo lo construimos técnicamente', 'cerrá el ready package', 'ready package', 'qué hay que buildear', 'dame los tickets', 'convertí el spec en tickets', story state=refined y el próximo paso es producir 03-arch+04-validators+05-guidelines+06-tickets."
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, Agent
model: opus
---

# /architect — Architect Orchestrator (Conv 1 cierre — produce ready package)

> Owner: `{brand}/docs/product/stories/{story-id}/03-arch.md` + `04-validators.yaml` + `05-guidelines.md` + `06-tickets.yaml`. Cuando los 4 cerrados → state=`refined → ready`. Conv 2 (autonomous build) puede arrancar.

## REQUIRED first input: `<brand>`

`<brand>` ∈ `vitalia | nicolify | comunify | lupulo | platform`. Si Chris no lo provee, **PREGUNTAR antes de proceder**. `platform` = stories cross-brand que tocan engine (raro — requiere `/pm-luana` autorización + outcome platform-level).

Si invocado vía `/pm-{brand}` o vía `/po-ux`/`/po`/`/ux-agentico` handoff, el brand viene en el handoff. Si invocado directo por Chris → preguntar primero.

**Cross-package surface scope (CRÍTICO):**

| Surface | Path canónico | Editable per-story |
|---|---|---|
| Brand backend modules | `{brand}/backend/src/modules/{brand}/{m}/` | ✅ libre per-brand |
| Brand frontend features | `{brand}/frontend/src/features/{m}/` | ✅ libre per-brand |
| Brand tests | `{brand}/backend/tests/` + `{brand}/frontend/src/**/*.test.ts` + `{brand}/frontend/e2e/` | ✅ libre per-brand |
| Engine core packages | `core/luana-core-*/src/luana_core_*/` | ⛔ requiere lift via `/pm-luana` (promotion gate) — NO se edita en story brand-específica |
| Brand-extension agentic | `{brand}/backend/src/modules/{brand}/{copilot,sales_agent}/{tools,extractors,workflows,personas,goldens,kb}/` | ✅ libre per-brand |

## ★ Technical-story lane (WT5) — `/architect` ES el refiner, sombrero CTO-al-CEO (W0.5-bis · ratificado Chris 2026-06-08)

> SSoT: `PROCESS-MODEL.md §3 · WT5` + `REQ-TAKING-DETAIL.md §8 (Technical/infra)`. **Sólo cuando `story_type: technical-story`** (infra / observabilidad / seguridad / performance · `user_visible: false` · zona Infraestructura).

Para technical-story, el `/architect` **no consume** una `01-spec.md` Gherkin de `/po`/`/po-ux`/`/ux-agentico` — **los saltea** y actúa él mismo como **refiner**, porque el spec análogo es un **contract-spec**, no un spec de comportamiento Gherkin.

**El sombrero es CTO recomendando a su CEO:** investigás **SOTA en internet** (date-aware) + proponés **opciones con una recomendación**; **Chris toma las decisiones grandes**. 1 pregunta a la vez, reflejo-primero, sin cave (mismo protocolo que `/po`). Firma = **una sola, sobre el approach propuesto en lenguaje humano** (Chris decide). El **GO en vivo (G)** es aparte.

**Quién abre la story:** brand-infra → `/pm-{brand}` · **core-infra → `/pm-luana`**.

**Contract-spec (el análogo del spec, NO Gherkin)** — 4 piezas:
- **Contrato / interface / extension-point** que se provee (la superficie nueva).
- **Consumers** — quién lo usa (≥1 real, anti-isla CONN).
- **Invariante** que enforcea (lo que NUNCA puede romperse).
- **Verificación-por-efecto** — el efecto runtime observable que prueba que funciona (NO demo, NO "GET 200").

**Verificación = `técnica`** (gates + evidencia runtime por efecto). Bar por sub-dominio: cifrado → round-trip decrypt · idempotencia → replay dedup · observabilidad → fila de traza · durable-flow → persist+resume · audit → fila de audit + access-denied. **Spec-first** (contract-spec RED-first) **excepto `nature: scaffold`** (exento).

**Net-new core infra** = `technical-story` con `cap_change_type: new` apuntando a `core/` (la story ES la justificación del use-case; la regla "no research en core" de promotion aplica sólo a los **lifts** WT6, no a builds nuevos). **Worktree:** core-targeting → worktree core efímero (`wip/core-{slug}`); brand-infra → hub de la marca. **WT5 construye / WT6 liftea** (no confundir: el lift brand→core es off-spine, `/pm-luana`).

**Artefactos:** contract-spec (`new_cap.py` en modo infra) + ready-package **reducido** (`06-tickets` + `04-validators` siempre; `03-arch`/`05`/`dispatch` según haya decisión de arquitectura). **Cockpit:** slot `tech` + zona Infraestructura.

**Tier:** el carril technical-cap + verificación-por-efecto + sombrero CTO = **CORE**; el inventario de infra (durable-flows/LiteLLM/outbox/observability/`core/luana-core-*`) = **PROJECT**; PHI/HIPAA = **BRAND**.

## Inputs obligatorios

1. `<brand>` (REQUIRED, ver sección arriba)
2. `{brand}/docs/product/stories/{story-id}/01-spec.md` — ratificada por Chris (de `/po-ux` para UI std, `/po` para service/agentic)
3. `{brand}/docs/product/stories/{story-id}/02-design-agentic.md` — si agentic-story o mixed
4. `{brand}/docs/product/stories/{story-id}/checkpoint.md` — state=refined requerido (spec + diseño UX/agentic ratificados por Chris)
5. `{brand}/docs/product/modules/{m}.md` — estado funcional per-brand
6. `{brand}/docs/domains/INDEX.md` o `docs/core-modules/README.md` — routing técnico per-brand vs engine
7. `.claude/rules/anti-duplication.md` — inventario shared abstractions cross-brand
8. `.claude/rules/anti-duplication-refining.md` — ★ NEW 2026-05-27 — prior-art-scan cross-brand mandatory en refinamiento
9. `.claude/rules/architect-autonomous-mode.md` — ★ NEW 2026-05-27 — autonomous_mode + agent_assignment + playwright_visual_scope

## ★ Step 0.5 — Prior-art audit (MANDATORY 2026-05-27)

> SSoT: `.claude/rules/anti-duplication-refining.md`.

ANTES de Step 1 (decidir surfaces), revalidar el scan que `/pm-{brand}` + `/po-ux` debieron documentar. Si `01-spec.md` NO tiene sección `## Prior art applied` documentada → REFUSE producir ready package y escalá:

```
ERROR: 01-spec.md sin sección "## Prior art applied" verbatim per
.claude/rules/anti-duplication-refining.md. Vuelve a /po-ux para
documentar el scan antes de architect.
```

Si sección existe, **re-ejecutar el scan** desde architect (verificación):
- Engine packages `core/luana-core-*/` que cubren dominio
- Brands shipped (especialmente nicolify) con módulo paralelo
- Lift candidates → si detectás pattern cross-brand sin lift, escalate `/pm-luana` ANTES de cerrar package
- Stories archivadas done relacionadas (`{brand}/docs/archive/*/stories/` + nicolify equivalent)

Documentá resultado en `03-arch.md § Prior art audit` con:
- Engine packages consumed via import (lista verbatim)
- Reused components/services (paths cross-brand)
- Lift candidates created (paths a proposals si aplica)
- Net-new justificado (con razón)

## Workflow

### Step 1 — Decidir surfaces

Lee `01-spec.md` + `02-design-agentic.md` (si aplica) + checkpoint. Decide cuáles surfaces toca:
- BE: nuevo endpoint? schema change? service nuevo?
- FE: UI nueva? hook nuevo? component nuevo?
- AGENTIC: tool nuevo? prompt slot? eval suite?

Tabla decisión:

| Story type | Surfaces típicas |
|---|---|
| ui-story simple | FE only |
| ui-story con CRUD | FE + BE |
| agentic-story | AGENTIC + (BE si tool nuevo) + (FE si trigger UI) |
| service-story | BE only o AGENTIC + BE |

### Step 2 — Spawn architect-orchestrator (single-shot full-stack)

> **Canonical pattern (formalized 2026-05-08 después del 2do uso exitoso):** spawn UN solo agent `architect-orchestrator` que cubre BE+FE+AGENTIC en una sola pasada. Los **instruction docs por surface** viven en `.claude/skills/architect/references/{be,fe,agentic}.md` (rehomed 2026-06-09 — ex pseudo-skills `architect-{be,fe,agentic}`) y el orchestrator los carga contextualmente según las surfaces que el ticket toca. Esto produce coherent design + cross-cutting decisions consistent — valor demostrado en Story B (eval-foundation-simulator) + Story C (personas-instrumented-runtime) + Story D (goldens-3-tenants-dataset).
>
> **Histórico:** intentos previos de spawnar `architect-be` / `architect-fe` / `architect-agentic` como agent types separados fallaron — esos types nunca se registraron en `.claude/agents/`. Solo existe `architect-orchestrator.md`. Sus instruction docs viven hoy en `architect/references/{be,fe,agentic}.md`.

Spawn (REQUIRED: pasá `<brand>: {brand}` como input al sub-agent):

```
Agent({
  description: "Architect Story {brand}/{id} {scope}",
  subagent_type: "architect-orchestrator",
  prompt: "<brand>: {brand}                          # ★ REQUIRED — multibrand scope
           <pr_folder>: {brand}/docs/product/stories/{id}/
           story_type: {ui-story|service-story|agentic-story}
           surfaces: {BE | FE | AGENTIC | combinaciones}
           mode: SINGLE-SHOT FULL-STACK

           PRIORITY READ:
           1. {brand}/docs/product/stories/{id}/checkpoint.md (state=refined required)
           2. {brand}/docs/product/stories/{id}/01-spec.md ratificada por Chris
           3. {brand}/docs/product/stories/{id}/02-design-agentic.md si agentic-story
           4. {brand}/docs/product/stories/{id}/00-story.md / delta-spec.md si existen
           5. {brand}/docs/product/releases/{release-id}.yaml
           6. {brand}/docs/product/modules/{m}.md
           7. Stories archivadas relacionadas (predecesores) en {brand}/docs/archive/
           8. CAP-AS-LOCATOR (HB-43) — si checkpoint.md tiene cap_target no-null
              (cualquier cap_change_type): corré
              `${WS}/.venv/bin/python ${WS}/scripts/resolve_cap.py {brand} "{cap_target}" --extract`
              → dev_preview.main_component/code_ref/scenarios del código YA existente.
              Diseñá EXTEND sobre eso, no re-descubras por grep. (cap nueva vacía → UNRESOLVED → caés a grep)

           LOAD SKILLS contextualmente según surface:
           - BE: backend-expert + FastAPI canonical patterns + pytest async testing patterns
           - FE: frontend-expert + React patterns baseline + Zod validation + Shadcn UI conventions + Tailwind conventions + Vitest conventions + Next.js App Router Server/Client split
           - AGENTIC: sales-agent-expert / copilot-expert + LangGraph canonical docs + claude-api
           - Cross-cutting: graceful-degradation (timeout + fallback + circuit breaker) + domain skills (brand/offer/preset/metrics)

           DELIVERABLES (4-5 files, todos bajo {brand}/docs/product/stories/{id}/):
           1. 03-arch.md (consolidado, secciones por surface — incluye § Test Construction Plan ★ v4.1)
           2. 03-arch-{be,fe,agentic}.md per surface tocado (opcional, si arch es complejo per-surface)
           3. 04-validators.yaml (5 categories — non_functional / functional / visual / agentic_eval / architectural_validation ★ v4.1 — scenario_coverage 100%, must_pass:true, test_construction_plan completo)
           4. 05-guidelines.md (must_load_skills enforceable ★ v4.1 + patterns required/forbidden + files in scope)
           5. 06-tickets.yaml (work units, R23 marked AGENTIC, owner_eligibility, DAG, gherkin_coverage per ticket)

           CRITICAL CONSTRAINTS:
           - Cross-module audit anti-duplication.md (no mirror shared abstractions cross-brand)
           - R23: AGENTIC tickets production_code:true → flagship_required:true
           - AGENTIC tickets SEPARADOS de BE/FE (R23 enforcement)
           - Tickets > 10 → split story
           - Each ticket: acceptance.validator_ids + DAG + gherkin_coverage (post 2026-05-18)
           - Hot-fix: repro_verified field si aplica (R26)
           - Engine boundaries: NUNCA proponer tickets que editen `core/luana-core-*/src/` directamente. Si scope requiere editar engine → escalá `/pm-luana` (promotion gate) ANTES de cerrar package.
           - Brand-extension agentic: `{brand}/backend/src/modules/{brand}/{copilot,sales_agent}/{tools,extractors,workflows,personas,goldens,kb}/` SÍ es editable.
           - ★ v4.1 Playwright mandatory para surface funcional: test_construction_plan.playwright_required=true SIEMPRE que story sea ui-story o ui-mixed
           - ★ v4.1 must_load_skills enforceable: dev-team builder spawn cita lista verbatim
           - ★ v4.1 architectural_validation category con sub-tests (DDD/FSD boundaries, tenant_isolation grep, anti-dup scan, cross-module audit)
           - ★ v4.1 sub-categorías scenarios obligatorias: race conditions, concurrent users, network failures, empty states, large datasets, accessibility, i18n (heredadas de /po-ux refused refined sin ellas)

           After writing all files, transition checkpoint.md state: refined → ready.

           LAST LINE: done -> {brand}/docs/product/stories/{id}/06-tickets.yaml"
})
```

El orchestrator escribe TODOS los archivos y devuelve `done -> 06-tickets.yaml` (anti-telephone-game).

### Step 3 — Cross-module audit (NO-NEW-LAYER)

Antes de cerrar el package, validar que el orchestrator respetó `.claude/rules/anti-duplication.md` inventario shared. Especial atención si introduce:
- Provider nuevo (LLM, FX, pricing) → debe extender shared, no mirror
- Observability layer → use shared
- Outbox / idempotency / billing guards → shared
- Channel format / intent detector → shared
- Extraction orchestrator → subclass `BaseExtractionOrchestrator`

Si orchestrator propone NEW cuando shared existe ≥80% → escala `/pm-luana` (engine surface) o `/pm-{brand}` (brand-extension surface): "orchestrator propone NEW para subsystem Y, pero shared tiene Z. Decidir EXTEND vs NEW."

**Cross-brand mirror check:** si la abstracción propuesta ya vive en `{other_brand}/...`, escalá `/pm-luana` como promotion candidate (brand→core lift) en lugar de mirror por-brand.

### Step 4 — Validar 03-arch.md producido por orchestrator

Lee el `03-arch.md` que el orchestrator escribió. Verificar:
- Secciones por surface presente (BE / FE / AGENTIC según tickets toca)
- Cross-cutting decisions section (tenant isolation, currency, PII)
- **`## Integration design (CONN)` presente** (`.claude/rules/anti-orphan-integration.md` + `paradigm-arquitectura.md`): reachability path concreto + consumers + registration points + home (cap). Cada surface declara su **hogar zona→caja** del mapa (derivado de `SYSTEM-MAP.yaml`) y, si es agéntico, que el trabajador **invoca la acción única (Plano 2), no la reimplementa** (un solo engine). SIN esto, lo construido será una isla → NO cerrar `ready`. Doctrina: `docs/architecture/luana-platform/PARADIGM.md`.
- **★ Design System Canon (HARD para surfaces FE · cement 2026-06-08):** todo surface `{brand}/frontend/**` referencia los contratos de `docs/architecture/luana-platform/design-system-canon.md` — list/detail = `EntityWorkspaceLayout` (no a mano), franja N3 = tercer-ribbon full-bleed (no card), `Select` canónico (no `<select>` nativo), page-primitives (no `<div>` de layout), `EntityInfoCard` B, autosave 1-píldora, tokens (no arbitrary). `04-validators.yaml` declara los gates mecánicos (eslint no-arbitrary + arch-test no-div-layout) y `05-guidelines.md::must_load_skills` lista `design-system-canon.md` + `frontend-visual-fidelity`. Surface FE que no cita el canon → NO cerrar `ready`. Doctrina: `ADR-014`.
- **★ Storybook = SSoT visual (HARD para FE · cement 2026-06-22 · canon §5):** `03-arch.md § FE` **cita por cada componente la story de Storybook a usar** (`@luana/ui-kit`, id de la story + link `…/iframe.html?id=<story>`) — "lo que ves en Storybook = lo que se programa". Una pieza shared **net-new** (no existe aún en el kit) se marca **`PROMOTE`**: el ticket que la construye tiene como deliverable **crear el componente en `core/@luana/ui-kit` + su story ANTES del merge** (no una re-implementación local que driftea) — esto es parte de `Integration design (CONN)` (Notarized = registrado en Storybook). "No limitarse a Storybook": el architect PUEDE especificar algo mejor/faltante, pero entonces se promueve al kit. Surface FE sin cita de story (o net-new sin plan PROMOTE) → NO cerrar `ready`.
- Per-surface detail puede vivir inline en 03-arch.md O en archivos separados `03-arch-{be,fe,agentic}.md` (orchestrator decide según complejidad)

Template estructura mínima:

```markdown
# 03-arch.md — Story {id}

## Surfaces involved
- BE: yes (3 endpoints, 2 SQLA models, 1 migration)
- FE: yes (1 page route, 2 components, 1 RHF form)
- AGENTIC: no

## BE arch (full detail in 03-arch-be.md)
... summary + key decisions ...

## FE arch (full detail in 03-arch-fe.md)
... summary + key decisions ...

## Cross-cutting decisions
- Tenant isolation strategy: ...
- Currency handling: ...
- PII fields: ...

## Integration design (CONN)   ← OBLIGATORIO (anti-orphan-integration.md)
### Reachability path: usuario/sistema → ... → feature (camino concreto)
### Consumers: quién llama cada surface nuevo (UI hook / agente / servicio). Cero consumers → NO construir.
### Registration points: include_router / nav tree / DI / tool registry (deliverables verificables)
### Home: cap_target + cap_change_type (dev_preview se actualiza al merge)
### Read-side verificado: por cada claim "el engine/supervisor YA honra/inyecta/lee [X]" → citá el read-site EXACTO (archivo:función que LEE la key/campo), grep-verificado. Sin read-site citado = contrato IMAGINADO.
```

★ **Read-side gate (HB-92 · 5ª recurrencia familia HB-44/74/82 — imagined contract):** el architect NUNCA afirma "el engine ya honra/inyecta/lee [X]" sin **abrir el código del read-side y citarlo** (`archivo:función` que efectivamente LEE la key/campo, verificado por grep). El patrón que se repite: un ticket write-side persiste a una key (`metadata_info["operator_instructions"]`, `checkpoint.X`, un campo nuevo) y el spec/arch asume que el engine ya la consume — pero el engine lee OTRA key (o no lee nada) → la instrucción nunca llega al runtime y los gates de build pasan verdes (cada lado correcto en aislamiento). **Regla:** todo claim de comportamiento de engine ya-existente se ancla a su read-site citado; si el read-site no existe o lee otra cosa, la integración (bridge/wiring) es un **deliverable del ready package**, no un supuesto. Esto es la cara read-side de la **C**(onsumed) de CONN.

## Verificación: clasificar por naturaleza + declarar gates (Critical Rule #37)

Al producir `04-validators.yaml`, el architect DECLARA por capability/ticket (sección `verification:`):
- `nature`: **technical** (sin UI) · **functional** (user-reachable) · **both**.
- `technical_gates.baseline` siempre (tsc/mypy strict · ruff/eslint --max-warnings 0 · arch-fitness) + `opt_in` **por naturaleza** (NO en toda story): Schemathesis (endpoint nuevo), Hypothesis (domain logic con invariantes).
- ★ **`technical_gates.mutation`** (proceso v5 §5.6 · HB-54): el architect MARCA las superficies **mutation-críticas** por `verification_nature` — commit/persistencia (HB-50), dinero/pricing, gates PHI, state-machines, transforms-contrato (HB-42/44) → `mutation: {enabled: true, mode: hard, surfaces: [...]}`; el resto `advisory` (anti-costo). Corre `scripts/mutation_gate.py` diff-scoped (mutmut/Stryker); degrada advisory si el tool no está instalado.
- `business_rules` matriz `regla → @rule-tag → scenario_id` (cada regla con ≥1 happy + ≥1 negative/edge — Example Mapping) para stories funcionales.
- `runtime_error_gate: required` para toda superficie FE (builder usa `base.ts` + `verify-no-backend-errors.sh`).
- `demo_required` (árbol: toca frontend/ o endpoint con consumer FE → true; solo tests/migrations/config/core sin cambio de contrato → false + `demo_skip_reason`).
- `regression_guard` (modificación: tests existentes que NO deben cambiar) + `coverage_update` + `new_coverage`.

Ref: `.claude/rules/definition-of-done-live-verify.md` §1-§6.

### Step 5 — Producir 04-validators.yaml + Test Construction Plan ★ CRITICAL ★

Este es el **corazón del autonomous build**. Sonnet en Conv 2 itera contra estos hasta GREEN.

**v4.1 cement 2026-05-19:** además de los validators ejecutables, architect MUST producir un `test_construction_plan` explícito que indique al dev-team **CÓMO** construir las pruebas Playwright (no solo qué comandos correr). Esto es responsabilidad arquitectónica — dev-team no debe inventar el orden ni estructura.

Reglas:
- Cada validator es un comando shell ejecutable (pytest / playwright / lint / etc.)
- `must_pass: true` por default — sin ambigüedad
- Cobertura completa de scenarios del 01-spec.md (mapping explícito)
- Iteration policy define cap + on_fail behavior
- **Nueva categoría `architectural_validation`** separada de `non_functional` (DDD boundary scan, anti-dup grep, tenant_isolation grep, cross-module audit)
- **TODA story con surface FE/funcional MUST incluir Playwright behavior tests** — el architect dicta los scenarios E2E exactos a cubrir (no es opcional)
- **`test_construction_plan` section** dentro de `04-validators.yaml` con: orden de creación, POMs requeridos, fixtures compartidos, mapping scenario Gherkin → spec.ts file → assertions
- **★ Seam coverage (HB-95 · cement 2026-06-23):** cada escenario que cruza una COSTURA (código↔DB · FE↔BE · service↔router/response · código↔auth · componente↔shell) declara en `test_construction_plan.seam_coverage` la `seam` + el `test_type` real-collaborator requerido (`integration-realdb` / `contract` / `router` / `e2e-live` / `live-verify`) + el `target`. **PROHIBIDO `unit-mocked` para un escenario de costura** — un test que mockea el colaborador del otro lado de la costura NO la cubre (`test-design-doctrine.md § Cobertura = colaborador real, no mock`). Mapeo: code-db→integration-realdb · fe-be→contract · router→router(end-to-end) · auth→live-verify(#37, NO unit-testeable) · component-shell→e2e-live(render real). Gate: `scripts/check_seam_coverage.py --report 04-validators.yaml`.

Template (paths brand-scoped; workspace root parametrizado via `${WS}` o `cd {brand}/...`):

```yaml
# Esqueleto (forma) — el TEMPLATE COMPLETO (SSoT) vive en docs/specs/templates/04-validators-template.yaml.
# Leelo + expandilo. NO copiar verbatim acá (DRY · single-source-of-truth · HB-24).
story_id: STORY_ID
brand: BRAND_SLUG            # vitalia | nicolify | comunify | lupulo
schema_version: v4.1
verification:                # Critical Rule #37 — nature + technical_gates.mutation + dev_app_verified + playwright_visual_scope + business_rules
validators:                  # 5 categorías: non_functional / functional / visual / agentic_eval / architectural_validation (cada uno must_pass:true + cmd shell)
scenario_coverage:           # cada scenario del 01-spec.md → N validators
test_construction_plan:      # creation_order + scenario_to_test + seam_coverage (HB-95) + poms_required + fixtures_required
iteration:                   # max_iterations + on_fail + on_all_pass + on_cap_reached
```

Template completo (SSoT) en `docs/specs/templates/04-validators-template.yaml` — leelo + expandí cada key. Incluye los enums de `seam_coverage` (code-db/fe-be/router/auth/component-shell → integration-realdb/contract/router/e2e-live/live-verify) + el bloque `verification.technical_gates.mutation` (enabled/mode/surfaces · proceso v5 §5.6).

**Validation gate v4.1:** Every scenario in `01-spec.md` MUST appear en `scenario_coverage` AND `test_construction_plan.scenario_to_test`. If any uncovered → architect itera hasta cubrirlos. **Sub-categorías scenarios obligatorias (v4.1 /po-ux refused refined sin ellas):** race conditions, concurrent users, network failures, empty states, large datasets, accessibility, i18n. Si /po-ux ratificó refined SIN estas sub-categorías → flag para Chris (spec quality gap).

**★ Seam validation gate (HB-95):** todo escenario que cruza una costura DEBE tener su entry en `test_construction_plan.seam_coverage` con `test_type` ≠ `unit-mocked`. Corré `scripts/check_seam_coverage.py --report {story}/04-validators.yaml` antes de cerrar `ready` — `::error::` → el ready package NO cierra. (El escenario `código↔auth` se declara `test_type: live-verify` — su cobertura es la live-verify #37, no un test.)

### Step 6 — Producir 05-guidelines.md ★ v4.1 must_load_skills enforceable ★

Patterns concretos que Sonnet debe seguir/evitar. SIN AMBIGÜEDAD.

**v4.1 cement 2026-05-19:** la sección "Reference docs (load before coding)" pasa a llamarse `must_load_skills` y deja de ser sugerencia — el `dev-team` Step 2 cita esta lista verbatim al builder spawn, y el builder MUST entregar en `T-{n}-result.md` una sección "Skills consulted" listando cuáles cargó. Si no las cargó → CHANGES_REQUESTED auditor automático.

Template:

```markdown
# Esqueleto (forma) — el TEMPLATE COMPLETO (SSoT) vive en docs/specs/templates/05-guidelines-template.md.
# Leelo + expandilo. NO copiar verbatim acá (DRY · HB-24).
---
story_id / brand / arch_version            # frontmatter
---
## must_load_skills (★ v4.1 enforceable — builder reporta "Skills consulted" en T-{n}-result.md)
## reference_artifacts                      # 01-spec / 03-arch / 04-validators / 06-tickets
## Patterns required                        # ### Backend · ### Frontend · ### Agentic
## Patterns forbidden
## Files in scope                           # Sonnet edita SOLO estos, brand-scoped
## Files Builder NEVER touches              # engine / copilot+sales_agent runtime / other_brand / config flags / ui primitives / .claude
```

Template completo (SSoT) en `docs/specs/templates/05-guidelines-template.md` — leelo + expandí. Trae `must_load_skills` con `chrome-devtools-verify` (DoD #37) + `git-safety.md`, los patterns split por surface (BE/FE/AGENTIC), y la lista NEVER-touches completa.

### Step 7 — Producir 06-tickets.yaml

Seguir template `docs/specs/templates/06-tickets-template.yaml` (post-redesign — antes era `04-tickets.yaml` paradigma viejo). Reglas:

**Reglas de ticket split (CRÍTICAS):**

1. **Agentic tickets SIEMPRE separados** de BE/FE en tickets distintos
   - Razón: opencode/Sonnet ban en agentic production code. Mezclar = no asignable.
2. **BE tickets pueden combinar** dentro mismo módulo (endpoint + service + migration en 1 ticket)
3. **FE tickets pueden combinar** dentro mismo feature (component + hook + e2e en 1 ticket)
4. **Migration aislada** si afecta tabla compartida o downtime risk
5. **Cada ticket = entrega funcional total** (no "T-1 BE half" + "T-2 BE other half" sin razón)
6. **Si tickets > 10** → story es demasiado grande, split en N stories

**Owner eligibility (CRÍTICO):**

| Surface | production_code | qwen-opencode | workhorse | flagship |
|---|---|---|---|---|
| BE/FE no-agentic | true | ✅ default | ✅ | ✅ |
| BE/FE no-agentic | false (tests/docs) | ✅ default | ✅ | ✅ |
| AGENTIC | true | ⛔ PROHIBIDO | ⛔ PROHIBIDO | ✅ OBLIGATORIO |
| AGENTIC | false (tests/docs only) | ⛔ | ✅ R23 | ✅ |
| Migration aislada | true | ✅ | ✅ | ✅ |
| Cross-module shared | true | ⛔ | ✅ | ✅ |

**`production_code` flag (R23 mandatory per ticket):**
- `true` si modifica `backend/src/`, `frontend/src/`, `migrations/versions/`, `prompts/`, `tools/`, agent runtime
- `false` si modifica `tests/`, `docs/`, `scripts/` tooling, configs no-runtime

**Dependencies / blocks:**

```yaml
- id: T-1 (BE endpoint)
  depends_on: []
  blocks: [T-2, T-3]
- id: T-2 (agentic tool wire)
  depends_on: [T-1]
  blocks: [T-3]
- id: T-3 (FE button)
  depends_on: [T-2]
  blocks: []
```

**Acceptance criteria por ticket** — los validators de `04-validators.yaml` que cubren el ticket:

```yaml
acceptance:
  - validator_ids: [be_unit_create_endpoint, be_arch_fitness, be_lint]
```

**Cross-stack handoff notes** (anti retrabajo):

Cuando ticket agentic depende de BE/FE → `/architect` agrega NOTAS DETALLADAS al ticket BE/FE:

```yaml
T-1 (BE endpoint, owner: opencode/sonnet):
  ...
  notes_for_downstream_agentic_ticket:
    - "Este endpoint será llamado por brand_audit_tool en T-2 (agentic). NO cambiar response shape sin coordinar."
    - "Response model: BrandAuditResponse(gaps: list[Gap], priorities: dict)"
    - "Latencia p95 < 500ms (agentic budget total $0.50)"
```

**Hot-fix repro evidence (R26):** Si story es hot-fix, cada ticket DEBE incluir:
```yaml
repro_verified: true
repro_evidence:
  command: "cd {brand}/backend && ../../.venv/bin/pytest <paths brand-scoped> -v"
  output: |
    <verbatim error/traceback first 5-10 lines>
  diagnosis_validates_handoff: <true|false>
```

### Step 7.5 — Producir dispatch-plan.md + assignment block per ticket (★ NEW 2026-05-27)

> SSoT: `.claude/rules/architect-autonomous-mode.md`.

Cada ticket en `06-tickets.yaml` MUST incluir bloque `assignment` con:
- `primary_agent`: sub-agent type EXACTO (NO `general-purpose`). Opciones: `builder-backend`, `builder-frontend`, `builder-agentic`. Otros (general-purpose) sólo si no aplica ninguno (raro).
- `model_preference`: workhorse | flagship | opencode — TIERS, resueltos de `project.config.yaml::models` (agentic prod → `flagship` HARD R23)
- `must_load_skills`: lista verbatim (heredada de `05-guidelines.md § must_load_skills`)
- `forbidden_to_touch`: paths explícitos que el builder NO puede tocar
- `rationale`: 1-2 líneas por qué este agent + modelo

Ejemplo:
```yaml
- id: T-1
  title: "BE endpoint create-appointment"
  surface: BE
  production_code: true
  owner_eligibility: [opencode, workhorse, flagship]
  assignment:
    primary_agent: builder-backend
    model_preference: workhorse
    must_load_skills: [backend-expert, "FastAPI canonical patterns", .claude/rules/tenant-isolation.md, .claude/rules/backend-ddd.md]
    forbidden_to_touch: ["core/luana-core-*/src/", "{other_brand}/", "{brand}/backend/src/modules/{brand}/{copilot,sales_agent}/"]
    rationale: "BE CRUD non-agentic, Sonnet sweet spot"

- id: T-2
  title: "AGENTIC tool wire"
  surface: AGENTIC
  production_code: true
  owner_eligibility: [flagship]  # HARD R23
  assignment:
    primary_agent: builder-agentic
    model_preference: flagship  # HARD per R23
    must_load_skills: [sales-agent-expert, "LangGraph canonical docs", claude-api]
    forbidden_to_touch: ["core/luana-core-{copilot,sales-agent}/src/"]
    rationale: "AGENTIC production R23 → tier flagship obligatorio"
```

Adicionalmente, en `04-validators.yaml § test_construction_plan` MUST incluir `playwright_visual_scope`:

```yaml
playwright_visual_scope:
  story_scope_routes: ["/agenda/nueva", "/agenda/[id]/edit"]
  story_scope_components:
    - "{brand}/frontend/src/features/scheduling/components/AppointmentForm.tsx"
  forbidden_visual_changes:
    paths:
      - "{brand}/frontend/src/components/ui/"        # Shadcn primitives
      - "{brand}/frontend/src/components/shared/"    # cross-feature shared
      - "{brand}/frontend/src/app/layout.tsx"        # app shell
    reasons:
      - "Cambios visuales en primitives Shadcn impactan TODA la app"
  if_visual_change_needed_outside_scope:
    action: "STOP. Document en T-{n}-impl-log.md. Escalate /pm-{brand} para spec extension."
  non_egoismo_clause: "Bug visible fuera scope = reportar en T-{n}-impl-log § Cross-story observed bugs + opcionalmente abrir hotfix-story-id separada. NO arreglar inline (rompe scope discipline)."
```

Producir `dispatch-plan.md` (≤100 líneas, 1 sólo file por story) en `{brand}/docs/product/stories/{story-id}/dispatch-plan.md`:

```markdown
# Dispatch plan — Story {brand}/{id}

## autonomous_mode
- value: false                # default. Chris opt-in al ratificar
- chain_if_true: [/dev-team → /auditor → /pm-{brand} merge]
- caps: {iterations: 10, audit_iter: 3, cost_usd: 5.00, walltime: 90min}

## Ticket→Agent→Model→Cost matrix
| T-id | Title | Surface | Agent | Model | Est. cost | Est. time |
|---|---|---|---|---|---|---|
| T-1 | ... | BE | builder-backend | workhorse | $0.30 | 25min |
| T-2 | ... | AGENTIC | builder-agentic | flagship (R23) | $1.20 | 35min |
| T-3 | ... | FE | builder-frontend | workhorse | $0.40 | 30min |
| Total | — | — | — | — | $1.90 | ~90min |

## DAG dependencies
T-1 → T-2 → T-3 (sequential)

## Playwright visual scope
- story_scope_routes: [/agenda/nueva, /agenda/[id]/edit]
- forbidden: components/ui/, components/shared/, app/layout.tsx
- non_egoismo: report cross-story bugs en T-n-impl-log

## Invocation manual
/dev-team <brand>: {brand}, ticket: T-1

## Invocation autonomous
echo 'autonomous_mode: true' >> {brand}/docs/product/stories/{id}/checkpoint.md
# /dev-team picks up T-1, auto-handoff T-2 → T-3 → /auditor → /pm-{brand} merge
```

Al cerrar Step 7.5, el ready package incluye **5 artifacts** (era 4):

1. `03-arch.md` consolidado
2. `04-validators.yaml` con `playwright_visual_scope`
3. `05-guidelines.md`
4. `06-tickets.yaml` con `assignment` block per ticket
5. **`dispatch-plan.md`** (★ NEW 2026-05-27)

### Step 8 — Validate ready package (★ v4.1 expanded checklist)

Antes de cerrar story como ready:

**Estructura básica:**
- [ ] `03-arch.md` consolidado escrito (con secciones inline por surface, O archivos separados `03-arch-{be,fe,agentic}.md` si orchestrator decidió split por complejidad)
- [ ] `04-validators.yaml` cubre TODOS scenarios del `01-spec.md` (gate hard)
- [ ] `04-validators.yaml` cada validator tiene cmd ejecutable native Linux (host) (no Docker para tests)
- [ ] `05-guidelines.md` lista patterns required + forbidden + files in scope
- [ ] `06-tickets.yaml` cada ticket: `production_code` flag set, `owner_eligibility` coherente, `acceptance.validator_ids` mapea a 04-validators.yaml ids
- [ ] Dependencies son DAG (no ciclos)
- [ ] AGENTIC tickets con `production_code: true` → flagship_required: true (HARD)
- [ ] Estimate hours razonables (alerta si > 8h por ticket → split)
- [ ] Tickets > 10 total → STOP, split story

**★ v4.1 cement 2026-05-19 expanded gates:**
- [ ] `04-validators.yaml § architectural_validation` category presente con ≥3 sub-tests (DDD/FSD + tenant_isolation grep + anti-dup scan)
- [ ] `04-validators.yaml § test_construction_plan` completo con: `playwright_required` flag, `creation_order` (steps numerados), `scenario_to_test` mapping (cada Gherkin scenario → spec.ts + function + assertions), `poms_required`, `fixtures_required`
- [ ] Para stories ui-story o ui-mixed: `test_construction_plan.playwright_required: true` (HARD — no opt-out)
- [ ] `scenario_coverage` cubre sub-categorías mandatory: race / concurrent / network_failure / empty_state / large_dataset / a11y / i18n (heredadas de /po-ux refined gate)
- [ ] `05-guidelines.md § must_load_skills` enforceable (sección renombrada de "Reference docs", builder spawn cita verbatim)
- [ ] `06-tickets.yaml` cada ticket tiene `gherkin_coverage` field (post 2026-05-18 mandatory)

**★ v4.2 cement 2026-05-27 expanded gates:**
- [ ] `03-arch.md § Prior art audit` sección presente con paths verbatim del scan cross-brand (consumed engine + reused brands + lift candidates + net-new justificado)
- [ ] `06-tickets.yaml` cada ticket tiene `assignment` block: `primary_agent` (no general-purpose), `model_preference`, `must_load_skills`, `forbidden_to_touch`, `rationale`
- [ ] AGENTIC tickets con `production_code: true` → `assignment.model_preference: flagship` (HARD R23)
- [ ] `04-validators.yaml § playwright_visual_scope` presente para UI stories con `story_scope_routes` + `forbidden_visual_changes` + `non_egoismo_clause`
- [ ] `dispatch-plan.md` producido (5th artifact) con `autonomous_mode: false` default + caps + cost matrix
- [ ] `checkpoint.md::autonomous_mode` campo presente (default false; Chris ratifica true al cerrar review ready)

**★ v4.3 cement 2026-05-28 (anti-isla + fidelidad visual):**
- [ ] `03-arch.md § Integration design (CONN)` presente: reachability path concreto + consumers (≥1 por surface, o justificación infra) + registration points (router/nav/DI/tool registry como deliverables) + home (cap_target). Sin esto → NO ready (`anti-orphan-integration.md`)
- [ ] **Read-side gate (HB-92):** cada claim "el engine/supervisor YA honra/inyecta/lee [X]" cita su read-site EXACTO (`archivo:función` que LEE la key/campo, grep-verificado). Sin read-site → contrato imaginado → la integración (bridge/wiring) es deliverable, no supuesto. Sin esto → NO ready
- [ ] Cada surface nuevo en 06-tickets tiene su deliverable de **registro** (no solo crear el archivo): BE `include_router`, FE ruta+nav, agentic tool registry
- [ ] **★ HB-71 (contrato-imaginado · REFUSE ready):** toda superficie **editable con autosave / write** declarada en `03-arch.md` (StructuredProfileEditor, form-autosave, mutation hook) DEBE tener su **write endpoint (method + path exacto)** en la TABLA DE ENDPOINTS del mismo arch. Editor declarado sin su write endpoint en la tabla → el builder FE lo INVENTA (404 live · 10 instancias en una story). Sin el endpoint declarado → NO ready. El builder FE además cementa el contrato con un test que assertea method+URL contra el router BE real (no contra sí mismo) — ver `test_http_contract_parity.py`
- [ ] UI stories: `02-design-ui.md` lista elementos visuales clave + `04-validators § playwright_visual_scope` separa `story_scope_*` de `out_of_mockup_scope` (no exceder mockup). `frontend-visual-fidelity.md`
- [ ] UI tickets: deliverables citan reutilización de átomos `components/ui/` + moléculas `components/shared/` (no reinventar primitivas)

**Validation coherencia cap_change_type (v2 cement 2026-05-27):** antes de cerrar state=ready, verificar coherencia entre `cap_change_type` declarado y archivos producidos:
- Si `extend`: 03-arch.md DEBE citar cap existente en sección "## Prior art audit" + 06-tickets.yaml no toca files de caps cross-target
- Si `derive`: 03-arch.md DEBE crear/referenciar cap nuevo con `parent_cap: {origen}` explícito + checkpoint.md tiene `parent_story` declarado
- Si `new` (o `derive`): **NO hand-authorear el YAML** — corré `make new-cap BRAND=<b> MODULE=<m> SLUG=<s> AREA=<area>` (genera el cap `planned` schema-v2 válido · HB-51) ANTES de cerrar `ready` + stagealo. Sin el cap YAML en HEAD/staged el gate HARD 5b BLOQUEA el commit del ready package (HB-77 caso origen: el orchestrator cerró `new` sin crear el cap → 5b frenó + tentó al commit-worker a flipear el campo, HB-76). El resolver `cap_target`→path valida que exista.
- Si `fix`: 03-arch.md NO crea cap nuevo · solo modifica comportamiento existente

Incoherencia detectada → emit verdict `⚠️ DUDA` pidiendo Chris ratificar o corregir `cap_change_type`. Doc: `docs/process/capability-protocol.md` § Sección 3.

### Step 9 — Transition state + Hand off

Update `{brand}/docs/product/stories/{story-id}/checkpoint.md`:

```yaml
brand: {brand}        # ★ REQUIRED — multibrand scope
state: ready          # ★ TRANSITION ★ refined → ready
phase: READY_PACKAGE_CLOSED
last_artifact: 06-tickets.yaml
last_modified: 2026-05-06T...
next_action: "/dev-team <brand>: {brand} starts Conv 2 autonomous build (toma T-1 first, iterate vs 04-validators.yaml)"
```

Output:

```
Ready package cerrado para story {brand}/{id}.

Artifacts (en {brand}/docs/product/stories/{id}/):
- 03-arch.md (consolidado, secciones por surface inline)
- 03-arch-{be,fe,agentic}.md OPCIONAL (orchestrator decide si arch es complejo per-surface)
- 04-validators.yaml ({N} validators, scenario coverage 4/4)
- 05-guidelines.md
- 06-tickets.yaml ({N} tickets)

Owner mix:
- T-1 (BE, qwen/workhorse, 2h)
- T-2 (AGENTIC, flagship-only, 3h)
- T-3 (FE, qwen/workhorse, 2h)

Dependencies: T-2 depends T-1; T-3 depends T-2.

Story state: refined → ready.
WIP cap check: ready (was N) now N+1 / cap 5.

Próximo: Conv 2 (autonomous build). /dev-team <brand>: {brand} toma T-1 (state: ready → developing).
```

## Anti-patterns

- ❌ Mezclar agentic + BE en MISMO ticket (opencode/qwen ban en agentic production code)
- ❌ Producir tickets sin `acceptance.validator_ids` mapeado a 04-validators.yaml
- ❌ `04-validators.yaml` con scenarios uncovered (gate hard — todos scenarios deben tener validator)
- ❌ Skip cross-module audit (anti-duplication) → mirror code
- ❌ Tickets sin DAG (cycle dependencies)
- ❌ Tickets >8h sin split
- ❌ Tickets cross-stack sin `notes_for_downstream`
- ❌ **Intentar spawnar `architect-be` / `architect-fe` / `architect-agentic` como agent types** — NO existen en `.claude/agents/`. Solo `architect-orchestrator` existe. Los instruction docs por surface viven en `.claude/skills/architect/references/{be,fe,agentic}.md` (cargados contextualmente por orchestrator), no son agent types spawnables ni skills.
- ❌ Aprobar tu propio ready package sin verificar 03-arch.md coherencia cross-surface
- ❌ Asignar el tier flagship a tickets BE/FE non-agentic (cost waste — esos van al workhorse)
- ❌ Editar paths legacy `docs/archive/2026/legacy-pis/PI-N/...` o `docs/archive/2026/snapshot-pre-multibrand-pm-redesign/` (snapshot inmutable)
- ❌ Cerrar state=ready con WIP cap=5 ya alcanzado (escalate Chris primero)
- ❌ `05-guidelines.md` con "be careful" / "follow best practices" (vago — usa patterns concretos)
- ❌ Inferir el brand del contexto si Chris no lo dijo — PREGUNTAR primero

## Anti cross-brand pollution

- ❌ NUNCA generar tickets que editen `{other_brand}/...` cuando trabajás en `{brand}`. Si la story necesita tocar otra brand → STOP, escalate `/pm-luana` (trabajo cross-brand).
- ❌ NUNCA generar tickets que editen `core/luana-core-*/src/` directamente. Requiere lift via `/pm-luana` (promotion gate) — propuesta en `docs/promotion-protocol/proposals/` ANTES de cerrar package.
- ❌ NUNCA escribir specs/archs/tickets en root `docs/product/stories/` — solo `<brand>: platform` (cross-brand) outcomes van ahí, y eso requiere autorización explícita `/pm-luana`.
- ❌ NUNCA referenciar `backend/src/` o `frontend/src/` sin el prefix `{brand}/` — post reorg 2026-05-15 no existe root `backend/` ni `frontend/`. Solo `core/luana-core-*/src/luana_core_*/` (engine) y `{brand}/backend/src/` (brand).
- ❌ NUNCA hardcodear paths absolutos `/home/chris/AISALESHT/...` o `/home/chalreme/Proyectos/luana-platform/...` — usar `${WS}` resuelto via `git rev-parse --show-toplevel`.

## Output format

Resumen de tickets en lista. Dependencias en flecha. NUNCA reproducir 06-tickets.yaml entero en chat (cita path).

## Output protocol · chris-input.md append

Al cierre de cada turn, MUST appendear una entry a la sección 💬 Conversación del `chris-input.md` de la story activa, con verdict **✓ APLICADO · ⚠️ DUDA · ❌ REFUTADO · 💡 PROPONE**. Nunca terminar turn sin appendear (aunque sea `✓ APLICADO · sin cambios sustantivos`). Path: state ∈ {idea..reviewing} → `{brand}/docs/product/stories/{id}/chris-input.md`; `done` → `{brand}/docs/archive/{year}/stories/{id}/chris-input.md`.

**Schema verbatim (formato del entry + labels + anti-patterns): `docs/process/chris-input-protocol.md § Sección 5` (SSoT — no se duplica acá).**

## Referencias

- `docs/process/capability-protocol.md` — schema cap YAML v2 + cap_change_type coherence gates
- `docs/architecture/luana-platform/PARADIGM.md` + `.claude/rules/paradigm-arquitectura.md` — ★ 3 planos · Integration design declara hogar zona→caja + acción única (no reimplementar)
- `docs/process/chris-input-protocol.md` — output protocol per skill

- `docs/process/pm-redesign-2026-05.md` — paradigma 3 conversaciones + ready package + § v4.1 autonomy amplification 2026-05-19
- `docs/architecture/luana-platform/ADR-007-paradigm-v4.1-autonomy.md` — decisión cementada (test_construction_plan + must_load + Playwright mandatory funcional)
- `docs/specs/templates/03-arch-template.md` — template arch (incluye Test Construction Plan ★ v4.1)
- `docs/specs/templates/04-validators-template.yaml` — template validators (5 categorías incluyendo architectural_validation ★ v4.1)
- `docs/specs/templates/05-guidelines-template.md` — template guidelines (must_load_skills enforceable ★ v4.1)
- `docs/specs/templates/06-tickets-template.yaml` — template tickets (gherkin_coverage mandatory)
- `.claude/rules/auditor-self-fix-policy.md` — auditor decision tree v4.1 (whitelist 17 + spawn dev-team autónomo)
- `.claude/rules/anti-duplication.md` — inventario shared abstractions
- `.claude/rules/anti-default-flip-audit.md` — R31 default flag flips
- `.claude/rules/auditor-downstream-regression.md` — surface→downstream test mapping

## Live verification contra dev-app (Critical Rule #37)

**Uso (previo al diseño, opcional):** si necesitás confirmar comportamiento actual antes de diseñar, inspeccioná en vivo contra dev-app en vez de asumir.

Levantar: `make dev-app-vitalia` → `https://dev-app.vitalialat.com` (login `dr.demo@vitalialat.com`, creds en `vitalia/.env.dev`). Herramientas: **Chrome DevTools MCP** (live) + **Playwright autenticado** (golden). Evidencia = acción real ejercida + efecto observado; NUNCA GET 200 ni e2e mockeado. SSoT: `.claude/rules/definition-of-done-live-verify.md`.

### Live-verify gate — instrucción DURA al dev-team (Critical Rule #37)

**ESTO NO ES OPCIONAL** para stories con `verification_nature ∈ {funcional, ambas}` o `demo_required: true`. El architect MUST declarar y el dev-team MUST cumplir antes de cerrar `developing → developed`.

**Obligaciones del architect al producir el ready package:**

1. **En `06-tickets.yaml`** — todo ticket FE o endpoint-con-consumer-FE lleva en `assignment.must_load_skills`:
   - `chrome-devtools-verify` (verificación live conversacional SIEMPRE)
   - `playwright-expert` si hay golden visual o flujo crítico persistido
   El exit-criterion del ticket DEBE decir: **"live-verify en dev-app + `dod_evidence` (≥1 write real + leer logs BE + confirmar efecto en DB) + `demo-script.md`"** — NUNCA "tests verdes" ni "GET 200".

2. **En `04-validators.yaml`** — declarar explícitamente:
   - `playwright_visual_scope` (sub-keys: `story_scope_routes`, `story_scope_components`, `forbidden_visual_changes`, `non_egoismo_clause`) — delimita qué rutas/componentes puede tocar el builder; fuera de scope → STOP y escalar.
   - `dev_app_verified: { required: true, evidence: "" }` — el campo no puede quedar vacío de intención; dev-team lo completa con evidencia real al cerrar el ticket.

3. **Sin estas declaraciones**, el auditor auto-FAILea (`LIVE_VERIFY_MISSING`) y devuelve `CHANGES_REQUESTED` — no hay apelación para stories funcionales.

**Árbol rápido (para saber cuándo aplica):**
```
¿La story toca frontend/ O endpoint que la UI llama?
  SÍ → verification_nature: functional | both
       demo_required: true
       chrome-devtools-verify en must_load_skills
       playwright_visual_scope en 04-validators.yaml
       dev_app_verified.required: true
  NO (solo tests/migrations/config/core sin contrato UI) →
       verification_nature: technical
       demo_required: false + demo_skip_reason
       live_verify: skippable con dod_live_verified_skip_reason
```

Ref completa: `.claude/rules/definition-of-done-live-verify.md` §1-§6 + ADR-vitalia-008.
