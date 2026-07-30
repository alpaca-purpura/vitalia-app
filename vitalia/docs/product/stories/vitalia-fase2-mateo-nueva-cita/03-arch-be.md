---
story_id: vitalia-fase2-mateo-nueva-cita
surface: backend
builder: builder-backend
auditor: auditor-backend
architecture_pattern: ADR-vitalia-004
---

# 03-arch-be — Nueva cita usable (backend)

> Consume con `03-arch.md` (consolidado). Esta hoja detalla el backend.
> DDD Inside-Out · HIPAA-lite dual filter · idempotent migration · response_model mandatory.

## 1. Surfaces tocadas (resumen)

| Capa | Acción | Path |
|---|---|---|
| domain | NEW | `scheduling/domain/availability_check.py` |
| application | NEW | `scheduling/application/services/availability_check_service.py` |
| application | MOD | `scheduling/application/services/create_appointment_service.py` |
| application | MOD | `scheduling/application/services/appointment_status_service.py` |
| application | NEW (port) | `scheduling/application/ports/availability_source_port.py` |
| infrastructure | NEW | `scheduling/infrastructure/repositories/availability_query_repository.py` |
| api | NEW | `scheduling/api/availability_router.py` + `api/dtos/availability_dtos.py` |
| api | MOD | `scheduling/api/agenda_router.py` |
| persistence | MOD | `scheduling/persistence/models/appointment_clinic_map_model.py` (+ start_time/end_time/status mirror) |
| crm | MOD | `crm/api/router.py` (+ POST /patients inline, GET /patients?q=), `crm/application/services/patient_service.py`, `crm/infrastructure/persistence/patient_repository.py` |
| offer | MOD | catalog DTO `ServiceListItemDTO` (BE-1) + `catalog_service` |
| migration | NEW | `vitalia/backend/alembic/versions/050_vitalia_appointment_no_overlap.py` |
| wiring | MOD | `vitalia/backend/src/main.py` (`include_router(availability_router, prefix="/api/v1/scheduling")`) |

## 2. Domain

```python
# scheduling/domain/availability_check.py
# cap: scheduling.mateo-agenda
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

class AvailabilityStatus(StrEnum):
    AVAILABLE = "available"
    BUSY = "busy"
    OUT_OF_HOURS = "out_of_hours"
    NO_SCHEDULE = "no_schedule"

@dataclass(frozen=True)
class TimeRange:
    start: datetime   # UTC tz-aware
    end: datetime
    def overlaps(self, other: "TimeRange") -> bool:
        # half-open [start, end): back-to-back NO solapa (RN-2)
        return self.start < other.end and other.start < self.end

@dataclass(frozen=True)
class AvailabilityCheckResult:
    status: AvailabilityStatus
    conflict_label: str | None        # "se solapa con 09:15" — SIN PHI
    conflict_start: datetime | None
```

Domain puro (sin framework). Tests RED primero: `overlaps()` truth table (10:00-10:30 vs 10:30-11:00 → False; vs 10:15-10:45 → True).

## 3. DTOs (Pydantic v2)

`scheduling/api/dtos/availability_dtos.py` — todos `model_config = ConfigDict(from_attributes=True)`, sin `Any`:

```python
class AvailabilityCheckRequest(BaseModel):
    doctor_id: UUID
    start_time: datetime
    duration_minutes: int = Field(ge=1)

class AvailabilityCheckResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    status: str                    # AvailabilityStatus value
    conflict_label: str | None = None
    conflict_start: datetime | None = None

class FreeDoctorsRequest(BaseModel):
    start_time: datetime
    duration_minutes: int = Field(ge=1)

class FreeDoctorItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    doctor_id: UUID
    doctor_label: str

class FreeDoctorsResponse(BaseModel):
    doctors: list[FreeDoctorItem]

class DayBlockItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    start_time: datetime
    end_time: datetime
    kind: str                      # working_hours | busy

class DayStripResponse(BaseModel):
    doctor_id: UUID
    date_local: str
    blocks: list[DayBlockItem]
```

`crm` DTOs (en `crm/application/dto/patient_dto.py`, EXTEND):
```python
class PatientInlineCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=128)
    phone: str = Field(min_length=6, max_length=24)
    email: EmailStr | None = None
    channel: str                   # walk_in | telefono

class PatientInlineCreateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    patient_id: UUID
    name_masked: str               # "M. López"

class PatientSearchItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    patient_id: UUID
    name_masked: str
    phone_masked: str

class PatientSearchResponse(BaseModel):
    items: list[PatientSearchItem]
    next_cursor: str | None = None
```

`CreateAppointmentRequestDTO` (existente) — reconciliar (D-F): `origin: Literal["walk_in","telefono"]`; `patient_id: UUID` (requerido, no nullable); remover `patient_new_data`. El endpoint deja de stubear el paciente.

