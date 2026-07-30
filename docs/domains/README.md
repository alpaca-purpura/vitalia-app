# docs/domains/ — DEPRECATED (legacy single-brand snapshot)

> **Status:** read-only legacy. Snapshot single-brand (Nicolify) pre-migración multimarca.
>
> **Razón de existencia:** preservación histórica + algunos tests/agents aún citan paths bajo este dir. NO mover hasta limpieza coordinada.

## Reemplazado por

| Era | Ahora |
|---|---|
| `docs/domains/{module}.md` (single-brand assumption) | `docs/core-modules/{package}.md` (contract público luana-core) |
| `docs/domains/{module}/{redesign,fpos,testing}-2026-04/` | `nicolify/docs/domains/` (es nicolify-specific historical) |
| `docs/domains/INDEX.md` | `docs/core-modules/README.md` |

## Migración pendiente

1. Auditar refs en `.claude/agents/*` y `.claude/skills/*` (varios apuntan acá hoy)
2. Mover contenido nicolify-specific → `nicolify/docs/domains/legacy-pre-multibrand/`
3. Mover contenido genuinamente transversal → `docs/core-modules/`
4. Eliminar este dir

Tracked en outcome futuro Luana core (no scope F1-F6 reorg actual).
