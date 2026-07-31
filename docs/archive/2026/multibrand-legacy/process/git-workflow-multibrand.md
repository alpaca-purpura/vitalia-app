# Git Workflow Multibrand — Runbook + Cheatsheet

> Triple-branch policy (ADR-004, 2026-05-15).
> Reemplaza politica legacy "solo development, main=prod auto".
> Detalle tecnico: `.claude/rules/git-safety.md` + `.claude/rules/parallel-safety.md`.

## Workflow 1: Sesion paralela (DEFAULT — hub único, ADR-009)

```bash
# N sesiones trabajan sobre el MISMO worktree canónico ~/Proyectos/luana-{brand}
# coordinadas por bucket locks M14 (code:{module} / docs / tests).
# Worktrees dedicados son la EXCEPCION (lift core, hotfix aislado, otra marca).
WS=$(git rev-parse --show-toplevel)

# Adquirir bucket lock para el módulo a trabajar
bash ${WS}/scripts/git/session-lock.sh acquire code:docker

# Trabajar + commitear frecuentemente por pathspec (índice compartido entre sesiones)
git add src/archivo.py
git commit -m "wip(docker): primera pasada base compose"
git push origin wip/vitalia              # safety net (M11: max cada 30 min)

# ... iteraciones ...
git add src/otro.py
git commit -m "wip(docker): compose multibrand vitalia + comunify"
git push origin wip/vitalia
```

## Workflow 1b: Sesion dedicada (EXCEPCION — worktree separado)

```bash
# Solo para: lift core, cross-cutting protocol, hotfix aislado, u otra marca.
WS=$(git rev-parse --show-toplevel)

# Crear worktree dedicado + branch wip/*
bash ${WS}/scripts/git/new-session.sh A-docker   # crea ../luana-A-docker + branch wip/A-docker
cd ../luana-A-docker

# Trabajar + commitear frecuentemente
git add src/archivo.py
git commit -m "wip(docker): primera pasada base compose"
git push origin wip/A-docker             # safety net (M11: max cada 30 min)

# ... iteraciones ...
git add src/otro.py
git commit -m "wip(docker): compose multibrand vitalia + comunify"
git push origin wip/A-docker
```

## Workflow 2: Integrar a main (squash-merge)

```bash
# Cuando el trabajo en wip/* esta listo para staging
# NOTA: staging deploy es MANUAL (GitHub Actions = DEFERRED, sentinel .ci-parity-deferred)
WS=$(git rev-parse --show-toplevel)
cd ${WS}    # worktree principal (PRINCIPAL branch main)

git checkout main
git merge --squash wip/A-docker             # squash todos los wip commits en uno
git commit -m "feat(docker): T-N compose multibrand servicios base"
git push origin main                         # push a main; staging deploy = MANUAL (no auto)
```

## Workflow 3: Deploy a produccion (release branch)

```bash
# Solo desde main validado post-staging.
# release/* es el ÚNICO auto-deploy a prod (cuando CI/CD prod este provisionado).
# git pull esta PROHIBIDO; sync con main via scripts/git/sync-from-main.sh.
git checkout main
# Si main local esta desactualizado, usar: bash scripts/git/sync-from-main.sh
git checkout -b release/vitalia-v0.3.0
git push origin release/vitalia-v0.3.0       # AUTO DEPLOY A PROD vitalia (via VPS + docker-compose)
# Branch release/* inmutable post-deploy; borrar manual si ya no se necesita
```

## Workflow 4: Cleanup de sesion terminada (worktree dedicado)

```bash
# Solo aplica para worktrees dedicados (Workflow 1b). El hub no se "limpia".
WS=$(git rev-parse --show-toplevel)

# Verificar que el worktree esta limpio antes de cleanup
cd ../luana-A-docker && git status           # debe estar limpio

# Cleanup: push final + remove worktree
cd ${WS}
bash ${WS}/scripts/git/cleanup-session.sh A-docker   # push + remove worktree ../luana-A-docker

# La branch wip/A-docker sigue en el repo (no se borra) — merge o borrar manual
# Si el trabajo ya fue squash-merged a main:
git branch -d wip/A-docker                  # borrar branch local (opcional)
```

## Recovery patterns

### Crash del sistema durante sesion activa

```bash
# Verificar estado del repositorio
git worktree list                            # que worktrees existen
git stash list                               # WIP en stash (si aplica)
git log --oneline -5 wip/A-docker           # ultimos commits del branch

# Si hay commits pusheados: recuperar worktree
git worktree add ../luana-A-docker wip/A-docker
cd ../luana-A-docker
# Continuar desde el ultimo commit pusheado
```

### Branch wip/* cercana al TTL de 30 dias

```bash
# Ver branches wip/* con su ultimo commit
git for-each-ref --sort=-committerdate refs/remotes/origin/wip --format='%(committerdate:short) %(refname:short)'

# Si hay trabajo valioso pendiente de merge: squash-merge a main ANTES de 30d
git checkout main
git merge --squash origin/wip/A-docker
git commit -m "feat(scope): descripcion del trabajo"
git push origin main
```

### Push wip/* falla (non-fast-forward)

```bash
# STOP. NO hacer git pull.
# Verificar que no hay otra sesion usando el mismo branch (git bloquea esto)
git log --oneline origin/wip/A-docker      # ver commits remotos
# Contactar a Chris para diagnosticar. La solucion NO es git pull.
```

### Worktree con cambios uncommitted al hacer cleanup

```bash
# cleanup-session.sh da exit code 2 con mensaje explicito
# Resolver antes de cleanup:
WS=$(git rev-parse --show-toplevel)

cd ../luana-A-docker
git status                                   # ver que archivos estan sucios

# Opcion A: commitear (recomendado)
git add src/archivo.py
git commit -m "wip: guardar estado antes de cleanup"

# Opcion B: stash (context-switch corto, max 30min)
git stash push -m "WIP: descripcion del cambio"

# Luego volver al monorepo y cleanup
cd ${WS}
bash ${WS}/scripts/git/cleanup-session.sh A-docker
```

### Olvidaste hacer cleanup de una sesion vieja

```bash
# Ver worktrees activos
git worktree list

# Verificar que estan limpios
git -C ../luana-A-docker status

# Cleanup manual si el script da error
git worktree remove ../luana-A-docker       # falla si dirty
git worktree remove --force ../luana-A-docker  # SOLO si ya se mergeo o no hay nada valioso
```

## Anti-patterns prohibidos

```bash
# PROHIBIDO: no usar el patron legacy
# git checkout -b feature-branch    # sin worktree separado
# git checkout main && trabajar     # pisa WIP de otras sesiones

# PROHIBIDO: operaciones destructivas sin verificacion
# git worktree remove --force       # bypasea verificacion dirty tree
# git add .                         # staging global (pisa WIP ajeno)
# git add -A / -u                   # idem

# PROHIBIDO: sincronizacion manual
# git pull                          # PROHIBIDO en todo contexto
# git fetch && git merge            # equivalente semantico a pull

# PROHIBIDO: amend de commits ya pusheados
# git commit --amend (post-push)    # reescribe historia compartida
# git push --force                  # destruye commits de otros
```

## Referencias

- ADR que ratifica esta politica: `docs/architecture/luana-platform/ADR-004-git-branching-and-environments.md`
- Policy completa: `.claude/rules/git-safety.md`
- Multi-sesion paralela: `.claude/rules/parallel-safety.md`
- Commit+push delegation: `.claude/rules/git-haiku-delegation.md`
- Scripts: `scripts/git/new-session.sh` + `scripts/git/cleanup-session.sh`
