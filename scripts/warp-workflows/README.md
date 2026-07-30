# Warp Workflows (mec. K)

Workflows portables Warp para ejecutar los scripts del worktree protocol desde la palette.

**SSoT:** `docs/process/parallel-sessions-protocol.md` § D7 + D14.

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
| `sync-check.yaml` | `sync-check` | Run `scripts/git/check-sync.sh` en cwd actual |
| `push-wip.yaml` | `push-wip` | Run `scripts/git/push-wip.sh` con prompt para branch |
| `new-session.yaml` | `new-session` | Run `scripts/git/new-session.sh` con prompts para BRAND/TYPE/SLUG |
| `cleanup-session.yaml` | `cleanup-session` | Run `scripts/git/cleanup-session.sh` con prompt para SLUG |
| `status-all.yaml` | `status-all` | Run `scripts/git/status-all.sh` (dashboard) |
| `regenerate-manifest.yaml` | `regenerate-manifest` | Run `scripts/git/regenerate-manifest.sh` |

## Para opencode users

Si usas opencode (no Claude Code), los Warp Workflows son tu canal principal para invocar mec. A (sync-check) y mec. L (push-wip) — Claude hooks no aplican en opencode.

Workflow recomendado al abrir nueva tab opencode:
1. `cd ~/Proyectos/luana-{brand}/` (canónico) o `~/Proyectos/luana-{brand}-{slug}/` (efímero)
2. Run `sync-check` workflow (verifica + auto-FF si trivial)
3. `opencode`

Antes de cada push:
1. Run `push-wip` workflow (advisory + push)

## Referencias

- `docs/process/parallel-sessions-protocol.md` § D14 (opencode parity)
- `docs/process/warp-multibrand-handbook.md` (manual operativo completo)
