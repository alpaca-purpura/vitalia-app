# Git Safety — detail (moved from .claude/rules/ 2026-05-30, load on-demand)

Detalle del flujo + procedimiento de sync. La rule slim (`.claude/rules/git-safety.md`) tiene la policy cardinal + PROHIBIDO. Esto se lee on-demand cuando hay que mergear/sync.

## Flujo completo (ejemplo)

```bash
# 1. Nueva sesion paralela (cada sesion su worktree + branch wip/*)
git worktree add ../luana-docker wip/docker-compose-multibrand

# 2. Trabajar + commitear frecuentemente en wip/*
cd ../luana-docker
git add scripts/docker-compose.dev.yml
git commit -m "wip(docker): base compose multibrand services"
git push origin wip/docker-compose-multibrand

# 3. Integrar a main via squash-merge (desde workdir principal)
cd /home/chalreme/Proyectos/luana-platform
git checkout main
git merge --squash wip/docker-compose-multibrand
git commit -m "feat(docker): compose multibrand servicios base"
git push origin main

# 4. Produccion: branch release/* desde main validado
git checkout -b release/vitalia-v0.3.0
git push origin release/vitalia-v0.3.0
```

## Worktrees per sesion paralela

```bash
# Patron canonico (obligatorio para sesiones paralelas)
git worktree add ../luana-{slug} wip/{slug}-{short-desc}

# Limpiar worktree despues de merge a main
git worktree remove ../luana-docker
git branch -d wip/docker-compose-multibrand
```

Git bloquea automaticamente que dos worktrees tengan el mismo branch — colision de WIP imposible por diseno. El ban historico de worktrees fue revocado en 2026-05-15 (D2 S-GIT-STRATEGY-CORE).

## Sync `wip/{brand}` con `main` post squash-merge

**Origen:** caso 2026-05-27. Después de squash-merge `wip/vitalia → main`, los demás canónicos (`wip/comunify`, `wip/nicolify`, `wip/lupulo`) quedaban atrasados sin procedimiento explícito de re-sync. Lockfiles + reglas + arquitectura cementations vivían SOLO en main hasta que cada brand sincronizara → riesgo de drift cross-brand silencioso.

**Regla cardinal:** después de cada squash-merge `wip/{brand_A} → main`, los demás canónicos brand activos **deben sincronizarse con main en la sesión siguiente** (no obligatorio inmediato, pero antes de arrancar trabajo nuevo en la brand).

### Decisión: qué hacer según commits propios del wip target

```bash
cd ~/Proyectos/luana-{brand_target}
git fetch origin
git log --oneline origin/main..HEAD | wc -l   # commits ahead = trabajo propio del brand
```

| Ahead | Procedimiento | Razón |
|---|---|---|
| **0** | **Reset hard a main** + push `--force-with-lease` | Sin trabajo que preservar. Limpia y rápida. |
| **≥1** | **Merge `origin/main` en wip/{brand}** + push (no force) | Preserva los commits propios + agrega merge commit que trae main. |

### Procedimiento detallado

**Caso A — 0 ahead (reset hard limpio):**

```bash
cd ~/Proyectos/luana-{brand_target}
git stash push --include-untracked -m "{brand}-pre-reset-$(date +%Y-%m-%d)"  # si hay uncommitted
git fetch origin
git diff HEAD origin/main --stat   # verificar diff antes (sanity check)
git reset --hard origin/main
git push origin wip/{brand} --force-with-lease
# git stash pop si quieres recuperar uncommitted (raro)
```

**Caso B — ≥1 ahead (merge preservando):**

```bash
cd ~/Proyectos/luana-{brand_target}
git stash push --include-untracked -m "{brand}-pre-sync-$(date +%Y-%m-%d)"   # si hay uncommitted
git fetch origin
git merge-tree $(git merge-base HEAD origin/main) HEAD origin/main | grep -c "<<<<<<< "   # conflict preview
git merge origin/main -m "chore({brand}): sync wip/{brand} con main post wip/{brand_origin} squash-merge {sha}"
# Si conflicts:
#   - Auto-gen files (BACKLOG.{md,yaml,-TLDR.md}, docs/portfolio/*) modify/delete → git rm (R3 v2 gitignored)
#   - Code conflicts → resolver caso a caso preservando lógica brand
git push origin wip/{brand}
# git stash pop si previamente se aplicó stash
```

**Pre-commit hook scope gate**: si el merge trae cambios cross-cutting (`.claude/rules/*`, `AGENTS.md`, `CLAUDE.md`, scripts compartidos) el hook bloqueará con error "SCOPE GATE BLOCKED". Override permitido para merge sync legítimo:

```bash
SCOPE_GATE_SKIP=1 git commit -m "chore({brand}): sync wip/{brand} con main ..."
```

