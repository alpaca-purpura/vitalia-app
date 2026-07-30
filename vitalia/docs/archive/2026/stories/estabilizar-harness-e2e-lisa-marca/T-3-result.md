# T-3 result — BE: X-User-ID opcional (sub-bug #1) + actor de audit real (sub-bug #2b)

> Builder: builder-backend (Sonnet). State: **tests-passing** (NO audit verdict — eso lo decide gate-runner + auditor-backend downstream).
> Surface: `vitalia/backend/src/modules/vitalia/{brand_studio,iam}/`. Cero core · cero cross-brand · cero copilot/sales_agent · cero frontend.

## Resumen del diff

5 archivos (1 modificado prod + 1 nuevo prod + 3 nuevos tests):

| Archivo | Tipo | Qué |
|---|---|---|
| `vitalia/backend/src/modules/vitalia/brand_studio/api/routers/marca_router.py` | MODIFY | Sub-bug #1: `get_prohibited_phrases` `user_id: str \| None = Header(alias="X-User-ID", default=None)` + `del user_id` (no se parsea/usa; `response_model=ProhibitedPhrasesListDTO` intacto; X-Tenant-ID required). Sub-bug #2b: import iam público + `UserNotFoundError`; NEW helper `_resolve_audit_actor(session, user_id_header) -> UUID` (DRY); reemplazo `UUID(user_id)` → `await _resolve_audit_actor(...)` en los 11 endpoints que parseaban user_id (9 que auditan + get_initial_state SSR + get_trust_signals). `tenant_uuid = UUID(tenant_id)` se mantiene crudo (tenant-isolation). |
| `vitalia/backend/src/modules/vitalia/iam/application/services/user_resolver.py` | NEW | Punto **público** `resolve_user_uuid_from_clerk_id(session, clerk_id) -> UUID` (M2: NO se llama el privado `ClinicResolver._resolve_user_uuid`). Query canónica `select(UserModel.id).where(UserModel.clerk_id == clerk_id)`; sin match → `UserNotFoundError`. `# cap: iam.iam-scaffold-slice-1`. |
| `vitalia/backend/tests/modules/vitalia/brand_studio/test_prohibited_phrases_optional_header.py` | NEW (test) | A1/A2 — 5 tests pure-app (ASGITransport). |
| `vitalia/backend/tests/modules/vitalia/brand_studio/test_audit_actor_real.py` | NEW (test) | A3 / SC-6 BE — 3 unit (resolución actor) + 1 integration DB (PATCH real → audit row). |
| `vitalia/backend/tests/modules/vitalia/iam/test_user_resolver.py` | NEW (test) | iam público — 2 unit + 2 integration DB. |

**Decisión del orchestrator seguida (mecanismo header-trust, NO JWT):** ver `T-3-impl-log.md § Decisión de arquitectura`. El actor se resuelve del valor de `X-User-ID` (UUID passthrough back-compat / Clerk id → users.id vía iam público). No se abre verificación JWT en este router.

## Validator gate output (literal)

Entorno local: venv raíz `/home/chalreme/Proyectos/luana-platform/.venv`; DB `vitalia_dev` en `127.0.0.1:5435` (`POSTGRES_DSN` + Settings env exportados; los tests app-import están `@pytest.mark.integration` → auto-skip sin Postgres, consistente con los siblings).

