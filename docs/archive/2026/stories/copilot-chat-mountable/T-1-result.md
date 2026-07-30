# T-1 Result — config.py lazy + shim back-compat + database.py engine/redis lazy

## Summary

Pieza 1 (`config.py`) and Pieza 2 (`database.py`) implemented. The validator
`v_no_eager_module_settings` (6 tests) went RED → GREEN. Full platform suite
regression: **290 passed, 0 failed**.

## Files modified

| File | Change |
|---|---|
| `core/luana-core-platform/src/luana_core_platform/core/config.py` | Added `get_settings()` @lru_cache + PEP 562 `__getattr__` shim for back-compat. Removed eager `settings = Settings()`. |
| `core/luana-core-platform/src/luana_core_platform/core/database.py` | Full rewrite: 3 eager module-load inits → `get_engine()`, `get_async_engine()`, `get_redis_client()` all @lru_cache. PEP 562 `__getattr__` shim for back-compat (engine/async_engine/async_session_maker/redis_client/SessionLocal). Graceful-degrade redis preserved inside `get_redis_client()`. |
| `core/luana-core-platform/src/luana_core_platform/core/rate_limit.py` | `from .database import redis_client` → `from .database import get_redis_client`. All usages of `redis_client` in the function body → `rc = get_redis_client()`. |
| `core/luana-core-platform/tests/test_lazy_settings_no_eager.py` | **NEW** — 6 tests (RED→GREEN): config import does not call Settings.__init__, cache currsize==0 after import, database import does not call create_engine/create_async_engine/redis.from_url, lazy functions exported, get_settings has lru_cache interface, shim emits DeprecationWarning. |
| `core/luana-core-platform/tests/conftest.py` | `_force_prompt_source_file` fixture: `settings` → `get_settings()` to avoid shim path in autouse fixture. |
| `core/luana-core-platform/tests/test_legacy_event_bus_deprecation_warning.py` | Updated 4 tests: `monkeypatch.setattr("...config.settings.X", ...)` → `monkeypatch.setattr(get_settings(), "X", ...)` to avoid shim triggering inside `warnings.catch_warnings`. Filter assertions to only check `EventBus.publish` warnings (not T-1 migration shim warnings). |

## Validator output

```
v_no_eager_module_settings: 6/6 PASS (RED against original code → GREEN after fix)
be_platform_unit: 290 passed, 0 failed (regression guard GREEN)
ruff check (touched files): All checks passed
ruff format --check (touched files): All checks passed
```

## RED→GREEN evidence

Before implementation:
```
FAILED test_import_database_does_not_create_engine_or_redis
AssertionError: database.py called ['create_engine', 'create_async_engine', 'redis.from_url']
at module-load time.
```

After implementation:
```
290 passed, 21 warnings in 1.78s
```

## Invariant verified

Importing `luana_core_platform.core.config` or `luana_core_platform.core.database` does NOT:
- Instantiate `Settings` (or any `BaseSettings` subclass)
- Call `create_engine` / `create_async_engine`
- Call `redis.from_url`

All deferred to first call of `get_settings()` / `get_engine()` / `get_async_engine()` / `get_redis_client()`.

## Back-compat shim behaviour

- `from luana_core_platform.core.config import settings` → works + emits `DeprecationWarning`
- `from luana_core_platform.core.database import redis_client` → works + emits `DeprecationWarning`
- `from luana_core_platform.core.database import engine` → works + emits `DeprecationWarning`
- These are T-4 migration targets (off-path consumers). The shim keeps semver-minor back-compat.

## Skills consulted

| Skill | Purpose | Decision |
|---|---|---|
| `backend-expert` | DDD patterns, @lru_cache singleton, graceful-degrade redis pattern | Used PEP 562 `__getattr__` for module-level shim; `@lru_cache` for lazy singleton; graceful-degrade preserved in `get_redis_client()` |
| `.claude/rules/tdd-mandatory.md` | RED test BEFORE implementation | Wrote 6 RED tests first (`test_lazy_settings_no_eager.py`); ran them against original eager code to confirm RED; implemented Pieza 1+2; confirmed GREEN |
| `.claude/rules/anti-duplication.md` | No mirror, extend existing | Fix consolidates (eliminates per-brand workaround for copilot routes); no new abstraction; `get_settings()` is the pydantic-settings standard idiom |
| `.claude/rules/backend-ddd.md` | DDD layer purity; no framework imports at domain level | Config/database are infra; pattern compliant; no cross-module import violations introduced |

## Commit SHA

`bb8e34f8` — wip/core-copilot-mountable
