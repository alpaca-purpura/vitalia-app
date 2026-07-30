# Auditor Downstream Regression — Tabla SSoT de targets (multibrand)

> **Reference doc** del rule `.claude/rules/auditor-downstream-regression.md`.
> No se carga en context auto — auditores lo leen on-demand vía `Read` tool durante Step `downstream_regression_scope`.
>
> **Convención paths:**
> - `${WS}` = `/home/chalreme/Proyectos/luana-platform/`
> - `${BRANDS}` = `{vitalia, nicolify, comunify, lupulo}` (4 activos). Cuando aplique, expandir cada brand.
> - Engine packages: `core/luana-core-{pkg}/src/luana_core_{pkg}/` (tests en `core/luana-core-{pkg}/tests/`)
> - Brand consumers: `{brand}/backend/tests/...` per brand listada
> - Pre-multibrand legacy paths (`backend/src/shared/...`, `backend/tests/modules/...`) NO aparecen en surfaces vivas — solo en ejemplos marcados `LEGACY:` al final del rule principal.

## A) Engine: `luana-core-observability`

| Surface modified (path) | Downstream test paths que MUST run | Razón |
|---|---|---|
| `core/luana-core-observability/src/luana_core_observability/recording/turn_envelope.py` | `core/luana-core-observability/tests/recording/`<br>`core/luana-core-copilot/tests/observability/`<br>`core/luana-core-sales-agent/tests/observability/`<br>`{brand}/backend/tests/modules/{brand}/copilot/observability/` ∀ brand ∈ ${BRANDS}<br>`{brand}/backend/tests/modules/{brand}/sales_agent/observability/` ∀ brand ∈ ${BRANDS} | TurnEnvelope base class — engine copilot + sales-agent extienden + brand extensions overlay |
| `core/luana-core-observability/src/luana_core_observability/recording/base_callback_handler.py` | `core/luana-core-copilot/tests/observability/test_callback_handler*.py`<br>`core/luana-core-sales-agent/tests/observability/test_callback_handler*.py`<br>`{brand}/backend/tests/modules/{brand}/{copilot,sales_agent}/observability/test_callback_handler*.py` ∀ brand | Callback base class (engine + brand overlays) |
| `core/luana-core-observability/src/luana_core_observability/cost/calculator.py` | `core/luana-core-observability/tests/cost/`<br>`core/luana-core-copilot/tests/observability/test_callback_handler_usage*.py`<br>`core/luana-core-sales-agent/tests/observability/test_callback_handler.py`<br>`{brand}/backend/tests/modules/{brand}/{copilot,sales_agent}/observability/` ∀ brand | Cost calculator consumido por todos callbacks (engine + brand) |
| `core/luana-core-observability/src/luana_core_observability/cost/pricing_resolver.py` | idem (filas calculator.py) | Pricing resolver |
| `core/luana-core-observability/src/luana_core_observability/cost/fx_resolver.py` | idem | FX resolver |
| `core/luana-core-observability/src/luana_core_observability/cost/cost_recorder.py` | `core/luana-core-copilot/tests/observability/test_callback_handler_usage_fallbacks.py`<br>`core/luana-core-sales-agent/tests/observability/test_callback_handler.py::TestOnChatModelEnd::test_persists_row_with_sales_columns`<br>`{brand}/backend/tests/modules/{brand}/{copilot,sales_agent}/observability/` ∀ brand | **CASO ORIGEN D4** — cost_recorder consumido por callback handlers engine + brand overlays |
| `core/luana-core-observability/src/luana_core_observability/persistence/base_trace_event_repo.py` | `core/luana-core-copilot/tests/observability/test_*_repo*.py`<br>`core/luana-core-sales-agent/tests/observability/test_*_repo*.py`<br>`{brand}/backend/tests/modules/{brand}/{copilot,sales_agent}/observability/test_*_repo*.py` ∀ brand | Trace event repo base |
| `core/luana-core-observability/src/luana_core_observability/persistence/base_llm_call_repo.py` | idem | LLM call repo base |
| `core/luana-core-observability/src/luana_core_observability/persistence/tenant_billing_config_repository.py` | `core/luana-core-billing/tests/`<br>`core/luana-core-copilot/tests/observability/`<br>`core/luana-core-sales-agent/tests/observability/`<br>`{brand}/backend/tests/modules/{brand}/{copilot,sales_agent}/observability/` ∀ brand | Billing config tenant |
| `core/luana-core-observability/src/luana_core_observability/channels/format_for_channel.py` | `core/luana-core-copilot/tests/`<br>`core/luana-core-sales-agent/tests/`<br>`{brand}/backend/tests/modules/{brand}/{copilot,sales_agent}/` ∀ brand | Channel format dispatcher |
| `core/luana-core-observability/src/luana_core_observability/channels/intent_detector.py` | idem | Intent detector |

