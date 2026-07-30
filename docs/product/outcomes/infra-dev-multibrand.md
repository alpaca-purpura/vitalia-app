---
slug: infra-dev-multibrand
kind: outcome-platform
owner: /pm-luana
state: refining
created: 2026-05-15
ratified_by: Chris
ratified_session: post-ff33858
priority: HIGH
why_now: |
  Sin esta infraestructura ningún deploy multimarca es viable. CI/CD manual hoy. Docker dev local
  single-brand legacy. Política git heredada de single-brand Nicolify, en contradicción con uso real
  (commits a main + multi-sesión Claude paralela + necesidad de WIP safety net).
sub_outcomes:
  - cicd-multibrand-deploy
  - docker-dev-multibrand
  - git-strategy-revised
estimated_total_effort: 30-40h (3 sesiones /dev-team)
---

# O-INFRA-DEV-MULTIBRAND — Infraestructura desarrollo + deploy multimarca

> **Outcome platform consolidado.** Cubre la base infra para que las 10 brands del portfolio Luana puedan desarrollarse en local + desplegarse independientemente a producción + manejarse en git con multi-sesión Claude paralela segura.
>
> Pointer-first: este file consolida decisiones cross-tema. Detalle por sub-outcome en archivos hermanos.

## Decisiones ratificadas Chris (commit ff33858 + esta sesión)

| # | Tema | Decisión | Sub-outcome |
|---|---|---|---|
| 1 | CI/CD multimarca | GitHub Actions puro + `dorny/paths-filter@v3` + reusable workflows + GitHub Environments per brand. NO Argo CD por ahora. Trigger producción: `push: release/{brand}-vX.Y.Z`. Trigger staging: `push: main` (auto-deploy a `{brand}-test.nicolify.com`). | [cicd-multibrand-deploy](./cicd-multibrand-deploy.md) |
| 2 | Docker dev local | 1 postgres shared + N databases via init script. Qdrant/Redis opt-in profiles. Brand-autocontenida: `{brand}/docker-compose.dev.yml` per brand. Hot-reload monorepo vía bind mount + uv editable workspace. Cloudflared tunnel opt-in per brand. | [docker-dev-multibrand](./docker-dev-multibrand.md) |
| 3 | Git strategy | Triple-branch: `wip/{slug}` autosave + `main` integración + staging auto-deploy + `release/{brand}-vX.Y.Z` prod. Worktrees DEDICADOS per sesión paralela (revoca ban legacy con justificación). WIP TTL 30d cron cleanup. Pre-commit hook dinámico por branch. | [git-strategy-revised](./git-strategy-revised.md) |
| 4 | Pattern canónico metadata | "Metadata-en-su-lugar + auto-gen index al raíz". Aplicado a infra (puertos, dominios) en `{brand}/config/brand.yaml::infra` + `docs/portfolio/INFRA-MATRIX.md` auto-gen. Generalizable a capabilities, integraciones, versions. | docker-dev-multibrand T-8/T-9 + cementación en /pm-luana SKILL.md |

## Ambientes y dominios definitivos

| Ambiente | Source | Dominio | Cuándo |
|---|---|---|---|
| **Local dev** | Linux (Mint) + `make dev-{brand}` + cloudflared opt-in | `{brand}-dev.nicolify.com` | Tests integraciones OAuth/Clerk/webhooks |
| **Staging (marcha blanca)** | auto-deploy de `main` a cluster/VPS staging shared (infra futura) | `{brand}-test.nicolify.com` | Validación pre-prod con dominio público |
| **Producción** | auto-deploy de `release/{brand}-vX.Y.Z` a servidor brand-específico | `app.{brand}.com` (vitalialat.com, nicolify.com, etc.) | Live para usuarios reales |

## Stories descompuestas (dependencias)

```
S-GIT-STRATEGY-CORE  (foundational — primero)
        ↓
        ├──→ S-DOCKER-DEV-MULTIBRAND  (puede empezar después de core)
        │
        └──→ S-CICD-DEPLOY  (puede empezar después de core)
                 ↓
                 └──→ S-GIT-STRATEGY-HELPERS  (último, helpers + docs)
```

| Story ID | Scope | Tickets | Sub-outcome | Estimate |
|---|---|---|---|---|
| `S-GIT-STRATEGY-CORE` | rules + workflows + hook | T-1..T-9 | git-strategy-revised | ~12-14h |
| `S-DOCKER-DEV-MULTIBRAND` | compose + Dockerfiles + Makefile + infra matrix | T-1..T-10 | docker-dev-multibrand | ~14-16h |
| `S-CICD-DEPLOY` | environments + workflows + manifests + changelog público | T-1..T-9 | cicd-multibrand-deploy | ~16-17h |
| `S-GIT-STRATEGY-HELPERS` | helper scripts + docs runbooks + ADRs | T-10..T-13 | git-strategy-revised | ~6-8h |

