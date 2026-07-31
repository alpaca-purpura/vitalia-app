# Guía de Contribución — vitalia-app

Esta guía cubre el flujo completo de trabajo para contribuir al repo `vitalia-app` (marca vitalia + engine vendored `core/`).

## Conventional Commits

Todos los commits deben seguir el formato [Conventional Commits](https://www.conventionalcommits.org/):

```
<tipo>(<scope>): <descripción corta>

[cuerpo opcional — explica el "por qué", no el "qué"]

[footer opcional — referencias a tickets/stories/outcomes]
```

### Tipos permitidos

| Tipo | Cuándo usarlo |
|---|---|
| `feat` | Nueva funcionalidad |
| `fix` | Corrección de bug |
| `refactor` | Refactorización sin cambio funcional |
| `docs` | Solo documentación |
| `test` | Agregar o modificar tests |
| `chore` | Tareas de mantenimiento (deps, config, CI) |
| `perf` | Mejoras de rendimiento |
| `ci` | Cambios en workflows de CI/CD |

### Scopes sugeridos

Usa el nombre del workspace member o área afectada:
`core`, `vitalia`, `ci`, `docs`, `repo`

### Ejemplos

```
feat(core): agregar abstracción BaseCallbackHandler para agentes AI
fix(vitalia): corregir filtro tenant_id en query de offers
docs: actualizar ARCHITECTURE con topología de subfolders
chore(ci): actualizar pnpm/action-setup a v4
```

## Flujo de trabajo (trunk-based)

**SSoT: [`git-workflow.md`](git-workflow.md)** — léelo antes de tu primer commit. Resumen:

1. `main` es el único branch permanente. Por story: branch `story/{story-id}` de vida corta (horas) → squash-merge → borrar. Bugfix chico: `fix/{slug}`.
2. TDD obligatorio: tests primero, implementación después.
3. Push frecuente al story branch — nunca más de 30 min sin push si hay cambios significativos.
4. Stories llevan review IA con contexto fresco (`/code-review`) antes del merge; el **tier de riesgo** (auth, tenant-isolation, migraciones, pagos, comportamiento de agentes) exige PR + review humano. Dev nuevo: TODO vía PR el primer mes. El merge a `done` lo gatekea `/pm-vitalia`.
5. Releases: hoy `release/vitalia-vX.Y.Z` desde `main` validado (Actions deferred); objetivo = tag `vX.Y.Z`.

**Prohibido:** `git pull` (salvo `--ff-only` sobre branch limpio), `git push --force`, `git commit --no-verify`, amend de pusheados, `git add .` / `-A` / `-u`.

GitHub Actions están en modo **deferred** (sentinel `.ci-parity-deferred`). La calidad se enforce con hooks locales (`make install-hooks` → `scripts/git-hooks/pre-commit` + `pre-push`) y `make ci-parity`. Los protocolos multi-worktree/multi-sesión del monorepo quedaron archivados en `docs/archive/2026/multibrand-legacy/process/` (histórico, no normativo).

## Reglas ADR (Architecture Decision Records)

Cualquier cambio que toque `core/**` (nuevas abstracciones, cambios de contrato,
schema migrations con impacto cross-module) **requiere ADR** antes de abrir PR.

Ver el proceso completo en [docs/architecture/ADR/README.md](architecture/ADR/README.md).

### Cuándo es obligatorio un ADR

- Nuevo abstract en `core/luana-core-*/` (engine) consumido por la marca
- Cambio de contrato API que rompe consumidores
- Schema migration con impacto cross-módulo
- Nueva abstracción del engine

### Cuándo NO se necesita ADR

- Bug fix con scope local (un módulo, sin contrato cambiado)
- Refactor interno sin cambio de contrato
- Documentación, config, o CI

## Español neutro LatAm

Todo texto user-facing en esta plataforma usa **español neutro latinoamericano**:
- Tuteo (`tú`, `tienes`, `puedes`) — sin voseo
- Sin regionalismos marcados
- Ortografía correcta con tildes y ñ

Ver `.claude/rules/spanish-text.md` para el glosario completo.

## Quality gates

Antes de abrir PR, verificar localmente:

```bash
WS=$(git rev-parse --show-toplevel)
BRAND=vitalia

# Python lint (venv raíz)
cd ${WS}/${BRAND}/backend && ${WS}/.venv/bin/ruff check src/ tests/

# Python tests
cd ${WS}/${BRAND}/backend && ${WS}/.venv/bin/pytest -x -q --tb=short

# TS lint + type-check
cd ${WS}/${BRAND}/frontend && npx tsc --noEmit && npx eslint src/ --cache

# TS tests
cd ${WS}/${BRAND}/frontend && npx vitest run --coverage

# Full CI gate (obligatorio pre squash-merge a main)
make ci-parity
```

## Licencia

Este software es propietario. Ver [LICENSE](../LICENSE) para más detalles.