`ServiceListItemDTO` (offer, BE-1): añadir `initial_appt_duration_minutes: int | None = None` (hoy solo en detail). Tocar `catalog_service` para poblarlo en la proyección de lista. Bump `_CATALOG_VERSION` NO requerido (no es catálogo de offer-studio, es DTO de servicios) — verificar en build qué endpoint sirve `/servicios`.

## 4. API Routes

`scheduling/api/availability_router.py` (`APIRouter(tags=["scheduling"])`, montado bajo `/api/v1/scheduling`):

| Method | Path | Auth headers | DTO | response_model |
|---|---|---|---|---|
| POST | `/availability/check` | X-Tenant-ID, X-Clinic-ID, X-User-ID, X-User-Role | `AvailabilityCheckRequest` | `AvailabilityCheckResponse` |
| POST | `/availability/free-doctors` | idem | `FreeDoctorsRequest` | `FreeDoctorsResponse` |
| GET | `/availability/day-strip?doctor_id=&date=` | idem (sin PHI en params) | query | `DayStripResponse` |

`scheduling/api/agenda_router.py` (MOD): `POST /appointments` — reconcilia origin, captura overlap→409, recibe `patient_id` resuelto.

`crm/api/router.py` (MOD):
| Method | Path | response_model |
|---|---|---|
| POST | `/patients` | `PatientInlineCreateResponse` |
| GET | `/patients?q=&cursor=&limit=` | `PatientSearchResponse` |

**Cada endpoint:** `@require_phi_access(roles=["admin_clinic","doctor"])` (RBAC check como el create existente: `if user_role not in ALLOWED_PHI_ROLES: 403`), `response_model=`, dual filter en service/repo. `redirect_slashes=False` ya en main.py.

## 5. Repository

`scheduling/application/ports/availability_source_port.py` (Protocol):
```python
class AvailabilitySourcePort(Protocol):
    async def get_working_hours(self, *, tenant_id: UUID, clinic_id: UUID, doctor_id: UUID, day: date) -> list[TimeRange]: ...
    async def get_busy_ranges(self, *, tenant_id: UUID, clinic_id: UUID, doctor_id: UUID, day: date) -> list[TimeRange]: ...
    async def list_active_doctors(self, *, tenant_id: UUID, clinic_id: UUID) -> list[tuple[UUID, str]]: ...
```

`scheduling/infrastructure/repositories/availability_query_repository.py` — implementa el port consumiendo:
- working_hours: `availability_block_service` / `vitalia_availability_slots` (slots materializados de 30min con `has_confirmed_appointment`).
- busy_ranges: query a `vitalia_appointment_clinic_map` (start_time/end_time mirror) WHERE status<>CANCELLED, dual filter.
- active_doctors: `DoctorService.list_active(tenant_id, clinic_id)`.

> **D-B:** verificar si existe link port en `core/luana-core-platform/links/` para clinics availability; si sí, consumir; si no, el adapter en infrastructure adapta los services de clinics sin importar su dominio. Cross-module read controlado.

`crm` PatientRepo (EXTEND `patient_repository.py`):
- `search(tenant_id, clinic_id, q, cursor, limit)` — typeahead. ⚠ name/phone están **pgcrypto-encrypted** → la búsqueda por nombre requiere `pgp_sym_decrypt(name, :kek) ILIKE :q` (lento pero correcto para ≤miles; SC-pacientes-grandes pide cursor + windowed FE; el server pagina). Devuelve **masked** (`name_masked`/`phone_masked`), nunca raw.
- `create_minimal(tenant_id, clinic_id, name, phone, email, channel)` — INSERT con `pgp_sym_encrypt(:val, :kek)` en cols PHI (patrón existente en repo). Devuelve patient_id.
- `find_by_phone(tenant_id, clinic_id, phone)` — RN-9 (D-C FOLD): `pgp_sym_decrypt(phone, :kek) = :phone` dual filter → patient | None.

Todo método: `tenant_id` AND `clinic_id` (dual filter, sin excepción — `test_phi_dual_filter`).

## 6. Application Services

`AvailabilityCheckService`:
```
check(doctor_id, start, duration) →
  working = port.get_working_hours(...)
  if not working: NO_SCHEDULE
  proposed = TimeRange(start, start+duration)
  if not any(proposed within w for w in working): OUT_OF_HOURS
  busy = port.get_busy_ranges(...)
  conflict = first b in busy where proposed.overlaps(b)
  if conflict: BUSY (conflict_label=fmt(conflict.start), conflict_start=conflict.start)
  else: AVAILABLE
free_doctors(start, duration) →
  [d for d in active_doctors if check(d, start, duration).status == AVAILABLE]
```
Half-open overlap (RN-2). Compara instantes absolutos UTC (RN-8 DST-safe). Labels sin PHI.

