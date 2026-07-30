---
story_id: vitalia-fase2-mateo-nueva-cita
brand: vitalia
arch_version: 1
schema_version: v4.1
architecture_pattern: ADR-vitalia-004
adr_004_compliance: full
architect_run_on: 2026-06-22
verification_nature: funcional
cap_target: scheduling.mateo-agenda
cap_change_type: extend
---

# Contract: Nueva cita usable — hoja full-page leaf (D11)

> Consolidado BE + FE. Surfaces per-surface en `03-arch-be.md` + `03-arch-fe.md`.
> Single source of truth para implementación paralela. NO agentic.

## 0. Context Summary

- **Story:** `vitalia-fase2-mateo-nueva-cita` — hoja full-page "Nueva cita" usable sobre la agenda de Mateo.
- **Architect run on:** 2026-06-22 (today).
- **CONTEXT-BRIEF source:** no había brief (story con spec firmada exhaustiva) → self-ran greps Path B + cap-as-locator resolver (`scheduling.mateo-agenda`).
- **Modules touched:** `scheduling` (dueño, BE+FE), `clinics` (availability + doctors, READ/CONSUME), `crm` (patients inline create, EXTEND), `offer` (1 campo DTO list, BE-1).
- **Skills consultados:**
  - `backend-expert` → DDD inside-out + arch fitness gates + master-data UTC + idempotent migration patterns.
  - `frontend-expert` → FSD-Lite, Server-First, RHF+Zod, React Query keys convention.
  - `design-system-canon § 5 (Storybook SSoT)` → componentes del kit citados por componente + 4 atoms PROMOTE.
  - `frontend-visual-fidelity` → D1 partir de Storybook, D3 scope discipline.
  - `vitalia hipaa-lite` → dual filter tenant+clinic, audit sync write, `@require_phi_access`, PHI masking, response_model whitelist.

### Surface → builder → auditor mapping (PM/dev-team spawn key)

| Surface | Builder | Auditor |
|---|---|---|
| `vitalia/backend/src/modules/vitalia/scheduling/**` (availability endpoint, create validation, repo) | `builder-backend` (workhorse) | `auditor-backend` (flagship) |
| `vitalia/backend/src/modules/vitalia/crm/**` (inline patient create + typeahead search) | `builder-backend` (workhorse) | `auditor-backend` (flagship) |
| `vitalia/backend/src/modules/vitalia/offer/**` (BE-1: 1 campo en list DTO) | `builder-backend` (workhorse) | `auditor-backend` (flagship) |
| `vitalia/backend/alembic/versions/050_*.py` (EXCLUDE constraint en `appointments`) | `builder-backend` (workhorse) | `auditor-backend` (flagship) |
| `vitalia/frontend/src/features/mateo/**` + `app/[tenantId]/(shell-organism)/mateo/agenda/nueva-cita/**` | `builder-frontend` (workhorse) | `auditor-frontend` (flagship) |
| `core/@luana/ui-kit/src/**` (4 atoms PROMOTE) | **`/pm-luana` promotion gate** (NOT a builder) | n/a (kit owns) |

### capability YAML + modules updates required (post-merge, /pm-vitalia Fase F.3)

- `vitalia/docs/product/capabilities/scheduling/mateo-agenda.yaml` — add scenarios: `crear-cita-disponibilidad-chip`, `crear-cita-anti-solape-db`, `crear-paciente-inline`, `reasignar-medico-libre`, `mini-vista-dia-medico`; update `business_rules` (RN-1..RN-10); `access` (admin_clinic + doctor PHI).
- `vitalia/docs/product/modules/scheduling.md` — narrativa "Nueva cita" actualizada (form usable + anti-doble-booking DB).
- (optional) `vitalia/docs/product/capabilities/offer/lisa-servicios.yaml` — note `initial_appt_duration_minutes` ahora en list DTO.

### Architecture gates that must keep passing

BE: `test_phi_dual_filter.py`, `test_audit_log_sync_write.py`, `test_audit_log_row_per_phi_endpoint.py`, `test_response_model_required.py`, `test_growth_studio_event_no_phi.py`, `test_migrations_idempotent.py`, `test_pgcrypto_phi_columns.py`, `test_no_phi_in_url_params.py`.
FE: `test-native-select.test.ts` (no `<select>`), `test-no-div-layout.test.ts`, `test_no_hardcoded_colors.test.ts`, `test_no_voseo_in_copy.test.ts`, `test_server_first.test.ts`, `test_fsd_boundaries.test.ts`, `test_no_cross_feature_imports.test.ts`, `test_no_phi_real_data.test.ts`, `test_page_padding.test.ts`, `test-no-dashboard-route-group.test.ts`.

## Prior art audit

