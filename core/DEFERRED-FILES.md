# Deferred Files — Story 2 + Story 3 Audit Trail

Files from `AISALESHT/backend/src/shared/` that were intentionally NOT lifted
in Story 2 (`luana-shared-lift`) because they import from `src.modules.{copilot,
sales_agent}`. They will lift when their consumer modules lift in later stories.

## Deferred to Story 6 (copilot lift)

| Source (AISALESHT) | Reason |
|---|---|
| `backend/src/shared/workers/copilot_quality_eval.py` | Imports `src.modules.copilot.*` |
| `backend/src/shared/workers/copilot_rag_eval.py` | Imports `src.modules.copilot.*` |
| `backend/tests/shared/workers/test_copilot_quality_eval.py` | Tests above worker |
| `backend/tests/shared/workers/test_copilot_rag_eval.py` | Tests above worker |

## Deferred to Story 7 (sales_agent lift)

| Source (AISALESHT) | Reason |
|---|---|
| `backend/src/shared/workers/sales_agent_quality_eval.py` | Imports `src.modules.sales_agent.*` |
| `backend/src/shared/application/personality_event_handlers.py` | Imports `src.modules.sales_agent.*` |
| `backend/tests/shared/workers/test_sales_agent_quality_eval.py` | Tests above worker |
| `backend/tests/shared/application/test_personality_event_handlers.py` | Tests above handler |

## Deferred arch tests

Three arch fitness tests from `AISALESHT/backend/tests/architecture/` are
deferred to `core/tests/architecture/_deferred/` for the same reason:

| File | Reason |
|---|---|
| `_deferred/test_extraction_orchestrator_inheritance.py` | Scans `src/modules/*/application/` — no equivalent in luana-platform yet |
| `_deferred/test_llm_routing_ssot.py` | Imports `src.core.config.Settings` from AISALESHT layout |
| `_deferred/test_channels_router_invariants.py` | Imports `src.modules.campaigns.*` |

These will be migrated to active arch tests when their respective packages lift.

## Story 3 deferrals

Story 3 (`luana-iam-tenancy-content`) lifted 6 packages. Two subfolders depend on
`src.modules.copilot.domain.ports` — deferred to Story 6 (copilot lift).

| Source (AISALESHT) | Target package | Reason |
|---|---|---|
| `backend/src/modules/commercial_calendar/copilot_provider/__init__.py` | `luana-core-commercial-calendar` | Imports `src.modules.copilot.domain.ports` |
| `backend/src/modules/commercial_calendar/copilot_provider/provider.py` | `luana-core-commercial-calendar` | Imports `src.modules.copilot.domain.ports` |
| `backend/src/modules/social_proof/copilot_provider/__init__.py` | `luana-core-social-proof` | Imports `src.modules.copilot.domain.ports` |
| `backend/src/modules/social_proof/copilot_provider/provider.py` | `luana-core-social-proof` | Imports `src.modules.copilot.domain.ports` |

These will lift in Story 6 alongside `luana-core-copilot`.

## Story 4 deferrals

Story 4 (`luana-crm-analytics-landing-connections`) lifted 4 packages. Nine files
are deferred to later stories.

### Deferred to Story 6 (copilot lift)

These subfolders import `src.modules.copilot.domain.ports` — deferred when their
consumer (`luana-core-copilot`) lifts.

| Source (AISALESHT) | Target package | Reason |
|---|---|---|
| `backend/src/modules/crm/copilot_provider/__init__.py` | `luana-core-crm` | Imports `src.modules.copilot.domain.ports` |
| `backend/src/modules/crm/copilot_provider/provider.py` | `luana-core-crm` | Imports `src.modules.copilot.domain.ports` |
| `backend/src/modules/analytics/copilot_provider/__init__.py` | `luana-core-analytics-engine` | Imports `src.modules.copilot.domain.ports` |
| `backend/src/modules/analytics/copilot_provider/provider.py` | `luana-core-analytics-engine` | Imports `src.modules.copilot.domain.ports` |
| `backend/src/modules/landing/copilot_provider/__init__.py` | `luana-core-landing` | Imports `src.modules.copilot.domain.ports` |
| `backend/src/modules/landing/copilot_provider/provider.py` | `luana-core-landing` | Imports `src.modules.copilot.domain.ports` |
| `backend/src/modules/connections/copilot_provider/__init__.py` | `luana-core-connections` | Imports `src.modules.copilot.domain.ports` |
| `backend/src/modules/connections/copilot_provider/provider.py` | `luana-core-connections` | Imports `src.modules.copilot.domain.ports` |

