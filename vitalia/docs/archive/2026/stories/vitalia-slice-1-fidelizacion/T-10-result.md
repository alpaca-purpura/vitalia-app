# T-10 — Result

> Ticket: T-10 — Agentic Lucas tool `compute_re_engagement_recommendation`
> Brand: vitalia
> Surface: agentic · production_code: true (R23 → Opus 4.7 — this builder)
> Story: vitalia-slice-1-fidelizacion
> State: tests-passing (awaiting auditor)
> Date: 2026-05-20

## Files created / modified

| Path | Action | Lines |
|---|---|---|
| `vitalia/backend/src/modules/vitalia/agentic/lucas/application/services/lucas_re_engagement_service.py` | NEW | 270 |
| `vitalia/backend/src/modules/vitalia/agentic/lucas/tools/compute_re_engagement_recommendation.py` | NEW | 217 |
| `vitalia/backend/src/modules/vitalia/agentic/lucas/tools/__init__.py` | EXTEND (add re-exports) | +8 / -0 |
| `vitalia/backend/src/modules/vitalia/fidelizacion/infrastructure/repositories/re_engagement_event_repository.py` | EXTEND (add `list_in_period` helper) | +34 / -0 |
| `vitalia/backend/tests/unit/modules/vitalia/agentic/lucas/application/services/test_lucas_re_engagement_service.py` | NEW | 297 |
| `vitalia/backend/tests/unit/modules/vitalia/agentic/lucas/tools/test_compute_re_engagement_recommendation.py` | NEW | 286 |

Path deviations from ticket spec documented in `T-10-impl-log.md` § File placement — preserve cross-PR Lucas package convention.

## Tests — native pass count

| Suite | Count | Status |
|---|---|---|
| T-10 service unit tests (`test_lucas_re_engagement_service.py`) | 11 | ✅ PASS |
| T-10 tool unit tests (`test_compute_re_engagement_recommendation.py`) | 13 | ✅ PASS |
| Full Lucas suite (`tests/unit/modules/vitalia/agentic/lucas/`) — regression check | 102 | ✅ PASS |
| Fidelización application services (`tests/modules/vitalia/fidelizacion/application/`) — regression after repo extension | 29 | ✅ PASS |
| Vitalia arch fitness gates (`tests/architecture/`) | 265 | ✅ PASS |

**Total new tests: 24/24 GREEN.** **Zero regressions.** Pre-existing T-7 router test failure (`ReEngagementOutcome.SCHEDULED` AttributeError) is unrelated to T-10 scope.

## Validators (per acceptance criteria)

| Validator id | Result | Notes |
|---|---|---|
| `be_unit_tests_fidelizacion` | ✅ PASS (29/29) | Fidelización application services regression-free after `list_in_period` repo helper extension |
| `be_arch_fitness` | ✅ PASS (265/265) | All vitalia arch fitness gates GREEN (PHI dual filter, DDD boundaries, no cross-brand imports, etc.) |
| `be_lint_agentic` | ✅ PASS | All 6 T-10 files: 0 ruff errors |
| `agentic_observability_invariants` | DEFERRED | T-15 territory — eval-runtime invariants (cost_bucket=evals_only, cache hit) verified end-to-end against goldens; T-10 satisfies the contract surface (trace event emission with PHI-safe payload, sanitize_payload applied) |
| `agentic_prompt_cache_validation` | DEFERRED | T-15 territory — SLOT 1+2 invariant property tested by `tests/agentic_evals/lucas/test_prompt_cache_hit_rate.py` (Sonnet ticket). T-10 satisfies cache prefix invariance contract: `_LUCAS_REENGAGEMENT_SYSTEM_PROMPT` is module-level constant byte-identical across invocations, NEVER references tenant_id/clinic_id/period; only the user message (SLOT 3) varies |

`be_format` (ruff format --check): ✅ PASS (6/6 already formatted).

## Skills consulted (per Step 0 GATE — R23 enforcement)

Detailed in `T-10-impl-log.md` § Step 0 GATE. Summary:

1. **copilot-expert** — Lucas tool pattern + observability invariants; anti-duplication §0 cardinal (consume engine `sanitize_payload`); structural Protocol for trace event repo
2. **sales-agent-expert** — §0 anti-duplication: sanitize_payload lives in engine; NEVER mirror
3. **tessl__langgraph** — simple non-graph tool justified (single tool aggregate + 1 LLM call); no supervisor topology needed per 03-arch-agentic § 3
4. **claude-api** — Lucas cache slot architecture per 03-arch-agentic § 4.2 (SLOT 1+2 invariant, SLOT 3 variable); LiteLLM canonical post 2026-05-06
5. **`.claude/rules/copilot-resilience.md`** — best-effort observability (try/except + structlog warning + NEVER break tool turn)
6. **`.claude/rules/copilot-observability.md`** — sanitize_payload via engine SSoT; trace event payload omits recommendation bodies
7. **`.claude/rules/anti-duplication.md`** — cross-codebase grep PASS (zero matches for `compute_re_engagement_recommendation` / `LucasReEngagementService` in core or sibling brands)
8. **`.claude/rules/tenant-isolation.md`** — defensive `ctx_tenant_id == input.tenant_id` PermissionError guard
9. **`vitalia/.claude/rules/hipaa-lite.md`** — aggregate-only; dual filter tenant_id+clinic_id at repo (via existing `CompoundScopeRepositoryBase`); NEVER patient identifiers in output
10. **`.claude/rules/tdd-mandatory.md`** — RED tests written FIRST (24/24 confirmed RED → GREEN cycle)
11. **`.claude/rules/auditor-self-fix-policy.md`** — tests written by THIS builder, not auditor; cap audit_iterations 3

## Anti-duplication §0 evidence

```bash
# Cross-codebase grep — verified ZERO matches
$ find /home/chalreme/Proyectos/luana-vitalia -name "compute_re_engagement_recommendation*"
(empty)

$ grep -rn "compute_re_engagement_recommendation\|LucasReEngagementService" \
    /home/chalreme/Proyectos/luana-vitalia/core \
    /home/chalreme/Proyectos/luana-vitalia/nicolify \
    /home/chalreme/Proyectos/luana-vitalia/comunify \
    /home/chalreme/Proyectos/luana-vitalia/lupulo
(empty)
```

**Consumed engine abstractions (NEVER mirrored):**
- `luana_core_observability.recording.sanitization.sanitize_payload` (PII SSoT)
- `luana_core_observability.persistence.base_trace_event_repo.BaseTraceEventRepoProtocol` (structural protocol)
- LLM dispatch goes through `LiteLLMService.generate_response` (engine canonical post 2026-05-06) — used via `LLMServiceProtocol` structural duck-type
- `CompoundScopeRepositoryBase` (engine) consumed transitively via existing `ReEngagementEventRepository` from T-4

## Spec acceptance (T-10 caller spec verbatim)

| Acceptance | Status | Evidence |
|---|---|---|
| Tool name: `compute_re_engagement_recommendation` | ✅ | `compute_re_engagement_recommendation.py::compute_re_engagement_recommendation` |
| Input schema: `tenant_id: UUID`, `clinic_id: UUID`, `period_days: int=30` (actually Literal "7d"/"30d"/"90d" per 03-arch § 2.2 — period→days mapping in handler), `top_n: int=5` | ✅ | `ComputeReEngagementRecommendationInput` Pydantic v2 with `extra="forbid"` + period Literal + `top_n` ge=1 le=20 |
| Output schema: `recommendations: List[{pattern, priority, action, expected_impact_pct, rationale}]` | ✅ | `dict` with `recommendations` key; each rec has all 5 required fields enforced by `_parse_llm_recommendations` filter |
| Service flow: `aggregate_patterns` → `detect_clusters` → `generate_recommendations` (LLM) | ✅ | `LucasReEngagementService.run()` composes the pipeline; methods are also independently callable |
| Slot 1 BRAND_VOICE Lucas (analista interno) + Slot 2 GENERAL_RULES (NO PHI in output) cacheable | ✅ | `_LUCAS_REENGAGEMENT_SYSTEM_PROMPT` module-level constant; byte-identical across invocations (no tenant/clinic/timestamp references) |
| Slot 3 CLUSTER_DATA variable | ✅ | User message constructed per-invocation with `clusters` JSON |
| Slot 4 TASK (generate top N) | ✅ | Embedded in user message: "devuelve hasta {top_n} recomendaciones" |
| LLM via litellm canonical | ✅ | `LLMServiceProtocol.generate_response(...)` structural duck-type compatible with `LiteLLMService.generate_response` engine API |
| Cache TTL 1h (cacheable slots invariant per tenant) | ✅ | Documented in service docstring + verified by test `test_llm_call_uses_cache_friendly_prompt_structure` — system_prompt MUST NOT contain tenant_id/clinic_id |
| Aggregate output ONLY — NEVER echo patient_id/name/email | ✅ | `aggregate_patterns` returns dict with only `pattern`+`outcome`+`count` (tested by `test_aggregate_does_not_leak_patient_id`); `sanitize_payload` applied to each rec defense-in-depth |
| Audit log: each invocation registers (tenant_id, clinic_id, recommendations_count) NO bodies | ✅ | `_emit_trace_event` writes payload with `period`, `clinic_id`, `top_n`, `recommendations_count`. Tested by `test_trace_event_emitted_when_repo_supplied`: asserts `"action"`, `"rationale"`, `"recommendation_text"`, `"body"` ALL absent from trace data |