- **EXTEND, no NEW** (cap_change_type=extend, resolver confirmó `main_component`).
- `CrearCitaForm.tsx` + `agenda-schema.ts` (`CreateAppointmentRequestSchema`) ya existen → se reescriben/extienden, NO se crean de cero. El form actual tiene los anti-patterns que la story arregla (UUID textbox del médico, servicio texto libre, hora-fin manual, patient stub fake UUID).
- `create_appointment_service.py` + `POST /api/v1/scheduling/appointments` ya existen → se extienden con validación in-horario + captura 23P01→409 + resolución de paciente real (hoy stub `uuid.uuid4()` línea 522-524, **bug confirmado**).
- Availability free/busy: CONSUME `availability_block_service` + `availability_projection_service` + `vitalia_availability_slots` + `availability_block_model`/`availability_slot_model` (clinics) — NO recrear (`anti-duplication.md`).
- Doctores: CONSUME `GET /api/v1/vitalia/clinics/doctors` (existe, `DoctorListResponse`).
- Patients: EXTEND `crm` (PHI pgcrypto `vitalia_patients`, `patient_service`, `patient_repository`) — alta inline mínima + typeahead search.
- ui-kit: CONSUME `EntityPicker`, `rich-select`, `SmartDatetimePicker`, `TogglePill`, `badge`, `inline-editable`, `EntityInfoCard`, `FormPageScaffold` (todos en `core/@luana/ui-kit/src/` con Storybook).
- **Cross-brand mirror check:** comunify NO agenda con disponibilidad (no mirror). nicolify reseteada. lupulo placeholder. → cero cross-brand mirror.
- **Lift candidate (NOT now):** el cómputo free/busy + condición de solape half-open podrían lift a `core/luana-core-scheduling` si otra marca lo necesita → `/pm-luana` candidate. Documentado, no se ejecuta en esta story.

## Existing systems audit (NO NEW LAYER rule)

### Source of evidence
- [x] Self-run greps (Path B) + cap-as-locator resolver.

### Audit cross-module ejecutado
```
resolve_cap.py vitalia "scheduling.mateo-agenda" --extract
  → main_component: features/mateo/components/agenda/MateoAgendaView.tsx
  → code_ref: scheduling/{infrastructure/repositories, api}
find scheduling/* + clinics/availability* + crm/patient* + core/luana-core-scheduling
grep create_appointment_service / availability_projection_service / EXCLUDE / btree_gist
```

### Sistemas existentes encontrados
| Sistema | Path | Config/enum | Service/Repo | Estado |
|---|---|---|---|---|
| Create appointment | `scheduling/application/services/create_appointment_service.py` | `AppointmentOrigin` enum | `AgendaGridRepositoryImpl.create()` | active — sin validación solape (bug latente) |
| Engine appointment table | `core/luana-core-scheduling/.../appointment_model.py` (`appointments`) | status string | `appointment_repository.py` | active — SIN constraint exclusión |
| Availability free/busy | `clinics/application/availability_projection_service.py` + `availability_block_service.py` | rrule weekly/biweekly | `availability_block_repository.py` + `vitalia_availability_slots` | active — consultable, sin endpoint FE para "libres en franja" |
| Doctores | `clinics/api/doctors_router.py` `GET /api/v1/vitalia/clinics/doctors` | — | `DoctorService` | active — reusable |
| Patients PHI | `crm/.../patient_repository.py` (`vitalia_patients` pgcrypto) | — | `patient_service` | active — sin alta inline mínima ni typeahead search |
| Service catalog | `offer/...` `ServiceListItemDTO` | — | `catalog_service` | active — falta `initial_appt_duration_minutes` en list (solo detail) |

### Decisión por sistema
- **Create appointment**: EXTEND — agregar validación in-horario + captura `23P01`→409 + resolución de paciente real (reemplaza stub).
- **Engine `appointments` table**: EXTEND vía migración brand idempotente (DDL al schema compartido). **NO se edita el modelo del engine ni código `core/luana-core-scheduling/src/`** — solo se añade un constraint a la tabla existente vía SQL de la marca (ver § Architecture Decisions D-A: engine-boundary). Esto NO requiere `/pm-luana` lift (no toca código del engine, no cambia su contrato de columnas; un constraint es una garantía de integridad sobre datos que la marca posee operacionalmente). Si el auditor objeta → escalar `/pm-luana` (documentado abajo).
- **Availability**: EXTEND — endpoint nuevo en scheduling que CONSUME los services de clinics vía port/import controlado (cross-module read permitido por interfaz; ver D-B).
- **Doctores**: CONSUME tal cual (dropdown del FE pega a `GET /clinics/doctors`).
- **Patients**: EXTEND `crm` — `POST /api/v1/crm/patients` (alta inline mínima) + `GET /api/v1/crm/patients?q=` (typeahead search). Misma tabla `vitalia_patients`, mismas garantías PHI.
- **Service catalog**: EXTEND — BE-1, exponer `initial_appt_duration_minutes` en `ServiceListItemDTO` (~1 línea + catalog_service).

