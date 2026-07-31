# Anti-Duplication — Inventario engine abstractions (SSoT stack-specific)

> **Detalle on-demand del slim stub `.claude/rules/anti-duplication.md`.** El cardinal (grep-before-write + extend-desde-engine, NUNCA mirror) vive always-on en la rule; esta tabla = el registro canónico de abstracciones compartidas de `core/luana-core-*` que las brands CONSUMEN vía import (NUNCA mirror). Extraída en W1 (harness-refactor 2026-06-08) porque es **stack-specific** (paths `core/luana-core-*` = seam `engine_prefix`). **tier: project.** Carga al hacer Step 0 grep antes de crear un subsistema en `{brand}/backend/src/modules/{brand}/X/`.

## Inventario engine abstractions (SSoT)

Patrón canónico vive en `core/luana-core-*/` packages. Brands consumen via Python imports `luana_core_*`, NUNCA mirror.

| Pattern | Path canónico engine | Consumers |
|---|---|---|
| Observability turn envelope | `core/luana-core-observability/src/luana_core_observability/recording/turn_envelope.py::BaseObservabilityContext` | copilot · sales_agent · futuros |
| Callback handler base | `core/luana-core-observability/src/luana_core_observability/recording/base_callback_handler.py::BaseAgentCallbackHandler` | copilot · sales_agent |
| PII sanitization | `core/luana-core-observability/src/luana_core_observability/recording/sanitization.py::sanitize_payload` | todos agentes |
| FX resolver factory | `core/luana-core-observability/src/luana_core_observability/cost/fx_resolver.py::FXResolver.default()` | todos agentes con cost |
| Pricing resolver | `core/luana-core-observability/src/luana_core_observability/cost/calculator.py` + `pricing_snapshot_repository.py` | todos agentes |
| Trace event repo base | `core/luana-core-observability/src/luana_core_observability/persistence/base_trace_event_repo.py` | copilot · sales_agent |
| LLM call repo base | `core/luana-core-observability/src/luana_core_observability/persistence/base_llm_call_repo.py` | copilot · sales_agent |
| Channel format registry | `core/luana-core-channels/src/luana_core_channels/format_for_channel.py` | sales_agent · copilot |
| Intent detector | `core/luana-core-channels/src/luana_core_channels/intent_detector.py` | sales_agent · futuros |
| Tenant billing config | `core/luana-core-observability/src/luana_core_observability/persistence/tenant_billing_config_repository.py` | todos cobran |
| Extraction orchestrator | `core/luana-core-extraction/src/luana_core_extraction/base_orchestrator.py::BaseExtractionOrchestrator` | brand · offer · buyer_persona · landing |
| Locale VO | `core/luana-core-platform/src/luana_core_platform/domain/locale.py::TenantLocale` | todos UI/timezone |
| LLM router + providers | `core/luana-core-llm/src/luana_core_llm/router.py` + `providers/` | todos llaman LLMs |
| Outbox pattern | `core/luana-core-events/src/luana_core_events/outbox/` | todos emiten eventos |
| Idempotency | `core/luana-core-idempotency/src/luana_core_idempotency/` | todos tasks idempotentes |
| Billing guards | `core/luana-core-billing/src/luana_core_billing/` (BudgetGuard + RateLimiter) | sales_agent · campaigns · copilot |
| Compliance gates | `core/luana-core-compliance/src/luana_core_compliance/` (ComplianceService) | campaigns · sales_agent |
| Domain events | `core/luana-core-events/src/luana_core_events/` | todos cross-module |
| Cross-module ports | `core/luana-core-platform/src/luana_core_platform/links/ports/` | todos cross-domain |

**Shrink-only:** registro NO duplica per-módulo. Patrón nuevo cross-agent → lift a core package primer commit (flujo engine `/pm-vitalia`: cambio directo en `core/` + arch tests).

## Anti-patterns concretos (ejemplos stack-specific de la doctrina)

- ❌ Mirror `modules/X/observability/recording/turn_envelope.py` cuando copilot existe — lift shared
- ❌ Mirror callback handler — heredar `BaseAgentCallbackHandler`
- ❌ Re-implementar `FXResolver(http_client_factory=...)` N módulos — `FXResolver.default()`
- ❌ Copy-paste `lambda: httpx.Client(timeout=10)` — encapsular classmethod
- ❌ Re-resolver currency del tenant local — usar `TenantLocale.currency` (locale VO) + `FXResolver.default()` (engine observability)
- ❌ Mirror PricingResolver setup — extract factory shared
- ❌ Re-implementar PII sanitization local — usar shared `sanitization`
- ❌ Mirror channel format dispatch — usar shared `format_for_channel`

## Referencias

- `.claude/rules/anti-duplication.md` — **el cardinal always-on** (grep-before-write doctrine)
- `docs/promotion-protocol/README.md` — workflow brand→core lift gate
- `core/luana-core-extension-sdk/` — EP-1..EP-18 registry