`CreateAppointmentService` (MOD):
- Pre-insert: `AvailabilityCheckService.check` → si `OUT_OF_HOURS` → `HTTPException 422 OUT_OF_HOURS` (RN-3, SC-bypass-availability). (BUSY no se chequea pre-insert porque el EXCLUDE lo garantiza atómicamente — evita TOCTOU; el chip FE es advisory.)
- Insert: escribe appointment (engine) + clinic_map **con start_time/end_time/status** (mirror, para que el EXCLUDE proteja).
- Captura `IntegrityError` con `orig.sqlstate == '23P01'` → `HTTPException 409 APPOINTMENT_OVERLAP` "Ese horario acaba de ocuparse, elegí otro" (SC-race, SC-half-open-block, SC-create-timeout-retry).
- Resuelve paciente real: recibe `patient_id` (ya creado por endpoint patient inline o por typeahead). **Elimina el stub `uuid.uuid4()`** (líneas 519-524 actuales).
- Audit sync write (ya está) + growth event (ya está).

`appointment_status_service` (MOD): al cancelar/completar, propagar `status` a `vitalia_appointment_clinic_map.status` (para que CANCELLED libere la franja en el EXCLUDE — RN-6, SC-cancelled-reuse).

`PatientInlineService` (crm, EXTEND `patient_service`): `create_minimal` + audit row + opcional `find_by_phone` (RN-9). PHI encrypt vía pattern existente.

## 7. Migración 050 (idempotente, raw SQL)

```python
# 050_vitalia_appointment_no_overlap.py
def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist;")
    op.execute("ALTER TABLE vitalia_appointment_clinic_map ADD COLUMN IF NOT EXISTS start_time timestamptz;")
    op.execute("ALTER TABLE vitalia_appointment_clinic_map ADD COLUMN IF NOT EXISTS end_time timestamptz;")
    op.execute("ALTER TABLE vitalia_appointment_clinic_map ADD COLUMN IF NOT EXISTS status varchar(32);")
    # backfill desde engine appointments
    op.execute("""
        UPDATE vitalia_appointment_clinic_map m
           SET start_time = a.start_time, end_time = a.end_time, status = a.status
          FROM appointments a
         WHERE m.appointment_id = a.id AND m.start_time IS NULL;
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_acm_doctor_range ON vitalia_appointment_clinic_map (doctor_id, start_time);")
    op.execute("""
        DO $$ BEGIN
          IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'no_overlap_per_doctor') THEN
            ALTER TABLE vitalia_appointment_clinic_map
              ADD CONSTRAINT no_overlap_per_doctor
              EXCLUDE USING gist (
                tenant_id WITH =, clinic_id WITH =, doctor_id WITH =,
                tstzrange(start_time, end_time, '[)') WITH &&
              ) WHERE (status <> 'CANCELLED' AND start_time IS NOT NULL);
          END IF;
        END $$;
    """)
```

NUNCA `op.create_table()`/`sa.Enum(create_type=True)`. `down_revision` = obtener via `alembic current` (049). Prod-clone test (§9 consolidado).

> ⚠ El `mapped_column` mirror en `appointment_clinic_map_model.py` debe añadir `start_time`/`end_time`/`status` con `Mapped[datetime | None]` / `Mapped[str | None]` (schema-mirror desde DDL — permitido por `backend-ddd.md § schema-mirror-exception`).

## 8. Tests (TDD RED-first, por capa)

| Test | Capa | Cubre |
|---|---|---|
| `test_availability_overlap.py` | domain | RN-2 half-open truth table |
| `test_availability_check_service.py` | app | status matrix (AVAILABLE/BUSY/OUT_OF_HOURS/NO_SCHEDULE) RN-3/4 |
| `test_availability_query_repository.py` | infra | dual filter, busy_ranges excludes CANCELLED |
| `test_create_appointment_overlap_409.py` | app/integration | 23P01→409 (SC-race), in-horario→422 (SC-bypass), paciente real (no stub) |
| `test_appointment_status_propagates_mirror.py` | app | cancel → clinic_map.status CANCELLED → franja libre (RN-6) |
| `test_patient_inline_create.py` | app/integration | create_minimal + audit row + masked response (SC-crear-paciente, SC-paciente-incompleto) |
| `test_patient_search_typeahead.py` | infra | search masked + cursor (SC-pacientes-grandes) |
| `test_patient_dedup_phone.py` | app | RN-9 find_by_phone (SC-paciente-duplicado) |
| `test_availability_router_phi.py` | api | dual tenant/clinic 403/404 (SC-cross-clinic/cross-tenant), RBAC 403 (SC-rbac) |
| `test_migration_050_exclude.py` | migration | EXCLUDE blocks overlap insert; back-to-back OK; CANCELLED reuse; idempotent re-run |
| arch fitness (EXTEND existing) | arch | response_model, dual_filter, audit_sync, no_phi_in_url, migrations_idempotent |

Mutation HARD (technical_gates) sobre: `create_appointment_service.py` (validación + 409), `availability_check_service.py` (overlap), migración EXCLUDE, PHI dual filter en repos.
