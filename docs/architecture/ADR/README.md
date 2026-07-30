# Architecture Decision Records (ADR)

Formato Michael Nygard (lightweight). Toda decisión que afecta `core/**`
(cross-module behavior, schema, API contract, abstracción shared) requiere
ADR antes de PR.

## Cuándo escribir ADR

- Nuevo abstract en `core/shared/` consumido cross-brand
- Cambio de contrato API que rompe consumidores
- Schema migration con impacto cross-module
- Nueva abstracción cross-brand
- Bug fix con scope local (no requiere ADR)
- Refactor interno de un módulo sin contrato cambiado
- Documentación o config sin impacto runtime

## ADR template (formato Michael Nygard)

Crear archivo en `docs/architecture/ADR/NNN-titulo-corto.md`:

```markdown
# ADR-NNN: <Título corto>

- **Status:** proposed | accepted | superseded by ADR-MMM
- **Date:** YYYY-MM-DD
- **Deciders:** Chris + (collaborators si aplica)

## Context

<Qué problema resolvemos. Qué fuerzas están en juego.>

## Decision

<Qué decidimos. Una frase clara.>

## Consequences

### Positive
<Qué ganamos.>

### Negative
<Qué cuesta.>

### Neutral
<Qué cambia sin ser bueno o malo.>

## Alternatives considered

1. <Alt A> — <por qué descartada>
2. <Alt B> — <por qué descartada>

## References

- Outcome / story que motivó el ADR
- Issues / PRs relacionados
```

## ADR index (índice)

| # | Título | Status | Date |
|---|---|---|---|
| [001](./001-luana-platform-monorepo-topology.md) | Luana Platform topology (monorepo) | accepted | 2026-05-10 |

## Anti-island enforcement

CODEOWNERS protege `docs/architecture/ADR/**` con review Chris obligatorio.
PR template requiere link a ADR si toca `core/**`. Sin ADR → PR rechazado.
