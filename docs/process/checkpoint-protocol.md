# Checkpoint Protocol — Resume sessions

> Cada story tiene `checkpoint.md` propio (vive junto al resto de artefactos de la story).
> Cualquier sesión nueva lee checkpoints PRIMERO antes de hacer nada.

## Por qué existe

Multi-instancia Claude Code (Chris) + sesiones que mueren mid-build + múltiples stories activas = perder contexto es caro.

`checkpoint.md` resuelve:
1. Qué sesión está activa en este nivel
2. Qué fue lo último escrito
3. Qué se debe hacer next
4. Si hay bloqueos / si es seguro tocar

## Estructura

Ver `../specs/templates/checkpoint-template.md`.

Campos críticos:
- `phase` — fase actual del nivel
- `status` — pending | in-progress | done | blocked
- `last_artifact` — último archivo escrito
- `last_modified` — timestamp
- `next_action` — qué hace la próxima sesión / agent
- `parallel_safe` — ¿otra sesión puede tocar?
- `audit_iterations` — para cap (story-level)

## Ubicación canónica

```
{brand}/docs/product/stories/{story-id}/
├── checkpoint.md          ← story-level (única granularidad)
├── chris-input.md
├── 01-spec.md
├── 03-arch.md
├── 04-validators.yaml
├── 05-guidelines.md
├── 06-tickets.yaml
└── 07-merge.md
```

## Reglas de update

| Quién toca | Cuándo updatea |
|---|---|
| `/pm` | Crear story. Cerrar phases. Aplicar merge. |
| `/po` | Tras aprobar `01-spec.md`. |
| `/ux-{ui,agentico}` | Tras escribir `02-design-*.md`. |
| `/architect` | Tras escribir `06-tickets.yaml`. |
| `/dev-team` | Por ticket: cambio state. |
| `/auditor` | Tras escribir `T-{n}-review.md` y `REVIEW-final.md`. |

> Nota: el hook `post-edit-checkpoint.sh` fue removido 2026-05-06. La actualización de `last_artifact` + `last_modified` ahora es responsabilidad explícita del skill que cierra el handoff (escribe el campo en el frontmatter del checkpoint).

### Frontmatter edit discipline (cement 2026-05-28 — causa raíz "story no aparece en cockpit")

Cuando una IA (skill/agente) edita el frontmatter de `checkpoint.md`, MUST:

1. **Actualizar la key EXISTENTE en su lugar — NUNCA appendear una key nueva con el mismo nombre.** Antes de escribir `phase: X`, buscar si ya hay un `phase:` en la cabecera y reemplazar ESE valor. Una key top-level duplicada (ej. `phase:` dos veces) produce **YAML inválido** → `gray-matter`/`js-yaml` tiran `duplicated mapping key` → el cockpit no puede parsear el checkpoint y la story desaparece del board (o cae a `state: idea`).
2. **Migrar keys legacy borrando la vieja.** Si encuentras cruft legacy (`outcome:`, un segundo `phase:` de templates pre-consolidación-SDD), elimina la línea vieja en el mismo edit — no convivan dos.
3. **Preferir reescritura estructurada del bloque** sobre `Edit` quirúrgico que inserta líneas sueltas (writers del cockpit serializan un objeto → keys únicas por diseño). Si editas a mano, relee la cabecera completa primero.

**Defensa-en-profundidad (no depende de que la IA recuerde):**
- **Cockpit fail-loud:** `app/api/stories/route.ts` ya NO silencia un checkpoint malformado — muestra badge rojo "⚠ checkpoint inválido" en la card con el mensaje del error YAML.
- **Pre-commit Section 17:** bloquea el commit de cualquier `checkpoint.md` con keys top-level duplicadas (override emergencia `CHECKPOINT_DUPKEY_SKIP=1`).

Estas dos capas mecánicas garantizan que el fallo no vuelva a ser **silencioso** (cockpit) ni llegue a **committearse** (hook), independientemente de qué agente o cómo escribió la cabecera.

**Campo `type` (cement 2026-05-30, ADR-011):** `type ∈ {ui-story, service-story, agentic-story, bugfix}`. `bugfix` = tipo lite (arreglo/completion quirúrgico, repro-first, sin diseño nuevo) — requiere `repro_verified: true` antes de `developing`. Ver `docs/process/lifecycle.md` § Tipos de story.

## Resume protocol — paso a paso

Cuando cualquier agent/sesión arranca o retoma:

```bash
# 1. Identificar brand + story activa
git status --short && git branch --show-current && git log --oneline -3
cat {brand}/docs/product/checkpoint.md          # brand-level state

# 2. Ver stories en curso (developing/developed/reviewing)
ls {brand}/docs/product/stories/
cat {brand}/docs/product/stories/{id}/checkpoint.md

# 3. Verificar parallel_safe
# si parallel_safe=false → otra sesión está activa, NO TOCAR sin coordinar

# 4. Verificar blocked_reason
# si blocked → escala a Chris, no proceder

# 5. Ejecutar next_action
# leer artefacto previo (last_artifact) → producir siguiente
```

