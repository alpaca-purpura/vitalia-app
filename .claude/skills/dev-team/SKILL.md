---
name: dev-team
description: "Developer team router v4 (Conv 2 autonomous build) — lee ready package, itera ticket-por-ticket implement→validators→fix hasta GREEN, decide owner (R23, tier flagship obligatorio para agentic prod), TDD, mantiene impl-log, ready→developing→developed + auto-handoff /auditor."
when_to_use: "Activa cuando user dice: '/dev-team', 'toma ticket T-N', 'implementa T-N', 'arranca build', 'autonomous build'."
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, Agent
model: opus
---
<!-- voseo-allowed: doc interno / buzón conversacional, no user-facing -->

# /dev-team — Developer Team Router (Conv 2 autonomous build)

> Owner: `T-{n}-impl-log.md` + `T-{n}-result.md` en `{brand}/docs/product/stories/{story-id}/`. Toma 1 ticket → ejecuta TDD + iteración contra `04-validators.yaml` → push. On pickup: state=ready→developing. On GREEN all tickets → state=developing→developed. **★ proceso v5:** default = **PAUSA en G (Chris-verify)** `phase: AWAIT_CHRIS_VERIFY` (NO auto-handoff); `autonomous_mode: true` → corre a `/auditor` sin pausa (story-closure-gate Fase G). Escape valve: `checkpoint.md::defer_audit: true` (razón + Chris). **REFUSE pickup si otra story DEL MISMO MÓDULO está en state ∈ {developing, developed, reviewing} sin `defer_audit: true` NI `phase: AWAIT_CHRIS_VERIFY`** (story en G no bloquea — exención WIP-cap; defense-in-depth Layer 2, ★ v2 module-scoped post ADR-009: stories de OTROS módulos developing en paralelo = OK).

## REQUIRED first input: `<brand>`

`<brand>` ∈ `vitalia | platform`. Si Chris no lo provee, **PREGUNTAR antes de proceder**. `platform` = stories que tocan engine (raro — requiere ratificación Chris vía `/pm-vitalia`).

Si invocado vía `/pm-vitalia` o `/architect` handoff, el brand viene en el handoff. Si invocado directo por Chris → preguntar primero.

## Inputs obligatorios (ready package)

1. `<brand>` (REQUIRED, ver sección arriba)
2. `{brand}/docs/product/stories/{story-id}/06-tickets.yaml` — pila tickets del story
3. `{brand}/docs/product/stories/{story-id}/04-validators.yaml` — ★ comandos shell ejecutables, must_pass:true ★
4. `{brand}/docs/product/stories/{story-id}/05-guidelines.md` — patterns required/forbidden + files in scope
5. `{brand}/docs/product/stories/{story-id}/03-arch.md` (+ `03-arch-{be,fe,agentic}.md`)
6. `{brand}/docs/product/stories/{story-id}/01-spec.md` (+ `02-design-agentic.md` si aplica)
7. Ticket específico que tomas (`T-{n}` con `state: ready`)
8. `{brand}/docs/product/stories/{story-id}/checkpoint.md` — state=ready requerido

## ★ Design System Canon — HARD GATE para todo ticket FE (cement 2026-06-08, ratificado Chris)

> **SSoT:** `docs/architecture/luana-platform/design-system-canon.md` (contratos + **ejemplos de código** que copiás como base). Doctrina: `ADR-014`. Auto-reforzado por `.claude/rules/frontend-visual-fidelity.md § Design System Canon` (que `builder-frontend` carga).

Todo ticket que toca `{brand}/frontend/src/**` (TODAS las marcas) **construye DESDE el canon** — `@luana/ui-kit` es el único lego. **El build debe igualar el mockup ratificado** ("lo que ves = lo que se programa"). Reglas HARD:

- **List/detail → `EntityWorkspaceLayout`** (1-panel: master grilla de `EntityInfoCard` + Toolbar; detalle = `EntitySubNavBar` **full-bleed tercer-ribbon** sticky + leaf). Root-pill `‹ {RootLabel}` vuelve; identidad = `EntityPicker`. **❌ cablear list/detail a mano** por superficie · **❌ franja N3 en card con borde redondeado**.
- **Contenedor HOJA:** 100% ancho full-responsive · franjas full-bleed · contenido en `PageContainer` + `PageContentStack`. **❌ `<div>` de layout sueltos** donde hay page-primitive.
- **`EntityPicker`:** buscar server-side debounced + fetch paginado (cursor) + render windowed + lazy. **❌ cargar toda la colección al cliente.**
- **`Select` canónico** (Shadcn). **❌ `<select>` nativo** en producto.
- **`EntityInfoCard` Opción B** (+ Skeleton + Empty) · **autosave** 600ms+coalesce + 1 `FloatingAutosaveIndicator` por página + barrita de agente.
- **Tokens, no arbitrary** (spacing/radius/font-size/color-hex de la escala — canon §0).

**Lo que YA existe se MODIFICA al canon** (punto de partida nuevo 2026-06-08), no se deja como estaba. Si una primitiva del canon aún no está en `@luana/ui-kit` (programa en build), implementala según el ejemplo del canon §6 (NO una versión a mano divergente). `builder-frontend` carga el canon vía la rule antes de tocar FE. `auditor-frontend` rechaza el build que no compone del canon.

**★ Storybook = SSoT visual (cement 2026-06-22 · canon §5):** `builder-frontend` **parte de la story de Storybook que `/architect` citó** en `03-arch.md § FE` (`@luana/ui-kit` · la lee — controles + estados — antes de codear) y construye DESDE el kit. Si la story introduce una **primitiva shared net-new**, el builder la **PROMUEVE a `core/@luana/ui-kit` + agrega su story** (deliverable, antes del merge) y la feature la consume vía import — **NUNCA** re-implementación local que driftea. `auditor-frontend` verifica que el net-new se promovió con story (si no, CHANGES_REQUESTED).

## Step 0 — Bootstrap + state transition

```bash
WS=$(git rev-parse --show-toplevel)
BRAND={brand}                                                # vitalia | platform
STORY_DIR=${WS}/${BRAND}/docs/product/stories/{story-id}
cat ${STORY_DIR}/checkpoint.md      # verify state=ready (o state=developing si retomas)
cat ${STORY_DIR}/06-tickets.yaml    # pila tickets
cat ${STORY_DIR}/04-validators.yaml # ★ corazón autonomous loop ★
cat ${STORY_DIR}/05-guidelines.md   # patterns + files in scope
```

Si state=ready → transition a building (primera vez):
```yaml
# checkpoint.md
state: developing   # ★ TRANSITION ready → developing ★
phase: BUILD_T1
```

WIP cap check (★ v2 2026-05-28): el cap `developing` es **≤ 1 por módulo** (un build en vuelo por módulo). Stories `developing` concurrentes en módulos DISTINTOS = OK. SSoT: `.claude/rules/story-closure-gate.md` § WIP cap v2.

### Step 0.4 — Build-claim + story-closure gate module-scoped (story-closure-gate.md Layer 2 · ADR-009)

ANTES de pickup, (a) computar el módulo de esta story, (b) verificar que NO haya otra story del **mismo módulo** abierta sin cerrar, (c) adquirir el build-claim (lock module-scoped + registro para el cockpit):

