<!-- voseo-allowed: contract-spec interno, no user-facing -->
# 00-contract-spec.md — copilot /chat brand-mountable (technical-story)

> El análogo del `01-spec.md` para una technical-story (no Gherkin de comportamiento, sino **contract-spec**: contrato + consumers + invariante + verificación-por-efecto). Producido por `/architect` (sombrero CTO). Approach firmado por Chris. Input del `architect-orchestrator` para el ready-package.

## Problema (root cause verificado 2026-06-16)

El router SSE `/chat` del motor (`core/luana-core-copilot/src/luana_core_copilot/api/chat.py`) **no es brand-mountable**. Importar el router arrastra, por 3 vías, la instanciación EAGER del `Settings` monolítico legacy + el engine async del platform a **import-time**:

```
chat.py importa:
  ├─ luana_core_platform.core.rate_limit  → importa .database
  ├─ luana_core_platform.core.database    → línea 32: `_async_url = settings.database_url...` (EAGER module-load)
  │                                          línea 13: from ...core.config import settings
  ├─ luana_core_platform.core.context     → (mismo paquete)
  └─ luana_core_iam.api.dependencies      → línea 12: from ...core.database import get_db (misma cadena)
       └─ luana_core_platform.core.config → línea 317: `settings = Settings()` (EAGER module-load)
            └─ Settings = BaseSettings con campos SIN default: POSTGRES_HOST/PORT/USER/PASSWORD/DB,
               WHATSAPP_API_TOKEN/PHONE_NUMBER_ID/VERIFY_TOKEN, TRAEFIK_NETWORK, DOMAIN_NAME,
               API_SECRET_KEY, QDRANT_URL  ("Visionarias Brain", pre-multimarca)
```

Las marcas multibrand se configuran con `DATABASE_URL` / `QDRANT_HOST`+`PORT` / `LITELLM_*` y **no proveen** las vars legacy → `pydantic ValidationError` en import → **boot crash del BE de la marca**.

### Hallazgos del recon (datos reales — informan el approach)

- **55 archivos del engine** importan el global `settings`; **50** lo usan por atributo (`settings.X`). → blast radius de C.
- **NO existe app standalone FastAPI del motor** (solo los tests construyen apps). El riesgo "no romper el standalone" de la proposal es **moot** — el engine se consume como librería, los deployables son las marcas.
- **Ningún código de producción monta el `/chat` hoy** (solo `core/luana-core-copilot/tests/test_rate_limit.py`). Mover el contrato no rompe consumidores vivos.
- Los **2 usos eager a module-load** en la cadena del `/chat` = `config.py:317` (`settings = Settings()`) + `database.py:32` (`_async_url`). El refactor C los elimina + migra los 55 call-sites a `get_settings()`.

## Contract-spec (4 piezas)

1. **Contrato / interface:** el `/chat` del motor importable + montable por un BE de marca multibrand **sin** instanciar el `Settings` legacy ni el engine async de `luana_core_platform.core.database` a import-time. Patrón: `get_settings()` (lazy, `@lru_cache`) reemplaza el global `settings = Settings()`; los accesos eager a module-load se difieren a primera llamada.
2. **Consumers (≥1 real — anti-isla CONN):** comunify (bloqueada hoy, shell-organism MVP) → vitalia/nicolify al cablear su sidebar Luana/Valeria al motor real (hoy MOCK) → lupulo al activarse. El fix **elimina la duplicación per-brand** del wiring del endpoint (vitalia hoy escribe sus propias rutas copilot para evitar el legacy Settings).
3. **Invariante (lo que NUNCA puede romperse):** importar cualquier módulo del engine (`chat.py`, `database.py`, `config.py`, …) **NUNCA** instancia el `Settings` monolítico ni crea el engine async a module-load. La validación de env se difiere a primera necesidad (cada deployable valida la suya).
4. **Verificación-por-efecto (NO demo, NO "GET 200"):**
   - Un BE de marca con SOLO env multibrand (`DATABASE_URL` + `LITELLM_*`, sin POSTGRES_*/WHATSAPP_*/…) **bootea** (no `pydantic ValidationError` en import).
   - El `/chat` montado en ese BE responde **401 sin auth** y **200 (stream SSE)** con auth válida — sin las vars legacy presentes.
   - **R3 downstream:** suite del engine (los 6 paquetes tocados) + boot + arch-suite de las **4 marcas** (vitalia/nicolify/comunify/lupulo) verde.

## Approach firmado (Chris 2026-06-16)

**C — full lazy refactor.** Reemplazar el global `settings` por `get_settings()` (`@lru_cache`) en los ~55 call-sites de los paquetes core afectados. End-state: sin global mutable.

- **Rechazados:** A (lazy solo en el límite del módulo — fixea root con menos churn, pero Chris quiere el end-state limpio) · B (router factory con DI — workaround que deja la deuda viva).
- **Semver minor (additive):** durante la transición se mantiene un **shim de back-compat** — `settings` como **proxy lazy deprecado** (módulo-level `__getattr__` o `LazyProxy`) — para que ningún call-site perdido rompa y el R3 valide incremental. El shim se retira cuando los 55 estén migrados (o queda deprecado un release). **Cero break** de las 4 marcas; no hay standalone que romper.
- **Cuidado clave para el orchestrator:** los usos **a module-load** (`database.py:32`, y cualquier otro `settings.X` a nivel de módulo en la cadena del `/chat`) deben diferirse a función/`@lru_cache` — migrar solo los accesos dentro-de-función NO alcanza si queda uno eager. Verificar también `rate_limit.py` (`redis_client`) por instanciación eager desde settings.

## Out of scope

- NO se construye el saga runtime ni nada de empleados-IA (ver `ADR-015` — gateado).
- NO se cablea el sidebar de ninguna marca acá (eso es story de marca post-fix: comunify T-agentic v2, vitalia/nicolify opt-in).
- NO se borran las rutas copilot propias de vitalia en esta story (cleanup posterior, opt-in).

## Referencias

- Proposal: `docs/promotion-protocol/proposals/2026-06-16-copilot-chat-brand-mountable.md` (accepted · vive en wip/comunify).
- Engine surface: `core/luana-core-copilot/src/luana_core_copilot/api/chat.py` · `core/luana-core-platform/src/luana_core_platform/core/{config,database,rate_limit,context}.py`.
- Contract a documentar al cerrar: `docs/core-modules/luana-core-copilot.md` (router brand-mountable).
- Origin blocker: `comunify/docs/product/stories/comunify-shell-organism/checkpoint.md § Blocker`.
