# Story Closure Gate — rationale + case study

**Cement-date:** 2026-05-18
**Origen:** caso vitalia 2026-05-18 (ver § Case study)
**Hard rule SSoT:** `.claude/rules/story-closure-gate.md`
**Decisión arquitectónica:** `docs/architecture/luana-platform/ADR-006-story-closure-gate.md`

> **★ Actualización proceso v5 (2026-06).** La hard rule `.claude/rules/story-closure-gate.md` (machinery CHECK 13-18) insertó las **fases nombradas G (`AWAIT_CHRIS_VERIFY`) + R (reconcile)** entre `developed` y `reviewing`, consolidó el signoff en `chris_verify.signoff` (retiró `demo_signoff`), y la WIP-cap es **module-scoped** (`≤1 por code:{module}`, NO por worktree). Este doc es el **rationale/case-study**; para el modelo de proceso VIVO leé la hard rule + `PROCESS-MODEL.md` §1-2.

## TL;DR

Una story end-to-end pasa por las fases A→F **+ las 2 fases nombradas G/R insertadas en proceso v5**: DEV → **[G `AWAIT_CHRIS_VERIFY`: Chris ejerce el kit live + firma `chris_verify.signoff`, ANTES del auditor]** → **[R reconcile: `/pm-{brand}` alinea spec/arch/cap → `reconciled: true`]** → AUDIT → FIX-LOOP → GHERKIN → DOCS → MERGE, antes de declararse `done`. `/dev-team` cierra `developed` → **G** (salvo `autonomous_mode: true`) → **R** → AUTO-HANDOFF `/auditor`. APPROVED → AUTO-HANDOFF `/pm-{brand}` merge. Escape valve: `defer_audit: true`. **Vocabulario vivo SSoT = la hard rule `.claude/rules/story-closure-gate.md` (v5) + `PROCESS-MODEL.md` §1-2** — este doc es rationale/case-study.

## Por qué este rule existe

El paradigm v4 (post pm-redesign 2026-05-06) introdujo el ciclo de 3 conversaciones: Discovery → Build → Review+Merge. La conv 3 quedó descrita como "Chris triggered manualmente para controlar gasto Opus". Esa frase literal apareció en:

- `CLAUDE.md` § Flujo extremo-a-extremo
- `docs/process/pm-redesign-2026-05.md:272`
- `.claude/skills/dev-team/SKILL.md:10` (description embedded en frontmatter YAML)
- `.claude/skills/auditor/SKILL.md:3` (description embedded en frontmatter YAML)

Tres puntos de control le decían a `/dev-team` "tu responsabilidad termina en `developed`. Chris dispara `/auditor` cuando quiera". El builder cumplió esa instrucción al pie de la letra. Cuando Chris dejó la sesión correr autónomamente, `/dev-team` interpretó "siguiente story ready" como next acción válida después de cerrar `developed`.

El control de costo Opus al que apuntaba "Chris manual trigger" ya está resuelto por el cost-routing del paradigm v4:

- `/dev-team` corre Sonnet/qwen-opencode default para BE/FE no-agentic
- Opus solo en AGENTIC `production_code: true` (R23 hard rule)
- `/auditor` puede usar Sonnet para tests/lint deterministicos, Opus solo en categorías cualitativas (C1-C3 + auditor-agentic)
- `/auditor` sub-fixes lint/format/typo se hacen Haiku-eligible (futuro)

El bug "Chris manual" era conservadurismo de la era pre-paradigm-v4-cost-routing, no un control de costo real post-routing.

## Decisiones cementadas (2026-05-18 — Chris ratificó)

1. **1 worktree = 1 story padre estricto**. Sub-stories del mismo outcome pueden compartir worktree PERO cada sub-story atraviesa las 6 fases (dev→audit→fix→gherkin→docs→merge) antes que la siguiente arranque.
2. **Conv 3 auto-handoff default** desde `/dev-team` → `/auditor` → `/pm-{brand}` merge. La opción "Chris manual trigger" queda como excepción opt-in via `checkpoint.md::defer_audit: true` con razón documentada.
3. **Docs al cierre: AMBOS** — `07-merge.md` (run frozen, 5 secciones cementadas) + capability YAML (`verification.commands` + `verification.gherkin_evidence` canónicos reusables).
4. **Cleanup deuda vitalia:** Linear Option A (pausar copilot-tools-impl, auditar+mergear infra-cross-cutting primero, después continuar copilot worktree nuevo). Esto solo después de cementar el harness modificado.

## 6 fases por story (detalle)

### Fase A — DEV
Owner: `/dev-team`. Input: ready package (`01-spec.md`, `03-arch.md`, `04-validators.yaml`, `05-guidelines.md`, `06-tickets.yaml`). Output: `T-{n}-result.md` por ticket + `gate-output.json` GREEN + commits pushed. Transition: `ready → developing → developed`.

