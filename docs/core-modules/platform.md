---
package: luana-core-platform
verdict: shared-runtime-foundation
version: 0.5.1
consumers: [vitalia, nicolify, comunify, lupulo, "+ every core/* package"]
status: active
---

# luana-core-platform — public contract

Shared runtime foundation of the engine: app settings, DB/redis access, security
helpers, cross-module `links/ports/*`, base entity, prompts/model registry. Every
other `core/*` package and every brand backend transitively depends on it, so its
boot behaviour is a cross-brand invariant.

## Settings contract — lazy + multibrand-instantiable

`core/config.py` exposes the "Visionarias Brain" monolith `Settings` (pydantic-settings).
Two invariants make it safe for multibrand brands to consume core routers:

- **Import-safe (since 0.5.0):** importing any platform module **never** instantiates
  `Settings` nor builds the DB engine / Redis client at module-load. Use the lazy accessors
  — `get_settings()` (`@lru_cache`), `get_engine()` / `get_async_engine()` /
  `get_async_session_maker()` / `get_redis_client()` (all `@lru_cache`, graceful-degrade).
  A PEP 562 `__getattr__` shim keeps `from ...config import settings` working but emits a
  `DeprecationWarning` — migrate off-path callers to `get_settings()`.

- **Instantiation-safe (since 0.5.1):** `Settings()` instantiates under a **minimal multibrand
  env** (`DATABASE_URL` + `REDIS_URL` + LLM keys) — the legacy-only fields (`POSTGRES_*`,
  `WHATSAPP_*`, `QDRANT_URL`, `TRAEFIK_NETWORK`, `DOMAIN_NAME`, `API_SECRET_KEY`, `LOG_LEVEL`,
  `API_URL`, `OPENAI_API_KEY`) are optional with benign defaults. This is what lets a brand
  **exercise** (not only mount) core routers: `get_db()` → `get_settings()` → `Settings()` no
  longer raises `ValidationError` for vars the brand doesn't set.

### `settings.database_url`

Returns the canonical **sync** URL (`postgresql://`). Resolution order:

1. `DATABASE_URL` if set — normalized to the sync scheme (strip any `+driver`); async consumers
   re-add `+asyncpg` via their existing `.replace("postgresql://", "postgresql+asyncpg://")`.
   This is the canonical multibrand env (matches each brand's `backend/src/db.py` + compose).
2. else compose from `POSTGRES_*` (legacy-standalone env).
3. else raise `RuntimeError` — loud at first DB use, never a blanket import/instantiation crash.

### Point-of-use validation

Subsystems that genuinely require a now-optional field validate it **where it's used**, fail-loud,
e.g. `core/security.py::get_encryption_key()` raises if `API_SECRET_KEY` is empty (no silent weak
key). The principle: the monolith is instantiable with near-zero env; each subsystem owns its slice.

## Consumer guidance

- A new brand backend needs only its multibrand env (`DATABASE_URL`, `REDIS_URL`, LLM keys, Clerk)
  to mount + serve core routers. It does **not** need the legacy `POSTGRES_*` / `WHATSAPP_*` / … vars.
- Never re-add a module-level `settings = Settings()` or a module-level engine — use the lazy
  accessors (arch direction; the remaining off-path module-level `settings.database_url` in
  `copilot/api/_dependencies.py` + `campaigns/api/_dependencies.py` is tolerated debt, no longer a
  crash after 0.5.1, migrate to a lazy factory when touched).

## Promotion history

- `2026-06-16-copilot-chat-brand-mountable` (Settings lazy, ratified Chris · **migrated**) — 0.5.0
  lazy import-path; 0.5.1 multibrand-instantiable `Settings` + `DATABASE_URL`-first resolution.
  Same root fix unblocked both the copilot `/chat` and the iam `auth_router` mounts.

## Drill-down

- Settings: `core/luana-core-platform/src/luana_core_platform/core/config.py`
- DB/redis lazy accessors: `core/luana-core-platform/src/luana_core_platform/core/database.py`
- Security: `core/luana-core-platform/src/luana_core_platform/core/security.py`
- Tests: `tests/test_lazy_settings_no_eager.py` (import-safe) +
  `tests/test_settings_multibrand_instantiation.py` (instantiation + `database_url` resolution)
- CHANGELOG: `core/luana-core-platform/CHANGELOG.md` (0.5.0 + 0.5.1)