**Total:** ~48-55h de `/dev-team`. ~3 sesiones de Sonnet/opencode (cap ~16h efectivas c/u) si se ejecuta en serial. ~2 sesiones si S-DOCKER y S-CICD corren en paralelo (sesiones Claude distintas, worktrees dedicados).

## Capabilities producidas al cerrar este outcome

- **dev-environment-multibrand:** `make dev-{brand}` levanta entorno completo brand-específico en local con dominio.
- **selective-cicd-deploy:** push a `release/{brand}-vX.Y.Z` deploya solo esa brand a su servidor producción.
- **staging-auto-deploy:** push a `main` auto-deploya a staging `{brand}-test.nicolify.com` para marcha blanca.
- **safe-parallel-sessions:** 2-3 sesiones Claude paralelas en worktrees dedicados sin riesgo de pisarse.
- **wip-safety-net:** push a `wip/{slug}` autosave continuo, recovery garantizado en caso de crash del sistema / cambio máquina.
- **infra-matrix-auto:** `make infra-matrix` regenera tabla cross-brand de puertos/dominios/DBs desde SSoT distribuido.
- **changelog-publico-per-brand:** `{brand}/CHANGELOG-PUBLIC.md` Keep-a-Changelog format auto-extracted a release notes.

## Riesgos identificados

| Riesgo | Mitigación |
|---|---|
| Worktrees mal usados (legacy "perdí una semana") | Pattern obligatorio `git worktree add + branch dedicado` (git protege automático contra colisión). Documentado en parallel-safety.md M9-M11. Helper scripts T-10. |
| Servidor staging no disponible al cierre del outcome | Infra staging es trabajo futuro (no scope). Workflow `cd-staging.yml` se deja preparado con server placeholder. Activable cuando Chris decida proveedor. |
| Brands sin dominio prod comprado (comunify, lupulo, saasora, inmoflow, retailly, fixia, guestly, fitflow) | `.env.prod.template` con placeholder. Activable cuando se compre. No bloqueante hoy. |
| Multi-cuenta Claude futuro (otras cuentas, otras máquinas) | Pattern worktree per sesión escala a multi-cuenta + multi-máquina sin cambios. Merge a main vía PR draft cuando llegue el caso. Documentado en parallel-safety.md. |
| Pre-commit hook complejidad (gates dinámicos por branch) | Tests cobertura del hook obligatorios en T-9. Magic comment escape `# wip-fast` documentado. |

## Anti-patterns prohibidos (cementados en rules nuevas)

- ❌ Worktrees humanos sin branch dedicado (cada worktree SU branch wip/*)
- ❌ Push a `main` cuando branch tree está sucio con WIP no commiteado (use `wip/{slug}` para staging WIP)
- ❌ Crear `release/*` desde una branch que no sea `main` (gate workflow)
- ❌ Deploy producción sin pasar por staging (gate convencional, no técnico — disciplina)
- ❌ Skip de pre-commit hook con `--no-verify` (excepto wip/* con magic comment justificado)
- ❌ Hardcoded ports/dominios fuera de `{brand}/config/brand.yaml::infra` (consume INFRA-MATRIX)

## Próximo paso

1. /po redacta `01-spec.md` por story (4 stories total, en orden de dependencia)
2. Chris ratifica cada spec (state refining → refined)
3. /architect cierra ready package por story (03-arch + 04-validators + 05-guidelines + 06-tickets)
4. /dev-team toma 06-tickets.yaml story por story, paralelizando con worktrees lo que se pueda
5. /auditor C1-C5 al final
6. /pm-luana mergea state → done por story
7. Capability promotion check (si patrones surge cross-brand)

## Referencias

- Sub-outcomes: [cicd-multibrand-deploy](./cicd-multibrand-deploy.md) · [docker-dev-multibrand](./docker-dev-multibrand.md) · [git-strategy-revised](./git-strategy-revised.md)
- Decisión fusión `/pm` + `/pm-luana`: commit ff33858 (predecesor a este outcome)
- Paradigm v4 (10 estados macro): `docs/process/pm-redesign-2026-05.md`
- Rules afectadas: `.claude/rules/{git-safety,parallel-safety,git-haiku-delegation}.md`
