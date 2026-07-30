# Architect Autonomous Mode + Explicit Agent Assignment

> **Slim stub (context-rot pass 2026-05-30).** Cuerpo operativo completo en `.claude/skills/architect/references/autonomous-mode.md` — carga on-demand cuando `/architect` se activa. **Origen:** conversación 2026-05-27 — Chris pidió: (a) opción de declarar story autonomous desde architect→done en misma sesión, (b) que architect dicte agentes/skills específicos por ticket (no general-purpose default), (c) guidance de visual scope E2E scoped a la story. **Cement-date:** 2026-05-27.

## Regla cardinal

`/architect` debe producir, además del ready package (`03-arch.md` + `04-validators.yaml` + `05-guidelines.md` + `06-tickets.yaml`), un **dispatch plan** (`dispatch-plan.md`) que: (1) declare `autonomous_mode` (default `false` — Chris opt-in al ratificar), (2) asigne **agente + skills exactos** por ticket (NUNCA `general-purpose`), (3) especifique la **disciplina de visual scope E2E** (rutas + componentes tocables / prohibidos), y (4) provea la **handoff matrix** ticket→agent→model con costo estimado.

## Cuándo carga el detalle

- Al producir `06-tickets.yaml` → leer `autonomous-mode.md § Explicit agent_assignment por ticket` para el schema `assignment:` completo (primary_agent, model_preference, must_load_skills, must_load_artifacts, forbidden_to_touch, rationale)
- Al producir `04-validators.yaml` con story ui-story → leer la sección de visual scope E2E de `autonomous-mode.md` para el bloque `playwright_visual_scope`
- Cuando Chris pregunta si la story puede correr autonomous → leer `autonomous-mode.md § autonomous_mode flag` (criterios safe/HARD false + caps)

## Anti-patterns (top 3 — lista completa en el detalle)

- ❌ `06-tickets.yaml` sin bloque `assignment` per ticket (o con `primary_agent: general-purpose`)
- ❌ Ticket AGENTIC con `model_preference: sonnet` o `opencode` (viola R23 — tier **flagship** obligatorio, `models.flagship` del seam)
- ❌ Architect declarando `autonomous_mode: true` sin Chris ratify (architect propone, Chris ratifica)

## Referencias

- `.claude/skills/architect/references/autonomous-mode.md` — **cuerpo operativo completo** (autonomous_mode flag schema, agent_assignment YAML examples ×3 surfaces, playwright_visual_scope schema, dispatch-plan.md template, enforcement layers)
- `.claude/rules/auditor-self-fix-policy.md` — R23 (AGENTIC production_code → tier **flagship** obligatorio)
- `.claude/rules/anti-duplication-refining.md` — prior art scan (precede assignment)
- `docs/specs/templates/06-tickets-template.yaml` — template a expandir con assignment block
- `docs/specs/templates/04-validators-template.yaml` — template a expandir con playwright_visual_scope
