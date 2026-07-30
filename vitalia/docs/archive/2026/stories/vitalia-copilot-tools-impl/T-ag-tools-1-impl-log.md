<!-- voseo-allowed: log cita el regex del hook spanish_neutro_voseo_check (glosario voseo→neutro) como evidencia de validador, no es output user-facing -->

# T-ag-tools-1 — IMPL log

**Ticket:** T-ag-tools-1 (Valeria 4 wizard tools + observability subclass + slot prompts MD + persona)
**Owner:** builder-agentic (Opus 4.7 R23 production_code=true)
**Brand:** vitalia
**Worktree:** /home/chalreme/Proyectos/luana-vitalia/ on `wip/vitalia`
**Start:** 2026-05-18

## Skills Consulted

1. **copilot-expert** — invoked per surface (Valeria wizard tools + observability subclass). Decisions captured:
   - `extract_tenant_context` / `confirm_slot` / `simulate_personality` / `complete_onboarding` are LangChain `@tool` decorated, async, call SERVICES (never raw repos), `tenant_id` UUID mandatory.
   - Observability subclass MUST inherit `BaseAgentCallbackHandler` from `luana_core_observability` — anti-duplication §0 cardinal. Only override `_persist_llm_call_row` + `_persist_trace_event_row` (engine owns plumbing).
   - Cost via `pop_cost(litellm_call_id)` (PI-12 S1 T-1 cement 2026-05-02) — NO `calculate_cost()` runtime.
   - `sanitize_payload(payload)` from engine (no `compliance_level` kwarg — engine signature does not accept it; vitalia compliance level lives in `compliance_level` column on persistence row).
   - Best-effort: try/except + structlog warning + rollback (never break turn).

2. **sales-agent-expert** — NOT invoked (ticket scope is Valeria copilot only; sales-agent surface is owned by T-ag-tools-2 Adrián builder). § Anti-duplication cardinal still relevant for copilot subclass enforcement → cross-applied from copilot-expert.

3. **tessl__langgraph** — informational only (T-ag-workflows-1 owns wizard graph; this ticket creates tools + prompts only). Tools must be `async def`, `@tool` decorator with Pydantic v2 `args_schema`, return type `str` summary for non-DTO tools.

4. **tessl__graceful-degradation** — tools call services that wrap external calls (website_scraper, document_extractor, personality adapter). Tool layer itself is thin — graceful degradation lives in adapter layer (T-be-services-1 owns adapters). Tool stays best-effort via service layer.

5. **claude-api** — confirmed via WebFetch (2026-05-18): cache_control syntax `{"type": "ephemeral"}` for 5min default, `{"type": "ephemeral", "ttl": "1h"}` for 1h. Max 4 cache breakpoints per request. Cache marker placed AFTER slot 4 (Valeria persona) per 03-arch-agentic § 5.2.

## State-of-the-art validation

- Anthropic Prompt Caching live docs accessed 2026-05-18 via WebFetch. Confirmed:
  - `cache_control: {"type": "ephemeral"}` (5min default) or `{"type": "ephemeral", "ttl": "1h"}` (1h batch).
  - Max 4 breakpoints per request.
  - Caches isolated per workspace (Feb 2026 update).
- LangGraph patterns (per `tessl__langgraph`): supervisor topology, AsyncPostgresSaver in production. Out of scope for this ticket (workflow ticket is T-ag-workflows-1).

## Step 0 — Default-flip detection

Not applicable. T-ag-tools-1 scope: tools + slot prompts + observability subclass. No `core/luana-core-platform/config.py` defaults flipped. Section bypassed per checklist.

## Cross-module systems audit (NO-NEW-LAYER)

Verified via grep:
- `BaseAgentCallbackHandler` lives in `core/luana-core-observability/src/luana_core_observability/recording/base_callback_handler.py` (engine SSoT). Subclassed via inheritance.
- `BaseObservabilityContext` lives in `core/luana-core-observability/src/luana_core_observability/recording/turn_envelope.py` (engine SSoT). Subclassed via inheritance.
- `sanitize_payload` lives in `core/luana-core-observability/src/luana_core_observability/recording/sanitization.py` (engine SSoT). Imported, never re-defined.
- Cross-brand scan (nicolify/comunify/lupulo): NO mirror files for the 4 tool basenames. PASS.

## Files created