```
############ G5.1 ticket tests (per-file, GREEN) ############
test_prohibited_phrases_optional_header.py  → 5 passed   (A1 no_user_id 200, A2 bad_tenant 422, no_tenant 422, with_user_id 200, passes_tenant_not_user)
test_audit_actor_real.py                    → 4 passed   (A3 clerk→users.id resuelto, UUID passthrough, clerk-not-found 422, integration DB audit actor real ≠ tenant)
test_user_resolver.py (iam)                 → 4 passed   (unit query + UserNotFoundError, integration seed+resolve, integration unknown→raise)
############ G5.2 arch-fitness ############
tests/architecture/                         → 335 passed, 0 failed
  (response_model required mantenido · brand_studio DDD ok · tenant-isolation · audit-sync-write · PHI dual-filter · sin cross-module a privado)
############ G5.3 ruff check + format ############
ruff check (brand_studio + iam + 3 tests)   → All checks passed!
ruff format --check (router + iam + tests)  → 5 files already formatted
############ G5.4 no core / cross-brand / forbidden ############
git status                                  → OK zero forbidden paths (cero core/ · nicolify/ · comunify/ · lupulo/ · frontend/ · copilot/ · sales_agent/)
############ A4 (be_arch_fitness) ############
tests/architecture/                         → 335 passed (response_model=ProhibitedPhrasesListDTO mantenido)
############ A5 (arch_no_core_edit) ############
! git diff --name-only main...HEAD | grep '^core/'  → vacío (cero core)
############ iam suite (no regresión) ############
tests/modules/vitalia/iam/                  → 44 passed
```

### mypy `--strict` (be_typecheck) — LIMITACIÓN DE ENTORNO LOCAL (re-run lo hace gate-runner)

- **mypy NO está instalado** en el venv raíz local (`${WS}/.venv/bin/mypy` no existe) ni hay config mypy en el repo. El validator `be_typecheck` (`${WS}/.venv/bin/mypy --strict marca_router.py`) **no es ejecutable en este entorno** — corre en la imagen dev del gate-runner/CI.
- Verificación parcial vía `uvx mypy`: `user_resolver.py --strict` → **Success: no issues found**. En `marca_router.py` los únicos errores son `untyped-decorator` (sobre los 21 `@router.X`, artefacto de stubs FastAPI ausentes en el entorno aislado de uvx — aplican al archivo entero, **pre-existentes, NO a mis líneas**) y `unused-ignore` en archivos NO tocados (`marca_service.py`, `voice_blocklist_service.py`). **Mi código añadido (`_resolve_audit_actor`, el import, el header opcional) está completamente anotado** (`async def _resolve_audit_actor(session: AsyncSession, user_id_header: str) -> UUID`). → gate-runner debe re-correr mypy con la config/venv real.

### Nota de entorno (NO regresión introducida por T-3)

La suite completa `tests/modules/vitalia/brand_studio/` tiene **48 failures PRE-EXISTENTES** verificadas con el router stasheado + mis tests removidos (48 failed idéntico al baseline). Causas, ambas ajenas a T-3: (a) los `test_marca_router_*.py` + `test_patch_personality_audit.py` siblings usan `AsyncClient(app=app, ...)` incompatible con httpx 0.28.1 (necesita `ASGITransport`); (b) contención asyncpg single-connection entre app-import tests y los `db_session`-based (migration/seed) en modo single-process. **Mis tests usan el patrón moderno `ASGITransport` y un engine async dedicado** → corren GREEN y order-independent; añaden 0 failures. (El `-k "prohibited_phrases or audit_actor_real"` de G5 arrastra los `test_prohibited_phrases_{migration,seed}.py` pre-existentes que fallan por esa contención — pre-existente, no de T-3.)

## Acceptance criteria

| AC | Verifier | Resultado |
|---|---|---|
| A1 — GET prohibited-phrases sin X-User-ID → 200 | `-k prohibited_phrases_no_user_id` | ✅ PASS |
| A2 — X-Tenant-ID inválido → 422 (tenant-isolation) | `-k prohibited_phrases_bad_tenant` | ✅ PASS |
| A3 — PATCH personality → audit actor = users.id real (≠ tenant_id) | `-k audit_actor_real` (3 unit + 1 integration DB) | ✅ PASS |
| A4 — be_arch_fitness verde (response_model mantenido) | `tests/architecture/` | ✅ 335 passed |
| A5 — cero archivo de core/ tocado | `! git diff ... grep '^core/'` | ✅ vacío |

## Skills consulted (must_load enforcement v4.1)