## Integration design (CONN) — nada llega como isla

- **Zona/caja:** Agentes → **Mateo** (Operar) → área `mateo.agenda`. La hoja es leaf de la sub-tab Agenda.
- **C (Consumed):** la hoja se consume desde la Agenda (toolbar "+ Nueva cita" + click en slot vacío). Cada endpoint nuevo tiene ≥1 consumidor real (FE de la hoja). El availability endpoint lo consume el chip + la mini-vista + la lista "médicos libres".
- **O (On the map):** vive en `scheduling.mateo-agenda` (cap existente, extend). Hogar declarado.
- **N (Navigable):** reachability path concreto:
  `Agenda (/{tenantId}/mateo/agenda)` → botón "+ Nueva cita" / click slot vacío → `push('/{tenantId}/mateo/agenda/nueva-cita')` → hoja leaf (back-pill "‹ Agenda" vuelve sin perder datos) → Crear → toast + `router.back()` + invalidate agenda query → la grilla refleja la cita.
- **N (Notarized):**
  - BE: `availability_router` nuevo `include_router(... prefix="/api/v1/scheduling")` en `vitalia/backend/src/main.py`; create/patient endpoints ya registrados (extend).
  - FE: nueva ruta estática `app/[tenantId]/(shell-organism)/mateo/agenda/nueva-cita/page.tsx` (Next.js descubre por filesystem); entry wiring en `AgendaToolbar` + `AgendaSlotInteractive` (slot vacío) → `router.push`.
  - El `CrearCitaButton` actual (DropdownMenu→Dialog) **se reemplaza** por navegación a la hoja (la story mata el modal — AC-9).
- **Soft-dep de build (4 atoms PROMOTE):** los tickets FE consumen `FormActionBar`, `Badge variant=success|warning`, `PageHeader back-pill`, `EntityPicker.createAction` desde `@luana/ui-kit`. Precursora: `/pm-luana` promotion proposal (ver § Architecture Decisions D-D + dispatch-plan). Si el kit aún no los tiene al arrancar el build FE → bloqueo soft (los tickets FE arrancan tras el merge del kit, o el architect/PM secuencia la promoción primero).

## 1. Domain Entities

No hay entidad de dominio nueva. Se reusa el `Appointment` del engine + `AppointmentClinicMapModel` brand-local + `Patient` (crm). El availability response es un read-model (DTO), no entidad persistida.

Value/read object nuevo (domain, sin persistencia):
```python
# scheduling/domain/availability_check.py
class AvailabilityStatus(StrEnum):
    AVAILABLE = "available"
    BUSY = "busy"
    OUT_OF_HOURS = "out_of_hours"
    NO_SCHEDULE = "no_schedule"

@dataclass(frozen=True)
class AvailabilityCheckResult:
    status: AvailabilityStatus
    conflict_label: str | None           # "se solapa con [09:15]" — sin PHI
    conflict_start: datetime | None      # para mini-vista
```

## 2. SQLAlchemy 2.0 Models

No model nuevo. Cambio de schema = **constraint** sobre la tabla `appointments` (engine), aplicado por migración brand:

```sql
-- migración 050 (idempotente, raw SQL)
CREATE EXTENSION IF NOT EXISTS btree_gist;
-- guard idempotente: solo crear si no existe el constraint
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'no_overlap_per_doctor'
  ) THEN
    ALTER TABLE appointments
      ADD CONSTRAINT no_overlap_per_doctor
      EXCLUDE USING gist (
        tenant_id WITH =,
        (metadata_info->>'doctor_id') WITH =,
        tstzrange(start_time, end_time, '[)') WITH &&
      ) WHERE (status <> 'CANCELLED');
  END IF;
END $$;
```

