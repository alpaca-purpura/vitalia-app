# Guía de Contribución — Luana Platform

Esta guía cubre el flujo completo de trabajo para contribuir al monorepo `luana-platform`.

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
`core`, `nicolify`, `vitalia`, `comunify`, `lupulo`, `ci`, `docs`, `repo`

### Ejemplos

```
feat(core): agregar abstracción BaseCallbackHandler para agentes AI
fix(nicolify): corregir filtro tenant_id en query de offers
docs: actualizar ARCHITECTURE con topología de subfolders
chore(ci): actualizar pnpm/action-setup a v4
```

## Flujo de trabajo (solo-operador · Triple-Branch)

Chris trabaja solo. No hay reviews multi-developer ni ramas `feat/`. El flujo es:

1. Desarrollar en `wip/{brand}` (autosave, commits frecuentes con Conventional Commits)
2. TDD obligatorio: tests primero, implementación después
3. Push frecuente a `wip/{brand}` — nunca más de 30 min sin push si hay cambios significativos
4. Squash-merge a `main` cuando la story cierra (`reviewing → done`) — gatekeado por `/pm-{brand}`
5. `release/{brand}-vX.Y.Z` se crea desde `main` validado para cada despliegue a producción

**Prohibido:** `git pull`, `git fetch && merge` automático, `git push --force`, ramas `feat/` sueltas, `git add .` / `-A`.
Sync `wip/{brand} ↔ main` SOLO vía `scripts/git/sync-from-main.sh`.

GitHub Actions están en modo **deferred** (sentinel `.ci-parity-deferred`). La calidad se enforce con hooks locales (`scripts/git-hooks/pre-commit` + `pre-push`) y `make ci-parity`.

Ver detalle completo en `.claude/rules/git-safety.md` y `.claude/rules/parallel-safety.md`.

## Reglas ADR (Architecture Decision Records)

Cualquier cambio que toque `core/**` (nuevas abstracciones, cambios de contrato,
schema migrations con impacto cross-module) **requiere ADR** antes de abrir PR.

Ver el proceso completo en [docs/architecture/ADR/README.md](architecture/ADR/README.md).

### Cuándo es obligatorio un ADR

- Nuevo abstract en `core/luana-core-*/` consumido cross-brand
- Cambio de contrato API que rompe consumidores
- Schema migration con impacto cross-módulo
- Nueva abstracción cross-brand

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
BRAND=vitalia  # o nicolify / comunify / lupulo

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
