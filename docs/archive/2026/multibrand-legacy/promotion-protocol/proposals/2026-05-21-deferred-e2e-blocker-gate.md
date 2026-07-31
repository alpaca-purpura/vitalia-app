---
proposal_id: 2026-05-21-deferred-e2e-blocker-gate
state: proposed
opened_date: 2026-05-21
opened_by: /pm-luana
ratified_by: null
ratified_date: null

# Origen
origin_learnings:
  - vitalia/docs/learnings/2026-05-21-auto-handoff-deferred-e2e-blocker.md   # severity: HIGH

origin_brands: [vitalia]    # caso origen único pero patrón aplica cross-brand

# Target — PROCESS LAYER, no engine package
target_package: null                                  # NO es engine package
target_module: process layer (.claude/rules/ + docs/process/)
target_files:
  - .claude/rules/story-closure-gate.md               # agregar Layer 8 (deferred-e2e/visual gate)
  - .claude/skills/dev-team/SKILL.md                  # Step 4.5 — verificar deferred count antes auto-handoff
  - .claude/skills/auditor/SKILL.md                   # Step 4 CHECKPOINTS template — checkbox C2 manual visual verification
  - docs/process/pm-redesign-2026-05.md               # § Conv 3 actualizar auto-handoff caveat deferred-e2e
  - docs/specs/templates/06-tickets-template.yaml     # validator categories field opcional
target_ep: null

# Impact assessment
semver_bump: null            # NO engine package, no semver
breaking_change: false       # forward-only post 2026-05-21 (legacy stories exempt)
brands_affected_consumers: [vitalia, nicolify, comunify, lupulo, saasora, inmoflow, retailly, fixia, guestly, fitflow]
brands_at_risk_regression: []   # process change, no code regression

# Lift plan
lift_estimated_effort: "30-60 min — solo edits a rules/skills MD"
lift_owner: /pm-luana                # process layer = /pm-luana directo, no /dev-team
arch_test_downstream_required: false # process change
migration_notes_required: false      # rule overlay forward-only
---

## 1. Patrón a promover

Nuevo Layer 8 en `story-closure-gate.md`: **deferred E2E/visual validator gate**.

Cuando `04-validators.yaml` lista validators de categoría `visual` o `e2e_smoke` que se marcan DEFERRED durante audit cycle (razón legítima: stack infra inestable, missing tokens, Turbopack issue, etc.), la cadena auto-handoff `developed → reviewing → done` NO procede automáticamente.

**Hard rule propuesta (forward-only post 2026-05-21):**

> Orchestrator (Opus) DEBE pausar en `developed` y emitir ping a Chris:
>
> 1. **Pausa en `developed`** — no auto-handoff a `/auditor`
> 2. **Ping explícito Chris:** "story X tiene N deferred E2E/visual validators — ratifica manual visual verification o reabro como `state: changes-requested`"
> 3. **Si Chris ratifica manual visual verification:** orchestrator levanta stack (`make dev-{brand}`), navega manualmente, captura screenshots de scenarios afectados, anexa a `06-audit/manual-verification.md` ANTES de proceder a auditor
> 4. **Si Chris dice "skip, mergeá igual":** marca learning con `severity: HIGH, deferred_verification_accepted_by: chris, risk: integration_bugs_possible`. Auto-emit a `{brand}/docs/learnings/` con risk acknowledgement.

**Origen story:** vitalia-slice-1-marketing shipped state=done con merge `fa921711` a main pero NO INTEGRADO a app real:
- `app/marketing/page.tsx` existe ✓
- Sidebar nav NO incluye link a Marketing ✗
- Dashboard sigue mostrando "Marketing·pronto" placeholder ✗
- Tailwind v4 tokens NO renderizan en runtime ✗

User no puede LLEGAR al `/marketing` porque sidebar no lo linkea. La story es **funcionalmente invisible**. Auditor APPROVED en 3 iter con C1-C5 GREEN porque tests unit + arch fitness + Gherkin coverage PASS. Pero E2E smoke marketing quedó DEFERRED CI por Turbopack stack instability ([[2026-05-20-docker-frontend-ram-turbopack-issue]]).

