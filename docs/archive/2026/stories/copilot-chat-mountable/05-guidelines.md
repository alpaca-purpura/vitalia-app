<!-- voseo-allowed -->
# 05-guidelines.md — copilot-chat-mountable

## Patterns required
- `@lru_cache def get_settings() -> Settings` como ÚNICA forma de obtener config. Llamarlo **dentro de función**, nunca a module-level.
- Inits costosos (engine async/sync, redis client) → funciones `@lru_cache` (`get_async_engine`, `get_redis_client`), nunca a module-load.
- Mantener el graceful-degrade de redis (None si Redis caído) dentro de `get_redis_client()`.
- Shim `__getattr__('settings')` con `DeprecationWarning` — solo como red de back-compat para off-path; NO usarlo en código nuevo.
- TDD: el test de verificación-por-efecto (`v_chat_import_multibrand_env`) se escribe RED **primero**; se difiere módulo por módulo hasta GREEN.
- semver minor + CHANGELOG por paquete bumpeado.

## Patterns forbidden
- `from luana_core_platform.core.config import settings` a module-level en CUALQUIER módulo del import-path de chat.py.
- `settings.X` / `Settings()` a module-load (eager). Cero excepciones en el hot-path.
- Re-instanciar `Settings()` fuera de `get_settings()` (rompe el `@lru_cache` singleton).
- Romper/retirar el shim ANTES de migrar todos los off-path (rompería semver minor).
- Tocar FE, runtime agentic, queries (tenant isolation), o migrations (no hay schema change).
- Editar código de las 4 marcas salvo que el R3 (T-5) revele un bug → entonces el fix vuelve a T-1..T-4 (core), no parche en la marca.

## Files in scope (builder edita SOLO core/)
- core/luana-core-platform/src/luana_core_platform/core/{config,database,rate_limit,context}.py
- core/luana-core-platform/tests/test_lazy_settings_no_eager.py (NEW)
- core/luana-core-copilot/src/luana_core_copilot/api/chat.py + import-path del orquestador
- core/luana-core-copilot/tests/{test_chat_import_multibrand_env,test_chat_mounted_brand_401_200}.py (NEW)
- core/luana-core-{connections,sales-agent,assets,llm,campaigns,analytics-engine,scheduling,events,brand-studio,tenant-domains,iam}/src/** (T-4 migración off-path)
- core/luana-core-{copilot,platform}/{pyproject.toml,CHANGELOG.md} (semver bump)
- docs/core-modules/luana-core-copilot.md (contrato router brand-mountable)

## Files NEVER touch
- {brand}/frontend/** · {brand}/backend/src/** (salvo verificar boot en T-5, sin editar)
- Runtime agentic (tools/workflows/personas/goldens) de copilot/sales_agent
- Otras stories / .claude/**

## must_load_skills (builder cita "Skills consulted" en T-{n}-result.md)
required:
  - id: backend-expert
    purpose: "DDD, arch fitness, patrones engine"
  - id: copilot-expert
    when: "T-2/T-3 (import-path del orquestador copilot)"
  - id: .claude/rules/tdd-mandatory.md
    purpose: "RED→GREEN del test de efecto primero"
  - id: .claude/rules/anti-duplication.md
    purpose: "el fix consolida, no mirrorea"
  - id: .claude/rules/auditor-downstream-regression.md
    when: "T-5 (R3 4 marcas)"
  - id: playwright-expert
    when: "T-5 si el 401/200 se ejerce por HTTP real"
reference_artifacts:
  - "00-contract-spec.md (root cause + approach C + verificación-por-efecto)"
  - "03-arch.md (plan de refactor + shim + import-path)"
  - "04-validators.yaml (gates + R3)"
