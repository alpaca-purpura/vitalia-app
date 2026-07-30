# T-onboarding-7 — Impl Log
## Wizard Goldens Smoke Regression — Post FE Wire-up

**Brand:** vitalia  
**Ticket:** T-onboarding-7  
**State:** done  
**Owner:** claude-sonnet  
**production_code:** false (R23 OPT-OUT ratificado Chris 2026-05-18 — smoke regression, no código agentic)

---

## § Skills Consulted

| Skill | Por qué invocada | Decisión tomada |
|---|---|---|
| `backend-expert` | Smoke test: pytest patterns, importlib usage, DDD constraints | Uso `importlib.util.spec_from_file_location` + `sys.modules` pre-registration para Python 3.12 @dataclass(frozen=True). `pytestmark = pytest.mark.no_eval`. |
| `tessl__pytest-api-testing` | Fixture scoping, edge cases | `_import_runner()` module-level singleton, `_load_yaml()` helper. No DB fixtures (smoke only). |

---

## § R24 Brief Acceptance Gate

- **CONTEXT-BRIEF.md:** `Validator pass: _pending_` — faithfulness flag `clean` (no blocker).
- **Decision:** Proceed. Faithfulness flag clean + ticket scope entirely legible from 06-tickets-refresh.yaml + existing test file. Validator skip cited per R24 exception path: `context-validator-skipped: faithfulness clean, ticket scope self-contained`.

---

## § Default-flip pre-audit (Step 0.5)

No flag flips in this ticket. Scope is smoke regression tests only — no production code, no config changes.

---

## § Cross-module reads (read-only)

- `vitalia/backend/tests/agentic_evals/copilot/test_wizard_pass_k_evaluation.py` — existing runner, READ-ONLY verify imports + constants.
- `vitalia/backend/tests/agentic_evals/copilot/wizard_goldens/happy.yaml` — READ-ONLY, extract Valeria assistant turns.
- `vitalia/backend/src/modules/vitalia/sales_agent/personas/warm_close_dental.yaml` — READ-ONLY, voice constraints anchor for grader smoke.
- `core/luana-core-brand-studio/src/luana_core_brand_studio/application/voice_fidelity/grader.py` — engine grader, consumed READ-ONLY via import.

---

## § Anti-duplication §0

Voice fidelity grader VIVE en engine:
`core/luana-core-brand-studio/src/luana_core_brand_studio/application/voice_fidelity/grader.py`

This file IMPORTS the engine grader — NEVER mirrors. The grader returns `judge_skipped=True` when no LLM API key is available (CI path). The smoke test verifies scaffolding is consumable; deep fidelity grading requires `RUN_LLM_JUDGE=1`.

---

## § TDD Flow

| Layer | RED state | GREEN state | Notes |
|---|---|---|---|
| Smoke test file | File did not exist (import → `ModuleNotFoundError`) | 14/14 PASS | Test file written, debugged, passing |

**RED confirmed:** `pytest vitalia/backend/tests/agentic_evals/copilot/test_wizard_goldens_post_fe_wire.py` → `No such file` (file not yet created) → collection error.

**GREEN achieved:** 4 new smoke tests PASS + 10 original runner tests PASS = 14/14.

---

## § Errors Encountered and Fixes

### Error 1: `ModuleNotFoundError: No module named 'vitalia'`

- **Cause:** Initial attempt used `import vitalia.backend.tests.agentic_evals.copilot.test_wizard_pass_k_evaluation as _runner`. pytest rootdir=`vitalia/backend` with `pythonpath=["."]` — `vitalia` package does not exist in sys.path.
- **Fix:** Switched to `importlib.util.spec_from_file_location(module_name, runner_path)` with absolute path resolution relative to `__file__`.

### Error 2: `AttributeError: 'NoneType' object has no attribute '__dict__'` in dataclasses

- **Cause:** Using importlib without pre-registering the module in `sys.modules`. Python 3.12 `@dataclass(frozen=True)` calls `sys.modules.get(cls.__module__).__dict__` during class construction. Without pre-registration, `cls.__module__` resolved to the unregistered module name → `sys.modules.get()` returned `None`.
- **Fix:** Added `sys.modules[module_name] = module` BEFORE `spec.loader.exec_module(module)`.

