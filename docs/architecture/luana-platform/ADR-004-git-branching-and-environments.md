# ADR-004 — Git Branching Strategy + Environments (Triple-Branch + Worktrees)

> **Status:** ACCEPTED
> **Date:** 2026-05-15
> **Decision-makers:** Chris (alpacapurpura@) + claude-opus-4-8 (advisory)
> **Supersedes:** politica legacy "Single branch = development, main = prod only, no worktrees" (AGENTS.md pre-2026-05-15)
> **Superseded by:** none
> **Related docs:**
>
> - `docs/product/outcomes/git-strategy-revised.md` — outcome doc con decisiones ratificadas
> - `.claude/rules/git-safety.md` — triple-branch policy completa (S-GIT-STRATEGY-CORE T-1)
> - `.claude/rules/parallel-safety.md` — multi-sesion paralela reglas (S-GIT-STRATEGY-CORE T-2)
> - `scripts/git/new-session.sh` — helper automatiza creacion worktree + branch wip/*
> - `scripts/git/cleanup-session.sh` — helper automatiza push final + remocion worktree
> - `docs/process/git-workflow-multibrand.md` — runbook cheatsheet diario

## 1. Context

### 1.1 Politica heredada (pre-2026-05-15)

La politica git del proyecto fue disenada para single-brand Nicolify con una sola sesion
de desarrollo activa. La politica legacy dictaba:

- **Una sola rama de trabajo:** `development` (unica branch de commits).
- **`main` = produccion auto-deploy:** push a main triggerea deploy inmediato.
  > Nota 2026-05-19: ese era el comportamiento legacy. Ahora main solo dispara CI gates; staging es manual + prod va por release/*.
- **Worktrees PROHIBIDOS:** ban explicito ("no worktrees") con justificacion historica
  de que "Chris perdio una semana" por colision de branches en worktrees.
- **Sesiones paralelas en mismo workdir:** dos sesiones Claude Code usaban el mismo
  directorio y branch, confiando en disciplina manual para no pisarse.

### 1.2 Cambios de contexto que invalidan la politica legacy

Desde la reorg multimarca 2026-05-15, el contexto cambio radicalmente:

1. **Multimarca (10 brands):** workflows de CI/CD requieren diferenciar deploy por brand
   (`release/{brand}-vX.Y.Z`) — imposible con una sola branch.

2. **2-3 sesiones Claude paralelas (patron actual):** Chris opera multiples sesiones
   Claude Code en Linux (Mint) simultaneamente para distintas stories/tickets. Con el patron
   legacy (mismo workdir + branch), una sesion puede sobreescribir el WIP de la otra.

3. **System crash recovery:** la volatilidad del entorno (crash del sistema, cambio de maquina)
   requiere un mecanismo de autosave push frecuente sin contaminar `main`.

4. **Diagnosis del ban historico de worktrees:** el problema reportado ("perdi una semana")
   no fue causado por la tecnologia de worktrees sino por el patron de uso incorrecto:
   dos sesiones humanas en el **mismo workdir cambiando branches** (`git checkout`).
   Con worktrees, cada sesion tiene su **directorio fisico separado** — git bloquea
   por diseno que dos worktrees compartan un branch activo.

### 1.3 Problema especifico de la politica legacy con sesiones paralelas

Con la politica legacy:

```text
Sesion A (worktree principal):  branch=development, files modificados sin commit
Sesion B (mismo worktree):      git checkout development (ya en development) → WIP de A sigue ahi
                                 git checkout otra-branch → DESTRUYE WIP de A
```

Git no puede proteger WIP que no esta commiteado. La "disciplina manual" no escala
con 3 sesiones Claude paralelas que no tienen memory compartida.

## 2. Decision

### 2.1 Triple-branch policy

| Branch | Proposito | Trigger CI/CD | Quien la usa |
|---|---|---|---|
| `wip/{slug}` | Autosave iterativo por sesion paralela. TTL 30 dias (cron cleanup). Commits WIP frecuentes. | `ci-wip.yml` (light: lint + tests targeted, <5 min) | Cada sesion Claude Code o developer en su worktree dedicado. |
| `main` | Integracion estable. Squash-merge wip/* cuando el trabajo esta listo. Estado siempre deployable. | `ci.yml` (full gates) | Squash-merge consciente desde wip/*. |
| `release/{brand}-vX.Y.Z` | Marcha blanca aprobada a produccion. Branch efimera (vida horas, auto-deleted post-deploy). | `cd-prod.yml` (parse brand+version, deploy selective) | Desde main validado. |

> **★ Cambio policy 2026-05-19 (ratificada Chris):** `cd-staging.yml` ya NO es auto-trigger en push a main. Pasó a `workflow_dispatch` (manual desde GH Actions UI o `gh workflow run`). Razón: evitar deploys staging continuos en cada commit a main (incluyendo docs-only PRs). Staging deploys son ahora explícitos cuando se necesita validar cambios runtime antes de release. CI gates en main (push + pull_request) se mantienen activos como guardrail. **Solo `release/*` dispara deploy automático** — cd-prod.yml.

### 2.2 Worktrees per sesion paralela (REVOCACION del ban historico)

Cada sesion Claude Code o desarrollador paralelo usa su propio worktree fisico dedicado
con branch `wip/*` dedicado:

```bash
# Patron canonico obligatorio para sesiones paralelas
git worktree add ../luana-{slug} wip/{slug}-{desc}

# O via helper:
scripts/git/new-session.sh {slug}
```

Git garantiza por diseno que dos worktrees no pueden compartir el mismo branch activo —
la colision de WIP es **imposible por construccion del sistema de archivos**.

### 2.3 WIP safety net

| Mecanismo | Frecuencia | Cuando usar |
|---|---|---|
| Squash-merge a `main` | ~80% | WIP listo para staging |
| Push a `wip/*` (autosave) | ~15% | WIP en progreso, commit frecuente |
| `git stash` | ~5% | Context-switch corto (<30 min) en mismo worktree |

**Regla M11:** nunca pasar >30 minutos sin push si hay cambios significativos en el worktree activo.

## 3. Justificacion tecnica de la reversion del ban de worktrees

| Lo que provoco el ban (2024-2026) | Por que fallaba | Patron actual | Por que funciona |
|---|---|---|---|
| Sesiones humanas en mismo workdir cambiando de branch | `git checkout` sobreescribe el filesystem — WIP no-commiteado se pierde sin advertencia | Cada sesion tiene su **worktree fisico separado** + **branch dedicado** | Worktrees son directorios fisicos distintos. Git **bloquea automaticamente** que dos worktrees tengan el mismo branch. Error explicito si se intenta. WIP imposible de pisar. |

**El problema no era la tecnologia de worktrees. El problema era el patron de uso:**
usar un solo directorio de trabajo con multiples sesiones cambiando branches.

La solucion correcta (worktrees) es la practica estandar de la industria para
desarrollo paralelo con git desde git 2.5+ (2015). Claude Code la adopta
nativamente (Agent isolation via worktrees).

## 4. Alternativas descartadas

### Alternativa A — Single branch `development` (politica legacy)

**Problema:** Con 2-3 sesiones Claude paralelas, el WIP no-commiteado de la sesion A
es invisible para la sesion B. Si B ejecuta cualquier operacion git que modifique el
working tree, puede destruir el WIP de A silenciosamente.

**Rechazada porque:** no escala con multiples sesiones paralelas. La disciplina manual
("no toques archivos de otra sesion") no es verificable ni garantizable entre procesos
sin memory compartida.

### Alternativa B — Feature branches sin worktrees (mismo workdir)

**Problema:** Misma branch = mismo directorio fisico. Dos sesiones con branches distintas
pero mismo directorio — `git checkout` entre branches modifica el working tree y puede
destruir cambios de la otra sesion.

**Rechazada porque:** sin aislamiento fisico de directorio, el checkout entre branches
es igualmente destructivo para WIP no-commiteado.

### Alternativa C — Multi-repo por sesion

**Problema:** Clonar el repo completo por sesion paralela es costoso en disco (+1GB por
clone), rompe el workspace uv+pnpm (hay que reinstalar deps por cada clone), y no hay
mecanismo de sincronizacion automatica entre clones.

**Rechazada porque:** overhead operacional prohibitivo para el patron de uso de Chris
(2-3 sesiones en Linux Mint con ~100GB disponible, 90% usado por repos existentes).

### Alternativa D — Git stash como mecanismo de aislamiento

**Problema:** `git stash` guarda WIP en la reflog del HEAD actual — es un mecanismo
de context-switch dentro de una sesion, no de aislamiento entre sesiones paralelas.
Dos sesiones accediendo al mismo stash pueden corromperse mutuamente.

**Rechazada porque:** stash no provee aislamiento entre procesos. TTL implicita (no
hay autosave automatico, stashes pueden perderse en garbage collection).

## 5. Consecuencias

### 5.1 Positivas

- **Paralelismo seguro garantizado:** git bloquea colision de WIP por construccion.
  Sin disciplina manual requerida entre sesiones.
- **System crash recovery:** push a `wip/*` frecuente (M11) garantiza recovery de WIP
  ante crash del entorno.
- **CI/CD diferenciado por branch:** `wip/*` usa gates ligeros (iteracion rapida);
  main usa gates completos (calidad); `release/*` triggerea deploy brand-especifico.
- **Multimarca nativa:** `release/{brand}-vX.Y.Z` permite deploy independiente
  por brand sin acoplar releases entre ellas.
- **Helper scripts:** `new-session.sh` + `cleanup-session.sh` reducen el ritual
  de gestion de worktrees a dos comandos.

### 5.2 Negativas / contrapartes

- **Disciplina mental:** cada sesion debe iniciar con `new-session.sh` — habito nuevo.
  Mitigado por: error explicito de git si se olvida + helper scripts.
- **Cleanup ritual:** `cleanup-session.sh` al terminar la sesion. Mitigado por:
  el helper es un one-liner y la branch `wip/*` persiste si se olvida.
- **TTL 30 dias branches wip/*:** si un wip/* con trabajo valioso no se mergea
  en 30 dias, el cron de cleanup lo borra. Mitigado por: M11 (push frecuente a main
  lo que este listo) + notificacion antes de delete en cleanup-wip.yml.
- **Abuso potential del pre-commit dinamico:** `# wip-fast` magic comment permite
  skip de checks en wip/*. Mitigado por: auditor Cat 14 revisa magic comments en review.

## 6. Referencias

- `docs/product/outcomes/git-strategy-revised.md` — decisiones tecnicas originales + trade-offs
- `.claude/rules/git-safety.md` — triple-branch policy completa + prohibiciones
- `.claude/rules/parallel-safety.md` — reglas M1-M14 para sesiones paralelas
- `.claude/rules/git-haiku-delegation.md` — delegacion commit+push a Haiku (3 destinos)
- `scripts/git/new-session.sh` — helper creacion worktree + branch wip/*
- `scripts/git/cleanup-session.sh` — helper push final + remocion worktree
- `docs/process/git-workflow-multibrand.md` — runbook cheatsheet diario

## 7. Historial de revisiones

| Version | Fecha | Cambio | Autor |
|---|---|---|---|
| 1.0 | 2026-05-15 | ADR inicial. Status ACCEPTED (Chris ratifico en outcome doc). | claude-opus-4-8 + /architect |
| 1.1 | 2026-06-01 | Addendum: M-range M1-M14, single-hub ADR-009, ci-wip/cleanup-wip deferred. | claude-opus-4-8 |

## Addendum (2026-06-01)

> Append-only. El texto de decisión original (Secciones 1–6) se preserva intacto.

### A1 — Rango de reglas paralelas: M1-M14 (no M1-M11)

La referencia original de Sección 6 citaba "M1-M11". Desde el cement 2026-05-18 (D1-D14),
el rango activo es **M1-M14**. Las reglas añadidas relevantes para este ADR:

- **M12:** `wip/{brand}` es ESTABLE — no rota story-by-story. Branch efímera solo por
  pedido explícito de Chris. Antes se asumía un `wip/` por historia; ahora hay un único
  `wip/{brand}` canónico por marca (hub único).
- **M13:** Scope por branch enforced (pre-commit §13). Cross-brand mixing PROHIBIDO.
- **M14:** N sesiones sobre el mismo cwd coordinadas por bucket locks
  (`docs`/`tests`/`code`/`code:{module}`). Commit siempre por pathspec (índice compartido).
  Módulos distintos pueden paralelizarse; mismo módulo serializa.

SSoT actualizado: `.claude/rules/parallel-safety.md` § "Reglas M1-M14".

### A2 — Topología single-hub (ADR-009 2026-05-28)

La Sección 2.2 describía "cada sesión paralela usa su propio worktree físico dedicado"
como patrón general. ADR-009 (2026-05-28) invirtió el default:

- **Default actual:** N sesiones sobre el **worktree canónico único** (`~/Proyectos/luana-{brand}/`)
  coordinadas por bucket locks M14. Un solo filesystem = un solo SSoT = el cockpit ve todo.
- **Worktree dedicado:** excepción para lift core, cross-cutting protocol, hot-fix aislado,
  u otra marca. No es la operación diaria.

Referencias: `docs/architecture/luana-platform/ADR-009-single-hub-worktree.md` +
`.claude/rules/worktree-dual-strategy.md`.

### A3 — ci-wip.yml y cleanup-wip.yml: DEFERRED

Los workflows `ci-wip.yml` (mencionado en Sección 2.1) y `cleanup-wip.yml` (mencionado en
Sección 5.2) están en modo **deferred** — no se garantiza que corran. La calidad se
enforce 100% vía hooks locales:

- `scripts/git-hooks/pre-commit` — SSoT calidad por commit (light en `wip/*`, full en `main`/`release/*`).
- `scripts/git-hooks/pre-push` — tests + tsc + arch fitness.
- `make ci-parity` — full suite local, obligatorio antes de squash-merge `wip→main`.

La limpieza de branches `wip/*` vencidas (TTL 30 días) queda como tarea manual hasta que
se provisione un servidor CI real. Reactivar cuando: servidor staging provisionado,
primera release vX.Y.Z, o segundo desarrollador.

SSoT: `.claude/rules/github-actions-deferred.md` + `docs/rules-detail/github-actions-deferred.md`.
