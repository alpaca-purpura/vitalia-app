# Changelog — luana-core-copilot

All notable changes to this package are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this package adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] — 2026-06-16

### Changed

- **`/chat` brand-mountable (additive, semver minor).** Migrated the copilot
  orchestrator + tools import-path from the module-level `luana_core_platform.core.config.settings`
  global to lazy `get_settings()` inside functions, so importing
  `luana_core_copilot.api.chat` no longer instantiates the legacy "Visionarias Brain"
  `Settings` monolith at import-time. A brand backend with only multibrand env
  (`DATABASE_URL` / `LITELLM_*`) can now mount the engine `/chat` router without the
  legacy `POSTGRES_*`/`WHATSAPP_*`/`QDRANT_URL` vars. Proposal
  `2026-06-16-copilot-chat-brand-mountable` (approach C, ratified Chris). Back-compat
  shim preserves the deprecated `settings` global during transition. No behaviour change.

## [0.2.0] — 2026-05-19

### Changed

- **BREAKING semantic (engine brand-agnostic principle):** purged 3 residual
  nicolify-specific hardcodes from copilot orchestrator + tools. Continuation
  of cement work started by `luana-core-platform` 0.3.0 (proposal
  [2026-05-19-purge-nicolify-defaults-core-config](../../docs/promotion-protocol/proposals/2026-05-19-purge-nicolify-defaults-core-config.md))
  and `luana-core-sales-agent` 0.2.0 (proposal
  [2026-05-19-purge-nicolify-hardcodes-sales-agent](../../docs/promotion-protocol/proposals/2026-05-19-purge-nicolify-hardcodes-sales-agent.md)
  broadened scope).

#### `src/luana_core_copilot/application/orchestrator/graph.py`

- Renamed `_TELEGRAM_CHANNEL_CONTEXT_ES` constant to
  `_TELEGRAM_CHANNEL_CONTEXT_ES_TEMPLATE` and changed semantics from
  module-load constant to lazy-built per-engine-instance result.
- Replaced 3 nicolify-specific literal strings inside the cacheable
  Telegram channel context prompt with brand-resolved markers:
  - `@nicolify_copilot_bot` → `@__TELEGRAM_BOT__` (line 699)
  - `app.nicolify.com/{tenant_slug}/{ruta}` → `__FRONTEND_DOMAIN__/{tenant_slug}/{ruta}` (lines 709 + 798)
- Added module-level `_get_telegram_channel_context_es()` helper that:
  - Lazy-builds the cached string at first telegram-channel invocation
  - Resolves markers from `settings.COPILOT_TELEGRAM_BOT_USERNAME` +
    `settings.FRONTEND_URL` (with protocol stripped to leave domain only)
  - Raises `RuntimeError` failfast if either setting is empty (per
    proposal padre principle: failfast > silent leak to nicolify defaults)
  - Returns cached result for subsequent calls (preserves Anthropic /
    Kimi prompt cache hit invariant — string stable per engine instance)
- Updated single caller (line 913 area, `build_channel_context_es()`) to
  invoke the new helper instead of the const.

**Cache invariant preserved:** the Telegram context still clears the
≥2048 Anthropic Sonnet floor / ≥1024 Kimi K2.6 floor. The cached string
is **identical bytes** for every call within the same engine instance,
so prompt prefix cache hits at the same rate as before. Each brand
engine instance has its own cache key (different bot username +
frontend domain), which is correct cross-brand isolation.

**Behavioral verify pre-merge:**
- nicolify (FRONTEND_URL=`https://app.nicolify.com`, BOT=`nicolify_copilot_bot`):
  template resolves to `app.nicolify.com/{tenant_slug}/{ruta}` +
  `@nicolify_copilot_bot` → **identical** to pre-lift hardcoded output
  → **ZERO REGRESSION** in nicolify LLM behavior.
- vitalia (FRONTEND_URL=`https://dev-app.vitalialat.com`, BOT=`vitalia_copilot_bot`):
  template resolves to `dev-app.vitalialat.com/{tenant_slug}/{ruta}` +
  `@vitalia_copilot_bot` → vitalia agent now correctly redirects users
  to vitalia FE (previously would have wrongly said "vayan a
  app.nicolify.com" — gravísimo UX bug + potential data leak).

#### `src/luana_core_copilot/application/tools/telegram_redirect.py`

- Updated `build_redirect_url()` docstring example to include both
  nicolify (legacy) and vitalia (new brand) URL outputs, clarifying
  the function is brand-agnostic and reads from `settings.FRONTEND_URL`
  at runtime (no code change — function already brand-agnostic since
  pre-lift, only docstring example was nicolify-only).

### Migration notes

- **Brand consumers MUST have both `FRONTEND_URL` and
  `COPILOT_TELEGRAM_BOT_USERNAME` set** in their `{brand}/.env.dev` /
  `.env.prod`. Already enforced by proposal padre `luana-core-platform`
  0.3.0 — this lift adds the requirement at copilot Telegram channel
  context build time. Any brand engine that processes Telegram channel
  turns will now failfast at first call if either setting is empty
  instead of silently leaking nicolify defaults into prompts.
- **LLM eval risk assessment:** the prompt text changes are purely
  substitutions of brand-specific values that were previously hardcoded
  nicolify. For nicolify (the only brand actively running copilot
  Telegram), the resulting prompt is BYTE-IDENTICAL to pre-lift.
  Therefore eval golden comparisons for nicolify should remain stable.
  For new brands (vitalia, comunify, lupulo) the prompt will contain
  their respective brand values, requiring brand-specific eval goldens
  when those brands activate copilot Telegram (separate brand stories,
  not in scope of this engine-level lift).

### Notes

- Bump is `minor` (0.1.0 → 0.2.0) — first CHANGELOG entry for
  `luana-core-copilot`. Initial 0.1.0 release (carve-out 2026-05-15
  from `backend/src/modules/copilot/`) was not formally changelogged;
  this entry establishes the cadence.

## [0.1.0] — 2026-05-15

### Added

- Initial extraction from `backend/src/modules/copilot/` to
  `core/luana-core-copilot/` as part of multibrand reorg (Story 5+).
  Establishes engine package for copilot with brand-extension surface
  in `{brand}/backend/src/modules/{brand}/copilot/{extractors,tools,workflows,kb}/`
  (per CLAUDE.md ENGINE + BRAND-EXTENSION verdict).
