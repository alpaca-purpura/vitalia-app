# Learning Capture System

> **Slim stub (context-rot pass 2026-05-30).** Detalle completo en `docs/rules-detail/learning-capture.md` — load on-demand vía Read. **Origen:** conversación 2026-05-27 — cement-date 2026-05-27.

## Regla cardinal

Cada aprendizaje vive en un archivo `.md` dedicado bajo un path canónico. **MEMORY.md sólo guarda pointer + 1-line hook** — nunca el contenido.

**★ Ciclo de vida (2026-06-11):** capturado NO es estado final. Cada learning lleva `applied:` en su frontmatter (`pending` ausente-default · `applied` · `promoted` · `wont-apply`; `promotable: no` ⇒ referencia, no espera acción). El triage lo fuerza el stop `/harnesses-improvement` (hasta 3 `pending` por sesión, jerarquía: gate/hook > rule/skill > proposal core > descarte consciente) y el cockpit (tab Learnings) lo escribe con un click. La métrica del loop: "esperando decisión" BAJA entre stops.

| Tipo | Path canónico |
|---|---|
| Técnico transversal (≥2 sistemas) | `docs/learnings/{date}-{slug}.md` |
| Negocio per-sistema | `{sistema}/docs/learnings/{date}-{slug}.md` |
| Process/paradigm | `docs/process/learnings.md` (append) |
| Tooling/workspace | `docs/learnings/tooling/{slug}.md` |

**Naming:** `YYYY-MM-DD-{kebab-slug}.md`.

**★ Ruteo al CIL (proceso v5 §5.7):** estos paths SON el **carril L2** del CIL (`docs/process/continuous-improvement.md`). Al cerrar story (`L · story-closure`), `/pm-{sistema}` + `/auditor` rutean cada aprendizaje al carril: producto/arq → **L2** (estos paths, sin forkear la taxonomía) · proceso/tooling → **L1** (`harness-backlog.md` vía `/harness-issue`) · deuda código/infra → **L3** (`docs/process/tech-debt.md`) · cap stale → **L4** (auto-detect cap_doctor/survivors). El stop `/harnesses-improvement` los homologa. Relaja el `learnings.md` per-story a "un lugar donde se acumulen" — cero archivo huérfano.

## Cuándo carga el detalle

- Chris dice "aprendamos de esto" / "capturá esto" / "/aprende" o equivalentes → **Trigger 1 mandatory**: STOP flujo actual, clasificar, proponer slug, escribir archivo, agregar pointer MEMORY.md.
- Hook `.claude/hooks/learning-detect.sh` sugiere post-Edit/Bash → **Trigger 2 advisory** (nunca captura sin ratificación Chris).
- Auditor identifica pattern recurrente (≥2 stories) → **Trigger 3**: sección "Suggested learning capture" en `T-{n}-review.md`.

## Anti-patterns (top 3 — lista completa en el detalle)

- ❌ Escribir contenido del aprendizaje DENTRO de `MEMORY.md` (rompe pointer-first)
- ❌ Capturar aprendizaje sin ratificación Chris (especialmente hook auto-trigger)
- ❌ Learning técnico capturado en `{sistema}/docs/learnings/` cuando aplica cross-sistema

## Referencias

- `docs/rules-detail/learning-capture.md` — **detalle completo** (template canónico, pointer schema MEMORY.md, promotion path learning→rule, cleanup periódico, enforcement layers)
- `docs/process/learnings.md` — process-level learnings
- `MEMORY.md` — índice pointer-first
- `CLAUDE.md` § Critical Rules — tabla rules cementadas
