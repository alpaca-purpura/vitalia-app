---
proposal_id: 2026-06-16-copilot-chat-brand-mountable
state: migrated                # ★ lift completo 2026-06-16 — Settings lazy (0.5.0) + multibrand-instantiable (0.5.1)
opened_date: 2026-06-16
opened_by: /pm-luana
ratified_by: Chris             # eligió dirección B (AskUserQuestion 2026-06-16)
ratified_date: 2026-06-16
migrated_date: 2026-06-16
migrated_commits:
  - "e9f16d06 — Settings lazy get_settings() (platform 0.5.0 + copilot 0.3.0), import-path migration"
  - "wip/vitalia (settings 0.5.1) — Settings multibrand-instantiable + DATABASE_URL-first resolution + security fail-loud; closes the exercise-safe invariant (2nd consumer iam covered by same root)"

# Origen (engine-fix, no lift de brand — el patrón nace de un blocker live)
origin_learnings:
  - comunify/docs/product/stories/comunify-shell-organism/checkpoint.md  # § Blocker (root cause anclado)
origin_brands: [comunify]      # 1er brand que intentó cablear el sidebar al motor copilot

# Target
target_package: core/luana-core-copilot
target_module: src/luana_core_copilot/api/chat.py  # + core/luana-core-platform/src/luana_core_platform/core/{config,rate_limit}.py (eager Settings)
target_ep: null

# Impact assessment
semver_bump: minor             # additive: nuevo router brand-mountable / Settings lazy; el path standalone del engine se preserva
breaking_change: false         # OBJETIVO: cero break del app standalone del engine + cero break de los 4 brands
brands_affected_consumers: [comunify, vitalia, nicolify, lupulo]  # todos los que quieran sidebar Luana cableado al motor
brands_at_risk_regression: [vitalia, nicolify, comunify, lupulo]  # luana_core_platform.Settings lo consume TODO → R3 obligatorio en los 4

# Lift plan
lift_estimated_effort: "1-2 days (engine refactor + downstream regression 4 brands + engine app)"
lift_owner: /dev-team (post /architect design · core worktree)
arch_test_downstream_required: true
migration_notes_required: false
---

> **★ SCOPE EXPANDIDO (2026-06-16, ratificado Chris):** la causa raíz NO es del router copilot — es **`luana_core_platform.core.config.settings` instanciado EAGER** y consumido por todo módulo core que toca DB (`luana_core_platform.core.{database,rate_limit}`). Un SEGUNDO consumer independiente lo confirmó: montar el **router iam del engine** (`luana_core_iam.api.routers.auth_router` vía `get_db`) en comunify rompe el boot por la MISMA razón (el `Settings` exige 15 campos legacy — POSTGRES_*/QDRANT/WHATSAPP/TRAEFIK/DOMAIN/API_SECRET — y arma su `database_url` de `POSTGRES_*`, ignorando el `DATABASE_URL` multibrand de la marca). Por eso el approach correcto es **#1 Settings lazy** (abajo), que desbloquea a TODOS los routers core brand-mountables (copilot `/chat` **e** iam **y** cualquier consumer de `get_db`), NO el **#2 chat-router factory** (que arregla solo el chat y deja iam roto). Evidencia iam: [[comunify-shell-organism]] § Option-2 login→tenant + checkpoint § Blocker login-redirect. Ver § 3bis.

## 1. Patrón a promover (engine FIX — no lift de brand)

El motor copilot (`core/luana-core-copilot`) expone un endpoint SSE `/chat` (`api/chat.py`) que **no es brand-mountable**: importar su `router` arrastra, vía `luana_core_platform.core.rate_limit`, la **instanciación EAGER (a import-time) del Settings monolítico legacy** `luana_core_platform.core.config.Settings` ("Visionarias Brain", pre-multibrand). Ese Settings exige `POSTGRES_HOST/PORT/USER/PASSWORD/DB`, `WHATSAPP_API_TOKEN/PHONE_NUMBER_ID/VERIFY_TOKEN`, `TRAEFIK_NETWORK`, `DOMAIN_NAME`, `API_SECRET_KEY`, `QDRANT_URL`. Los brands multibrand se configuran con `DATABASE_URL` / `QDRANT_HOST`+`PORT` / `LITELLM_*` y **no proveen** esas vars → `pydantic ValidationError` en el boot del app del brand.

