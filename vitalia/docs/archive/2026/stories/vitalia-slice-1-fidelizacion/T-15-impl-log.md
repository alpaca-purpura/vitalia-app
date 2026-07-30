# T-15 Implementation Log — Agentic eval goldens (Adrián 4 + Lucas 3 + voice fidelity smoke)

Story: vitalia-slice-1-fidelizacion
Ticket: T-15
Brand: vitalia
Date: 2026-05-20
R23: production_code=false (tests/goldens — Sonnet OK)

## Scope summary

T-15 creates the agentic eval dataset for the re-engagement fidelización module:
- 4 Adrián (sales_agent) reengagement golden YAMLs
- 3 Lucas (copilot/agentic) re_engagement_recommendation golden YAMLs
- 4 corresponding eval persona YAML files
- voice fidelity grader smoke test (15 test functions)
- Lucas prompt cache prefix invariance test (11 test functions)
- Observability invariants extension for reengagement + lucas tools (11 test functions)
- Update test_pass_k_evaluation.py count assertions (13 → 17 goldens, 12 → 16 personas)

## Skills Consulted

### sales-agent-expert
Consulted for: golden YAML schema, voice fidelity grader engine import path, slot 5 BRAND_VOICE cache prefix invariance, voseo-allowed magic comment requirement, pass^k trial policy, persona file location (eval personas separate from production personas).

Decision taken:
- Voice fidelity grader CONSUMED from `luana_core_brand_studio.application.voice_fidelity.grader` (engine) — NOT mirrored (anti-duplication §0)
- Persona files in `tests/agentic_evals/sales_agent/personas/` (eval dir), NOT in `vitalia/backend/src/modules/vitalia/sales_agent/personas/` (production)
- `voseo-allowed` magic comment at top of `test_voice_fidelity_reengagement.py` + golden files that cite voseo markers as detection input
- VOICE_FIDELITY_MIN = 0.85 (per design § 2.8)
- `pytestmark = pytest.mark.no_eval` on all eval tests (CI cost guard)

### copilot-expert
Consulted for: Lucas tool observability trace schema, compute_re_engagement_recommendation output shape, HIPAA-lite dual filter (tenant_id + clinic_id) in all traces, PHI exclusion from trace payloads.

Decision taken:
- Lucas golden YAMLs use `expected_observability.trace_payload_includes/excludes` to declare invariants
- Trace event type: `"tool.compute_re_engagement_recommendation.completed"` (canonical tool event format)
- PHI fields (action, rationale, patient_name, risk_details) MUST be excluded from trace payload
- Aggregate data only in trace: period, clinic_id, top_n, recommendations_count

## State-of-the-art validation

This ticket is `production_code: false` (tests/goldens, not runtime). No LangGraph or Anthropic SDK calls in the test files — synthetic deterministic approach. Cache prefix invariance validated via SHA-256 hash simulation (same approach as existing `test_cache_hit_rate.py` Wave 4 pattern).

Canonical references consulted (accessed 2026-05-20):
- Anthropic prompt caching: `https://platform.claude.com/docs/en/build-with-claude/prompt-caching`
  Key invariant: cache prefix must be byte-identical across turns — no timestamps, conversation_id, turn counters, or random IDs in cacheable blocks.

## Cross-module audit (NO-NEW-LAYER)

Existing engine grader: `core/luana-core-brand-studio/src/luana_core_brand_studio/application/voice_fidelity/grader.py` — consumed, not mirrored.

Grep evidence:
```bash
grep -rn "voice_fidelity" core/luana-core-brand-studio/src/ → grader.py (engine SSoT)
grep -rn "from luana_core_brand_studio" vitalia/backend/tests/agentic_evals/ → test_voice_fidelity_*.py (correct consume pattern)
```

No new abstraction layers created. All new code is test/golden YAML only.

## Files created / modified