### Deferred to Story 7 (ChatOrchestrator composition root)

The connections `api/dependencies/__init__.py` wires `ChatOrchestrator` as the
concrete `MessageHandlerPort` implementation — not available until `luana-core-copilot`
and `luana-core-sales-agent` both lift.

| Source (AISALESHT) | Target package | Reason |
|---|---|---|
| `backend/src/modules/connections/api/dependencies/__init__.py` (real wiring) | `luana-core-connections` | Requires `ChatOrchestrator` from Story 7 (sales_agent lift) |

Note: A `NotImplementedError` stub is in place at the same path in `luana-core-connections`
to keep the package import-compatible until Story 7 completes.

### Deferred to Story 8 (campaigns lift — forward coupling)

Two CRM files and their test forward-couple to `src.modules.campaigns.*` which
lifts in Story 8.

| Source (AISALESHT) | Target package | Reason |
|---|---|---|
| `backend/src/modules/crm/application/services/contact_query_service.py` | `luana-core-crm` | Imports `src.modules.campaigns.*` |
| `backend/src/modules/crm/api/contacts.py` | `luana-core-crm` | Imports `contact_query_service` (forward couple) |
| `backend/tests/modules/crm/test_contacts_api.py` | `luana-core-crm` | Tests above API endpoint |

## Story 5 deferrals (2026-05-11)

Story 5 (`luana-brand-offer-studios`) lifted 2 packages (brand-studio +
offer-studio). The following files are deferred to later stories per 03-arch.md §9.6.

### Defer to Story 6 (copilot lift)

`copilot_provider/` subfolders import `src.modules.copilot.domain.{ports, workflow}`
— deferred when their consumer (`luana-core-copilot`) lifts.

| Source (AISALESHT) | Target package | Reason |
|---|---|---|
| `backend/src/modules/brand/copilot_provider/*` (8 files) | `luana-core-brand-studio` | Imports `src.modules.copilot.domain.{ports, workflow}` |
| `backend/src/modules/offer/copilot_provider/*` (5 files) | `luana-core-offer-studio` | Imports `src.modules.copilot.domain.{ports, workflow}` |
| `backend/src/modules/offer/api/offer_ai.py` | `luana-core-offer-studio` | Imports `src.modules.copilot.application.services.offer_psychology_service` |
| `backend/tests/modules/brand/test_brand_context_injector.py` | `luana-core-brand-studio` | Imports copilot ports |
| `backend/tests/modules/brand/test_buyer_persona_fields_dropped_regression.py` | `luana-core-brand-studio` | Imports copilot |
| `backend/tests/modules/brand/test_worker_emits_summary_and_pills.py` | `luana-core-brand-studio` | Imports copilot |
| `backend/tests/modules/offer/test_offer_data_access_provider.py` | `luana-core-offer-studio` | Tests `copilot_provider/provider.py` |

### Defer to Story 8 (campaigns / advertising lift)

`counts.py` + `campaigns.py` import `src.modules.advertising.*` — deferred to
Story 8 (campaigns/advertising lift).

| Source (AISALESHT) | Target package | Reason |
|---|---|---|
| `backend/src/modules/offer/api/counts.py` | `luana-core-offer-studio` | Imports `src.modules.advertising.application.services.offer_campaigns_read_adapter` |
| `backend/src/modules/offer/api/campaigns.py` | `luana-core-offer-studio` | Idem |

Note: `test_offer_ai_endpoint.py` was lifted but contains `@pytest.mark.skip`
decorators referencing the deferred `offer_ai.py` routes. Similar pattern for
`test_counts_api.py` + `test_campaigns_api.py` (module-level `pytest.skip` at
import time, deferred Story 8).

### Reserved (design decisions, NOT existing AISALESHT code)

These are NEW abstractions/data per outcome §7 ADR-001 and outcome §11 voice
cloning roadmap — they do NOT exist in AISALESHT today and will be introduced
in future stories.

