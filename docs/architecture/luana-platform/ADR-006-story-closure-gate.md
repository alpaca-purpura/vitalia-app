# ADR-006 — Story Closure Gate (Conv 3 auto-handoff)

> **Renumber note:** Originalmente ADR-005 durante cement-session 2026-05-18. Renombrado a ADR-006 pre-merge porque main concurrentemente introdujo `ADR-005-worktree-policy.md` (commits af8dfc3 + 25bd3bf). Conflicto numérico resuelto.

**Status:** Accepted
**Date:** 2026-05-18
**Deciders:** Chris (Luana founder) + `/pm-vitalia` + `/pm-luana` (process owner)
**Origen:** caso vitalia 2026-05-18 — `vitalia-slice-1-infra-cross-cutting` developed sin auditar/mergear, `vitalia-copilot-tools-impl` arrancó en mismo worktree (2 stories abiertas simultáneamente).

## Context

El paradigm v4 (pm-redesign 2026-05-06) introdujo el ciclo 3 conversaciones: Discovery → Build → Review+Merge. Conv 3 quedó descrita como "Chris triggered manualmente para controlar gasto Opus". Esta frase apareció embebida en:

1. `CLAUDE.md` § Flujo extremo-a-extremo + tabla cost-routing
2. `docs/process/pm-redesign-2026-05.md:272`
3. `.claude/skills/dev-team/SKILL.md:10` (frontmatter description YAML)
4. `.claude/skills/auditor/SKILL.md:3` (frontmatter description YAML)

Cuatro puntos documentales le decían a `/dev-team` "tu responsabilidad termina en `state: developed`. Chris dispara `/auditor` cuando quiera". El builder cumplió la instrucción al pie de la letra: cuando Chris dejó la sesión correr autónomamente, `/dev-team` interpretó "siguiente story ready disponible" como next acción válida.

### Síntoma operacional (2026-05-18 vitalia)

```
Worktree wip/vitalia-slice-1-shipping
├── Story A: vitalia-slice-1-infra-cross-cutting
│   state: developed   (10 tickets pushed, validators GREEN)
│   → NUNCA auditada, NUNCA mergeada
└── Story B: vitalia-copilot-tools-impl
    state: developing  (4 tickets pushed sobre código de A no validado)
    → arrancada sin cerrar A
```

Dos stories abiertas en mismo worktree. Story B construye sobre infraestructura de Story A que no pasó auditoría — si A tiene bugs, B hereda riesgo invisible.

### Costo real del bug

- Si A pasa auditoría limpia → cero costo, suerte.
- Si A requiere CHANGES_REQUESTED → B basada en código no validado, probable rework de B también.
- Acumulación de stories "developed" sin auditar → drift entre código y SSoT funcional creciente.
- Worktree branch name (`wip/vitalia-slice-1-shipping`) hospedando >1 story → cleanup-session ambiguo.

## Decision

**Conv 3 default = AUTO-HANDOFF en cadena `/dev-team → /auditor → /pm-{brand} merge`.** Sin Chris-trigger manual obligatorio.

Excepción explícita opt-in: `checkpoint.md::defer_audit: true` con razón documentada + ratificación Chris. Mientras `defer_audit: true`, la story NO cuenta contra WIP cap `developed ≤ 1` (es excepción cementada).

Concretamente:

1. **`/dev-team` Step 5/6 final:** cuando todos los tickets pushed + validators GREEN, emite handoff explícito a `/auditor` (verbatim line). Refuse pickup de tickets de otras stories hasta current `done` o `defer_audit: true`.

2. **`/auditor` Phase D + Step 5 final:** Phase D nueva = gherkin verification matrix (cada scenario de `01-spec.md` → test path → status). APPROVED dispara handoff explícito a `/pm-{brand}` merge (verbatim line).

3. **`/pm-{brand}` bootstrap Step 0:** escanea `{brand}/docs/product/stories/*/checkpoint.md`. Si alguna en state ∈ {developed, reviewing} en worktree activo Y sin defer_audit → REUSE THAT FIRST, refuse menu (a) nueva story.

4. **Templates:** `06-tickets-template.yaml` gana `gherkin_coverage` field (scenario → test paths) mandatory post-cement-date. `07-merge-template.md` cementa 5 secciones obligatorias.