## B) Engine: `luana-core-extraction`, `luana-core-llm`

| Surface modified (path) | Downstream test paths que MUST run | Razón |
|---|---|---|
| `core/luana-core-extraction/src/luana_core_extraction/application/base_orchestrator.py` | `core/luana-core-extraction/tests/`<br>`core/luana-core-brand-studio/tests/application/test_extraction*.py`<br>`core/luana-core-offer-studio/tests/application/test_extraction*.py`<br>`core/luana-core-landing/tests/application/test_extraction*.py`<br>`{brand}/backend/tests/modules/{brand}/{brand,offer,landing,buyer_persona}/application/test_extraction*.py` ∀ brand | Wave-based extraction base (engine + brand extractors overlay) |
| `core/luana-core-llm/src/luana_core_llm/router.py` | `core/luana-core-llm/tests/`<br>`core/luana-core-copilot/tests/`<br>`core/luana-core-sales-agent/tests/`<br>`core/luana-core-brand-studio/tests/`<br>`core/luana-core-offer-studio/tests/`<br>`core/luana-core-landing/tests/`<br>`{brand}/backend/tests/modules/{brand}/` ∀ brand (all llm callers) | LLM router consumido cross-engine + cross-brand |
| `core/luana-core-llm/src/luana_core_llm/providers/litellm.py` | idem fila router.py | LiteLLM service (canonical post PI-12 S1 T-5) |
| `core/luana-core-llm/src/luana_core_llm/providers/{kimi,deepseek,openai,qwen,gemini}.py` | `core/luana-core-llm/tests/providers/`<br>`core/luana-core-copilot/tests/observability/test_callback_handler_usage*.py`<br>`core/luana-core-sales-agent/tests/observability/`<br>`{brand}/backend/tests/modules/{brand}/{copilot,sales_agent}/observability/` ∀ brand | Provider adapters |

## C) Engine: `luana-core-events`, `luana-core-idempotency`, `luana-core-billing`, `luana-core-compliance`

| Surface modified (path) | Downstream test paths que MUST run | Razón |
|---|---|---|
| `core/luana-core-events/src/luana_core_events/outbox/` | `core/luana-core-events/tests/`<br>`core/luana-core-sales-agent/tests/`<br>`core/luana-core-copilot/tests/`<br>`core/luana-core-brand-studio/tests/`<br>`{brand}/backend/tests/modules/{brand}/` ∀ brand (outbox consumers) | Outbox pattern (per anti-default-flip USE_OUTBOX_PATTERN_*) |
| `core/luana-core-idempotency/src/luana_core_idempotency/` | `core/luana-core-idempotency/tests/`<br>`core/luana-core-platform/tests/` (scheduling)<br>`core/luana-core-connections/tests/`<br>`{brand}/backend/tests/modules/{brand}/{scheduling,connections}/` ∀ brand | Idempotency keys |
| `core/luana-core-billing/src/luana_core_billing/` (BudgetGuard, RateLimiter) | `core/luana-core-billing/tests/`<br>`core/luana-core-sales-agent/tests/`<br>`core/luana-core-campaigns/tests/`<br>`core/luana-core-copilot/tests/`<br>`{brand}/backend/tests/modules/{brand}/{sales_agent,campaigns,copilot}/` ∀ brand | Billing guards (engine + brand consumers) |
| `core/luana-core-compliance/src/luana_core_compliance/` (ComplianceService) | `core/luana-core-compliance/tests/`<br>`core/luana-core-campaigns/tests/`<br>`core/luana-core-sales-agent/tests/`<br>`{brand}/backend/tests/modules/{brand}/{campaigns,sales_agent}/` ∀ brand | Compliance gates |
| `core/luana-core-events/src/luana_core_events/` (DomainEvent base) | `core/luana-core-events/tests/`<br>`core/luana-core-{m}/tests/application/` for each engine `{m}` in diff<br>`{brand}/backend/tests/modules/{brand}/{m}/application/` ∀ brand for each `{m}` in diff | Domain events cross-engine + cross-brand |

