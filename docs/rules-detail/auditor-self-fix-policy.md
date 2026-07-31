# Auditor Self-Fix Policy (paradigm v4.1 → v4.2)
<!-- voseo-allowed: glosario/doctrina reference verbatim (no user-facing) -->

> **★ SUPERSEDED por v4.2 (cement 2026-05-28).** El SSoT cardinal vigente es `.claude/rules/auditor-self-fix-policy.md` v4.2 (3 carriles por NATURALEZA DE LA VERIFICACIÓN, no por tamaño). Cambios clave: (1) eliminado el cap "≤2 files/≤10 líneas" — el criterio de self-fix ahora es "¿lo verifica un test/gate EXISTENTE?"; (2) Carril A lo ejecuta el **sub-auditor mismo** (auditor-{be,fe,agentic} con tool `Edit`), sin re-spawn full; (3) caps `self_fix_iter: 5` + `audit_iterations: 4`; (4) AGENTIC Carril A solo mecánico. La whitelist de 17 categorías de abajo sigue siendo un subconjunto VÁLIDO de Carril A (todas no requieren test nuevo). El workflow Caso B/C/D de abajo aplica con esos números actualizados. Análisis: `docs/process/audits/2026-05-28-agentic-machinery-audit.md` § 1.

**Origen:** Conversación 2026-05-19 ratificada por Chris. Amplificación autonomy post-refinamiento del paradigm v4 (10 estados macro + story-closure-gate). Decisión clave: cuando auditor encuentra CHANGES_REQUESTED, ¿auditor lo arregla (Opus single-mind) o spawnea dev-team autónomo? **Híbrido por NATURALEZA DEL FIX, no tamaño.**

**Cement-date:** 2026-05-19.

**SSoT consumido por:** `.claude/skills/auditor/SKILL.md` Step 3 Caso B + Caso C.

## Regla cardinal

Auditor decision tree ante hallazgo en review:

```
¿El fix requiere ESCRIBIR un nuevo test (TDD RED→GREEN)?
├─ SÍ  → SPAWN dev-team autónomo. Auditor NUNCA escribe tests.
└─ NO  → ¿El fix toca ≥3 archivos O cambia lógica de negocio?
        ├─ SÍ  → SPAWN dev-team autónomo.
        └─ NO  → ¿Está en la WHITELIST § self-fix permitido?
                ├─ SÍ  → SELF-FIX (cap 4 iter) [v4.1 — v4.2: 5/4].
                └─ NO  → ESCALATE Chris (o /pm-vitalia si engine).
```

Cap absoluto **3 audit_iterations** [v4.1 — v4.2: 5/4] (no 2, ampliado para forward-motion autonomy). Después → ESCALATE.

## Whitelist verbatim — self-fix permitido (cap 4 iter) [v4.1 — v4.2: 5/4]

Auditor PUEDE editar directo SOLO estos tipos de fix. Lista exhaustiva:

| # | Categoría | Ejemplo concreto | Files típicos |
|---|---|---|---|
| 1 | Lint (ruff/eslint) | `ruff check --fix` auto-fixable | cualquier `.py` `.ts` `.tsx` |
| 2 | Format (ruff format / prettier) | `ruff format` reformat | idem |
| 3 | Import ordering | reordenar imports per isort/eslint-plugin-import | idem |
| 4 | Typo en string user-facing | `"Aún no tienes ofertas"` (vs typo `"Aun no tenes"`) | components, microcopy |
| 5 | Comentario decorativo eliminar | `# TODO: noqa-style left behind` | cualquier file |
| 6 | Type annotation trivial faltante | `def foo(x):` → `def foo(x: str)` (cuando uso es claro 1-líneas) | typed code |
| 7 | Off-by-one en bound check | `range(1, n)` → `range(0, n)` cuando el bug es obvio del diff | algorithms simples |
| 8 | Signo invertido en condición | `if x > 0:` → `if x >= 0:` (cuando spec/test dice el límite es inclusivo) | conditions |
| 9 | Default value incorrecto | `def f(x=None)` → `def f(x="default")` (cuando spec lo cita) | signatures |
| 10 | Log message corrección | `logger.info("user created")` → `logger.info("user updated")` (cuando contexto es claro) | logging calls |
| 11 | Magic comment add | `# voseo-allowed: glosario reference` cuando hook bloquea | rules MD, fixtures |
| 12 | Docstring trivial faltante | docstring 1-línea en función pública (auditor escribe lo obvio del code) | public APIs |
| 13 | Spanish neutro fix verbatim | `vos` → `tú`, `tenés` → `tienes` (per glosario `.claude/rules/spanish-text.md`) | UI strings |
| 14 | Currency hardcoded → tenant_locale | `'USD'` → `tenant.currency` cuando 1-line fix obvio | DTOs, formatters |
| 15 | Missing `response_model=` en endpoint | agregar `response_model=ExistingDTO` cuando el DTO ya existe | api/routes.py |
| 16 | Import inutilizado eliminar | drop `from x import unused` flagged por linter | cualquier |
| 17 | Variable renombrada sin propagar todos los usos | rename consistency 2-3 sites (no refactor estructural) | scoped |

