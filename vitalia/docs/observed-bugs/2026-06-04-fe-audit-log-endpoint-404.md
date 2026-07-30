# Observed bug — FE `AuditedSection` POST `/api/v1/vitalia/audit-log` → 404 (PHI audit, cross-cutting)

**Found:** 2026-06-04 · durante live E2E del inbox de Adrián contra `dev-app.vitalialat.com` (story `vitalia-fase2-adrian-inbox`), al resolver el telemetry-404 (twin de este bug).
**Severity:** **media-alta** — es un gap de **cumplimiento HIPAA-lite** (la escritura de audit-log de PHI **no persiste**: el endpoint no existe) + **trippea el gate anti-burbuja** de toda e2e que abra una conversación (la `ContactSidebar` monta `AuditedSection` → 404).
**Scope:** **NO es del inbox per se.** Es transversal (componente PHI compartido `components/shared/phi/AuditedSection.tsx` + el módulo `audit`). Mismo patrón exacto que el telemetry-404 (`2026-06-04-fe-telemetry-growth-studio-event-404.md`): **raw `fetch` a una ruta BE inexistente**.

## Síntoma

En la e2e del inbox (`adrian-inbox-tenant.spec.ts:43`), el fixture `base.ts` (anti-burbuja) falla en el teardown:

```
console.error en el browser: Failed to load resource: the server responded with a status of 404 ()
  @ https://dev-app.vitalialat.com/api/v1/vitalia/audit-log:0
```

## Causa raíz

- `vitalia/frontend/src/components/shared/phi/AuditedSection.tsx:93` hace `POST /api/v1/vitalia/audit-log` con un `fetch` crudo. **A diferencia del telemetry-404, este SÍ manda headers** (`Authorization` + `X-Tenant-ID` + `X-Clinic-ID`) — el problema es puramente que **no existe el router BE**.
- `main.py` no monta ningún router en `/api/v1/vitalia/audit-log`. El módulo `audit` tiene `AsyncAuditWriter` (`vitalia/backend/src/modules/vitalia/audit/audit_writer.py`) que los routers llaman **internamente** (sync write pre-response per `hipaa-lite.md`), pero **nunca se expuso un endpoint de ingestión FE**.
- `AuditedSection` se renderiza en `ContactSidebar.tsx` (panel derecho del inbox) → **cada apertura de conversación** dispara el 404.

## Por qué importa (más que telemetry)

`hipaa-lite.md § Audit log` exige que **toda lectura/modificación de PHI** registre una fila de audit_log (sync, no opcional). Si la lectura de PHI desde el FE (ver datos del contacto en `ContactSidebar`) intenta escribir el audit-log vía un endpoint inexistente, **ese registro de auditoría se pierde silenciosamente** (el `catch` lo traga). Es un gap de cumplimiento, no solo ruido de consola.

> ⚠️ Verificar si la lectura de PHI del lado servidor (el endpoint compound `GET /crm/conversations/{id}` usa `get_async_session_committing`) YA escribe su propia fila de audit_log server-side. Si lo hace, el `AuditedSection` del FE sería redundante (doble registro) y la decisión correcta podría ser **borrar el `fetch` del FE** en vez de crear el endpoint. Esto es parte de la decisión de contrato.

## Fix recomendado (decisión de contrato — análoga a telemetry pero PHI/seguridad)

Dos caminos, a decidir:

- **(A) Crear el endpoint** `POST /api/v1/vitalia/audit-log` (router en módulo `audit`) que resuelve ctx vía `ClinicResolver`, valida `action`/`resourceType`/`resourceId`, y delega a `AsyncAuditWriter` (sync write). Persiste el audit de lecturas PHI iniciadas desde el FE.
- **(B) Borrar el `fetch` del FE** si la auditoría de la lectura PHI ya se hace server-side en el endpoint que sirve los datos (evita doble registro + elimina el 404). Preferible si server-side ya cumple `hipaa-lite.md § Audit log`.

En ambos casos: cambiar el `fetch` crudo de `AuditedSection` por `fetchClient` (si se mantiene) o eliminarlo (si B).

## Impacto en la e2e del inbox (honesto)

- `adrian-inbox-tenant.spec.ts:43` queda **rojo por este 404** (además del 404 cross-tenant deliberado de `/crm/conversations/{tenantB-conv}` que el propio test provoca y NO opt-outea del gate — ver nota de test-design abajo).
- El telemetry-404 (twin) YA está resuelto (endpoint creado + `fetchClient`). El resto de la suite del inbox corre verde salvo lo de arriba.

## Nota de test-design (separada del bug de producto)

Los tests adversariales SC-10 (`:43`, `:101` cross-tenant) **provocan un 404 a propósito** (acceder a una conv de otro tenant → 404 = aislamiento CORRECTO). El gate `base.ts` NO exenta esos 404 → el test debería:
- `test.use({ failOnRuntimeError: false })` (opt-out documentado en `base.ts`) y assertear directamente el comportamiento de aislamiento, **o**
- el `base.ts` permitir 404 esperados en specs marcados adversariales.
Además `:76` abre una conv `00000…01` (de tenant B) — probable **state-bleed** de `:43` vía last-conv en localStorage/URL ([[e2e-seeded-state-masks-cold-start]]) → la variante cold-start debería limpiar el estado.
