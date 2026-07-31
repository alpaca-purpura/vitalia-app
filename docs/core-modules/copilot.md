---
package: luana-core-copilot
verdict: brand-mountable-router
version: 0.3.0
eps: [EP-4, EP-7, EP-14]
consumers: [comunify, vitalia, nicolify, lupulo]
status: active
---

# luana-core-copilot — public contract

Shared **copilot engine** (internal-audience agent — Plano 3 trabajador supervisado, zona
Infraestructura/motor-agentico del SYSTEM-MAP). A brand backend mounts the engine's `/chat`
SSE router instead of re-writing its own copilot routes.

## Contrato público — `/chat` brand-mountable (since 0.3.0)

```python
from luana_core_copilot.api.chat import router as chat_router

app.include_router(chat_router, prefix="/api/copilot")   # the brand chooses the prefix
```

- `router` is a bare `APIRouter()` — SSE streaming `/chat` → `CopilotOrchestrator` (the real engine).
- **Invariante de import (since 0.3.0):** importing `luana_core_copilot.api.chat` (and its
  transitive import-path: `luana_core_platform.core.{config,database,rate_limit,context}`,
  `luana_core_iam.api.dependencies`) **NEVER** instantiates the legacy "Visionarias Brain"
  `Settings` monolith nor creates the async DB engine / Redis client at import-time.
- **Invariante de ejecución (since platform 0.5.1):** the monolith `Settings` is also
  *instantiable* under multibrand env, so a brand backend with **only** `DATABASE_URL` +
  `REDIS_URL` + LLM keys not only mounts but **serves** the router (`get_db()` →
  `get_settings()` → `Settings()` no longer raises for the absent `POSTGRES_*` / `WHATSAPP_*` /
  `QDRANT_URL` / `TRAEFIK_NETWORK` vars). `settings.database_url` resolves `DATABASE_URL` first
  (normalized to the sync scheme), composing from `POSTGRES_*` only as legacy fallback.
- Each deployable validates its own env: subsystems that genuinely need a legacy field fail
  **loud at point-of-use** (e.g. engine encryption requires `API_SECRET_KEY`), never as a blanket
  crash. Auth: `/chat` returns 401 without auth, 200 SSE stream with valid auth.

This **eliminates the per-brand duplication** of copilot routes (brands used to hand-write their
own copilot routes to dodge the eager legacy `Settings`). One engine, one mount — `anti-duplication.md`.

## Dependency

- `luana-core-platform >= 0.5.1` — provides `get_settings()` (lazy `@lru_cache`) + the lazy
  `get_engine()` / `get_async_engine()` / `get_redis_client()` accessors (import-safe, 0.5.0) +
  the multibrand-instantiable `Settings` with `DATABASE_URL`-first resolution (exercise-safe,
  0.5.1). See `docs/core-modules/platform.md` + that package's CHANGELOG.

## Extension points

- **EP-4 / EP-7 / EP-14** — copilot brand extensions (tools, workflows, channels) registered via
  the Extension SDK. A brand extends `{brand}/backend/src/modules/{brand}/copilot/` (never mirrors
  the engine; engine edits go via `/pm-vitalia` flujo engine — arch tests como gate).

## Brands consumidoras

| Brand | `/chat` mount | Estado |
|---|---|---|
| comunify | re-mount limpio (quita el guard try/except) | desbloqueado post-fix (story comunify-shell-organism T-agentic v2) |
| vitalia | sidebar Valeria → motor real | opt-in (hoy MOCK; cleanup de rutas copilot propias = posterior) |
| nicolify | sidebar Luana → motor real | opt-in (hoy MOCK) |
| lupulo | — | al activarse (placeholder) |

## Promotion history

- `2026-06-16-copilot-chat-brand-mountable` (Settings lazy, ratified Chris · **migrated**) — two
  platform releases: (0.5.0) lazy `get_settings()` import-path migration so the `/chat` router is
  brand-mountable with multibrand env; (0.5.1) `Settings` multibrand-*instantiable* +
  `DATABASE_URL`-first resolution so the router also *serves* (exercise-safe), covering the 2nd
  consumer (iam `auth_router`) by the same root fix. T-4 (retirar shim, end-state sin global)
  deferido a story follow-up.

## Drill-down

- Router: `core/luana-core-copilot/src/luana_core_copilot/api/chat.py`
- Lazy settings (dep): `core/luana-core-platform/src/luana_core_platform/core/{config,database}.py`
- Tests: `core/luana-core-copilot/tests/test_chat_import_multibrand_env.py` (driver subprocess) +
  `core/luana-core-platform/tests/test_lazy_settings_no_eager.py`
- CHANGELOG: `core/luana-core-copilot/CHANGELOG.md` (0.3.0)
