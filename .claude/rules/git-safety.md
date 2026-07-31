# Git Safety — Trunk-Based Policy

> **Slim stub (reescrita trunk-based 2026-07-31 — muere el triple-branch `wip → main → release`; worktrees/multi-sesión ya retirados).** SSoT del flujo completo (tabla situación→camino, releases actual+objetivo, checklist 2º dev, enforcement hooks): `docs/process/git-workflow.md` — load on-demand al mergear/release/dudar. **Origen:** reorg standalone 2026-07-31 (reemplaza S-GIT-STRATEGY-CORE 2026-05-15).

## Regla cardinal — trunk-based

| Ref | Rol | Ciclo de vida |
|---|---|---|
| `main` | Trunk — ÚNICO branch permanente, deployable siempre | Permanente. Directo solo docs/chores/config (Chris); stories entran por squash-merge |
| `story/{story-id}` | Branch de story, vida corta (horas) | Build agentic → review IA (`/code-review`) → squash-merge → **borrar** |
| `fix/{slug}` | Bugfix/hotfix chico | Idem story: squash-merge → borrar |
| tags `vX.Y.Z` | Prod deploy (OBJETIVO; hoy branches `release/vitalia-vX.Y.Z` — Actions deferred) | Tag anotado sobre `main` validado |

**Tier de riesgo** (auth · tenant-isolation · migraciones · pagos · comportamiento de agentes) → PR + review humano de Chris además del review IA. El merge de una story a done lo gatekea `/pm-vitalia` (story-closure-gate Fase F) — Claude NUNCA lo decide solo. **Push ≤30 min** si hay cambios significativos.

## Commits y stage

- **Conventional Commits**: `<type>(<scope>): <desc>`. Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `perf`, `ci`.
- **Stage por pathspec exacto:** `git add path/to/file`. NUNCA `git add .` / `-A` / `-u`. `git status` antes. NUNCA commitear `.env*`/credentials/secrets.
- **Squash-merge siempre** al integrar a `main` (1 commit por story/cambio).

## PROHIBIDO

- `git pull` en forma pull-merge o pull-rebase. **Única forma permitida: `git pull --ff-only` sobre branch limpio** (working tree clean). El ff falla → STOP, reportar — NO forzar merge.
- `git push --force` / `--force-with-lease` — **sin excepción**.
- `git commit --no-verify` — **sin excepción**. Amend de commits ya pusheados — **sin excepción**.
- `git revert` / `git reset --hard` sin aprobación explícita Chris.

**Si push non-fast-forward falla:** STOP. Reportar a Chris. NO resolver con pull-merge. **Cualquier excepción a PROHIBIDO requiere ratificación Chris.**

## Inicio de conversación (branch check)

```bash
git status --short && git branch --show-current && git log --oneline -3
```
`main` limpio → proceder (story nueva → crear `story/{id}`). `story/*`/`fix/*` limpio → proceder. Branch desconocido → reportar antes de tocar. Tree sucio propio → commit/stash. Tree sucio ajeno → NO tocar, reportar.

## Cuándo carga el detalle (`docs/process/git-workflow.md`)

- Vas a mergear una story a `main` / abrir PR / decidir si algo es tier de riesgo
- Release a prod (mecanismo actual `release/vitalia-vX.Y.Z` vs objetivo tags) o reactivación de CI
- Onboarding / setup del 2º dev (Team upgrade, branch protection, sentinel `.ci-parity-deferred`)

## Anti-patterns (top 4)

- ❌ Branch de story que vive días (trunk-based = horas; integrar chico y seguido)
- ❌ Merge-commit o rebase-merge a `main` (siempre squash) · dejar el branch sin borrar post-merge
- ❌ `git pull` a secas o pull-rebase "para sincronizar" (solo `--ff-only` sobre tree limpio)
- ❌ Story de tier de riesgo squash-mergeada sin PR + review humano

## Referencias

- `docs/process/git-workflow.md` — **SSoT del flujo completo** (situaciones, releases, hooks, 2º dev)
- `.claude/rules/git-haiku-delegation.md` — commit+push multi-file → delegar Haiku
- `.claude/rules/github-actions-deferred.md` — CI advisory mientras no haya servidor real
