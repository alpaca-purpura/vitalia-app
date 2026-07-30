# Verificación REAL god-matrix (anti-teatro · JWT real Clerk contra dev-app)

> **Ejecutada por orchestrator (autónomo, ratificado Chris)** el 2026-05-30 contra el dev-app vivo (`luana-dev-vitalia_backend_dev-1` :8002, hot-reload tomó T-1+T-2). JWT real minteado vía **Clerk Backend API** (`POST /v1/sessions` → `POST /v1/sessions/{id}/tokens`, sk_test dev instance). **NO se imprimió secret, JWT ni PHI** — solo status codes + logs sanitizados (HIPAA-lite).

## Metodología (verificación REAL ≠ HTTP 200)

Se ejerció la **acción real del usuario** con JWT real de Clerk (firma RS256 verificable por JWKS), no monkeypatch. Se leyeron los **logs del backend** + se inspeccionó la DB. Endpoint usado para el happy path: `GET /api/v1/crm/conversations` (PHI-gated, tabla `vitalia_conversations` existe en dev).

## Resultados god-matrix (status codes — sin PHI body)

| Scenario | Usuario / token | Endpoint | Esperado | **Real (live)** | Veredicto |
|---|---|---|---|---|---|
| SC-1 happy | doctor.demo JWT real (rol DB=doctor) | GET /crm/conversations | 200 | **HTTP 200** | ✅ JWKS real verificado + rol desde DB + PHI concedido |
| SC-2 negative | marketing.demo JWT real (rol DB=marketing) | GET /crm/conversations | 403 | **HTTP 403** | ✅ rol desde DB → RBAC deniega, sin leak |
| SC-3 edge (no-rol) | doctor JWT real + tenant ajeno | GET /crm/conversations | 403/404 | **HTTP 403** | ✅ sin rol en ese tenant → deniega, sin leak |
| SC-4 adversarial | token forjado | GET /crm/conversations | 401 | **HTTP 401** | ✅ decoder rechaza (Not enough segments) |
| SC-4b adversarial | `stub:...` legacy | GET /crm/conversations | 401 | **HTTP 401** | ✅ stub NO aceptado en runtime (sin VITALIA_AUTH_STUB) |

**El objetivo central de la story está PROBADO LIVE:** el origen era que las superficies PHI **rechazaban el JWT real de Clerk → 401** (decoder stub). Ahora el JWT real del doctor → **200**, marketing → **403**, forjado/stub → **401**. El decoder fue desentubado (stub → JWKS real reusando engine `verify_token_payload`) + el rol fluye desde `user_tenants.role` (DB) al `ClinicContext`. Verificado ejerciendo la acción real + leyendo logs, NO "saqué 200 = funciona".

## Evidencia de logs (backend)

- SC-1/SC-2/SC-3 (200/403): el JWT real **se verificó OK** (cero `JWT Validation Error` para esos requests) → la verificación JWKS real funciona sobre el token real de Clerk.
- SC-4/SC-4b (401): logs muestran `jwt.exceptions.DecodeError: Not enough segments` / `Invalid header string` → el decoder rechaza forjado/stub correctamente.

## Audit row (SC-1 grader) — verificado por código + tests, NO live-ejercitable en dev

El grader de SC-1 pide "audit_log row escrito". El audit PHI está cableado a nivel **service+repo** (no endpoint):
- `crm/application/services/patient_service.py`: métodos decorados `@require_phi_access(resource_type="patient")`.
- `crm/infrastructure/persistence/patient_repository.py`: escribe `AuditLogEntry` vía `self._audit_repo.write(...)` en cada acceso a paciente (líneas 116/124/263/271/323/332/387/395).
- inbox services escriben audit vía `self._audit_writer.write(...)`.
- Integration tests SC-1..SC-4 assertean el audit write en el path de paciente.

**No live-ejercitable en dev** porque la tabla base `vitalia_patients` NO existe en la DB dev (ver observed-bug abajo) → el endpoint de paciente daría 500 antes de poder leer el audit row. El endpoint `/conversations` que sí pude ejercer live no escribe el audit per-paciente (es mensajería, gated por rol). Conclusión honesta: el audit-on-patient-access está **probado por código + integration tests**, NO por ejercicio live (bloqueado por gap de DB pre-existente, ajeno a esta story).

## Hallazgos del anti-teatro (gaps pre-existentes, NO causados por esta story)

1. **Tablas base PHI faltantes en dev:** `vitalia_patients` + `vitalia_leads` NO existen en `vitalia_dev` (solo `vitalia_patient_{dental,medical}_histories`, `vitalia_conversations`, `vitalia_messages`). Los endpoints `GET /crm/leads` y `GET /crm/patients/{id}` dan **HTTP 500** (`relation "vitalia_leads" does not exist`). **Pre-existente** (gap de migración dev, no de esta story de auth). Documentado en `vitalia/docs/observed-bugs/2026-05-30-vitalia-patients-leads-tables-missing-dev.md`. → follow-up: migración/seed dev.

## Conclusión

- **Story scope (JWKS real + rol DB + repos reales): PROBADO LIVE.** El desentubado funciona end-to-end con JWT real.
- **Gaps expuestos por el anti-teatro:** tablas base faltantes en dev (pre-existente) → follow-up separado.
- El audit-on-patient está codeado + integration-tested; su ejercicio live quedó bloqueado por el gap de tablas (no por el código de esta story).
