# T-BE-2 — Impl Log: scheduling plomería (slot-marking + hold-TTL + sweep)

## § Skills Consulted

| Skill | Por qué invocada | Decisión tomada |
|---|---|---|
| `backend-expert` | FastAPI/SQLA anti-patterns, runtime quality checklist | `mapped_column(Boolean, server_default="false")` para `hold_created_by_agent`; `DateTime(timezone=True)` UTC siempre; `text()` parameterizado dual-filter; structlog no print/logging |
| `tenant-isolation` (rule) | Dual filter hipaa-lite: tenant_id + clinic_id mandatory en CADA query | Todas las firmas de repo reciben `tenant_id + clinic_id`; `mark_slot_confirmed` incluye `clinic_id` en el WHERE |
| `hipaa-lite` (vitalia overlay) | PHI write obliga audit sync pre-response | `set_hold` + `create_appointment` ambos disparan audit; sweep emit activity event sanitizado |
| `tdd-mandatory` (rule) | RED tests primero, luego código | Tests escritos en orden: domain port → infra model → app services → existing tests extendidos |
| `anti-duplication` (rule) | No duplicar engine `verify_pending_bookings` | Sweep brand-local (`HoldExpirySweepService`) cubre ÚNICAMENTE el lane de la clinica local (appointments con `origin=proactivo_adrian`). El engine `verify_pending_bookings` reconcilia el estado del provider externo — rutas ortogonales, no duplicadas |

## § Plan

### Diseño técnico (Inside-Out)

**Layer domain:**
- `vitalia/.../scheduling/application/ports/scheduling_hold_port.py` — ABC `SchedulingHoldPort` con 3 métodos async:
  - `mark_slot_confirmed(*, tenant_id, clinic_id, slot_id, confirmed) -> None`
  - `set_hold(*, tenant_id, clinic_id, appointment_id, status, expires_at) -> None`
  - `list_expired_holds(*, tenant_id, now) -> list[UUID]`

**Layer infrastructure (modelo):**
- `appointment_clinic_map_model.py` — 3 columnas nuevas: `hold_status`, `hold_expires_at`, `hold_created_by_agent`
- `scheduling_hold_repository.py` — implementa `SchedulingHoldPort` con SQLA 2.0 async:
  - `mark_slot_confirmed`: UPDATE `vitalia_availability_slots` WHERE `(id=slot_id AND tenant_id=t AND clinic_id=c)`
  - `set_hold`: UPDATE `vitalia_appointment_clinic_map` WHERE `(appointment_id=id AND tenant_id=t AND clinic_id=c)`
  - `list_expired_holds`: SELECT `appointment_id` FROM clinic_map WHERE `hold_status='hold_pending_payment' AND hold_expires_at <= now AND tenant_id=t`
- **Anti doble-booking**: columna `has_confirmed_appointment=True` en `vitalia_availability_slots` como lock lógico. El `CREATE` verifica `has_confirmed_appointment=False` antes de marcar (SELECT FOR UPDATE o check + 409).

**Layer application:**
- `create_appointment_service.py` — EXTEND: después del `create_clinic_map`, llama `hold_service.mark_slot_confirmed(True)` + `hold_service.set_hold(hold_pending_payment, now+TTL)`. Nuevo parámetro inyectable `hold_service: SchedulingHoldPort | None = None` (backwards-compatible: si None = no-op para creates de Mateo sin slot).
- `scheduling_hold_service.py` — NEW: service wrapper que lee `tenant_config.adrian_hold_ttl_minutes` (default 30) y llama el port. Audit sync + growth event.
- `hold_expiry_sweep_service.py` — NEW worker ARQ: lista holds expirados → cancela appointment (UPDATE status=expired) + libera slot (`mark_slot_confirmed(False)`) + emite activity event. Idempotente.

**Layer migration:**
- `047_vitalia_hold_status_columns.py` — raw SQL `IF NOT EXISTS` para 3 columnas + 1 índice parcial.

### Batería de tests (TDD RED → GREEN)

| Test | Naturaleza | Por qué |
|---|---|---|
| `test_scheduling_hold_port_abstract.py` | Unit domain | Verifica que `SchedulingHoldPort` no sea instanciable |
| `test_hold_expiry_sweep.py` (SC-10 / V-FN-10) | Unit app | Sweep libera slot + cancela appointment + emite event; idempotente (doble run = no-op) |
| `test_scheduling_hold_service.py` | Unit app | TTL desde tenant_config; audit sync; growth event |
| `test_create_appointment_service.py` (EXTEND) | Unit app | Slot marcado confirmed=True en create + hold set; cross-tenant 403 no regresa slot de otro tenant |
| `test_phi_dual_filter` (arch) | Arch fitness | Dual filter en TODOS los repos scheduling |
| `test_migration_idempotent` | Integration | Re-apply migración 047 = no-op |

### CONN (anti-isla)
- **Consumed by**: `create_appointment_service` (existe y se extiende) → consumed por `scheduling_router` + futuro `book_appointment` tool
- **On-map**: cap `scheduling.mateo-agenda` (extend)
- **Navigable**: Mateo agenda muestra appointments con `origin=proactivo_adrian`; el sweep libera slots que vuelven a aparecer free
- **Notarized**: `HoldExpirySweepService` registrado en ARQ worker settings; `SchedulingHoldPort` en DI factory del router

### Prior-art confirmado
- `has_confirmed_appointment` EXISTE en `vitalia_availability_slots` — REUSE
- `create_appointment_service` EXISTE — EXTEND (no new service)
- `FiscalEmitPort` = patrón ABC port — REUSE patrón
- ARQ worker scaffold EXISTE en `_shared/workers/jobs/` — REUSE estructura

## § TDD — Primera entrada (RED antes de todo código)

Test RED #1 (escrito ANTES de implementar):

```python
# test_hold_expiry_sweep.py — RED: HoldExpirySweepService no existe todavía
from vitalia.scheduling.application.services.hold_expiry_sweep_service import HoldExpirySweepService
```

Este import falla → RED confirmado → luego se implementa.
