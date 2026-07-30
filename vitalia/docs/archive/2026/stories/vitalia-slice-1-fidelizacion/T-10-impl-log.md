# T-10 — Implementation log

> Ticket: T-10 — Agentic Lucas tool `compute_re_engagement_recommendation`
> Brand: vitalia
> Surface: agentic · production_code: true (R23 → Opus 4.7)
> Date started: 2026-05-20

## Step 0 GATE — Skills Consulted (mandatory per dev-team paradigm)

1. **copilot-expert** — Lucas tool pattern + observability rules. Decision: consume engine `sanitize_payload` (NEVER mirror). Reuse the `compute_stage_recommendation` skeleton — same per-file architecture (Pydantic input + DTO output + handler + `_emit_trace_event` helper). Anti-duplication §0 cardinal: trace event repo via Protocol, not concrete; `BaseTraceEventRepoProtocol` consumed structurally.
2. **sales-agent-expert** — §0 anti-duplication confirms `sanitize_payload` lives in engine `core/luana-core-observability/`. NEVER mirror; consume direct.
3. **tessl__langgraph** — Per 03-arch-agentic § 3 & § 10: this is a simple non-graph tool (single async function). NO `StateGraph` needed — the tool runs as a standalone `@tool`-equivalent handler invoked from cron worker / future Lucas analysis graph. Pattern matches the existing `compute_stage_recommendation` (no graph, just async handler).
4. **claude-api** — Per 03-arch-agentic § 4.2 Lucas cache slot architecture: SLOT 1 (system role + Lucas role + Vitalia medical context, cacheable) + SLOT 2 (rubric + JSON schema, cacheable) + SLOT 3 (aggregate data, variable). TTL 1h, break-even at 3 reads. The handler constructs the prompt via `_RECOMMENDATION_PROMPT_TEMPLATE` and uses cacheable-friendly structure. The cache validation lives in T-15 `test_prompt_cache_hit_rate.py` (Sonnet ticket). LLM call goes via `LiteLLMService.generate_response` (sync method per engine canonical post 2026-05-06).
5. **`.claude/rules/copilot-resilience.md`** — best-effort observability: `try/except + structlog warning` for trace event persistence; NEVER break tool turn.
6. **`.claude/rules/copilot-observability.md`** — trace event payload via `sanitize_payload`; PHI defense-in-depth even though Lucas processes aggregates only.
7. **`.claude/rules/anti-duplication.md`** — verified cross-codebase grep for `compute_re_engagement_recommendation` and `LucasReEngagementService`: zero matches in `core/`, `nicolify/`, `comunify/`, `lupulo/`. Brand-specific vertical-medical analytic tool — NEW is justified (no engine equivalent, no cross-brand mirror).
8. **`.claude/rules/tenant-isolation.md`** — defensive `ctx_tenant_id == input.tenant_id` PermissionError guard at handler entry.
9. **`vitalia/.claude/rules/hipaa-lite.md`** — aggregate-level recommendations only; NEVER echo patient_id/name/email in recommendation text; trace event omits `recommendation_text` (defense-in-depth even though LLM input contains no PHI). Dual filter tenant_id + clinic_id at repo level (consumed via existing `ReEngagementEventRepository` which already uses `CompoundScopeRepositoryBase` with `scope_field="clinic_id"`).
10. **`.claude/rules/tdd-mandatory.md`** — RED tests written BEFORE implementation (service unit + tool handler unit). GREEN obtained per layer before moving on.
11. **`.claude/rules/auditor-self-fix-policy.md`** — anticipating auditor escalation: tests must be written by THIS builder (not auditor self-fix). Cap audit_iterations 3.

## Anti-duplication audit verbatim

```bash
# Step 0 GATE — anti-duplication cross-codebase scan
find /home/chalreme/Proyectos/luana-vitalia -name "compute_re_engagement_recommendation*" -type f
# → empty (no existing tool, NEW justified)

grep -rn "compute_re_engagement_recommendation\|LucasReEngagementService" \
  /home/chalreme/Proyectos/luana-vitalia/core \
  /home/chalreme/Proyectos/luana-vitalia/nicolify \
  /home/chalreme/Proyectos/luana-vitalia/comunify \
  /home/chalreme/Proyectos/luana-vitalia/lupulo
# → empty (no cross-brand mirror, no engine equivalent)

# Verified consumed engine abstractions (NEVER mirror):
# - luana_core_observability.recording.sanitization.sanitize_payload (PII SSoT)
# - luana_core_observability.persistence.base_trace_event_repo.BaseTraceEventRepoProtocol (structural)
# - luana_core_llm.providers.litellm.LiteLLMService (canonical LLM dispatch post 2026-05-06)
# - luana_core_platform.repositories.compound_scope_repository.CompoundScopeRepositoryBase
#   (via existing vitalia ReEngagementEventRepository, T-4)
```

