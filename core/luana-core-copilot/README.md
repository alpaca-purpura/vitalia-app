# luana-core-copilot

Version: 0.0.6-alpha

Copilot conversational engine ("Claude Code de marketing") lifted from AISALESHT
`backend/src/modules/copilot/` (Story 6, closed 2026-05-12). LangGraph 2.0
StateGraph + deepagents subagent harness + Anthropic prompt cache slots 1-11 +
Qdrant tenant-agnostic marketing_kb + 33 unique `[COPILOT-*]` anchors capped
(V-AG-8 cement).

## Lift origin

- AISALESHT path: `backend/src/modules/copilot/` (33k LOC, the largest module)
- Lift Stories 6 commits (luana-platform main):
  - T-1..T-15 → 15 sequential commits (workspace + skeleton + lift layers domain → infra → application → api → evals/utils/aggregate GREEN)
  - T-16 (UNLIFT) → commit `ca3cd18` — 30 files unlifted from Stories 2-5 deferrals (8 packages' `copilot_provider/` subfolders + 4 cross-coupling tests + offer_ai.py)
  - T-19 → commit `9a7a0df` — brand-agnostic + no-forward-imports arch fitness
  - T-20 → commit `eaa1446` — D-T1+D-T2+D-T6 cement (6 arch fitness tests) + entry-points wiring across 8 pyprojects
  - T-21 → final polish

## Key exports (D-T1 FROZEN per 03-arch.md §7.3)

Public API surface of 5 registries is **byte-stable** per
`core/tests/architecture/_snapshots/copilot_registry_v1.json`. Bump
(schema_version increment) requires architect ratification —
Story 8 EP-1..EP-5 SDK introduction is the next allowed bump occasion.

- **Tools registry** (`luana_core_copilot.application.tools.registry`):
  - `ROUTE_TOOL_MAP`, `ALWAYS_AVAILABLE_GROUPS`, `TOOL_GROUPS`, `TOOL_GROUP_META`
  - `get_tools_for_route()`, `get_tools_for_context()`, `get_all_tools()`,
    `get_tool_names_for_route()`, `is_group_available_in_channel()`
  - `ToolNameCollisionError`, `ToolGroupMeta` (dataclass)
- **Workflows registry** (`luana_core_copilot.application.workflows.registry`):
  - `collect_workflows()`, `WorkflowRegistryError`
- **Module registry** (`luana_core_copilot.domain.module_registry`):
  - `get_module_registry()`, `reset_module_registry_cache()`,
    `ModuleDescriptor` (dataclass)
- **Extraction domain registry** (`luana_core_copilot.domain.extraction_domain_registry`):
  - `get_extraction_config()`, `supported_domains()`,
    `ExtractionDomainConfig` (dataclass), `ResponseValueKind`
- **Suggestions registry** (`luana_core_copilot.application.suggestions.registry`):
  - `get_default_engine()`, `register_provider()`

## D-T6 anti-mirror observability (cardinal)

- `CopilotObservabilityContext` SUBCLASSES `BaseObservabilityContext` from
  `luana_core_observability.recording.turn_envelope` (NEVER redeclares)
- `ObservabilityCallbackHandler` SUBCLASSES `BaseAgentCallbackHandler` from
  `luana_core_observability.recording.base_callback_handler`
- NO local declarations of `FXResolver`, `PricingResolver`, `CostCalculator`,
  `sanitize_payload` — all imported from `luana_core_observability`
- Enforced by `core/tests/architecture/test_no_mirror_observability_in_copilot.py`

## Provider discovery (entry-points + filesystem fallback)

`luana_core_copilot.application.discovery.discover_providers()` merges
two sources:

1. **Entry-points** (`nicolify.copilot_providers` group). Wired across 8
   Stories 2-5 pyproject.toml files. This is the canonical path in
   luana-platform context.
2. **Convention scan** of `src.modules.*.copilot_provider`. Returns empty
   in luana-platform (no `src.modules` filesystem). Active in AISALESHT.

## Deferrals (per 03-arch.md §9.4)

### Defer to Story 10 (nicolify shell migration)
- `backend/src/admin/pages/{trazas,copilot-routing,costo-copilot,copilot-limits,copilot-quality,marketing-kb,brand-summaries}.py` —
  Streamlit admin shell migrates with nicolify shell.

### Defer to Story 7 (sales_agent lift)
- `backend/src/modules/connections/api/dependencies/__init__.py` real wiring of
  `ChatOrchestrator` — requires `luana_core_sales_agent.MessageHandlerPort` impl
  that arrives Story 7. Stub `NotImplementedError` stays.
- `MessageModel` stub in offer-studio + copilot + crm + connections conftest.py —
  sales_agent.MessageModel lifts in Story 7 (T-17 R26 deferral).
- `_event_types()` lazy import in `application/tools/offer_section_tools.py` —
  type-ignored until `luana_core_scheduling` lifts (Story 8 — actually next
  to Story 7 in DAG ordering, but module-level constraint per arch).

### Defer to Story 8 (scheduling lift — campaigns-extension-sdk batch)
- `AppointmentModel` stub in offer-studio + copilot + crm + connections conftest.py —
  scheduling module lifts in Story 8.
- `ProductModel` / `_ProductStub` stubs in brand-studio + crm + connections +
  landing conftest.py — catalog/product module lifts in Story 8.

### Reserved (NEW abstractions, NOT existing AISALESHT code)
- EP-1..EP-5 Extension SDK formalization → Story 8. Story 6 freezes registries
  per D-T1; Story 8 wraps them as formal SDK without changing internals.
- BrandVoicePort introduction → Story 7 (D-T3).

## UNLIFTED Stories 2-5 (post T-16 UNLIFT)

T-16 unlifted **30 files** previously deferred from Stories 2-5:
- `commercial-calendar/copilot_provider/` (Story 3 deferral) — 2 files
- `social-proof/copilot_provider/` (Story 3) — 2 files
- `crm/copilot_provider/` (Story 4) — 2 files
- `analytics-engine/copilot_provider/` (Story 4) — 2 files
- `landing/copilot_provider/` (Story 4) — 2 files
- `connections/copilot_provider/` (Story 4) — 2 files
- `brand-studio/copilot_provider/` (Story 5) — 8 files
- `offer-studio/copilot_provider/` (Story 5) — 5 files
- `offer-studio/api/offer_ai.py` (Story 5) — 1 file
- Cross-coupling tests (Story 5) — 4 files

All discoverable via `nicolify.copilot_providers` entry-points (T-20 wiring).