**Step de cierre crítico (post-decreto):** cuando todos los tickets pushed + validators GREEN, `/dev-team` MUST emitir handoff explícito (NO Chris-trigger):

```
✅ Story {brand}/{story-id} all tickets pushed.
WIP cap status: developing was N → developed (N-1) + 1.
Story state: developing → developed.

→ HAND OFF /auditor brand={brand} story={story-id}

(salvo defer_audit:true documentado en checkpoint.md — en ese caso STOP, pingear Chris en próxima bootstrap /pm-{brand})
```

Y refuse pickup de cualquier ticket de otra story hasta que current story alcance `done` (o tenga `defer_audit: true` ratified).

### Fase B — AUDIT
Owner: `/auditor`. Input: `T-{n}-result.md` + `gate-output.json` + `01-spec.md` (Gherkin scenarios) + `04-validators.yaml`. Output: `T-{n}-review.md` por ticket + `CHECKPOINTS.md` (C1-C5 grid). Transition: `developed → reviewing`.

`/auditor` toma story en `developed` (auto-handoff de A o por Chris manual si defer venció). Transitiona a `reviewing` al pickup. Spawna sub-auditores (`auditor-backend` / `auditor-frontend` / `auditor-agentic`) por ticket según surface. Veredicto: APPROVED | CHANGES_REQUESTED | ESCALATED.

### Fase C — FIX-LOOP
Owner: `/dev-team` (si CHANGES_REQUESTED). Input: `T-{n}-review.md` findings. Output: fix commits + re-audit. Cap absoluto 2 iter. Si excede → ESCALATED (escala Chris).

### Fase D — GHERKIN verification
Owner: `/auditor` (Phase D dentro de B). Input: `01-spec.md § Acceptance criteria` (Gherkin scenarios) + `06-tickets.yaml::gherkin_coverage` (mapping scenario → test paths). Output: `06-audit/gherkin-matrix.md` (verdict per scenario).

Algoritmo:
1. Lee `01-spec.md`, extrae lista scenarios Gherkin (Given/When/Then bloques).
2. Lee `06-tickets.yaml`, agrega `gherkin_coverage[scenario] → tests[]` cross-ticket.
3. Para cada scenario, ejecuta los tests citados.
4. Escribe `06-audit/gherkin-matrix.md`:
   ```markdown
   # Gherkin verification matrix — {brand}/{story-id}

   | Scenario (Gherkin) | Test path | Status | Notes |
   |---|---|---|---|
   | SC-01 "..." | `{brand}/backend/tests/.../test_x.py::test_y` | ✅ PASS | |
   | SC-02 "..." | `{brand}/frontend/e2e/.../{id}.spec.ts::scenario-02` | ✅ PASS | |
   | SC-03 "..." | (none) | ❌ NO COVERAGE | scenario sin mapping en gherkin_coverage |
   | SC-04 "..." | `{brand}/backend/.../test_z.py::test_w` | ❌ FAIL | test exists, fails |
   | ... | ... | ... | ... |
   ```
5. Cualquier ❌ → CHANGES_REQUESTED + cita scenarios en `T-{n}-review.md`.

**Playwright targeted:** E2E corre solo specs que tocan rutas de `01-spec.md § rutas afectadas` (no full smoke suite — eso es `/test-all`).

### Fase E — DOCS
Owner: `/pm-{brand}`. Input: story + audit artifacts. Output:
- `{brand}/docs/product/capabilities/{m}/{c}.yaml` creado/actualizado con `verification.commands` + `verification.gherkin_evidence`
- `{brand}/docs/product/modules/{m}.md` auto-list refresh
- Embedded en F como prep paso 1-4 antes de transition.

### Fase F — MERGE
Owner: `/pm-{brand}`. Input: APPROVED CHECKPOINTS + Fase E docs. Output: `07-merge.md` con 5 secciones cementadas + squash-merge `wip/* → main` + archive story to `{brand}/docs/archive/{year}/stories/{id}/`. Transition: `reviewing → done`.

5 secciones de `07-merge.md` (schema verbatim en `.claude/rules/story-closure-gate.md`):
1. **§ Gherkin verification matrix** (copia de `06-audit/gherkin-matrix.md`)
2. **§ Playwright E2E run** (comando + output verdict)
3. **§ Capabilities updated/created** (paths exactos)
4. **§ Modules MD refreshed** (paths exactos)
5. **§ How to verify** (comandos copy-paste reproducibles)

`/pm-{brand}` REHÚSA cerrar `reviewing → done` si missing alguna sección.

## Forward-only retroactividad

Stories transicionadas a `reviewing` ANTES del cement-date (2026-05-18) quedan exentas del gherkin_coverage gate (auditor usa regla anterior, sin Phase D estricta). Stories que transicionan POST-cement-date deben cumplir.