Documentar override en commit body con razón. Override prohibido para edición LOCAL intencional de cross-cutting (eso requiere worktree dedicado `protocol`/`exp`).

### Conflictos esperados típicos

- `pnpm-lock.yaml` / `uv.lock` — workspace shared, auto-merge usualmente OK
- `.claude/rules/*` — main suele tener versiones más nuevas, aceptar main
- `comunify/docs/product/BACKLOG.{md,yaml,-TLDR.md}` — auto-gen R3 v2, `git rm`
- `docs/portfolio/{PORTFOLIO,brand,luana}.md` — auto-gen R3 v2, `git rm`
- `vitalia/.claude/rules/*` — brand overlay, resolver según overlay extiende root
- `core/luana-core-*/src/` — engine shared, CRITICAL — escalate `/pm-luana` si conflict

### Excepciones revocando "PROHIBIDO"

Este procedimiento usa EXPLICITAMENTE comandos del bloque "PROHIBIDO". La autorización es:

| Comando | Por qué OK acá |
|---|---|
| `git reset --hard origin/main` | Cuando wip/{brand} tiene 0 commits propios, no destruye trabajo |
| `git push --force-with-lease` | Lease check previene sobrescribir commits no vistos por agente |
| `git merge origin/main` | Es el merge LEGITIMO main→wip, no es `git pull` (fetch + merge automático sin ratificación) |

`git pull` sigue PROHIBIDO. La diferencia es: `fetch` separado + `merge` explícito con ratificación (este procedimiento) vs `pull` automático sin verificación previa de diff/conflictos.

### Cuando NO sincronizar

- Brand bootstrap pendiente (saasora, inmoflow, retailly, fixia, guestly, fitflow): sus wip/* no existen aún, N/A
- Worktree con sesión activa en curso developing/reviewing: terminar la story primero, sync después
- Conflict en `core/luana-core-*/src/`: STOP, escalate `/pm-luana` (engine boundary)

## Fase solo-bootstrap — SCOPE_GATE_SKIP relajado (cement 2026-05-28) — detalle

**Origen:** sesión 2026-05-28. Chris está construyendo activamente las propias reglas + cockpit, solo dev, sin CI activo. Exigir un worktree `protocol` dedicado para cada ajuste cross-cutting es fricción sin beneficio en esta fase. Mismo razonamiento + patrón que `github-actions-deferred` ("relajar ahora, endurecer cuando un trigger concreto aparezca").

**Regla (mientras dure la fase):** `SCOPE_GATE_SKIP=1` está PERMITIDO para edición intencional cross-cutting Y cross-brand cuando Chris está seguro del cambio, con razón documentada en el commit body. El worktree `protocol` (y la sesión `/pm-{brand}` correcta para cross-brand) siguen siendo lo prolijo recomendado pero NO obligatorio.

**Guardrails que se mantienen (no es barra libre):**
- El scope gate sigue corriendo y bloqueando por default — pasar requiere tipear `SCOPE_GATE_SKIP=1`.
- Razón obligatoria en el commit body.
- Siguen PROHIBIDOS sin excepción: `--no-verify`, secrets/`.env*`, `--force`, `git pull`, amend de pusheados.
- Pre-commit hook full gate (lint/format/voseo/PII/arch) NO se saltea — `SCOPE_GATE_SKIP` solo apaga el scope gate (Section 13).

**Re-endurecer cuando CUALQUIERA:**

| Trigger | Quién declara |
|---|---|
| Entra un 2º desarrollador al equipo | Chris |
| Chris declara reglas + cockpit "fijos/estables" | Chris |
| Se activa CI/CD real (server staging/prod) | Chris |

Al re-endurecer: revertir el bloque a "PROHIBIDO para edición local intencional cross-cutting (requiere worktree protocol)" + crear ADR documentando el trigger + actualizar `parallel-safety.md` línea espejo + MEMORY.md pointer.

## CI/CD workflows (referencia)

| Workflow | Trigger | Accion |
|---|---|---|
| `.github/workflows/ci.yml` | push:main + pull_request:main | Full gates (lint + test + arch-fitness + coverage) |
| `.github/workflows/ci-wip.yml` | push:wip/** | Light gates (lint targeted + tests targeted, <5 min) |
| `.github/workflows/cd-staging.yml` | push:main | Auto-deploy staging (placeholder si STAGING_HOST no configurado) |
| `.github/workflows/cd-prod.yml` | push:release/** | Deploy brand prod (parse brand+version + dorny/paths-filter) |
| `.github/workflows/cleanup-wip.yml` | cron semanal / workflow_dispatch | Listar/eliminar wip/* branches >30d sin commits |
| `.github/workflows/release.yml` | push:tags:v*.*.* | Publish luana-core-* a GH Packages (NO modificar) |