**HARD límite:** edits whitelisted en MÁXIMO 2 archivos por iter, MÁXIMO 10 líneas modificadas por iter. Si excede → NO es self-fix, ES refactor → spawn dev-team.

## NUNCA self-fix — lista exhaustiva

Auditor REFUSE editar (spawn dev-team autónomo en su lugar):

| # | Categoría | Razón |
|---|---|---|
| 1 | **Escribir nuevo test** (cualquier extensión `.test.*`, `.spec.*`, `test_*.py`) | TDD vive en dev-team. Auditor escribir tests rompe disciplina RED→GREEN. |
| 2 | Cambiar/agregar branch lógico (`if/else/match/elif`) | Lógica de negocio = dev-team scope |
| 3 | Refactor 2+ archivos | dev-team tiene validator loop |
| 4 | Agregar nuevo método/función | scope expansion |
| 5 | Modificar SQL query / SQLAlchemy `select(...)` | data model = dev-team |
| 6 | Modificar migration (`alembic/versions/*.py`) | irreversible side effect |
| 7 | Modificar Pydantic DTO field (add/remove) | contract change |
| 8 | Modificar prompt slot (sales_agent/copilot) | agentic territory, R23 tier flagship required dev-team |
| 9 | Modificar React Query keys o invalidation | data flow = FE dev-team |
| 10 | Modificar Zod schema fields | contract |
| 11 | Modificar wireframe / mockup / spec gherkin scenario | escala /po-ux o /po (no auditor) |
| 12 | Cualquier security fix (auth, PII sanitize, tenant_id filter) | escalate Chris |
| 13 | Architecture refactor (boundary cross-module, DDD layer) | escalate Chris |
| 14 | Touch `core/luana-core-*/src/` | flujo engine /pm-vitalia |
| 15 | Touch paths fuera de `vitalia/**` | out-of-scope → Chris |
| 16 | Touch `.claude/{skills,rules}/` o `docs/{process,architecture,specs}/` | meta-paradigm change, escalate |

## Workflow auditor — decisión + acción

### Step 3 Caso B — CHANGES_REQUESTED estructural (spawn dev-team autónomo)

Cuando finding es de la lista NUNCA self-fix, auditor:

1. Document finding en `T-{n}-review.md § Findings` (path + line + razón + fix sugerido)
2. Update `06-tickets.yaml` ticket → `state: changes-requested`, increment `audit_iterations`
3. Si `audit_iterations <= 3` → SPAWN dev-team autónomo con findings:

```
Agent({
  description: "Auto-fix T-{n} brand={brand} (auditor handoff)",
  subagent_type: "builder-{backend|frontend|agentic}",
  model: "<workhorse | flagship si AGENTIC production_code:true (R23) — resolver tier en project.config.yaml::models>",
  prompt: "<brand>: {brand}
           <pr_folder>: {brand}/docs/product/stories/{story-id}/
           ticket: T-{n}
           mode: AUDITOR_AUTO_FIX_LOOP
           findings_source: {brand}/docs/product/stories/{story-id}/T-{n}-review.md § Findings
           
           AUTONOMOUS LOOP:
           1. Read T-{n}-review.md § Findings (cada finding cita path + line + fix sugerido)
           2. Apply targeted fix EACH finding (no scope creep — NO touches fuera de findings)
           3. Re-run validators de acceptance.validator_ids
           4. If validator GREEN → commit + push wip/{slug} + done -> T-{n}-result.md (updated)
           5. If validator RED → iterate fix → re-run (cap 5 iter)
           
           GUARDRAILS:
           - Only edit files cited en T-{n}-review.md § Findings
           - TESTS (condicional según motivo del spawn):
               · Si el finding ES "falta test / cobertura insuficiente" (NUNCA-self-fix #1) →
                 ESCRIBÍ el test nuevo RED→GREEN (ése es EL motivo del spawn — dev-team es
                 dueño del TDD).
               · Para cualquier otro finding estructural ya cubierto por tests existentes →
                 NO agregues tests nuevos (auditor verifica el fix vs scenarios existentes).
           - NO refactor outside findings scope
           - Spanish neutro respected
           - Push branch ACTUAL (wip/{brand}-{story-padre-id})
           
           Last line: done -> T-{n}-result.md (con sección 'Auto-fix loop iter N')
                      O blocked -> T-{n}-impl-log.md (cap_reached, escalate)"
})
```

4. **WAIT result** (NO arrancar nueva story, NO esperar Chris). Cuando dev-team termina:
5. Auditor RE-AUDIT autónomo: re-run gate-runner + re-spawn sub-auditor + re-write `T-{n}-review.md` (append iter section)
6. Si verdict nuevo = APPROVED → continuar Step 4 CHECKPOINTS.md
7. Si verdict nuevo = CHANGES_REQUESTED Y `audit_iterations >= 3` → ESCALATE Chris (cap absoluto)

### Step 3 Caso C — Self-fix whitelisted (cap 4 iter) [v4.1 — v4.2: 5/4]

Cuando finding es de la lista whitelist:

1. Document finding en `T-{n}-review.md § Self-fix log` (path + line + categoría whitelist # + diff aplicado)
2. Apply edit (max 2 files, max 10 lines per iter)
3. Re-run validators asociados
4. If GREEN → APPROVED, mark `state: audit-passed`
5. If RED → escala Caso B (spawn dev-team)
6. Cap absoluto 4 self-fix iter por ticket → después spawn dev-team

### Step 3 Caso D — ESCALATED (Chris/PM)

Cuando finding es:
- Security violation (auth/PII/tenant_id leak)
- Architecture drift fundamental (DDD broken, anti-duplication mirror cross-brand)
- Cross-brand pollution
- Engine surface edit sin promotion proposal
- Spec ambiguity (auditor NO puede decidir intent sin Chris)

→ STOP audit autónomo. `state: blocked`. Output verbatim:

```
ESCALATED — auditor cannot self-fix ni spawn dev-team.

Razón: <categoría>
Detalle: <T-{n}-review.md § Findings>
Próximo: Chris ratifica acción (refine spec / lift core / discard scope / etc.)
```

## Documentación obligatoria en T-{n}-review.md

Cada audit iter MUST documentar:

```markdown
## Audit iteration N (2026-MM-DDTHH:MM:SSZ)

### Verdict
APPROVED | CHANGES_REQUESTED (spawn dev-team) | CHANGES_REQUESTED (self-fix) | ESCALATED

### Findings (N)
1. {brand}/backend/.../foo.py:42 — missing response_model. Suggested fix: add `response_model=FooResponse`. Category: self-fix whitelist #15.
2. {brand}/frontend/.../bar.tsx:100-120 — branch logic missing for empty state. Suggested fix: agregar handler `if (data.length === 0) ...`. Category: NEVER self-fix #2 (branch lógico).

### Action taken
- Finding #1 → SELF-FIX applied (1 line, foo.py). Validator re-run → GREEN.
- Finding #2 → SPAWN dev-team `builder-frontend` model=sonnet. Awaiting result.

### Re-audit cycle (cuando dev-team retorna)
- Re-spawn sub-auditor. Re-run gate-runner. Append "Audit iteration N+1" section.
```

## Anti-patterns

- ❌ Auditor escribe un test (cualquier `.test.*` o `test_*.py`) — viola identidad TDD del dev-team
- ❌ Auditor "rápido fix" que toca 4 archivos porque "es trivial" — refactor camuflado
- ❌ Auditor edita lógica de negocio porque "claro qué quería el dev" — usurpa scope
- ❌ Auditor llena `audit_iterations` haciendo self-fix sin progreso real
- ❌ Auditor self-fix de security/auth/tenant_id sin escalate
- ❌ Auditor edita `core/luana-core-*/` o `{other_brand}/` (HARD BAN)
- ❌ Auditor APPROVED + skip CHECKPOINTS.md (story-level review obligatorio)
- ❌ Auditor spawn dev-team SIN documentar findings en T-{n}-review.md (telephone game)
- ❌ Auditor re-spawn dev-team con prompt vago "fix bugs" — cita finding paths verbatim
- ❌ Auditor cap_reached (3 iter) sin escalate explícito → debe ESCALATE Chris

## Caps absolutos

| Métrica | Cap | Acción al exceder |
|---|---|---|
| `self_fix_iter` por ticket | 4 (v4.1 — v4.2: 5) | Spawn dev-team Caso B |
| `audit_iterations` por ticket | 3 (v4.1 — v4.2: 4) | ESCALATE Chris |
| Files modificados por self-fix iter | 2 | Refactor camuflado → spawn dev-team |
| Líneas modificadas por self-fix iter | 10 | idem |
| Tiempo wall-clock audit cycle | 30 min wall | escalate "stuck" |

## Justificación decision tree

**¿Por qué whitelist por categoría (no por tamaño)?**

Tamaño del fix engaña: 1-line change puede ser un branch lógico crítico (cambia comportamiento) o un typo (sin riesgo). La naturaleza define el riesgo, no LOC.

**¿Por qué auditor nunca escribe tests?**

TDD discipline: tests RED primero, fix después. Auditor que escribe tests post-fix introduce confirmation bias (tests pasan porque están diseñados al fix, no al spec). Dev-team mantiene RED→GREEN puro.

**¿Por qué cap 4 self-fix vs cap 2 anterior?**

Forward motion autonomy. Cap 2 era conservador (paradigm v4 inicial). Whitelist verbatim restringe scope → riesgo bajo → ampliar cap a 4. Si excede 4 iter de fixes whitelisted, indica que el dev-team original tenía calidad baja → spawn dev-team para tomar control del ciclo.

**¿Por qué cap 3 audit_iterations totales?**

Auditor que itera 4+ veces indica que findings son síntoma, no root cause. Después de 3 vueltas (dev-team fix + auditor re-review × 3), patrón = problema estructural → ESCALATE Chris para refinar spec o re-decompose story.

## Referencias

- `.claude/skills/auditor/SKILL.md` Step 3 — consume esta rule
- `.claude/skills/dev-team/SKILL.md` Step 2C — recibe auditor handoff con `mode: AUDITOR_AUTO_FIX_LOOP`
- `.claude/rules/tdd-mandatory.md` — TDD discipline (auditor never breaks)
- `.claude/rules/story-closure-gate.md` — Fase B AUDIT + Fase C FIX-LOOP
- `docs/architecture/luana-platform/ADR-007-paradigm-v4.1-autonomy.md` — decisión cementada
- `docs/process/pm-redesign-2026-05.md` § v4.1 amplificación autonomy 2026-05-19 — append

---

## ★ v4.2 Rediseño — 3 carriles por NATURALEZA DE LA VERIFICACIÓN (cement 2026-05-28)

> **SSoT vigente:** esta sección + stub `.claude/rules/auditor-self-fix-policy.md`. El árbol v4.1 de arriba sigue siendo válido como referencia histórica; v4.2 reemplaza la lógica de decisión cardinal. Análisis: `docs/process/audits/2026-05-28-agentic-machinery-audit.md` § 1.

**Insight cardinal v4.2:** el riesgo del self-fix NO es de capacidad del modelo — es **estructural** (sesgo de confirmación). PERO los gates mecánicos (lint, mypy strict, arch-fitness ratchet, coverage, jscpd, tests EXISTENTES) son verificación independiente del actor. Por lo tanto:

> El sesgo de confirmación solo muerde donde la corrección **requiere un test NUEVO**. Si el fix está totalmente verificado por gates + tests existentes → self-fix + re-correr gates ES verificación independiente. Esa es la línea correcta — no el tamaño del fix.

### Decision tree v4.2

```
¿El fix requiere ESCRIBIR un test NUEVO? (comportamiento NO cubierto por un test existente)
├─ SÍ  → CARRIL B: SPAWN dev-team (TDD RED→GREEN). Auditor NUNCA escribe tests.
└─ NO  → ¿Categoría STAKE-ASIMÉTRICO? (security/auth/tenant_id/PII/migration/
         prompt-slot/eval-goldens/state-machine/engine core/cross-brand/meta-paradigm)
        ├─ SÍ  → CARRIL C: ESCALATE Chris (o dev-team, o 2º auditor independiente)
        └─ NO  → CARRIL A: SELF-FIX gate-verified.
                 Aplicar fix → re-correr gate-runner COMPLETO (mecánico, independiente).
                 ALL GREEN → audit-passed (SIN re-spawn full del sub-auditor).
                 RED tras cap → CARRIL B.
```

**Cambio clave vs v4.1:** eliminado el cap "≤2 files/≤10 líneas" y la rama "≥3 archivos O lógica de negocio → spawn". El criterio de Carril A es **"¿lo verifica un gate/test existente?"** — el tamaño era un proxy malo.

### Carril A — gate-verified self-fix (sub-auditor mismo, con Edit)

Aplica cuando TODAS:
1. NO hace falta test nuevo — el comportamiento afectado YA está ejercitado por un test existente (auditor lo cita: `path::test_fn`). Si no encuentra → NO es Carril A → va a B.
2. NO es categoría stake-asimétrico (ver Carril C).
3. El fix vive en el surface del sub-auditor (BE/FE/agentic) — NUNCA cross-surface.

Verificación = gate-runner completo re-corrido (lint + format + mypy + arch-fitness + coverage + jscpd + tests asociados). El sub-auditor NO se re-audita a sí mismo categoría-por-categoría.

Ejemplos típicos Carril A: empty/error-state UI faltante con test de componente existente · condición invertida cubierta por test que ejercita ambas ramas · `response_model=` no cableado con DTO ya definido · off-by-one cubierto por test de borde · import/lint/format/typo/docstring/spanish-neutro/currency-locale.

**Caveat AGENTIC:** Carril A en agentic se limita a **mecánico** (lint/format/typo/import/docstring/observability-write faltante con `try/except`). TODO lo que toque comportamiento del agente — prompt slots, eval goldens, state machine, tool logic, voice — va a **Carril B (builder-agentic)**. Razón: los gates agénticos (eval goldens, pass^k) son no-deterministas → self-fix podría sobre-ajustar el golden.

### Carril B — needs-new-test (spawn dev-team)

Cuando el fix requiere un test nuevo → spawn dev-team `mode: AUDITOR_AUTO_FIX_LOOP`. dev-team es dueño del TDD (escribe test RED→GREEN + el fix). También entra cualquier refactor estructural genuino que ningún test existente cubra.

### Carril C — stake-asimétrico (escalate)

NUNCA self-fix: security/auth · `tenant_id` filter · PII (`response_model` que expone) · migrations · prompt slots · eval goldens · state machine agéntica · `core/luana-core-*/src/` (→ `/pm-vitalia`) · paths fuera de `vitalia/**` · `.claude/{skills,rules}/` o `docs/{process,architecture,specs}/`. Acción: ESCALATE Chris. Opción: 2º auditor Opus independiente como verifier.

### Caps absolutos v4.2

| Métrica | Cap | Acción al exceder |
|---|---|---|
| `self_fix_iter` (Carril A) por ticket | 5 | → Carril B (spawn dev-team) |
| `audit_iterations` totales por ticket | 4 | ESCALATE Chris |
| Tiempo wall-clock audit cycle | 30 min | escalate "stuck" |
| ~~Files/líneas por iter~~ | **ELIMINADO** | el verificador es el gate, no el tamaño |

### Por qué v4.2 da más confianza (no menos)

- **Verificación independiente preservada** donde importa: los gates mecánicos no son cómplices del auditor. Donde los gates NO bastan (test nuevo, seguridad) → sigue el round-trip / escalate.
- **Menos round-trips** = menos pérdida de información + menos costo (~30-60% por finding) + más rápido.
- **Sub-auditor Opus produce mejor fix** que dev-team Sonnet en findings que ya tiene en su modelo mental — sin re-acquirir contexto.