| Skill / rule | Por qué invocada | Decisión tomada (cita) |
|---|---|---|
| `backend-expert` (SOP + runtime-quality-checklist) | Toda la implementación BE | Inside-Out: la resolución del actor vive en el router (api thin → app), la firma del service (`user_id: UUID`) NO cambia. SQLA 2.0 `select(...).where(...)` en el resolver. Patrón FastAPI `Header(default=None, alias=...)` para opcional. `response_model=` mantenido (PII allowlist). Sin `Any`, sin dict mágico. |
| `.claude/rules/backend-ddd.md` | Cross-module brand_studio→iam | "Cross-module default forbidden excepto port/event"; M2 resuelto exponiendo **app service público** (`resolve_user_uuid_from_clerk_id`), NO el privado `_resolve_user_uuid`. Verificado live que `iam` NO está en `CROSS_MODULE_FORBIDDEN_PATTERNS` de `test_brand_studio_module_ddd.py:56-63` (solo scheduling/payments/fiscal/crm). `FastAPI(redirect_slashes=False)` no tocado. |
| `.claude/rules/tenant-isolation.md` | GET prohibited-phrases + actor | `X-Tenant-ID` SIGUE required; `tenant_uuid = UUID(tenant_id)` crudo intacto en todos los endpoints (no se resuelve el tenant, solo el actor). Tenant inválido → 422 (test A2). |
| `vitalia/.claude/rules/hipaa-lite.md` | Audit log actor (sub-bug #2b) | El actor del `audit_log` DEBE ser UUID (audit_writer hace `CAST(:user_id AS uuid)`); por eso un Clerk id crudo rompía. El fix resuelve a `users.id` UUID real → fidelidad del "quién" (audit row con actor real ≠ tenant). `audit_writer` no se modifica (solo el VALOR del actor que recibe). Estos flujos son brand-config (no-PHI) pero el "quién" del audit se corrige. |
| `.claude/rules/pii-sanitisation.md` | response_model + actor | `response_model=ProhibitedPhrasesListDTO` mantenido (whitelist PII en la respuesta). El resolver no expone PII (solo devuelve UUID). audit_writer ya rutea payload por `sanitize_phi_payload` — preservado. |
| `.claude/rules/tdd-mandatory.md` | Orden de trabajo | RED primero (3 RED confirmados: 422, ModuleNotFound, AttributeError) → GREEN. Bug fix con test que reproduce el bug primero. Cero código antes de RED. |
| `.claude/rules/auditor-self-fix-policy.md` | Contexto de handoff | Builder produce estado `tests-passing`; el verdict (Carril A/B/C) lo decide el auditor downstream, no el builder. |
| FastAPI Header params canonical | Sub-bug #1 | `user_id: str \| None = Header(alias="X-User-ID", default=None)` — sin default un Header es required (causa del 422). Patrón canónico confirmado (brief §15 FastAPI header-params). |
| pytest async testing patterns | Tests | `httpx.AsyncClient(transport=ASGITransport(app=app))` (httpx 0.28 — los siblings usan el `app=` legacy roto); `@pytest.mark.integration` para auto-skip sin Postgres; factory de engine dedicado en integration DB tests para aislar contención asyncpg. |

## Cross-module reads (read-only)

- `iam/application/services/clinic_resolver.py` (leído para confirmar la query canónica `clerk_id → users.id` en `:164` y reusar `UserNotFoundError`). El nuevo público replica esa query SIN tocar el `ClinicResolver` (que sigue sirviendo el path JWT Slice 2).

## Handoff a downstream

- **T-2 (FE-prod)** depende de este BE: con `_resolve_audit_actor` en su lugar, el FE puede mandar `X-User-ID: opts.userId` (Clerk userId real) sin romper el PATCH (el BE lo resuelve a users.id). Back-compat: si el FE/tests aún mandan un UUID, sigue funcionando.
- **live-verify (SC-6/SC-7, Critical Rule #37):** pendiente — requiere `make dev-vitalia` UP + Chrome DevTools MCP (PATCH personality real con owner Clerk → audit_log actor real; GET prohibited-phrases 200 sin header inyectado). Lo ejerce el cierre de story (dod_evidence en checkpoint), no este ticket BE aislado.
- **mypy `--strict`:** re-correr en el entorno con la config/venv real del gate-runner (mypy ausente local).
