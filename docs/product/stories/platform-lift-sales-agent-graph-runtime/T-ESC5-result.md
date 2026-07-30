# T-ESC5-result.md — PromptLoader templates engine-package-relative (cwd-independiente)

**State:** tests-passing (GREEN). **Builder:** builder-agentic (flagship). **Date:** 2026-06-22.

## Diff summary (production code)

`core/luana-core-sales-agent/src/luana_core_sales_agent/infrastructure/prompts/base.py` `PromptLoader.__init__`:

```diff
     def __init__(
         self,
-        templates_dir: str = "src/modules/sales_agent/infrastructure/prompts/templates",
+        templates_dir: str | None = None,
     ) -> None:
         """Initialize instance."""
         # 1. Configurar File System Loader (Fallback)
-        base_path = Path.cwd()
-        self.templates_dir = templates_dir
-        full_path = str(base_path / templates_dir)
+        # Default: templates shipped WITH the engine package — cwd-independent, multibrand-safe.
+        # Override (explicit param): absolute as-is, relative resolved against cwd (back-compat).
+        if templates_dir is None:
+            full_path = str(Path(__file__).resolve().parent / "templates")
+        else:
+            _p = Path(templates_dir)
+            full_path = str(_p if _p.is_absolute() else Path.cwd() / _p)
+        self.templates_dir = full_path
```

Verified: `self.templates_dir` is consumed only within `base.py` (grep). The override branch preserves back-compat. The `copilot` sibling loader (`core/luana-core-platform/.../prompts/base.py`) is a DIFFERENT package — NOT touched (out of scope → /harness-issue). Template `message_completeness.j2` confirmed present in the engine package templates dir (GREEN assertion is real, not false-positive).

## Test created (TDD)

- `core/luana-core-sales-agent/tests/architecture/test_esc5_templates_cwd_independent.py` (NEW — verbatim copy from `verified-arch-tests.md`).

## TDD evidence

- **RED** (test created before diff): `jinja2.exceptions.TemplateNotFound: 'message_completeness.j2' not found in search path: '/tmp/.../src/modules/sales_agent/infrastructure/prompts/templates'` (cwd-relative path from `monkeypatch.chdir(tmp_path)`) — matches architect spike + live error. 2 failed, 1 passed (override test already green).
- **GREEN** (after diff): all 3 tests pass — templates resolve from arbitrary cwd, default dir ends with engine-package path, explicit override honored.

## Validator output (literal)

```
════════ VALIDATOR: esc5_templates_cwd_independent ════════
core/luana-core-sales-agent/tests/architecture/test_esc5_templates_cwd_independent.py::test_explicit_override_still_honored PASSED [ 33%]
core/luana-core-sales-agent/tests/architecture/test_esc5_templates_cwd_independent.py::test_default_templates_dir_is_engine_package_relative PASSED [ 66%]
core/luana-core-sales-agent/tests/architecture/test_esc5_templates_cwd_independent.py::test_templates_resolve_from_arbitrary_cwd PASSED [100%]
======================== 3 passed, 10 warnings in 2.28s ========================
```

Command (literal from 04-validators.yaml):
```
PYTHONPATH=${WS}/core/luana-core-sales-agent/src:${WS}/core/luana-core-platform/src \
  ${WS}/.venv/bin/pytest core/luana-core-sales-agent/tests/architecture/test_esc5_templates_cwd_independent.py -v -p no:cacheprovider --override-ini='addopts='
```

`ruff_check`: `All checks passed!` · `ruff_format` on base.py: `already formatted`.

## Skills consulted

- **sales-agent-expert** — §3 protected surfaces: `PromptLoader.__init__` path resolution is NOT in §3 (the protected prompt surface is `PromptVersionModel` schema, not the file loader's default dir). Anti-pattern check: no agent-behavior change (template CONTENT untouched; only WHERE the loader looks). Decided: engine-package-relative default is the multibrand-safe fix; override branch keeps back-compat for any caller passing an explicit relative dir.
- **backend-expert** (via guidelines) — `Path(__file__).resolve().parent / "templates"` is the canonical pattern for package-shipped resources (cwd-independent). NEVER `Path.cwd()` + hardcoded relative for package resources.
- **.claude/rules/tdd-mandatory.md** — RED (TemplateNotFound) before GREEN. Reproduces the live cwd-relative load failure first.

## Out-of-scope flagged (NOT fixed)

- copilot `PromptLoader` (`core/luana-core-platform/.../prompts/base.py:23`, default `"src/modules/copilot/..."` + cwd, singleton L195) = same bug-class as ESC-5. Different package, copilot wires it separately → /harness-issue (future copilot). NOT touched (forbidden_to_touch).
- Smell residual: `prompt_loader = PromptLoader()` module-level singleton (global state) — DI refactor out of scope.
