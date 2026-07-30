# Changelog — luana-core-platform

All notable changes to this package are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this package adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.1] — 2026-06-16

### Changed

- **Multibrand-instantiable `Settings` + `DATABASE_URL`-first DB resolution (additive,
  backward-compatible).** Completes `2026-06-16-copilot-chat-brand-mountable`: 0.5.0 made the
  *import* path lazy; 0.5.1 makes `Settings()` *instantiable* under a minimal multibrand env so
  brands can also *exercise* (not just mount) core routers (copilot `/chat`, iam `auth_router`).
  - The legacy "Visionarias Brain"-only required fields (`POSTGRES_*`, `WHATSAPP_*`, `QDRANT_URL`,
    `TRAEFIK_NETWORK`, `DOMAIN_NAME`, `API_SECRET_KEY`, `LOG_LEVEL`, `API_URL`, `OPENAI_API_KEY`,
    `REDIS_URL`) are now optional with benign defaults. Existing standalone envs that set them are
    unaffected (loosening required→optional is backward-compatible).
  - New `DATABASE_URL` field; `settings.database_url` resolves `DATABASE_URL` first (normalized to
    the sync `postgresql://` scheme — async consumers re-add `+asyncpg`), composing from
    `POSTGRES_*` only as legacy fallback, and raising a loud `RuntimeError` if neither is set
    (at point-of-use, never a blanket import/instantiation crash). Aligns the engine with each
    brand's own `db.py` (already `DATABASE_URL`-first).
  - `core/security.py::get_encryption_key()` migrated to `get_settings()` and now fails loud if
    `API_SECRET_KEY` is empty — no silent deterministic weak key under the new optional default.

## [0.5.0] — 2026-06-16

### Changed

- **Lazy settings + DB/redis init (additive, semver minor).** `core/config.py`:
  added `@lru_cache get_settings()`; the module-level `settings = Settings()` eager
  instantiation is replaced by a PEP 562 `__getattr__` back-compat shim (deprecated).
  `core/database.py`: the eager module-load engine/redis init (sync engine, async
  engine, `redis_client`) is deferred to `@lru_cache get_engine()` / `get_async_engine()`
  / `get_redis_client()` (graceful-degrade preserved). Importing any engine module no
  longer instantiates the legacy `Settings` monolith → enables brand-mountable routers.
  `prompts/base`, `model_registry`, `links/ports/*`, `workers/*` migrated to
  `get_settings()`. Proposal `2026-06-16-copilot-chat-brand-mountable` (approach C).
  No behaviour change; deployments validate their own env on first access.

## [0.4.0] — 2026-05-20

### Added

- **`luana_core_platform.workers.cron_envelope`** — `@cron_envelope(name, *, ttl, enable_otel, enable_sentry)`
  engine-grade decorator for ARQ cron job functions. Composes four cross-cutting concerns:
  1. Idempotency deduplication via `luana_core_idempotency.@idempotent` (soft-fail if package absent).
  2. OTel span via `luana.cron` tracer (graceful degrade when `opentelemetry-api` not installed).
  3. structlog audit event `cron_completed` logged on success.
  4. Sentry capture on exception (graceful degrade when `sentry-sdk` not installed).
  Promoted from `vitalia/_shared/workers/base.py::idempotent_cron` (brand-local, clinic-specific).
  Now brand-agnostic: any brand uses `@cron_envelope("{brand}.cron.{slug}")`.
  Public import: `from luana_core_platform.workers import cron_envelope`.

- **`luana_core_platform.repositories.compound_scope_repository`** — `CompoundScopeRepositoryBase[ModelT, IdT]`
  abstract async repository base class enforcing dual-scope isolation on every query:
  - `tenant_id`: root multitenant isolation (per `.claude/rules/tenant-isolation.md`)
  - `scope_id`: brand-specific secondary axis (named via `scope_field` constructor arg)
  Brand consumers set semantic names: `"clinic_id"` (vitalia), `"studio_id"` (fitflow),
  `"store_id"` (retailly), `"cohort_id"` (comunify), `"workspace_id"` (saasora), etc.
  Provides `get_by_id(*, id, tenant_id, scope_id)` and `list_for_scope(*, tenant_id, scope_id, limit, offset)`.
  All queries exclude soft-deleted rows (`deleted_at IS NULL`).
  Promoted from `vitalia/_shared/repositories/phi_repository.py::PhiRepositoryBase` (vitalia HIPAA-lite).
  Public import: `from luana_core_platform.repositories import CompoundScopeRepositoryBase`.

### Migration notes

- **Vitalia callers**: `vitalia/_shared/workers/base.py::idempotent_cron` and
  `vitalia/_shared/repositories/phi_repository.py::PhiRepositoryBase` remain in place
  for this release (backward-compatible). Phase 2 migration ticket will update the 11 brand
  callers to import from the engine and delete the brand-local originals.
  See proposal `docs/promotion-protocol/proposals/2026-05-20-core-platform-extensions-slice-1.md`.
