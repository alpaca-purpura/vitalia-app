# Story Closure Gate

> **Slim stub (context-rot pass 2026-05-30).** Detalle completo (07-merge schema verbatim · gherkin_coverage · F.3 cap ledger · v3.1/v3.2 enforce tables · WIP cap v2 · defer_audit schema · 7 enforcement layers · caso origen) en `docs/rules-detail/story-closure-gate.md` — load on-demand. **Origen:** caso de marca 2026-05-18. **tier: core.**

## Regla cardinal

Story en `state: developed` o `reviewing` **NO puede abandonarse** para arrancar otra story (mismo módulo). Ciclo único (★ proceso v5 2026-06-05 inserta **G** + **R** entre developed y auditor — cero estado/eje nuevo: G/R son `phase` de `developed`):

```
ready → developing → developed ─[G Chris-verify]─[R reconcile]→ reviewing → done
                         │                                          └─ APPROVED→/pm-{sistema} merge
                         └─ default: pausa-y-ofrece (phase: AWAIT_CHRIS_VERIFY)
                            autonomous_mode: true → corre a /auditor sin pausa
```

`/dev-team` cierra `developed` → **G (Chris-verify)** salvo `autonomous_mode: true` → **R (reconcile /pm-{sistema})** → AUTO-HANDOFF `/auditor`. APPROVED → `/pm-{sistema}` merge. Sin `defer_audit: true` el gate es ABSOLUTO.

## 8 fases (resumen · A→F + G/R insertadas)

| Fase | Owner | Transition |
|---|---|---|
| A — DEV | `/dev-team` | `ready → developing → developed` |
| **G — CHRIS-VERIFY** ★ | Chris + `/dev-team` | `developed` + `phase: AWAIT_CHRIS_VERIFY` (default pausa-y-ofrece; **salta si `autonomous_mode: true`**). Chris ejerce el kit live → `chris_verify.signoff`. Scope dinámico + **piso HARD happy-path** (func. nueva → core construido) |
| **R — RECONCILE** ★ | `/pm-{sistema}` | spec/arch/validators/cap ⟵ realidad + cambios ratificados; escribe `reconciled: true`; congela ledger `deferred` → spawnea historias visibles. **★ 04-validators NO es solo el checkpoint (HB-79):** todo validator de scope DEFERIDO/descopado en G → `must_pass: false` + tag `deferred:` (si no, queda verde-fantasma latente que el auditor corre contra código inexistente). |
| B — AUDIT | `/auditor` (auto-handoff) | `developed → reviewing` — lee docs **RECONCILIADOS** + `chris_verify.signoff` (no revierte scope ratificado) |
| C — FIX-LOOP | `/dev-team` si CHANGES_REQUESTED | cap 2 iter |
| D — GHERKIN | `/auditor` Phase D (embedded en B) | gherkin-matrix.md |
| E — DOCS | `/pm-{sistema}` | cap YAML + modules MD |
| F — MERGE | `/pm-{sistema}` | `reviewing → done` · REFUSE sin `chris_verify.signoff` (funcional) · 07-merge.md · archive story R2 |

**WIP cap v2 (module-scoped):** ≤ 1 story en `developing/developed/reviewing` por `code:{module}` bucket. Módulos distintos paralelos = OK. **Excepciones que NO cuentan contra `developed ≤ 1`:** `defer_audit: true` (ratificado Chris) **y `phase: AWAIT_CHRIS_VERIFY`** (story en G parkeada esperando a Chris — si no, una story en verify deadlockea otra del mismo módulo). Ambas liberan el bucket para que otra story del módulo avance.

## G/R schema + signoff consolidado (chris_verify) ★ proceso v5

```yaml
# checkpoint.md — G vive como phase de developed (sin estado nuevo)
state: developed
phase: AWAIT_CHRIS_VERIFY          # o AUTONOMOUS si autonomous_mode: true
chris_verify:
  required: true                   # false sólo si autonomous_mode o bugfix sin pedido
  signoff: null                    # → {by: Chris, date, result: SATISFIED|SATISFIED_WITH_FOLLOWUPS|REJECTED, notes, open_items}
  rounds: []                       # cada corrección anotada + cómo se resolvió o a qué historia fue (= allowlist de scope ratificado para el auditor)
reconciled: false                  # /pm-{sistema} lo pone true en R (precondición que el auditor LEE antes de empezar)
```

- **Un solo signoff:** `chris_verify.signoff` reemplaza el viejo `demo_signoff` (movido de F a G — `definition-of-done-live-verify.md` §5). NO se duplica F+G. La Fase F REFUSE-merge lee `chris_verify.signoff.result ∈ {SATISFIED, SATISFIED_WITH_FOLLOWUPS(severity≤medium)}`.
- **`reconciled: true`** es precondición de B (auditor): sin él, el auditor REFUSE empezar (lee un spec stale).
- **`chris_verify.signoff.rounds`** = allowlist de cambios que Chris ratificó: un scope-delta que NO está en `rounds` SIGUE siendo finding del auditor (no degenera en "no revertir NINGÚN scope").

## Cuándo carga el detalle

- `/pm-{sistema}` Fase F.3 (cap_change_type: new/fix/extend/derive → lógica + v3.1/v3.2 enforce tables)
- Necesitás el schema verbatim de `07-merge.md` 5 secciones o `defer_audit` en checkpoint.md
- Troubleshoot enforcement layers (hooks · cleanup-session · templates)

## Anti-patterns (top 6 — lista completa en el detalle)

- ❌ `/dev-team` cierra `developed` + arranca ticket de otra story sin defer_audit (bug origen)
- ❌ `/pm-{sistema}` ofrece "nueva story" con story pendiente audit sin defer_audit
- ❌ `/auditor` cierra APPROVED sin handoff explícito a `/pm-{sistema}` merge
- ❌ `/dev-team` auto-handoff directo a `/auditor` cuando `!autonomous_mode` (debe pausar en G · proceso v5)
- ❌ contar una story en `phase: AWAIT_CHRIS_VERIFY` contra `developed ≤ 1` (deadlockea otra del módulo)
- ❌ duplicar el signoff (`demo_signoff` en F + `chris_verify` en G) — un solo campo `chris_verify.signoff`, antes del auditor
- ❌ `/auditor` empieza sin `reconciled: true` (lee spec stale, revierte lo que Chris ratificó)

## Referencias

- `docs/rules-detail/story-closure-gate.md` — **detalle completo**
- `docs/process/story-closure-gate.md` — rationale + case study
- `docs/architecture/{workspace.repo_prefix}-platform/ADR-006-story-closure-gate.md` — decisión
- `.claude/rules/sistema-docs-schema.md` § R2 — archive path canónico