### NEW — Adrián eval persona YAMLs (4)
- `vitalia/backend/tests/agentic_evals/sales_agent/personas/reengagement_multi_session.yaml`
- `vitalia/backend/tests/agentic_evals/sales_agent/personas/reengagement_follow_up.yaml`
- `vitalia/backend/tests/agentic_evals/sales_agent/personas/reengagement_maintenance.yaml`
- `vitalia/backend/tests/agentic_evals/sales_agent/personas/reengagement_absence_opted_out.yaml`

### NEW — Adrián reengagement golden YAMLs (4)
- `vitalia/backend/tests/agentic_evals/sales_agent/goldens/reengagement/happy_multi_session.yaml`
- `vitalia/backend/tests/agentic_evals/sales_agent/goldens/reengagement/happy_follow_up.yaml`
- `vitalia/backend/tests/agentic_evals/sales_agent/goldens/reengagement/happy_maintenance.yaml`
- `vitalia/backend/tests/agentic_evals/sales_agent/goldens/reengagement/absence_optin_guard.yaml`

### NEW — Lucas golden YAMLs (3)
- `vitalia/backend/tests/agentic_evals/lucas/re_engagement_recommendation/high_value_dental_critico.yaml`
- `vitalia/backend/tests/agentic_evals/lucas/re_engagement_recommendation/psicologia_safety_referral.yaml`
- `vitalia/backend/tests/agentic_evals/lucas/re_engagement_recommendation/estetica_maintenance_segment.yaml`

### NEW — __init__.py files (2)
- `vitalia/backend/tests/agentic_evals/lucas/__init__.py`
- `vitalia/backend/tests/agentic_evals/lucas/re_engagement_recommendation/__init__.py`

### NEW — Test files (3)
- `vitalia/backend/tests/agentic_evals/sales_agent/test_voice_fidelity_reengagement.py` (15 test functions)
- `vitalia/backend/tests/agentic_evals/lucas/test_prompt_cache_hit_rate.py` (11 test functions)
- `vitalia/backend/tests/agentic_evals/test_observability_invariants.py` (11 test functions)

### MODIFIED — Existing test file (1)
- `vitalia/backend/tests/agentic_evals/sales_agent/test_pass_k_evaluation.py`
  - `_grade_tool_trajectory`: added `absence_optin_guard` to empty-trajectory scenarios
  - `test_adrian_goldens_count_is_13` → `test_adrian_goldens_count_is_17` (13 → 17)
  - `test_adrian_personas_count_is_12` → `test_adrian_personas_count_is_16` (12 → 16)
  - `test_adrian_pass_k_evaluation`: docstring + count assertion updated (13 → 17)

## HIPAA-lite compliance

All golden files comply with `vitalia/.claude/rules/hipaa-lite.md`:
- PHI fields (patient.name, patient.phone, patient.dni, etc.) use placeholders: `[PATIENT_ID]`, `[PATIENT_PHONE]`
- Trace payload includes/excludes declarations correctly exclude action/rationale
- Dual filter (tenant_id + clinic_id) declared in `expected_tenant_isolation` sections
- `voseo-allowed` magic comment added where golden files cite voseo markers as detection test input

## Test results

All 47 tests PASS (2026-05-20):
- test_voice_fidelity_reengagement.py: 15 passed
- test_pass_k_evaluation.py: 11 passed (including 3 parametrized pass^k trials × 17 goldens)
- test_prompt_cache_hit_rate.py: 11 passed
- test_observability_invariants.py: 11 passed (includes I8-I14 invariants)

Native gates: ruff check (0 errors) + ruff format (clean).

## Default-flip detection (Step 0.5)

No feature flags flipped. This is tests/goldens only — no config.py touches.

## §11 gaps (R24 context-brief partial)

CONTEXT-BRIEF.md was a skeleton (all fields _pending_). Fell back to direct reads per R24 fallback policy. No faithfulness gaps identified — raw files (06-tickets.yaml, tool source files) were read directly.