**Root cause:** la cadena auto-handoff cementada 2026-05-18 (`story-closure-gate.md`) asume implícitamente que **al menos UN gate verdadero de integración corre en cada merge**. Cuando E2E queda DEFERRED uniformemente (vitalia llevamos 2 stories consecutivas — copilot-tools-impl + marketing), el gate de integración nunca corre.

[[2026-05-21-auto-handoff-deferred-e2e-blocker]]

## 2. Por qué cross-brand

| Brand | Aplicabilidad | Razón |
|---|---|---|
| vitalia | origen | Caso reproducido 2 stories consecutivas (copilot-tools-impl 2026-05-18 + marketing 2026-05-21) |
| nicolify | aplica | Mismo stack Next.js + sidebar centralizada. Próxima story vulnerable. |
| comunify | aplica | idem stack. WIP recovery activo, design system pendiente — vulnerable. |
| lupulo | aplica | Placeholder bootstrap pendiente. Heredará gate desde día 1. |
| saasora / inmoflow / retailly / fixia / guestly / fitflow | aplica | 6 brands futuras bootstrap. Process gate aplicable universally. |

Este gap reproduce inevitablemente en cualquier brand que:
1. Use Next.js + Turbopack en dev
2. Tenga sidebar/nav centralizada que requiera updates explícitos al agregar rutas
3. Acepte E2E deferred como WARN

→ 10/10 brands son candidate. Process layer, NO engine package — promoción es edit de rules/skills MD, no code lift.

## 3. Análisis técnico

### Signature comparison

NO aplica (process layer, no code).

### Lift mechanism

Edits MD a:

1. **`.claude/rules/story-closure-gate.md`** — agregar sección "Layer 8 — Deferred E2E/visual gate":
   ```markdown
   ### Layer 8 — Deferred E2E/visual validators block auto-handoff

   Cuando `06-tickets.yaml` o `T-{n}-result.md` o `T-{n}-review.md` marca CUALQUIER
   validator de categoría `visual` o `e2e_smoke` como DEFERRED:
   - Orchestrator (Opus) MUST pause en `state: developed`
   - NO auto-handoff a `/auditor`
   - Emit ping Chris (verbatim template)
   - Chris ratifica: (a) manual visual verification → anexar screenshots a 06-audit/manual-verification.md → proceed | (b) skip + auto-emit learning HIGH severity
   ```

2. **`.claude/skills/dev-team/SKILL.md`** — Step 4.5 nuevo "Deferred validator check":
   ```markdown
   ### Step 4.5 — Deferred validator check
   Before emitir auto-handoff /auditor en Step 5:
   - grep 04-validators.yaml + T-{n}-result.md por categoría `visual` o `e2e_smoke` con status: DEFERRED
   - If count > 0 → STOP. Emit ping verbatim a Chris (template Layer 8).
   - Else → proceed Step 5 normal.
   ```

3. **`.claude/skills/auditor/SKILL.md`** — Step 4 CHECKPOINTS.md template addition:
   ```markdown
   ## C2 — Spec coverage
   - [ ] Gherkin matrix completed (Phase D)
   - [ ] All visual/e2e_smoke validators GREEN OR
   - [ ] Manual visual verification ran post-deferred (06-audit/manual-verification.md exists with screenshots)
   ```

4. **`docs/process/pm-redesign-2026-05.md`** — § Conv 3 update con caveat:
   > Conv 3 auto-handoff default proceeds EXCEPT cuando deferred E2E/visual presente → pause + Chris ratify (Layer 8 story-closure-gate).

5. **`docs/specs/templates/06-tickets-template.yaml`** — agregar enum de categorías validator:
   ```yaml
   acceptance:
     validators:
       - id: val-1
         category: e2e_smoke  # non_functional | functional | visual | e2e_smoke | agentic_eval
         must_pass: true
         deferred_allowed: false   # if true, Layer 8 ping required when deferred
   ```

### Risk assessment

