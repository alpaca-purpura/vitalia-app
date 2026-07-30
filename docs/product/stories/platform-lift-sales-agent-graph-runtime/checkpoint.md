---
story_id: platform-lift-sales-agent-graph-runtime
type: technical-story                 # engine-hardening · user_visible:false · zona Infraestructura · /architect ES refiner (WT5)
title: Lift sales_agent engine multibrand-capable — el grafo corre en una marca (ESC-1..6)
brand: platform                       # story platform-level — owner /pm-luana (cross core: sales-agent + platform)

# Release / programa
release: null                         # platform technical-story, sin release de marca
program: null

# Capability lineage
cap_target: null                      # engine-hardening transversal · map_zone infraestructura (motor-agentico) · gate HB-34 no exige cap YAML para fix
cap_change_type: fix                  # bugfix + additivo de engine (relationship/prompt-path/columna + registries EP-3) · sin cap nueva
parent_story: null
predecessor_story: vitalia-fase2-adrian-canal-inbound   # OLA-1 construida en wip/vitalia; su G live-verify surfaceó ESC-4/5/6

state: done                           # ★ TRANSITION reviewing → done (/pm-luana merge, auditor APPROVED, Chris ratified)
phase: MERGED
done_at: 2026-06-22
merge_artifact: 07-merge.md
audit_verdict: APPROVED               # T-ALL-review.md (8/8 checks, 0 regresión, platform downstream 294/0)
build_commit: 5120881a                # feat(sales-agent): engine lift Phase 1 (ESC-4/5/6 + T-DEBT1)
dod_live_verified_skip_reason: "technical-story user_visible:false; el efecto runtime real (grafo en vitalia · mensaje Telegram→reply de Adrián) se ejerce POST merge+sync a vitalia — lo verifica Chris. In-worktree DoD = arch tests por ESC GREEN (independientemente re-corridos por el orchestrator) + diffs = los proven del architect + platform suite verde (ESC-4 downstream)."
chris_verify:
  required: true
  signoff: {by: Chris, date: 2026-06-22, result: SATISFIED, notes: "Ratifica Phase 1 sobre evidencia mecánica (3 fixes spike-proven + 4 arch tests GREEN re-corridos + platform suite verde + diffs == proven + arquitectura multimarca revisada: EP-3/puertos limpios, Phase 2 cierra el cableado). Autoriza chain auditor→done→merge→propagar.", open_items: []}
  rounds: []
reconciled: true                      # zero-drift: el build committeado == el plan proven verbatim (orchestrator verificó diff por diff). spec/arch == realidad, sin scope-delta que reconciliar.
map_zone: infraestructura             # caja = motor-agentico (runtime del trabajador, no feature)
module: sales_agent
cross_module_scope: [sales_agent, platform-crm]   # core/luana-core-sales-agent + core/luana-core-platform (ESC-4)
agent_owner: null                     # technical-story · sin trabajador user-facing propio
last_artifact: 06-tickets.yaml
last_modified: 2026-06-22T00:00:00-05:00

# Phasing (ratificado Chris en el proposal)
phasing:
  phase_1:
    name: runtime
    escs: [ESC-4, ESC-5, ESC-6]
    goal: "grafo CORRE + Adrián responde (testeable: mensaje Telegram → reply). ESTE package."
    state: ready
  phase_2:
    name: features
    escs: [ESC-1, ESC-2, ESC-3]
    goal: "book/match/share (desbloquea OLA-2). Package separado tras cierre Phase 1."
    state: pending

# Promotion governance — esta story ES la ejecución de la proposal accepted
promotion_proposal: docs/promotion-protocol/proposals/2026-06-22-sales-agent-multibrand-graph-runtime.md
proposal_state: accepted              # ratified Chris 2026-06-22 · al merge Phase 2 completa → migrated
proposal_location: wip/vitalia        # ⚠️ el proposal vive en wip/vitalia (no sincronizado a main aún) — leído vía git show

# Verificación (technical · por-efecto)
verification_nature: técnica          # gates + arch tests por ESC + EFECTO runtime real (grafo corre live en vitalia post-merge)
demo_required: false                  # technical-story infra · sin UI · sin demo Chris (G = efecto runtime, no demo manual)
demo_skip_reason: "engine-hardening user_visible:false; el bar es el grafo corriendo live en vitalia (Chris lo verifica post-merge+sync), no una demo UI"
runtime_effect_bar: "grafo sales_agent end-to-end en vitalia: mensaje Telegram real → reply de Adrián + fila conversación/trace/costo en DB + cero traceback. NO 'arch tests verdes'. Se ejerce tras merge a main + sync a vitalia (Chris)."

# Worktree (constraint dura)
worktree: "core efímero wip/core-sales-agent-multibrand (NO editar core desde hub de marca — invisible al venv, learning 2026-06-16). Validación in-place con PYTHONPATH override SIEMPRE."

# Autonomous mode
autonomous_mode: false                # engine + agentic = stake-asimétrico (R23) · Chris ratifica entre fases
autonomous_mode_chain: []