## D) Engine: `luana-core-extension-sdk`, `luana-core-platform`

| Surface modified (path) | Downstream test paths que MUST run | Razón |
|---|---|---|
| `core/luana-core-extension-sdk/src/luana_core_extension_sdk/ports/` | `core/luana-core-extension-sdk/tests/`<br>`core/luana-core-{m}/tests/` para each engine importer del port<br>`{brand}/backend/tests/modules/{brand}/` ∀ brand (extensions.py register_all consumers) | Cross-module ports (EP-1..EP-18 registry) |
| `core/luana-core-extension-sdk/src/luana_core_extension_sdk/extension_points.py` | `core/luana-core-extension-sdk/tests/test_registry*.py`<br>`{brand}/backend/tests/modules/{brand}/test_extensions.py` ∀ brand | EP registry (any new EP requires brand re-register audit) |
| `core/luana-core-platform/src/luana_core_platform/domain/locale.py::TenantLocale` | `core/luana-core-platform/tests/`<br>`core/luana-core-{m}/tests/` con timezone/locale<br>`{brand}/backend/tests/modules/{brand}/` ∀ brand con timezone/locale | Locale VO |
| `core/luana-core-platform/src/luana_core_platform/config.py` defaults flip | Per `.claude/rules/anti-default-flip-audit.md` Step 1 grep tests path viejo (cross engine + cross brand) | Default flip side-effect (PI-11 origin) |
| `core/luana-core-platform/src/luana_core_platform/enums/` | grep usage cross-codebase (engine + brand) + run all tests cross-module | Enums shared (engine + brand consumers) |

## E) Engine + brand extension: `copilot`, `sales-agent`

| Surface modified (path) | Downstream test paths que MUST run | Razón |
|---|---|---|
| `core/luana-core-copilot/src/luana_core_copilot/observability/recording/` | `core/luana-core-copilot/tests/observability/`<br>`{brand}/backend/tests/modules/{brand}/copilot/observability/` ∀ brand<br>arch fitness: shared abstraction non-mirror (per anti-duplication.md) | Engine recording layer |
| `core/luana-core-sales-agent/src/luana_core_sales_agent/observability/recording/` | `core/luana-core-sales-agent/tests/observability/`<br>`{brand}/backend/tests/modules/{brand}/sales_agent/observability/` ∀ brand<br>arch fitness | idem sales-agent |
| `core/luana-core-copilot/src/luana_core_copilot/domain/module_registry.py` | `core/luana-core-copilot/tests/architecture/` arch test ModuleDescriptor entry required<br>`{brand}/backend/tests/modules/{brand}/copilot/` ∀ brand | Per SSoT guard |
| `{brand}/backend/src/modules/{brand}/copilot/{extractors,tools,workflows,kb}/` | `{brand}/backend/tests/modules/{brand}/copilot/`<br>**Cross-brand mirror scan** ∀ otro brand ∈ ${BRANDS} (ver § Cross-brand mirror detection en rule principal) | Brand copilot extension overlay (EP-3, EP-4, EP-5, EP-6) |
| `{brand}/backend/src/modules/{brand}/sales_agent/{tools,personas,goldens}/` | `{brand}/backend/tests/modules/{brand}/sales_agent/`<br>`{brand}/backend/tests/agentic_evals/sales_agent/`<br>**Cross-brand mirror scan** ∀ otro brand | Brand sales_agent extension overlay |

## F) Agentic evals: simulator (engine shared) + brand goldens

