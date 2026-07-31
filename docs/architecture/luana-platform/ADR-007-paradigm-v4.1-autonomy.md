# ADR-007 — Paradigm v4.1 Autonomy Amplification

**Status:** accepted
**Date:** 2026-05-19
**Deciders:** Chris (ratificación explícita) + /pm-luana (modo Core Engineering)
**Scope:** Engineering process (SDD Level 3) — `.claude/skills/{po-ux,architect,dev-team,auditor}/SKILL.md` + `.claude/rules/auditor-self-fix-policy.md` + `docs/specs/templates/` + `docs/process/pm-redesign-2026-05.md` § v4.1 append

## Context

Paradigm v4 (post pm-redesign 2026-05-06 + story-closure-gate 2026-05-18) cementó:

- 10 estados macro unificados (idea → refining → refined → ready → developing → developed → reviewing → done | parked | dropped)
- 3 conversaciones (discovery/ready · autonomous build · review/merge)
- Auto-handoff cadena `/dev-team` → `/auditor` → `/pm-{brand}` merge (story-closure-gate forward motion)
- Validators ejecutables `04-validators.yaml` con 4 categorías (non_functional / functional / visual / agentic_eval)
- Self-fix cap 2 para triviales lint/format/typo
- Phase D Gherkin verification matrix

Pero post 2026-05-18 caso vitalia (auditor no se disparó automáticamente, story quedó `developed` sin avanzar) emergieron gaps:

1. **Auditor decision policy ante CHANGES_REQUESTED estructural** — paradigm v4 no especificaba si auditor (Opus single-mind) arregla o spawnea dev-team. Forward motion se paralizaba ante errores no-triviales esperando trigger Chris.
2. **Architect handoff incompleto** — `04-validators.yaml` lista validators pero no especifica CÓMO construir Playwright tests (orden, POMs, fixtures, mapping scenario→spec.ts). Dev-team inventaba estructura.
3. **`05-guidelines.md` skills sugerencia** — la sección "Reference docs (load before coding)" era sugerencia, no enforceable. Dev-team podía skipear sin documentar.
4. **Verificación arquitectónica mezclada con lint** — `be_arch_fitness` un solo validator. Sin categoría dedicada con sub-checks (DDD/FSD/anti-dup/tenant_isolation grep).
5. **`/po-ux` no enforce coverage exhaustivo** — happy/negative/edge/adversarial pero sin sub-categorías obligatorias (race, concurrent, network failure, empty, large, a11y, i18n).
6. **Playwright opcional para funcional** — algunas stories pasaban sin behavior tests E2E.

## Decision

Cementar **paradigm v4.1** que amplifica autonomy post-refinamiento Chris (`state=refined → ready → developing → developed → reviewing → done` sin Chris en medio salvo ESCALATE).

### D1 — Auditor decision policy: HÍBRIDO por NATURALEZA DEL FIX

| Tipo de fix | Quién | Cap |
|---|---|---|
| Whitelist verbatim (17 categorías triviales) | Auditor self-fix | 4 iter |
| TDD requerido (nuevo test RED→GREEN) | Spawn dev-team autónomo | dev-team interno 5 iter |
| Refactor 2+ archivos o lógica de negocio | Spawn dev-team autónomo | idem |
| Security / arch drift / cross-brand / engine | ESCALATE Chris o /pm-vitalia | n/a (manual) |

Auditor NUNCA escribe tests (preserva TDD discipline dev-team).

**Cap absoluto `audit_iterations: 3`** (ampliado de 2 → 3 para forward motion). Después → ESCALATE.

**Autonomy clave:** después de spawn dev-team, auditor re-corre gate-runner + Phase D sin trigger Chris. Loop cerrado dentro de Conv 3.

SSoT: `.claude/rules/auditor-self-fix-policy.md` (whitelist verbatim 17 + lista NEVER 16 + caps).

### D2 — Architect entrega `test_construction_plan` mandatory

`04-validators.yaml` gana nueva sección `test_construction_plan` con:

- `playwright_required: true | false` (HARD `true` para stories ui-story / ui-mixed)
- `creation_order` (steps numerados: fixtures → POMs → spec.ts por type)
- `scenario_to_test` mapping verbatim (cada Gherkin scenario → spec.ts file + function + assertions)
- `poms_required` (Page Object Models con métodos esperados)
- `fixtures_required` (auth state, DB seed, network mock)

Dev-team CONSTRUYE siguiendo el plan, no inventa.

### D3 — `must_load_skills` enforceable

`05-guidelines.md § must_load_skills` reemplaza sección "Reference docs". Builder spawn prompt cita lista verbatim. Builder DEBE entregar en `T-{n}-result.md` sección "Skills consulted (must_load enforcement v4.1)" con tabla skill/rule + status (loaded | n/a) + when consulted.

Auditor verifica esa sección existe + completa. Missing → CHANGES_REQUESTED automático.

### D4 — Nueva categoría `architectural_validation` en validators

Separada de `non_functional`. Sub-tests dedicados:

- `arch_ddd_boundaries` (BE)
- `arch_tenant_isolation_grep` (BE)
- `arch_anti_duplication_scan` (cross-brand mirror)
- `arch_fsd_boundaries` (FE)
- `arch_no_cross_brand_imports` (BE+FE)

`04-validators.yaml` schema_version: v4.1, ahora 5 categorías.

### D5 — `/po-ux` refused refined sin sub-categorías scenarios mandatory

Stories funcionales DEBEN cubrir (≥1 scenario cada una aplicable, o `not_applicable_reason` ratificado por Chris):

- `race_condition` (si create/update con unique constraint)
- `concurrent_users` (si list/detail filterable)
- `network_failure` (si fetch FE)
- `empty_state` (si list/dashboard)
- `large_dataset` (si pagination)
- `accessibility` (si surface FE user-facing)
- `i18n` (si copy o currency)

Cada scenario funcional declara `playwright_required: true | false`.

### D6 — Phase D pre-handoff check local en /dev-team

`/dev-team` Step 4.5 verifica LOCALMENTE coverage `gherkin_coverage` ≥ scenarios `01-spec.md`. Si gap → REFUSE auto-handoff, vuelve a iterar. Cierra el round-trip dev-team→auditor cuando coverage falta.

## Consequences

### Positivas

- ✅ **Forward motion autónomo:** auditor no se paraliza, spawnea dev-team o self-fix sin trigger Chris
- ✅ **Calidad tests Playwright:** architect dicta orden + POMs → tests consistentes cross-stories
- ✅ **Skills enforcement medible:** builder entrega evidencia, auditor verifica
- ✅ **Verificación arquitectónica explícita:** 5 categorías validators, no mezcla con lint
- ✅ **Refinamiento exhaustivo:** sub-categorías mandatory garantizan cobertura race/concurrent/etc.
- ✅ **Playwright como default funcional:** todo lo funcional se prueba E2E behavior
- ✅ **Auditor identity preservada:** senior reviewing junior, NUNCA escribe tests

### Negativas / Tradeoffs

- ⚠️ **Cost auditor mayor potencial:** self-fix cap 4 (vs 2) puede gastar más Opus en fixes triviales. Mitigación: whitelist verbatim restringe scope, no es "auditor escribiendo código libremente".
- ⚠️ **Architect work más extenso:** `test_construction_plan` + `must_load_skills` resolved + `architectural_validation` agregan al ready package. Mitigación: orchestrator single-shot ya hace full-stack, scope expanded marginal.
- ⚠️ **Stories más caras de refinar:** sub-categorías mandatory ≥ 4 scenarios extra. Mitigación: previene CHANGES_REQUESTED downstream, ROI positivo.
- ⚠️ **Templates desync existing stories:** stories pre-2026-05-19 no tienen `test_construction_plan` ni `must_load_skills` enforced. Mitigación: forward-only (legacy exempt, igual que cement-date 2026-05-18 story-closure-gate).

## Forward-only enforcement

Stories transicionadas a `state >= ready` ANTES de cement-date 2026-05-19 quedan EXENTAS de los nuevos gates (no retroactivo). Stories con `state=refining` o `state=refined` post-cement-date DEBEN cumplir todo v4.1.

