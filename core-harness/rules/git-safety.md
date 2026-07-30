# Git Safety — Triple-Branch Policy

> **Slim stub (context-rot pass 2026-05-30).** Flujo completo, procedimiento de sync `wip/{sistema}↔main`, Fase solo-bootstrap detalle + tabla CI/CD en `docs/rules-detail/git-safety.md` — load on-demand al mergear/sync. **Origen:** multisistema reorg 2026-05-15 (S-GIT-STRATEGY-CORE).

## Triple-branch policy

| Branch | Rol | Quién la usa |
|---|---|---|
| `wip/{slug}` | Autosave iterativo, commits frecuentes | Cada sesión en su worktree |
| `main` | Integración + staging (deployable) | Squash-merge desde wip/* |
| `release/{sistema}-vX.Y.Z` | Producción sistema-específica, inmutable | Desde main validado |

**WIP safety net:** squash-merge a `main` (~80%) · push `wip/*` autosave (~15%) · `git stash` <30 min mismo worktree (~5%). **M11:** nunca >30 min sin push si hay cambios significativos.

## Commits y stage

- **Conventional Commits**: `<type>(<scope>): <desc>`. Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `perf`, `ci`, `wip`.
- **Stage por nombre exacto:** `git add path/to/file`. NUNCA `git add .` / `-A` / `-u`. `git status` antes. NUNCA commitear `.env*`/credentials/secrets.

## PROHIBIDO (con excepciones documentadas en el detalle)

- `git pull` (cualquier forma) — **sin excepción**. Non-fast-forward push → STOP, reportar.
- `git fetch && merge` automático sin ratificación — salvo sync `wip/{sistema}↔main` (ver detalle).
- `git push --force` — **sin excepción**. `--force-with-lease` PROHIBIDO por default (excepción: reset post squash-merge 0-ahead).
- `git revert` / `git reset --hard` sin aprobación explícita Chris.
- `git commit --no-verify` — **sin excepción**. Amend de commits ya pusheados — **sin excepción**.
- `SCOPE_GATE_SKIP=1 git commit` — relajado en Fase solo-bootstrap (razón en commit body); fuera de esa fase requiere worktree protocol o merge sync legítimo.

**Si push non-fast-forward falla:** STOP. Reportar a Chris. NO hacer git pull. **Cualquier excepción a PROHIBIDO requiere ratificación Chris** (o estar documentada como caso permitido en el detalle).

## Inicio de conversación (branch check)

```bash
git status --short && git branch --show-current && git log --oneline -3
```
`main`/`wip/*` limpio → proceder. `release/*` → solo hotfix urgente. Desconocido → switch main o crear `wip/*`. Tree sucio propio → commit/stash. Tree sucio ajeno → NO tocar, reportar.

## Referencias

- `docs/rules-detail/git-safety.md` — **flujo + sync procedure + Fase solo-bootstrap + CI/CD table**
- `.claude/rules/git-haiku-delegation.md` — commit+push multi-file → delegar Haiku (3 destinos)
- `.claude/rules/parallel-safety.md` · `docs/architecture/{workspace.repo_prefix}-platform/ADR-{004,005,009}*.md`