```bash
WS=$(git rev-parse --show-toplevel)
BRAND={brand}
STORY_DIR=${WS}/${BRAND}/docs/product/stories/{story-id}
MODULE=$(grep -E "^module:" ${STORY_DIR}/checkpoint.md | head -1 | awk '{print $2}')
MODULE=${MODULE:-_nomodule}

# (b) Gate module-scoped: bloquea SOLO si otra story del MISMO módulo está abierta
#     sin defer_audit (cross-módulo concurrente = permitido bajo hub único).
#     ★ proceso v5: phase AWAIT_CHRIS_VERIFY (story en G esperando a Chris) NO bloquea
#     — si no, una story en verify deadlockea otra del mismo módulo (story-closure-gate).
for cp in ${WS}/${BRAND}/docs/product/stories/*/checkpoint.md; do
  OTHER_ID=$(basename $(dirname $cp))
  [[ "$OTHER_ID" == "{story-id}" ]] && continue
  OTHER_MOD=$(grep -E "^module:" $cp | head -1 | awk '{print $2}')
  STATE=$(grep -E "^state:" $cp | head -1 | awk '{print $2}')
  DEFER=$(grep -E "^defer_audit:" $cp 2>/dev/null | awk '{print $2}')
  PHASE=$(grep -E "^phase:" $cp 2>/dev/null | head -1 | awk '{print $2}')
  if [[ "$OTHER_MOD" == "$MODULE" ]] && [[ "$STATE" =~ ^(developing|developed|reviewing)$ ]] \
     && [[ "$DEFER" != "true" ]] && [[ "$PHASE" != "AWAIT_CHRIS_VERIFY" ]]; then
    echo "BLOCK: story $OTHER_ID (módulo $MODULE) en state=$STATE sin defer_audit"
  fi
done

```

Si encuentro otra story open del **mismo módulo** (developing/developed/reviewing) SIN `defer_audit: true` → REFUSE pickup. Output verbatim:

```
❌ Story closure gate (module-scoped): cannot pickup ticket T-{n} de story {new-story-id}
   porque story {open-story-id} del MISMO módulo {module} está en state={state} sin defer_audit.
   (Stories de OTROS módulos developing en paralelo = OK.)

   Acciones disponibles:
   1. Continuar story {open-story-id} hasta state=done (default forward-motion)
   2. Ratificar defer_audit:true en {open-story-id}/checkpoint.md con razón + Chris explícito
   3. Tomar una story de OTRO módulo

   SSoT regla: .claude/rules/story-closure-gate.md (Layer 2)
```

NO arrancar el ticket si el gate bloquea. Esperar acción explícita Chris.

## Step 0.5 — Phase 0: Context pre-flight (MANDATORY antes Step 1)

> Origen: process-improvement 2026-05-05 R1. Sin context-builder cada subagent
> re-lee 30-50k tokens spec+arch+rules. Brief Haiku 5-8k tokens amortiza.

Antes de tomar ticket, asegurás `CONTEXT-BRIEF.md` fresco existe en story-folder.

```bash
BRIEF=$STORY_DIR/CONTEXT-BRIEF.md
LATEST_COMMIT=$(git log -1 --format=%H -- $STORY_DIR)
```

Decidir si spawn context-builder:
- `CONTEXT-BRIEF.md` no existe → SPAWN
- `CONTEXT-BRIEF.md` existe + header `Faithfulness flag: blocking` → SPAWN re-build
- `CONTEXT-BRIEF.md` más viejo que último commit story → SPAWN refresh
- Fresco + `clean|partial` → SKIP

Si SPAWN:
```
Agent({
  description: "Build context brief for ticket T-{n} brand={brand}",
  subagent_type: "context-builder",
  model: "haiku",
  prompt: "<brand>: {brand}                          # ★ REQUIRED — multibrand scope
           <pr_folder>: <STORY_DIR absolute>;
           <modules>: <comma list from story spec>;
           <phase>: builder;
           <subsystem_keywords>: <comma list>;
           <frameworks>: <fastapi, langgraph, anthropic, sqlalchemy, pydantic, etc.>"
})
```

Espera context-builder + context-validator. Lee header. Si flag `blocking` → STOP, escalate Chris.

**Pasás `CONTEXT-BRIEF.md` path + `<brand>: {brand}` en TODO prompt subagent downstream.**

## Step 0.6 — Hot-fix repro gate (R26 2026-05-05)

> SSoT: `.claude/rules/hotfix-repro-mandatory.md`.

Si ticket es hot-fix (señales: title contiene `bug|hot-fix|regression|incident|bis|revert`, origin `handoff doc|incident|escalation`, sub-num `T-N.bis`, scope quirúrgico ≤2h), ANTES de spawn builder, reproducir bug local + validar diagnóstico (paths brand-scoped, e.g. `cd ${WS}/{brand}/backend && ${WS}/.venv/bin/pytest ...`). Cita `repro_evidence` en ticket entry de `06-tickets.yaml`.

Si `repro_verified: false` o ausente en hot-fix ticket → REFUSE spawn:
```
ERROR — hot-fix ticket missing repro_verified per
.claude/rules/hotfix-repro-mandatory.md.
Run repro command first, document evidence, then proceed.
```

Detalle workflow Step 1-3 (reproduce → diagnóstico → cite evidence) en rule SSoT.

## Step 0.7 — Dispatch plan + autonomous_mode (NEW 2026-05-27)

> SSoT: `.claude/rules/architect-autonomous-mode.md`.

Si `{brand}/docs/product/stories/{story-id}/dispatch-plan.md` existe (producido por `/architect` Step 7), **leerlo + respetar verbatim**:

1. **`assignment` block en cada ticket de `06-tickets.yaml`** dicta:
   - `primary_agent`: el sub-agent type EXACTO a spawnar (NO usar `general-purpose` default — usar el agente nombrado: `builder-backend`, `builder-frontend`, `builder-agentic`)
   - `model_preference`: el TIER (workhorse | flagship | opencode), resuelto en `project.config.yaml::models` — respetar salvo override hard de R23 (agentic prod → `flagship`)
   - `must_load_skills`: lista verbatim a citar en spawn prompt
   - `forbidden_to_touch`: pasar al builder como guardrail explícito
   - `rationale`: respeta razón (no override silencioso)

2. **`autonomous_mode` en `checkpoint.md`**:
   - `false` (default) → `/dev-team` para después de cada ticket completo + espera ratificación Chris para próximo. Auto-handoff a `/auditor` cuando ALL tickets GREEN (story-closure-gate Layer 1).
   - `true` (Chris opt-in explícito) → encadenar TODOS los tickets seguidos sin pausa + auto-handoff `/auditor` + auto-handoff `/pm-vitalia` merge si APPROVED. Respetar `autonomous_mode_caps` (max_iterations, max_audit_iterations, max_total_cost_usd, max_wall_clock_minutes).
   - Si caps excedidos durante autonomous_mode → halt + state=blocked + escalate Chris (NO continuar a ciegas).

3. **`playwright_visual_scope` en `04-validators.yaml`**:
   - `story_scope_routes` + `story_scope_components` definen DÓNDE puede tocar visualmente
   - `forbidden_visual_changes.paths` definen DÓNDE NO (Shadcn primitives, shared, app shell)
   - Si builder necesita cambio visual fuera scope → STOP + documentar en `T-{n}-impl-log.md § Cross-story observed bugs` + escalate Chris (anti-egoísmo: no arreglar fuera de scope sin ratificar)

**Si `dispatch-plan.md` NO existe** (architect skill viejo pre-2026-05-27): inferir assignments del `06-tickets.yaml` legacy + warning al user "story produced sin dispatch-plan — usando defaults (puede ser sub-óptimo)". NO bloquear.

## Step 1 — Tomar ticket + decidir owner

Filtrar tickets con `state: ready` (deps cumplidas). Decidir owner según `owner_eligibility` + `production_code` flag (R23):

| Surface | production_code | Owner preferido | Razón |
|---|---|---|---|
| BE no-agentic | true | qwen-opencode | costo, qwen capable |
| BE no-agentic | false (tests/docs/tooling) | qwen-opencode o workhorse | trivial test/doc work |
| FE no-agentic | true | qwen-opencode | costo, qwen capable |
| FE no-agentic | false | qwen-opencode | trivial |
| AGENTIC | true | flagship (MISMA sesión, NO opencode) | brand voice + protected surfaces + prompt eng del flagship |
| **AGENTIC** | **false (tests/docs only)** | **workhorse** | **R23 — test-only/doc-only sobre módulo agentic NO requiere el flagship** |
| Migration aislada | true | qwen-opencode | trivial DDL |
| Cross-module shared | true | workhorse o flagship | complexity |