| Riesgo | Severidad | Mitigación |
|---|---|---|
| Brand existente tiene story in-flight cuando rule cementa | Baja | Forward-only post 2026-05-21. Legacy stories exempt. |
| Orchestrator interpreta "deferred" semánticamente distinto | Media | Template verbatim ping + checklist explícito + Step 4.5 grep pattern documented |
| Chris flooded con pings deferred mientras stack infra inestable | Media | Encoraged path = arreglar root cause (Tailwind v4 diag, etc.) en lugar de skip indefinido. Auto-emit learning si skip recurrent. |
| Casos legítimos deferred bloqueados (refactor sin UI change) | Baja | Excepciones documentadas: service-only stories, pure refactor, hot-fix con repro_verified — N/A automático. |

## 4. Lift plan

### Pre-lift checklist

- [ ] ADR-008 unrelated (no dependency)
- [ ] Story `vitalia-slice-1-marketing-integration` ratifica scope (incluía T-mki-4 = update story-closure-gate.md Layer 8 — la coordina aquí)
- [ ] /pm-luana valida edits MD no rompen reading flow rules raíz

### Lift execution

1. /pm-luana edita los 5 files target (proceso directo, no /dev-team — es rules/skills MD)
2. Pre-commit hook valida no rompe schema (tests pre-commit existing)
3. Commit conventional `feat(process): cement Layer 8 deferred-e2e gate (cross-brand)`
4. Push wip/* worktree apropiado (probable wip/vitalia o wip/protocol-deferred-e2e-gate)
5. NO migration test downstream (process change, no code)
6. Rollback path: revert commit, brands continúan con paradigm v4 sin Layer 8

### Post-lift

- Vitalia próximas stories Slice 1 (pipeline + agenda + fidelización) heredan el gate automáticamente
- Nicolify / comunify / lupulo heredan inmediatamente (rule cardinal aplica forward-only)
- Brands futuras bootstrap heredan desde día 1
- Story `vitalia-slice-1-marketing-integration::T-mki-4` se vuelve obsoleta (este proposal cementa el patrón cross-brand, brand-local edit no necesario)

## 5. Decisión

**Recomendación `/pm-luana`:** APPROVED

**Razón:**

1. **Severidad HIGH del caso origen** — story shipped functionally invisible, auditor passed con C1-C5 GREEN. Sin gate, próximas stories Slice 1 (pipeline + agenda + fidelización) van a repetir mismo bug porque mismo Tailwind v4 issue persiste.
2. **Cross-brand inevitabilidad** — cualquier brand con Next.js stack reproduce el patrón. Lift NOW evita 10 incidentes futuros (1 per brand).
3. **Edit cost bajo** — 5 files MD, ~30-60 min. Cost/benefit obvio.
4. **No risk regression** — process change forward-only, no code touched.
5. **Aligns with paradigm v4.1 autonomy** — fortalece auto-handoff cadena agregando guard sin paralizar default forward-motion (default path = arreglar stack, no skip).

**Ratificación Chris:** _pending_

## 6. Bitácora

- 2026-05-21: opened state=proposed por /pm-luana (origen learning vitalia)
- Pending: Chris ratifica → state=accepted o feedback iteración

## 7. Cross-references

- Origin learning: `vitalia/docs/learnings/2026-05-21-auto-handoff-deferred-e2e-blocker.md` (severity HIGH, promotable yes)
- Related learning: `vitalia/docs/learnings/2026-05-20-docker-frontend-ram-turbopack-issue.md` (cause root deferred E2E)
- Story actual (deuda local): `vitalia/docs/product/stories/vitalia-slice-1-marketing-integration/checkpoint.md` (T-mki-4 se vuelve obsoleta post este proposal)
- Process SSoT actual: `.claude/rules/story-closure-gate.md` (Layer 1-7 existing, Layer 8 nuevo)
- Paradigm cementado: `docs/architecture/luana-platform/ADR-007-paradigm-v4.1-autonomy.md`
- Skills target: `.claude/skills/{dev-team,auditor}/SKILL.md`
- Template target: `docs/specs/templates/06-tickets-template.yaml`
