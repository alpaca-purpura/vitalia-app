# Architect Autonomous Mode + Explicit Agent Assignment — operational detail (loaded on-demand by /architect, moved from .claude/rules/ 2026-05-30)

**Origen:** conversación 2026-05-27 — Chris pidió: (a) opción de declarar story autonomous desde architect→done en misma sesión, (b) que architect dicte agentes/skills específicos por ticket (no general-purpose default), (c) Playwright guidance scoped a la story (no broad replicate que rompa otras features).

**Cement-date:** 2026-05-27. **Aplica a:** `/architect` skill + `architect-orchestrator` agent + `/dev-team` skill.

## Regla cardinal

`/architect` debe producir, además de los 4 artifacts del ready package (`03-arch.md` + `04-validators.yaml` + `05-guidelines.md` + `06-tickets.yaml`), un **dispatch plan** explícito que:

1. Declare `autonomous_mode` (default `false` — Chris opt-in explícito al ratificar ready)
2. Asigne **agente + skills** exactos por ticket (NUNCA `general-purpose` por default)
3. Especifique **Playwright visual scope discipline** (qué rutas tocar, qué NO tocar)
4. Provea **handoff matrix** ticket→agent→model con costo estimado

## autonomous_mode flag

Agregar al `checkpoint.md` cuando state=ready:

```yaml
state: ready
phase: READY_PACKAGE_CLOSED
autonomous_mode: false                # default. Chris opt-in true al ratificar
autonomous_mode_chain: [dev-team, auditor, pm-merge]   # qué encadena auto si true
autonomous_mode_ratified_by: chris    # required si true
autonomous_mode_ratified_at: 2026-MM-DDTHH:MM:SS-05:00
autonomous_mode_caps:
  max_iterations_per_ticket: 10
  max_audit_iterations: 3
  max_total_cost_usd: 5.00
  max_wall_clock_minutes: 90
  on_cap_exceeded: "state=blocked + escalate Chris"
```

### Cuándo autonomous_mode = true es seguro

- Story es **ui-story standard** (CRUD/list/detail/form/dashboard) sin agentic
- ≤5 tickets en 06-tickets.yaml
- Ningún ticket toca `core/luana-core-*/` (engine ban)
- Ningún ticket toca `{other_brand}/...`
- Ningún ticket es `production_code: true + AGENTIC` (flagship-only — Chris debería supervisar)
- Validators tienen `must_pass: true` claros, no `pass_k` ambiguos

### Cuándo autonomous_mode debe ser false (HARD)

- Cualquier ticket AGENTIC `production_code: true` (requiere Chris supervise el tier flagship)
- Story toca engine (`/pm-luana` promotion gate obligatorio)
- Story toca cross-brand (`/pm-luana` outcome)
- Validators incluyen `pass_k` con thresholds < 0.66 (eval ruido riesgo)
- Hot-fix repro_verified: false (necesita Chris ratify diagnosis)
- Cualquier story marked `defer_audit: true` en checkpoint

## Explicit agent_assignment por ticket

Cada ticket en `06-tickets.yaml` MUST incluir bloque `assignment`:

```yaml
- id: T-1
  title: "BE endpoint create-appointment"
  surface: BE
  production_code: true
  owner_eligibility: [opencode, workhorse, flagship]
  assignment:
    primary_agent: builder-backend       # ★ explícito — NO general-purpose
    model_preference: workhorse           # default; opencode fallback ok (tiers → project.config.yaml::models)
    must_load_skills:                     # verbatim, builder spawn cita estos
      - backend-expert
      - .claude/rules/tenant-isolation.md
      - .claude/rules/backend-ddd.md
      - .claude/rules/tdd-mandatory.md
    must_load_artifacts:
      - "{brand}/docs/product/stories/{id}/01-spec.md § Scenario {n}"
      - "{brand}/docs/product/stories/{id}/03-arch.md § BE"
      - "{brand}/docs/product/stories/{id}/04-validators.yaml § test_construction_plan"
    forbidden_to_touch:
      - "core/luana-core-*/src/"
      - "{other_brand}/"
      - "{brand}/backend/src/modules/{brand}/{copilot,sales_agent}/"
    rationale: "BE CRUD non-agentic, workhorse sweet spot; flagship_required:false"

- id: T-2
  title: "AGENTIC tool wire create-appointment"
  surface: AGENTIC
  production_code: true
  owner_eligibility: [flagship]            # HARD R23
  assignment:
    primary_agent: builder-agentic        # ★ explícito
    model_preference: flagship              # HARD per R23
    must_load_skills:
      - sales-agent-expert | copilot-expert  # según módulo
      - claude-api
      - .claude/rules/anti-duplication.md
    must_load_artifacts:
      - "{brand}/docs/product/stories/{id}/02-design-agentic.md (full)"
      - "{brand}/docs/product/stories/{id}/03-arch.md § AGENTIC"
    forbidden_to_touch:
      - "core/luana-core-copilot/src/"
      - "core/luana-core-sales-agent/src/"
    rationale: "AGENTIC production code R23 → tier flagship obligatorio. NUNCA opencode/workhorse."

- id: T-3
  title: "FE form create-appointment"
  surface: FE
  production_code: true
  owner_eligibility: [opencode, workhorse, flagship]
  assignment:
    primary_agent: builder-frontend
    model_preference: workhorse
    must_load_skills:
      - frontend-expert
      - playwright-expert                   # SI test_construction_plan.playwright_required=true
      - .claude/rules/frontend-fsd.md
      - .claude/rules/spanish-text.md
    must_load_artifacts:
      - "{brand}/docs/product/stories/{id}/01-spec.md § Wireframes / UI"
      - "{brand}/docs/product/stories/{id}/03-arch.md § FE"
    forbidden_to_touch:
      - "{brand}/frontend/src/components/ui/"      # Shadcn primitives
      - "{brand}/frontend/src/lib/api/fetchClient.ts"
    rationale: "FE standard form workhorse sweet spot"
```

## Playwright visual scope discipline

**Problema observado:** dev-team a veces toca componentes shared / globales para "arreglar" fidelidad visual de UNA story → rompe otras pantallas downstream.

**Regla:** `04-validators.yaml § test_construction_plan` debe explicitar:

```yaml
playwright_visual_scope:
  story_scope_routes:
    - "/agenda/nueva"           # ÚNICA ruta donde aplicar visual changes
    - "/agenda/[id]/edit"
  story_scope_components:
    - "{brand}/frontend/src/features/scheduling/components/AppointmentForm.tsx"
    - "{brand}/frontend/src/features/scheduling/components/SlotPicker.tsx"

  forbidden_visual_changes:
    paths:
      - "{brand}/frontend/src/components/ui/"        # Shadcn primitives — escalate /pm-{brand}
      - "{brand}/frontend/src/components/shared/"    # cross-feature shared
      - "{brand}/frontend/src/app/layout.tsx"        # app shell
    reasons:
      - "Cambios visuales en primitives Shadcn impactan TODA la app"
      - "Cambios en shared impactan otros features no tocados por esta story"
      - "Cambios en layout app shell romperían navegación global"

  if_visual_change_needed_outside_scope:
    action: "STOP. Document in T-{n}-impl-log.md. Escalate /pm-{brand} para spec extension o spawn dedicated cross-cutting story."

  playwright_assertions_scope:
    - "Assertions visual SOLO sobre story_scope_routes + story_scope_components"
    - "NUNCA snapshot global page screenshot fuera scope (use bounded boxes)"
    - "Si snapshot diverge en area no relacionada (toolbar, sidebar) → flag like-for-like comparison + check baseline drift en otra story (no fix here)"

  non_egoismo_clause:
    description: "Si bug visible en otro feature/ruta NO tocada por esta story es REAL (no es snapshot drift), reportar en T-{n}-impl-log.md sección 'Cross-story observed bugs' y opcionalmente abrir hotfix-story-id separada. NO arreglar inline (rompe scope discipline)."
```

## Handoff matrix output (architect debe producir)

Al cerrar ready package, architect genera `dispatch-plan.md` (1 sólo file ≤ 100 líneas):

