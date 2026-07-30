# Story Closure Gate

**Origen:** caso vitalia 2026-05-18 — `vitalia-slice-1-infra-cross-cutting` quedó en `state: developed` (10 tickets pushed, validators GREEN) sin auditar+mergear, y arrancó `vitalia-copilot-tools-impl` en el mismo worktree (4 tickets pushed). Dos stories abiertas simultáneamente. Raíz del gap: paradigm v4 (CLAUDE.md + pm-redesign + dev-team SKILL + auditor SKILL) decía "Conv 3 Chris triggers manualmente para controlar gasto Opus" — la palabra "manualmente" hizo que `/dev-team` interpretara que su responsabilidad terminaba en `developed`.

**Cement-date:** 2026-05-18.

## Regla cardinal

**Una story que entra a `state: developed` o `state: reviewing` NO PUEDE ser abandonada para arrancar trabajo en otra story.** El ciclo completo es:

```
ready → developing → developed → reviewing → done
                         │           │
                         └─ AUTO ─→  │
                         (default)   │
                                     └─ APPROVED ─→ merge ─→ done
```

Default forward-motion: `/dev-team` al cerrar `developed` emite handoff AUTOMÁTICO a `/auditor`. `/auditor` al cerrar APPROVED emite handoff AUTOMÁTICO a `/pm-{brand}` para merge. Sin Chris-trigger manual obligatorio.

## Las 6 fases por worktree

Una story = un ciclo end-to-end. Cada fase tiene owner explícito y artifact producido.

| Fase | Owner | Input | Output / artifact | Transition |
|---|---|---|---|---|
| **A — DEV** | `/dev-team` | ready package (`01-spec.md`, `03-arch.md`, `04-validators.yaml`, `05-guidelines.md`, `06-tickets.yaml`) | `T-{n}-result.md` por ticket · `gate-output.json` GREEN · commits pushed | `ready → developing → developed` |
| **B — AUDIT** | `/auditor` (auto-handoff de A) | `T-{n}-result.md` · `gate-output.json` · `01-spec.md` (Gherkin) | `T-{n}-review.md` por ticket · `CHECKPOINTS.md` (C1-C5) | `developed → reviewing` |
| **C — FIX-LOOP** | `/dev-team` (si CHANGES_REQUESTED) | `T-{n}-review.md` findings | fix commits · re-audit | cap 2 iter · si excede → ESCALATED |
| **D — GHERKIN** | `/auditor` (Phase D dentro del audit) | `01-spec.md § Acceptance criteria` + `06-tickets.yaml::gherkin_coverage` | `06-audit/gherkin-matrix.md` (scenario → test path → status) | embedded en B |
| **E — DOCS** | `/pm-{brand}` | story + audit artifacts | `{brand}/docs/product/capabilities/{m}/{c}.yaml` (créate/update con `verification.commands` + `verification.gherkin_evidence`) · `{brand}/docs/product/modules/{m}.md` (auto-list refresh) | embedded en F prep |
| **F — MERGE** | `/pm-{brand}` | APPROVED CHECKPOINTS + Fase E docs | `07-merge.md` (5 secciones cementadas) · squash-merge `wip/* → main` · **archive story** (`git mv {brand}/docs/product/stories/{story-id}/ {brand}/docs/archive/{year}/stories/{story-id}/` en MISMO commit del 07-merge — R2 per `.claude/rules/brand-docs-schema.md`) | `reviewing → done` |

Solo después de F=done, otra story puede arrancar (en worktree nuevo si la convention "1 worktree = 1 story padre" aplica).

**Cross-reference:** la acción "archive story" en Fase F está concretada como hard rule en `.claude/rules/brand-docs-schema.md` § R2. El path canónico es `{brand}/docs/archive/{year}/stories/{story-id}/` (immutable snapshot). El `git mv` debe ir en el MISMO commit que escribe `07-merge.md` — auditor escruta esto pre-merge (ver `.claude/skills/auditor/SKILL.md` § C5 + § Anti-patterns).

## Contrato `07-merge.md` (5 secciones cementadas)

`/pm-{brand}` REHÚSA cerrar `reviewing → done` si `07-merge.md` no contiene las 5 secciones. Schema verbatim:

```markdown
# Merge artifact — {brand}/{story-id}

> Brand: {brand}
> Merged: <iso-date>
> Commit (squash-merge): <SHA>

## § 1 — Gherkin verification matrix

> Cada scenario de `01-spec.md` mapeado a test que pasa. Copia de `06-audit/gherkin-matrix.md`.

| Scenario (Gherkin) | Test path | Status |
|---|---|---|
| SC-01 "..." | `{brand}/backend/tests/.../test_x.py::test_y` | ✅ PASS |
| SC-02 "..." | `{brand}/frontend/e2e/.../{story-id}.spec.ts::scenario-02` | ✅ PASS |
| ... | ... | ... |

## § 2 — Playwright E2E run

> Última corrida E2E targeted a rutas de esta story. Comando + output verdict.

\`\`\`bash
cd {brand}/frontend && E2E_BASE_URL=http://localhost:300X npx playwright test --grep "{story-id}"
\`\`\`

- Specs run: <N>
- Passed: <N>
- Failed: 0
- Trace: `{brand}/frontend/playwright-report/` (link/path)

## § 3 — Capabilities updated/created

> Inventory enforcement (R32). Paths exactos.

- `{brand}/docs/product/capabilities/{module-a}/{cap-x}.yaml` — NEW (status: live)
- `{brand}/docs/product/capabilities/{module-b}/{cap-y}.yaml` — UPDATE (status: planned → live)
- ...

## § 4 — Modules MD refreshed

> Auto-list marker regenera. Paths.

- `{brand}/docs/product/modules/{module-a}.md` — auto-list incluye `{cap-x}` post-merge
- `{brand}/docs/product/modules/{module-b}.md` — auto-list incluye `{cap-y}` post-merge

## § 5 — How to verify (reproducible commands)

> Comandos copy-paste para reproducir la verificación de la funcionalidad.

\`\`\`bash
# Setup (asumiendo stack {brand} corriendo via make dev-{brand}):
WS=$(git rev-parse --show-toplevel)

# 1. Unit tests
cd ${WS}/{brand}/backend && ${WS}/.venv/bin/pytest tests/modules/{brand}/{m}/ -v

# 2. Architecture fitness
cd ${WS}/{brand}/backend && ${WS}/.venv/bin/pytest tests/architecture/ -v

# 3. Frontend tests + type-check
cd ${WS}/{brand}/frontend && npx tsc --noEmit && npx vitest run src/features/{m}/

# 4. E2E smoke (Playwright)
cd ${WS}/{brand}/frontend && E2E_BASE_URL=http://localhost:300X npx playwright test --grep "{story-id}"

# 5. (Si agentic) Eval goldens
cd ${WS}/{brand}/backend && ${WS}/.venv/bin/pytest tests/agentic_evals/ --trials=3
\`\`\`

**Expected:** todos los comandos retornan exit code 0.
```

## `gherkin_coverage` field en `06-tickets.yaml`

Forward-only post-cement-date (2026-05-18). Cada ticket entry en `06-tickets.yaml` MUST incluir mapping explícito scenario → test paths:

```yaml
tickets:
  - id: T-1
    title: "..."
    state: ready
    surface: backend
    owner_eligibility: [qwen-opencode, claude-sonnet]
    production_code: true
    acceptance:
      validator_ids: [val-be-1, val-be-2]
    gherkin_coverage:                          # ★ NEW field mandatory ★
      - scenario: "SC-01 Wizard finaliza con tenant_id válido"
        tests:
          - "{brand}/backend/tests/modules/{brand}/onboarding/test_wizard_complete.py::test_creates_tenant"
      - scenario: "SC-02 Wizard rechaza email duplicado"
        tests:
          - "{brand}/backend/tests/modules/{brand}/onboarding/test_wizard_complete.py::test_duplicate_email_rejected"
```

`/auditor` Phase D lee este mapping, ejecuta los tests citados, escribe `06-audit/gherkin-matrix.md` con verdict por scenario. Cualquier scenario sin mapping O test FAIL → CHANGES_REQUESTED.

**Retroactividad:** stories transicionadas a `reviewing` ANTES de cement-date (2026-05-18) quedan exentas. Stories que transicionan POST-cement-date deben cumplir gherkin_coverage.

