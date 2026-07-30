---
proposal_id: 2026-06-22-sales-agent-multibrand-graph-runtime
state: migrated                  # ★ 2026-06-22 — runtime bar MET: graph runs live in vitalia + brand tools EXECUTE live (share/match, real DB) + downstream ×4 green. Engine SHAs cherry-picked to main b4155f2a + sync-all (comunify/nicolify synced). See migrated_2026-06-22 below.
opened_date: 2026-06-22
opened_by: /pm-luana
ratified_by: Chris               # APPROVED 2026-06-22 (lift) + 2026-06-22 (promote: "ci-parity → si verde, promote+sync")
ratified_date: 2026-06-22

# ── Migration record (E · /pm-vitalia self-paced loop) ──────────────────────────
migrated_2026-06-22:
  promoted_to_main: b4155f2a       # cherry-picked (oldest-first) onto main + pushed:
  promoted_shas:                   #   44e1d4af (Tier1 ESC-7/8/13/15/16) · 64c0e3e1 (stateful ToolRegistry seam)
    - 44e1d4af                     #   ad6a95ff←e43015ee (2.1 tools-hint) · 746878a1←3aff15af (2.2 scheduler resolver)
    - 64c0e3e1                     #   b4155f2a←3d2f3cf8 (uv.lock fastembed==0.5.1)
    - e43015ee
    - 3aff15af
    - 3d2f3cf8
  sync_all: "comunify + nicolify synced; vitalia (origin) already has content under original SHAs (own sync-from-main deferred — dirty ajeno tree + content-dup merge, not functionally needed)"
  downstream_x4: "sales-agent engine net-new=0 (461 pass / 29 pre-existing booking_links+payment_webhook+appointments-MetaData SQLite-isolation) · comunify arch 144 ✓ · nicolify arch 20 ✓ · vitalia live"
  runtime_bar: MET                 # share/match execute live vs real dev DB (in-container seam exercise) + graph live (webhook)
  deferred_NOT_migrated:
    - "ESC-18 (appointment_model.lead removal) — entangled in brand commit b834b130; promote-to-main refuses brand-touching commits. Not urgent (other brands import the full model graph at startup → configure_mappers succeeds; only book's lazy-import path hit it). Reaches main via vitalia squash-merge OR a future extracted shared-only commit."
    - "Phase-2 book_appointment 'agenda' — escalated (ESC-19 scheduling create-lane). Chris ratified leaving escalated."
    - "autonomous-dispatch — ✅ RESOLVED + PROMOTED 2026-06-22 (follow-up to this migrated lift). The F-path 'LLM doesn't dispatch' was NOT agentic/persona — it was 3 wiring bugs in the native-calling path: (1) MultiRoleLLMRouter didn't override generate_with_tools → inherited text-only fallback (native never ran live); (2) EP-3 dotted tool names {brand}.{tool} 400 on DeepSeek/OpenAI (charset ^[a-zA-Z0-9_-]+$) → silent text fallback; (3) dispatch metric undercounted (tool logs only on data-success path). Fix promoted to main: d8c737c4 (fe02df19 native mechanism) + 7a326124 (a24604c0 sanitize+router-delegation+seam-log) + sync-all (comunify+nicolify). Live measured 0 → ~1.0 per-conversation dispatch across phrasings (≥0.5 bar met), default REASONING model, NO persona/routing/model change needed. Learning: docs/learnings/2026-06-22-tools-advertised-executable-not-dispatched.md § fifth pass. Live harness: core/luana-core-sales-agent/scripts/live_dispatch_eval.sh."
    - "uv.lock pillow/hf-hub downgrade impact NOT Docker-validated (ci-parity deferred sentinel). The pin (fastembed==0.5.1) is the corrected state; main was at broken 0.8.0. Validate on next ci-parity/Docker rebuild."

# Phase 1 status (ESC-4/5/6) — reconciled by /pm-vitalia 2026-06-22 after vitalia live-verify
phase_1:
  engine_code: merged            # ff0b9345 → main (auditor APPROVED + 07-merge); ESC-4/5/6 fixes present
  arch_tests: green              # 6/6 ESC arch tests GREEN vs synced engine
  vitalia_adoption: done         # 049_vitalia_prompt_versions_tenant_id applied to dev DB; container engine carries PromptVersion.tenant_id
  runtime_bar: BLOCKED           # ★ the graph still does NOT run end-to-end → NOT migrated (proposal §5 bar = runtime, not arch-green)
  blocker: ESC-7
