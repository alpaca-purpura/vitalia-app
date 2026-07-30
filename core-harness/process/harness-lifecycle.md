# Harness Lifecycle Process (HLP)

> SSoT del proceso de gestión del ciclo de vida del **harness** (skills, rules, agents, hooks, cockpit, templates, docs de proceso) de {workspace.repo_prefix}-platform. Premisa: **tus herramientas son un producto que mantenés.** Diseñado para **un solo operador (Chris)** + Claude. Origen: sesión modernización 2026-06-01. Cement-date: 2026-06-01.

## Por qué existe

Operar el harness (usarlo para construir producto) y mantenerlo (mejorarlo) son **dos concerns distintos**. Mezclarlos = editar una skill a mitad de un feature → contamina el contexto, deja fixes a medias, y rompe cosas (caso voseo-en-línea-1). El HLP separa ambos: las deficiencias que notás operando se **capturan sin fricción** y se **arreglan en lotes ordenados**, nunca mid-feature.

## 1. Captura sin fricción (el corazón)

Un solo archivo: **`docs/process/harness-backlog.md`** (issue-tracker liviano en markdown). Cuando notás algo raro a mitad de trabajo:
- decís *"anotá al harness backlog: X"* o invocás **`/harness-issue "X"`**
- Claude appendea 1 fila (fecha + descripción + severidad + estado `reported`). **No frenás tu flujo de feature.**

## 2. Ciclo de vida del item (5 estados)

```
reported → triaged → ratified → applied → verified
```
Columnas del backlog. `reported` lo pone la captura; `triaged` la pasada de clasificación; `ratified` cuando Chris aprueba el fix; `applied` tras el batch/workflow; `verified` cuando se confirma en vivo (no "pasó el gate", sino *ejercido*).

## 3. Severidad → ruta

| Severidad | Ruta |
|---|---|
| 🔴 silent-killer (rompe en silencio) | **fix inmediato** + commit (excepción a "nunca mid-work") |
| 🟡 quick-win mecánico | próximo **batch** |
| 🔵 decision (criterio de Chris) | **cola de ratificación** (tabla tipo D-1..D-N) |
| 🟣 wave (grande/estructural) | **workflow dedicado** en sesión fresca |

## 4. Cadencia (operable por una persona)

| Frecuencia | Acción |
|---|---|
| **Diario / mientras operás** | solo capturás al backlog. Cero ceremonia. |
| **Al cerrar sesión** | si apareció un silent-killer → fix + commit `fix(harness):` |
| **Cada ~10 sesiones (o semanal)** | triage 5 min (Claude clasifica, Chris ratifica) + batch-apply vía workflow si hay ≥3 quick-wins |
| **Mensual/trimestral (o "huele a drift")** | `/harness-audit-2026` full → catálogo fresco que realimenta el backlog |

## 5. Cómo se ejecuta (sesiones) — la regla que más se usa

- **Liviano** (capturar, triage, cementar proceso, decisiones, fixes de 1-3 archivos) → **en la sesión actual**.
- **Pesado** (aplicar Waves multi-archivo, correr workflows de auditoría/aplicación, revisar diffs grandes) → **sesión fresca** con un **prompt de handoff** (apunta a los SSoT docs: catálogo + session-plan + backlog). Esto evita context-rot: la conversación pesada arranca con contexto limpio.
- El handoff es **un prompt copy-paste** + los docs committeados. Se puede ejecutar cuando sea (mismo worktree, conversación nueva).

## 6. Regla de oro

**Nunca editar el harness en medio de trabajo de producto.** Todo cambio de harness = lote/sesión dedicada + commit `fix(harness):` / `docs(harness):` por pathspec + `SCOPE_GATE_SKIP` con razón (cross-cutting, fase solo-operador). Catalog+propose para todo lo no-trivial: Claude propone el diff, Chris ratifica antes de commitear.

### El apply pipeline (probado punta a punta 2026-06-01)

Loop por **chunk ratificable** — un diff = una ratificación:

