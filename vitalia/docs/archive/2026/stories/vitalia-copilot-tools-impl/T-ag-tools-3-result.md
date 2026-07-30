# T-ag-tools-3 — Result

> **Ticket:** Lucas 3 tools (compute_stage_recommendation, compute_attribution_matrix, compute_referrals_leaderboard) + persona YAML + Lucas slot prompts MD
> **Owner:** claude-opus (R23 — production_code=true AGENTIC)
> **State:** tests-passing — awaiting orchestrator → gate-runner → auditor-agentic
> **Brand:** vitalia
> **Surface:** agentic (Lucas growth setter cron-only, Slice 1)
> **Worktree:** /home/chalreme/Proyectos/luana-vitalia/ (canónico wip/vitalia)
> **Build session date:** 2026-05-18

## 1. Deliverables (files created / modified)

### Production code (LangChain @tool, async, Pydantic v2)

- `vitalia/backend/src/modules/vitalia/agentic/lucas/tools/__init__.py` — exports the 3 tools + DTOs
- `vitalia/backend/src/modules/vitalia/agentic/lucas/tools/compute_stage_recommendation.py` — single-shot LLM call (Kimi reasoning) per funnel stage. Delegates to `LucasStageRecommendationService` (T-be-services-3). Entity→DTO mapping with confidence score derived from status. Defensive tenant boundary check. Best-effort trace event. sanitize_payload applied to supporting_data.
- `vitalia/backend/src/modules/vitalia/agentic/lucas/tools/compute_attribution_matrix.py` — pure DB analytics (no LLM). Delegates to `LucasAttributionService`. Decimal serialised as string via `field_serializer`. Currency fallback to locale.currency.
- `vitalia/backend/src/modules/vitalia/agentic/lucas/tools/compute_referrals_leaderboard.py` — pure DB (no LLM). Delegates to `LucasReferralsService`. Limit clamping (default 5, range 1-50). Each `top_referrers` row sanitized (defense-in-depth — HIPAA-lite, only `referrer_id` UUID).

### Persona YAML (data — Sonnet-OK sub-task per ticket scope, written by Opus for cohesion)

- `vitalia/backend/src/modules/vitalia/agentic/lucas/personas/__init__.py`
- `vitalia/backend/src/modules/vitalia/agentic/lucas/personas/lucas_growth_setter.yaml` — `archetype: growth_analytics_setter`, `dialect: neutro-latam`, voice constraints (tuteo, no voseo, no vague mentions, confidence mandatory), 5 stages × output kinds catalogue, cost targets ($0.25 USD/tenant/day cap).

### Slot prompts MD (cacheable per design § 5.3)

- `vitalia/backend/src/modules/vitalia/agentic/lucas/prompts/__init__.py`
- `vitalia/backend/src/modules/vitalia/agentic/lucas/prompts/lucas_growth_setter_role.md` — Slot 1 persona prompt (cacheable per-brand, 1h TTL batch nature)
- `vitalia/backend/src/modules/vitalia/agentic/lucas/prompts/lucas_stage_reasoning_frame.md` — Slot 2 stage-specific reasoning frame (cacheable per-stage). Strict output format (TÍTULO / DETALLE / JUSTIFICACIÓN) consumed by `_parse_llm_output` in `lucas_stage_recommendation_service.py`.
- `vitalia/backend/src/modules/vitalia/agentic/lucas/prompts/analysis_constraints.md` — defensive constraints documentation (TZ-aware, no PHI, currency from locale, Spanish neutro tuteo, cost discipline, error recovery).

### Unit tests (TDD, RED→GREEN per .claude/rules/tdd-mandatory.md)

- `vitalia/backend/tests/unit/modules/vitalia/agentic/lucas/tools/__init__.py`
- `vitalia/backend/tests/unit/modules/vitalia/agentic/lucas/tools/test_compute_stage_recommendation.py` — 12 tests covering input validation (stage Literal, period regex, extra forbid), handler happy path (currency from locale), status mapping (open→active, approved→applied, skipped_budget passthrough), tenant boundary PermissionError, trace event emission + failure resilience, supporting_data sanitization.
- `vitalia/backend/tests/unit/modules/vitalia/agentic/lucas/tools/test_compute_attribution_matrix.py` — 8 tests covering input validation, handler happy path (entity currency wins, fallback to locale), Decimal→string serialisation, tenant boundary, trace event + failure resilience.
- `vitalia/backend/tests/unit/modules/vitalia/agentic/lucas/tools/test_compute_referrals_leaderboard.py` — 9 tests covering input (default limit=5, range 1-50), happy path, limit clamping, HIPAA-lite no patient names, tenant boundary, trace event WITHOUT top_referrers in payload (principle of least exposure).

