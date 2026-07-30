# Worktree Strategy — Single-Hub default

> **Slim stub (context-rot pass 2026-05-30).** Cuerpo operativo completo en `.claude/skills/worktree-protocol/references/dual-strategy.md` — carga on-demand. **Origen:** 2026-05-27 (v2 cement 2026-05-28 ADR-009 — default invertido a hub único).

## Regla cardinal

Para paralelizar refinamiento + build dentro de la MISMA marca, **NO se crean worktrees separados**. Todas las sesiones corren sobre el **único worktree canónico** (hub), coordinadas por bucket locks M14 (`code:{module}` / `docs` / `tests`). Worktrees dedicados se reservan para: lift core, cross-cutting protocol, hot-fix aislado, u otra marca.

## Cuándo carga el detalle

- Necesitás setup de un worktree refine-lane en modo excepción (script + `.session.yaml`)
- Necesitás la tabla de naming convention de worktrees o la scope table
- Necesitás el workflow "no egoísmo" (bug visto en worktree ajeno) o el cross-worktree sync post squash-merge

## Anti-patterns (top 3 — lista completa en el detalle)

- ❌ Crear worktree separado refine-lane dentro de una marca como operación diaria (violación ADR-009 — el hub es el default)
- ❌ Worktree refine editando `{sistema}/backend/src/` o `{sistema}/frontend/src/` (viola scope discipline)
- ❌ Bug visto en otra worktree ignorado sin documentar en `{sistema}/docs/observed-bugs/`

## Referencias

- `.claude/skills/worktree-protocol/references/dual-strategy.md` — **cuerpo operativo completo** (setup ad-hoc, naming convention, no-egoísmo clause, cross-worktree sync, enforcement layers)
- `.claude/rules/parallel-safety.md` D2 + M14 — base topología + locks
- `.claude/rules/step-0-worktree.md` — manifest + verification
- `.claude/rules/git-safety.md` § Sync wip/{sistema} con main — post squash-merge sync
- `docs/architecture/{workspace.repo_prefix}-platform/ADR-009-single-hub-worktree.md` — decisión hub único
