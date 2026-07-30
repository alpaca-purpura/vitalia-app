# Observed bug — `GET /clinics/doctors` 500 (badly formed hexadecimal UUID string)

- **Fecha:** 2026-06-01
- **Detectado por:** live-verify del dual-mount fix (T-2) — al navegar autenticado a `/{tenant}/lisa/staff` contra el stack real (BE :8002), el endpoint de doctores devolvió **500** (el shell renderizó OK; esto es un bug de DATOS, no del shell).
- **Severidad:** alta para `vitalia-fase2-lisa-doctores` (bloquea su live-verify real · ADR-008). NO bloquea el dual-mount fix (shell estructural).
- **Por qué nunca se vio:** el harness e2e de doctores **mockea el backend** (`STAFF_SEED` / `page.route`) → falso verde (mismo patrón lisa-marca). La primera navegación contra el BE real lo expuso.

## Evidencia (backend log, stack real)

```
"GET /api/v1/vitalia/clinics/doctors?page=1&page_size=24 HTTP/1.1" 500
ValueError: badly formed hexadecimal UUID string
  File ".../modules/vitalia/clinics/api/doctors_router.py", line 175, in list_doctors
    tenant_id=UUID(tenant_id),     # ← coerción UUID() sin validación
  File ".../uuid.py", line 178, in __init__
```

## Root cause (diagnóstico)

`doctors_router.py::list_doctors` toma `clinic_id: str = Header(alias="X-Clinic-ID")` y hace `UUID(clinic_id)` directo (líneas 159-175). El `fetchClient` del FE auto-inyecta `X-Tenant-ID` (válido: `e69a691d-…`) pero **NO** un `X-Clinic-ID` con UUID válido → el header llega vacío/no-UUID → `UUID("")`/`UUID("<slug>")` lanza `ValueError` → 500 (debería ser 422 o resolverse clinic desde el tenant).

`tenant_id=UUID(tenant_id)` es la línea que el traceback marca, pero el tenant_id es UUID válido; el culpable es la coerción de header sin guarda (el orden de evaluación de args evalúa ambos `UUID(...)` en la misma llamada).

## Fix candidato (para `/dev-team` en Pendiente B)

Decidir UNA de:
1. **FE** envía `X-Clinic-ID` con el clinic UUID real (resolver clinic activa del tenant en `fetchClient` o en el caller del hook de doctores).
2. **BE** resuelve `clinic_id` desde el tenant (clinic por defecto) cuando el header falta, en vez de exigirlo crudo.
3. **BE** valida los headers a UUID con `422` explícito (no `UUID()` desnudo) — guarda mínima anti-500.

Regression test FIRST (RED): request a `/clinics/doctors` con `X-Clinic-ID` ausente/invalid → debe dar 422 (no 500); con válido → 200 dual-filter tenant+clinic.

## Relación con otras stories

- **vitalia-fase2-lisa-doctores** (reviewing, defer_audit:true): este 500 es prerequisito de su live-verify real (ADR-008). No puede llegar a `done` con evidencia real hasta resolverlo.
- **vitalia-shell-dual-mount-a11y-fix**: NO afectado — el shell renderizó single-main + single-slot + consola limpia aún con el panel en error state; `lisa/marca/identidad` (sin doctores) también verde.
