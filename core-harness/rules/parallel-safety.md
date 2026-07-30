# Parallel Safety (OBLIGATORIO)

> **Slim stub (context-rot pass 2026-05-30).** Detalle completo (sub-agent ban · sync KISS · bucket lock · opencode parity · scope per branch · N sesiones · conflict resolution · M14 v2 module-scoped · protocol worktree · Fase solo-bootstrap) en `docs/rules-detail/parallel-safety.md`. **Origen:** D1-D14 cement 2026-05-18. **tier: core (W5b 2026-06-09)** — la doctrina multi-sesión (M1-M15 · bucket locks · sync · single-hub) es agnóstica; los paths concretos del engine se escriben como `{slot}` (`{engine_prefix.python_glob}`, resuelto del seam `project.config.yaml`). La convención de worktrees `{workspace.worktree_root}/{workspace.repo_prefix}-{sistema}` usa el placeholder `{sistema}` (no un enum hardcodeado).

## Topología filesystem (D2)

| Path | Tipo | Branch | Scope |
|---|---|---|---|
| `{workspace.worktree_root}/{workspace.repo_prefix}-platform/` | PRINCIPAL | `main` | read-only (solo merges) |
| `{workspace.worktree_root}/{workspace.repo_prefix}-{sistema}/` | CANÓNICO **HUB único** (ADR-009) | `wip/{sistema}` ESTABLE (M12) | `{sistema}/**` · N sesiones con bucket locks M14 |
| `{workspace.worktree_root}/{workspace.repo_prefix}-{sistema}-{slug}/` | EFÍMERO sistema | `wip/{sistema}-{slug}` | `{sistema}/**` |
| `{workspace.worktree_root}/{workspace.repo_prefix}-{sistema}-hotfix-{slug}/` | EFÍMERO hotfix | `hotfix/{sistema}-{slug}` | `{sistema}/**` |
| `{workspace.worktree_root}/{workspace.repo_prefix}-core-{slug}/` | EFÍMERO core | `wip/core-{slug}` | `{engine_prefix.python_glob}/**` |
| `{workspace.worktree_root}/{workspace.repo_prefix}-protocol-{slug}/` | EFÍMERO protocol | `wip/protocol-{slug}` (SCOPE_GATE_SKIP=1) | cross-cutting: `.claude/**`, `docs/process/**`, `tools/**`, `Makefile` |

## Reglas M1-M14 (vigentes)

| # | Regla (1-liner) |
|---|---|
| M1 | Sesiones paralelas = branches DISTINTOS — EXCEPTO mismo canónico con bucket lock M14 |
| M2 | SSoT (BACKLOG, MEMORY, PORTFOLIO) SOLO `/pm-{sistema}` o `/pm-{platform}`. Builders nunca |
| M3 | Tests/contenedores/migrations SECUENCIAL por sistema. Max 1 stack de contenedores por sistema |
| M4 | Claim by commit: state change en checkpoint.md + commit/push inmediato pre-claim |
| M5 | NO pull · NO force push · NO revert sin aprobación · Push non-FF → STOP |
| M6 | Bootstrap PM pregunta story activa antes proceder |
| M7 | Subagentes paths PRIMARIOS story + read all + extend-no-destroy ajenos |
| M8 | Tocar archivos otra sesión OK si leés primero + append/extend, no replace |
| M9 | **REVOCADA v2:** Sub-agents NO crean worktrees. Trabajan in-place sobre cwd del caller |
| M10 | `wip/*` = autosave. NO stash >30 min |
| M11 | NUNCA >30 min sin push si hay cambios significativos |
| M12 | `wip/{sistema}` ESTABLE (no rota story-by-story). Efímero SOLO por pedido explícito Chris |
| M13 | Scope per branch enforced (pre-commit §13). Cross-sistema mixing PROHIBIDO |
| M14 | N sesiones mismo cwd con lock por bucket `docs`/`tests`/`code`/`code:{module}`. Módulos distintos paralelos = OK; mismo módulo serializa. Commit por pathspec (índice compartido) |
| M15 | **Sweep-guard (HB-31, cement 2026-06-04):** `scripts/git/multi-session-scope-guard.sh` (pre-commit) BLOQUEA un commit que stagea el scope EXCLUSIVO de ≥2 sesiones VIVAS distintas (story-folder + módulo). Paralelo varias sesiones same-hub = **PERMITIDO** (Chris revocó "no 2 /dev-team" para acelerar); lo prohibido es la contaminación cross-sesión (`git add -A/-u/.` que barre lo ajeno). Fail-OPEN + override `MULTI_SESSION_ACK=1` |

## Session start / cierre

```bash
git status --short && git branch --show-current && git log --oneline -3
git worktree list && scripts/git/status-all.sh
scripts/git/sync-from-main.sh --check   # sync KISS (solo reportar)
```

Cierre (`"eso es todo"` / `/cierra-limpio`): `git status` → stage por nombre exacto → commit → push → reportar SHA → si efímero + done → `cleanup-session.sh`.

**≥2 sesiones `claude` concurrentes** → `export HARNESS_LANE=<único>` ANTES de lanzar claude (aísla el perfil del Chrome DevTools MCP; sin lane distinto → colisión `SingletonLock` → toda tool-call de Chrome falla). Detalle: § Chrome DevTools MCP / HB-73.

## Prohibido

- `git pull` · `git fetch && merge` automático · `git push --force` / `--force-with-lease`
- `git revert` o `git reset --hard` sin aprobación · `git add .` / `-A` / `-u` · `git commit --no-verify`
- Editar código en PRINCIPAL · Misma branch en 2 worktrees · `make dev-{sistema}` en 2 worktrees mismo sistema
- Builders editando SSoT · `/pm-{sistema-X}` desde worktree sistema Y · Sub-agent crea worktree (M9)
- Lift core sin promotion proposal accepted

## Cuándo carga el detalle

- Setup/troubleshoot bucket locks M14 (scripts, lock files, PID cleanup)
- Sub-agent worktree ban enforcement (arch fitness test + grep isolation:)
- Scope per branch table completa + SCOPE_GATE_SKIP procedure
- opencode parity (Warp Workflows equivalentes a hooks Claude Code)

## Referencias

- `docs/rules-detail/parallel-safety.md` — **detalle completo**
- `docs/process/parallel-sessions-protocol.md` — SSoT D1-D14
- `docs/architecture/{workspace.repo_prefix}-platform/ADR-{004,005,009}*.md` — triple-branch + worktree + single-hub
- `.claude/rules/{git-safety,git-haiku-delegation,step-0-worktree,worktree-dual-strategy}.md`
- `scripts/git/{new-session,cleanup-session,status-all,sync-from-main,session-lock}.sh`
