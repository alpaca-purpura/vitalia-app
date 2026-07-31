---
slug: git-strategy-revised
kind: outcome-sub
parent_outcome: infra-dev-multibrand
owner: /pm-luana
state: refining
created: 2026-05-15
priority: HIGH-CRITICAL
why_now: |
  Política git heredada de single-brand Nicolify ("solo development, main = prod auto") en
  contradicción con uso real (commits a main). Chris corre 2-3 sesiones Claude paralelas — pattern
  legacy de "filesystem compartido sin worktrees" pone en riesgo WIP no-commiteado al pisarse
  branches. Ambiente "volátil" (sistema crashea, cambio máquina) requiere safety net push frecuente.
estimated_effort: 18-22h (split en 2 stories)
stories:
  - S-GIT-STRATEGY-CORE       # rules + workflows + hook
  - S-GIT-STRATEGY-HELPERS    # helper scripts + docs runbooks
foundational: true             # bloquea S-DOCKER-DEV-MULTIBRAND + S-CICD-DEPLOY (sus workflows usan triple branch)
---

# git-strategy-revised — Triple-branch + worktrees per sesión + WIP safety net

> Sub-outcome de [O-INFRA-DEV-MULTIBRAND](./infra-dev-multibrand.md). Resuelve la pieza git workflow.
>
> **FOUNDATIONAL:** debe completarse antes que los otros sub-outcomes porque sus workflows asumen la triple-branch policy.

## Decisión final

### Triple-branch policy

