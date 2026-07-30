# Observed bug — FE telemetry POST `/api/telemetry/growth-studio-event` → 404 (cross-cutting)

**Found:** 2026-06-04 · durante live E2E del inbox de Adrián contra `dev-app.vitalialat.com` (story `vitalia-fase2-adrian-inbox`).
**Severity:** media (no rompe UX — fire-and-forget — pero **trippea el gate anti-burbuja** de TODA e2e que aterrice en una página que dispare telemetría, y ensucia la consola del navegador en prod).
**Scope:** **NO es del inbox.** Es transversal (mateo/telemetry + plataforma). Lo dejo documentado, no lo arreglo desde la story del inbox (scope discipline + el endpoint tiene una decisión de contrato propia).

## Síntoma

En la e2e del inbox (`adrian-inbox-tenant.spec.ts:43` y `:101`), el fixture `base.ts` (anti-burbuja) falla en el teardown:

```
console.error en el browser: Failed to load resource: the server responded with a status of 404 ()
  @ https://dev-app.vitalialat.com/api/telemetry/growth-studio-event:0
```

El gate es correcto: hay un 404 real en runtime. La lógica de aislamiento cross-tenant del test pasa; lo que falla es la verificación de "0 errores de consola" por culpa de este 404.

## Causa raíz

- `vitalia/frontend/src/features/mateo/lib/telemetry.ts:184` hace `POST /api/telemetry/growth-studio-event` con un `fetch` crudo (sin `fetchClient` → **sin** `Authorization` ni `X-Tenant-ID`).
- **No existe** ningún router HTTP que sirva esa ruta. El `GrowthStudioEmitter` (`backend/src/modules/vitalia/_shared/telemetry/growth_studio_emitter.py`) es un emisor **server-side fire-forget** que los routers (scheduling/clinics/payments/crm) llaman internamente — nunca se expuso como endpoint FE.
- Resultado: cada `trackEvent(...)` del FE pega contra un 404.

## Por qué NO lo arreglo acá

Wirear `POST /api/telemetry/growth-studio-event` correctamente requiere una decisión de contrato que no es del inbox:
1. **Auth/tenant resolution**: el FE manda el POST sin headers de auth ni tenant. O se cambia `telemetry.ts` para usar `fetchClient` (auto-inyecta `X-Tenant-ID` + token), o el endpoint deriva tenant del cookie de Clerk. `emit_event` exige `tenant_id` (UUID).
2. **PHI**: `emit_event` sanitiza props server-side, pero el contrato de ingestión FE→BE debe validar el `event_type` (≤64 chars, sin PHI) + rate-limit.
3. Es **mateo/plataforma**, dispara app-wide (no solo inbox).

## Fix recomendado (story dedicada · mateo o plataforma)

- Crear `vitalia/backend/src/modules/vitalia/_shared/telemetry/api/telemetry_router.py` con `POST /api/telemetry/growth-studio-event` que: resuelve ctx (tenant/clinic/user) vía el mismo `ClinicResolver` que el resto, valida `event_type`, y delega a `GrowthStudioEmitter.emit_event(...)` fire-forget.
- Cambiar `telemetry.ts` para usar `fetchClient` (headers tenant/auth) en vez de `fetch` crudo.
- Hasta entonces: el gate anti-burbuja seguirá marcando este 404 en cualquier e2e real-backend que dispare telemetría.

## Impacto en la e2e del inbox (honesto)

- `adrian-inbox-tenant.spec.ts:43` + `:101` quedan **rojos por este 404 pre-existente**, NO por un defecto de aislamiento del inbox. No los fake-greeneo allowlisteando un 404 real en el `base.ts` compartido (sería ocultar el bug).
- El resto de la suite del inbox corre verde contra dev-app.
