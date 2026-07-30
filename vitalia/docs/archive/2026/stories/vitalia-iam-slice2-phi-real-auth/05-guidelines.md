# 05-guidelines — vitalia-iam-slice2-phi-real-auth

> Build SUPERVISADO (autonomous_mode: false — auth/PHI). El orchestrator (Chris) reporta en el gate de verificacion PHI con JWT real ANTES de cerrar.

## must_load_skills (por surface)

### BE-auth core + repos-wire (builder-backend)
- `backend-expert`
- `tessl__fastapi`
- `tessl__pytest-api-testing`
- `.claude/rules/tenant-isolation.md`
- `.claude/rules/backend-ddd.md`
- `.claude/rules/anti-duplication.md`
- `.claude/rules/tdd-mandatory.md`
- `.claude/rules/test-design-doctrine.md`
- `vitalia/.claude/rules/hipaa-lite.md`

### FE hook (builder-frontend)
- `frontend-expert`
- `vitalia-design-system`   # canal unico FE (no hereda overlay) — aunque este ticket no toca shell, lo carga por convencion
- `.claude/rules/frontend-fsd.md`
- `.claude/rules/spanish-text.md`
- `.claude/rules/tdd-mandatory.md`

## Files in scope

| Path | Accion | Surface |
|---|---|---|
| `vitalia/backend/src/modules/vitalia/iam/infrastructure/clerk_jwt_decoder.py` | MODIFY (JWKS real + stub env-gated) | BE |
| `vitalia/backend/src/modules/vitalia/iam/application/services/clinic_resolver.py` | MODIFY (rol desde DB) | BE |
| `vitalia/backend/src/modules/vitalia/crm/api/router.py` | MODIFY (repos reales DI) | BE |
| `vitalia/backend/src/modules/vitalia/crm/api/consent_endpoints.py` | MODIFY (repos reales DI) | BE |
| `vitalia/backend/src/modules/vitalia/marketing/api/deps.py` | MODIFY (rol desde DB) | BE |
| `vitalia/backend/src/modules/vitalia/marketing/api/routes.py` | MODIFY (rol desde DB) | BE |
| `vitalia/backend/src/modules/vitalia/inbox/api/router.py` | MODIFY (repos reales + rol DB) | BE |
| `vitalia/backend/tests/integration/test_phi_real_auth.py` | NEW (SC-1..SC-4) | BE |
| `vitalia/backend/tests/architecture/test_auth_stub_env_gate.py` | NEW | BE |
| `vitalia/frontend/src/hooks/useCurrentUser.ts` | MODIFY (rol desde /me) | FE |

## Patterns REQUIRED

- **REUSE engine JWKS:** `from luana_core_iam.application.auth import verify_token_payload`. NUNCA recrear `PyJWKClient` ni la logica JWKS.
- **REUSE engine model:** `from luana_core_iam.infrastructure.models.user_tenant_model import UserTenantModel` + `UserModel` para la query de rol async. Cero tabla nueva.
- **Stub env-gated (Q2/AD-4):** `if os.environ.get("VITALIA_AUTH_STUB")=="1" and token.startswith("stub:") -> _decode_stub; else -> verify_token_payload(token)`.
- **ClinicContext shape intacto:** los consumers leen `ctx.role`; solo cambia la FUENTE del rol. No tocar la dataclass fields.
- **Repos reales via `Depends(get_async_session)`:** instanciar repo real + `AuditLogRepository(session)` por request. Quitar `from unittest.mock import AsyncMock` inline de los routers runtime.
- **HIPAA-lite intacto:** `@require_phi_access(roles=["doctor","nurse","admin_clinic"], audit_repo=...)` + dual filter `tenant_id+clinic_id` + audit sync pre-response.
- **SQLA 2.0 async:** `select(...).where(...)` + `await session.execute(...)`. NUNCA `session.query()`.
- **`response_model=` en cada endpoint** (ya presente — preservar).
- **structlog**, nunca `print`/`logging`.
- **TDD RED-first** por capa (decoder gate, resolver rol DB, integration SC-1..SC-4, arch stub-env-gate, FE hook).
- **Spanish neutro** en errores user-facing 401/403 (preservar los existentes).

## Patterns FORBIDDEN

- Editar `core/luana-core-*/src/` (HARD — consume via import; si requiere cambio engine -> STOP + escalar `/pm-luana`).
- Recrear `PyJWKClient` / `verify_token_payload` / JWKS logic brand-local (anti-duplication).
- Crear tabla/model `user_tenants` mirror brand-local.
- Sacar el rol del token payload (debe venir de DB).
- Dejar `AsyncMock()` inline en paths runtime de crm/consent/marketing/inbox.
- Setear `VITALIA_AUTH_STUB` en `.env.dev.template`, `docker-compose.dev.yml`, o cualquier config runtime.
- Aceptar tokens `stub:...` en runtime (sin la env).
- Bypass de JWKS verify ("dev shortcut").
- Skip dual filter `clinic_id` ("single-clinic tenant").
- Audit log async fire-and-forget (debe ser sync-awaited pre-response).
- Tocar `vitalia/frontend/src/components/ui/`, `layout.tsx`, o `useClinicId` (clinic_id sigue por header).
- Inventar repo nuevo si falta uno real -> marcar sub-scope en impl-log (OQ-1).
- PHI en URL/query params (POST body siempre).

## forbidden_to_touch (verbatim para builders)

```
core/luana-core-*/src/
nicolify/  comunify/  lupulo/  (cualquier otra brand)
vitalia/backend/src/modules/vitalia/{copilot,sales_agent}/
vitalia/frontend/src/components/ui/
vitalia/frontend/src/app/**/layout.tsx
vitalia/backend/src/modules/vitalia/_shared/auth/rbac.py        (reusar, NO modificar)
vitalia/backend/src/modules/vitalia/_shared/repositories/audit_log_repository.py  (reusar, NO modificar)
```

## Verification gate (supervisado — anti-teatro)

Antes de cerrar (Chris ratifica):
1. `cd vitalia/backend && ${WS}/.venv/bin/pytest tests/integration/test_phi_real_auth.py tests/architecture/ -v` -> verde.
2. `${WS}/.venv/bin/ruff check src/modules/vitalia/{iam,crm,marketing,inbox}/` -> 0 errores.
3. god-matrix con JWT real (mint Clerk Backend API) contra dev-app: doctor.demo PHI **200 + audit row** ; recepcion **403** ; cross-tenant **404** ; **logs backend leidos** (sin 401 inesperado en el flujo doctor). Ejercido de verdad — NO "saque 200 = funciona".