| Reserved item | Future story | Notes |
|---|---|---|
| `BrandVoicePort` Protocol | Story 7 (sales_agent / copilot lift) | Consumer-side intro; impl in core-brand-studio wired then. Story 5 forbids new abstractions (§7.3) — verbatim placement of existing `PersonalityCompiler` only |
| `voice_cloning` BrandConfig flag | Stories 11-13 (per-brand vertical bootstrap) | Per-brand value at vertical bootstrap; BrandConfig schema itself in Story 8/9 |
| Voice cloning pipeline (LLM-distillation from chat samples) | Stories 11-13 | NEW code, does NOT exist in AISALESHT today |

## Story 6 deferrals (2026-05-11) + unlifts

### UNLIFTED Story 6 (previously deferred Stories 2-5 — 30 files)

T-16 (commit `ca3cd18`) lifted these `copilot_provider/` subfolders + cross-coupling
tests + `offer_ai.py` from their host packages now that `luana_core_copilot.domain.ports`
exists. All discoverable via `nicolify.copilot_providers` entry-points (T-20 wiring
across 8 pyproject.toml files).

| Source (AISALESHT) | Target package | Count |
|---|---|---|
| `backend/src/modules/commercial_calendar/copilot_provider/*` (Story 3 defer) | `luana-core-commercial-calendar` | 2 |
| `backend/src/modules/social_proof/copilot_provider/*` (Story 3 defer) | `luana-core-social-proof` | 2 |
| `backend/src/modules/crm/copilot_provider/*` (Story 4 defer) | `luana-core-crm` | 2 |
| `backend/src/modules/analytics/copilot_provider/*` (Story 4 defer) | `luana-core-analytics-engine` | 2 |
| `backend/src/modules/landing/copilot_provider/*` (Story 4 defer) | `luana-core-landing` | 2 |
| `backend/src/modules/connections/copilot_provider/*` (Story 4 defer) | `luana-core-connections` | 2 |
| `backend/src/modules/brand/copilot_provider/*` (Story 5 defer) | `luana-core-brand-studio` | 8 |
| `backend/src/modules/offer/copilot_provider/*` (Story 5 defer) | `luana-core-offer-studio` | 5 |
| `backend/src/modules/offer/api/offer_ai.py` (Story 5 defer) | `luana-core-offer-studio` | 1 |
| Cross-coupling tests (Story 5 defer — 3 brand + 1 offer) | various | 4 |

Total: **30 files unlifted** in T-16. Validates D-T1 frozen registry contracts (V-AG-3
snapshot) — these 8 packages' providers consume `ToolRegistry` / `WorkflowRegistry` /
`ExtractorRegistry` / `ModuleRegistry` / `SuggestionRegistry` public APIs unchanged.

### NEW Story 6 deferrals

#### Defer to Story 7 (sales_agent lift)

Per T-17 R26 deferral (`docs/product/stories/luana-copilot-engine/T-17-impl-log.md`):
the architect spec for T-17 ("MessageModel stub cleanup") was premise-mismatched —
`MessageModel` lives in **sales_agent territory** (per `.claude/skills/sales-agent-expert`
§3 forbidden-touch list), NOT copilot. Story 7 sales_agent lift will:
1. Create `luana_core_sales_agent.persistence.models.message_model`
2. Replace MessageModel stubs in offer-studio + copilot + crm + connections conftest.py
   with real `luana_core_sales_agent` imports

| Source (AISALESHT) | Target package | Reason |
|---|---|---|
| `backend/src/modules/sales_agent/infrastructure/models/message_model.py` | `luana-core-sales-agent` | Native sales_agent SQLA model — Story 7 lift |
| MessageModel stubs in 4 conftest.py files | (consumer modules) | Replaced by real import post Story 7 |
| `connections/api/dependencies/__init__.py` real `ChatOrchestrator` wiring | `luana-core-connections` | Requires `luana_core_sales_agent.MessageHandlerPort` impl |
| `_event_types()` lazy import in `application/tools/offer_section_tools.py` | `luana-core-copilot` | Type-ignored until `luana_core_scheduling` lifts |

#### Defer to Story 8 (scheduling lift — campaigns-extension-sdk batch)

| Source (AISALESHT) | Target package | Reason |
|---|---|---|
| AppointmentModel stubs in 4 conftest.py files | (consumer modules) | Scheduling module lifts in Story 8 |
| ProductModel / `_ProductStub` stubs in 4 conftest.py files | (consumer modules) | Catalog/product module lifts in Story 8 |