5. **Hooks:** `pre-commit` Section 12 bloquea stage de files de story B si story A pending. `cleanup-session.sh` refuse remove worktree si state ≠ done. `new-session.sh` requiere `--story-id`.

6. **Naming convention:** `wip/{brand}-{story-padre-id}` exact, no slugs ambiguos.

## Rationale

### Por qué auto-handoff y no cap numérico

Considerada alternativa "max 3 audits auto-disparados por session, después requiere ratify Chris". Rechazada — recrea el bug exacto (cuarta story queda colgada en developed). Cap implícito = mismo agujero, distinto número.

Gate ABSOLUTO con escape valve EXPLÍCITO (`defer_audit: true`) es el patrón correcto:
- Default seguro (sigue el ciclo)
- Excepción explícita controlada (no implícita por inactividad)
- Si defer_audit=true documentado, `/pm-{brand}` bootstrap recuerda esa deuda en TODA sesión futura

### Por qué el control de costo Opus original ya no aplica

La frase "Chris manual para controlar gasto Opus" era de la era pre-paradigm-v4-cost-routing. Post-routing:

- `/dev-team` corre Sonnet/qwen-opencode default (R23 — Opus solo AGENTIC production_code: true)
- `/auditor` sub-fixes lint/format puede ser Haiku-eligible (futuro)
- `/auditor` categories C1-C3 + auditor-agentic son Opus pero son la fracción de costo razonable
- gate-runner es Haiku
- context-builder es Haiku

Control de costo real = cost-routing, no manual-trigger. Manual-trigger era conservadurismo redundante.

### Por qué docs en ambos (07-merge.md + capability YAML)

- `07-merge.md`: artifact de cierre frozen — congela la run específica de esta story (gherkin matrix snapshot, comando E2E ejecutado, capabilities updated paths). Es histórico.
- Capability YAML `verification.commands` + `verification.gherkin_evidence`: SSoT vivo — comandos canónicos reusables para re-verificar la capability cuando se quiera (audits cuatrimestrales, regresiones, brands consumers).

Splitting evita el SSoT-dilemma: si solo está en 07-merge.md, la capability queda muda. Si solo está en capability YAML, perdés la traza de la run original.

### Por qué 1 worktree = 1 story padre estricto (NO mezcla cross-outcome)

Sub-stories del mismo outcome pueden compartir worktree (mismo branch wip/{brand}-{outcome}) pero cada sub-story pasa las 6 fases antes que la siguiente arranque. Razón: el outcome tiene cohesión semántica (mismo padre `01-spec.md` consolidado, mismo `03-arch.md`) — separarlos en N worktrees fragmenta navegación y rebase.

Stories de outcomes distintos = worktrees distintos. Razón: cero cohesión semántica + colisión Lookback `.claude/` rules.

## Consequences

### Positive
- Stories no acumulan deuda invisible en `developed` (worktree cleanup natural)
- Cross-brand: paradigm uniforme — todas las brands heredan el gate (lift root)
- Gherkin scenarios trazables a tests específicos (no orfandad spec/test)
- `07-merge.md` 5 secciones = documentación de funcionalidad shipped consistente cross-brand
- Bootstrap `/pm-{brand}` siempre ve deudas reales (no surprise)
- Cleanup-session.sh seguro (no remueve worktree con WIP no resuelto)

### Negative
- Opus cost up — auditor auto-disparado en lugar de manual. Mitigado por cost-routing per phase (sub-auditors Sonnet eligible para FE/BE deterministico).
- Workflow más rígido — `defer_audit: true` requiere ratificación Chris explícita (no skip silencioso).
- Templates más verbose — `gherkin_coverage` field adds friction al `/architect` cerrar 06-tickets.
- Sub-stories cross-outcome ban — fuerza split worktree si Chris quiere parallelizar.

### Neutral
- Pre-commit hook adds latency mínima (escanea checkpoint.md de stories en worktree, ~50ms).
- Templates retroactividad solo forward (post-cement-date) — stories pre-decreto sin gherkin_coverage no rompen.

## Affected systems

