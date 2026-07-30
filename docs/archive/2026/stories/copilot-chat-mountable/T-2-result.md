# T-2 Result — migrar import-path de chat.py a get_settings() lazy (+ gran parte de T-4)

## Summary
El `/chat` del motor ahora es **brand-mountable**: importar `luana_core_copilot.api.chat` con env multibrand-only (sin POSTGRES_*/WHATSAPP_*/QDRANT_URL) NO instancia `Settings()` → no `ValidationError`. La migración se extendió más allá del import-path estricto (el builder migró también muchos consumers off-path = adelanto de T-4). Todos los paquetes tocados GREEN.

## Driver test (acceptance T-2)
`tests/test_chat_import_multibrand_env.py` — **reescrito a SUBPROCESS**: corre `import luana_core_copilot.api.chat` en un intérprete fresco con env multibrand-only. RED→GREEN. Ventaja: cero mutación de `sys.modules`/lru_caches del proceso de test → elimina la polución cruzada (la versión in-process con `del sys.modules` + reload rompía tests no relacionados por duplicate-module identity).

## Migración src (get_settings() lazy)
- `luana-core-copilot`: orchestrator/{chat,graph}, extraction_card_flow, tools/{assets_tools,awareness,extract_from_doc,extraction_tools}, infrastructure/{qdrant/marketing_kb_store,web/tavily_search}, workers/copilot_rag_eval.
- `luana-core-platform`: prompts/base, model_registry, links/ports/{calendar,channel_adapter,crm_enrichment,lead_resolution,payment_connection,scheduling,social_proof}, workers/brand_summary_regen, core/database (refinamientos shim).
- `luana-core-events`: outbox/event_bus_adapter.
- `luana-core-assets`: storage/{local,r2}.
Patrón: `from config import settings` (module-level) → `get_settings()` dentro de función. Shim back-compat de T-1 cubre lo no migrado.

## Test fixes (rotos por la migración — parcheaban globals module-level removidos)
- `test_extraction_card_idempotency`: `extraction_card_flow.redis_client` → `_get_redis_client` (return_value=None).
- `test_outbox_adapter_integration` + `test_event_bus_adapter` + `test_event_bus_adapter_infers_module`: `event_bus_adapter.settings` → `event_bus_adapter.get_settings` (lambda).
- `test_prompt_loader_resilience`: `prompts.base.SessionLocal` → `core.database.SessionLocal`.
- `conftest.py` (copilot): provee `FRONTEND_URL`+`COPILOT_TELEGRAM_BOT_USERNAME` (CI defaults — worktree fresco sin `.env`; el fragment telegram failfasta si vacíos).
- Driver reescrito a subprocess → arregló las víctimas de orden (sse_v2, channel_format, voice, streaming_timeout, telegram_webhook).

## Validators
```
copilot:  1641 passed, 25 skipped (incl. driver subprocess GREEN)
platform: 290 passed
events:   76 passed
assets:   58 passed
iam:      passed
ruff check (todos los paquetes tocados): All checks passed
```

## Pendiente (T-4 restante)
Consumers off-path que aún usan el shim deprecado (`from config import settings` / `from database import redis_client/SessionLocal`) en otros paquetes (sales_agent, connections, etc.) — emiten DeprecationWarning, funcionan. Completar en T-4 + retirar el shim.

## Notas
- `test_offer_psychology_service.py` (skipped) parchea `base.settings.PROMPT_SOURCE` (target latente roto, pero skipped → no rompe). Fixear si se un-skipea.
- `static/uploads/` artefacto de test removido (no versionado).

## Skills consulted
| Skill / Rule | Status |
|---|---|
| backend-expert | ✅ |
| copilot-expert | ✅ (orchestrator import-path) |
| .claude/rules/tdd-mandatory.md | ✅ (driver RED→GREEN) |
| .claude/rules/anti-duplication.md | ✅ (migración consolida, no mirror) |