> **⚠ DECISIÓN CLAVE (D-E):** el `doctor_id` no es columna en la tabla `appointments` del engine (vive en `vitalia_appointment_clinic_map`). El builder DEBE verificar **dónde** está `doctor_id` accesible para el EXCLUDE. Dos opciones, decidir en build:
> - **(D-E.1 preferida)** Poner el EXCLUDE en `vitalia_appointment_clinic_map` (brand-local, tiene `doctor_id`, `tenant_id`, `clinic_id` columns reales) + agregar a esa tabla las columnas `start_time`/`end_time`/`status` (mirror del appointment) para que el rango sea computable, o referenciar via `appointment_id` con una expresión. Esto mantiene el constraint 100% en superficie brand → **cero ambigüedad de engine-boundary**.
> - **(D-E.2)** Constraint en `appointments` usando `metadata_info->>'doctor_id'` JSONB (requiere que el create persista `doctor_id` en `metadata_info`). Más frágil (JSONB extract en gist).
>
> **Recomendación del architect: D-E.1** — EXCLUDE en `vitalia_appointment_clinic_map` con columnas `start_time`/`end_time`/`status` mirror (la story ya añade esas a la tabla brand). Mantiene engine intacto + dual filter natural (tenant+clinic+doctor). El builder concreta el ALTER TABLE idempotente que añade las 3 columnas mirror + el EXCLUDE. Ver `03-arch-be.md § migración`.

## 3. Pydantic v2 DTOs

Ver `03-arch-be.md § 3` para el listado completo. Esenciales:

```python
# Availability check
class AvailabilityCheckRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    doctor_id: UUID
    start_time: datetime          # UTC, tz-aware
    duration_minutes: int = Field(ge=1)

class AvailabilityCheckResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    status: str                   # available|busy|out_of_hours|no_schedule
    conflict_label: str | None    # sin PHI
    conflict_start: datetime | None

# Free doctors in slot
class FreeDoctorsRequest(BaseModel):
    start_time: datetime
    duration_minutes: int = Field(ge=1)

class FreeDoctorItem(BaseModel):
    doctor_id: UUID
    doctor_label: str             # nombre del médico (no PHI de paciente)

class FreeDoctorsResponse(BaseModel):
    doctors: list[FreeDoctorItem]

# Day strip (mini-vista)
class DayBlockItem(BaseModel):
    start_time: datetime
    end_time: datetime
    kind: str                     # working_hours | busy
class DayStripResponse(BaseModel):
    doctor_id: UUID
    date_local: str
    blocks: list[DayBlockItem]    # busy SIN PHI (solo rangos)

# Inline patient create (BE-6) — mínimo
class PatientInlineCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=128)
    phone: str = Field(min_length=6, max_length=24)
    email: EmailStr | None = None
    channel: str                  # walk_in | telefono
class PatientInlineCreateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    patient_id: UUID              # solo el id — sin PHI fuera de whitelist
    name_masked: str              # "M. López" — masked para confirmación visual

# Typeahead search
class PatientSearchItem(BaseModel):
    patient_id: UUID
    name_masked: str
    phone_masked: str
class PatientSearchResponse(BaseModel):
    items: list[PatientSearchItem]
    next_cursor: str | None
```

`CreateAppointmentRequestDTO` (existente) → reconciliar `origin` (ver BE-7): `walk_in | telefono` (canal); `patient_id` siempre presente (typeahead o recién creado). `patient_new_data` se elimina del payload de create (el alta inline es endpoint aparte → devuelve `patient_id` → el create recibe el id).

## 4. API Routes (tabla completa — HB-71 method+path de TODO write)

| Method | Path | Auth | Request DTO | response_model | Descripción |
|---|---|---|---|---|---|
| POST | `/api/v1/scheduling/availability/check` | Bearer + X-Tenant-ID + X-Clinic-ID + `@require_phi_access` | `AvailabilityCheckRequest` | `AvailabilityCheckResponse` | chip live (médico+franja) — BE-2 |
| POST | `/api/v1/scheduling/availability/free-doctors` | idem | `FreeDoctorsRequest` | `FreeDoctorsResponse` | médicos libres en franja — BE-2 |
| GET | `/api/v1/scheduling/availability/day-strip` | idem (params en body? NO → GET con query, sin PHI) | query: doctor_id, date | `DayStripResponse` | mini-vista del día — BE-2 |
| POST | `/api/v1/scheduling/appointments` | idem | `CreateAppointmentRequestDTO` (reconciliado) | `AppointmentDetailDTO` | crear cita (EXTEND: validación + 409) — BE-4 |
| POST | `/api/v1/crm/patients` | Bearer + X-Tenant-ID + X-Clinic-ID + `@require_phi_access` | `PatientInlineCreateRequest` | `PatientInlineCreateResponse` | alta inline mínima — BE-6 |
| GET | `/api/v1/crm/patients?q=&cursor=` | idem | query: q, cursor, limit | `PatientSearchResponse` | typeahead existing-first — BE-6 |
| GET | `/api/v1/vitalia/clinics/doctors` | Bearer + X-Tenant-ID + X-Clinic-ID | — | `DoctorListResponse` | dropdown médicos — BE-5 (EXISTE, consume) |
| GET | `/api/v1/offer/servicios` (o equivalente) | Bearer + X-Tenant-ID | — | `ServiceListResponse` (con `initial_appt_duration_minutes`) | dropdown servicios — BE-1 (extend DTO) |