## Escape valve — `defer_audit: true`

Caso de uso: Chris quiere pausar auditoría por razón explícita (revisar diseño antes de gastar Opus auditor, esperar feedback externo, story en hold por bloqueo upstream).

```yaml
# {brand}/docs/product/stories/{story-id}/checkpoint.md
---
brand: {brand}
story_id: {story-id}
state: developed
phase: AWAIT_AUDIT_DEFERRED
defer_audit: true                                          # ★ escape valve explícito
defer_audit_reason: "Chris ratificó pausa 2026-05-18: revisar 03-arch sub-tema X antes de gastar auditor Opus"
defer_audit_ratified_by: chris
defer_audit_at: 2026-05-18T15:30:00-05:00
defer_audit_until: 2026-05-25                              # opcional, hint para bootstrap ping
---
```

Mientras `defer_audit: true`:
- `/dev-team` NO auto-handoff a `/auditor` al cerrar `developed`
- `/pm-{brand}` bootstrap PINGEA esta deuda en cada sesión (lista `deferred_audits` en `{brand}/docs/product/checkpoint.md`)
- WIP cap relax: la story NO cuenta contra el cap `developed ≤ 1` (es excepción documentada)
- Para arrancar nueva story con story-padre A con defer_audit, /pm-{brand} requiere ratify explícito Chris ("OK sigo, A queda parked manual hasta {fecha}")

Sin `defer_audit: true` el gate es ABSOLUTO: refuse nueva story.

## WIP cap post-decreto (hard rule)

| Estado | Cap default | Razón |
|---|---|---|
| `developing` | ≤ 1 por worktree | Forward motion — una story padre activa por worktree |
| `developed` | ≤ 1 por worktree | Pending audit — no acumular |
| `reviewing` | ≤ 1 por worktree | Auditor en curso |
| `done` | ∞ (rolling 90d archive) | Cerradas |

Sub-stories del mismo outcome (estructura padre/hija) pueden compartir worktree pero pasan secuencialmente: sub-story A `done` ANTES de sub-story B arrancar.

`defer_audit: true` documentado en checkpoint es la única excepción.

## Naming convention worktree

```bash
# Convention:
wip/{brand}-{story-padre-id}
# Ejemplos:
wip/vitalia-ux-discovery
wip/nicolify-pi13-billing-overhaul
wip/comunify-voice-cloning-rollout
```

**NO** `wip/{brand}-slice-N-shipping` ni `wip/{brand}-misc` (ambiguos — hospedaron historicamente >1 story).

`scripts/git/new-session.sh` requiere `--story-id` flag y valida que la story exista en `{brand}/docs/product/stories/`. Branch derivado: `wip/{brand}-{story-id}`.

## Enforcement layers (defense-in-depth)

| Layer | Mecanismo | Falla → |
|---|---|---|
| 1 — Skill `/pm-{brand}` bootstrap | Step 0 NEW: escanea `{brand}/docs/product/stories/*/checkpoint.md`. Si alguna state ∈ {developed, reviewing} en worktree activo Y sin defer_audit → REUSE THAT FIRST, refuse menu (a) nueva story | Mensaje claro a Chris con story-id pendiente |
| 2 — Skill `/dev-team` Step 5 final | Auto-handoff explícito a `/auditor` con prompt verbatim cuando state=developed. Refuse pickup nuevo ticket si checkpoint worktree tiene >1 story en state ∈ {developing, developed, reviewing} sin defer_audit | STOP + emisor handoff line |
| 3 — Skill `/auditor` Phase D + Step 5 | Phase D gherkin verification. Step 5 final auto-handoff a `/pm-{brand}` para merge con prompt verbatim cuando APPROVED | STOP + emisor handoff line |
| 4 — Hook `scripts/git-hooks/pre-commit` Section 12 | Bloquea stage de archivos de story B si story A en mismo worktree state ∈ {developed, reviewing} sin defer_audit | Exit 1 con hint accionable |
| 5 — `scripts/git/cleanup-session.sh` | Refuse remove worktree si ninguna story en él alcanzó state=done O todas las open tienen defer_audit ratificado | Mensaje "story X pending audit/merge, resolver antes cleanup" |
| 6 — Template `06-tickets-template.yaml` | `gherkin_coverage` field documentado mandatory post-cement-date | Auditor Phase D FAIL si missing |
| 7 — Template `07-merge-template.md` | 5 secciones cementadas (gherkin matrix · playwright · capabilities · modules · how to verify) | `/pm-{brand}` REFUSE merge si missing sections |