#### Defer to Story 10 (nicolify shell migration)

Streamlit admin pages stay in AISALESHT until nicolify shell migrates as the
SaaS host application:

| Source (AISALESHT) | Target | Notes |
|---|---|---|
| `backend/src/admin/pages/trazas.py` | nicolify shell (Story 10) | Copilot trace event admin |
| `backend/src/admin/pages/copilot-routing.py` | nicolify shell (Story 10) | F8 routing log viewer |
| `backend/src/admin/pages/costo-copilot.py` | nicolify shell (Story 10) | Cost dashboard |
| `backend/src/admin/pages/copilot-limits.py` | nicolify shell (Story 10) | Per-tenant limits admin |
| `backend/src/admin/pages/copilot-quality.py` | nicolify shell (Story 10) | F9 weekly judge report |
| `backend/src/admin/pages/marketing-kb.py` | nicolify shell (Story 10) | F10 KB curation UI |
| `backend/src/admin/pages/brand-summaries.py` | nicolify shell (Story 10) | F3 lighthouse viewer |
| `backend/src/admin/app.py` + `modules/` + `pages/__init__.py` | nicolify shell (Story 10) | Streamlit registry shell |

### Reserved (NEW abstractions, NOT existing AISALESHT code)

| Reserved item | Future story | Notes |
|---|---|---|
| EP-1..EP-5 Extension SDK formalization | Story 8 | Story 6 freezes registries per D-T1; Story 8 wraps as formal SDK without changing internals |
| BrandVoicePort introduction | Story 7 (D-T3) | Story 6 does NOT introduce; Story 7 architect handles consumer-side wiring |

### Pre-existing Story 5 territory (V-F-x-2 conftest collision workspace constraint)

Documented for completeness — not Story 6's responsibility:

- Some Story 5 conftest.py fixtures collide across brand-studio + offer-studio
  workspace test collection. Pre-existing constraint flagged Story 5; Story 6
  inherits without action.

## Story 7 deferrals (2026-05-12) + INTRODUCED + UNLIFTED

Story 7 luana-sales-agent-engine closed lift of `backend/src/modules/
sales_agent/` into `core/luana-core-sales-agent/` over 19 tickets
(T-1..T-19). Net workspace delta documented here.

### INTRODUCED Story 7 (D-T3 ADR-001 §2.4)

| Surface | Path | Notes |
|---|---|---|
| `BrandVoicePort` Protocol | `core/luana-core-brand-studio/src/luana_core_brand_studio/application/ports/brand_voice_port.py` | Hexagonal port wrapping voice compiler. 2 async methods FROZEN per arch fitness V-AG-4 |
| `BrandVoiceService` adapter | `core/luana-core-brand-studio/src/luana_core_brand_studio/application/services/brand_voice_service.py` | Concrete impl binding to `domain.personality.PersonalityCompiler` (Story 5 SSoT) |
| `BrandVoicePort` tests | `core/luana-core-brand-studio/tests/application/ports/test_brand_voice_port.py` | Protocol conformance |
| `BrandVoiceService` tests | `core/luana-core-brand-studio/tests/application/services/test_brand_voice_service.py` | Adapter behavior |

Cross-package consumers (`luana-core-sales-agent`) consume via DI — NEVER
import `PersonalityCompiler` directly. Arch fitness V-AG-3 enforces.

### UNLIFTED Story 7

| Surface | Notes |
|---|---|
| `connections/api/dependencies/__init__.py` real `ChatOrchestrator` wiring | Stories 4+6 deferral RESOLVED in T-16. `NotImplementedError` stub replaced with `_message_handler = ChatOrchestrator()` singleton |
| `connections/tests/conftest.py` MessageModel stub | REMOVED — replaced with real `from luana_core_sales_agent...message_model import MessageModel` registered FIRST so stub guard skips |
| `luana_core_platform.infrastructure.models.crm.LeadModel.messages` relationship | `foreign_keys="MessageModel.lead_id"` (stub-target, did not exist on real model — `lead_id` is a Python @property; real FK column is `user_id`) REPLACED with `back_populates="lead"` matching AISALESHT SSoT |

### NEW Story 7 deferrals — eval framework → Luana v0.2.0