| Surface modified (path) | Downstream test paths que MUST run | Razón |
|---|---|---|
| `core/luana-core-sales-agent/src/luana_core_sales_agent/observability/eval_simulator/` | `core/luana-core-sales-agent/tests/agentic_evals/simulator/test_simulator_smoke.py`<br>`core/luana-core-sales-agent/tests/agentic_evals/simulator/test_concurrency_property.py`<br>`core/luana-core-sales-agent/tests/agentic_evals/simulator/test_schema_migration_regression.py`<br>`core/luana-core-sales-agent/tests/agentic_evals/simulator/test_termination_registry.py`<br>`core/luana-core-sales-agent/tests/architecture/test_eval_simulator_observability_invariants.py`<br>`core/luana-core-sales-agent/tests/architecture/test_simulator_no_mirrors_shared.py`<br>`core/luana-core-sales-agent/tests/architecture/test_simulator_writes_eval_kind_tag.py`<br>`core/luana-core-sales-agent/tests/architecture/test_simulator_public_api_surface.py`<br>`core/luana-core-sales-agent/tests/architecture/test_termination_policy_registry_contract.py`<br>`core/luana-core-sales-agent/tests/architecture/test_schema_migrations_registry_complete.py`<br>`{brand}/backend/tests/agentic_evals/sales_agent/` ∀ brand | Eval simulator schema-mirror surface (Story B). Cost-bucket separation tables consumed por smoke + property + schema regression suite + brand goldens runners. |
| `core/luana-core-sales-agent/tests/agentic_evals/simulator/_internal/personas_loader.py` | `core/luana-core-sales-agent/tests/agentic_evals/simulator/test_personas_loader.py`<br>`core/luana-core-sales-agent/tests/agentic_evals/simulator/test_simulator_smoke.py`<br>`core/luana-core-sales-agent/tests/agentic_evals/simulator/test_customer_prompt_v2_unit.py`<br>`core/luana-core-sales-agent/tests/agentic_evals/simulator/test_customer_node_unit.py`<br>`core/luana-core-sales-agent/tests/architecture/test_personas_yaml_completeness.py` | Story C personas loader — ActorProfile via `load_actor_profile_for_tenant()` + ARCHETYPE_DIALECT_MAP. |
| `core/luana-core-sales-agent/tests/agentic_evals/simulator/_internal/customer_persona_prompt.py` | `core/luana-core-sales-agent/tests/agentic_evals/simulator/test_customer_prompt_v2_unit.py`<br>`core/luana-core-sales-agent/tests/agentic_evals/simulator/test_customer_node_unit.py`<br>`core/luana-core-sales-agent/tests/agentic_evals/simulator/test_simulator_smoke.py` | Story C Customer Prompt V2 — V1 byte-equal preservation + V2 sub-slot rotation. Cache prefix safety. |
| `core/luana-core-sales-agent/tests/agentic_evals/simulator/_internal/customer_node.py` | `core/luana-core-sales-agent/tests/agentic_evals/simulator/test_customer_node_unit.py`<br>`core/luana-core-sales-agent/tests/agentic_evals/simulator/test_simulator_smoke.py` | Story C V1/V2 dispatch + eval_metadata 3 NEW keys. Story B 6-key invariants preserved. |
| `docs/specs/personas/archetype-aware/*.yaml` (PLATFORM cross-brand) | `core/luana-core-sales-agent/tests/architecture/test_personas_yaml_completeness.py`<br>`core/luana-core-sales-agent/tests/agentic_evals/simulator/test_personas_loader.py`<br>`{brand}/backend/tests/agentic_evals/sales_agent/` ∀ brand (consumen personas catalog cross-brand) | Story C 15 archetype-aware personas YAML catalog — schema enforced by arch fitness + loader contract. Voseo magic comment line 2 enforced for AR YAMLs. |
| `{brand}/backend/tests/agentic_evals/sales_agent/goldens/**` (per brand) | `{brand}/backend/tests/agentic_evals/sales_agent/test_goldens_schema.py`<br>`{brand}/backend/tests/agentic_evals/sales_agent/test_goldens_coverage.py`<br>`{brand}/backend/tests/agentic_evals/sales_agent/test_goldens_pii_scanner.py`<br>`{brand}/backend/tests/architecture/test_goldens_schema_completeness.py`<br>`{brand}/backend/tests/architecture/test_goldens_no_mirror_simulator_schema.py`<br>`{brand}/backend/tests/architecture/test_pii_patterns_single_source.py`<br>`{brand}/backend/tests/architecture/test_goldens_no_committed_pii.py`<br>`{brand}/backend/tests/architecture/test_goldens_cost_bucket_invariant.py`<br>`{brand}/backend/tests/scripts/test_generate_golden_candidates.py`<br>`{brand}/backend/tests/scripts/test_promote_golden.py` | Story D goldens dataset infra PER brand — schema cement v1 + 15-cell coverage matrix + 5 arch fitness gates + PII defense-in-depth. |
| `scripts/_pii_patterns.py` (platform script — shared cross-brand) | `core/luana-core-platform/tests/scripts/test_seed_pii_scanner.py`<br>`core/luana-core-platform/tests/scripts/test_pre_commit_hook.py`<br>`{brand}/backend/tests/agentic_evals/sales_agent/test_goldens_pii_scanner.py` ∀ brand<br>`{brand}/backend/tests/architecture/test_pii_patterns_single_source.py` ∀ brand | Story D LIFT shared PATTERNS dict — 9 regex categories. DRY threshold 2 consumers. Pre-commit hook Sections 8+9 + arch gate single-source. |
| `scripts/generate_golden_candidates.py` (platform script) | `{brand}/backend/tests/scripts/test_generate_golden_candidates.py` ∀ brand<br>`{brand}/backend/tests/architecture/test_goldens_cost_bucket_invariant.py` (env-gated `EVAL_GOLDENS_COST_BUCKET_VERIFY=1`) ∀ brand | Story D generation orchestrator — matrix 5×3×N cells, cost preflight strict abort, per-cell isolation, deterministic seeding uuid5. |
| `scripts/promote_golden.py` (platform script) | `{brand}/backend/tests/scripts/test_promote_golden.py` ∀ brand | Story D promotion CLI — auto-derive `expected_termination_reason` + `expected_tools_invoked` + `forbidden_tools`. Idempotent YAML safe_dump. |
| `core/luana-core-sales-agent/tests/agentic_evals/grader/_internal/maj_eval.py` | `core/luana-core-sales-agent/tests/agentic_evals/grader/test_maj_eval_unit.py`<br>`core/luana-core-sales-agent/tests/agentic_evals/grader/test_maj_eval_debate.py`<br>`core/luana-core-sales-agent/tests/agentic_evals/grader/test_maj_eval_happy.py`<br>`core/luana-core-sales-agent/tests/agentic_evals/grader/test_maj_eval_adversarial.py`<br>`core/luana-core-sales-agent/tests/agentic_evals/grader/test_judge_registry.py`<br>`core/luana-core-sales-agent/tests/agentic_evals/grader/test_grader_cache.py`<br>`core/luana-core-sales-agent/tests/agentic_evals/grader/test_unconverged_fallback.py`<br>`core/luana-core-sales-agent/tests/architecture/test_grader_sandbox_markers_enforced.py`<br>`core/luana-core-sales-agent/tests/architecture/test_grader_pii_sanitize_pre_judge.py`<br>`core/luana-core-sales-agent/tests/architecture/test_grader_round_2_no_self_reasoning.py`<br>`core/luana-core-sales-agent/tests/architecture/test_grader_writes_eval_only_bucket.py`<br>`core/luana-core-sales-agent/tests/architecture/test_grader_public_api_surface.py`<br>`{brand}/backend/tests/agentic_evals/sales_agent/grader/` ∀ brand (cuando brand opta-in grader) | Story E grader runtime — MAJ-EVAL state machine. Cost-bucket invariant H7 cement. Variance threshold 0.15 → Round 2 debate → unconverged fallback. |
| `core/luana-core-sales-agent/tests/agentic_evals/grader/_internal/judge_prompts.py` | `core/luana-core-sales-agent/tests/agentic_evals/grader/test_judge_prompts.py`<br>`core/luana-core-sales-agent/tests/agentic_evals/grader/test_maj_eval_adversarial.py`<br>`core/luana-core-sales-agent/tests/agentic_evals/grader/test_judge_no_system_leak.py`<br>`core/luana-core-sales-agent/tests/architecture/test_grader_sandbox_markers_enforced.py`<br>`core/luana-core-sales-agent/tests/architecture/test_grader_round_2_no_self_reasoning.py` | Story E sandbox markers DQ2 — defense-in-depth vs prompt-injection. Slot 5 literal markers + Round 2 peer-only critique. |
| `docs/specs/rubrics/qualification-accuracy.md` (PLATFORM cross-brand) | `core/luana-core-sales-agent/tests/agentic_evals/grader/test_maj_eval_unit.py`<br>`core/luana-core-sales-agent/tests/agentic_evals/grader/test_maj_eval_debate.py`<br>`core/luana-core-sales-agent/tests/agentic_evals/grader/test_maj_eval_happy.py`<br>`core/luana-core-sales-agent/tests/agentic_evals/grader/test_maj_eval_adversarial.py`<br>`core/luana-core-sales-agent/tests/agentic_evals/grader/test_grader_cache.py` | Story E rubric MD v1. Rubric MD bump → `rubric_version` change → cache invalidation → full re-grade cascade. |