| Branch | Propósito | Trigger CI/CD | Dispara |
|---|---|---|---|
| `wip/{slug}` | Autosave per sesión. TTL 30d (cron auto-cleanup). Cada sesión Claude paralela SU branch wip/*. Push frecuente garantiza recovery. | `ci-wip.yml` (light) | Nada deploy. CI ligero. |
| `main` | Integración estable. Squash-merge wip/* → main cuando algo está listo. | `ci.yml` (full) + `cd-staging.yml` | **Staging auto-deploy** `{brand}-test.nicolify.com` |
| `release/{brand}-vX.Y.Z` | Marcha blanca aprobada → producción. Vida horas, auto-deleted post-deploy. | `ci.yml` (full) + `cd-prod.yml` | **Prod deploy** brand-específico |

### Worktrees per sesión paralela (REVOCAR ban legacy)

**Justificación técnica del cambio:**

| Lo que probaste antes | Por qué falló | Patrón canónico 2026 | Por qué funciona |
|---|---|---|---|
| Sesiones humanas en mismo workdir cambiando de branch | `git checkout` sobreescribe filesystem → WIP no-commiteado se pierde | Cada sesión su **worktree físico separado** + **branch dedicado** | Worktrees son directorios físicos distintos. Git **bloquea** dos worktrees en el mismo branch. Imposible pisarse. |

**Política actualizada:**

| Caso | Política |
|---|---|
| 1 sesión activa | Workdir principal `/home/chalreme/Proyectos/luana-platform`, branch main o wip/* |
| 2-3+ sesiones paralelas (caso actual Chris) | CADA sesión SU worktree: `git worktree add ../luana-{X} wip/X-{slug}`. OBLIGATORIO. |
| Sub-agents Agent tool dentro de sesión | `Agent({ isolation: "worktree" })` automático. Efímero, cleanup auto. OK. |
| Otras cuentas Claude / otras máquinas (futuro) | Mismo patrón. Worktrees locales por máquina, push a wip/* remoto, merge a main vía PR draft |

### WIP safety net (3 mecanismos en orden de uso)

1. **Push frecuente a `main`** cuando hay commit conventional listo (80% casos). Vía Haiku delegation pattern existente.
2. **Push a `wip/{slug}` para snapshots incompletos** (15% casos). Para hipótesis o trabajo a medias.
3. **`git stash push -m "WIP: ..."` solo context-switches cortos** mismo día (5% casos). Si dura más → convertir a commit en `wip/*`.

**Regla M11 nueva:** NUNCA pasar >30 min sin push si hay cambios significativos en worktree.

### Pre-commit hook dinámico

| Branch | Checks |
|---|---|
| `main` | Lint + tests full + arch fitness + coverage + jscpd + voseo + interrogate + pip-audit |
| `wip/*` | Lint + tests targeted. Skip arch fitness/coverage/jscpd. Magic comment `# wip-fast` para skip adicional. |
| `release/*` | Todo lo de main + smoke E2E adicional |

## Story `S-GIT-STRATEGY-CORE` — tickets (foundational, primero)

| Ticket | Descripción | Tipo |
|---|---|---|
| T-1 | Reescribir `.claude/rules/git-safety.md` (triple branch policy + worktrees revocación ban + helper scripts ref) | docs |
| T-2 | Reescribir `.claude/rules/parallel-safety.md` (M9 worktree Agent isolation OK + M10 wip branches autosave + M11 push >30min + cambios M1-M8) | docs |
| T-3 | Update `.claude/rules/git-haiku-delegation.md` (3 destinos: main/wip/release con guardrails distintos) | docs |
| T-4 | Rewrite `.github/workflows/ci.yml` — trigger en `push: main` + PR, full gates | code |
| T-5 | Nuevo `.github/workflows/ci-wip.yml` — trigger en `push: wip/*`, light gates (lint + tests targeted) | code |
| T-6 | Nuevo `.github/workflows/cd-staging.yml` placeholder — trigger en `push: main`, deploy a staging shared cluster (server config placeholder hasta infra staging futura) | code |
| T-7 | Nuevo `.github/workflows/cd-prod.yml` (= cd-brands.yml del Tema 1) — trigger en `push: release/*`, parse brand, selective deploy a prod | code |
| T-8 | Nuevo `.github/workflows/cleanup-wip.yml` — scheduled cron weekly, borra `wip/*` >30d sin commits (safeguard) | code |
| T-9 | Update pre-commit hook (`scripts/git-hooks/pre-commit`) — gates dinámicos por branch + magic comment `# wip-fast` | code |

## Story `S-GIT-STRATEGY-HELPERS` — tickets (post-core)

| Ticket | Descripción | Tipo |
|---|---|---|
| T-10 | Helper scripts: `scripts/git/new-session.sh {slug}` (crea worktree + branch wip/* + setup .env) y `scripts/git/cleanup-session.sh {slug}` (push final + worktree remove + cleanup) | code |
| T-11 | Update `CLAUDE.md` § Git Workflow + `AGENTS.md` § Git Workflow (replace legacy "solo development" con triple-branch + worktrees patterns) | docs |
| T-12 | ADR `docs/architecture/luana-platform/ADR-004-git-branching-and-environments.md` (rationale completo + decisión worktrees revertida + alternativas descartadas) | docs |
| T-13 | Runbook `docs/process/git-workflow-multibrand.md` (cheatsheet diario + recovery patterns) + entry `MEMORY.md` | docs |

## Ejemplo workflow diario (cementado)

```bash
# Sesión A: trabajo docker-compose multimarca
cd /home/chalreme/Proyectos/luana-platform
scripts/git/new-session.sh A-docker      # crea worktree ../luana-A + branch wip/A-docker
cd ../luana-A
# ... trabaja ...
git commit -m "wip(docker): primera pasada base compose"
git push origin wip/A-docker             # safety net

# Sesión B paralela: CI/CD
cd /home/chalreme/Proyectos/luana-platform
scripts/git/new-session.sh B-cicd
cd ../luana-B
# ... trabaja paralelo, NO se pisa con A ...

# Cuando wip/A-docker está listo
cd /home/chalreme/Proyectos/luana-platform
git checkout main
git merge --squash wip/A-docker
git commit -m "feat(docker): T-1+T-2 base compose multibrand"
git push origin main                      # AUTO DEPLOY A STAGING

# Después de validar staging
git checkout -b release/vitalia-v0.3.0
git push origin release/vitalia-v0.3.0    # AUTO DEPLOY A PROD vitalia

# Cleanup
scripts/git/cleanup-session.sh A-docker   # remove worktree ../luana-A
```

## Trade-offs cementados

| Decisión | Pro | Contra |
|---|---|---|
| Worktrees per sesión (revoca ban) | Paralelismo seguro garantizado, jamás se pisan, alineado state of art 2026 | Disciplina mental "cada sesión su worktree" + cleanup ritual (mitigado helper scripts) |
| Main → staging auto-deploy | Feedback rápido marcha blanca, no esperar release | Requiere infra staging (futura, no bloqueante hoy) |
| Release/* → prod | Gate explícito producción, no accidents | Más manual que "push y deploy" — pero deseable |
| WIP TTL 30d cron cleanup | Sin ramas zombies eternos | Si olvidás wip valioso 30d, se borra (mitigado: pushes frecuentes a main para lo bueno) |
| Pre-commit hook dinámico por branch | Checks rápidos en wip = iteración fluida; checks full en main = calidad | Magic-comment-skip puede abusarse (mitigado audit Cat 14) |

## Anti-patterns prohibidos (cementados)

- ❌ Worktrees humanos sin branch dedicado (cada uno SU branch wip/*)
- ❌ 2 sesiones en mismo workdir cambiando branches (pisa WIP)
- ❌ Crear `release/*` desde branch que no sea `main`
- ❌ Deploy producción sin pasar por staging
- ❌ Skip pre-commit con `--no-verify` excepto wip/* magic comment justificado
- ❌ Pasar >30 min sin push si hay cambios significativos (M11)
- ❌ Force push, revert sin aprobación, `--amend` pushed commits (todos siguen prohibidos)

## Referencias

- Outcome padre: [infra-dev-multibrand](./infra-dev-multibrand.md)
- Research sources: trunk-based vs GitHub Flow (Atlassian + codewithmukesh), git worktrees parallel AI (MindStudio, Boris Cherny Anthropic), WIP patterns 2026 (DEV)
- Rules a reescribir: `.claude/rules/{git-safety,parallel-safety,git-haiku-delegation}.md`
- Anti-default-flip-audit rule sigue vigente: `.claude/rules/anti-default-flip-audit.md`
