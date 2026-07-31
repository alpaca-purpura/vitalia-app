# Git Workflow — vitalia-app (trunk-based · 2 devs + agentes)

> **SSoT del flujo git** desde 2026-07-31. Reemplaza el triple-branch `wip/* → main → release/*` heredado del monorepo luana-platform (archivado en `docs/archive/2026/multibrand-legacy/`). Enforcement primario = **hooks locales** (`make install-hooks` — obligatorio en onboarding); GitHub Actions está en modo **deferred** (repo privado plan Free, sin servidor real) → la CI de GitHub es señal *advisory* hasta el upgrade a GitHub Team. La versión enforce-able para agentes vive en `.claude/rules/git-safety.md` (slim stub → apunta acá).

## Modelo

```
main (trunk — ÚNICO branch permanente, deployable siempre)
 ├─ story/{story-id}   ← vida corta (horas): build de una story → squash-merge → borrar
 ├─ fix/{slug}         ← bugfix/hotfix chico → squash-merge → borrar
 └─ tags vX.Y.Z        ← OBJETIVO: deploy prod por tag (hoy: branches release/vitalia-vX.Y.Z)
```

- La historia de `main` = 1 commit por story/cambio (squash-merge siempre).
- Los branches de story/fix se borran al mergear. No hay branches de larga vida.

## Situación → camino

| Situación | Camino |
|---|---|
| Docs / chores / config (Chris) | Commit directo a `main` (pre-commit full + pre-push gate corren) |
| Story de producto (Chris) | `story/{story-id}` → build agentic → **review IA con contexto fresco** (`/code-review`) → squash-merge local (o PR self-merge) → borrar branch |
| Story **tier de riesgo** — auth, tenant-isolation, migraciones, pagos, comportamiento de agentes | **PR obligatorio + review humano** además del review IA |
| Nuevo dev — primer mes | **TODO vía PR**: CI advisory corre → review IA → Chris revisa el review IA + skim del diff → squash-merge |
| Nuevo dev — después del primer mes | Mismas reglas tiered que Chris (directo a main solo docs/chores; stories con review IA; tier de riesgo con PR + humano) |
| Release a prod | Hoy: branch `release/vitalia-vX.Y.Z` desde `main` validado (ver § Releases). Objetivo: tag anotado `vX.Y.Z` |
| Hotfix prod | Default: fix en `main` (vía `fix/{slug}`) + release nueva. Branch desde el tag SOLO si prod divergió de main (raro) |

## Reglas por persona

**Chris (owner):** puede pushear directo a `main` para docs/chores/config. Stories siempre en `story/{id}` con review IA de contexto fresco antes del squash-merge. Tier de riesgo → PR + su propio review humano del diff completo.

**Nuevo dev:** primer mes TODO vía PR (sin excepciones — incluye docs). Después, mismas reglas tiered. Día 1: `make install-hooks` antes del primer commit — sin hooks no hay gates.

**Agentes (Claude):** siguen `.claude/rules/git-safety.md`. Commit+push multi-file → delegar a Haiku (`git-haiku-delegation.md`). Nunca deciden merges a `main` de stories — eso lo gatekea `/pm-vitalia` (Fase F del story closure gate).

## Releases

**Mecanismo actual:** `.github/workflows/cd-prod.yml` escucha push a branches `release/**` con formato `release/vitalia-vX.Y.Z`. GitHub Actions está en modo **deferred** (sin servidor real provisionado) → el workflow existe pero no se garantiza que corra; el deploy real es manual. Detalle del modo deferred: `.claude/rules/github-actions-deferred.md`.

**Objetivo (al provisionar prod):** deploy por **tag anotado `vX.Y.Z`** sobre `main` + GitHub Release con changelog generado desde Conventional Commits. Migrar `cd-prod.yml` de `release/**` a `tags: v*` es parte de ese corte — NO se editan workflows hasta entonces.

## Enforcement local (los hooks SON el gate)

| Hook | Qué hace |
|---|---|
| `pre-commit` | Dispatcher de **23 checks** (`scripts/git-hooks/checks/`). **Light** en `story/*` y `wip/*` (voseo + ruff check + format sobre staged); **full** en `main` y todo lo demás (agrega SSoT freshness, capability gates, PII scanners, story-closure, etc.) |
| `pre-push` | Push a `main` exige marker `.git/ci-parity-passed-vitalia-<sha>` que deja `scripts/ci-parity.sh` en verde. Con el sentinel `.ci-parity-deferred` presente → **advisory** (avisa, no bloquea); `cross_check_3` (cap↔código) sigue HARD |
| `make ci-parity` | Suite full equivalente a CI — obligatorio antes de squash-merge a `main` |

Instalación: `make install-hooks` (symlinks desde `scripts/git-hooks/`). Bypass (`--no-verify`, `CI_PARITY_OVERRIDE=1` sin ratificar) = prohibido.

## Prohibiciones

- **`git pull`**: pull-merge y pull-rebase PROHIBIDOS. Relajación única (2026-07-31): **`git pull --ff-only` permitido SOLO sobre branch limpio** (working tree clean) — necesidad diaria con 2 devs. Si el ff falla → STOP, reportar, NO forzar merge.
- `git push --force` / `--force-with-lease` — sin excepción.
- `git commit --no-verify` — sin excepción.
- Amend de commits ya pusheados — sin excepción.
- `git add .` / `-A` / `-u` — stage siempre por pathspec exacto.
- `git revert` / `git reset --hard` sin aprobación explícita de Chris.
- Commitear `.env*` / credentials / secrets.
- Push non-fast-forward que falla → STOP y reportar (no "resolverlo" con pull-merge).

## Hábitos (sobreviven del flujo anterior)

- **Push cada ≤30 min** si hay cambios significativos (sobre el story branch).
- **Squash-merge siempre** — main limpio, 1 commit por cambio.
- **Conventional Commits**: `<type>(<scope>): <desc>` — types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `perf`, `ci`.
- **Stage por pathspec exacto**: `git add path/al/archivo` — `git status` antes de stagear.
- **Branch check al empezar sesión**: `git status --short && git branch --show-current && git log --oneline -3`.

## Cuando se sume el 2º dev (checklist día 1 del equipo)

1. **Invitación** como colaborador al repo privado (Settings → Collaborators).
2. **Upgrade a GitHub Team** (el plan Free no soporta branch protection en repos privados).
3. **Branch protection en `main`**: require PR antes de merge + required status check (el job de CI) + prohibir force-push/deletion.
4. **Reactivar CI hard**: borrar el sentinel `.ci-parity-deferred` + `make install-hooks` (el propio sentinel lista los triggers y el pre-requisito: agregar stage `test` al Dockerfile de vitalia). Desde ahí el pre-push a main bloquea de verdad y la CI de GitHub deja de ser advisory.
5. Onboarding del dev: `docs/onboarding/README.md` (incluye `make install-hooks` como paso obligatorio).
6. Primer mes del dev: TODO vía PR (ver tabla arriba).

## Referencias

- `.claude/rules/git-safety.md` — rule enforce-able para agentes (slim stub de este doc)
- `.claude/rules/git-haiku-delegation.md` — delegación commit+push a Haiku
- `.claude/rules/github-actions-deferred.md` — modo deferred de GitHub Actions
- `docs/process/story-closure-gate.md` — quién mergea una story a done (`/pm-vitalia` Fase F)
- `docs/onboarding/README.md` — onboarding del developer nuevo
- `docs/archive/2026/multibrand-legacy/process/git-workflow-multibrand.md` — flujo anterior (histórico, no normativo)