```markdown
# Dispatch plan — Story {brand}/{id}

## autonomous_mode
- value: false                   # Chris opt-in al ratificar
- chain_if_true: [/dev-team → /auditor → /pm-{brand} merge]
- caps: {iterations: 10, audit_iter: 3, cost_usd: 5.00, walltime: 90min}

## Ticket→Agent→Model→Cost matrix

| T-id | Title | Surface | Agent | Model | Est. cost | Est. time |
|---|---|---|---|---|---|---|
| T-1 | BE endpoint create-appointment | BE | builder-backend | workhorse | $0.30 | 25 min |
| T-2 | AGENTIC tool wire | AGENTIC | builder-agentic | flagship (R23) | $1.20 | 35 min |
| T-3 | FE form + e2e | FE | builder-frontend | workhorse | $0.40 | 30 min |
| Total | — | — | — | — | **$1.90** | **~90 min** |

## DAG dependencies
T-1 → T-2 → T-3 (sequential)

## Playwright visual scope
- story_scope_routes: [/agenda/nueva, /agenda/[id]/edit]
- forbidden: components/ui/, components/shared/, app/layout.tsx
- non_egoismo: report cross-story bugs en T-n-impl-log § Cross-story observed bugs

## Recommended invocation if autonomous

```bash
# Chris opt-in autonomous chain
echo 'autonomous_mode: true' >> {brand}/docs/product/stories/{id}/checkpoint.md
# /dev-team picks up T-1, completes T-1, auto-handoff T-2 → T-3 → /auditor → /pm-{brand} merge
```

## Recommended invocation if manual

```
/dev-team <brand>: {brand}, ticket: T-1     # Chris elige cuándo arrancar cada ticket
```
```

## Anti-patterns prohibidos

- ❌ Architect produciendo 06-tickets.yaml sin bloque `assignment` per ticket
- ❌ `primary_agent: general-purpose` (subagent generic — NO existe primary_agent generic)
- ❌ AGENTIC ticket con `model_preference: sonnet` o `opencode` (viola R23)
- ❌ Architect omitiendo `playwright_visual_scope` cuando story es ui-story
- ❌ Architect declarando `autonomous_mode: true` sin Chris ratify (architect propone, Chris ratifica)
- ❌ `must_load_skills` vago ("relevant skills") en lugar de lista verbatim citable
- ❌ `forbidden_to_touch` omitido (builder debe saber qué NO tocar explícitamente)
- ❌ Falta `rationale` en assignment (why this agent + this model, no just default)
- ❌ Autonomous chain sin caps (riesgo cost runaway)

## Enforcement layers

| Layer | Mecanismo | Status |
|---|---|---|
| 1 | `/architect` Step 7 expand: produce dispatch-plan.md además de 06-tickets.yaml | ⏳ skill update |
| 2 | `06-tickets.yaml` template incluye sección `assignment` mandatory | ⏳ template update |
| 3 | `04-validators.yaml` template incluye `playwright_visual_scope` mandatory si ui-story | ⏳ template update |
| 4 | `/dev-team` Step 0 lee dispatch-plan.md + respeta `assignment.primary_agent` (NO override sin razón) | ⏳ skill update |
| 5 | `/dev-team` Step 2 builder spawn cita `must_load_skills` verbatim + verifica T-{n}-result.md report "Skills consulted" | ✅ already in architect SKILL.md |
| 6 | Auditor Phase D detecta si dev-team violó `forbidden_to_touch` o `playwright_visual_scope` → CHANGES_REQUESTED | ⏳ auditor SKILL update |
| 7 | Autonomous chain hook detecta caps_exceeded → halts chain + state=blocked + escalate Chris | ⏳ hook TBD |

## Referencias

- `.claude/skills/architect/SKILL.md` — skill principal a modificar
- `.claude/skills/dev-team/SKILL.md` — consumer de assignment + dispatch-plan
- `.claude/skills/auditor/SKILL.md` — verificador post-hoc
- `docs/specs/templates/06-tickets-template.yaml` — template a expandir con assignment block
- `docs/specs/templates/04-validators-template.yaml` — template a expandir con playwright_visual_scope
- `.claude/rules/auditor-self-fix-policy.md` — R23 (AGENTIC production_code → tier flagship obligatorio)
- `.claude/rules/anti-duplication-refining.md` — prior art scan (precede assignment)
