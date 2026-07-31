# Auditor Downstream Regression Scope (Multibrand)

**Origen:** PI-12 S1 Story A T-1 (2026-05-04). Auditor `auditor-backend` aprobó cost_recorder canonicalization PASS — pero NO corrió tests downstream que mockean callback_handler en `modules/{copilot,sales_agent}/observability/`. Bug `litellm.get_llm_provider("kimi/kimi-k2.6")` raises BadRequestError llegó a S1 (T-1-bis micro-ticket nuevo). Severidad: **CRÍTICA**.

**Single-brand update 2026-07-31:** shared abstractions viven en `core/luana-core-*/src/luana_core_*/` (27 packages). Tests viven en `core/luana-core-*/tests/` (engine) Y en `vitalia/backend/tests/` (brand consumer). Workspace root: `$(git rev-parse --show-toplevel)` (variable `${WS}` en comandos).

**Split 2026-05-16:** tabla SSoT (secciones A-I, ~30k chars) movida a `docs/rules-detail/auditor-downstream-targets.md` para mantener rule principal <40k chars context budget. Auditores leen el reference doc on-demand (Read tool) durante Step `downstream_regression_scope`.

## Regla cardinal

Cuando auditor reviewing PR toca código `core/luana-core-*/` (engine), brand extension (`{brand}/backend/src/modules/{brand}/...`), o módulo con consumers cross-brand conocidos, MUST:

1. **Engine edit detection** — verificar promotion proposal (si toca `core/luana-core-*/src/`)
2. **Cross-brand mirror scan** — detectar duplicación (si toca `{brand}/backend/src/modules/{brand}/`)
3. **Downstream test run** — ejecutar tests cross-consumer per tabla SSoT (ver reference doc)

**Mecánica:** auditor lee diff `git diff --name-only HEAD~N..HEAD`. Para cada path tocado:
- Infiere `BRAND` (primera componente path si match `^[a-z]+/(backend|frontend)/`, sino "engine")
- Read `docs/rules-detail/auditor-downstream-targets.md` → lookup row por surface
- Aggregate downstream_test_targets (engine + per-brand consumers)
- Spawn gate-runner adicional con scope si no cubierto en gate-output.json original

## Tabla SSoT — surface → downstream test paths

> **SSoT vive en** `docs/rules-detail/auditor-downstream-targets.md` (split 2026-05-16).
>
> 9 secciones: **A** observability · **B** extraction+llm · **C** events+idempotency+billing+compliance · **D** extension-sdk+platform · **E** copilot+sales-agent · **F** agentic evals (simulator+grader+goldens) · **G** brand business modules (analytics/offer/landing) · **H** frontend per-brand · **I** brand overlay rules + extensions registry.
>
> **Convención `${WS}` + `${BRANDS} = {vitalia}`.**
>
> Maintainer rules + ratchet (shrink-only) documentados al final del reference doc.

## Workflow auditor (Step `downstream_regression_scope`)