## Anti-patterns prohibidos

- ❌ `/dev-team` cierra ticket final + state=developed + arranca otro ticket de story distinta en mismo worktree (este es el bug origen)
- ❌ `/pm-{brand}` ofrece menú "nueva story" cuando hay story pendiente audit sin defer_audit
- ❌ `/auditor` cierra APPROVED sin emitir handoff explícito a `/pm-{brand}` merge
- ❌ `/pm-{brand}` transitions `reviewing → done` sin `07-merge.md` 5 secciones completas
- ❌ `06-tickets.yaml` post-cement-date sin `gherkin_coverage` field
- ❌ Worktree branch nombrado ambiguo (`wip/vitalia-slice-1-shipping` hospedó 2 stories)
- ❌ `defer_audit: true` en checkpoint sin razón documentada + ratificación Chris
- ❌ `defer_audit: true` usado como atajo crónico para evitar auditar (es escape valve, no default)
- ❌ Mergear story sin actualizar `{brand}/docs/product/capabilities/{m}/{c}.yaml` con `verification.commands`
- ❌ `cleanup-session.sh` ejecutado en worktree con story pendiente

## Caso origen verbatim (2026-05-18 vitalia)

```
git log --oneline -5
21f57a4 docs(vitalia): T-be-services-3 SHA pin 476a755
476a755 feat(vitalia/agentic/lucas): T-be-services-3 — Lucas backend services
032807a feat(vitalia/sales_agent): T-be-services-2 — Adrián backend services
55dd313 feat(vitalia/copilot): T-be-services-1 Valeria wizard backend services
fe0fbad docs(vitalia): T-be-migrations-1 SHA pin 3adea2c

# Story 1: vitalia-slice-1-infra-cross-cutting
#   state: developed (10 tickets pushed) — NUNCA auditada/mergeada
# Story 2: vitalia-copilot-tools-impl
#   state: developing (4 tickets pushed) — INICIADA sin cerrar Story 1
# Worktree: wip/vitalia-slice-1-shipping (ambos commits)
```

`/dev-team` cumplió textualmente "On all GREEN all tickets: state=developing→developed". El paradigm v4 decía "Chris triggers manualmente". Sin Chris in-chat el ciclo se rompe.

Post-decreto: el mismo escenario falla en Layer 2 (`/dev-team` refuse pickup) Y Layer 4 (pre-commit hook bloquea stage de files de story B con story A pending).

## Fase F.3 — Capability ledger update (v2 cement 2026-05-27)

> **★ v4 alignment (cement 2026-05-28):** `atomics` MUERTO — `scenario` es la unidad atómica de comportamiento. SSoT del schema cap: `docs/process/capability-protocol.md` + `docs/process/lifecycle.md`.

`/pm-{brand}` aplica logic del `cap_change_type` (declarado en checkpoint.md de la story) al cap YAML target:

| `cap_change_type` | Acción sobre cap YAML |
|---|---|
| `new` | Crear `{brand}/docs/product/capabilities/{module}/{slug}.yaml` con schema v4 completo · `change_log[0]` con `type: new` + scenarios iniciales |
| `fix` | Append `change_log` entry con `type: fix` · `scenarios_added: []` · NO toca `scenarios[]` |
| `extend` | Append `change_log` entry con `type: extend` + scenarios nuevos · Append al array `scenarios[]` con `added_in_story: {story_id}` |
| `derive` | Crear cap YAML hijo con `parent_cap: {origen_slug}` + `change_log[0] type: derive` · Update cap padre: append `derives_capabilities: [hijo_slug]`. Crear hijo primero, luego actualizar padre. |

Actualizar también: `last_modified` del cap = today.

### Enforce reglas v3.1 — cap verification (cement 2026-05-28)

