# T-0 Result — Gate extension pytest (cross_check_3 path-aware)

**Story:** vitalia-stub-caps-scenario-backfill
**Ticket:** T-0
**Surface:** TOOLING (`scripts/`)
**Production code:** false
**Builder:** claude-sonnet-4-6

## Summary

Extended `scripts/validate_code_cap_bidirectional.py` cross_check_3 to recognize
pytest test files (`.py` extension) alongside the existing JS patterns. Change is
**additive and path-aware** — no existing `.ts` behaviour was modified.

### Diff summary

| File | Lines changed |
|---|---|
| `scripts/validate_code_cap_bidirectional.py` | +8 lines: `PYTEST_PATTERN` constant + path-aware branch in `cross_check_3` + updated `drift_reason` message |
| `scripts/tests/test_validate_code_cap_bidirectional.py` | +4 new test functions (cases a/b/c/d from spec); 15→19 tests total |

### Key change (aditivo)

**Before** (line 185 original):
```python
has_pattern = any(p in content for p in E2E_TEST_PATTERNS)
```

**After** (path-aware):
```python
# Path-aware pattern check: pytest for .py, JS patterns for others.
if full_path.suffix == ".py":
    has_pattern = bool(PYTEST_PATTERN.search(content))
else:
    has_pattern = any(p in content for p in E2E_TEST_PATTERNS)
```

New constant added after `E2E_TEST_PATTERNS`:
```python
PYTEST_PATTERN = re.compile(r"\bdef test", re.MULTILINE)
```

`re` was already imported — no new imports needed.

## TDD evidence (RED → GREEN)

Test (a) confirmed RED against old code:
```
FAILED test_cross_check_3_py_with_def_test_passes
E   AssertionError: Expected pass=1 for .py file with 'def test_',
    got drift instead. Confirms path-aware pattern not yet implemented (RED).
E   assert 0 == 1
```

After fix: all 19 tests GREEN (see gate output below).

## Gate 1 — pytest output (LITERAL)

```
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-9.0.3, pluggy-1.6.0
rootdir: /home/chalreme/Proyectos/luana-vitalia
configfile: pyproject.toml
plugins: anyio-4.13.0, randomly-4.1.0, timeout-2.4.0, langsmith-0.8.3,
         hypothesis-6.152.9, asyncio-1.3.0
asyncio: mode=Mode.AUTO, debug=False
collected 19 items

scripts/tests/test_validate_code_cap_bidirectional.py .................. [ 94%]
.                                                                        [100%]

============================== 19 passed in 0.17s ==============================
```

## Gate 2 — ruff check + format (LITERAL)

```
All checks passed!
ruff check PASS
2 files already formatted
ruff format PASS
```

## Gate 3 — regression: validate --brand vitalia --strict (LITERAL)

```
Loaded 68 caps from vitalia
Running cross-check 3 (scenarios e2e_test paths)...
  total=61 pass=61 drift=0
Running cross-check 4 (access roles ↔ decorators)...
  total=12 pass=11 drift=1

Verdict: SOFT_DRIFT
Drift total: 1 · in HARD checks ([3]): 0
Saved to: vitalia/docs/product/capabilities/_bidirectional-validation.json
exit=0
```

Verdict analysis:
- `cross_check_3 drift=0` — all 61 existing `.ts` scenarios pass unchanged (regression OK)
- `cross_check_4 drift=1` — pre-existing ADVISORY soft drift (unchanged, same as before T-0)
- `exit=0` with `--strict` — HARD drift remains 0
- **Verdict identical to pre-T-0 run** — zero regression

## Skills consulted

| Skill | Invoked | Decision cited |
|---|---|---|
| `backend-expert` | via role (tooling/pytest patterns) | Anti-patterns checked: no `session.query()`, no `datetime.utcnow()`, no `Any`, no `Column()`. `re` already imported — no duplication. Aditivo puro. |
| `.claude/rules/tdd-mandatory.md` | loaded | TDD RED→GREEN order confirmed. First entry in bitácora = RED test (a). |
| `.claude/rules/git-safety.md § Fase solo-bootstrap` | loaded | Commit with `SCOPE_GATE_SKIP=1` + reason in commit body confirmed (scripts/ cross-cutting). |
| `.claude/rules/anti-duplication.md` | loaded | `re` already in scope (line 23). `PYTEST_PATTERN` added at module level alongside `E2E_TEST_PATTERNS` — no duplication. `compute_capability_status.py` NOT touched (as specified). |
| `.claude/rules/test-design-doctrine.md § Verificación REAL` | loaded | Nature = tooling script — pure unit tests with `tmp_path` (deterministic, no network, no DB). Negative cases (b) + regression cases (c/d) included. |

## commit SHA

`6163a930` — pushed to `wip/vitalia` (fast-forward, non-force).

---

*Builder phase output state: tests-passing. Awaiting gate-runner → auditor-backend (independent verdict).*