> **POST para availability/check + free-doctors:** se usa POST (no GET) porque el body lleva `start_time` + `duration` y, aunque no es PHI, el `doctor_id` + franja es contexto clínico; coherente con `no_phi_in_url_params` y evita query-param leak en logs. `day-strip` es GET (solo doctor_id + date, sin PHI, cacheable). Todas bajo `redirect_slashes=False` (ya en main.py).
> **Idempotencia del create (RN-1 / SC-create-timeout-retry):** la garantía la da el EXCLUDE constraint (un retry que solapa → 409, nunca 2 filas). NO se necesita idempotency-key header adicional (el constraint ES la dedup natural por franja+doctor). Documentado en SC-create-timeout-retry.

## 5. TypeScript Types (Frontend)

camelCase mirror en `agenda-schema.ts` (extend). Ver `03-arch-fe.md § 5`. Esenciales:
```typescript
AvailabilityCheckRequest { doctorId; startTime; durationMinutes }
AvailabilityCheckResponse { status: "available"|"busy"|"out_of_hours"|"no_schedule"; conflictLabel: string|null; conflictStart: string|null }
FreeDoctorsResponse { doctors: { doctorId; doctorLabel }[] }
DayStripResponse { doctorId; dateLocal; blocks: { startTime; endTime; kind: "working_hours"|"busy" }[] }
PatientInlineCreateRequest { name; phone; email: string|null; channel: "walk_in"|"telefono" }
PatientInlineCreateResponse { patientId; nameMasked }
PatientSearchResponse { items: { patientId; nameMasked; phoneMasked }[]; nextCursor: string|null }
// CreateAppointmentRequest reconciliado: origin: "walk_in"|"telefono"; patientId: string (siempre); sin patientNewData
```

## 6. Repository Interfaces

ABC async, todo método recibe `tenant_id` + `clinic_id` (dual filter PHI). Ver `03-arch-be.md § 6`. Nuevos métodos:
- `AvailabilityQueryRepo.get_busy_ranges(tenant_id, clinic_id, doctor_id, day) -> list[(start,end)]` (citas activas, sin PHI)
- `AvailabilityQueryRepo.get_working_hours(tenant_id, clinic_id, doctor_id, day) -> list[(start,end)]` (de slots/blocks)
- `AvailabilityQueryRepo.list_active_doctors(tenant_id, clinic_id) -> list[doctor]`
- `PatientRepo.search(tenant_id, clinic_id, q, cursor, limit) -> (items, next_cursor)` (typeahead, masked)
- `PatientRepo.create_minimal(tenant_id, clinic_id, name, phone, email, channel) -> patient_id`
- `PatientRepo.find_by_phone(tenant_id, clinic_id, phone) -> patient | None` (RN-9 si fold)

## 7. Application Services

- `AvailabilityCheckService` — orquesta busy_ranges + working_hours → status; computa half-open overlap (`s1 < e2 AND s2 < e1`); free-doctors = list_active_doctors menos los con conflicto.
- `CreateAppointmentService` (EXTEND) — pre-insert valida in-horario (RN-3) → 422 si fuera; insert; captura `IntegrityError` (psycopg `23P01`) → 409 `APPOINTMENT_OVERLAP`; resuelve paciente real (recibe `patient_id` ya creado, no stub). Audit sync write (ya está). Growth event (ya está).
- `PatientInlineService` (EXTEND crm) — `create_minimal` (PHI encrypt vía pgcrypto pattern existente) + audit row + opcional dedup `find_by_phone` (RN-9).
- **Transaction boundary:** create_appointment = 1 transacción (engine appointment + clinic_map + audit). El 23P01 hace rollback automático → 409. Patient create = transacción separada (ya está creado antes del create_appointment, por eso el create recibe el id).
- **Idempotency:** EXCLUDE constraint = dedup natural (no key adicional).

## 8. Agentic Surfaces

**N/A — esta story NO toca `copilot/` ni `sales_agent/`.** No hay LangGraph state, tools, prompt slots, ni goldens. (El `origin=proactivo_adrian` es un valor de enum existente que Adrián usa, pero esta story no modifica el flujo agentic — solo reconcilia el enum a canal para el flujo manual de Mateo, sin tocar Adrián.)

## 9. Migration Notes