# ★ Lesson: marking this `migrated` on arch-green was premature (verification-real-not-200). The proposal's own
# §5 bar is "el grafo corre end-to-end en vitalia... NO arch tests verdes". Live-verify (Chris wrote to the bot)
# surfaced ESC-7 → reverted to `accepted`. `migrated` ONLY after Adrián replies live.
esc_7:                           # NEW wall — same onion class as ESC-4/5/6, surfaced once ESC-4 stopped masking it
  package: core/luana-core-platform
  file: src/luana_core_platform/infrastructure/models/crm.py
  line: 214-218
  problem: >-
    LeadModel.appointments = relationship("AppointmentModel", foreign_keys="AppointmentModel.lead_id") references a
    bare class name that no brand registers (vitalia has AppointmentClinicMapModel/AppointmentPaymentModel/
    VitaliaAvailabilitySlotModel, none named AppointmentModel, none with lead_id). configure_mappers() fails on the
    unresolvable target → "name 'AppointmentModel' is not defined" → whole ORM init crashes → "Could not fetch
    tenant" cascade → graph cannot run. The relationship is UNUSED by the graph (grep empty); the comment admits
    "AppointmentModel remains stub-targeted (Story 8 lift pending)" — a lift that never landed.
  fix: >-
    Engine (core, /pm-luana — brand cannot edit core). Minimal: remove the dead `appointments` relationship from
    engine LeadModel (unused + dangling). Then re-exercise the graph in vitalia until Adrián replies — there may be
    further onion layers (e.g. SaleModel.offer→ProductModel import order) that only surface once ESC-7 clears.
  status: pending
brand_adoption:
  vitalia: "049_vitalia_prompt_versions_tenant_id (ESC-6 brand-authored migration, wip/vitalia, applied to dev DB)"
phase_2:
  status: in_progress            # engine wiring (ESC-1/2/3) DONE on wip/vitalia; OLA-2 tool handlers pending (Tier 2.4)
  escs:
    ESC-1: done                  # 3aff15af — scheduler_provider_for_tenant resolves tenants.config_json
    ESC-2: done                  # 64c0e3e1 (stateful ToolRegistry + merged dispatch) + e43015ee (prompt advertises)
    ESC-3: done                  # 64c0e3e1 stage-scope (ExtensionTool.stage_scope) + is_extension_tool_in_stage
  remaining: >-
    Tier 2.4b status (b834b130): share_doctor_profile (b13c6455) + match_service_and_specialist (dd950beb)
    DONE+LIVE. book_appointment WIRED + the run_async cross-loop bridge FIXED (set_main_loop + main-loop
    submission) + ESC-18 FIXED (dead AppointmentModel.lead removed). book's "agenda" runtime is BLOCKED on
    ESC-19 (below). VitaliaSchedulerProvider deferred (engine event_slug Protocol doesn't fit vitalia's
    doctor+slot model; revisit post-ESC-19).
esc_18:                           # FIXED b834b130
  package: core/luana-core-scheduling
  problem: >-
    AppointmentModel.lead = relationship("LeadModel") — dead cross-registry bare-string (forward mirror of
    ESC-7's removed reverse). Crashed the first appointments ORM query (per-registry configure can't locate
    LeadModel). No consumer. Surfaced live by book_appointment.
  fix: removed the relationship (FK lead_id kept). net-new regression 0.
  status: fixed