La deuda vitalia (vitalia-slice-1-infra-cross-cutting + vitalia-copilot-tools-impl) transita POST-cement-date → debe cumplir el gate nuevo. Es el test operacional del decreto.

## Case study — vitalia 2026-05-18

### Estado en worktree `wip/vitalia-slice-1-shipping` (commit `21f57a4`)

```
vitalia-slice-1-infra-cross-cutting
  state: developed
  phase: ALL_10_TICKETS_PUSHED_AWAITING_AUDIT
  tickets_pushed: [T-arch-1, T-infra-1..9]   # 10 tickets
  next_action: "/auditor spawns auditor-frontend + auditor-backend"
  → NEVER triggered

vitalia-copilot-tools-impl
  state: developing
  phase: T_BE_SERVICES_3_PUSHED_AWAITING_AG_TOOLS
  tickets_pushed: [T-be-migrations-1, T-be-services-1, T-be-services-2, T-be-services-3]   # 4 tickets
  blocker_dependencies: [vitalia-slice-1-infra-cross-cutting T-infra-{1,2,3} state=developed]
  → BLOCKER LITERALLY MET, but the prerequisite story is NOT done — it's developed
```

### Cómo llegó ahí

1. `/architect` cerró ready packages para ambas stories. Las dos en `state: ready`.
2. Chris arrancó `/dev-team` sobre infra-cross-cutting. 10 tickets pushed, validators GREEN. `/dev-team` transitionó `developing → developed`.
3. Sin Chris in-chat, `/dev-team` interpretó "blocker for copilot-tools-impl is met (infra developed)" → picked copilot-tools-impl ready package → arrancó developing.
4. 4 tickets pushed copilot. Worktree ahora tiene 2 stories abiertas simultáneamente.
5. Cuando Chris volvió a la sesión, encontró infra developed sin auditar/mergear y copilot en plena ejecución sobre código no validado del padre.

### El bug del paradigm v4

Layer-1 documental: paradigm v4 dijo "Chris manual trigger Conv 3". Layer-2 skills: `/dev-team` frontmatter description embebió esa frase + steps internos cementaron "awaiting QA Chris triggers". Layer-3 ausencia de hooks: pre-commit no detectaba "story B commit con story A pending audit".

### Fix decretado (este rule)

| Layer | Antes | Después |
|---|---|---|
| Documental | "Conv 3 manual trigger" | "Conv 3 auto-handoff default; defer_audit:true escape valve" |
| Skill /dev-team | Cierra developed + STOP | Cierra developed + AUTO-HANDOFF /auditor + REFUSE pickup nueva story |
| Skill /auditor | Cierra APPROVED + STOP | Cierra APPROVED + AUTO-HANDOFF /pm-{brand} merge + Phase D gherkin |
| Skill /pm-{brand} | Bootstrap menú (a) nueva story disponible siempre | Bootstrap step 0 scan stories developed/reviewing → REUSE FIRST |
| Hook pre-commit | (sin guard) | Section 12: bloquea stage de files de story B si A pending |
| Hook cleanup-session | Remove worktree always | Refuse si state ≠ done sin defer_audit |
| Template 06-tickets | (sin gherkin field) | `gherkin_coverage` mandatory post-cement |
| Template 07-merge | Flexible | 5 secciones cementadas |

### Operational test

El cleanup vitalia (auditar+mergear infra-cross-cutting + retomar copilot-tools-impl worktree nuevo) es la primera ejecución del nuevo gate. Si funciona, infra cierra limpia con `07-merge.md` 5 secciones completas + `06-audit/gherkin-matrix.md` + capabilities/* updates. Si falla, debugeás el gate antes de aplicarlo a más stories.

## Ratchet — qué NO está en este rule

Cosas que evaluamos y dejamos OUT (shrink-only):
- Cap numérico "max 3 audits auto-disparados por session": rechazado. Recrea el bug (cuarta story queda colgada). Gate absoluto + defer_audit explícito es mejor.
- Promotion proposal en `docs/promotion-protocol/proposals/`: NO. Esa carpeta es estrictamente para code-level lifts brand→core. Este es proceso/paradigm cross-cutting → ADR-005 platform-level.
- Auto-fix loop infinito C: cap absoluto 2 iter mantiene control de costo.

## Cross-references

- `.claude/rules/story-closure-gate.md` — hard rule SSoT (consumido por skills + hooks)
- `docs/architecture/luana-platform/ADR-006-story-closure-gate.md` — decisión arquitectónica
- `docs/process/pm-redesign-2026-05.md` — paradigm v4 con Conv 3 actualizado
- `docs/process/learnings.md` — 2026-05-18 entry "Conv 3 auto-handoff cement" promotable: yes
- `CLAUDE.md` — secciones Conv 3 + cost-routing actualizadas