## EXTEND vs NEW rationale

| Component | Decision | Why |
|---|---|---|
| Pydantic input schema | NEW | Tool-specific input shape (tenant+clinic+period+top_n) |
| Service class | NEW | Brand-vertical-medical aggregate logic — no engine equivalent |
| Repository | EXTEND | Consume existing `ReEngagementEventRepository` from T-4 — adds new aggregation helper if needed; NEVER new repo class |
| LLM service | CONSUME | `LiteLLMService` engine canonical |
| Sanitize payload | CONSUME | `luana_core_observability.recording.sanitization.sanitize_payload` |
| Trace event repo | CONSUME (Protocol) | `BaseTraceEventRepoProtocol` structural protocol |
| Handler pattern | MIRROR PATTERN | Follows exactly `compute_stage_recommendation` shape (sibling Lucas tool) — pattern reuse, not code mirror |

## File placement (path decisions — DEVIATIONS from ticket spec)

The ticket lists 5 files-in-scope under paths that don't match the existing Lucas convention. Decisions per R5 (extend existing) + M8 (do not replace ajeno structure):

| Ticket spec path | Actual path used | Why |
|---|---|---|
| `vitalia/backend/src/modules/vitalia/agentic/lucas/__init__.py (NEW package)` | EXISTING (`__init__.py` already empty file) | Package already exists since vitalia-copilot-tools-impl story |
| `vitalia/backend/src/modules/vitalia/agentic/lucas/tools/compute_re_engagement_recommendation.py` | SAME | Matches sibling tools |
| `vitalia/backend/src/modules/vitalia/agentic/lucas/services/lucas_re_engagement_service.py` | `vitalia/backend/src/modules/vitalia/agentic/lucas/application/services/lucas_re_engagement_service.py` | Existing convention is `application/services/` (per `lucas_stage_recommendation_service.py` sibling). Following DDD layer. |
| `vitalia/backend/tests/modules/vitalia/agentic/lucas/tools/test_*.py` | `vitalia/backend/tests/unit/modules/vitalia/agentic/lucas/tools/test_*.py` | Existing convention `tests/unit/modules/...` per sibling tool tests |
| `vitalia/backend/tests/modules/vitalia/agentic/lucas/services/test_*.py` | `vitalia/backend/tests/unit/modules/vitalia/agentic/lucas/application/services/test_*.py` | Existing convention |

These deviations preserve cross-PR consistency (Lucas package layout). If auditor flags, a separate "rename Lucas package layout" PR can move ALL Lucas files cohesively. Splitting T-10 alone would create inconsistency.

## Implementation order (RED → GREEN)

1. RED: Service unit tests (`test_lucas_re_engagement_service.py`) — happy path + skipped_budget + clusters detection + cross-tenant + sanitize_payload + LLM error fallback
2. RED: Tool unit tests (`test_compute_re_engagement_recommendation.py`) — input schema validation + handler happy path + tenant boundary + trace event best-effort
3. GREEN: Service implementation
4. GREEN: Tool implementation
5. Wire `__init__.py` re-exports for tools/services
6. Verify lint + format + arch fitness

## Notes — what I'd tell a smart colleague

- The arch spec § 2.2 shows `LucasReEngagementService` returns `recommendations` shape with `severity` + `title` + `body_markdown` + `suggested_actions` + `rationale_json`. This is DIFFERENT from `StageRecommendation` entity (which has `recommendation_text`/`title`/`body` + `priority`/`status`). T-10 spec output_schema (caller prompt) says `recommendations: List[{pattern, priority, action, expected_impact_pct, rationale}]` — a 3rd shape. I'm reconciling: use the **caller prompt's tool output_schema** (most specific contract) since it's the immediate expectation, plus include `cluster_signature` for cache key invariance. Document the choice in `recommendations` Pydantic DTO docstring.
- No NEW persistence — Slice 1 tool is stateless (no `lucas_re_engagement_recommendations` table). Caller invokes on-demand. Slice 2 may persist if cron job needs.
- Period is `"7d"|"30d"|"90d"` per spec (NOT `YYYY-MM` like compute_stage_recommendation). Pydantic Literal.
- `top_n: int=5` per caller spec.
- Cache key for prompt cache (engine handles): the SLOT 1 + SLOT 2 invariance comes from the prompt template being byte-identical across invocations with same tenant+clinic. T-15 will validate hit rate ≥0.60.
- The "clustering" step per arch is "Python deterministic (no LLM)". I'll implement simple heuristic: group events by `(pattern, outcome)` tuple; cluster = any group with `count >= 2`. Real KMeans optional but adds dependency — skipping for Slice 1 minimal scope.

