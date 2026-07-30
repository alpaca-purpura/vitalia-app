---
name: git-manager
description: >
  Git and GitHub workflow assistant for Nicolify (ap_sales_agent). Creates and manages branches,
  handles pull requests, resolves merge conflicts, generates changelogs, and manages releases and
  deployments. Use when the user asks to "create a branch", "sync with github", "push changes",
  "merge to main", "create a release", "make a PR", "resolve conflicts", "check git status",
  "deploy to production", "create a version", "write a changelog", or any git/GitHub related task.
  Also triggers on "quiero hacer un commit", "quiero pushear", "hacemos un release",
  "pasamos a producción", "nueva versión", "rama nueva".
disable-model-invocation: true
user-invocable: false
---

> [RETIRADO 2026-06-01] Este skill apuntaba al repo externo `alpacapurpura/ap_sales_agent` y usaba
> comandos git prohibidos por `git-safety.md` (`git pull --rebase`, `--force-with-lease`, rama
> `development`). El workflow git canónico de luana-platform (triple-branch
> `wip/{brand}` → `main` → `release`, commit por pathspec, delegación Haiku) lo cubre `/commit-push`.
> Para sync usar `scripts/git/sync-from-main.sh`.

## A dónde ir

- **Commit + push** → `/commit-push` (delega a Haiku, commit por pathspec, sin `git add .`)
- **Cierre de sesión / limpieza** → `/cierra-limpio`
- **Protocolo worktree / sesiones paralelas** → `/worktree-protocol`
- **Estado del repo y sync wip ↔ main** → `scripts/git/sync-from-main.sh` + `scripts/git/status-all.sh`