Per outcome §2 OQ1 + Session 3 ratificación 2. Story E voice fidelity CI
gate WAIVED. Eval framework lifts in v0.2.0 NOT v0.1.0.

| Source (AISALESHT) | Reason | Defer to |
|---|---|---|
| `backend/src/modules/sales_agent/observability/eval_simulator/` (entire subfolder) | Eval simulator runtime — cost-bucket separation tables consumed | Luana v0.2.0 |
| `backend/tests/agentic_evals/sales_agent/` (entire tree) | Simulator smoke + concurrency + schema regression + termination registry + grader runtime + adversarial + personas + goldens | Luana v0.2.0 |
| MAJ-EVAL grader cost-bucket tables: `eval_simulator_llm_call`, `eval_simulator_trace_event`, `eval_simulator_grade`, `eval_simulator_grade_cache`, `eval_synthetic_tenants` | Cost-bucket separation rationale — production cost stays clean | Luana v0.2.0 |
| Story E `sales-agent-voice-fidelity-grader-runtime` story | Voice fidelity grader runtime + CI gate | Luana v0.2.0 |
| Adversarial jailbreak suite (Story I) | Eval prompt-injection defense gate | Luana v0.2.0 |
| Personas catalog `docs/specs/personas/archetype-aware/*.yaml` | 15 archetype-aware personas dataset infra | Luana v0.2.0 |
| Goldens dataset infra `backend/tests/agentic_evals/sales_agent/goldens/` | 15-cell coverage matrix (5 tenants × 3 persona_kinds) | Luana v0.2.0 |

Arch fitness V-AG-5 (`test_no_eval_framework_lifted.py`) defensive cement
against accidental partial lift attempts.

### NEW Story 7 deferrals — scheduling concrete provider runtime → Story 8

| Surface | Reason | Defer to |
|---|---|---|
| `luana_core_scheduling` package (concrete provider runtime) | NOT lifted yet — `application/tools/scheduling/providers.py` lifts with deferred-import pattern preserved (per 03-arch.md §9.2). Runtime fails on scheduler tool invocation in Luana standalone UNTIL Story 8 lifts | Story 8 (campaigns-extension-sdk + scheduling) |

Arch fitness V-AG-2 (`test_story7_no_forward_module_imports.py`) allows
TYPE_CHECKING / function-local imports of `luana_core_scheduling` —
top-level imports flagged as violation.

### NEW Story 7 deferrals — Streamlit admin pages → Story 10

| Source (AISALESHT) | Target | Notes |
|---|---|---|
| `backend/src/admin/pages/sales-routing.py` | nicolify shell (Story 10) | Routing log viewer |
| `backend/src/admin/pages/sales-agent-quality.py` | nicolify shell (Story 10) | Judge weekly report |
| `backend/src/admin/pages/costo-agentes.py` | nicolify shell (Story 10) | Cross-agent cost dashboard |
| `backend/src/admin/pages/llm-virtual-keys.py` | nicolify shell (Story 10) | LiteLLM key admin |
| `backend/src/admin/pages/llm-models.py` | nicolify shell (Story 10) | Model registry admin |

### Reserved (NEW abstractions, NOT existing AISALESHT code) — Story 7

| Reserved item | Future story | Notes |
|---|---|---|
| `voice_cloning` BrandConfig field | Stories 11-13 (vertical bootstrap) | Per-brand voice cloning toggle. Not in Story 7 scope |
| Eval framework formalization | Luana v0.2.0 | Cost-bucket separation tables + MAJ-EVAL + personas + goldens + Story E voice fidelity gate |

### Pre-existing Story 4/5 territory (V-F-x-2 waiver continued)

Documented for completeness — Story 7 inherits per outcome §7.2 + Story 6
precedent V-F-x-2 waiver:

- Some `conftest.py` "Plugin already registered" collisions across Story 4
  + Story 5 + Story 6 packages when running aggregate `uv run pytest core/`.
  Per-package `uv run pytest core/<pkg>/tests/` is the canonical execution
  unit. Pre-existing constraint flagged Story 4; Stories 5+6+7 inherit
  without action.
- `core/luana-core-analytics-engine/tests/test_seed_metrics.py` imports
  `scripts.seed_metrics` which does not exist as installable module —
  Story 4 tech debt.

