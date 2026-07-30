# CLAUDE.md Hierarchy + Sistema Overlay Auto-load

> **Slim stub (context-rot pass 2026-05-30).** Detalle completo en `docs/rules-detail/claude-md-overlay.md` — load on-demand vía Read. **Origen:** conversación 2026-05-27 — cement-date 2026-05-27.

## Regla cardinal

`CLAUDE.md` sigue hierarchy de 2 niveles — Claude Code los carga via **walking ancestors del cwd** (built-in, sin hook custom):

| Nivel | Archivo | Cap | Cuándo carga |
|---|---|---|---|
| Root | `CLAUDE.md` | **≤270 líneas** | Siempre (cualquier worktree) |
| Sistema overlay | `{sistema}/CLAUDE.md` | **≤165 líneas** | Auto cuando cwd cae dentro de `{sistema}/` |

**Anti-loop:** sistema overlay NUNCA re-importa root vía `@CLAUDE.md` (ya está cargado por walking). Solo extiende contenido sistema-específico.

## Cuándo carga el detalle

- Bootstrap de sistema nuevo (saasora, inmoflow, etc.) → leer estructura canónica de las 10 secciones del overlay + procedure bootstrap.
- Root o sistema overlay superan su cap (270/165 líneas) → leer qué mover y adónde.
- Duda sobre qué secciones van en root vs sistema overlay vs `docs/rules-detail/` → leer tabla de estructura.

## Anti-patterns (top 3 — lista completa en el detalle)

- ❌ Root `CLAUDE.md` >270 líneas o sistema overlay >165 líneas (mover detalle a `docs/rules-detail/` o `{sistema}/docs/domains/`)
- ❌ Sistema overlay importando `@../CLAUDE.md` (duplica context — root ya cargado por walking)
- ❌ Sistema overlay con contenido que aplica cross-sistema (debe ir a root o `.claude/rules/`)

## Referencias

- `docs/rules-detail/claude-md-overlay.md` — **detalle completo** (estructura root 15 secciones, estructura overlay 10 secciones, tabla detection por cwd, hook complementario, bootstrap procedure)
- `CLAUDE.md` (root) — SSoT cross-platform
- `{sistema}/CLAUDE.md` — ejemplo overlay activo
- `{sistema}/CLAUDE.md` — overlay canónico de referencia para sistemas nuevos (no hay template dedicado aún)
