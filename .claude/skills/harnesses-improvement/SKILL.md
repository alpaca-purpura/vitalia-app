---
name: harnesses-improvement
description: "Stop semanal de mejora continua del harness — lee los 4 carriles del CIL (L1 harness-backlog · L2 learnings · L3 tech-debt · L4 capability-desfasada auto-detect), los muestra (reúsa el board /harness del cockpit), Chris remedia + marca aplicado. Para el barrido exhaustivo (schemas CC / staleness / punteros rotos / overlap) invoca el deep-sweep Workflow harness-audit-2026. Owner /pm-luana. Reemplaza al naming /mejora-semanal. Activa: '/harnesses-improvement', 'stop semanal', 'mejora del harness', 'revisemos los carriles', 'qué hay para reforzar', 'deep sweep del harness', 'auditá el harness'."
when_to_use: "Ritual periódico (semanal o cuando Chris lo pida) para acumular + remediar mejoras del harness. NO mid-feature (HLP regla de oro). Usá el deep-sweep cuando quieras la auditoría exhaustiva del harness."
user-invocable: true
---

# /harnesses-improvement — stop semanal de mejora continua (CIL)

> El ritual de **homologación** del CIL (`docs/process/continuous-improvement.md`). Owner `/pm-luana`, transversal `docs/process/`. **Regla de oro HLP:** NUNCA mid-feature — es la sesión/momento dedicado. SSoT del modelo de 4 carriles: `continuous-improvement.md`.

## Qué hace (no improvisa — lee los 4 carriles de sus hogares reales)

| Carril | Lee de | Acción |
|---|---|---|
| **L1 · harness** | `docs/process/harness-backlog.md` (board `/harness` del cockpit) | mostrar OPEN por estado/carril; Chris remedia en lote (apply-pipeline HLP §6) |
| **L2 · producto/skills-arq** | `docs/learnings/` + `{brand}/docs/learnings/` + `docs/process/learnings.md` (cockpit tab Learnings = la pantalla: estado `applied` en frontmatter) | **Triage con decisión forzada — hasta 3 `pending` por stop** (práctica retro: pocas acciones, cerradas). Cada uno muere en una de 4 salidas (jerarquía de efectividad): gate/hook > rule/skill > proposal core > `wont-apply` consciente. Marcar con los botones del cockpit (✓ aplicado · ⬆ promovido · ✗ no aplica). **Regla de tendencia:** 3+ pending con el mismo tag (🔥 en el cockpit) → UNA acción sistémica contra la causa, no parches |
| **L3 · deuda técnica** | `docs/process/tech-debt.md` | priorizar; agendar fixes |
| **L4 · capability-desfasada** | auto-detect: `scripts/cap_doctor.py` + caps pre-cement-date + survivors heredados del mutation gate | refrescar/retirar caps stale |

## Flujo del stop

1. **Step 0** — worktree detection (`@.claude/rules/step-0-worktree.md`) · este ritual corre donde estés (homologa en merge→main→sync · sin worktree especial).
2. **Leer los 4 carriles** (tabla arriba). El cockpit `/harness` board (HB-26, extendido con badge de carril) es la pantalla del stop.
2b. **Docs-graph (DOCS-SWEEP gate · 2026-06-10):** correr `make docs-graph` — reporta huérfanos nuevos bajo root `docs/` (reporte docs/process/DOCS-GRAPH.md — gitignored, lo genera el comando) + regenera `docs/process/HARNESS-DOCS.manifest`. Huérfano nuevo → mover a `legacy/` o citarlo desde su consumidor. Cuarentena borrable: `legacy/2026-06-10-docs-sweep/INVENTORY.md`.
3. **Presentar** a Chris: OPEN por carril + severidad, candidatos a refuerzo, caps stale (L4), huérfanos docs-graph (2b).
4. **Remediar en lote** con el **apply-pipeline (HLP §6)**: verify-first → editar disjunto → verificación del diff → `make machinery-check` 0 regresiones → Chris ratifica → commit por pathspec (Haiku).
5. **Marcar** `applied`/`verified` en el hogar de cada ítem (L2: el cockpit escribe `applied:` en el frontmatter del learning — la métrica del loop es que "esperando decisión" BAJE entre stops).

## Deep-sweep (barrido exhaustivo · invoca el workflow)

Cuando Chris quiere la auditoría EXHAUSTIVA del harness (frontmatter schemas Claude Code, staleness, punteros rotos, overlap entre skills/rules) → invocar:

```
Workflow({ name: 'harness-audit-2026' })
```

Es el motor pesado (Enumerate→Audit→Synthesize, multi-agente, NO edita — produce catálogo ratificable). Su salida alimenta L1 (harness-backlog). El workflow vive en `.claude/workflows/harness-audit.js` — reachable SOLO vía este ritual (no es un comando suelto).

## Anti-patterns

- ❌ Correr mid-feature (rompe la regla de oro HLP — esto es momento dedicado).
- ❌ Escribir aprendizajes DENTRO de este skill (viven en sus hogares · el ritual LEE + remedia).
- ❌ Editar el harness sin `make machinery-check` 0 regresiones + ratificación Chris (apply-pipeline).
- ❌ Tratar el deep-sweep como editor (NO edita — produce catálogo; el editor es el apply-pipeline).

## Referencias

- `docs/process/continuous-improvement.md` — CIL (modelo 4 carriles · SSoT)
- `docs/process/harness-lifecycle.md` — HLP (apply-pipeline §6, verify-first §6.1, regla de oro)
- `docs/process/harness-backlog.md` — L1 · `docs/process/tech-debt.md` — L3
- `.claude/rules/learning-capture.md` — L2 taxonomía
- `.claude/workflows/harness-audit.js` — deep-sweep engine (workflow `harness-audit-2026`)
- `scripts/cap_doctor.py` · `scripts/mutation_gate.py` — fuentes L4