```
# Pseudocode auditor agent inserts post consume_gate_output, pre audit_categories.
# WS = $(git rev-parse --show-toplevel)
# BRANDS = vitalia

1. List files modified in diff: git diff HEAD~N..HEAD --name-only

2. For each path → infer BRAND + classify scope:
   - Match `^core/luana-core-([^/]+)/src/` → scope=ENGINE, pkg=$1 → Step 2a
   - Match `^([a-z]+)/(backend|frontend)/` AND $1 in BRANDS → scope=BRAND, brand=$1 → Step 2b
   - Match `^docs/specs/(personas|rubrics)/` → scope=PLATFORM-CROSS-BRAND
   - Match `^scripts/` → scope=PLATFORM-SCRIPT
   - Match `^[a-z]+/\.claude/rules/` → scope=BRAND-OVERLAY → Step 2c (§ Brand overlay scope)
   - Otherwise → scope=UNCLASSIFIED, escalate Chris (likely LEGACY path needing migration)

2a. ENGINE scope (Step `engine_edit_detection`) — MANDATORY:
    - Verify que el cambio de engine está DECLARADO en el scope de la story/ticket (ratificado
      vía flujo engine `/pm-vitalia`) y que los arch tests del paquete corren GREEN.
    - Engine edit "de contrabando" (no declarado en 03-arch/06-tickets) → FAIL: "engine edit
      no declarado. Escalar `/pm-vitalia` ANTES merge."
    - Read `docs/rules-detail/auditor-downstream-targets.md` → downstream_test_targets includes engine tests + vitalia consumer

2b. BRAND scope (Step `engine_mirror_scan`) — MANDATORY for brand extensions
    bajo `vitalia/backend/src/modules/vitalia/{copilot,sales_agent}/`:

    BASENAME=$(basename <path>)
    MATCHES=$(find ${WS}/core/luana-core-*/src -name "$BASENAME" 2>/dev/null)
    if [ -n "$MATCHES" ]; then
      diff <(git show HEAD:<path>) "$MATCHES" | head -50
    fi

    Si MIRROR detected → FAIL AUTOMÁTICO con verdict:
    "engine mirror detected: vitalia/... <-> core/luana-core-*/...
     Pattern debe consumirse desde `core/luana-core-*/` vía import, NUNCA mirror local
     (per anti-duplication.md § lift shared rule). Escalar `/pm-vitalia` (flujo engine)."

3. Aggregate downstream_test_targets = unión sets per matched path.

4. Verify gate-output.json scope cubre downstream_test_targets:
   - gate-runner.command was full suite (`make test-all`)? → cubierto
   - gate-runner.command was scoped (e.g., `core/luana-core-X/tests/`)? → puede no cubrir brand consumers

5. Si NO cubre → SPAWN gate-runner adicional con scope=downstream_test_targets:

   Backend ENGINE scope:
     command: cd ${WS} && .venv/bin/pytest <engine + brand test paths> -v --tb=short
     iter: <N>-downstream-engine

   Backend BRAND scope (per-brand):
     command: cd ${WS} && .venv/bin/pytest <BRAND>/backend/tests/<scoped paths> -v --tb=short
     iter: <N>-downstream-be-<BRAND>

   Frontend BRAND scope (R3 parity, per-brand):
     command: cd ${WS}/<BRAND>/frontend && npx vitest run <paths> --reporter=default
     iter: <N>-downstream-fe-<BRAND>

   E2E smoke scope (when downstream targets include `{brand}/frontend/e2e/`):
     command: cd ${WS}/<BRAND>/frontend && E2E_BASE_URL=http://localhost:300X npx playwright test --project=smoke <specs>
     iter: <N>-downstream-e2e-<BRAND>
     (Port: vitalia=3002)

6. Read new gate-output.json (gate-runner renames previous → gate-output.iter-N.json automatic).

7. Si downstream tests FAIL → escalate REVIEW.md FAIL — Cat 10 (Tests/TDD) BE/FE,
   o Cat 1 (FSD-Lite cross-feature import) si FE, o Cat 12 (anti-duplication) si cross-brand mirror —
   con cita exacta tests fallaron y mapping a surface + brand modificada.

8. Si downstream tests PASS Y engine_edit_detection PASS Y cross_brand_mirror_scan PASS
   → continuar audit_categories.
```

## Cross-brand mirror detection

**Cuándo aplica:** PR toca `{brand_A}/backend/src/modules/{brand_A}/X/Y.py` o `{brand_A}/frontend/src/lib/...` (componentes lib candidatos a shared abstraction).

**Algoritmo verbatim:**

```bash
WS=$(git rev-parse --show-toplevel)
BRAND_A=<brand inferido en Step 2>
TARGET_PATH=<path tocado>
BASENAME=$(basename "$TARGET_PATH")

find ${WS}/core/luana-core-*/src -name "$BASENAME" 2>/dev/null
find ${WS}/vitalia/backend/src -name "$BASENAME" 2>/dev/null | grep -v "$TARGET_PATH"
find ${WS}/vitalia/frontend/src -name "$BASENAME" 2>/dev/null | grep -v "$TARGET_PATH"
```