next_action: "Phase 1 build GREEN + verificado (commit 5120881a). autonomous_mode false → PAUSA. Chris ratifica el lift → /auditor (auditor-agentic, review independiente engine stake-asimétrico) → /pm-luana migrate (merge a main + sync vitalia) → Chris ejerce el grafo LIVE en vitalia (bar runtime, cierra G de canal-inbound + Phase 1)"
tickets_count: 4   # T-ESC4 + T-ESC5 + T-ESC6 (runtime) + T-DEBT1 (test-housekeeping)
phase1_status: build_green_verified   # 4/4 arch tests GREEN (re-corridos por orchestrator) · diffs = proven · platform suite verde · message_model.py/marca/alembic/conftest intactos
---

# checkpoint — platform-lift-sales-agent-graph-runtime (Phase 1)

## Estado

`refined → ready` (Phase 1 = ESC-4/5/6 runtime). Package reducido de technical-story:
`03-arch.md` + `04-validators.yaml` + `05-guidelines.md` + `06-tickets.yaml` + `dispatch-plan.md` + `migration_notes.md`.

`/architect` actuó como **refiner** (CTO-al-CEO, WT5) — no consume 01-spec Gherkin; el **contract-spec** es la
proposal accepted (§4) + las decisiones de approach en `03-arch.md § Approach refinements (PROPONE a Chris)`.

## Phase 1 — 3 muros runtime (★ EMPÍRICAMENTE PROBADOS por architect · RED→GREEN + no-regression)

| ESC | Surface | Fix | Estado |
|---|---|---|---|
| ESC-4 | `core/luana-core-platform/.../infrastructure/models/crm.py` L210 (**UNILATERAL** — solo crm.py) | relationship target **module-qualified** | proven · ready |
| ESC-5 | `core/luana-core-sales-agent/.../infrastructure/prompts/base.py` `__init__` | `templates_dir` default **engine-package-relative** + override back-compat | proven · ready |
| ESC-6 | `core/luana-core-sales-agent/.../infrastructure/models/prompt_version_model.py` | columna `tenant_id` (model) + **migración brand-authored** | proven · ready |

## ★ Spike verification (architect-proven · diffs aplicados → probados → revertidos para TDD)

- **ESC-4**: RED `InvalidRequestError: Multiple classes found for path "MessageModel"` (idéntico al live) → fix 1 línea en crm.py → `configure_mappers()` OK con set realista COMPLETO (platform+sales-agent+scheduling+iam+offer-studio + homónimo sintético). ★ **CORRECCIÓN: UNILATERAL** — `LeadModel` es único (vitalia NO homonyma LeadModel, solo MessageModel) → NO se toca `message_model.py:46`.
- **ESC-5**: RED `TemplateNotFound ...'/tmp/src/modules/sales_agent/...'` → fix engine-relative → `get_template` OK desde cwd=/tmp.
- **ESC-6**: RED `AttributeError ...no attribute 'tenant_id'` (`PROMPT_SOURCE=HYBRID` default ejecuta la rama DB) → columna → queries construyen.
- **No-regression PROBADO**: subset DB-persistencia en aislamiento determinístico = baseline==edited (3 failed/37 passed idéntico; las 3 son `sqlite no such table booking_links`, env-gap ajeno).

## ★ Realidad del entorno (CRÍTICO)

Suite completa vía PYTHONPATH-override en este worktree = **FLAKY** (configure_mappers global + conftest sintético AppointmentModel + test stale de colección + sqlite gaps). Gate autoritativo in-worktree = **arch tests por ESC** (ESC-4 en subproceso). Suite completa + downstream ×4 = entorno canónico (`ci-parity` + Postgres), post-merge. Detalle + diffs exactos + código de tests: `03-arch.md` + `verified-arch-tests.md`.

## Hallazgos colaterales (fuera de scope · → /harness-issue)

- `LeadModel.appointments` (crm.py:214) = misma ambigüedad latente que ESC-4; seguro en prod hoy (vitalia sin homónimo AppointmentModel); abordar en Story 8 lift.
- copilot `core/luana-core-platform/.../prompts/base.py:23` = mismo bug-class ESC-5.
- test stale `tests/orchestrator/test_chat_orchestrator_snapshot.py` (import monolítico) + conftest sintético AppointmentModel = tech-debt de tests.

## Hallazgos colaterales (fuera de scope · flaggeados)

- **copilot tiene el mismo bug-class ESC-5**: `core/luana-core-platform/.../prompts/base.py:23` (`templates_dir="src/modules/copilot/..."` + `Path.cwd()`). NO en scope de este lift (proposal es sales-agent). Candidato a `/harness-issue` o sibling-fix cuando se cablee copilot en una marca.
- Posible homónimo engine-interno `LeadModel` (`core/luana-core-crm/.../lead_model.py` vs `core/luana-core-platform/.../crm.py`) — no bloqueó el grafo live; no se toca. Nota para Phase 2 / auditor.
