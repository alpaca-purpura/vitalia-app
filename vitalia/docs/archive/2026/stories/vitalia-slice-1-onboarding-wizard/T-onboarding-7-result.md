# T-onboarding-7 — Result

**Brand:** vitalia  
**Ticket:** T-onboarding-7 — Wizard Goldens Smoke Regression (Post FE Wire-up)  
**State:** done  
**Depends on:** T-onboarding-5 (69049df), T-onboarding-6 (221d0ef)  
**production_code:** false

---

## Verdict: PASS — 14/14 tests GREEN

All 4 new smoke tests PASS. All 10 existing runner tests still PASS. No regressions introduced by T-onboarding-6 FE wire-up.

---

## Deliverables

### File created

| Path | LOC | Description |
|---|---|---|
| `vitalia/backend/tests/agentic_evals/copilot/test_wizard_goldens_post_fe_wire.py` | ~160 | Smoke regression test file (4 tests) |

### Files NOT modified (read-only verify)

- `vitalia/backend/tests/agentic_evals/copilot/test_wizard_pass_k_evaluation.py` — runner intact
- `vitalia/backend/tests/agentic_evals/copilot/wizard_goldens/*.yaml` — all 4 goldens intact
- `vitalia/backend/src/modules/vitalia/sales_agent/personas/warm_close_dental.yaml` — read-only
- `core/luana-core-brand-studio/**` — engine grader consumed via import, never touched

---

## Test Results

```
vitalia/backend/tests/agentic_evals/copilot/test_wizard_goldens_post_fe_wire.py::test_4_goldens_exist PASSED
vitalia/backend/tests/agentic_evals/copilot/test_wizard_goldens_post_fe_wire.py::test_runner_imports_resolve PASSED
vitalia/backend/tests/agentic_evals/copilot/test_wizard_goldens_post_fe_wire.py::test_run_happy_golden_smoke PASSED
vitalia/backend/tests/agentic_evals/copilot/test_wizard_goldens_post_fe_wire.py::test_voice_fidelity_grader_smoke PASSED
vitalia/backend/tests/agentic_evals/copilot/test_wizard_pass_k_evaluation.py::test_discover_goldens PASSED
vitalia/backend/tests/agentic_evals/copilot/test_wizard_pass_k_evaluation.py::test_happy_golden_schema PASSED
vitalia/backend/tests/agentic_evals/copilot/test_wizard_pass_k_evaluation.py::test_adversarial_golden_schema PASSED
vitalia/backend/tests/agentic_evals/copilot/test_wizard_pass_k_evaluation.py::test_negative_golden_schema PASSED
vitalia/backend/tests/agentic_evals/copilot/test_wizard_pass_k_evaluation.py::test_edge_browser_close_schema PASSED
vitalia/backend/tests/agentic_evals/copilot/test_wizard_pass_k_evaluation.py::test_persona_resolution PASSED
vitalia/backend/tests/agentic_evals/copilot/test_wizard_pass_k_evaluation.py::test_happy_golden_pass_k PASSED
vitalia/backend/tests/agentic_evals/copilot/test_wizard_pass_k_evaluation.py::test_adversarial_golden_pass_k PASSED
vitalia/backend/tests/agentic_evals/copilot/test_wizard_pass_k_evaluation.py::test_negative_golden_pass_k PASSED
vitalia/backend/tests/agentic_evals/copilot/test_wizard_pass_k_evaluation.py::test_edge_browser_close_pass_k PASSED

14 passed, 4 warnings in 0.63s
```

---

## Quality Gates

| Gate | Result |
|---|---|
| `ruff check` | 0 errors |
| `ruff format --check` | PASS (clean) |
| 4 new smoke tests | PASS |
| 10 existing runner tests (regression) | PASS |
| wizard goldens untouched | verified |
| runner untouched | verified |
| engine core untouched | verified |

---

## Smoke Test Coverage

| Test | What it verifies | Threshold |
|---|---|---|
| `test_4_goldens_exist` | 4 golden YAML files at exact canonical paths post FE wire-up | Must exist |
| `test_runner_imports_resolve` | Runner importable, k=3, threshold=0.5, voice=0.85 constants not drifted, 4 goldens discovered | Exact match |
| `test_run_happy_golden_smoke` | happy.yaml → `_grade_trial()` → trial_passed, all 5 rubric scores in [0,1] | ≥0.5 pass rate |
| `test_voice_fidelity_grader_smoke` | Engine grader on Valeria wizard turn → valid GraderResult shape, `banned_vocab_absence=True` | Shape valid + no banned phrases |

---

## Notes

- **Python 3.12 importlib fix:** `_import_runner()` pre-registers module in `sys.modules` before `exec_module()` to satisfy `@dataclass(frozen=True)` `cls.__module__` resolution. This is the canonical pattern for importing sibling pytest files by path.
- **judge_skipped=True in CI:** Engine voice fidelity grader returns `judge_skipped=True` when no LLM API key is available. Smoke test explicitly handles this path — shape validation + `banned_vocab_absence` do not require LLM judge.
- **R23 OPT-OUT:** production_code=false — Sonnet eligibility confirmed.