**Resultado match → FAIL AUTOMÁTICO:**
- Cita ambos paths exactos (vitalia + engine, o los dos módulos de vitalia)
- Verdict: "mirror detected. Pattern compartible debe vivir en `core/luana-core-*/` y consumirse vía import, NUNCA mirror local (per anti-duplication.md § lift shared rule). Escalar `/pm-vitalia` (flujo engine). PR queda BLOCKED hasta resolver."

**Falso positivo guard:** si match es solo `__init__.py` vacío o `conftest.py` de test scaffold local → no es mirror. Diff conceptual >50% del archivo es el threshold para flag MIRROR.

## Engine edit detection

**Cuándo aplica:** PR toca `core/luana-core-*/src/luana_core_*/` (cualquier file runtime engine, NO tests).

**Verificación obligatoria:**

```bash
PKG=$(echo "$TARGET_PATH" | sed -nE 's#^core/luana-core-([^/]+)/.*#\1#p')
# 1. El scope de la story/ticket declara el cambio de engine (03-arch / 06-tickets, ratificado /pm-vitalia)
# 2. Arch tests del paquete GREEN:
cd ${WS}/core/luana-core-${PKG} && ${WS}/.venv/bin/pytest tests/architecture/ -x -q
```

**Engine edit no declarado → FAIL:**
- Verdict: "engine edit no declarado en el scope de la story. Engine `core/luana-core-${PKG}/` es SSoT compartido. Cambios runtime siguen el flujo engine `/pm-vitalia` (declarados en el ready package + arch tests GREEN) ANTES merge."

**Downstream regression scope:** engine edit → reference doc row engine + vitalia consumer tests (este es el costo del SSoT engine).

**Exception:** hotfix engine bug crítico (per `.claude/rules/hotfix-repro-mandatory.md`) con `repro_verified: true` + Chris ratificación explícita en checkpoint.md → la declaración formal puede ir post-fix (mismo sprint).

## Brand overlay scope

**Cuándo aplica:** PR toca rules brand-specific en `.claude/rules/` (ej. `hipaa-lite.md`, `shell-feature-architecture-mandatory.md` — consolidadas a root 2026-07-31).

**Verificación obligatoria:**

1. **No-contradicción con root:** read root `.claude/rules/<same-basename>.md` (si existe). Brand overlay debe EXTEND (override de defaults específicos brand) NUNCA SOBREESCRIBIR completamente regla raíz. Si overlay anula una hard rule raíz → FAIL.
2. **Referencias absolutas consistentes:** todos los paths citados deben prefix con `vitalia/` (no paths sueltos que parezcan engine pero apunten brand-local).
3. **Generic pattern detection:** si overlay describe un patrón repo-wide (no vitalia-específico) → flag CHANGES_REQUESTED con verdict: "patrón overlay genérico. Propose lift a `.claude/rules/` raíz (no duplicación de reglas en el overlay)."

**Default verdict:** overlay self-contained brand-specific con override claro → APPROVED.

## Pre-commit freshness gate (origen C1 R21 2026-05-05 — multibrand 2026-05-15)

Hook `scripts/git-hooks/pre-commit` Section 4 detecta automáticamente nuevos archivos (status `A` o `R`) en cualquiera de estos paths multibrand:

| Regex path | Scope | Owner |
|---|---|---|
| `^core/luana-core-[^/]+/src/luana_core_[^/]+/.+\.py$` | Engine canonical (post reorg) | Promotion proposal + reference doc row |
| `^[a-z]+/backend/src/shared/.+\.py$` | Per-brand shared (rare; lift candidato) | Reference doc row + cross-brand mirror check |
| `^backend/src/shared/.+\.py$` | LEGACY pre-multibrand — hook bloquea + dirige a `core/luana-core-*/` | Block & redirect |