- **050_vitalia_appointment_no_overlap.py** (idempotente):
  1. `CREATE EXTENSION IF NOT EXISTS btree_gist;`
  2. `ALTER TABLE vitalia_appointment_clinic_map ADD COLUMN IF NOT EXISTS start_time timestamptz;` (+ `end_time`, `status`) — columnas mirror para el rango (D-E.1).
  3. backfill: `UPDATE vitalia_appointment_clinic_map m SET start_time = a.start_time, end_time = a.end_time, status = a.status FROM appointments a WHERE m.appointment_id = a.id AND m.start_time IS NULL;`
  4. `DO $$ ... IF NOT EXISTS (pg_constraint conname='no_overlap_per_doctor') ... EXCLUDE USING gist (tenant_id WITH =, clinic_id WITH =, doctor_id WITH =, tstzrange(start_time, end_time, '[)') WITH &&) WHERE (status <> 'CANCELLED') $$;`
  5. índices de soporte si faltan (`CREATE INDEX IF NOT EXISTS ix_acm_doctor_range ON vitalia_appointment_clinic_map (doctor_id, start_time)`).
- Raw SQL, `IF NOT EXISTS`, `DO $$` guards. NUNCA `op.create_table()` / `sa.Enum(create_type=True)`.
- **Prod-clone test command** (runbook `backend-migrations.md`): `createdb migration_test; pg_dump --schema-only $PROD | psql migration_test; alembic stamp 049; alembic upgrade head; dropdb migration_test`.
- El create service DEBE escribir `start_time`/`end_time`/`status` en `vitalia_appointment_clinic_map` (no solo en el engine appointment) para que el EXCLUDE proteja. Status updates (cancel) deben propagar a la columna mirror — añadir a `appointment_status_service`.

## 9.5 Tests audit (default flip)

`[x] No aplica — 03-arch.md no flipea defaults side-effect.` (No hay feature flag `USE_*`/`ENABLE_*` flipeado; el cambio de comportamiento es vía constraint DB + validación, no flag.)

## 10. File Structure

Ver `03-arch-be.md § 10` + `03-arch-fe.md § 10`. Resumen (NEW vs MODIFIED):

**BE:**
- NEW `scheduling/domain/availability_check.py`
- NEW `scheduling/application/services/availability_check_service.py`
- NEW `scheduling/api/availability_router.py` + `api/dtos/availability_dtos.py`
- NEW `scheduling/infrastructure/repositories/availability_query_repository.py`
- MOD `scheduling/application/services/create_appointment_service.py` (validación + 409 + paciente real)
- MOD `scheduling/api/agenda_router.py` (reconciliar origin, 409 handling)
- MOD `scheduling/application/services/appointment_status_service.py` (propagar status a mirror cols)
- MOD `crm/api/router.py` (+ `POST /patients` inline, `GET /patients?q=`) + `crm/application/services/patient_service.py` + repo
- MOD `offer/...catalog DTO` (BE-1, `initial_appt_duration_minutes`)
- NEW `vitalia/backend/alembic/versions/050_vitalia_appointment_no_overlap.py`
- MOD `vitalia/backend/src/main.py` (`include_router(availability_router)`)
- MOD `scheduling/persistence/models/appointment_clinic_map_model.py` (+ start_time/end_time/status mirror cols)

**FE:**
- NEW `app/[tenantId]/(shell-organism)/mateo/agenda/nueva-cita/page.tsx` (Server) + `loading.tsx` + `error.tsx`
- NEW `features/mateo/components/nueva-cita/NuevaCitaView.tsx` (client root)
- NEW `features/mateo/components/nueva-cita/{ServicePicker,DoctorPicker,AvailabilityChip,DayAvailabilityStrip,FreeDoctorsList,PatientPickerWithCreate}.tsx`
- NEW `features/mateo/api/nueva-cita.ts` (React Query hooks: useAvailabilityCheck, useFreeDoctors, useDayStrip, usePatientSearch, useCreatePatientInline)
- NEW `features/mateo/store/nueva-cita-store.ts` (Zustand UI state)
- MOD `features/mateo/types/agenda-schema.ts` (extend: availability + reconcile origin + patient inline)
- MOD `features/mateo/components/agenda/CrearCitaForm.tsx` → **DEPRECATE/REMOVE** (reemplazado por NuevaCitaView); o reescribir como wrapper. Decisión: REMOVE (los tests del legacy form se migran).
- MOD `features/mateo/components/agenda/CrearCitaButton.tsx` → reemplaza Dialog por `router.push('.../nueva-cita')`
- MOD `features/mateo/components/agenda/AgendaSlotInteractive.tsx` → click slot vacío → push con fecha/hora prellenada
- MOD `features/mateo/index.ts` (public API exports)

## 11. Cross-Cutting Concerns