## Estados conflict

- 2 sesiones tocan misma story → `parallel_safe=false` + última sesión espera
- Si `parallel_safe=true` y dos artefactos diferentes (story tiene varios archivos), OK paralelo

## Anti-patterns

- ❌ Empezar trabajo sin leer checkpoint
- ❌ Saltarse phases (ej. /architect sin spec ratificada)
- ❌ No actualizar checkpoint tras escribir artefacto
- ❌ Ignorar `blocked_reason`

## Crash recovery (R27 2026-05-05)

System hangs / computer crashes / network blip pueden interrumpir mid-pipeline.
Para que recovery sea trivial, cada agent + orchestrator MUST:

### Subagent contract (write artifacts EARLY)

Cada subagent escribe su output a disco apenas tiene contenido suficiente
— NO bufferea hasta el final. Pattern:

| Agent | Artifact | Write trigger |
|---|---|---|
| `context-builder` | `CONTEXT-BRIEF.md` | Skeleton at Step 0, fill Edits per Step. Crash mid-build → partial brief + audit log explica what's missing. |
| `context-validator` | `CONTEXT-BRIEF-validation.md` | Skeleton at Step 0, fill Edits per Step. |
| `gate-runner` | `gate-output.json` + `gate-logs/iter-N-*.log` | Raw log streamed via `tee` during execute. JSON written + verified post-condition (R22). |
| `builder-{be,fe,agentic}` | `T-{n}-impl-log.md` | Write skeleton at Step 1. Append per fase. `T-{n}-result.md` + commit hash AFTER push. |
| `auditor-{be,fe,agentic}` | `T-{n}-review.md` | Write skeleton early, fill cat scores incrementally. |

### Orchestrator contract (frequent commits + push)

`/dev-team` + `/auditor` orchestrator (Claude main session) MUST:

- Commit cada artefacto downstream apenas terminado (never batch ≥3 artefactos)
- `git push origin wip/{brand}` después de cada commit (no acumular >2 commits unpushed)
- Update `checkpoint.md` story-level con `last_artifact` + `last_modified` + `next_action`

Razón: crash recovery = `git log --oneline -5` + leer `checkpoint.md` =
contexto restaurado en <30 seconds. Sin push frecuente, perdés horas de
work si crash + machine no boots.

### Resume from crash workflow

Sesión nueva post-crash:

```bash
# 1. State estable
git status --short                                        # debe estar limpio
git log --oneline -5                                      # confirmar commits llegaron remoto

# 2. Identificar brand + story en progreso
WS=$(git rev-parse --show-toplevel)
BRAND=vitalia   # o nicolify/comunify/lupulo
cat ${WS}/${BRAND}/docs/product/checkpoint.md             # brand-level state
ls ${WS}/${BRAND}/docs/product/stories/                   # stories activas
cat ${WS}/${BRAND}/docs/product/stories/{id}/checkpoint.md

# 3. Verificar artefactos del ticket interrumpido
ls -lt ${WS}/${BRAND}/docs/product/stories/{id}/          # artefactos presentes

# 4. Consultar gate-output.json freshness (R22 post-condition)
GATE=${WS}/${BRAND}/docs/product/stories/{id}/gate-output.json
[ -f $GATE ] && jq '.overall.any_fail, .iter' $GATE

# 5. Re-run scoped tests para confirm state consistente
cd ${WS} && .venv/bin/pytest <ticket scope tests> -v

# 6. Continue from `next_action` field of checkpoint.md
```

### Background tasks (Bash run_in_background)

Crash kills bg tasks. NUNCA confíes en bg task output sin re-verify:
- `pytest` corriendo en bg → re-run scoped suite post-crash
- `npm run test:e2e` corriendo en bg → re-run preflight + smoke

Mejor: usar `run_in_background: true` solo para tasks <5min wall-clock.
Tasks largas → use Monitor con persistent: true (sobrevive sesión, no
process crash).

### Tests state recovery

Si crash mid-pytest run, tests no escribieron coverage report ni quizá
.pytest_cache. Re-run desde scope mínimo (ticket-scoped) → escala scope
a downstream (R3) → escala scope a full suite si hay tiempo.

| Scope | Comando | Tiempo aprox |
|---|---|---|
| Ticket-scoped (verificar fix) | `pytest <ticket test paths>` | 10-30s |
| Downstream regression (R3) | `pytest <SSoT downstream targets>` | 1-3min |
| Module-scoped | `pytest tests/modules/{m}/` | 2-5min |
| Full backend | `pytest -x -q --tb=short` | 8-15min |

Empezar siempre por ticket-scoped. Solo escalas si red flag (memory
test pollution, unrelated cascade fail).

Origen R27: PI-12 T-1.bis 2026-05-05 — system crash mid-pytest pero commits
ya pushed → state recovery <2min via git log + scoped re-run. Lección:
commits pequeños + push frecuente = zero pérdida.