Condición trigger: path no listado en reference doc (substring match exact path OR parent dir) AND sin magic comment `# downstream-regression-na: <reason>` en primeras 20 líneas.

→ Hook BLOQUEA commit con hint accionable. Devs eligen entre:
- (A) agregar row a reference doc (sección apropiada A-I) con `downstream_test_targets`
- (B) marcar `# downstream-regression-na: <reason>` si surface es self-contained (no cross-consumers — auditor escruta razón post-merge)
- (C) si LEGACY path `backend/src/shared/...` → migrar a `core/luana-core-*/src/...` ANTES commit (post reorg legacy paths están deprecated)

Tests cubren escenarios en `core/luana-core-platform/tests/scripts/test_pre_commit_hook.py` (post reorg path).

Ratchet: reference doc shrink-only excepto cuando agregás surface nueva. Renombre de path → update row mismo commit. Lift de brand → engine = remove brand row + add engine row + add ∀ brand consumer rows downstream.

## Anti-patterns prohibidos

- ❌ Auditor APPROVED PR `core/luana-core-observability/` modify sin run downstream tests `core/luana-core-copilot/tests/observability/` + `core/luana-core-sales-agent/tests/observability/` + `{brand}/backend/tests/modules/{brand}/{copilot,sales_agent}/observability/` ∀ brand
- ❌ Auditor APPROVED PR `core/luana-core-llm/` modify sin run consumers cross-engine + cross-brand (todos modules llaman LLM)
- ❌ Auditor APPROVED PR enum `core/luana-core-platform/src/luana_core_platform/enums/` modify sin grep importers cross engine+brand + run sus tests
- ❌ Auditor APPROVED PR `core/luana-core-platform/src/luana_core_platform/config.py` flag flip sin Step 1 grep + run AMBOS valores per anti-default-flip-audit.md
- ❌ Auditor APPROVED PR `core/luana-core-*/src/` modify **sin verificar promotion proposal accepted/migrated** (§ Engine edit detection)
- ❌ Auditor APPROVED PR `{brand_A}/backend/src/modules/{brand_A}/...` con código que **mirrorea `{brand_B}/backend/src/modules/{brand_B}/...`** (§ Cross-brand mirror detection) — debe lift to `core/luana-core-*/`
- ❌ Auditor APPROVED PR `{brand}/backend/src/modules/{brand}/{copilot,sales_agent}/` (brand extension) **sin correr cross-brand scan** ∀ otro brand ∈ ${BRANDS}
- ❌ Skip engine edit detection cuando PR toca `core/luana-core-*/` "porque parece trivial" — todo cambio engine es cross-brand por definición
- ❌ Skip reference doc lookup porque "module change parece self-contained" — si toca engine o brand extension shared, downstream puede ser invisible
- ❌ Auditor APPROVED PR `{brand}/.claude/rules/X.md` que contradice regla raíz `.claude/rules/X.md` (overlay debe extend, no sobreescribir)
- ❌ Auditor APPROVED PR `{brand}/.claude/rules/X.md` con patrón cross-brand sin proponer lift to root (§ Brand overlay scope)

## Enforcement layers

| Layer | Mecanismo | Owner |
|---|---|---|
| 1 Auditor agent | Step `downstream_regression_scope` MANDATORY post `consume_gate_output` | `auditor-{backend,agentic}` |
| 2 /auditor SKILL | Step 2 prompt sub-auditor referencia este file + reference doc | `/auditor` skill |
| 3 Reviews | T-{n}-review.md sección "Downstream regression" obligatoria con tests targets + gate-output result | sub-auditor |
| 4 Self-audit | Si CASO ORIGEN D4 reproduce — auditor verdict FAIL automático | sub-auditor |

## Penalizaciones

- Auditor missing downstream regression cuando surface lo requiere → process-learnings.md case study + re-audit
- Cambio shared/ sin update reference doc → process-learnings.md case study (catch en commit hook futuro)

## Ejemplo CORRECTO (auditor caso D4 reproducido — multibrand)