### Files modificados (cement batch)
- `CLAUDE.md` — secciones Conv 3 + cost-routing + flujo 3-conv
- `docs/process/pm-redesign-2026-05.md` — Conv 3 narrative + tabla 10 estados
- `.claude/skills/dev-team/SKILL.md` — frontmatter + Step 5/6 auto-handoff
- `.claude/skills/auditor/SKILL.md` — frontmatter + Phase D + Step 5 merge handoff
- `.claude/skills/pm-{vitalia,nicolify,comunify,lupulo,luana,saasora,inmoflow,retailly,fixia,guestly,fitflow}/SKILL.md` — bootstrap Step 0
- `.claude/skills/_pm-brand-template/SKILL.md` — scaffold incluye gate
- `docs/specs/templates/06-tickets-template.yaml` — `gherkin_coverage` field
- `docs/specs/templates/07-merge-template.md` — 5 secciones cementadas
- `scripts/git-hooks/pre-commit` — Section 12 story-closure-gate
- `scripts/git/new-session.sh` — `--story-id` flag required
- `scripts/git/cleanup-session.sh` — refuse if state ≠ done

### Files creados
- `.claude/rules/story-closure-gate.md` — hard rule SSoT
- `docs/process/story-closure-gate.md` — rationale + case study
- `docs/architecture/luana-platform/ADR-006-story-closure-gate.md` — este file

### Brands impactadas
Todas las activas: vitalia, nicolify, comunify, lupulo. Las 6 pendientes bootstrap (saasora, inmoflow, retailly, fixia, guestly, fitflow) heredan via `_pm-brand-template`.

### Operational test
Cleanup deuda vitalia (Option A linear):
1. PAUSE `vitalia-copilot-tools-impl` checkpoint state developing→ready con rewind reason
2. Run `/auditor vitalia-slice-1-infra-cross-cutting` (auto Phase D gherkin)
3. Fix-loop si CHANGES_REQUESTED (cap 2)
4. Update capabilities/* per modules tocados por infra
5. Write `07-merge.md` 5 secciones
6. Transition `reviewing → done` + squash-merge `wip/vitalia-slice-1-shipping → main`
7. Después continuar copilot-tools-impl en worktree nuevo `wip/vitalia-copilot-tools-impl`

Si infra cierra limpia con artifacts completos → gate operacional. Si falla, debug gate antes de aplicar a más stories.

## Compliance

### Migration path stories existentes
- Stories en `developed`/`reviewing` ANTES de cement-date (2026-05-18) → quedan exentas de gherkin_coverage gate (auditor usa regla anterior).
- Stories que transitan POST-cement-date → deben cumplir gate completo.

### Backwards compatibility
- Stories `done` archived no se tocan.
- Capability YAMLs existentes ganan `verification.*` fields opcionales — no breaking.
- `06-tickets.yaml` legacy stories sin `gherkin_coverage` → auditor warning (no FAIL) si transit post-cement.

## Alternatives considered

### Alt 1: Mantener "Chris manual trigger" + alarma proactiva al bootstrap

`/pm-{brand}` bootstrap detecta stories developed pendientes → ping Chris. Pero `/dev-team` sigue libre para tomar nueva story si Chris no respondió.

**Rechazada** — recrea el bug. Si Chris no está in-chat (sesión autónoma overnight), `/dev-team` decide sin gate.

### Alt 2: Cap numérico audits auto-disparados (max 3)

Auto-handoff hasta 3 audits por sesión, después requiere Chris ratify.

**Rechazada** — cap implícito = mismo bug, distinto número. La cuarta story queda colgada.

### Alt 3: Worktree por sub-story estricto (1 sub-story = 1 worktree)

Cada sub-story tiene su propio worktree. Cero ambigüedad.

**Rechazada** — fragmenta navegación + rebase pesado. Sub-stories del mismo outcome consumen `01-spec.md` consolidado + `03-arch.md` consolidado del padre — separarlos físicamente rompe SSoT.

### Alt 4: Promotion proposal en docs/promotion-protocol/

Tratar este cambio como lift formal.

**Rechazada** — `docs/promotion-protocol/proposals/` es estrictamente para code-level lifts brand→core. Process/paradigm cambios van por ADR + learnings + commit batch ratify Chris.

## References

- `.claude/rules/story-closure-gate.md` — hard rule
- `docs/process/story-closure-gate.md` — rationale + case study
- `docs/process/pm-redesign-2026-05.md` — paradigm v4 actualizado
- `docs/process/learnings.md` — 2026-05-18 entry promotable: yes
- `docs/architecture/luana-platform/ADR-002-cicd-multibrand.md` — predecesor multibrand
- `docs/architecture/luana-platform/ADR-004-git-branching-and-environments.md` — triple-branch policy (worktree convention)