## G) Brand business modules (analytics, offer, brand, landing, copilot domain registry)

| Surface modified (path) | Downstream test paths que MUST run | Razón |
|---|---|---|
| `{brand}/backend/src/modules/{brand}/{m}/api/` route changes (for the modifying brand) | `{brand}/backend/tests/modules/{brand}/{m}/api/`<br>`{brand}/frontend/src/features/{m}/api/` consumers if FE PR<br>**Cross-brand mirror scan** ∀ otro brand | Contract change ripple (brand-internal) |
| `{brand}/backend/src/modules/{brand}/{m}/domain/events.py` | grep `Event` class importers en `{brand}/backend/` + run their tests<br>`core/luana-core-events/tests/` si Event registered cross-brand | Cross-module event consumers (brand + engine bus) |
| `core/luana-core-analytics-engine/src/luana_core_analytics_engine/domain/extraction_contract.py` | Run `make extraction-contract` + arch test<br>`core/luana-core-analytics-engine/tests/`<br>`{brand}/backend/tests/modules/{brand}/analytics/` ∀ brand opta-in analytics | ETL contract regen (engine SSoT) |
| `core/luana-core-analytics-engine/src/luana_core_analytics_engine/domain/metric_catalog.py` | `core/luana-core-analytics-engine/tests/`<br>arch test catalog↔contract alignment<br>`{brand}/backend/tests/modules/{brand}/analytics/` ∀ brand | Catalog change (cross-brand) |
| `core/luana-core-offer-studio/src/luana_core_offer_studio/domain/{archetype,value_level,format}_catalog.py` | bump `_CATALOG_VERSION` + arch tests both stacks<br>`core/luana-core-offer-studio/tests/`<br>`{brand}/backend/tests/modules/{brand}/offer/` ∀ brand opta-in offer-studio<br>`{brand}/frontend/src/features/offer-studio/` ∀ brand (FE arch test cross-brand) | Per offer-catalogs.md (engine catalog cross-brand) |