1. **Verify-first — la auditoría SOBREESTIMA.** Cada finding del catálogo se verifica contra el **FS real** ANTES de tocar nada. Muchos resultan ya-arreglados o falsos (ej.: ADR-011 ya citaba el path correcto; globs analytics/offer ya OK; los scripts D-5 SÍ faltaban aunque la rule decía "probado live"). Editar sin verificar = propagar ruido. Los **overestimates se capturan** explícitamente (Chris los quiere registrados — son señal de calidad del catálogo).
2. **Editar en lotes DISJUNTOS** vía workflow JS (`agent()` sonnet por archivo, `parallel()`), **sin commit** y **sin `isolation: worktree`** — los edits deben quedar en el working tree del hub para poder mostrar el `git diff`.
3. **Verificación independiente del orchestrator** (opus): revisar el `git diff` real + spot-check de las claims fácticas que citan los sub-agents (NO confiar en su reporte; ej.: confirmar el YAML de `cd-staging.yml`, el conteo real de `def test_`).
4. **Present diff → Chris ratifica.** Nada se commitea sin el ✓ (regla cardinal del HLP).
5. **Commit por pathspec, delegado a Haiku** (>2 archivos) con guardrails verbatim: `git commit <rutas-exactas>` (NUNCA `git add .`/`-A`), `SCOPE_GATE_SKIP=1` con razón en el body, sin `--no-verify`, push; non-fast-forward → STOP.

**Cost-routing del pipeline:** haiku enumera/commitea · **sonnet edita** · **opus sintetiza + verifica el diff + ratifica con Chris**. Mismo principio que la auditoría (§8). Verificación de campos/schemas dudosos (ej. frontmatter CC-2026) → agente `claude-code-guide` o WebFetch a docs oficiales ANTES de mass-edit.

## 7. Roles (solo-operador)

- **Chris** = ratificador + operador (decide, aprueba diffs, opera el harness día a día).
- **Claude** = auditor + aplicador (audita, propone, aplica en batch, verifica).
- Sin review externo; el contrapeso es **catalog+propose** + verificación REAL (ejercer, no "gate verde").

## 8. Auditoría periódica — `/harness-audit-2026`

Workflow JS multi-agente (`.claude/workflows/harness-audit.js`) que enumera todo el harness, audita en paralelo contra los schemas CC vigentes (`docs/learnings/tooling/claude-code-2026-capabilities.md`), y sintetiza un catálogo ratificable (NO edita). Cost-routing: haiku enumera, sonnet audita, opus sintetiza. **Snapshot de schemas verificados embebido** → refrescar cuando salgan features CC nuevas (re-fetch docs + actualizar el baseline).

## 9. Maduración → plugin

Cuando el harness se estabilice, empaquetarlo como **plugin `prenter-harness`** versionado (semver) → tus herramientas pasan a tener "releases" (Wave 5 del roadmap de modernización). Distribución/versionado limpio incluso para una persona.

## Automatización CC-2026 que lo sostiene

- `/harness-audit-2026` saved workflow (`.claude/workflows/harness-audit.js`) — auditoría periódica.
- Extender `learning-detect.sh` para sugerir capturas de harness post-Edit/Bash.
- `memory: user` en agents auditores + architect (acumulan anti-patterns cross-sesión). **Aplicado 2026-06-01** como *enabler* (provisiona el dir `~/.claude/agent-memory/`); activarlo requiere instrucción en el body del agente de *escribir* los anti-patterns recurrentes (Wave 5b). NB: `user`, NO `project` — en hub compartido `project` clobberea entre sesiones.
- hook `PostCompact` → recordar recargar `harness-backlog.md` + catálogo tras compactación.

## Referencias

- `docs/process/harness-backlog.md` — el backlog vivo
- `docs/learnings/tooling/harness-audit-2026-06-01.md` — catálogo de la 1ª auditoría exhaustiva
- `docs/learnings/tooling/claude-code-2026-capabilities.md` — baseline de features CC (schema truth)
- `docs/learnings/tooling/harness-modernization-session-plan.md` — plan + D-1..D-11 ratificadas
- `.claude/skills/harness-issue/SKILL.md` — captura sin fricción
- `.claude/workflows/harness-audit.js` — workflow de auditoría reutilizable