**Objetivo:** que cualquier brand pueda montar el `/chat` del motor usando **su propia config multibrand**, sin arrastrar el Settings legacy a import-time.

**Origen story/incident:**
- comunify: [[comunify-shell-organism]] T-agentic — el thin-mount del `/chat` bricó el BE comunify (health 000). Lo cazó la live-verify del DoD #37 (los 312 tests nativos pasaban — verde ≠ booteable). Mitigado con un guard try/except en `comunify/backend/src/main.py` (endpoint 404, BE booteable). Root cause verbatim + logs: `comunify/docs/product/stories/comunify-shell-organism/checkpoint.md § Blocker`.

## 2. Por qué cross-brand

Cablear el sidebar (Luana/Valeria supervisora) al motor copilot real es **net-new en TODAS las marcas** (vitalia y nicolify tienen el chat-store MOCK; ninguna cableó el sidebar al `/chat`). El primer brand que lo intenta (comunify) choca con el límite del engine. Resolverlo en el engine desbloquea a las 4.

| Brand | Aplicabilidad | Razón |
|---|---|---|
| comunify | bloqueada hoy | 1er consumer del `/chat` real (shell-organism MVP) |
| vitalia | consumer próximo | sidebar Valeria hoy MOCK; querrá el motor real |
| nicolify | consumer próximo | sidebar Luana 100% MOCK |
| lupulo | futuro | hereda al activarse |

> **Patrón establecido hoy (anti-duplicación):** vitalia NO monta el `/chat` del engine — escribe sus **propias** rutas copilot (`vitalia/backend/src/modules/vitalia/copilot/api/routes/wizard_onboarding_routes.py`) usando el orquestador del engine. Eso evita el Settings legacy pero **duplica** el wiring del endpoint en cada brand. Este fix elimina la duplicación: un router del motor montable con la config del brand.

## 3. Análisis técnico

### Causa raíz (verificada)

```
brand/main.py
  → from luana_core_copilot.api.chat import router
      → chat.py importa luana_core_platform.core.rate_limit (+ .database, .context)
          → rate_limit.py instancia EAGER el Settings global (luana_core_platform.core.config.Settings)
              → BaseSettings con campos sin default (POSTGRES_*, WHATSAPP_*, TRAEFIK_NETWORK, ...)
                  → el brand no los provee → pydantic ValidationError en import → boot crash
```

### 3bis. Segundo consumer (iam) — por qué el fix es del platform, no del chat

comunify quiso cablear el **login → tenant** real (root `/` resuelve el tenant del usuario vía `GET /api/v1/iam/users/me/tenants`, patrón vitalia/nicolify). Eso exige montar `luana_core_iam.api.routers.auth_router` en el BE de la marca. Ese router usa `luana_core_platform.core.database.get_db` → que importa `luana_core_platform.core.config.settings` (EAGER) → mismo `ValidationError`/crash que el `/chat`. Es decir: **dos routers core distintos (copilot, iam), una sola causa raíz** (el `settings` global eager del platform). vitalia monta ambos solo porque su env trae los **15** campos legacy completos; las marcas multibrand limpias (comunify: `DATABASE_URL`+`REDIS_URL`+`OPENAI_API_KEY`) no.

