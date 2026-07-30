# Learning Capture System — detail (moved from .claude/rules/ 2026-05-30, load on-demand)

**Origen:** conversación 2026-05-27 — Chris pidió sistema que evite que memory.md crezca sin control, capture aprendizajes cross-brand (técnicos) y per-brand (negocio), con árbol navegable de `.md` files referenciado pointer-first.

**Cement-date:** 2026-05-27. **Aplica a:** TODAS las sesiones Claude Code en luana-platform.

## Regla cardinal

Cada aprendizaje **debe vivir en un archivo `.md` dedicado** bajo un path canónico según su naturaleza. **MEMORY.md sólo guarda pointer + 1-line hook** — nunca el contenido del aprendizaje.

### Clasificación + path canónico

| Tipo | Naturaleza | Path canónico | Indexado en |
|---|---|---|---|
| **Técnico transversal** | Patterns, anti-patterns, framework gotchas, integraciones aplicables ≥2 brands | `docs/learnings/{date}-{slug}.md` | `MEMORY.md` § cross-portfolio |
| **Negocio per-brand** | Verticales, regulación, GTM, buyer personas, pricing, competidores específicos a 1 brand | `{brand}/docs/learnings/{date}-{slug}.md` | `MEMORY.md` § brand-specific (sólo si activamente trabajando esa brand) |
| **Process/paradigm** | Cambios al flujo /pm-/po-/architect-/dev-team-/auditor, gates nuevos, ADRs metodológicos | `docs/process/learnings.md` (append) + ADR si decisión cementada | `MEMORY.md` § process |
| **Tooling/workspace** | Comandos, scripts, hooks, IDE setup, MCP servers, environment quirks | `docs/learnings/tooling/{slug}.md` | `MEMORY.md` § workspace operacional |
| **Cockpit ↔ doctrina iteration** (v2 cement 2026-05-27) | Cuando una iteración del cockpit (mockup o impl) revela una mejora del proceso o doctrina cap_change_type/release/chris-input que no estaba clara → captura como `process` | `docs/process/learnings.md` (append) | `MEMORY.md` § process |

**Naming convention:** `YYYY-MM-DD-{kebab-slug}.md`. Ej: `2026-05-27-clerk-storage-state-freshness-gate.md`.

## Trigger system (cuándo capturar)

### Trigger 1 — Frase explícita del usuario (mandatory)

Cuando Chris dice **"aprendamos de esto"**, **"esto es un aprendizaje"**, **"capturá esto"**, **"/aprende"**, o equivalentes coloquiales (vocabulario expansivo: "esto hay que recordarlo", "anota esto para futuro"):

1. STOP cualquier flujo en curso (no descartar contexto).
2. Determinar tipo (técnico transversal | negocio per-brand | process | tooling) — preguntar a Chris si ambiguo.
3. Determinar brand (si negocio per-brand) — inferir del worktree actual + confirmar.
4. Proponer `slug` (kebab-case, ≤60 chars).
5. Escribir archivo en path canónico siguiendo template (abajo).
6. Agregar pointer a `MEMORY.md` (1 línea: `- [Slug](path) — hook ≤120 chars`).
7. Confirmar ratificación a Chris ("aprendizaje capturado en {path}").

### Trigger 2 — Hook auto-sugiere (advisory, never blocking)

Hook `.claude/hooks/learning-detect.sh` corre post-`Edit`/`Write`/`Bash` y emite system-reminder al modelo cuando detecta patterns:

| Pattern detectado | Hook acción |
|---|---|
| Commit body contiene "fix forward" + tests reproducer | Sugerir captura técnica (bug + root cause + test pattern) |
| Comentario en código `# WHY:` o `// WHY:` introducido | Sugerir captura del razonamiento (puede ser invariant técnico transversal) |
| Spec/handoff cita "process improvement" o "lesson learned" | Sugerir captura process |
| Decisión arquitectónica nueva (ADR-* creado o accepted) | Sugerir captura cross-link ADR ↔ learning |
| User dice "esto no funcionó" / "esto rompió" / "ya nos pasó" | Sugerir captura anti-pattern |

Hook **NUNCA captura sin ratificación de Chris** — sólo sugiere via system-reminder al siguiente turn del modelo. Modelo evalúa relevancia + pregunta a Chris si conviene capturar.

### Trigger 3 — Auditor descubre learning durante review

Cuando `/auditor` finaliza una story y identifica un pattern recurrente (≥2 stories repiten mismo bug/issue/improvement), incluir en `T-{n}-review.md` sección "Suggested learning capture" → Chris ratifica al merge → `/pm-{brand}` ejecuta captura como parte del merge commit.

## Template canónico (técnico transversal)

```markdown
---
title: "{Slug en title case}"
date: 2026-MM-DD
type: technical | business | process | tooling
brands_affected: [vitalia, nicolify, comunify, lupulo]   # técnico transversal lista todas las que aplica
brand: vitalia                                            # business per-brand: 1 sola brand
origen: "story-id | bug-id | session-date | ADR-XXX | manual-capture"
ratified_by: chris
tags: [clerk, auth, freshness, storage-state, e2e]       # 3-7 tags grep-friendly
---

# {Título}

## Contexto

¿Qué situación generó el aprendizaje? (2-4 líneas, factual)

## Aprendizaje

La regla / pattern / anti-pattern verbatim. Cementado para que futuras sesiones lo apliquen sin redescubrir.

## Aplicación práctica

- **Cuándo aplica:** triggers concretos
- **Cómo aplica:** acción específica
- **Cuándo NO aplica:** excepciones (si las hay)

## Ejemplo (opcional)

Snippet código / config / comando que ilustra. Mantener < 30 líneas. Si más → linkear archivo real del repo.

## Referencias

- [Spec/story original]({brand}/docs/product/stories/{id}/01-spec.md)
- [ADR relacionado](docs/architecture/luana-platform/ADR-NNN-*.md)
- [Rule cementada](.claude/rules/*.md)   # si el learning se promovió a rule
- [Memory entry](memory/{slug}.md)         # cross-link a MEMORY entry
```