- **Tenant isolation + clinic (hipaa-lite):** TODA query availability/create/patient con `tenant_id` AND `clinic_id`. Repos reciben ambos. Cross-clinic → 403, cross-tenant → 404 (SC-cross-clinic, SC-cross-tenant).
- **PHI:** `@require_phi_access(roles=[admin_clinic, doctor])` en availability/create/patient endpoints. `response_model=` whitelist en todos. `name_masked`/`phone_masked` server-side (nunca raw). Availability/day-strip responses NO llevan PHI de paciente (solo rangos + nombre de médico). Audit log sync write pre-response en create + patient create.
- **Currency:** `currency_override` ya está en create. Availability no maneja dinero.
- **Master data:** `DateTime(timezone=True)`, store UTC; FE ingresa/muestra en tz IANA del tenant (`useTenantLocale`/`formatTenantDate*`). Overlap compara instantes absolutos (DST-safe — RN-8, SC-i18n-tz).
- **Spanish neutro LatAm:** UI strings + error messages + chip labels (sin voseo). `test_no_voseo_in_copy`.
- **Native-first dev:** lint/tests host (`${WS}/.venv/bin/`, `npx`), nunca docker exec.

## 12. Architecture Fitness Impact

Gates listados en § 0. Allowlist updates esperados: NINGUNO que crezca. El `availability_router` nuevo debe pasar `response_model_required` + `no_phi_in_url_params` + `audit_log` (create endpoint). El EXCLUDE constraint debe pasar `test_migrations_idempotent`. Si algún allowlist necesita shrink (e.g. legacy `desde_paciente_existente` origin string), removerlo.

## 13. capability YAML + modules updates required

Listado en § 0 (post-merge /pm-vitalia Fase F.3). Header `# cap: scheduling.mateo-agenda` en todos los archivos nuevos (Python líneas 1-3, TS líneas 1-3).

## 14. Test Surfaces (TDD-mandatory · RED first)

- **BE domain:** `availability_check` overlap half-open (RN-2), out_of_hours (RN-3), no_schedule (RN-4).
- **BE infra:** availability_query_repo busy_ranges + working_hours (dual filter); patient repo search + create_minimal + find_by_phone.
- **BE app:** AvailabilityCheckService status matrix; CreateAppointmentService 23P01→409 + in-horario→422 + paciente real.
- **BE API/integration:** availability endpoints (dual tenant/clinic 403/404), create 409 on overlap (SC-race, SC-bypass-availability), patient inline create + audit row, RBAC 403 (SC-rbac), PHI not leaked (SC-phi-audit).
- **BE migration:** EXCLUDE prevents overlap insert; CANCELLED reuse (RN-6); back-to-back OK (RN-2).
- **FE hook:** useAvailabilityCheck debounce + revalidate on change (SC-revalida-cambio), useCreatePatientInline.
- **FE component:** AvailabilityChip states, DayAvailabilityStrip render, FreeDoctorsList reassign, PatientPickerWithCreate, NuevaCitaView fin>inicio validation.
- **FE store:** nueva-cita-store transitions.
- **E2E Playwright (autenticado dev-app, write real):** SC-happy, SC-crear-paciente, SC-solape, SC-reasignar, SC-mini-vista, SC-empty-*, SC-fin-invalido, SC-a11y (axe wcag2aa), SC-i18n-tz. SC-cross-tenant/SC-bypass/SC-rbac/SC-phi-audit = BE integration (no UI).

## 15. Research Notes (date-aware)

- **PostgreSQL EXCLUDE constraint + btree_gist** — `https://www.postgresql.org/docs/current/rangetypes.html` + `ddl-constraints` (exclusion constraints), accessed 2026-06-22. Pattern: `EXCLUDE USING gist (... WITH =, tstzrange(...) WITH &&)`. Half-open `[)` = back-to-back no overlaps. Partial `WHERE status<>CANCELLED` = cancelled libera la franja. 23P01 (`exclusion_violation`) → map a 409. Mi conocimiento del modelo cubre este patrón (pre-cutoff estable); verificado contra docs canónicas hoy. Por qué EXCLUDE sobre lock optimista: race-proof declarativo, sin lógica de app, inmune a concurrencia (SC-race garantizado a nivel DB, no UI).
- **asyncpg/SQLAlchemy IntegrityError → 23P01** — `https://docs.sqlalchemy.org/en/20/` IntegrityError wrapping; `pgcode == '23P01'` via `orig.sqlstate`. Accessed 2026-06-22.
- **Half-open interval overlap** `s1 < e2 AND s2 < e1` — algoritmia estándar (00-research-availability.md citó PostgreSQL rangetypes, Cybertec).
- **UX (chip + reassign + manual input):** Tebra/Jane/Acuity/Cal.com — síntesis en 00-research-availability.md.
- **Storybook = SSoT visual** — `design-system-canon § 5`, accessed 2026-06-22. Componentes del kit consumidos por story id (ver § FE).

## 16. Open Questions for PM