```
git diff HEAD~1..HEAD --name-only
→ core/luana-core-observability/src/luana_core_observability/cost/cost_recorder.py

Step 2: scope=ENGINE, pkg=observability
Step 2a (engine_edit_detection):
  ls docs/promotion-protocol/proposals/*observability*.md
  → 2026-05-10-observability-cost-canonical.md (state: accepted) ✓ PASS

Read reference doc § A (luana-core-observability):
  cost_recorder.py → cost recorder row →
    core/luana-core-copilot/tests/observability/test_callback_handler_usage_fallbacks.py
    core/luana-core-sales-agent/tests/observability/test_callback_handler.py
    vitalia/backend/tests/modules/vitalia/{copilot,sales_agent}/observability/

Spawn gate-runner downstream (engine + vitalia).

Resultado engine: 2 fail con `cost_usd > 0` AssertionError → bug `kimi/kimi-k2.6 → BadRequestError`.

Verdict: REVIEW.md FAIL Cat 10 (Tests/TDD) — "T-1 cost_recorder canonicalization
introduces regression downstream: litellm.get_llm_provider() doesn't recognize
'kimi' as provider (custom yaml alias). Add fallback in
`core/luana-core-observability/src/luana_core_observability/cost/cost_recorder.py`:
if get_llm_provider() raises, set provider = model.split('/')[0].lower() if '/' in
model else 'unknown'. Re-run downstream tests engine + vitalia."
```

## Ejemplo CORRECTO (engine mirror detection)

```
git diff HEAD~1..HEAD --name-only
→ vitalia/backend/src/modules/vitalia/sales_agent/tools/scheduler_tool.py

Step 2: scope=BRAND
Step 2b (engine_mirror_scan):
  BASENAME=scheduler_tool.py
  find ${WS}/core/luana-core-*/src -name "$BASENAME"
  → core/luana-core-scheduling/src/luana_core_scheduling/tools/scheduler_tool.py EXISTS
  → diff conceptual: 80% código compartido (scheduling logic) + 20% brand-specific (booking policy)

Verdict: FAIL AUTOMÁTICO — "engine mirror detected:
  vitalia/backend/src/modules/vitalia/sales_agent/tools/scheduler_tool.py
  <-> core/luana-core-scheduling/src/.../scheduler_tool.py
  Pattern compartido debe consumirse desde el engine vía import, con
  BookingPolicyDef de la marca via EP-X. Escalar /pm-vitalia (flujo engine).
  PR BLOCKED hasta resolver."
```

## Referencia cruzada

- `docs/rules-detail/auditor-downstream-targets.md` — **tabla SSoT secciones A-I** (read on-demand)
- `.claude/rules/anti-duplication.md` — inventario shared abstractions engine (§ lift shared rule — base del cross-brand mirror detection)
- `.claude/rules/anti-default-flip-audit.md` — Step 1 grep tests path viejo (ortogonal pero análogo: detect ripple)
- `docs/promotion-protocol/README.md` — workflow brand→core lift gate (consumido por § Engine edit detection)
- `docs/portfolio/PORTFOLIO.md` — vista master 11 universos (referencia ${BRANDS} catalog)
- `docs/architecture/luana-platform/ADR-001-luana-platform.md` — rationale topología engine + brand
- `.claude/agents/auditor-backend.md` — Step `downstream_regression_scope` (integrado 2026-05-05, multibrand-aware 2026-05-15)
- `.claude/agents/auditor-agentic.md` — Step idem (integrado 2026-05-05)
- `.claude/agents/auditor-frontend.md` — Step idem FE-side (integrado 2026-05-05, B1 parity)
- `docs/process/process-improvement-handoff-2026-05-05.md` — R3 (D4 origen)
- `docs/process/learnings.md` 2026-05-05 entry — closure ciclo R1-R9 + B1 FE parity
- `docs/process/pm-redesign-2026-05.md` — paradigm v4 + filosofía pointer-first cross-brand