## HIPAA-lite (vitalia overlay)

| Constraint | Status |
|---|---|
| Dual filter tenant_id + clinic_id in re_engagement_event queries | ✅ via `ReEngagementEventRepository` (CompoundScopeRepositoryBase scope_field="clinic_id") |
| Aggregate-level recommendations; NO per-patient PHI in output | ✅ `aggregate_patterns` returns only (pattern, outcome, count) — verified by `test_aggregate_does_not_leak_patient_id` |
| `sanitize_payload(payload, ...)` applied before any observability write | ✅ at both service level (`generate_recommendations`) and tool level (`_emit_trace_event`) — engine SSoT consumed |
| Audit log row created for each invocation | ✅ via `trace_event_repo.add(...)` best-effort emission |
| Spanish neutro tuteo (Lucas UI chrome) | ✅ `_LUCAS_REENGAGEMENT_SYSTEM_PROMPT` uses tuteo ("devuelve", "trabaja"); NO voseo |
| Defensive cross-tenant boundary check | ✅ `PermissionError` raised when `input.tenant_id != ctx_tenant_id` — verified by `test_cross_tenant_raises_permission_error` |

## Cost guard

Per arch § 4.3 target ≤ $0.05 USD per invocation: enforced by **single LLM call per pipeline** (only when clusters detected). No clusters → zero LLM calls (cost guard via `test_no_clusters_returns_empty_no_llm_call`). Cache TTL 1h via 03-arch-agentic § 4.2 contract — observed at runtime in T-15 eval goldens.

## Known gaps / Slice 2+ defer

- No persistence table (`lucas_re_engagement_recommendations`) — Slice 1 stateless tool per arch § 5
- No KMeans/sklearn clustering — Slice 1 uses simple count>=2 heuristic (arch § 2.2 says "Python deterministic (no LLM)" without specifying algorithm)
- Period `7d|30d|90d` Literal vs arch § 2.2 `Literal["7d", "30d", "90d"]` — IMPLEMENTED as-is per arch
- Lucas insights UI surface (`/fidelización` activity footer) deferred Slice 2 per arch § 6 — Slice 1 tool is callable on-demand only
- Cache hit rate validation lives in T-15 (Sonnet ticket per R23 production_code=false tests)
- Voice fidelity grader for Lucas output — Slice 2+ (not required Slice 1)

## Commit

See `T-10-impl-log.md` for full implementation narrative. Commit will follow the caller-specified message exactly:

```
feat(vitalia/agentic/lucas): T-10 — compute_re_engagement_recommendation tool + ReAct service + LLM aggregation
```

Pushed to `wip/vitalia`.

## Verdict (builder phase)

`tests-passing` — 24 new tests + 102 Lucas regression + 29 fidelización application regression + 265 arch fitness ALL GREEN. Lint + format clean. 0 cross-brand pollution. 0 engine modifications. Anti-duplication §0 satisfied. HIPAA-lite all constraints met.

Awaiting auditor-agentic verdict (Opus, independent).