## H) Frontend (per-brand)

| Surface modified (path) | Downstream test paths que MUST run | Razón |
|---|---|---|
| `{brand}/frontend/src/lib/api/fetchClient.ts` | `{brand}/frontend/src/features/*/api/` tests + `{brand}/frontend/e2e/` smoke (auth-tenant)<br>**Cross-brand mirror scan** ∀ otro brand (fetchClient pattern cross-brand) | Cross-feature API client base (per-brand fetcher) |
| `{brand}/frontend/src/lib/api/` (other shared API utils) | grep importers en `{brand}/frontend/src/features/` + their feature tests | Cross-feature API helpers (per-brand) |
| `{brand}/frontend/src/lib/tokens/` design tokens | `{brand}/frontend/src/__tests__/architecture/test-page-padding.test.ts`<br>studio section pages tests (`{brand}/frontend/src/features/`) | Design tokens consumed cross-studio per-brand |
| `{brand}/frontend/src/lib/format/` (formatMoney, formatTenantDate*) | grep importers en `{brand}/frontend/` + currency/locale tests cross-feature<br>**Cross-brand mirror scan** (formatters shared abstraction candidate) | Master-data formatters consumed cross-feature per-brand |
| `{brand}/frontend/src/hooks/` (global hooks like `useTenantLocale`) | grep importers across `{brand}/frontend/src/features/` + their tests | Global hooks consumed cross-feature per-brand |
| `{brand}/frontend/src/components/shared/` | grep importers en `{brand}/frontend/src/` + their feature tests + visual smoke E2E | Shared components rendered cross-feature per-brand |
| `{brand}/frontend/src/components/ui/` (Shadcn primitives) | full `{brand}/frontend/` vitest run + `{brand}/frontend/e2e/` smoke | UI primitives ripple universally per-brand |
| `{brand}/frontend/src/features/{m}/api/` | `{brand}/frontend/src/features/{m}/` full feature tests + smoke E2E for that route | Feature API contract change (brand-internal) |
| `{brand}/frontend/src/features/{m}/types/` exported | grep cross-feature importers en `{brand}/frontend/` + their tests | Type contract ripple cross-feature per-brand |
| `{brand}/frontend/src/lib/zod-schemas/` shared schemas | grep importers en `{brand}/frontend/` + form tests cross-feature<br>**Cross-brand mirror scan** (Zod schemas shared abstraction candidate) | Shared validation schemas per-brand |
| `{brand}/frontend/src/__tests__/architecture/*.test.ts` allowlist shrink | full `{brand}/frontend/` FE arch fitness suite | Ratchet enforcement per-brand |
| `{brand}/frontend/e2e/auth.fixture.ts` o `{brand}/frontend/e2e/fixtures/*` | full smoke project `{brand}/frontend/` + relevant POMs | E2E fixture change ripples to all auth-protected specs per-brand |
| `{brand}/frontend/playwright.config.ts` | full smoke project `{brand}/frontend/` | Config change affects every spec per-brand |

