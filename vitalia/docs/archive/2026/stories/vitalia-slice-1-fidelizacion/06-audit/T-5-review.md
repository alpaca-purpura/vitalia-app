<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 -->
# Backend Code Review: T-5 BE fideliz application services

**Date:** 2026-05-20
**Brand:** vitalia
**Ticket:** T-5
**Files Reviewed:** 10 (3 DTOs + 6 services + 1 repo extension)
**Verdict:** **WARN**

## Category Summary

| # | Category | Status | Notes |
|---|---|---|---|
| 1 | DDD Compliance | PASS | Servicios en `application/services/` orquestan repos + audit + outbox. NO DB queries directas. DTOs aislados en `application/dtos/`. Domain events emitidos via outbox `adapter_bus.publish` (engine `luana_core_events`) |
| 2 | Tenant Isolation | PASS | Cada llamada repo pasa `tenant_id + clinic_id` explícito. Verificado en `proactive_outbound_service.py`, `nps_service.py`, `opt_out_service.py`, `pause_patient_service.py`, `manual_call_service.py` |
| 3 | Soft Deletes | PASS | opt_out cascade marca `outcome=OPTED_OUT` (verified `opt_out_service.py`) — no hard delete |
| 4 | Code Quality | PASS | ruff 0 errors fideliz module. format clean |
| 5 | SQLAlchemy 2.0 | PASS | Services consume repos (no SQLA direct) — separación correcta DDD |
| 6 | Async Consistency | PASS | `async def` en todos los services + `await` consistente en repo + outbox + audit calls |
| 7 | Pydantic v2 / PII | PASS | DTOs ConfigDict, response sin PHI (verificado `ProactiveReminderResponse`, `NPSResponseResponse`, `OptOutResponse` solo UUIDs + flags + status enum) |
| 8 | Migration Quality | N/A | Sin migraciones en este ticket |
| 9 | Security | WARN | F1 — `proactive_outbound_service.py` step 2 bloquea TODAS las plantillas si `marketing_opt_in=False`, sin distinguir UTILITY vs MARKETING (contradice 03-arch-be.md § 7 + T-8 `WhatsAppTemplateDef.requires_marketing_opt_in` field). Comportamiento "fail-safe" pero sobrebloquea UTILITY (citas confirmadas) → UX bug + lógica que contradice docstring. Ver § F1 |
| 10 | Tests / TDD | PASS | 29 service unit tests RED→GREEN. SC-01 happy + SC-02 negative cubiertos explícitamente |
| 11 | Cross-cutting | PASS | structlog only, `datetime.now(UTC)` (no `utcnow()`), Spanish neutro en mensajes de output, audit_log payload_redacted=b"" (no PHI), outbox pattern para domain events |
| 12 | Mirror detection | PASS | `adapter_bus` consumido del engine (`luana_core_events.outbox.adapter_bus`); `AuditLogEntry` del shared brand-local; `ComplianceService` engine. NO mirror |

## Findings

### WARN F1 — Step 2 bloquea UTILITY templates sin distinguir categoría

**Category:** 9 (Security/UX false-positive) + 5 (Service contract drift)

**File:** `vitalia/backend/src/modules/vitalia/fidelizacion/application/services/proactive_outbound_service.py:164-180`

**Issue:** El paso 2 del flow:
```python
# Paso 2 — Verificar marketing_opt_in para templates MARKETING
# Templates de tipo MARKETING requieren opt-in explícito del paciente.
# Templates UTILITY (recordatorios de citas confirmadas) no lo requieren.
if not marketing_opt_in:
    return ProactiveReminderResponse(... blocked_reason="marketing_opt_in_required" ...)
```

El docstring (líneas 165-166) afirma "Templates UTILITY no lo requieren", pero el código bloquea **siempre** cuando `marketing_opt_in=False`, sin consultar la categoría del template. La fuente de verdad está en `WhatsAppTemplateDef.requires_marketing_opt_in: bool` en `vitalia/backend/src/modules/vitalia/connections/whatsapp/registry.py` (T-8 shipped). Templates UTILITY como `recordatorio_proxima_sesion` (cita confirmada) y `recordatorio_control_doctor` tienen `requires_marketing_opt_in=False`.

Resultado: paciente que NO opt-in marketing pero tiene cita agendada NO recibe el recordatorio UTILITY. Bug UX silencioso y contradice 03-arch-be.md § 7 (líneas 622-625):
```python
template = await self.template_registry.get(request.template_id)
if template.category == "MARKETING" and not patient.marketing_opt_in:
    raise HTTPException(403, ...)
```

**Fix sugerido:**
```python
from src.modules.vitalia.connections.whatsapp.registry import WHATSAPP_TEMPLATE_REGISTRY

template_def = WHATSAPP_TEMPLATE_REGISTRY.get(template_id)
if template_def is None:
    return ProactiveReminderResponse(... blocked_reason="template_unknown" ...)
if template_def.requires_marketing_opt_in and not marketing_opt_in:
    return ProactiveReminderResponse(... blocked_reason="marketing_opt_in_required" ...)
```

**Severity:** WARN — no es security leak (over-block es fail-safe), pero es contrato funcional roto. Tests T-5 (`test_send_proactive_blocks_marketing_no_optin`) probaron template `multi_session_reminder_01` con un template_id ficticio que ningún testfile correlaciona con UTILITY explícita; no detecta el regression.

**Skill ref:** Contract spec 03-arch-be.md § 7 + T-8-result.md § D4 ("Enforcement at `ProactiveOutboundService` layer (T-5/T-9 implementation — service checks `if template.requires_marketing_opt_in and not patient.marketing_opt_in:`").

**Whitelist self-fix?** NO — fix toca lógica de branch + cambio comportamiento + agregar import nuevo + ajustar test fixtures → categoría NEVER self-fix #2 (cambio branch lógico). → SPAWN dev-team para Caso B fix loop.

### info — Outbox `adapter_bus` import wrapped try/except

**File:** Multiple service files (proactive_outbound, nps, opt_out, pause)
**Issue:** Patrón `try/except ImportError` cuando importa `adapter_bus` del engine. Documentado como pattern dev-env-fallback (mismo precedente en `patient_consent_service.py` per T-2 review).
**Fix:** N/A — pattern intentional + Slice 2 cleanup tracked.

## Allowlist Movement

- Sin cambios. Engine bases consumidas directamente.

## Gherkin coverage verification

| Scenario | Mapping | Status |
|---|---|---|
| SC-01 Happy send_proactive_reminder full flow | `test_proactive_outbound_service.py::test_send_proactive_reminder_full_flow` | EXISTS + PASS |
| SC-02 Negative opt-in blocks MARKETING | `test_proactive_outbound_service.py::test_send_proactive_blocks_marketing_no_optin` | EXISTS + PASS (pero no diferencía UTILITY vs MARKETING — ver F1) |

## Verdict Math

- 10 PASS + 1 WARN (F1) + 0 FAIL → **WARN**
- F1 es decisión per `.claude/rules/auditor-self-fix-policy.md`:
  - NO self-fix (refactor lógico + import + 2 archivos potencial)
  - Spawn dev-team Caso B con findings cita exacta + fix sugerido
  - Cap absoluto 3 audit_iterations; este es iter 1

## Skills Consulted Trace

✓ backend-expert (runtime-quality-checklist) ✓ tessl__fastapi (DTOs) ✓ tessl__pytest-api-testing (29 unit tests) — per T-5-result.md