**Reglas hard:**
- AGENTIC ticket + `production_code: true` → SIEMPRE el tier flagship (`models.flagship` del seam). Esto se ejecuta en MISMA sesión Claude Code (tú como `/dev-team` corriendo el flagship).
- AGENTIC ticket + `production_code: false` → Sonnet OK. Tests/docs/tooling
  sobre `modules/{copilot,sales_agent}/` no requieren el reasoning del flagship.
- Si tu modelo de sesión NO es el flagship (`models.flagship` en project.config.yaml) y ticket=AGENTIC + production_code=true → STOP, escala
  Chris: "necesito el modelo flagship (ver project.config.yaml::models) para este ticket. Cambiame de modelo."

Update `06-tickets.yaml` ticket `T-{n}`:
```yaml
state: assigned
assigned_to: qwen-opencode | flagship | workhorse   # tiers → project.config.yaml::models
assigned_at: 2026-05-06T...
transitions:
  - { state: assigned, at: ..., by: "/dev-team", to: "<owner>" }
```

Crear `{brand}/docs/product/stories/{story-id}/T-{n}-impl-log.md` con plan inicial + iteration_log empty.

## Step 2 — Spawn builder (model-specific)

### ★ Pre-commit smoke gate (G5 — origen report.html 2026-05-09: 17 buggy_code incidents)

Antes de cualquier `git commit` por el builder, MUST cumplir gate hard:

1. Run validators asociados al ticket (`acceptance.validator_ids` en `06-tickets.yaml`)
2. ALL validators GREEN antes commit. RED → bloquea commit, fix file, re-run.
3. Lint + format clean (`ruff check src/ + ruff format --check src/` BE; `eslint + tsc --noEmit` FE).
4. Si validator es env-gated (ej. `EVAL_GOLDENS_COST_BUCKET_VERIFY=1`) → builder MUST run con env real, NO skip.
5. Si validator requiere case-sensitivity check (enum/string-literal) → builder verifica match exacto antes commit.

**HARD rule:** builder commitea SOLO con todos los gates GREEN. Auditor catch-bugs-pre-existing era cost-leak Opus 2-3x. Pre-commit gate cierra esto.

Builder prompts en Step 2A/2B/2C citan este gate verbatim. Si builder pushea con RED → /dev-team rebota a `state: tests-failing` ANTES Step 4 verify.

### ★ must_load_skills enforcement (v4.1 cement 2026-05-19)

**Antes de spawn builder**, `/dev-team` LEE `05-guidelines.md § must_load_skills` y EXTRACTA la lista completa (con `when:` conditions evaluadas según ticket surface). Pasa la lista RESOLVIDA al builder spawn como bloque verbatim.

**Builder MUST entregar** en `T-{n}-result.md` una sección obligatoria:

```markdown
## Skills consulted (must_load enforcement v4.1)

| Skill / Rule | Status | When consulted |
|---|---|---|
| backend-expert | ✅ loaded | Step 0 — DDD pattern check |
| frontend-expert | n/a | surface=BE only |
| .claude/rules/tenant-isolation.md | ✅ loaded | mid-build — verify query filter |
| .claude/rules/anti-duplication.md | ✅ loaded | Step 0 grep cross-brand |
| playwright-expert | ✅ loaded | mid-build — POM patterns |
| ... | ... | ... |
```

