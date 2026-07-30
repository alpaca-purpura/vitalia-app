<!-- voseo-allowed: arquitectura interna -->
# 03-arch.md — copilot /chat brand-mountable (technical-story, approach C)

> Refactor del engine para que importar `core/luana-core-copilot/api/chat.py` NO instancie el `Settings` monolítico legacy ni el engine async/redis a import-time. Approach **C (full lazy `get_settings()`)** firmado por Chris. Build en worktree core `wip/core-copilot-mountable`.

## Surfaces involved
- BE engine refactor: `core/luana-core-platform` (root: config + database) + ~12 paquetes consumers del global `settings`. NO FE · NO agentic · NO UI · NO migrations (cero schema change).

## Prior art audit
- **Consumed via import:** ningún engine package nuevo. El fix consolida — `get_settings()` reemplaza el global `settings` ya existente (`luana_core_platform.core.config`).
- **Reused:** el patrón `@lru_cache get_settings()` es el idiom estándar pydantic-settings (no se inventa abstracción).
- **Net-new justificado:** ninguno. Es refactor in-place.
- **Anti-duplication:** el fix ELIMINA duplicación (hoy vitalia escribe sus propias rutas copilot para esquivar el legacy Settings — `vitalia/.../copilot/api/routes/wizard_onboarding_routes.py`). Post-fix las marcas montan el router del engine. NO crea mirror.

## Root cause (recon verificado)

```
importar chat.py  →  database.py (módulo) ejecuta EAGER:
   línea 22/32: engine async/sync desde settings.database_url
   líneas 45-59: redis_client = redis.from_url(settings.REDIS_URL).ping()
              →  config.py línea 317: settings = Settings()  (BaseSettings, campos legacy sin default)
                 → marca multibrand no provee POSTGRES_*/WHATSAPP_*/QDRANT_URL/... → ValidationError en import → boot crash
```

55 archivos del engine usan el global `settings` (13 paquetes). Pero **solo los del import-path transitivo de `chat.py` bloquean el mount** — el resto son off-path.

## Diseño del fix

### Pieza 1 — `config.py`: lazy + shim back-compat (semver minor)

```python
from functools import lru_cache

@lru_cache
def get_settings() -> Settings:
    return Settings()

# Shim back-compat DEPRECADO (módulo-level PEP 562) — para off-path consumers durante la transición.
def __getattr__(name: str):
    if name == "settings":
        import warnings
        warnings.warn("usá get_settings() en vez del global `settings`", DeprecationWarning, stacklevel=2)
        return get_settings()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
```

> ⚠️ **El shim NO basta para el import-path de `chat.py`.** `from ...config import settings` dispara `__getattr__('settings')` al importar el consumer → instancia `Settings` igual. Por eso los módulos **en el import-path de chat** deben pasar a `get_settings()` **llamado dentro de función** (lazy real), no `from config import settings` a nivel de módulo. El shim solo salva a los **off-path** (que se importan donde la env legacy SÍ existe, o que migran en T-2).

### Pieza 2 — `database.py`: diferir engine + redis a lazy

Los 3 inits eager a module-load se vuelven funciones `@lru_cache`:
- `_async_url`/async engine (línea 32) → `@lru_cache get_async_engine()` que llama `get_settings().database_url` dentro.
- sync engine (línea ~22) → idem `get_engine()`.
- `redis_client` (líneas 45-59) → `@lru_cache get_redis_client()` (mantiene el graceful-degrade: None si Redis caído). `rate_limit.py` consume `get_redis_client()` en vez del global `redis_client`.

Tras Pieza 1+2, **importar `database.py` no instancia nada** → `chat.py` importable con env multibrand.

### Pieza 3 — migrar el import-path transitivo de `chat.py` a `get_settings()`

El builder traza el set exacto vía el test RED (Pieza 4): `context.py`, `rate_limit.py`, `iam/api/dependencies.py`, y los módulos de `copilot.application.orchestrator.chat` (`CopilotOrchestrator`) que toquen `settings`. Regla: en el import-path, NUNCA `from config import settings` a module-level; siempre `get_settings()` dentro de función.

### Pieza 4 — completar C (end-state sin global) — los ~48 off-path

Migración mecánica de los consumers off-path restantes (`connections` 13, `copilot` resto, `sales-agent` 5, `assets` 5, `llm` 3, `campaigns` 3, `analytics` 2, `scheduling` 2, `events` 1, `brand-studio` 1, `tenant-domains` 1, `iam` resto, `platform` resto) → `get_settings()`. Al terminar, el shim queda **deprecado** (warning) o se retira. Esto es lo que vuelve C "full" (Chris).

## Estrategia TDD (RED→GREEN)

El **test de verificación-por-efecto es el driver de la Pieza 1-3**: un test que importa `chat.py` con SOLO env multibrand (monkeypatch que borra POSTGRES_*/WHATSAPP_*/QDRANT_URL, deja DATABASE_URL+LITELLM_*) y asserta que NO levanta `ValidationError`. RED al inicio → se difiere módulo por módulo hasta GREEN. El test REVELA el import-path completo (lo que falte lazy, crashea y nombra el módulo).

## Integration design (CONN)

- **Reachability path:** BE de marca → `app.include_router(chat_router)` → `/chat` SSE → `CopilotOrchestrator` (motor real). Hoy roto (import crash); post-fix, montable.
- **Consumers (≥1 real):** comunify (bloqueada, shell-organism MVP — re-mount limpio post-fix, quita el guard try/except). Próximos: vitalia/nicolify (sidebar hoy MOCK), lupulo.
- **Registration points:** el contrato = el router del engine importable + `include_router` por marca (deliverable verificable: comunify boota + monta sin guard). Doc del contrato → `docs/core-modules/luana-core-copilot.md`.
- **Home:** engine package `core/luana-core-copilot` (motor único — zona Infraestructura/motor-agentico del SYSTEM-MAP). NO crea cap user-facing (`cap_change_type: fix`).
- **Un solo engine (paradigma):** el fix REFUERZA "un solo motor montable" — mata la duplicación per-brand de rutas copilot.

## Cross-cutting
- **Tenant isolation:** sin cambio (el router ya usa `get_tenant_context`). El fix no toca queries.
- **PII:** sin cambio.
- **Semver:** `core/luana-core-platform` + `core/luana-core-copilot` bump **minor** (additive: `get_settings()` nuevo, shim preserva back-compat). breaking_change: false.
- **No standalone app:** confirmado — no existe app FastAPI del motor; los deployables son las marcas. El "fail-fast de env al boot" que se pierde con lazy NO es un riesgo (cada marca valida su propia env multibrand; no hay deployable del engine que dependa del fail-fast legacy).

## R3 downstream (obligatorio)
Suite de los paquetes tocados (al menos `platform`, `copilot`, `iam`, `connections`) + **boot + arch-suite de las 4 marcas** (vitalia/nicolify/comunify/lupulo) verde. Detalle en `04-validators.yaml`.