| `cap_change_type` | `scenarios_added.length` | Otros checks |
|---|---|---|
| `new` | `>= 1` REQUIRED | `scenarios[]` overall ≥1 scenario con shape válido |
| `extend` | `>= 1` REQUIRED | `scenarios[]` debió crecer vs commit anterior |
| `fix` | `>= 0` (opcional) | NO requiere scenario nuevo |
| `derive` | `>= 1` REQUIRED en cap hijo | `parent_cap.derives_capabilities[]` lista hijo |

Enforce: `scripts/reconcile_capabilities.py --validate-ledger`. Pre-commit hook HARD en `main/release/*` + WARN en `wip/*`.

### Enforce reglas v3.2 — bidirectional code↔cap (cement 2026-05-28)

Cross-checks Fase F.3 adicionales:
1. **Scenarios → e2e_test paths:** todos los `scenarios[*].e2e_test` declarados existen en filesystem (cross-check 3 · HARD)
2. **Access → roles:** roles en `access.entry_points[*].requires_role` coinciden con `@require_phi_access` decorators (cross-check 4 · advisory hasta resolver gap RBAC)

Enforce: `scripts/validate_code_cap_bidirectional.py`. Pre-push hook HARD bloquea si cross_check_3 drift > 0.

Doc canónico: `docs/process/capability-protocol.md` § Sección 11 (v3.2) + § Sección 13 (bidirectional validator).

## WIP cap v2 — module-scoped (cement 2026-05-28 · ADR-009)

Bajo el modelo **hub único** (N sesiones / un worktree por marca), el cap es **por `code:{module}` bucket**: un build en vuelo por módulo. Stories de módulos distintos `developing` en paralelo = OK.

| Estado | Cap default (v2) |
|---|---|
| `developing` | ≤ 1 por **`code:{module}`** (no por worktree) |
| `developed` | ≤ 1 por módulo (cerrar antes de otra del mismo módulo) |
| `reviewing` | ≤ 1 por módulo |
| `done` | ∞ (rolling 90d) |

Stories del MISMO módulo siguen secuenciales (A `done` ANTES de B del mismo módulo). `defer_audit: true` documentado es la única excepción. SSoT: `.claude/rules/parallel-safety.md` M14 + `docs/architecture/luana-platform/ADR-009-single-hub-worktree.md`.

## defer_audit — schema verbatim en checkpoint.md

```yaml
state: developed
phase: AWAIT_AUDIT_DEFERRED
defer_audit: true
defer_audit_reason: "Chris ratificó pausa 2026-MM-DD: razón X"
defer_audit_ratified_by: chris
defer_audit_at: 2026-MM-DDTHH:MM:SS-05:00
defer_audit_until: 2026-MM-DD   # opcional, hint bootstrap ping
```

Mientras `defer_audit: true`: `/dev-team` NO auto-handoff · `/pm-{brand}` pingea deuda en bootstrap · WIP cap relax (no cuenta contra `developed ≤ 1`). Para arrancar nueva story requiere Chris ratify explícito. Sin `defer_audit: true` el gate es ABSOLUTO.

## Referencias

- `docs/process/story-closure-gate.md` — rationale + workflow detail (case study + ratchet)
- `docs/architecture/luana-platform/ADR-006-story-closure-gate.md` — decisión arquitectónica
- `docs/process/pm-redesign-2026-05.md` — paradigm v4 actualizado (Conv 3 auto-default)
- `docs/specs/templates/07-merge-template.md` — schema 5 secciones cementadas
- `docs/specs/templates/04-tickets-template.yaml` — `gherkin_coverage` field
- `.claude/skills/dev-team/SKILL.md` Step 5/6 — auto-handoff trigger
- `.claude/skills/auditor/SKILL.md` Phase D + Step 5 — gherkin verification + merge handoff
- `.claude/skills/pm-{brand}/SKILL.md` Bootstrap Step 0 — scan stories developed/reviewing
- `.claude/rules/brand-docs-schema.md` — R2 concreta el path archive + auto-move como hard rule (cement 2026-05-19)
- `scripts/git-hooks/pre-commit` Section story-closure-gate — pre-commit guard
- `scripts/git/new-session.sh` — `--story-id` required
- `scripts/git/cleanup-session.sh` — refuse if state != done
