---
date: 2026-06-12
slug: reset-hard-post-squash-borra-wip-ajeno
promotable: yes
applied: pending
---

# reset --hard post-squash borró 73 archivos WIP de sesiones paralelas (hub compartido)

**Qué pasó:** al cerrar el squash wip/vitalia→main, el orchestrator ejecutó la excepción autorizada `git reset --hard origin/main` verificando SOLO el diff entre ramas (0) — pero el working tree compartido tenía 73 archivos M sin commit de sesiones paralelas (servicios refining ronda 4, ds-showcase, embudo archive, contract-gate HB-42 WIP). Recuperación ~95% vía blobs dangling (las sesiones habían stageado → `git fsck --unreachable`), pero ediciones unstaged posteriores al último stage se perdieron.

**Why:** la excepción de git-safety detail valida "wip tiene 0 commits propios" — condición de RAMA. En el hub único (ADR-009) el working tree es COMPARTIDO: el reset destruye WIP ajeno aunque la rama esté limpia.

**How to apply (gate propuesto):** el procedimiento post-squash MUST anteponer: `git status --short | grep -v '^??' | wc -l` → si >0, **stash etiquetado obligatorio** (`git stash push -m "pre-reset-squash $(date)"`) ANTES del reset, y reportar a las sesiones vivas (locks). Candidato a script `scripts/git/safe-reset-postsquash.sh` + línea en git-safety detail § Excepciones.

**Recuperación (receta que funcionó):** `git fsck --unreachable --no-reflogs | grep blob` → `git cat-file -p` + clasificación por contenido/frontmatter → restaurar versión más reciente. Los blobs existen SOLO si hubo staging.