1. **RN-9 (dedup paciente inline por teléfono):** FOLD en esta story (ticket BE liviano `find_by_phone` + FE prompt "¿usar el existente?"). Justificación: es un guard de calidad de datos PHI de bajo costo (1 query + 1 branch UI), el SC ya está escrito (SC-paciente-duplicado), y separarlo a fast-follow dejaría un hueco de datos duplicados desde el día 1. **Decisión del architect: FOLD** (documentado en § Architecture Decisions D-C). PM ratifica o descopa.
2. **DayAvailabilityStrip lift:** se queda como componente feature (`features/mateo/components/nueva-cita/`) — lift-candidate a `core/luana-core-scheduling` NO ahora (comunify no agenda con disponibilidad). PM nota el candidate para futuro.
3. **Engine-boundary del EXCLUDE (D-E.1):** el constraint vive en `vitalia_appointment_clinic_map` (brand-local) → NO toca `core/luana-core-scheduling/src/`. Si el auditor-backend lo considera engine-touch, escalar `/pm-luana`. Architect afirma que NO es lift (cero edición de código engine).

## § Architecture Decisions

- **D-A (engine-boundary, anti-cross-brand-pollution):** NO se edita `core/luana-core-scheduling/src/` ni `appointment_model.py`. La garantía anti-solape se implementa enteramente en superficie brand (`vitalia_appointment_clinic_map` + columnas mirror + EXCLUDE) → respeta `anti-duplication.md` + engine boundary sin lift. La memoria `engine-boundary-consume-not-mount` aplica: consumimos los availability services de clinics + replicamos el rango en tabla brand, no montamos ni editamos el engine.
- **D-B (cross-module read availability):** `scheduling` lee free/busy de `clinics` vía import del service (cross-module dentro del mismo brand). Default DDD prohíbe cross-module imports salvo `copilot`. Aquí se usa el patrón **port/interface**: `scheduling` define `AvailabilitySourcePort` y la implementación adapta `availability_block_service`/`availability_projection_service` de clinics (o, si ya hay un link port en `core/luana-core-platform/links/`, consumirlo). El builder verifica si existe link port; si no, crea el adapter en infrastructure sin import directo del dominio de clinics. **Rationale:** evita acoplar dominios; coherente con `backend-ddd.md`.
- **D-C (RN-9 FOLD):** dedup paciente inline por teléfono se incluye (ticket BE-6 extendido + FE prompt). Bajo costo, cierra hueco PHI. Ver Open Question 1.
- **D-D (4 atoms PROMOTE a @luana/ui-kit):** `FormActionBar`, `Badge variant=success|warning`, `PageHeader back-pill`, `EntityPicker.createAction` son transversales (CORE). **NO se generan tickets de marca que editen `core/@luana/ui-kit/src/`.** Secuencia: el architect señala el handoff a `/pm-luana` (promotion proposal `docs/promotion-protocol/proposals/2026-06-22-ui-kit-nueva-cita-atoms.md`). Los tickets FE de vitalia CONSUMEN estos atoms (soft-dep de build). Si el kit no los tiene al arrancar, el build FE espera a la promoción (dispatch-plan documenta el orden). Contrato API de cada atom en `mockups/PROPOSED-CANON-ATOMS.md`.
- **D-E (EXCLUDE en clinic_map, no en engine table):** ver § 2. EXCLUDE sobre `vitalia_appointment_clinic_map` con columnas mirror `start_time`/`end_time`/`status` + dual filter natural (tenant+clinic+doctor). Preferida sobre JSONB extract en `appointments`.
- **D-F (origin reconciliation, BE-7):** `origin` pasa de `walk_in|telefono|proactivo_adrian|portal` (+ legacy FE `existing_patient`/`desde_paciente_existente`) a **canal** puro para el flujo Mateo: el create recibe `origin ∈ {walk_in, telefono}` y `patient_id` siempre resuelto (typeahead o recién creado inline). El enum de dominio `AppointmentOrigin` conserva `proactivo_adrian`/`portal` (otros flujos). Se remueve `existing_patient`/`desde_paciente_existente` del path de create de Mateo (la existencia del paciente es ortogonal: la decide el typeahead). Migración: actualizar `CreateAppointmentRequestSchema` (FE) + validación del endpoint (BE) + el check legacy `desde_paciente_existente` (línea 496) se elimina.
- **D-G (entry point = navegación, no modal):** el `CrearCitaButton` (DropdownMenu→Dialog) se reemplaza por `router.push('.../nueva-cita')`. AC-9: hoja full-page, data-safe, back-pill. El Dialog modal muere (pierde datos al click-afuera). Click en slot vacío (`AgendaSlotInteractive`) → push con `?date=&time=` prellenado.
