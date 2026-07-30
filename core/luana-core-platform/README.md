# luana-core-platform

Foundation package for the Luana Platform monorepo.

Lifted verbatim from AISALESHT:
- `backend/src/core/` → `luana_core_platform/core/` (config, database, enums, logger, security, etc.)
- `backend/src/shared/domain/` → `luana_core_platform/domain/` (base entities, VOs, events, currency, locale, messages)
- `backend/src/shared/links/` → `luana_core_platform/links/` (cross-domain ports, schemas, service)
- `backend/src/shared/infrastructure/{files,prompts,database,external,web,models}/` → `luana_core_platform/infrastructure/`
- `backend/src/shared/workers/brand_summary_regen.py` → `luana_core_platform/workers/`
- `backend/src/shared/api/` → `luana_core_platform/api/`
- `backend/src/shared/application/{ai_action_service,brand_summary_event_handlers,field_diff,progress_emitter}.py` → `luana_core_platform/application/`

Key exports: `Base` (SQLAlchemy base), `TenantLocale`, `utc_now`, `settings` (core config), `LLMFactory` (via cyclic dep on luana-core-llm), `sanitize_payload`, `BaseExtractionOrchestrator`.

Story 2 lift — `luana-shared-lift` (T-2).