Corolario de diseño: el **factory por-router (#2)** NO escala — habría que factorizar `chat`, `iam`, y cada futuro router core uno por uno. El **Settings lazy (#1)** ataca la raíz una vez y los libera a todos.

### Opciones a evaluar en /architect (engine-scoped)

1. **Settings lazy (★ DIRECCIÓN RATIFICADA 2026-06-16)** — diferir la instanciación de `luana_core_platform.core.config.Settings` (no a import-time de `rate_limit`/`database`/`config`; usar `@lru_cache get_settings()` invocado dentro de las funciones, no en el módulo). Desbloquea **todos** los routers core brand-mountables (chat + iam + futuros) de un saque. Riesgo: muchos módulos del engine asumen el `settings` global eager → `/architect` mapea el blast-radius + R3 4 brands + app standalone. Es el approach que cubre el 2º consumer (iam) sin trabajo extra.
2. **Chat-router factory** — `create_chat_router(*, get_db, rate_limiter, ...)` por DI. **Descartado como solución general** (§3bis): arregla solo el chat, deja iam y cada router futuro rotos. Solo viable si además se hace lazy o factory para iam por separado (más superficie, no escala).

`/architect` (WT5 technical-story lane, **worktree core efímero** — NO desde el hub de una marca) decide el detalle del approach #1 + el contract-spec (interface + consumers {copilot chat, iam} + invariante + verificación-por-efecto = ambos routers montados en una marca multibrand bootean + responden 401/200 sin la env legacy) + el semver. Chris ve la blast-radius del cambio a `luana_core_platform` antes de commitear core.

### Risk assessment

| Riesgo | Severidad | Mitigación |
|---|---|---|
| `luana_core_platform.Settings` lo consume el app standalone del engine + otros módulos core | **Alta** | R3 downstream: correr la suite del engine + los 4 brands; el app standalone del engine NO debe romperse (su env legacy sigue válido) |
| Settings lazy cambia orden de validación de env (fail-fast perdido) | Media | Mantener un check de arranque explícito en el app standalone; el brand valida su propia env |
| Bump minor + brand existente no opt-in | Baja | comunify es el único consumer activo; vitalia/nicolify opt-in cuando cableen su sidebar |

## 4. Lift plan

### Pre-lift checklist (lo cierra /architect + /dev-team)
- [ ] /architect produce el ready package engine-scoped (contract-spec + 03-arch + 04-validators + 06-tickets) en una **platform/technical-story**.
- [ ] Approach ratificado (lazy vs factory) — Chris ve la blast-radius del cambio a `luana_core_platform` antes de commitear core.
- [ ] Tests engine + R3 downstream (4 brands + app standalone del engine).
- [ ] `docs/core-modules/luana-core-copilot.md` documenta el contract del router brand-mountable.

### Lift execution
- **Worktree core efímero** (`wip/core-copilot-mountable`) por parallel-safety (no editar core desde el hub de comunify).
- Engine change (Settings lazy / factory) + bump `core/luana-core-copilot` (+ `core/luana-core-platform` si toca) minor + CHANGELOG.
- R3 arch test downstream en los 4 brands + el app standalone del engine.

### Post-lift
- comunify: T-agentic **v2** — re-mount limpio del router copilot brand-mountable (quita el guard) → desbloquea `comunify-shell-organism` → T-e2e + DoD #37 + auditor + merge.
- comunify: **iam-adoption** (login→tenant real, Option 2) — ahora desbloqueado por el mismo fix: montar `auth_router` iam con la config multibrand + migración iam idempotente (mirror vitalia 022: `tenants`/`users`/`user_tenants`) + seed tenant comunify + bind usuario + FE (`lib/iam/api.ts` + root `page.tsx` resolver). Mientras B no aterrice, el login queda con redirect provisional (Opción 1 force-redirect al slug demo) o dead-end.
- vitalia/nicolify: opt-in al cablear su sidebar (reemplazan su MOCK por el chat-store real, ver lift candidate `chat-store` de comunify).

## 5. Decisión

**Recomendación `/pm-luana`:** **APPROVED** (dirección B). Es la deuda real del engine; resolverla desbloquea a todas las marcas y elimina la duplicación per-brand del wiring del endpoint. La opción C (proveer env legacy a cada brand) se **rechaza** (acopla los brands al config "Visionarias Brain", anti-multibrand). La opción A (re-architect per-brand al patrón vitalia) resuelve comunify pero deja la deuda viva (cada brand re-duplica) — por eso Chris eligió B.

**Ratificación Chris:** ✅ **dirección B ratificada** (2026-06-16, AskUserQuestion). El **approach técnico concreto** (lazy vs factory) + el **semver** quedan pendientes de la design de `/architect` y una ratificación final antes de commitear código a `core/`.

## 6. Bitácora
- 2026-06-16: opened by /pm-luana (engine-fix desde blocker live comunify-shell-organism).
- 2026-06-16: Chris ratifica dirección B (AskUserQuestion) → state: accepted. Approach concreto → /architect.
- 2026-06-16 (tarde): **scope expandido** (Chris, AskUserQuestion "expandir proposal B / engine lazy"). 2º consumer descubierto en vivo: el router **iam** (`auth_router` vía `get_db`) choca con la MISMA raíz al intentar el login→tenant real de comunify (Option 2). Confirma que la causa es el `settings` eager de `luana_core_platform`, no el chat → **approach #1 (Settings lazy) queda como dirección ratificada** (cubre chat + iam + futuros); #2 factory descartado como solución general (§3bis). `brands_affected_consumers` sin cambio (los 4). Próximo paso sin cambio: `/architect` engine-scoped en worktree core efímero.
- 2026-06-16 (noche): **lift completo → state accepted → migrated.** Ejecutado en dos releases del platform:
  - **0.5.0 (`e9f16d06`)** — lazy `get_settings()` + lazy DB/redis accessors; el **import-path** de `chat.py` deja de instanciar el `Settings` monolítico (invariante de import).
  - **0.5.1 (wip/vitalia)** — `Settings` **multibrand-instanciable** (campos legacy `POSTGRES_*`/`WHATSAPP_*`/`QDRANT_URL`/`TRAEFIK_NETWORK`/`DOMAIN_NAME`/`API_SECRET_KEY`/`LOG_LEVEL`/`API_URL`/`OPENAI_API_KEY`/`REDIS_URL` → opcionales con default benigno) + nuevo `DATABASE_URL` con resolución **DATABASE_URL-first** (normalizada al esquema sync) y fallback `POSTGRES_*` (raise loud si ninguno). Cierra la **invariante de ejecución** (la 0.5.0 sólo cubría *montar*; faltaba *servir* — `get_db`→`Settings()` seguía crasheando bajo env multibrand). `security.get_encryption_key()` migrado a `get_settings()` + fail-loud si `API_SECRET_KEY` vacío (sin clave débil silenciosa). 2º consumer (iam `auth_router`) cubierto por la MISMA raíz, sin trabajo extra. Tests: `test_settings_multibrand_instantiation.py` (4) + suite platform verde (~294, sin regresión). **Decisión de approach concreto:** lazy puro **+ DATABASE_URL-first** (la proposal lo dejaba abierto a `/architect`; resuelto así porque "montar sin env legacy" no alcanza — el `200` real necesita resolver la DB del brand). **Decisión de worktree:** sin worktree core efímero; el lift viajó en `wip/vitalia` (SCOPE_GATE_SKIP, decisión Chris 2026-06-16), validado vía `PYTHONPATH` override (el `.venv` editable apunta a la copia del worktree main).
  - **Docs:** `docs/core-modules/platform.md` (creado, contract del settings lazy + database_url) + `docs/core-modules/copilot.md` (invariante de ejecución + dep `>= 0.5.1`).
  - **Pendiente downstream (NO bloquea el migrated del engine):** comunify-adoption (otra sesión, hub comunify) = quitar el guard try/except del mount copilot + montar iam `auth_router` + migración iam + seed tenant. R3 full 4-brand + live-verify DoD #37 (boot comunify health 200 + 401/200 sin env legacy) se cierran en esa sesión.

## 7. Cross-references
- Origin blocker: `comunify/docs/product/stories/comunify-shell-organism/checkpoint.md § Blocker` + `chris-input.md` (2026-06-16).
- Target contract: `docs/core-modules/luana-core-copilot.md` (a crear/actualizar en el lift).
- Engine surface: `core/luana-core-copilot/src/luana_core_copilot/api/chat.py` · `core/luana-core-platform/src/luana_core_platform/core/{config,rate_limit}.py`.
- Patrón establecido a eliminar: `vitalia/backend/src/modules/vitalia/copilot/api/routes/wizard_onboarding_routes.py` (own-routes per-brand).
- Process: `docs/promotion-protocol/README.md`.