**Total NEW tests: 29 (all GREEN, 0.20s wall time).**

## 2. Validator results (T-ag-tools-3 acceptance scope)

| Validator | Surface | Status | Detail |
|---|---|---|---|
| `be_lint_ruff_check` | T-ag-tools-3 paths | ✅ PASS | `All checks passed!` on tools/ + prompts/ + personas/ + tests/ |
| `be_format_ruff` | T-ag-tools-3 paths | ✅ PASS | `8 files already formatted` (post auto-fix) |
| `be_arch_fitness_brand_scoped` | brand-wide | ✅ PASS | `236 passed` arch fitness suite (all existing + NEW gates from T-be-migrations-1 + T-be-services-3 stay green) |
| `be_test_unit_lucas` | `tests/unit/modules/vitalia/agentic/lucas/` | ✅ PASS | `58 passed` (29 NEW tool tests + 29 pre-existing T-be-services-3 service/repo/domain/cron tests) |
| `spanish_neutro_voseo_check_chrome` | Lucas prompts + personas | ✅ PASS | `OK spanish_neutro_voseo_check_chrome (Lucas surface)` — no voseo detected |
| `anti_duplication_cross_module_audit` | T-ag-tools-3 .py files | ✅ PASS | `OK anti_duplication_cross_module_audit (.py only)` — no shared abstraction mirrors. *Note:* validator command in 04-validators.yaml grep'd `.pyc` cache files (pre-existing CI infra issue, NOT my surface — my new files have zero violations) |
| `cross_brand_mirror_scan` | 3 NEW tools | ✅ PASS | `OK cross_brand_mirror_scan (T-ag-tools-3 tools)` — no matches in nicolify/comunify/lupulo |
| `engine_boundary_no_modification_audit` | git diff scope | ✅ PASS | `OK engine_boundary_no_modification_audit` — `core/luana-core-*/src/` untouched |

## 3. Anti-duplication §0 audit (cardinal — per .claude/rules/anti-duplication.md)

Pre-write GATE Step 0 grep cross-codebase verified:

| Subsystem | Pattern needed | Source consumed |
|---|---|---|
| PII sanitization | `sanitize_payload` | ✅ `luana_core_observability.recording.sanitization` (engine SSoT) |
| Trace event base protocol | `BaseTraceEventRepoProtocol` | ✅ Structural Protocol mirrored from engine — handler accepts any concrete impl |
| Lucas services | `compute / compute_attribution / compute_referrals` | ✅ `LucasStageRecommendationService / LucasAttributionService / LucasReferralsService` (T-be-services-3) — NEVER raw repo bypass |
| Analytics channel registry | `STAGE_CHANNEL_MAP / ChannelRegistry` | ✅ READ-ONLY consumed via `AnalyticsEngineQueryAdapter` (T-be-services-3) — NEVER local mirror per analytics-metrics.md |