esc_19:                           # NEW — ESCALATED to Chris (scheduling-architecture decision)
  severity: high                  # blocks book "agenda" runtime
  package: vitalia/backend scheduling (NOT sales_agent — out of OLA-2 scope)
  problem: >-
    The scheduling create-appointment lane is incomplete + inconsistent. (1) CreateAppointmentService calls
    repo.create()/repo.create_clinic_map() — NO repo implements them (mock-tested only; embudo). (2) Two
    appointment tables: engine `appointments` (ORM, what create-service targets) = 0 rows; brand
    `vitalia_appointments` (raw-SQL agenda grid) = 88 rows. A create writing the engine table = an island
    (anti-orphan: invisible in Mateo's agenda).
  fix: >-
    Scheduling-domain decision (which table is canonical + reconcile) + build the real create-repo
    (engine appointment + brand clinic_map OR vitalia_appointments). HIPAA-sensitive. Separate story/owner.
  status: escalated
  blocks: book_appointment "agenda" verb (the tool is wired + degrades gracefully until this lands)
  next: >-
    Fix ESC-17 (handler ABI) FIRST (sub-phase 2.4a), then build book/match/share (2.4b), then promote.
esc_17:                           # NEW wall — discovered in Tier 2.4 pre-flight (verify-before-build), 2026-06-22
  severity: critical              # END-STATE blocker: no brand tool actually executes
  class: "registered != executable (arch-green != runtime · embudo pattern)"
  package: core/luana-core-sales-agent  # the ABI; the wrong-shaped handlers are brand-side (vitalia/extensions.py)
  problem: >-
    node_tool_executor dispatches `tool_fn(state, db=state.get("_db"))` (sync, state-driven). Every engine tool
    matches (`def tool_x(state, db=None) -> dict`). But all 9 of vitalia's "real" EP-3 handlers are LangChain
    @tool StructuredTools (async, Pydantic args). Empirically `screening_questions(state, db=None)` raises
    `TypeError: 'StructuredTool' object is not callable` → dispatch's except returns {"status":"error"} → the
    tool never runs. The 4 `_not_implemented_yet` plain-fn placeholders are the only callable EP-3 handlers.
    846388a6's "real tools dispatchable" verified registry-presence, not ABI-callability.
  fix: >-
    Brand registers sync `(state, db) -> dict` ADAPTERS (engine ABI = port; brand adapts). Adapter extracts args
    from state → bridges to the async service (event-loop footgun: no asyncio.run inside the async stack) →
    returns a dict. Add an EXECUTION test (call handler as node_tool_executor does) + an arch test (every EP-3
    handler is a plain sync callable, not StructuredTool/coroutine). builder-agentic flagship (R23, HIPAA).
  status: fixed                  # ★ b13c6455 (Tier 2.4a) — brand-side structured_tool_adapter wraps the 9
                                 # StructuredTools as sync (state,db)->dict; run_async bridge (thread+fresh loop);
                                 # pilot share_doctor_profile native-sync. arch+execution tests GREEN; live-verified
                                 # via the REAL merged registry + real dev DB → real doctor URL. Two design
                                 # assumptions overridden empirically: state["_db"] is None at inbound (adapter makes
                                 # its own session); the 9 tools' DI resolvers were never wired (graceful degrade now).
  learning: docs/learnings/2026-06-22-ep3-tool-handler-abi-mismatch.md
# ★ phase_2 is NOT mergeable-for-execution until ESC-17 is fixed: the dispatch/advertise/scope seam is live
# (a tool is found + advertised + stage-gated) but the handlers can't be CALLED. proposal stays `accepted`
# (NOT migrated) — runtime bar (a real brand tool executes live) still unmet, same lesson as ESC-7.
phasing: >-
  Phase 1 (runtime · ESC-4/5/6) → grafo corre + Adrián responde (TESTEABLE: mensaje Telegram → reply).
  Phase 2 (features · ESC-1/2/3) → book/match/share (desbloquea OLA-2). Chris testea tras Phase 1.

# Origen — NO es un brand-pattern-lift; es engine-hardening surfaced por live-verify
origin_learnings:
  - vitalia/docs/product/stories/vitalia-fase2-adrian-canal-inbound/chris-input.md   # G live-verify 2026-06-22 (ESC-4/5/6)
  - vitalia/docs/product/stories/vitalia-fase2-adrian-canal-inbound/03-arch.md        # § Engine-boundary escalations (ESC-1/2/3)
origin_brands: [vitalia]          # 1ra marca que ejerce el grafo sales_agent en un proceso de marca

# Target — 2 engine packages
target_package: core/luana-core-sales-agent
target_secondary_package: core/luana-core-platform   # ESC-4 (LeadModel relationship)
target_module: >-
  sales-agent: application/tools/scheduling/providers.py · application/agents/sales/tools.py ·
  application/tools/registry.py · infrastructure/prompts/base.py · infrastructure/models/prompt_version_model.py
  · platform: infrastructure/models/crm.py
target_ep: EP-3 extension (sales_agent_tool_register gana stage_scope + dispatch real)

# Impact assessment
semver_bump: minor               # additivo (nuevas APIs de registro + columna) + bugfix; sin romper contrato existente
breaking_change: false
brands_affected_consumers: [vitalia, nicolify, comunify, lupulo]   # todas consumen el engine sales_agent
brands_at_risk_regression: [vitalia, nicolify, comunify, lupulo]   # engine compartido → downstream regression obligatoria
migration_required: true         # ESC-6 agrega columna prompt_versions.tenant_id (idempotente + backfill)

# Lift plan
lift_estimated_effort: "3-5 días (engine story: architect engine → build → downstream regression ×4 marcas)"
lift_owner: /dev-team
lift_worktree: "core efímero wip/core-sales-agent-multibrand (NO editar core desde hub de marca — invisible al venv, learning 2026-06-16)"
arch_test_downstream_required: true
migration_notes_required: true
---

# Promotion Proposal — sales_agent engine multibrand-capable (grafo ejecutable en una marca)

## 1. Qué se promueve (engine-hardening, no feature-lift)

El engine `core/luana-core-sales-agent` **nunca se ejerció dentro de un proceso de marca** — el loop inbound
nunca se cableó en ninguna brand (cap deprecada slice-1). Al cablearlo en vitalia (`vitalia-fase2-adrian-canal-inbound`,
OLA-1 construida + verde en aislamiento) y ejercer el grafo **live** contra el stack dev (mensaje Telegram real),
salieron **6 muros de engine** que impiden que el grafo corra en una marca. Son bugs/limitaciones latentes del
engine, **cero brand-fixable** (la fix canónica es en `core/`). Este lift los cierra + expone el contrato que toda
marca necesita para cablear su trabajador sin más engine edits.

**Origen:** live-verify G de `vitalia-fase2-adrian-canal-inbound` (2026-06-22, ratificado Chris abrir el lift).
3 muros (ESC-1/2/3) los halló el `/architect` en el prior-art re-scan (book/match/share gated); 3 más (ESC-4/5/6)
los halló la ejecución live del grafo (mensaje llega + dispatch + buffer OK tras arreglar Redis, pero el grafo crashea).

## 2. Por qué cross-brand (no brand-specific)

Las 4 marcas activas consumen el MISMO engine sales_agent. Ninguna corre el grafo hoy (vitalia es la 1ra en
intentarlo). Estos muros bloquearían a CUALQUIER marca que cablee su agente de ventas. Por eso es engine, no vitalia.

| Brand | Aplicabilidad | Razón |
|---|---|---|
| vitalia | origen + 1er consumidor | cablea el loop Adrián ahora |
| nicolify | consumidor futuro | Christian (SDR) corre el mismo engine — mismos muros |
| comunify | consumidor futuro | agente de ventas creator-economy, mismo engine |
| lupulo | consumidor futuro | idem cuando bootstrap |

## 3. Los 6 muros (path:line verificados · análisis técnico)

| # | Path:line | Síntoma | Fix |
|---|---|---|---|
| **ESC-1** | `core/luana-core-sales-agent/.../application/tools/scheduling/providers.py:447` | `scheduler_provider_for_tenant` hace `_ = tenant_id # reserved` → siempre `SCHEDULER_PROVIDERS["internal"]`; un provider de marca registrado no routea | routear por `tenant_config.scheduler_provider`; `register_scheduler_provider()` ya existe (436) |
| **ESC-2** | `core/luana-core-sales-agent/.../application/agents/sales/tools.py:107` + `nodes.py:402` | `TOOL_REGISTRY` dict estático; el grafo despacha `TOOL_REGISTRY.get(name)` sin mergear tools EP-3 de marca → book/match/share no dispatchan | `register_tool_from_extension` + dispatch desde registry que incluye extension tools. **Desbloquea OLA-2 (book/match/share)** |
| **ESC-3** | `core/luana-core-sales-agent/.../application/tools/registry.py:56` | `STAGE_TOOL_SCOPE` hardcodeado → tool names nuevos no surfacean por stage | `get_tools_for_stage` mergea stage-scope de la extensión EP-3 |
| **ESC-4** | `core/luana-core-platform/.../infrastructure/models/crm.py:209` | `LeadModel.messages = relationship("MessageModel")` string PELADO → ambiguo (engine MessageModel vs `vitalia/.../crm` MessageModel, mismo Base) → `InvalidRequestError: Multiple classes found for path "MessageModel"` → mapper init falla → "Could not fetch tenant" cascada | relationship con path **module-qualified** (lo dice SQLAlchemy). Verificar consumers |
| **ESC-5** | `core/luana-core-sales-agent/.../infrastructure/prompts/base.py:32` | `templates_dir` default `"src/modules/sales_agent/..."` (layout monolítico pre-multibrand); el real es `modules/{brand}/sales_agent/...` → `TemplateNotFound: message_completeness.j2` | path multibrand-aware (config/param por marca, no default monolítico) |
| **ESC-6** | `core/luana-core-sales-agent/.../infrastructure/models/prompt_version_model.py` | `PromptVersion` sin `tenant_id` → `has no attribute 'tenant_id'` al cargar prompts DB | columna `tenant_id` + migración idempotente (+ backfill) |

**Cascada observada live:** ESC-4 rompe el mapper init → tenant=None → cae a carga de prompts por archivo → ESC-5
(path mal) → `TemplateNotFound`. ESC-6 rompe la carga DB de prompts (el fallback que ESC-4 fuerza). ESC-1/2/3 gatean
book/match/share. El blocker primario es **ESC-4** (sin él nada downstream corre).

## 4. Contrato que el lift expone (para cablear marcas sin más engine edits)

1. `register_scheduler_provider(VitaliaSchedulerProvider)` + `scheduler_provider_for_tenant` elige por `tenant_config.scheduler_provider`.
2. EP-3 `sales_agent_tool_register` acepta `stage_scope`; el grafo despacha el tool por nombre desde un registry que incluye extension tools.
3. Protocol `SchedulerProvider` queda **sync** (`db: Session`) — el brand provider hace el bridge a sus services async.
4. **CERO cambio al `AgentState` TypedDict** — las keys de marca viven en overlay/`metadata_info`.
5. Prompts resuelven por marca + DB con `tenant_id`.
6. Relationships del engine resuelven sin ambigüedad cuando una marca define modelos homónimos (`MessageModel`, `LeadModel`, …).

## 5. Verificación (technical · por-efecto · arch test por ESC)

- ESC-1 → `test_scheduler_provider_per_tenant.py` (provider de marca routea por tenant).
- ESC-2 → `test_extension_tool_dispatchable.py` (tool EP-3 dispatcha por el grafo).
- ESC-3 → stage-scope de la extensión surfacea en `get_tools_for_stage`.
- ESC-4 → relationship resuelve con 2 `MessageModel` registrados en el Base.
- ESC-5 → prompt carga en layout `modules/{brand}/sales_agent`.
- ESC-6 → `prompt_versions.tenant_id` presente + carga DB OK.
- **Efecto runtime real (el bar honesto):** el grafo sales_agent corre end-to-end en vitalia — mensaje Telegram real → reply de Adrián, leído de logs + fila conversación/trace/costo en DB. NO "arch tests verdes".
- **Downstream regression (R3):** suites de las 4 marcas verdes tras el lift (`auditor-downstream-regression`). El engine es shared — un cambio al relationship/registry/prompt path puede romper consumers.

## 6. Semver + migración

- **minor** sobre `core/luana-core-sales-agent` (+ `core/luana-core-platform` para ESC-4): additivo (APIs de registro nuevas) + bugfix (relationship/prompt path) + columna nueva. Sin romper contrato existente → opt-in por marca para los provider/tools; los fixes (ESC-4/5/6) aplican a todos (son correcciones).
- **Migración** (ESC-6): `prompt_versions.tenant_id` idempotente (`IF NOT EXISTS`) + backfill. `migration_notes` obligatorio.

## 7. Relación con otras proposals

- `2026-05-19-purge-nicolify-hardcodes-sales-agent.md` — antecedente (hardcodes de marca en el engine sales_agent). Mismo espíritu multibrand-cleanup; este lift es el siguiente paso (ejecución del grafo).
- `2026-06-16-copilot-chat-brand-mountable.md` — patrón hermano (hacer un engine agéntico montable por marca).
- T-LIFT-1 en `vitalia-fase2-adrian-canal-inbound/06-tickets.yaml` — este proposal ES la realización de ese ticket (crecido de ESC-1/2/3 → ESC-1..6).

## 8. Recomendación /pm-luana

**APPROVED.** Es el camino crítico real: sin este lift el grafo sales_agent no corre en NINGUNA marca (vitalia lo probó, falla). El código de marca de OLA-1 ya está construido + verde esperándolo; su valor (Adrián que descubre/recomienda/agenda/responde) está 100% gated por esto. Riesgo: toca engine compartido por 4 marcas → la downstream regression (R3) es el guardrail. Esfuerzo realista 3-5 días (engine story completa). **Pendiente ratificación de Chris** (no marco `accepted` sin su APPROVED — anti-pattern del promotion gate).

**Primer paso si Chris ratifica:** crear worktree core efímero `wip/core-sales-agent-multibrand` → `/architect` (engine) produce el ready package del lift (arch + validators por ESC + tickets) → `/dev-team` construye en el worktree → downstream regression ×4 → migrate. Luego vitalia OLA-1 ejerce el grafo live (cierra el G de canal-inbound) + se desbloquea OLA-2.