- **New brand consumers**: import from engine directly — no brand-local copy needed.
  `from luana_core_platform.workers import cron_envelope`
  `from luana_core_platform.repositories import CompoundScopeRepositoryBase`

## [0.3.0] — 2026-05-19

### Changed

- **BREAKING semantic (engine brand-agnostic principle):** purged 4 nicolify-specific
  hardcoded defaults from `src/luana_core_platform/core/config.py`. Defaults now
  empty strings (or `localhost:4000/v1` for LITELLM) — each brand MUST override
  via `{brand}/.env.dev` / `.env.prod`. Engine no longer assumes a specific brand.
  - `COPILOT_TELEGRAM_BOT_USERNAME`: `"nicolify_copilot_bot"` → `""`
  - `FRONTEND_URL`: `"https://app.nicolify.com"` → `""`
  - `QDRANT_COLLECTION`: `"visionarias_knowledge"` → `""`
  - `QDRANT_COLLECTION_HYBRID`: `"visionarias_hybrid"` → `""`
  - `LITELLM_BASE_URL`: `"http://visionarias_litellm:4000/v1"` → `"http://localhost:4000/v1"`
    (brand-agnostic dev default — production override per-brand container name)

### Migration notes

- **Brand consumers MUST set explicit overrides** in their `{brand}/.env.dev` and
  `.env.prod`. Brand templates `{brand}/.env.dev.template` updated with the canonical
  "Brand-specific config" block. Per `_pm-brand-template/`, future brand bootstraps
  (saasora, inmoflow, retailly, fixia, guestly, fitflow) inherit the pattern from
  day 1.
- **Failfast > silent contamination.** If a brand consumer attempts to call code
  paths that need these settings (copilot Telegram deep-link, sales_agent vector
  store, LiteLLM proxy) without setting them, it will fail explicitly instead of
  silently using nicolify defaults (e.g., writing to Qdrant collection
  `visionarias_knowledge` from a vitalia tenant — gravísimo bajo HIPAA-lite).
- Promotion proposal:
  [`docs/promotion-protocol/proposals/2026-05-19-purge-nicolify-defaults-core-config.md`](../../docs/promotion-protocol/proposals/2026-05-19-purge-nicolify-defaults-core-config.md)
  (state: migrated).

### Notes

- Bump is `minor` (0.2.0 → 0.3.0) per semver-disciplinada convention even though
  semantically it's a "behavior change forcing explicit config". Justification: no
  Python API broke (Settings class signature unchanged, only default values), and
  pre-lift verification ensured all 4 active brand `.env.dev` files were
  pre-populated with explicit overrides before merge — zero runtime behavior
  regression for nicolify/vitalia/comunify/lupulo dev stacks.

## [0.2.0] — 2026-05-17

### Added

- `TenantLocationContract` Protocol in
  `src/luana_core_platform/links/ports/tenant_profile.py`. Universal columns
  brand `tenants` tables MUST implement: `is_onboarded` (bool), `location_country`
  (ISO 3166-1 alpha-2 nullable), `location_city` (str nullable), `timezone`
  (IANA TZ nullable). Enables locale-aware cron jobs, currency defaults per
  country, compliance jurisdiction resolution (HIPAA-lite PE/AR/CL/MX/CO/BR),
  and analytics regionalization. Promotion proposal:
  [`docs/promotion-protocol/proposals/2026-05-17-platform-tenants-location-columns.md`](../../docs/promotion-protocol/proposals/2026-05-17-platform-tenants-location-columns.md)
  (state: migrated).
- Contract tests at `tests/links/test_tenant_location_contract.py` (Protocol
  shape + 8 ISO country code parametrize + non-conforming fail).

### Notes

- Backward-compatible minor bump. All fields are optional via `None` defaults
  or default-safe values; existing brand `tenants` tables remain valid until
  they opt-in via local Alembic migration (`ADD COLUMN IF NOT EXISTS`).
- `docs/core-modules/platform.md` engine-docs file pending creation (deferred
  to a follow-up engine-docs cementing pass — see TODO in promotion proposal).
- Brand consumer opt-in tracking: Vitalia (origen, T-be-migration-014) opt-in
  immediate in Slice 1. Nicolify/Comunify/Lupulo opt-in incremental per story
  demand.

## [0.1.0] — 2026-05-15

### Added

- Initial extraction from `backend/src/shared/` to `core/luana-core-platform/`
  as part of multibrand reorg (Story 5+). Ports for cross-module access:
  access, advertising, analytics, brand, calendar, campaigns, channel_adapter,
  conversational_channel, crm_enrichment, crm_repos, domain_lookup,
  editable_fields, edition_landing_clone, lead_resolution, message_handler,
  offer, payment_connection, sales_agent, scheduling, social_proof,
  tenant_profile.