### Error 3: ruff format failure

- **Cause:** String formatting style in `assert not missing` multi-line statement.
- **Fix:** Ran `ruff format vitalia/backend/tests/agentic_evals/copilot/test_wizard_goldens_post_fe_wire.py` — reformatted 1 file.

---

## § Implementation Summary

**File created:** `vitalia/backend/tests/agentic_evals/copilot/test_wizard_goldens_post_fe_wire.py`

4 smoke tests:

| Test | Scope | Result |
|---|---|---|
| `test_4_goldens_exist` | Filesystem check: 4 golden YAML at exact canonical paths | PASS |
| `test_runner_imports_resolve` | Runner importable, constants not drifted (k=3, threshold=0.5, voice=0.85), 4 goldens discovered | PASS |
| `test_run_happy_golden_smoke` | happy.yaml → single `_grade_trial()` → `trial_passed=True`, all 5 rubric scores in [0,1] | PASS |
| `test_voice_fidelity_grader_smoke` | Engine grader on Valeria wizard turn → valid `GraderResult` shape, `banned_vocab_absence=True` | PASS |

**Key implementation detail:** `_import_runner()` uses `importlib.util.spec_from_file_location` with `sys.modules[module_name] = module` pre-registration before `exec_module()` to satisfy Python 3.12 `@dataclass(frozen=True)` `cls.__module__` resolution requirement.

**Voice fidelity anchor:** `warm_close_dental.yaml` from `vitalia/backend/src/modules/vitalia/sales_agent/personas/` provides `voice_constraints.forbidden_phrases` + `allowed_phrases`. A Valeria wizard assistant turn from `happy.yaml` is the test response. The dental persona was shipped in T-ag-evals-1.

---

## § Final Gate Results

```
pytest vitalia/backend/tests/agentic_evals/copilot/ -v
========================================
test_wizard_goldens_post_fe_wire.py::test_4_goldens_exist PASSED
test_wizard_goldens_post_fe_wire.py::test_runner_imports_resolve PASSED
test_wizard_goldens_post_fe_wire.py::test_run_happy_golden_smoke PASSED
test_wizard_goldens_post_fe_wire.py::test_voice_fidelity_grader_smoke PASSED
test_wizard_pass_k_evaluation.py::test_discover_goldens PASSED
test_wizard_pass_k_evaluation.py::test_happy_golden_schema PASSED
test_wizard_pass_k_evaluation.py::test_adversarial_golden_schema PASSED
test_wizard_pass_k_evaluation.py::test_negative_golden_schema PASSED
test_wizard_pass_k_evaluation.py::test_edge_browser_close_schema PASSED
test_wizard_pass_k_evaluation.py::test_persona_resolution PASSED
test_wizard_pass_k_evaluation.py::test_happy_golden_pass_k PASSED
test_wizard_pass_k_evaluation.py::test_adversarial_golden_pass_k PASSED
test_wizard_pass_k_evaluation.py::test_negative_golden_pass_k PASSED
test_wizard_pass_k_evaluation.py::test_edge_browser_close_pass_k PASSED
========================================
14 passed, 4 warnings in 0.63s

ruff check: 0 errors
ruff format: clean (1 file reformatted during dev)
```

**No files modified** outside the new test file. Wizard goldens untouched. Runner untouched. Engine core untouched.

---

## § Scope Verification (forbidden boundaries)

- [x] NO edit `core/luana-core-*/src/` — engine consumed READ-ONLY via import
- [x] NO touch `vitalia/backend/src/modules/vitalia/copilot/` — exclusive `builder-agentic`
- [x] NO touch `vitalia/backend/src/modules/vitalia/sales_agent/` — exclusive `builder-agentic`
- [x] NO touch wizard goldens YAML (read-only verify)
- [x] NO touch runner `test_wizard_pass_k_evaluation.py` (read-only verify)
- [x] NO cross-brand pollution
- [x] NO root legacy paths

---

*Impl log: T-onboarding-7 — state: done*