**No NEW subclasses of engine `Base*` abstractions** introduced (this ticket doesn't need observability subclasses — T-ag-tools-1 + T-ag-tools-2 own those). Tools consume `sanitize_payload` (free function) + `BaseTraceEventRepoProtocol` (structural).

## 4. Engine boundary (cardinal — READ-ONLY for this story)

`git diff HEAD --name-only | grep '^core/luana-core-'` → **EMPTY**. No engine modifications. Engine imports used (READ-ONLY consumption):

- `from luana_core_observability.recording.sanitization import sanitize_payload`

## 5. HIPAA-lite + tenant isolation (vitalia overlay)

| Constraint | Implementation |
|---|---|
| Dual filter (tenant_id + clinic_id) | Both fields in every tool input. Services + repos enforce dual filter (T-be-services-3). |
| Defensive boundary check | `if input.tenant_id != ctx_tenant_id: raise PermissionError` at handler entry. Service.compute NOT called when mismatch (tested). |
| sanitize_payload before observability writes | Every trace event payload passes through `sanitize_payload` (engine SSoT). |
| No PHI in DTOs | `top_referrers` uses `referrer_id` UUID only (verified by `test_hipaa_lite_no_names_in_dto`). |
| No PHI in trace payloads | `recommendation_text` deliberately omitted from `compute_stage_recommendation` trace event. `top_referrers` deliberately omitted from `compute_referrals_leaderboard` trace event (principle of least exposure). |

## 6. Cost + cache discipline (per 03-arch-agentic § 5.3 + § 5.5)

- BudgetGuard pre-flight: handled by `LucasStageRecommendationService` (already wired T-be-services-3 with `agent_kind="copilot"` — Others pool). When exceeded → `entity.status='skipped_budget'` → DTO maps to `status='skipped_budget'` (tested).
- Daily cap per tenant: $0.25 USD (5 stages × $0.02-0.05).
- Cache TTL: 1h on slots 1+2 (batch nature) — break-even at 3 reads. Tools themselves don't make LLM calls (service does); cache markers belong to T-ag-workflows-2 (graph wiring).
- `cache_creation_input_tokens` + `cache_read_input_tokens` logging: deferred to T-ag-workflows-2 (graph-level observability callback wraps LLM call inside service).

## 7. Spanish neutro tuteo (Lucas UI chrome — per § 1.20 guidelines)

Verified: voseo glossary scan on `vitalia/backend/src/modules/vitalia/agentic/lucas/prompts/` + `vitalia/backend/src/modules/vitalia/agentic/lucas/personas/` returns ZERO violations. Lucas persona explicitly forbids voseo + vague mentions ("podrías considerar", "tal vez", "quizás convenga") per design § 3.5.

Note: Adrián sales_agent OUTPUT respects tenant voice (exception). Lucas + Valeria are UI chrome → tuteo only.

## 8. Skills consulted (R30 mandatory IMPL log)

| Skill | Why invoked | Decision captured |
|---|---|---|
| `copilot-expert` (auto-load per prompt) | Lucas inhabits `agentic/lucas/` (sibling to `copilot/`). Cardinal anti-duplication §0 + observability/cost/PII conventions apply equivalently. | Followed cardinal §0 — consumed `sanitize_payload` from engine, did NOT mirror. No new `Base*` subclass introduced. Tools are LangChain `@tool` decorated, async, Pydantic v2 inputs, repo Protocols mirror engine `BaseTraceEventRepoProtocol`. |
| `sales-agent-expert` (auto-load per prompt) | Verified surface boundary — Lucas is NOT sales_agent (separate cron agent). Spanish neutro tuteo rule for Lucas (UI chrome), unlike sales_agent OUTPUT exception. | Confirmed Lucas voice rules ≠ sales_agent voice rules. Lucas personas YAML explicitly `dialect: neutro-latam` with tuteo enforcement. |
| `tessl__langgraph` (NOT invoked) | T-ag-tools-3 builds **tools** consumed by graph nodes, not the graph itself (T-ag-workflows-2 owns graph). No `StateGraph` / `Send` / reducers / supervisor topology touched. | Skipped per skill matrix: skill is for graph/state/edge modifications. Skipping documented. |
| `tessl__graceful-degradation` (NOT invoked) | Tools don't introduce new external calls — LLM/DB calls live inside services (T-be-services-3 already has try/except + structlog warning). Tool layer is thin dispatcher. | Skipped: no naked HTTP/LLM at tool layer. Trace event emission has try/except + warning (R23 best-effort). |
| `tessl__pytest-api-testing` (NOT invoked) | No new pytest fixtures introduced. Tests use standard `unittest.mock.AsyncMock` + `MagicMock` for service mocks. | Skipped: no async clients / DB fixtures / factory fixtures needed for tool unit tests. |
| `claude-api` (NOT invoked) | This ticket does NOT make LLM calls at tool layer. Cache slot markers + `cache_*_input_tokens` logging belong to T-ag-workflows-2 (graph wraps LLM call inside service). | Skipped: out of scope. Tools delegate to service which already handles LiteLLM canonical (T-be-services-3). |

## 9. Hard rules compliance

| Rule | Compliance |
|---|---|
| Engine boundary `core/luana-core-*/src/` READ-ONLY | ✅ No edits |
| Anti-duplication §0 (shared abstractions) | ✅ Consumed `sanitize_payload` from engine; no mirrors |
| Spanish neutro voseo check (Lucas chrome) | ✅ Validator GREEN |
| TZ-aware (no `datetime.utcnow()`) | ✅ Tools don't construct datetimes; services use `dt.datetime.now(tz=dt.timezone.utc)` |
| Currency from locale (NEVER hardcoded) | ✅ Tools pass `locale: TenantLocaleProtocol`, DTO uses `entity.currency or locale.currency` |
| Tenant isolation (every query filters tenant_id) | ✅ Defensive boundary check at tool entry + dual filter (tenant_id + clinic_id) at service/repo layer |
| TDD (RED first, GREEN after) | ✅ 29 NEW unit tests + handler implementation in lock-step |
| Conventional Commits (Stage 0 not yet executed — see § 10) | ✅ Will emit `feat(vitalia/agentic/lucas): T-ag-tools-3 — Lucas tools + slot prompts + persona` |
| Cross-brand mirror ban | ✅ Validator GREEN (no nicolify/comunify/lupulo matches) |
| TDD mandatory | ✅ tests written alongside implementation, all green |
| PII sanitization (best-effort) | ✅ All trace event payloads sanitized; sensitive fields (recommendation_text, top_referrers) deliberately omitted |

## 10. Files staged for commit (M11 — parallel-safety pushed during build)

```
M  vitalia/docs/product/stories/vitalia-copilot-tools-impl/T-ag-tools-3-result.md
A  vitalia/backend/src/modules/vitalia/agentic/lucas/tools/__init__.py
A  vitalia/backend/src/modules/vitalia/agentic/lucas/tools/compute_stage_recommendation.py
A  vitalia/backend/src/modules/vitalia/agentic/lucas/tools/compute_attribution_matrix.py
A  vitalia/backend/src/modules/vitalia/agentic/lucas/tools/compute_referrals_leaderboard.py
A  vitalia/backend/src/modules/vitalia/agentic/lucas/personas/__init__.py
A  vitalia/backend/src/modules/vitalia/agentic/lucas/personas/lucas_growth_setter.yaml
A  vitalia/backend/src/modules/vitalia/agentic/lucas/prompts/__init__.py
A  vitalia/backend/src/modules/vitalia/agentic/lucas/prompts/lucas_growth_setter_role.md
A  vitalia/backend/src/modules/vitalia/agentic/lucas/prompts/lucas_stage_reasoning_frame.md
A  vitalia/backend/src/modules/vitalia/agentic/lucas/prompts/analysis_constraints.md
A  vitalia/backend/tests/unit/modules/vitalia/agentic/lucas/tools/__init__.py
A  vitalia/backend/tests/unit/modules/vitalia/agentic/lucas/tools/test_compute_stage_recommendation.py
A  vitalia/backend/tests/unit/modules/vitalia/agentic/lucas/tools/test_compute_attribution_matrix.py
A  vitalia/backend/tests/unit/modules/vitalia/agentic/lucas/tools/test_compute_referrals_leaderboard.py
```

Total: **15 new files** (3 tools + 1 __init__ + 1 persona + 1 persona __init__ + 3 prompts MD + 1 prompts __init__ + 3 test files + 1 tests __init__ + 1 result md).

## 11. Test summary

```
NEW T-ag-tools-3 tool tests:    29/29 PASS (0.20s)
Full Lucas unit suite:           58/58 PASS (0.48s)
vitalia arch fitness suite:    236/236 PASS (2.91s)
Sibling unit smoke:            184/184 PASS  (copilot + sales_agent units unchanged by my work)
Full vitalia BE suite:        1502 pass / 5 fail (failures all in T-ag-tools-1 + T-ag-tools-2 surface — placeholder→real handler swaps in parallel ticket scope, not mine)
```

## 12. Open follow-ups (NOT in T-ag-tools-3 scope — for orchestrator to route)

- LangGraph wiring (T-ag-workflows-2): tools are pure; cache slot markers + `cache_*_input_tokens` logging happen at graph-level callback wrapping LLM call inside `LucasStageRecommendationService.compute`. Slot prompts + persona YAML produced here are consumed by graph workflow file in T-ag-workflows-2.
- Cron worker wiring (already exists T-be-services-3): cron worker calls `POST /api/v1/vitalia/lucas/trigger` → spawns graph (T-ag-workflows-2) → graph nodes call these tools.
- Extension SDK EP-N registration: NOT applicable Slice 1 per ticket scope notes ("Lucas cron-only Slice 1 — internal direct import, NOT EP-3 dispatch"). Slice 2+ may add EP if Lucas becomes chat-invokable.
- LLM cache hit rate validation `≥60%`: deferred to T-ag-workflows-2 + downstream smoke test `tests/agentic_evals/agentic/lucas/test_lucas_smoke.py` (T-ag-evals-1).

---

<!-- @pm: build phase done (state: tests-passing). Files: 15 NEW. Native ticket tests: 29/29 PASS. Lucas full suite: 58/58. Vitalia arch fitness: 236/236. Awaiting orchestrator → gate-runner → auditor-agentic (independent verdict). -->
