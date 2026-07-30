# CLAUDE.md Hierarchy + Brand Overlay Auto-load — detail (moved from .claude/rules/ 2026-05-30, load on-demand)

**Origen:** conversación 2026-05-27 — Chris pidió: (a) root `CLAUDE.md` liviano (agentic + topología + commands esenciales), (b) brand overlay `{brand}/CLAUDE.md` que extienda root cuando worktree está en esa brand, (c) auto-load según cwd path detection.

**Cement-date:** 2026-05-27. **Aplica a:** root `CLAUDE.md` + `{brand}/CLAUDE.md` (4 activas + 6 futuras bootstrap).

## Regla cardinal

`CLAUDE.md` sigue hierarchy de 2 niveles:

1. **Root `/CLAUDE.md`** — siempre cargado. Contiene: filosofía agentic dev, topología 1-liner, comandos esenciales, paradigm v4 estados macro, tabla `.claude/rules/`, links a docs/. **≤270 líneas total.**

2. **Brand overlay `/{brand}/CLAUDE.md`** — auto-cargado vía Claude Code's built-in path-based loading cuando cwd cae dentro `{brand}/`. Contiene: product vision pointer, verticales target, brand-specific gates (HIPAA-lite si vitalia, B2B si nicolify, etc.), brand-specific anti-patterns, brand-specific commands. **≤165 líneas total.**

Claude Code carga automáticamente cualquier `CLAUDE.md` que esté en el cwd o ancestros (working directory walking). Por eso colocar `{brand}/CLAUDE.md` hace que se cargue auto cuando sesión arranca en `{brand}/...` o `~/Proyectos/luana-{brand}/...`.

## Estructura root `CLAUDE.md` (canonical)

Secciones obligatorias (orden):

1. **Header** — 1-liner identificando luana-platform (multimarca, modular monolith DDD, uv/pnpm workspace, Docker-First)
2. **Brand overlay pointer** — instrucción explícita: "cuando trabajés dentro de `{brand}/`, su `CLAUDE.md` overlay se carga auto"
3. **Topology (1-liner)** — árbol ASCII compacto
4. **Workspace tooling** — uv + pnpm + Docker
5. **Paradigm v4 — 10 estados macro** — tabla compacta
6. **10 Brand verticals quick reference** — tabla
7. **Brand → Core mapping (Extension SDK)** — 1-liner + link
8. **Git Workflow (1-liner)** — triple-branch
9. **Critical Rules tabla** — ~20 rules auto-loaded
10. **Conditional Rules tabla** — stub → skill on-demand
11. **Resume protocol** — bootstrap commands
12. **Workspace bootstrap (fresh clone)** — quickstart
13. **Anti-telephone-game** — subagent return contract
14. **Vision pointer** — `docs/product/vision.md`
15. **`@AGENTS.md`** — import AGENTS.md complementario

**Cap:** 270 líneas. Si excede → mover detalle a `docs/rules-detail/` con pointer.

## Estructura brand overlay `{brand}/CLAUDE.md` (canonical)

Secciones obligatorias (orden):

1. **Header** — "Brand {Name} overlay — auto-cargado cuando cwd cae dentro `{brand}/`"
2. **Product vision pointer** — link a `{brand}/docs/product/vision.md` + 3-5 bullets de qué es la brand
3. **Verticales target** — tabla compacta (qué profesiones/industria específica)
4. **Brand-specific gates** — HIPAA-lite si vitalia, B2B contracts si nicolify, Creator economy si comunify, Restauración KDS si lupulo
5. **Brand-specific anti-patterns** — qué NUNCA hacer en esta brand (regulación, voz, GTM, etc.)
6. **Brand-specific commands** — port, dev-up, alembic, tests específicos
7. **Brand-specific skills** — `/pm-{brand}` + skills que aplican
8. **Cross-brand learning sources** — qué brand consultar para prior-art (nicolify default principal)
9. **Brand checkpoint pointer** — `{brand}/docs/product/checkpoint.md`
10. **Bootstrap brand-specific** — env, .env.dev, migrations

**Cap:** 165 líneas. Si excede → mover detalle a `{brand}/docs/domains/` con pointer.

## Detection automática + protección

Claude Code carga `CLAUDE.md` por **walking ancestors del cwd** (built-in). No requiere hook custom. Sin embargo, para garantizar coherencia:

| Cwd | CLAUDE.md cargados | Notas |
|---|---|---|
| `~/Proyectos/luana-platform/` (principal, main) | `CLAUDE.md` (root) | sin overlay (estás en raíz) |
| `~/Proyectos/luana-vitalia/` (canónico wip/vitalia) | `CLAUDE.md` (root) + `vitalia/CLAUDE.md` (overlay) | overlay aparece en worktree path |
| `~/Proyectos/luana-vitalia/vitalia/backend/src/...` | root + `vitalia/CLAUDE.md` | walking ancestors |
| `~/Proyectos/luana-vitalia-story-X/` (efímero) | root + `vitalia/CLAUDE.md` | si manifest brand=vitalia, overlay debería estar |
| `~/Proyectos/luana-protocol/` (efímero protocol) | `CLAUDE.md` (root) | sin overlay (no brand) |
| `~/Proyectos/luana-core-X/` (efímero core lift) | `CLAUDE.md` (root) | sin overlay (core es root) |

**Anti-loop:** brand overlay NUNCA debe re-importar root via `@CLAUDE.md` (root ya está cargado por walking). Solo extender contenido brand-específico.

## Hook complementario (opcional pero recomendado)

`.claude/hooks/claude-md-overlay-check.sh` — SessionStart hook que verifica:
- Si cwd cae dentro `{brand}/` o `~/Proyectos/luana-{brand}-*/` PERO `{brand}/CLAUDE.md` no existe → emite advisory ("brand overlay missing, considera crear via `_pm-brand-template/`")
- Si cwd es PRINCIPAL pero `vitalia/CLAUDE.md` falta → silent (overlay sólo se carga cuando cwd brand)

Hook NO carga overlay (Claude Code lo hace built-in) — sólo valida existencia.

## Anti-patterns prohibidos

- ❌ Root `CLAUDE.md` >270 líneas (mueve detalle a `docs/rules-detail/` o brand overlay)
- ❌ Brand overlay >165 líneas (mueve a `{brand}/docs/domains/`)
- ❌ Brand overlay importando `@../CLAUDE.md` (root ya se carga via walking — duplica context)
- ❌ Brand overlay con contenido que aplica cross-brand (debió ir a root o `.claude/rules/`)
- ❌ Root `CLAUDE.md` con vision específica de UNA brand (debió ir a brand overlay)
- ❌ Editar root o brand overlay sin actualizar `MEMORY.md` entry si cambia paradigm
- ❌ Hardcodear paths absolutos `/home/chris/...` en CLAUDE.md (usar `${WS}` o paths relativos)
- ❌ Cargar overlay manualmente via Read en bootstrap (Claude Code lo hace auto — no duplicar)

## Enforcement layers

| Layer | Mecanismo | Status |
|---|---|---|
| 1 | Root `CLAUDE.md` cap 270 líneas — pre-commit hook `wc -l CLAUDE.md` check | ⏳ TBD |
| 2 | Brand overlay cap 165 líneas — pre-commit hook check si `{brand}/CLAUDE.md` modificado | ⏳ TBD |
| 3 | Hook SessionStart `claude-md-overlay-check.sh` advisory si overlay falta | ⏳ a crear |
| 4 | `_pm-brand-template/` enforce schema brand overlay al bootstrap brand nueva | ⏳ template update |
| 5 | Audit Cat 12 (anti-duplication) detecta cross-brand content en brand overlay → flag | ⏳ auditor update |

## Bootstrap de overlay para brand nueva

Cuando user pide "bootstrap brand {slug}" (saasora, inmoflow, retailly, fixia, guestly, fitflow):

1. Tomar como referencia `vitalia/CLAUDE.md` (overlay canónico de ejemplo; no hay template dedicado aún) → crear `{slug}/CLAUDE.md`
2. Reemplazar placeholders: `{BRAND_NAME}`, `{VERTICAL_SHORT}`, `{PORT_BE}`, `{PORT_FE}`, etc.
3. Escribir `{slug}/docs/product/vision.md` (puede arrancar como stub)
4. Cementar pointer en MEMORY.md (entry sub-section "brand-specific")
5. Commit en mismo PR de bootstrap

## Referencias

- `CLAUDE.md` (root) — SSoT cross-platform
- `vitalia/CLAUDE.md` (ejemplo overlay)
- `vitalia/CLAUDE.md` — overlay canónico de referencia para brands nuevas (no hay template dedicado aún)
- `.claude/hooks/claude-md-overlay-check.sh` — advisory hook
- `.claude/rules/parallel-safety.md` D2 — topology worktrees (consumer de overlay detection)
