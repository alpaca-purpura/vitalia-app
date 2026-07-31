# Warp Workflows (mec. K)

Workflows portables Warp para ejecutar los scripts git del repo desde la palette.

> Simplificado 2026-07-31 (repo standalone single-brand, worktrees retirados):
> quedan solo `push-wip` y `status-all`.

## Cómo importar a Warp

Cada `.yaml` aquí es un Warp Workflow. Para importar:

1. Abrir Warp
2. `Cmd+Shift+R` → Workflows
3. New Workflow → paste contenido del yaml
4. Save (queda en `~/.warp/workflows/`)

O via UI: Settings → Workflows → Import.

## Workflows incluidos

| File | Atajo Warp | Acción |
|---|---|---|
| `push-wip.yaml` | `push-wip` | Run `scripts/git/push-wip.sh` con prompt para branch |
| `status-all.yaml` | `status-all` | Run `scripts/git/status-all.sh` (dashboard del repo) |

## Para opencode users

Si usas opencode (no Claude Code), los Warp Workflows son tu canal para invocar
mec. L (push-wip) — Claude hooks no aplican en opencode.

Antes de cada push:
1. Run `push-wip` workflow (advisory + push)
