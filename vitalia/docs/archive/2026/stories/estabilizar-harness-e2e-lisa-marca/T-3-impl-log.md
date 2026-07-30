# T-3 impl-log — BE: X-User-ID opcional (sub-bug #1) + actor real (sub-bug #2b)

> Owner ejecución: builder-backend (Sonnet). Orchestrator: /dev-team (Opus).
> Surface: `vitalia/backend/src/modules/vitalia/{brand_studio,iam}/`. Cero core, cero cross-brand.

## ★ Decisión de arquitectura del orchestrator (divergencia ratificable vs 03-arch § PARTE C/D)

**Contexto:** el 03-arch (D2-be-resolves-actor) dice "resolver el actor desde el `clerk_sub` del **JWT** vía `_resolve_user_uuid`". Al construir se verificó (live, HEAD) que **el `marca_router` NO recibe JWT** — toda su auth es header-trust: `X-User-Role` (`rbac.py::require_brand_owner_access` lee el header directo) + `X-User-ID` (header directo). No hay bearer token ni `request.state.clerk_sub` en estos 21 endpoints. El path JWT (`ClinicResolver.async_resolve(token, ...)`) es de otro slice (Slice 2) y no aplica acá.

**Decisión (mecanismo, misma intención + mismo scope):**
- **FE (T-2):** `X-User-ID` deja de ser el `tenantId`; pasa a ser el **Clerk userId real** (`useAuth().userId`, ej. `user_2abc...`).
- **BE (T-3 #2b):** en los endpoints que auditan (PATCH personality + los demás PATCH/POST que escriben audit), resolver el actor a `users.id` UUID a partir del valor del header `X-User-ID`:
  - si el valor parsea como UUID → usarlo tal cual (**back-compat**: callers internos/tests legacy que ya mandan `users.id`).
  - si NO es UUID (= Clerk userId) → resolver `clerk_id → users.id` con la lógica iam existente. Sin match → 422 (`Invalid user_id` / `UserNotFoundError` mapeado).
- **Por qué NO el JWT:** abrir verificación JWT en este router toca infra de auth + el contrato de los 21 endpoints = fuera de bugfix-lite (story aparte). El fix de sub-bug #2 es la fidelidad del "quién" en el audit (hoy graba el **tenant** como actor — claramente mal), NO cerrar el hueco de header-spoof (vuln pre-existente y separada; `X-User-Role` ya es header-trust). Este fix mejora "quién" dentro del modelo de confianza vigente.

**M2 (DDD boundary) resuelto:** NO llamar el método privado `iam.ClinicResolver._resolve_user_uuid` cross-module. Exponer un punto **público** en iam — función/servicio app que haga solo el lookup `clerk_id → users.id` (sin requerir el `ClerkJwtDecoder`), p. ej. `iam/application/services/.../resolve_user_uuid_from_clerk_id(session, clerk_id) -> UUID`. `brand_studio` consume ese punto público (patrón cross-module sancionado: app service público, no internals).

**Estado:** decisión del orchestrator (Opus) — divergencia de **mecanismo**, no de intención ni scope. Surfaceada a Chris en `chris-input.md` (💡 PROPONE) + a verificar por `/auditor`. Chris ratificó "scope completo · sub-bug #2 in-story" (dispatch-plan § open-item); puede vetar en demo/merge.

## M1 (grep-gate SC-2 vacuo) — NO es de T-3

El brief (§11 M1) detectó que `sc2_no_mock_backend_bajo_prueba` matchea single-line y el mock es multi-línea → pasa vacuo. Eso se corrige en **T-1** (ajustar el pattern a `page.route("**/api/v1/lisa/marca/{identity,visuals,personality}")`). Anotado para no perderlo.

## Plan (builder-backend — technical design, TDD RED→GREEN)

### Diseño técnico por capa DDD

**iam (solo agregar punto público — M2):**
- NEW `iam/application/services/user_resolver.py::resolve_user_uuid_from_clerk_id(session, clerk_id) -> UUID`. Query `select(UserModel.id).where(UserModel.clerk_id == clerk_id)` (idéntico a `clinic_resolver.py:164`, sin `ClerkJwtDecoder`). Sin match → `UserNotFoundError` (reusa la excepción ya exportada en clinic_resolver). Función app pública (no `_`-prefix). `iam` NO está en `CROSS_MODULE_FORBIDDEN_PATTERNS` de `test_brand_studio_module_ddd.py` (solo scheduling/payments/fiscal/crm) — verificado live.

**brand_studio (router):**
- Sub-bug #1: `get_prohibited_phrases` `user_id: str = Header(alias="X-User-ID")` → `user_id: str | None = Header(alias="X-User-ID", default=None)`. X-Tenant-ID required intacto. `response_model=ProhibitedPhrasesListDTO` intacto. `user_id` NO se parsea/usa (`del user_id`).
- Sub-bug #2b: NEW helper privado `_resolve_audit_actor(session, user_id_header) -> UUID` (DRY): `try UUID(header)` (back-compat) `except ValueError` → `resolve_user_uuid_from_clerk_id`; `UserNotFoundError` → HTTPException 422. Aplicado en los 11 endpoints que parsean user_id (los 9 que auditan + 2 reads que también parsean y T-2 les mandará Clerk id: get_initial_state SSR, get_trust_signals). `tenant_uuid = UUID(tenant_id)` se mantiene crudo (tenant-isolation). La firma del service (`user_id: UUID`) NO cambia — la resolución ocurre en el router.

### Header de cap
- iam nuevo → `# cap: iam.iam-scaffold-slice-1` (mismo cap del módulo).

## Iteration log

### iter-1 (builder-backend, 2026-06-03)

**RED (paso 1):**
- `test_prohibited_phrases_optional_header.py::test_prohibited_phrases_no_user_id` → 422 (hoy) → RED ✓ (+ `passes_tenant_not_user` RED por consecuencia: service nunca se llama por el 422).
- `test_user_resolver.py` → `ModuleNotFoundError` (user_resolver no existe) → RED ✓.
- `test_audit_actor_real.py::TestPatchPersonalityActorResolution` → `AttributeError: ...does not have 'resolve_user_uuid_from_clerk_id'` → RED ✓.

**GREEN (paso 2):**
- NEW `iam/application/services/user_resolver.py` (público `resolve_user_uuid_from_clerk_id`).
- `marca_router.py`: import iam público + `UserNotFoundError`; NEW helper `_resolve_audit_actor`; sub-bug #1 header opcional; reemplazo `UUID(user_id)` → `await _resolve_audit_actor(session, user_id)` en 11 endpoints; el `except` de tenant pasó a `"Invalid tenant_id"` (user_id ya no se parsea ahí).

**Hallazgo de entorno (httpx 0.28 + asyncpg single-connection):**
- Los `test_marca_router_*.py` + `test_patch_personality_audit.py` pre-existentes usan `AsyncClient(app=app, ...)` que **NO** soporta httpx 0.28.1 (necesita `ASGITransport`). Mis tests usan el patrón moderno `AsyncClient(transport=ASGITransport(app=app))` → corren OK.
- La suite completa `brand_studio` tiene **48 failures PRE-EXISTENTES** (verificado con el router stasheado + mis tests removidos: 48 failed idéntico). Causa: (a) `app=app` httpx-incompat en siblings, (b) contención asyncpg single-connection entre app-import tests y los db_session-based (migration/seed). **Mis cambios añaden CERO failures nuevos** (de hecho suman 13 passing).
- Mis integration tests (audit_actor_real DB + iam DB) usan un **engine async dedicado** (no el fixture `db_session` compartido) para evitar esa contención → order-independent.

**GREEN final (per-file, env completo POSTGRES_DSN→vitalia_dev:5435 + Settings env):**
- `test_prohibited_phrases_optional_header.py` → 5 passed.
- `test_audit_actor_real.py` → 4 passed (incl. integration DB: PATCH personality real con Clerk id → audit_log.user_id = users.id resuelto ≠ tenant_id).
- `test_user_resolver.py` → 4 passed (unit + integration).
- `tests/architecture/` → **335 passed, 0 fail** (response_model mantenido, brand_studio DDD ok, tenant-isolation, audit-sync, no cross-module privado).
- `tests/modules/vitalia/iam/` → 44 passed (sin regresión).
- ruff check + format → clean. mypy: ver § limitación de entorno en T-3-result.md (mypy no instalado en venv local; iam file pasa `--strict` vía uvx; los errores `untyped-decorator` del router son artefacto de stubs FastAPI ausentes en uvx, pre-existentes a nivel whole-file, NO de mis líneas).
- Scope guards: cero core / cross-brand / copilot / sales_agent / frontend.

### Integración (handoff al orchestrator)

- Construido en worktree aislado de agente `worktree-agent-ac076fb4683d383dc` (base `09e12ae9`). El commit T-3 es **`e1bdc6e0`** (7 archivos), pusheado a `origin/worktree-agent-ac076fb4683d383dc`.
- **NO se pusheó a `wip/vitalia` directo:** el worktree `wip/vitalia` (`~/Proyectos/luana-vitalia`) está en `22f25e4d`, divergente de mi base `09e12ae9` (mi base lo incluye y va adelante con `7b9f7289`/`ab8621e7`/`09e12ae9`) → push directo sería non-fast-forward (prohibido por parallel-safety M5 / git-safety). El orchestrator integra `e1bdc6e0` a `wip/vitalia` (cherry-pick/merge) según su política de branches.
- `git status` limpio; HEAD == origin del branch de agente.
