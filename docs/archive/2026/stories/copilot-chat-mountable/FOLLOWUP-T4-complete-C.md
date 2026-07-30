# Follow-up — completar approach C (retirar el shim)

> Deferido por decisión de Chris (G, 2026-06-16): la story `copilot-chat-mountable` shipea el **unblock** (T-1/T-2/T-3); completar el end-state "sin global mutable" es trabajo mecánico grande sin valor funcional nuevo (el shim deprecado funciona). Esto queda como **story follow-up** para cuando convenga. Owner futuro: `/pm-luana` (es engine/core).

## Qué falta (scope T-4)

Migrar de `from luana_core_platform.core.config import settings` (global, vía shim deprecado) a `get_settings()` lazy + de los shims de `database` (`redis_client`/`SessionLocal`/`engine`) a los accessors lazy, en los consumers **off-path** restantes, y luego **retirar el shim back-compat** de `config.py` + `database.py`.

**Inventario (medido 2026-06-16, post T-2):**
- `settings` global: **~47 archivos** en 12 paquetes — connections 13 · copilot 9 · sales-agent 5 · assets 3 · campaigns 3 · llm 3 · platform 3 · analytics-engine 2 · iam 2 · scheduling 2 · brand-studio 1 · tenant-domains 1.
- `database` shim (`redis_client`/`SessionLocal`/`engine`): **~61 archivos**.

## Cómo (patrón probado en T-2)

1. Migrar cada módulo: `from config import settings` (module-level) → `get_settings()` dentro de función. Idem `from database import redis_client/SessionLocal` → `get_redis_client()`/accessor lazy.
2. **Arreglar los test-mocks que se rompen** (el whack-a-mole de T-2): tests que parchean `<module>.settings` / `<module>.redis_client` / `base.SessionLocal` → apuntar al accessor (`<module>.get_settings` con `lambda: MagicMock(...)`, `core.database.SessionLocal`, etc.). Tests que setean env + reload → subprocess o cache_clear.
3. Retirar el shim `__getattr__('settings')` de `config.py` + los shims de `database.py` cuando no queden consumers.
4. R3: suite de cada paquete tocado + boot de las 4 marcas.

## Verificación de cierre
`grep -rln "from luana_core_platform.core.config import settings\b" core/*/src --include="*.py" | grep -v config.py` → 0. Idem database shims. Suites GREEN. Shim removido.

## Por qué es seguro deferir
El shim emite `DeprecationWarning` pero funciona idéntico al global anterior. El unblock (montar el `/chat` con env multibrand) NO depende de esta migración — depende solo del import-path de chat, ya migrado (T-2). Las 4 marcas importan limpio hoy (R3-light verde).