See `T-ag-tools-1-result.md` § Files created (22 entries, ~960 production LOC + tests + docs).

Summary:
- 4 LangChain @tool files (extract_tenant_context, confirm_slot, simulate_personality, complete_onboarding) + 1 tools `__init__.py`
- 3 slot prompts MD (Slot 4 Valeria persona, Slot 2 wizard role, extractor subagent sandbox)
- 2 observability subclass files + 2 `__init__.py` (callback_handler.py + turn_envelope.py)
- 5 unit test files (58 tests total) + 2 test `__init__.py`
- 1 architecture fitness gate (10 assertions)
- 2 docs (this impl-log + result)

## Files modified

- `vitalia/backend/src/modules/vitalia/extensions.py` — 4 NEW EP-3 entries for Valeria tools.

## Test execution log

| Step | Command | Result |
|---|---|---|
| ruff check (full T-ag-tools-1 surface) | `.venv/bin/ruff check vitalia/backend/src/modules/vitalia/{copilot,sales_agent,agentic,compliance}/ vitalia/backend/tests/...` | All checks passed |
| ruff format (T-ag-tools-1 scoped) | `.venv/bin/ruff format --check <scoped paths>` | 18 files already formatted (4 other files belong to T-ag-tools-2 parallel session) |
| arch fitness (full suite) | `.venv/bin/pytest vitalia/backend/tests/architecture/` | 236/236 PASS |
| unit copilot (full suite) | `.venv/bin/pytest vitalia/backend/tests/unit/modules/vitalia/copilot/` | 128/128 PASS (58 NEW) |
| observability subclass tests | `.venv/bin/pytest .../observability/test_callback_handler.py` | 10/10 PASS |
| anti-duplication audit | `grep -rln "class.*\(BaseObservabilityContext\|BaseAgentCallbackHandler\|FXResolver\|...\)" ... | xargs grep -L "from luana_core_*"` | OK (no violations) |
| cross-brand mirror scan | `for tool in <10 names>; for B in nicolify comunify lupulo; find $B/backend/src -name "${tool}.py"` | OK (no mirrors) |
| engine boundary | `git diff --name-only main...HEAD | grep ^core/luana-core-` | OK (engine src untouched) |
| spanish neutro voseo (copilot/lucas chrome) | `grep -rEn "vos\|sos\|tenés\|..." <prompts dirs> | grep -v "voseo-allowed"` | OK (no voseo in chrome) |
| extensions registration smoke | `register_all(ExtensionPointRegistry()) + reg.get_sales_agent_tool(...)` | All 4 Valeria tools registered with correct tool_groups |

## Anti-duplication audit (cardinal §0) — verified

1. `BaseAgentCallbackHandler` imported from `luana_core_observability.recording.base_callback_handler` ✓
2. `BaseObservabilityContext` imported from `luana_core_observability.recording.turn_envelope` ✓
3. `sanitize_payload` imported from `luana_core_observability.recording.sanitization` (never re-defined) ✓
4. `FXResolver`, `PricingResolver` consumed via base class field — never re-implemented ✓
5. AST parse of subclasses: NO plumbing method redefined (10 forbidden names checked: `on_chat_model_start`, `on_llm_end`, `on_llm_error`, `on_tool_*`, `on_chain_*`, `_persist_llm_call`, `_extract_*` helpers, etc.) ✓
6. AST parse of envelope subclass: NO lifecycle method redefined (`observe_turn`, `_write_turn_*`, `set_turn_*`, `langchain_config`, `_commit_session`) ✓
7. Cross-brand mirror scan: NO duplicate basenames in `nicolify/`, `comunify/`, `lupulo/` ✓
8. Engine boundary: 0 modifications to `core/luana-core-*/src/` (git diff verified) ✓

## Notes — spec drift detected (escalation-worthy but not blocking)

The architectural doc + hipaa-lite rule declares `sanitize_payload(payload, compliance_level="hipaa_lite")` (with kwarg). Engine signature is `sanitize_payload(payload: dict)` — no kwarg. I implemented per engine signature (correct, doesn't break) and surfaced `compliance_level` as a dataclass attribute on the subclass plus a column on the schema-mirror persistence rows. If the platform team later decides `compliance_level` should be an explicit engine kwarg, that's a `/pm-luana` promotion proposal (out of scope here, but flagged in result.md § Critical notes 2).