## Story 8 deferrals (2026-05-12) + INTRODUCED + ALLOWLISTED STUBS

Story 8 luana-campaigns-extension-sdk lifted `backend/src/modules/campaigns/`
into `core/luana-core-campaigns/` and formalized the extension SDK in
`core/luana-core-extension-sdk/` over 18 tickets (T-1..T-18).

### INTRODUCED Story 8

| Surface | Path | Notes |
|---|---|---|
| `luana-core-campaigns` package | `core/luana-core-campaigns/` | Full campaigns engine: domain + infrastructure + application + api + workers + observability (446 tests) |
| `luana-core-extension-sdk` package | `core/luana-core-extension-sdk/` | 18 EP contracts: EP-1..5 executable, EP-6..18 signatures-only, CC-1..5 cross-cutting policies |
| `apps/test-brand` smoke app | `apps/test-brand/` | Vertical brand FastAPI app with 18 register_all handlers + 10 smoke scenarios |
| `@luana/extension-sdk` TS package | `core/@luana/extension-sdk/` | TypeScript mirror of Python SDK types |
| `docs/architecture/luana-platform/extension-points.md` | `docs/architecture/luana-platform/extension-points.md` | §1-§5 extension points reference + vertical-agent-recipe (Vitalia treatment-agent) |
| 12 arch fitness tests | `core/tests/architecture/test_*_story8.py` + related | V-NF-3/4 + V-AG-1..7 + V-D-2/3 cemented |

### ALLOWLISTED STUBS (Story 8 carried over from Story 7)

Per Story 8 checkpoint `allowlisted_stubs_for_story_8` — these stubs remain
in conftest.py files and are NOT removed in Story 8. They defer to later stories:

| Stub | Location | Defer to |
|---|---|---|
| `AppointmentModel` stub | `core/luana-core-campaigns/tests/conftest.py` + others | Scheduling module lift (Story TBD per DAG) |
| `ProductModel` / `_ProductStub` | Multiple conftest.py files | Catalog/product module lift |

These stubs are explicitly allowlisted in `core/tests/architecture/
test_no_residual_test_stubs_post_story_6.py` (Story 8 arch fitness — ratchet
allowlist shrinks only when scheduling/catalog surfaces lift).

### NEW Story 8 deferrals — scheduling concrete provider runtime

Per Story 7 carry-over: `luana_core_scheduling` package NOT lifted in Story 8.
The campaigns worker `run_campaign_scheduler_tick` operates on scheduling
appointments via `AppointmentModel` stub pattern (SQLite-compatible conftest.py).
Real scheduling lift deferred to standalone Story per DAG.

| Surface | Reason | Defer to |
|---|---|---|
| `luana_core_scheduling` package | Not in Story 8 scope (campaigns-extension-sdk focused on campaigns engine + EP SDK) | Dedicated scheduling lift story |
| `AppointmentModel` real SQLA model | Lives in scheduling territory | Scheduling lift story |

### NEW Story 8 deferrals — offer advertising counts/campaigns → Story 9+

| Source (AISALESHT) | Target package | Reason |
|---|---|---|
| `backend/src/modules/offer/api/counts.py` | `luana-core-offer-studio` | Imports advertising module (not yet lifted) |
| `backend/src/modules/offer/api/campaigns.py` | `luana-core-offer-studio` | Idem |

Per Story 5 carry-over documentation — unchanged in Story 8.

### Pre-existing territory (Stories 3-7 carry-over)

- Arch fitness tests for stories 3+4+5 forward import checks now
  correctly allowlist `copilot_provider/` integration directories (added
  Story 8 T-18 ratchet fix — pre-existing failure from Story 6 T-16).
- §3 protected surfaces hash-stable snapshot updated for ruff format
  (4 files: closer_studio.py + output_manager.py + enrollment_model.py +
  follow_up_engine.py — whitespace only, no semantic change to §3 surfaces).
- Story 4 `test_story4_no_forward_module_imports.py` updated to also
  allowlist `connections/api/dependencies/__init__.py` (Story 7 T-16
  composition root — intentional DI wiring, not forward-coupling).

## Lift rule

All deferred files follow the lift-verbatim constraint: when they are lifted,
they must be copied with only import path rewrites (no logic changes). The
`src.modules.*` imports become `luana_core_*` imports pointing to the
corresponding lifted package.