**Auditor verification:** auditor Step 2 verifica esa sección existe + lista todas las skills `must_load`. Si missing/incomplete → CHANGES_REQUESTED automático (categoría: process discipline). Auditor self-fix puede agregar la sección si builder olvidó documentar pero cargó las skills (whitelist #12 docstring trivial análogo).

### Step 2A — Owner = qwen-opencode (BE/FE no-agentic)

Construir prompt para qwen invocando opencode CLI. **Paths brand-scoped + workspace root parametrizado** (`${WS}` resuelto via `git rev-parse --show-toplevel`):

```bash
WS=$(git rev-parse --show-toplevel)
BRAND={brand}                                                # vitalia | platform
STORY_DIR=${WS}/${BRAND}/docs/product/stories/{story-id}

cat > /tmp/T-{n}-qwen-prompt.md <<EOF
Eres developer Luana ({brand} brand) ejecutando T-{n} de story {story-id}.
Brand scope: ${BRAND} — TODO edit debe respetar paths bajo ${BRAND}/. NO editar ${WS}/core/luana-core-*/src/ (engine, requires /pm-vitalia flujo engine). NO editar paths fuera de ${BRAND}/.

PRIORITY READ — CONTEXT-BRIEF (Haiku-built, 5-8k tokens, contiene spec+arch+rules+anti-dup+canonical docs):
- ${STORY_DIR}/CONTEXT-BRIEF.md

Lee TAMBIÉN estos archivos del READY PACKAGE (si brief insuficiente):
- ${STORY_DIR}/01-spec.md — Gherkin scenarios + (si UI std) wireframes
- ${STORY_DIR}/03-arch.md — technical decisions (★ v4.1: incluye § Test Construction Plan)
- ${STORY_DIR}/04-validators.yaml — ★ comandos must_pass + § test_construction_plan (orden + POMs + fixtures + scenario_to_test mapping)
- ${STORY_DIR}/05-guidelines.md — patterns required/forbidden + § must_load_skills (★ v4.1 enforceable)
- ${STORY_DIR}/06-tickets.yaml — find your ticket entry T-{n} + gherkin_coverage

★ MUST LOAD SKILLS (v4.1 enforceable — DEBE cargar TODAS antes de codear):
<LIST EXTRACTED FROM 05-guidelines.md § must_load_skills RESOLVED, e.g.:>
- backend-expert
- playwright-expert (si test_construction_plan.playwright_required=true)
- .claude/rules/tenant-isolation.md
- .claude/rules/anti-duplication.md
- .claude/rules/spanish-text.md
- .claude/rules/auditor-self-fix-policy.md (saber qué auditor self-fix vs spawn dev-team)
- FastAPI canonical patterns (si BE endpoint nuevo)
- ... (extractar verbatim según ticket surface + module)

AUTONOMOUS LOOP:
1. Load must_load_skills listed above (Step 0). Each Skill tool invocation registrado.
2. Read 04-validators.yaml § test_construction_plan — sigue creation_order para Playwright tests (no inventes orden).
3. Read 04-validators.yaml validators list. Run validators ASOCIADOS al ticket T-{n} (acceptance.validator_ids list).
4. RED: tests fallarán (no implementation yet).
5. Implementá MÍNIMO para que validators GREEN — solo files dentro 05-guidelines.md "Files in scope" (TODOS brand-scoped bajo ${BRAND}/).
6. Re-run validators. Si fallan: fix targeted file por error trace, re-run failing validator only.
7. Repeat hasta TODOS validators GREEN o iteration cap reached (default 10).
8. Update T-{n}-impl-log.md con iteration_log VIVO mientras trabajás (cada iter: timestamp + validator + result + fix applied).
9. ★ v4.1: T-{n}-result.md MUST incluir sección "Skills consulted (must_load enforcement v4.1)" con tabla skill/rule + status + when consulted (ver dev-team SKILL.md § must_load_skills enforcement).

Reglas TDD obligatorias:
1. RED: validators fallan primero (sin implementation)
2. GREEN: implementa mínimo
3. REFACTOR: limpiar

Convenciones (.claude/rules/* — citados también en 05-guidelines.md):
- backend-ddd.md o frontend-fsd.md
- tenant-isolation.md
- spanish-text.md (Spanish neutro, no voseo)
- backend-migrations.md (idempotente)
- anti-duplication.md (cross-brand mirror ban)
- tdd-mandatory.md
- git-safety.md (triple-branch: wip/* | main | release/*; NO 'origin development')

Quality gates antes push (★ HARD — G5 pre-commit smoke gate):
- TODOS validators de 04-validators.yaml asociados al ticket → GREEN antes commit
- Lint + format clean (cd ${BRAND}/backend && ../../.venv/bin/ruff check + ruff format --check; cd ${BRAND}/frontend && npx eslint + tsc --noEmit)
- Env-gated validators corridos con env real (NO skip si validator dice EVAL_*=1)
- Case-sensitivity check si validator compara enum/string-literal
- 05-guidelines.md "Files in scope" respected (no escape; SOLO ${BRAND}/ paths)
- RED bloquea commit. Fix file → re-run validator → repeat hasta GREEN.

Push destination (triple-branch policy):
- git push origin "\$(git branch --show-current)"   # wip/{slug} autosave, main post squash, release/{brand}-vX.Y.Z
- NUNCA 'git push origin development' (branch eliminado en reorg 2026-05-15)

Output al terminar:
- T-{n}-result.md con diff resumen + validator gates output literal + commit SHA
- Estado ticket: pushed (en 06-tickets.yaml)
- Last line del response: "done -> T-{n}-result.md"

**Output protocol · chris-input.md per ticket (v2 cement 2026-05-27):** al cerrar cada ticket T-{n} (`T-{n}-result.md` escrito + commit pushed), appendear entry al chris-input.md de la story con verdict `✓ APLICADO` listando paths modified + decisión técnicas tomadas + reference al gate-output.json result. NO validar cap_change_type (eso es responsabilidad de `/architect`).

Si cap_reached (10 iter sin GREEN):
- T-{n}-impl-log.md sección "Cap reached — escalating"
- Estado ticket: blocked
- Last line: "blocked -> T-{n}-impl-log.md (see iteration_log)"
EOF

cd ${WS}
opencode run \
  --prompt-file /tmp/T-{n}-qwen-prompt.md \
  --workspace ${WS} \
  --model qwen-coder \
  --max-iterations 50

# Si opencode falla / API no disponible → fallback: copiá prompt + Chris ejecuta manual:
# echo "Pegá esto en opencode CLI: $(cat /tmp/T-{n}-qwen-prompt.md)"
```

Mientras qwen trabaja → tú NO interfieres. Cuando termina:
1. Verificás `T-{n}-result.md` existe y dice `state: pushed` (o blocked)
2. Verificás commit SHA en git log
3. Actualizás `06-tickets.yaml` ticket → state: pushed o blocked
4. Si pushed → continúa Step 4 (next ticket). Si blocked → escalate.

### Step 2B — Owner = flagship (AGENTIC production code)

Spawnás agent `builder-agentic` (tier flagship) via Agent tool. REQUIRED: pasá `<brand>: {brand}` en prompt.

```
Agent({
  description: "Build agentic ticket T-{n} brand={brand}",
  subagent_type: "builder-agentic",
  prompt: "<brand>: {brand}                          # ★ REQUIRED — multibrand scope
           <pr_folder>: {brand}/docs/product/stories/{story-id}/
           PRIORITY READ: {brand}/docs/product/stories/{story-id}/CONTEXT-BRIEF.md (Haiku-built, 5-8k tokens compresses spec+arch+rules+anti-dup+canonical docs)
           READY PACKAGE (todos bajo {brand}/docs/product/stories/{story-id}/): 01-spec.md + 02-design-agentic.md + 03-arch.md (★ v4.1: incluye § Test Construction Plan) + 03-arch-agentic.md + 04-validators.yaml (★ v4.1: 5 categorías + test_construction_plan + scenario_coverage sub-categorías) + 05-guidelines.md (★ v4.1: must_load_skills enforceable) + 06-tickets.yaml (gherkin_coverage por ticket)
           ★ MUST_LOAD SKILLS (v4.1 enforceable): <list extracted from 05-guidelines.md § must_load_skills resolved per ticket surface — typical agentic: copilot-expert/sales-agent-expert + LangGraph canonical docs + claude-api + graceful-degradation (timeout+fallback+circuit breaker) + auditor-self-fix-policy.md + tenant-isolation.md + spanish-text.md>
           ★ MUST DELIVER in T-{n}-result.md: sección "Skills consulted (must_load enforcement v4.1)" con tabla skill/rule + status + when. Auditor flag CHANGES_REQUESTED si missing.
           Surface scope: SOLO {brand}/backend/src/modules/{brand}/{copilot,sales_agent}/{tools,extractors,workflows,personas,goldens,kb}/ (brand-extension). NUNCA core/luana-core-*/src/ (engine — requires /pm-vitalia lift).
           AUTONOMOUS LOOP: implement → run validators (acceptance.validator_ids) → fix → repeat hasta GREEN o cap_reached
           TDD: eval goldens RED first, integration tests, tools tests, etc.
           ★ G5 PRE-COMMIT SMOKE GATE: validators GREEN + lint + format + env-gated tests con env real + case-sensitivity match — TODO antes commit.
           ★ Test Construction (v4.1): seguir test_construction_plan.creation_order del 04-validators.yaml para Playwright tests (no inventar orden, POMs ni fixtures).
           Push destination: git push origin \$(git branch --show-current). NUNCA 'origin development'.
           Output: T-{n}-result.md (con Skills consulted) + commit pushed
           Last line: done -> {brand}/docs/product/stories/{story-id}/T-{n}-result.md (o blocked -> T-{n}-impl-log.md)"
})
```

`builder-agentic` corre validators + push. Devuelve `done -> T-{n}-result.md`.

### Step 2C — Owner = workhorse (cross-module shared o tests/docs sobre agentic)

Spawnás agent `builder-backend` o `builder-frontend` con model=sonnet (default). Prompt SIEMPRE referencia `CONTEXT-BRIEF.md` + propaga `<brand>`:

```
Agent({
  description: "Build {surface} ticket T-{n} brand={brand}",
  subagent_type: "builder-{backend|frontend}",
  model: "sonnet",
  prompt: "<brand>: {brand}                          # ★ REQUIRED — multibrand scope
           <pr_folder>: {brand}/docs/product/stories/{story-id}/
           Read {brand}/docs/product/stories/{story-id}/CONTEXT-BRIEF.md FIRST (saves 30-50k tokens vs raw docs).
           READY PACKAGE (todos bajo {brand}/docs/product/stories/{story-id}/): 01-spec.md + 03-arch.md (★ v4.1 § Test Construction Plan) + 04-validators.yaml (★ v4.1 5 categorías) + 05-guidelines.md (★ v4.1 must_load_skills) + 06-tickets.yaml
           ★ MUST_LOAD SKILLS (v4.1 enforceable): <list extracted from 05-guidelines.md § must_load_skills resolved>
           ★ MUST DELIVER in T-{n}-result.md: sección "Skills consulted (must_load enforcement v4.1)".
           Surface scope: SOLO vitalia/backend/src/ + vitalia/frontend/src/. NUNCA core/luana-core-*/src/ (engine).
           AUTONOMOUS LOOP: implement → run validators → fix → repeat
           TDD obligatorio.
           ★ G5 PRE-COMMIT SMOKE GATE: validators GREEN + lint + format + env-gated tests con env real + case-sensitivity match — TODO antes commit. RED bloquea commit.
           ★ Test Construction (v4.1): seguir test_construction_plan.creation_order del 04-validators.yaml.
           Push destination: git push origin \$(git branch --show-current). NUNCA 'origin development'.
           Last line: done -> {brand}/docs/product/stories/{story-id}/T-{n}-result.md"
})
```

## Step 3 — Self-monitor durante build

Mientras el dev (qwen | builder-{be,fe,agentic}) trabaja, tú:
- Touchéas `T-{n}-impl-log.md` periodically con timestamps "still in progress"
- Si dev se cuelga > 30min sin progress visible → escala Chris
- Si dev reporta `blocked` → registrar en log + escala `/pm`

## Step 4 — Verificar result + gate-runner enforcement

Cuando dev termina, leer `T-{n}-result.md` + verificar `gate-output.json`:

- [ ] Validators de 04-validators.yaml asociados al ticket → todos ✅?
- [ ] **`gate-output.json` existe en story-folder + `overall.any_fail = false`?**
      Si missing → builder no invocó gate-runner. SPAWN gate-runner directo aquí:
      ```
      Agent({
        description: "Force gate-runner T-{n} brand={brand}",
        subagent_type: "gate-runner",
        model: "haiku",
        prompt: "<brand>: {brand};
                 <pr_folder>: {brand}/docs/product/stories/{story-id}/;
                 <command>: test-{backend|frontend|all};
                 <iter>: <N>"
      })
      ```

      **R22 post-spawn validation (origen 2026-05-05 caso T-1.bis):**
      Después del spawn, VERIFY el artifact realmente escribió a disco. Si gate-runner
      reporta "ERROR — gate-output.json write failed" en su last-line, OR si el
      file no existe post-spawn, NO confíes en stdout output del agent — re-spawn
      UNA segunda vez con mismo prompt. Si segunda invocación también falla:
      ```bash
      # Fallback manual: orchestrator escribe gate-output.json directo (paths brand-scoped + workspace root parametrizado)
      WS=$(git rev-parse --show-toplevel)
      cd ${WS}/{brand}/backend && ${WS}/.venv/bin/{ruff,pytest} ... > /tmp/gate.log 2>&1
      python3 -c "import json; ..." > ${WS}/{brand}/docs/product/stories/{story-id}/gate-output.json
      ```
      Documentar en T-{n}-impl-log.md sección "Gate-runner failover" + escalar
      backlog R22 retry.

      Read JSON. Si `any_fail=true` → ticket vuelve a `tests-failing`, hand off `/dev-team` con findings.
- [ ] Commit SHA presente + git log lo confirma?
- [ ] Push exitoso (`git push origin "$(git branch --show-current)"` — wip/* | main | release/{brand}-vX.Y.Z. NUNCA 'origin development')?

Si cualquier gap → ticket vuelve a `tests-failing` o `building`. Si dev itera ≥5x sin éxito → `blocked` + escala.

> **Origen R2 process-improvement 2026-05-05 (D2):** sin gate-runner enforcement
> orchestrator, cada subagent corre su propio pytest cycle (~10-15% tokens
> duplicados). gate-runner Haiku produce JSON estructurado consumible por auditor
> sin re-correr suite ni parsear stdout.

### Step 4.5 — Phase D local coverage check (★ v4.1 pre-handoff verification)

> Origen v4.1 cement 2026-05-19. Antes de cerrar TODO el story (auto-handoff
> auditor), `/dev-team` verifica LOCALMENTE que cada Gherkin scenario de
> `01-spec.md` mapea a ≥1 test PASS. NO espera al auditor para descubrir gaps.

```bash
WS=$(git rev-parse --show-toplevel)
STORY_DIR=${WS}/{brand}/docs/product/stories/{story-id}

# Extract scenarios from 01-spec.md
grep -nE "^### Scenario" ${STORY_DIR}/01-spec.md > /tmp/scenarios.txt
SCENARIO_COUNT=$(wc -l < /tmp/scenarios.txt)

# Extract gherkin_coverage from 06-tickets.yaml
grep -A 10 "gherkin_coverage:" ${STORY_DIR}/06-tickets.yaml > /tmp/coverage.txt
COVERED_COUNT=$(grep -c "scenario:" /tmp/coverage.txt)

if [ $SCENARIO_COUNT -gt $COVERED_COUNT ]; then
  echo "❌ Phase D local gap: $SCENARIO_COUNT scenarios en 01-spec.md, $COVERED_COUNT cubiertos en gherkin_coverage"
  echo "   STOP — agrega entries faltantes a 06-tickets.yaml::gherkin_coverage antes auto-handoff auditor"
  exit 1
fi

# Verify cada test citado existe + PASS
# (lectura gherkin_coverage + pytest/playwright targeted run + report)

# ★ Seam coverage gate (HB-96 · cobertura = colaborador real, no mock)
# Un escenario de costura cubierto SOLO por un test que mockea el colaborador del otro
# lado = MOCK-ONLY (= MISSING). El gate valida la declaración seam_coverage + escanea
# los targets code-db/router/component-shell (mock-markers sin colaborador real → FAIL).
${WS}/.venv/bin/python ${WS}/scripts/check_seam_coverage.py \
    --report ${STORY_DIR}/04-validators.yaml --story-dir ${STORY_DIR} || {
  echo "❌ Phase D local: cobertura de costura inválida o MOCK-ONLY."
  echo "   Construí el test del tipo declarado (integration-realdb/contract/router/e2e-live)"
  echo "   contra el COLABORADOR REAL, o ejercé la live-verify (#37) para la costura auth."
  echo "   Escape por test (auditor escruta): línea '# seam-ok: <razón>'."
  exit 1
}

echo "✅ Phase D local coverage: $SCENARIO_COUNT/$SCENARIO_COUNT scenarios mapeados + costuras OK"
```

Si Phase D local detecta gap → `/dev-team` REFUSE auto-handoff. Update `T-{n}-impl-log.md § Phase D gap` + revolver al loop autonomous para completar cobertura. Si gap es de spec (scenario sin test natural) → ESCALATE Chris ("scenario X de 01-spec.md no es testeable como definido").

**Justificación:** auditor Phase D antes detectaba gaps post-handoff → CHANGES_REQUESTED round-trip. Pre-check local en dev-team cierra el loop sin desperdiciar audit cycle del flagship.

### ★ Step 4.5b — Ledger de cobertura vivo: PRODUCTOR (proceso v5 §5.2)

`/dev-team` es el **productor** que mantiene VIVA la columna `estado` de la `§ Matriz de cobertura` (`01-spec.md`). Cada vez que un ticket construye el comportamiento de un `Bif-N`/`RN-N`/`AC-N`, dev-team marca ese ítem `✅ construido` (con su test/ruta) en la matriz. Sin este paso el ledger nace en `refined` y llega STALE a G (Chris leería una foto vieja).

- Ítem construido → `✅ construido` + test/ruta en la celda.
- Ítem que NO se construirá en esta story → se deja `⬜ pendiente` (en G se decide `⏳ ahora` o `→ historia {id}`).
- **PISO HARD:** si `cap_change_type: new`, los ítems del **happy path** DEBEN quedar `✅` antes de cerrar `developed` — el core no se difiere (REFUSE si un happy-path queda `⬜`/`→historia`).

## Step 4.6 — Gate live-verify (Critical Rule #37) — BLOQUEANTE antes de developed

> Mismo rango imperativo que el Phase D local de gherkin. Si falla → NO se escribe `state: developed` y NO se emite el auto-handoff a `/auditor`.

```bash
WS=$(git rev-parse --show-toplevel)
STORY_DIR=${WS}/{brand}/docs/product/stories/{story-id}

NATURE=$(grep -E "^verification_nature:" ${STORY_DIR}/04-validators.yaml 2>/dev/null | head -1 | awk '{print $2}')
DEMO_REQ=$(grep -E "^demo_required:" ${STORY_DIR}/04-validators.yaml 2>/dev/null | head -1 | awk '{print $2}')

# Auto-skip para stories puramente técnicas (sin UI ni superficie user-reachable)
if [[ "$NATURE" == "técnica" && "$DEMO_REQ" != "true" ]]; then
  echo "✅ Live-verify gate auto-skip: verification_nature=técnica, demo_required=false"
  # Registrar la razón en checkpoint si aún no está
  grep -q "dod_live_verified_skip_reason:" ${STORY_DIR}/checkpoint.md || \
    echo "  (agregar dod_live_verified_skip_reason en checkpoint.md antes del handoff)"
else
  # GATE DURO — verificar los 3 requisitos en checkpoint.md
  DOD_FLAG=$(grep -E "^dod_live_verified:" ${STORY_DIR}/checkpoint.md 2>/dev/null | awk '{print $2}')
  DOD_EVIDENCE=$(grep -A 2 "^dod_evidence:" ${STORY_DIR}/checkpoint.md 2>/dev/null | grep -c "action:")
  DEMO_SCRIPT=$(ls ${STORY_DIR}/demo-script.md 2>/dev/null | wc -l)

  GATE_OK=true
  [[ "$DOD_FLAG" != "true" ]] && GATE_OK=false
  [[ "$DOD_EVIDENCE" -lt 1 ]] && GATE_OK=false
  [[ "$DEMO_REQ" == "true" && "$DEMO_SCRIPT" -lt 1 ]] && GATE_OK=false

  if [[ "$GATE_OK" != "true" ]]; then
    echo "❌ Gate live-verify BLOQUEADO (Critical Rule #37):"
    echo "   Story funcional/UI sin live-verify real. Antes de cerrar developed:"
    echo "   1. Ejercé la acción REAL en dev-app (POST/PATCH/PUT/DELETE) con Chrome DevTools MCP"
    echo "      → skill chrome-devtools-verify; leer Console (0 errores) + Network + logs"
    echo "   2. Registrá en checkpoint.md: dod_live_verified: true + dod_evidence (≥1 entry con"
    echo "      action/observed/backend_log — GET 200 NO basta)"
    echo "   3. Creá demo-script.md en la carpeta de la story (si demo_required: true)"
    echo "   NO marcar state: developed hasta que los 3 pasen."
    echo "   Ref: .claude/rules/definition-of-done-live-verify.md"
    exit 1
  fi
  echo "✅ Gate live-verify: dod_live_verified=true, dod_evidence OK, demo-script OK"
fi
```

Si el gate falla → STOP. Volvé a Step 2/3 para ejercer la acción real con Chrome DevTools MCP antes de avanzar.

## Step 5 — Avanzar a siguiente ticket o cerrar story

Update `06-tickets.yaml`:
```yaml
state: pushed
push_commit_sha: abc1234
transitions:
  - { state: tests-passing, ... }
  - { state: pushed, ..., commit: "abc1234" }
```

Si quedan tickets `ready` → continuar Step 1 con next ticket.

Si TODOS tickets pushed → (1) verificar Phase D local (Step 4.5) + (2) verificar gate live-verify (Step 4.6) → transition story a `developed`. **Recién entonces RAMA según `autonomous_mode` (★ proceso v5 · story-closure-gate Fase G — re-secuencia: el auto-handoff ya NO es incondicional):**

```bash
AUTONOMOUS=$(grep -E "^autonomous_mode:" ${STORY_DIR}/checkpoint.md 2>/dev/null | awk '{print $2}')
DEFER=$(grep -E "^defer_audit:" ${STORY_DIR}/checkpoint.md 2>/dev/null | awk '{print $2}')
```

### Caso default — G · Chris-verify (pausa-y-ofrece) ★ proceso v5

Si `autonomous_mode` NO es `true` y la story es funcional (`demo_required: true` / `verification_nature ∈ {funcional, ambas}`) → **NO auto-handoff a `/auditor`**. Pausá en **G**: Chris ejerce el kit ANTES del auditor. Sin estado nuevo (`state: developed` + `phase: AWAIT_CHRIS_VERIFY`).

```yaml
# {brand}/docs/product/stories/{story-id}/checkpoint.md
brand: {brand}     # ★ REQUIRED — multibrand scope
state: developed   # ★ TRANSITION developing → developed ★
phase: AWAIT_CHRIS_VERIFY        # ★ G · NO HANDOFF_TO_AUDITOR todavía
chris_verify: { required: true, signoff: null, rounds: [] }
last_artifact: T-{N}-result.md (last ticket)
next_action: "Chris ejerce el kit live → firma chris_verify.signoff → /pm-vitalia reconcile (R) → /auditor"
```

EMITIR el KIT verbatim (el kit ya lo produjo el developed-boundary, #37 Layer 10):

```
✅ Story {brand}/{story-id} all tickets pushed · validators GREEN · live-verify OK.
Story state: developing → developed · phase: AWAIT_CHRIS_VERIFY (G · Chris-verify).

(WIP cap: phase AWAIT_CHRIS_VERIFY NO cuenta contra developed≤1 → otra story
 del módulo puede avanzar mientras verificás.)

🧪 KIT para que ejerzas vos (antes del auditor):
- demo-script.md: {path}
- dev-app live: make dev-app-{brand} → dev-app.{brand}lat.com (Chrome DevTools MCP)
- dod_evidence: {N} writes ejercidos
- 📊 LEDGER de cobertura: {X ✅ construido · Y → historia · Z ⏳ ahora}

→ Ejercé live → anotá correcciones/observaciones. Scope dinámico: fuera-de-scope →
  implementar-ahora (corto+necesario) o spawneamos historia(s) visibles. PISO HARD:
  funcionalidad nueva → core/happy-path construido sí o sí. Cada corrección entra a
  chris_verify.rounds. Cuando estés satisfecho → firmás chris_verify.signoff.

⏸  PAUSA en G. NO auto-handoff a /auditor hasta tu signoff + /pm-vitalia reconcile (R).
```

STOP la sesión `/dev-team` aquí (G). Tras `chris_verify.signoff` → `/pm-vitalia` reconcile (R) → `/auditor`.

### Caso autonomous_mode: true — corre a `/auditor` (G se salta)

Si `autonomous_mode: true` ratificado por Chris → **G se salta** (corre a done sin pausa-verify · NO requiere reconcile: el auditor procede por la rama autonomous):

```yaml
state: developed
phase: HANDOFF_TO_AUDITOR
next_action: "/auditor <brand>: {brand} toma story {id} para Conv 3 (AUTONOMOUS · G saltada)"
```

```
✅ Story {brand}/{story-id} all tickets pushed · validators GREEN.
Story state: developing → developed · AUTONOMOUS (G saltada por opt-in Chris).

→ AUTO-HANDOFF /auditor <brand>: {brand} story={story-id}
  (el auditor procede por la rama autonomous: reconciled=false PERO autonomous_mode=true.
   Lee T-{n}-result.md + Phase D gherkin + CHECKPOINTS.md C1-C5.)
```

STOP la sesión `/dev-team` aquí. (`defer_audit: true` → ver caso abajo.)

### Caso defer_audit:true — STOP + ping bootstrap

Si `defer_audit: true` ratificado:

```
✅ Story {brand}/{story-id} all tickets pushed.
Story state: developing → developed.
defer_audit: true (razón: "{defer_audit_reason}", ratified_by: {defer_audit_ratified_by})

⏸  AUDIT DEFERRED.

  /pm-vitalia bootstrap pingeará esta deuda en cada sesión futura hasta
  resolución. Cuando Chris quiera reanudar, dice "audita {story-id}" y
  /auditor toma el handoff con full context del defer.
```

STOP la sesión `/dev-team`.

### Anti-pattern bloqueado (caso vitalia 2026-05-18 origen)

```
❌ NUNCA: cerrar state=developed + pickup ticket de otra story DEL MISMO MÓDULO.
   Layer 2 enforcement (★ v2 module-scoped · ADR-009): si Step 0.4 detecta otra story
   abierta DEL MISMO módulo sin defer_audit, REFUSE pickup. Una story developed del módulo X
   debe llegar a state=done (auditor → merge → archive) antes de arrancar otra del módulo X.
   ✅ SÍ permitido: pickup de una story de OTRO módulo (bucket code:{otro} libre) en una
   sesión paralela del MISMO hub — eso es exactamente lo que ADR-009 habilita.
```

## Step 5.5 — R12 layer 1: emit process metric

> Origen: process-improvement A1 partial (2026-05-05). Foundation para
> medir ROI cross-PI. Token-level detail viene del transcript via
> `scripts/extract_baseline_metrics_from_transcripts.py`; aquí emitimos
> orchestrator-level metadata (verdict + commit_sha + ticket + phase) que
> NO está en transcript.

Antes de cerrar Step 5, append metric row a `docs/process/metrics/runs.jsonl`:

```bash
WS=$(git rev-parse --show-toplevel)
python3 ${WS}/scripts/emit_process_metric.py \
  --brand "{brand}" \
  --story "{story-id}" \
  --ticket "T-{n}" \
  --phase build \
  --agent-type "<builder-backend|builder-agentic|builder-frontend|qwen-opencode>" \
  --verdict "<tests-passing|tests-failing|pushed|blocked>" \
  --commit-sha "$(git log -1 --format=%h)" \
  --total-tokens "<from agent tool result if visible, else omit>" \
  --tool-use-count "<from agent tool result if visible, else omit>" \
  --duration-ms "<wall-clock ms agent ran, else omit>" \
  --iter <N> \
  --note "<1-line context if relevant>"
```

`runs.jsonl` is gitignored (rolling). Periodic aggregation: post-story close,
`/pm` runs analysis script comparing `runs.jsonl` to baseline.

If `python3 scripts/emit_process_metric.py` fails (script missing, etc.) →
log warning + continue. Metrics emission is best-effort, NEVER blocks the
pipeline.

## Cap reached (autonomous loop blocked)

Si dev itera ≥10x sin GREEN (cap from `04-validators.yaml` `iteration.max_iterations`):

```yaml
# {brand}/docs/product/stories/{story-id}/checkpoint.md
brand: {brand}     # ★ REQUIRED — multibrand scope
state: blocked     # NOT review — autonomous failed
phase: BUILD_T{n}_BLOCKED
last_artifact: T-{n}-impl-log.md
next_action: "Chris reviews iteration_log to decide: refine validators / refine guidelines / split ticket / restart"
```

Output:
```
Story {brand}/{id} ticket T-{n} BLOCKED — autonomous loop cap reached (10 iter).

Last error trace (verbatim):
---
{paste last validator failure}
---

iteration_log summary:
- Iter 1-3: implementation phase, RED on validator X
- Iter 4-6: refactor approach Y, still RED
- Iter 7-10: edge case Z not handled by guidelines

Story state: developing → blocked.

Próximo: Chris reviews {brand}/docs/product/stories/{story-id}/T-{n}-impl-log.md →
decide:
- Refine 04-validators.yaml (validator was wrong)
- Refine 05-guidelines.md (missing pattern guidance)
- Split T-{n} (too large)
- Restart with different approach
```

## Multi-ticket parallel

Si 2 tickets independientes (no `depends_on`) están `ready` simultáneamente:
- Podés spawnear builders en PARALELO (single message, multiple Agent calls / multiple opencode bash)
- IMPORTANTE: ambos no deben tocar mismos archivos (conflict)
- Si overlap detectado → secuencial

## ★ Delegation pattern (cementado 2026-05-27 — origen autonomous chain lisa-marca)

> **Caso origen:** durante el autonomous chain de `vitalia-fase2-lisa-marca` (12 tickets, ~6 hours of orchestration), el `/dev-team` orchestrator delegó tareas de finalize (commit + result file + ticket state update) a un Haiku `general-purpose` agent. Resultado:
> - El Haiku stageó archivos incorrectos (5 valeria-agenda test files de sesión paralela en lugar de los 8 lisa-marca files solicitados)
> - El Haiku claimó `done -> 8c51ff5a` con SHA real pero contenido WRONG
> - El orchestrator tuvo que hacer un recovery commit con los 12 archivos correctos
> - Cost: ~1 turn de inference + reputation damage

**Regla cardinal:** delega a `subagent_type` ESPECIALIZADO según el dominio del trabajo, NUNCA a `general-purpose` para tareas que requieren domain knowledge.

### Subagent_type matrix por tarea

| Tarea | subagent_type correcto | Por qué |
|---|---|---|
| Implementar BE ticket | `builder-backend` (workhorse/flagship) | DDD/FastAPI/SA patterns embedded en su system prompt |
| Implementar FE ticket | `builder-frontend` (workhorse/flagship) | FSD-Lite/React Query/RHF patterns embedded |
| Implementar AGENTIC ticket production_code:true | `builder-agentic` (flagship OBLIGATORIO) | LangGraph + prompt cache + voice + observability |
| Run quality gates + write gate-output.json | `gate-runner` (Haiku) | Specialized para ruff+pytest+playwright+JSON output |
| Build CONTEXT-BRIEF.md (Phase 0 pre-flight) | `context-builder` (Haiku) | Specialized compression spec+arch+rules → 5-8k tokens |
| Validate CONTEXT-BRIEF.md adversarially | `context-validator` (Haiku) | Specialized re-scan + spot-check + verdict |
| Audit ticket (BE) | `auditor-backend` (flagship) | 11 categorías DDD/tenant/migrations + 13 gates |
| Audit ticket (FE) | `auditor-frontend` (flagship) | 12 categorías FSD/Server-Client/forms + 8 gates |
| Audit ticket (AGENTIC) | `auditor-agentic` (flagship) | 14 categorías LangGraph/cache/observability |
| Open-ended research / catch-all | `general-purpose` (Sonnet/Haiku) | Cuando NO existe especialista; raro en /dev-team flow |

**Hard ban:** NO usar `general-purpose` para:
- Git workflow finalize (commit/push/result file write/06-tickets state update) — orchestrator hace Bash directo
- Build/implement code (siempre builder-* especializado)
- Run validators (siempre gate-runner)
- Audit (siempre auditor-{be,fe,agentic})

**Exception válida:** `general-purpose` para tareas que CRUZAN dominios sin specialist clear (e.g., "investiga si X pattern existe en docs/archivos cruzados"). En `/dev-team` flow esto es raro.

### Agent continuation pattern

Cuando un sub-agent stalls mid-work (context exhaustion, API Overload, tool budget reached):

1. **Check git tree first** — agent puede haber dejado partial progress como uncommitted changes. Inspect via `git status --short` + `git diff` para ver scope real.
2. **Preferir SendMessage** sobre spawn nuevo, si available — preserva el contexto del agent (el agent recuerda qué archivos tocó, qué errores hit). Requiere `agentId` del agent original (presente en su last-line result).
3. **Spawn nuevo agent (fallback)** cuando SendMessage no disponible — el prompt MUST citar:
   - Partial work in tree (paths específicos + estado)
   - Remaining work items (verbatim)
   - Original task spec (cita path al PRIORITY READ docs)
   - Workspace state at point of failure
4. **Document continuation** en `T-{n}-impl-log.md` sección "Continuation iter X" con: razón stall + commits hechos antes + remaining + new agent's verdict.

### API Overload handling

`anthropic.APIStatusError: Overloaded` es common en chains largos (cost spikes Anthropic infra). Cuando ocurre:

1. Verify partial work en tree (`git status`)
2. NO restart from scratch — preserve any commits/files agent produced
3. Spawn continuation agent con explicit "previous work in tree, finish remaining" prompt
4. Si overload persiste >2 retries → escalate Chris o pause autonomous chain
5. Document API Overload incidents en `T-{n}-impl-log.md` para tracking pattern

### Orchestrator-level direct work (vs delegation)

Orchestrator (Opus PM coordinator) hace DIRECTAMENTE via Bash/Edit/Write:
- Git commits + push con paths exactos (más control que Haiku stage por nombre)
- Read context files (spec/arch/rules) cuando deciding scope
- Update checkpoint.md state transitions (1-2 line edits)
- Write CHECKPOINTS.md story-level (cuando audit completo)
- Write 07-merge.md (Fase F MERGE artifact)

Orchestrator DELEGA via Agent tool:
- Implementación de tickets (subagent_type=builder-*)
- Quality gates execution (subagent_type=gate-runner)
- Audit categorías scoring (subagent_type=auditor-*)
- Context brief building (subagent_type=context-builder)

**Justificación:** Opus tokens son ~5x más caros que Sonnet/Haiku. PM coordinator usa Opus para reasoning/orchestration; trabajos mecánicos (validators, finalize, gates) van a Sonnet/Haiku especializados.

## Anti-patterns

- ❌ AGENTIC ticket production_code=true asignado a qwen/workhorse (HARD BAN — flagship only)
- ❌ **Delegar finalize (commit+push+result file) a `general-purpose` Haiku** — orchestrator hace Bash directo (caso origen lisa-marca 2026-05-27)
- ❌ Spawn nuevo agent cuando uno stalled — si tree tiene partial progress, continúa via SendMessage o continuation prompt explícito
- ❌ Restart from scratch tras API Overload — preserve partial work first
- ❌ Skip TDD (escribir código sin validators RED primero)
- ❌ `git add .` / `git add -A` / `git add -u` (git-safety)
- ❌ `git commit --no-verify`
- ❌ `git pull` antes commit (git-safety)
- ❌ Push falla non-fast-forward → NO `git pull`. STOP, escala.
- ❌ `git push origin development` — branch eliminado en reorg 2026-05-15. Triple-branch: wip/* | main | release/{brand}-vX.Y.Z.
- ❌ Marcar ticket pushed sin verify TODOS validators ticket-asociados → GREEN
- ❌ Self-fix más de cap_reached iter sin escalar bloqueo
- ❌ Dev tocando archivos out_of_scope (5-guidelines.md "Files in scope" hard)
- ❌ Dumpear código en chat (anti-teléfono — todo en archivos)
- ❌ Editar paths legacy `docs/archive/2026/legacy-pis/PI-N/...` o `docs/archive/2026/snapshot-pre-multibrand-pm-redesign/` (snapshot inmutable)
- ❌ Skip 04-validators.yaml — implementar sin validators es paradigma viejo
- ❌ Cerrar story como done sin pasar por `/auditor` Conv 3
- ❌ Hardcodear paths `/home/chris/AISALESHT/...` o `/home/chalreme/Proyectos/luana-platform/...` — usar `${WS}` resuelto via `git rev-parse --show-toplevel`
- ❌ Inferir el brand del contexto si Chris no lo dijo — PREGUNTAR primero

## Anti cross-brand pollution

- ❌ NUNCA editar paths fuera de `vitalia/**` (+ story docs). STOP + escalate `/pm-vitalia`.
- ❌ NUNCA editar `core/luana-core-*/src/` directamente. Requiere lift via `/pm-vitalia` (flujo engine).
- ❌ NUNCA escribir/leer archivos en root `docs/product/stories/` — solo `<brand>: platform` (cross-brand) outcomes van ahí, y eso requiere autorización explícita `/pm-vitalia`.
- ❌ Spawn sub-agent sin propagar `<brand>: {brand}` en el prompt — sub-agent puede editar fuera del scope brand.

## Output format

Cada update al user/PM:
- 1 frase status ticket
- Quality gates resumen (validators ID + ✅/❌)
- Próximo paso
- NO dump de diff o tests output (cita paths)

## Output protocol · chris-input.md append

Al cierre de cada turn, MUST appendear una entry a la sección 💬 Conversación del `chris-input.md` de la story activa, con verdict **✓ APLICADO · ⚠️ DUDA · ❌ REFUTADO · 💡 PROPONE**. Nunca terminar turn sin appendear (aunque sea `✓ APLICADO · sin cambios sustantivos`). Path: state ∈ {idea..reviewing} → `{brand}/docs/product/stories/{id}/chris-input.md`; `done` → `{brand}/docs/archive/{year}/stories/{id}/chris-input.md`.

**Schema verbatim (formato del entry + labels + anti-patterns): `docs/process/chris-input-protocol.md § Sección 5` (SSoT — no se duplica acá).**

## Referencias

- `docs/process/pm-redesign-2026-05.md` — paradigma 3 conversaciones + autonomous build
- `.claude/rules/tdd-mandatory.md` — TDD obligatorio + R31 default flag flips
- `.claude/rules/anti-duplication.md` — inventario shared abstractions
- `docs/architecture/luana-platform/PARADIGM.md` + `.claude/rules/paradigm-arquitectura.md` — ★ 3 planos: el trabajador invoca la acción única (Plano 2), no reimplementa; un solo engine; no cruzar de plano sin escalar
- `.claude/rules/hotfix-repro-mandatory.md` — R26 hot-fix gate
- `.claude/rules/git-safety.md` — prohibiciones git + stage por pathspec
- `.claude/agents/builder-{backend,frontend,agentic}.md` — sub-builders specs
- `.claude/agents/gate-runner.md` — gate-output.json producer (Haiku)
- `.claude/agents/context-builder.md` — CONTEXT-BRIEF.md producer (Haiku)

## DoD endurecida — obligaciones del builder (Critical Rule #37)

Antes de cerrar `developing → developed`:
- **★ Correr los `technical_gates` declarados (HB-97 · no saltar silenciosamente):** baseline + cada opt-in que `04-validators` marque `enabled: true` (mutation diff-scoped vía `scripts/mutation_gate.py`, schemathesis). El `T-{n}-result.md` DEBE incluir la **salida** de cada gate declarado (score de mutación / resumen schemathesis), no solo el conteo unit. Si `mutation.enabled: true` o `schemathesis.enabled: true` y NO hay evidencia de corrida en el result-file → la story **NO cierra `developed`** (un "GREEN" por conteo unit con un gate HARD declarado-y-no-corrido = falso-verde, caso mateo). Tool ausente (mutmut/Stryker/schemathesis) → degrada advisory + lo dice **explícito** en el result-file (no silencio).
- **Superficies FE**: usar `{brand}/frontend/e2e/fixtures/base.ts` (gate anti-burbuja: pageerror=burbuja Next, hidratación, console.error con allowlist tight, `/api/` 4xx-5xx, diálogo de error Next) en los specs nuevos; correr `scripts/verify-no-backend-errors.sh {brand} "$SINCE"` tras ejercer writes.
- **Live-verify con Chrome DevTools MCP**: ejercer la acción real + LEER el panel **Console** (0 errores rojos) + Network + logs + confirmar efecto.
- Cubrir **cada regla de negocio** (gherkin-matrix sin MISSING).
- **Modificación**: respetar `regression_guard` (tests viejos verdes sin tocarse); snapshot/characterization se actualiza revisando el diff (nunca `vitest -u`/`--update-snapshots` mecánico).
- Producir `demo-script.md` (template `docs/specs/templates/demo-script-template.md`) para stories `demo_required: true`.
- Registrar `dod_evidence` en `checkpoint.md`. NO cerrar por "tests verdes" mockeados.
- ★ **HARD GATE**: para stories `verification_nature ∈ {funcional, ambas}` o `demo_required: true`, el **Step 4.6** es BLOQUEANTE — la transición `developing → developed` (y el auto-handoff a `/auditor`) se REFUSE hasta que `dod_live_verified: true` + `dod_evidence` (write real ejercido) + `demo-script.md` estén en el checkpoint. No es una obligación soft: es el mismo nivel imperativo que el Phase D local de gherkin. Ref: `.claude/rules/definition-of-done-live-verify.md` (Critical Rule #37).