## Pointer schema en MEMORY.md

`MEMORY.md` es índice — NUNCA contenido. Cada entrada **1 línea ≤150 chars**:

```markdown
- [{Title}]({path}) — {hook ≤120 chars que explique por qué importa al futuro Claude}
```

Ejemplos:
```markdown
- [Clerk storage state freshness gate](docs/learnings/2026-05-27-clerk-storage-state-freshness-gate.md) — E2E auth Clerk requiere check freshness pre-test, retry+sanity, no cachear >5min
- [Vitalia HIPAA-lite LatAm 6 países](vitalia/docs/learnings/2026-05-27-hipaa-lite-latam-marco.md) — Habeas Data CO + LFPDPPP MX + Ley 25.326 AR + LGPD BR + Ley 29733 PE + Ley 19.628 CL obligan a Vitalia consentimiento digital + retención 10-20 años + encripción at-rest
```

## Promotion path: learning → rule

Un learning se promueve a rule (`.claude/rules/*.md`) cuando:
- Se citó ≥3 veces en sesiones distintas como referencia ("ya nos pasó", "ver learning X")
- Auditor lo marca como enforce-able (decision tree, anti-pattern, gate)
- Chris ratifica explícitamente "esto debe ser rule"

Workflow promotion:
1. `/pm-luana` o Chris identifica el learning como rule-candidate
2. Crear `.claude/rules/{slug}.md` (formato rule, no learning) referenciando learning original
3. Marcar learning con `## Promoted to rule` section + link
4. Agregar pointer rule a `CLAUDE.md` § Critical Rules (tabla actualizar)
5. Memory entry: actualizar pointer del learning a apuntar a rule (rule wins SSoT)

## Cleanup periódico de MEMORY.md (rule shrink)

Cada 6 meses Chris hace pass de cleanup:
- Entries marcados `deprecated`/`obsolete` → archive (mover a `memory/_archive/{year}/`)
- Entries duplicados con rules cementadas → mantener pointer a rule, eliminar duplicado
- Learnings nunca citados >12 meses → evaluar si still valid; si sí, mantener; si no, archive
- Target: `MEMORY.md` ≤ 50 entries activas (umbral)

`MEMORY.md` capped at 200 lines (frontmatter del agente trunca después). Mantenerlo <150 líneas.

## Anti-patterns prohibidos

- ❌ Escribir contenido del aprendizaje DENTRO de `MEMORY.md` (rompe pointer-first)
- ❌ Capturar aprendizaje sin ratificación Chris (especialmente hook auto-trigger)
- ❌ Archivo learning sin frontmatter `tags:` (rompe grep-discovery)
- ❌ Slug ambiguo / sin fecha en filename (rompe orden cronológico)
- ❌ Learning técnico capturado en `{brand}/docs/learnings/` cuando aplica cross-brand (debió ser `docs/learnings/`)
- ❌ Learning negocio capturado en `docs/learnings/` cuando es 100% brand-specific
- ❌ Duplicar learning ya existente (grep antes de capturar — keyword + tags)
- ❌ Promote learning a rule sin agregar pointer a CLAUDE.md § Critical Rules
- ❌ Capturar "decisión efímera" como aprendizaje permanente (ej. "hoy usamos lib X pero podríamos cambiar") — eso va en checkpoint, no learning

## Enforcement layers

| Layer | Mecanismo | Status |
|---|---|---|
| 1 | Hook `.claude/hooks/learning-detect.sh` sugiere captura post-Edit/Bash | ⏳ a crear |
| 2 | Hook `.claude/hooks/memory-pointer-only.sh` valida que MEMORY.md no contenga blocks >5 líneas | ⏳ a crear |
| 3 | `.claude/skills/auditor/SKILL.md` Phase D agrega "Suggested learning capture" si detecta pattern recurrente | ⏳ TBD |
| 4 | `scripts/learning/capture.sh` CLI helper para captura ratificada Chris | ⏳ a crear |
| 5 | Pre-commit hook detecta cambios `MEMORY.md` con bloques >5 líneas → bloquea + sugiere refactor | ⏳ TBD |
| 6 | `/pm-luana` bootstrap Step 0.5 reporta nuevos learnings de los últimos 30 días | ⏳ TBD |

## Referencias

- `scripts/learning/capture.sh` — CLI helper (autenticado Chris)
- `.claude/hooks/learning-detect.sh` — auto-suggest hook
- `docs/process/learnings.md` — process-level learnings (legacy + futuros)
- `docs/learnings/` — root para learnings técnicos transversales
- `{brand}/docs/learnings/` — root per-brand para learnings negocio
- `MEMORY.md` — índice pointer-first (~/.claude/projects/.../memory/MEMORY.md)
- `CLAUDE.md` § Critical Rules — tabla rules cementadas (destino de learnings promovidos)