## I) Brand overlay rules + extensions registry

| Surface modified (path) | Downstream test paths que MUST run | Razón |
|---|---|---|
| `{brand}/.claude/rules/*.md` | Manual review per § Brand overlay scope (verify NO contradicción con `.claude/rules/` raíz) | Brand-specific rule overlay |
| `{brand}/backend/src/modules/{brand}/extensions.py::register_all(registry)` | `{brand}/backend/tests/modules/{brand}/test_extensions.py`<br>`core/luana-core-extension-sdk/tests/test_registry_brand_smoke.py` (si existe) | EP-1..EP-18 registration per-brand. Cambio en register_all puede romper brand bootstrap. |
| `{brand}/config/brand.yaml` (enabled_sections + field_overrides + preset_pack + feature flags) | `{brand}/backend/tests/modules/{brand}/{brand,offer}/` (config consumers)<br>`{brand}/frontend/src/features/brand-studio/` tests (overrides surface) | Brand config — flips comportamiento engine per-brand |

## Mantenimiento tabla

Cuando agregás:
- Nueva surface en `core/luana-core-X/src/luana_core_X/` cross-consumer → MUST add row en sección apropiada (A-I) con downstream_test_targets incluyendo engine tests + `{brand}/...` ∀ brand consumer
- Nuevo módulo importer engine de surface listada → MUST add path a downstream_test_targets row existente
- Nueva brand activa (bootstrap saasora/inmoflow/etc.) → MUST expand `{brand}` template ∀ row applicable (sed-friendly: `{brand}` → `<new-brand>`)
- Cambia downstream test path (rename) → update row mismo commit
- Lift brand → engine (promotion proposal merged) → remove brand row + add engine row + add ∀ brand consumer rows

Tabla SSoT vive aquí (post split 2026-05-16 — fit en <40k chars context limit). NO duplicar en agent files. NO duplicar per-brand (brand template `{brand}` se expande sintácticamente, no físicamente).
