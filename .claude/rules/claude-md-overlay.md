# CLAUDE.md Hierarchy + Brand Overlay Auto-load

> **Slim stub (context-rot pass 2026-05-30 · materializada single-brand 2026-07-31).** Detalle completo en `docs/rules-detail/claude-md-overlay.md` — load on-demand vía Read. **Origen:** conversación 2026-05-27 — cement-date 2026-05-27.

## Regla cardinal

`CLAUDE.md` sigue hierarchy de 2 niveles — Claude Code los carga via **walking ancestors del cwd** (built-in, sin hook custom):

| Nivel | Archivo | Cap | Cuándo carga |
|---|---|---|---|
| Root | `CLAUDE.md` | **≤270 líneas** | Siempre |
| Brand overlay | `vitalia/CLAUDE.md` | **≤165 líneas** | Auto cuando cwd cae dentro de `vitalia/` |

**Anti-loop:** el overlay NUNCA re-importa root vía `@CLAUDE.md` (ya está cargado por walking). Solo extiende contenido vitalia-específico.

## Cuándo carga el detalle

- Root o overlay superan su cap (270/165 líneas) → leer qué mover y adónde.
- Duda sobre qué secciones van en root vs overlay vs `docs/rules-detail/` → leer tabla de estructura.

## Anti-patterns (top 3 — lista completa en el detalle)

- ❌ Root `CLAUDE.md` >270 líneas u overlay >165 líneas (mover detalle a `docs/rules-detail/` o `vitalia/docs/domains/`)
- ❌ Overlay importando `@../CLAUDE.md` (duplica context — root ya cargado por walking)
- ❌ Overlay con contenido que aplica a todo el repo (debe ir a root o `.claude/rules/`)

## Referencias

- `docs/rules-detail/claude-md-overlay.md` — **detalle completo** (estructura root, estructura overlay, tabla detection por cwd, hook complementario)
- `CLAUDE.md` (root) — SSoT del repo
- `vitalia/CLAUDE.md` — overlay activo
