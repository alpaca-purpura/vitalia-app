---
brand: vitalia
date: 2026-05-27
slug: dev-team-delegation-pattern-pending-cement
promotable: yes
applies_to_other_brands_potentially: [nicolify, comunify, lupulo, all]
target_core_package: .claude/skills/dev-team/SKILL.md (root)
blocked_by_scope_gate: true
---

# /dev-team SKILL.md update — delegation pattern + continuation (cement pending)

## What we learned

Durante autonomous chain de vitalia-fase2-lisa-marca (12 tickets, ~6h orchestration), descubrimos 4 patterns críticos para el `/dev-team` orchestrator que NO están en su SKILL.md:

### 1. Subagent_type matrix por tarea (HARD BAN general-purpose para domain tasks)

Delegar a `subagent_type` ESPECIALIZADO según dominio:
- Implementar BE → `builder-backend`
- Implementar FE → `builder-frontend`
- Implementar AGENTIC → `builder-agentic` (Opus mandatory)
- Run gates → `gate-runner` (Haiku)
- Build CONTEXT-BRIEF → `context-builder` (Haiku)
- Validate brief → `context-validator` (Haiku)
- Audit BE → `auditor-backend` (Opus)
- Audit FE → `auditor-frontend` (Opus)
- Audit AGENTIC → `auditor-agentic` (Opus)

NUNCA `general-purpose` para finalize (commit+push+result file write) — orchestrator hace Bash directo.

**Caso origen (caso 1):** delegué T-2 finalize a Haiku `general-purpose`. Stageó 5 archivos valeria-agenda WRONG. Recovery cost: 1 turn + reputation. Lesson: `general-purpose` no tiene domain awareness.

### 2. Agent continuation pattern

Cuando agent stalls mid-work (context exhaustion / API Overload / token budget):
1. Check `git status --short` first — partial work may be in tree
2. Preferir `SendMessage` para continuar el mismo agent (preserva context)
3. Spawn nuevo agent solo si SendMessage no available — prompt MUST cite partial work paths + remaining work verbatim
4. Document continuation en `T-{n}-impl-log.md § Continuation iter N`

**Caso origen (caso 2):** T-2 builder-backend ran out of context mid-cleanup. Initially I spawned a fresh agent without inspecting tree first. Lesson: tree inspection saves restarts.

### 3. API Overload handling

`anthropic.APIStatusError: Overloaded` common en chains largos. Cuando ocurre:
1. Preserve partial work (no restart)
2. Spawn continuation con explicit "previous work in tree" prompt
3. If overload persists >2 retries → escalate Chris

**Caso origen (caso 3):** auto-fix iter 2 builder died Overload after ~40 tool calls. Tree had marca_router.py partial fix uncommitted + 13 new test files untracked. Spawning continuation with explicit "partial work in tree" allowed completing the fix.

### 4. Orchestrator-level direct work vs delegation

PM coordinator (Opus) hace DIRECTAMENTE via Bash/Edit/Write:
- Git commits + push (más control que Haiku stage por nombre)
- Read context files (spec/arch/rules) cuando deciding scope
- Update checkpoint.md state transitions (1-2 line edits)
- Write CHECKPOINTS.md story-level + 07-merge.md (Fase F MERGE)

DELEGA via Agent tool:
- Implementación tickets → builder-*
- Quality gates → gate-runner
- Audit → auditor-*
- Context brief → context-builder

Justificación: Opus tokens ~5x más caros que Sonnet/Haiku. PM usa Opus para reasoning/orchestration; trabajos mecánicos van a Sonnet/Haiku specialists.

## Why blocked from cementing in /dev-team SKILL.md

Scope-gate hook en pre-commit bloquea modificaciones a `.claude/skills/` raíz desde branch `wip/vitalia` (brand-scoped worktree). Per `docs/process/worktree-protocol-v2-plan.md § CORE #4`, transversal model files requieren protocol worktree dedicado.

## Recommended action (Chris en morning)

1. Crear protocol worktree: `scripts/git/new-session.sh protocol exp dev-team-delegation-cement`
2. Editar `.claude/skills/dev-team/SKILL.md` agregando sección "Delegation pattern (cementado 2026-05-27)" + nuevos anti-patterns
3. Texto verbatim disponible en este learning file (sección "What we learned" arriba)
4. Commit + push protocol worktree
5. Cleanup session post-merge

## How to apply

Próximos `/dev-team` orchestrators (post cementación SKILL.md update) seguirán pattern correctamente sin re-learn. Esto reduce cost de futuros autonomous chains.

## Cross-brand relevance

Aplica IDÉNTICO a todas las brands (vitalia/nicolify/comunify/lupulo/futuras). Es paradigma transversal del `/dev-team` skill, no brand-specific. `promotable: yes` justified.

## Referencias

- `vitalia/docs/archive/2026/stories/vitalia-fase2-lisa-marca/07-merge.md` § "Promotion candidates" #3
- `vitalia/docs/archive/2026/stories/vitalia-fase2-lisa-marca/T-2-impl-log.md` (caso origen partial fix)
- `docs/process/worktree-protocol-v2-plan.md § CORE #4` (scope-gate enforcement)