`/po-ux` Step 5 gate check post-2026-05-19 forward.
`/architect` Step 5 + Step 6 deliverables expandidos post-2026-05-19 forward.
`/auditor` Caso B auto-spawn dev-team aplicable a CUALQUIER story en `reviewing` (no breaking — solo amplifica forward motion).

## Implementation files changed (this commit)

| File | Change |
|---|---|
| `.claude/rules/auditor-self-fix-policy.md` | NEW — whitelist verbatim 17 + NEVER 16 + caps |
| `.claude/skills/auditor/SKILL.md` | Step 3 reescrito (Caso B auto-spawn + Caso C amplificado cap 4) |
| `.claude/skills/architect/SKILL.md` | Step 5 + Step 6 + Step 8 expanded (test_construction_plan + must_load + architectural_validation) |
| `.claude/skills/dev-team/SKILL.md` | Step 2 cita must_load + Step 4.5 Phase D pre-handoff |
| `.claude/skills/po-ux/SKILL.md` | Sub-categorías mandatory + Step 5 gate refined |
| `docs/specs/templates/01-spec-template.md` | Sub-categorías scenarios 5-11 + playwright_required |
| `docs/specs/templates/03-arch-template.md` | Sección Test Construction Plan |
| `docs/specs/templates/04-validators-template.yaml` | 5 categorías + test_construction_plan + brand-scoped paths |
| `docs/specs/templates/05-guidelines-template.md` | NEW — must_load_skills enforceable |
| `docs/specs/templates/06-tickets-template.yaml` | renamed from `04-tickets` + must_load_skills per ticket |
| `docs/specs/templates/T-result-template.md` | Sección "Skills consulted" obligatoria |
| `docs/process/pm-redesign-2026-05.md` | Append § v4.1 amplification 2026-05-19 |
| `docs/architecture/luana-platform/ADR-007-paradigm-v4.1-autonomy.md` | THIS ADR |

## References

- ADR-006 — story-closure-gate (forward motion antecedente)
- `.claude/rules/story-closure-gate.md` — Fase A-F (v4.1 amplifica B y C)
- `.claude/rules/tdd-mandatory.md` — TDD discipline (auditor never breaks)
- `docs/process/pm-redesign-2026-05.md` — paradigm v4 base
- Conversación 2026-05-19 — propuesta Chris + 3 decisiones ratificadas (auditor híbrido + checklist mandatory + full v4.1 cement)

---

## Bitácora de versiones posteriores

### v4.2 (cement 2026-05-28) — 3 carriles por naturaleza de verificación

> **Este cuerpo (v4.1) queda SUPERSEDED en los caps de autonomy.** El resto del ADR (D1-D6, Forward-only enforcement, Consequences) permanece válido como contexto histórico. Las cifras que manda son las de v4.2.

**Caps actualizados (v4.2 reemplaza v4.1):**

| Cap | v4.1 (este ADR) | v4.2 (vigente) |
|---|---|---|
| `self_fix_iter` (Carril A) | 4 iter | **≤ 5** |
| `audit_iterations` total | 3 | **≤ 4** |
| Wall-clock conv 3 | no especificado | **≤ 30 min** |

**Nuevo modelo 3 carriles (reemplaza tabla D1):**

```
¿Fix requiere ESCRIBIR test NUEVO?
├─ SÍ  → Carril B: SPAWN dev-team (TDD RED→GREEN). Auditor NUNCA escribe tests.
└─ NO  → ¿Categoría STAKE-ASIMÉTRICO? (security/auth/tenant_id/PII/migration/…)
         ├─ SÍ  → Carril C: ESCALATE Chris
         └─ NO  → Carril A: SELF-FIX gate-verified (cap ≤ 5 iter)
```

**Caveat agentic (v4.2):** Carril A solo para mecánico (lint/format/typo/import). Todo lo que toca comportamiento agéntico (prompt slots, eval goldens, state machine, voice) → Carril B siempre.

**SSoT vigente:** `.claude/rules/auditor-self-fix-policy.md` (whitelist v4.1 17 categorías + 3 carriles v4.2 + caps v4.2). Ese archivo es la referencia canónica; este ADR es historia.

**Deciders v4.2:** sesión 2026-05-28 — auditoría machinery + análisis costo/tensión → Chris ratificó los 3 carriles + caps ampliados.
