---
story_id: vitalia-fase2-lisa-doctores
surface: backend
architecture_pattern: ADR-vitalia-004
adr_004_compliance: full
---

# 03-arch-be · Backend contract — Staff (clinics module EXTEND)

> Owner: `builder-backend` (Sonnet). Auditor: `auditor-backend` (Opus).
> Module: `clinics`. Inside-Out DDD. Consume `luana-core-assets` + `luana-core-scheduling`. `python-dateutil` for recurrence.
> ALL queries dual-filter (tenant_id + clinic_id). ALL mutations audit-log sync pre-response. ALL endpoints `response_model=` + RBAC `admin_clinic`.

## § 1 — Domain Entities (`clinics/domain/`)

### `doctor.py::Doctor` (frozen dataclass, NEW)
```
id: UUID
tenant_id: UUID
clinic_id: UUID
first_name: str
last_name: str
dni: str                      # PII (pgcrypto at-rest)
email: str                    # PII
phone: str | None             # PII
specialty: str | None
credential: str               # PII (colegio medico)
credential_country: str       # PE|AR|MX|CL (ISO-2)
years_experience: int | None
languages: list[str]
bio_inputs_notes: str | None
bio_links: list[str]
bio_public: BioPublic | None  # {resumen, formacion, enfoque}
avatar_key: str | None        # R2 key
visible_en_landing: bool      # default False
active: bool                  # default True (soft-deactivate)
created_at / updated_at / deleted_at
```
Display helper: `display_name -> "Dr(a). {first} {last}"`.

### `bio.py::BioPublic` (frozen dataclass)
`resumen: str | None`, `formacion: str | None`, `enfoque: str | None`. Editable secciones.

### `availability_block.py::AvailabilityBlock` (frozen dataclass, NEW)
```
id: UUID
tenant_id: UUID
clinic_id: UUID
doctor_id: UUID
kind: Literal["recurrent", "one_off"]
# recurrent fields:
day_of_week: int | None       # 0=Mon..6=Sun
start_time: time
end_time: time
freq: Literal["weekly", "biweekly"] | None
end_condition_kind: Literal["end_date","occurrences","open_ended"] | None
end_date: date | None
occurrences: int | None
# one_off fields:
specific_date: date | None
created_at / updated_at / deleted_at
```
**Domain validation (`recurrence-end-condition-required`):** si `kind=="recurrent"` -> exactamente uno de {end_date, occurrences, open_ended=True} debe estar presente; sino `ValueError("Un bloque recurrente requiere condicion de fin")`. Si `kind=="one_off"` -> `specific_date` requerido. `start_time < end_time` siempre.

### `credential_country.py` enum (StrEnum): `PE, AR, MX, CL` (extensible).

## § 2 — SQLAlchemy 2.0 Models (`clinics/infrastructure/models/`)

### `doctor_model.py::VitaliaDoctorModel` -> `vitalia_doctors`
- `mapped_column()` SA 2.0. `id: Mapped[UUID] = mapped_column(PgUUID, primary_key=True, default=uuid4)`.
- `tenant_id` (PgUUID, nullable=False, index=True), `clinic_id` (PgUUID, nullable=False, index=True).
- PII columns **stored as BYTEA ciphertext** (`dni_encrypted`, `email_encrypted`, `phone_encrypted`, `credential_encrypted`) — write via `pgp_sym_encrypt`, read via `pgp_sym_decrypt` in repo. (pattern: `channel_sync_state.oauth_token_encrypted`).
- `specialty: Mapped[str|None] String(64)`, `credential_country: Mapped[str] String(2)`, `years_experience: Mapped[int|None]`, `languages: Mapped[list] JSONB default list`.
- `bio_inputs_notes: Mapped[str|None] Text`, `bio_links: Mapped[list] JSONB default list`, `bio_public: Mapped[dict|None] JSONB`.
- `avatar_key: Mapped[str|None] String(512)`, `visible_en_landing: Mapped[bool] default False`, `active: Mapped[bool] default True`.
- `created_at/updated_at` (DateTime(timezone=True), server_default func.now()), `deleted_at: Mapped[datetime|None]`.
- `__table_args__`: `UniqueConstraint("tenant_id","dni_hash", name="uq_vitalia_doctors_tenant_dni")` — **dni unique via deterministic hash column** `dni_hash String(64)` (HMAC-SHA256 with KEK) because encrypted BYTEA isn't comparable. Index `(tenant_id, clinic_id)`, `(tenant_id, specialty)`, `(tenant_id, active)`, `(tenant_id, visible_en_landing, active)`.

### `availability_block_model.py::VitaliaAvailabilityBlockModel` -> `vitalia_availability_blocks`
- `id, tenant_id(idx), clinic_id(idx), doctor_id(idx, FK vitalia_doctors.id)`, `kind String(16)`, `day_of_week Integer|None`, `start_time Time`, `end_time Time`, `freq String(16)|None`, `end_condition_kind String(16)|None`, `end_date Date|None`, `occurrences Integer|None`, `specific_date Date|None`, timestamps + `deleted_at`.

### `availability_slot_model.py::VitaliaAvailabilitySlotModel` -> `vitalia_availability_slots`
- `id, tenant_id(idx), clinic_id(idx), doctor_id(idx)`, `block_id UUID(idx, FK availability_blocks.id ON DELETE CASCADE)`, `slot_date Date(idx)`, `start_ts DateTime(tz)`, `end_ts DateTime(tz)`, `has_confirmed_appointment Boolean default False`, timestamps + `deleted_at`. Index `(tenant_id, doctor_id, slot_date)`.

> `vitalia_doctor_extensions` (existente) NO se modifica; su `doctor_id` referenciara `vitalia_doctors.id` (resuelto en application, sin JOIN hard cross-module).

## § 3 — Pydantic v2 DTOs (`clinics/api/dtos.py`)

`model_config = ConfigDict(from_attributes=True)`. Explicit types, no `Any`.

| DTO | Purpose | PII masking |
|---|---|---|
| `DoctorCreateRequest` | POST body | full (server-side) |
| `DoctorListItemDTO` | grid card | `dni`/`email`/`phone` MASKED |
| `DoctorListResponse` | `{items: list[DoctorListItemDTO], total, page, page_size}` | — |
| `DoctorDetailDTO` | workspace (admin only) | unmasked (admin_clinic RBAC) |
| `DoctorPatchRequest` | PATCH (bio/active/visible/avatar_key) | — |
| `BioPublicDTO` | `{resumen, formacion, enfoque}` | — |
| `GenerateBioRequest` | `{}` (uses stored inputs) | — |
| `GenerateBioResponse` | `BioPublicDTO` | — |
| `AvailabilityBlockCreateRequest` | discriminated by `kind` | — |
| `AvailabilityBlockDTO` | block read | — |
| `AvailabilityBlocksResponse` | `{blocks: list[AvailabilityBlockDTO]}` | — |
| `DeleteBlockResponse` | `{deleted: bool, preserved_appointments: int}` | — |
| `PublicDoctorDTO` | public endpoint — **ALLOW-LIST only** | `{display_name, specialty, avatar_url, years_experience, languages, bio_public, credential_label?}` |
| `PublicDoctorsResponse` | `{doctors: list[PublicDoctorDTO]}` | — |
| `AssetUploadResponse` | `{key, url}` | — |

**Channel guard (`public-endpoint-phi-allowlist`):** `PublicDoctorDTO` is constructed by an explicit allow-list serializer fn `to_public_dto(doctor)` that maps ONLY the 7 allow-listed fields. It physically cannot emit `dni/email/phone/kpis`. Arch test `test_public_doctors_allowlist.py` asserts the DTO has NO PHI field names.

## § 4 — API Routes

All under `/api/v1/vitalia/clinics/doctors` (entidad doctor). Bearer + `X-Tenant-ID` + `X-User-Role` headers. `response_model=` mandatory. `redirect_slashes=False` (app-level, ya configurado).

| Method | Path | Auth | Request | response_model | Notes |
|---|---|---|---|---|---|
| GET | `/api/v1/vitalia/clinics/doctors` | admin_clinic+read roles | query `clinic,q,specialty,active,page,page_size` | `DoctorListResponse` | masked list; server-side pagination (SC-9) |
| POST | `/api/v1/vitalia/clinics/doctors` | admin_clinic | `DoctorCreateRequest` | `DoctorDetailDTO` (201) | validates credential; 422 invalid; 409 dni dup (SC-2,SC-5); audit `doctor.created` |
| GET | `/api/v1/vitalia/clinics/doctors/{id}` | admin_clinic | — | `DoctorDetailDTO` | dual-filter; 404 cross-tenant + audit (SC-4) |
| PATCH | `/api/v1/vitalia/clinics/doctors/{id}` | admin_clinic | `DoctorPatchRequest` | `DoctorDetailDTO` | autosave bio/active/visible/avatar_key; audit `doctor.updated`/`doctor.deactivated` |
| POST | `/api/v1/vitalia/clinics/doctors/{id}/generate-bio` | admin_clinic | `GenerateBioRequest` | `GenerateBioResponse` | bio-gen from stored inputs |
| GET | `/api/v1/vitalia/clinics/doctors/{id}/availability-blocks` | admin_clinic | — | `AvailabilityBlocksResponse` | — |
| POST | `/api/v1/vitalia/clinics/doctors/{id}/availability-blocks` | admin_clinic | `AvailabilityBlockCreateRequest` | `AvailabilityBlockDTO` (201) | expand recurrence + materialize slots; audit `doctor.availability_block_created` |
| PATCH | `/api/v1/vitalia/clinics/doctors/{id}/availability-blocks/{block_id}` | admin_clinic | `AvailabilityBlockCreateRequest` | `AvailabilityBlockDTO` | reproject future only |
| DELETE | `/api/v1/vitalia/clinics/doctors/{id}/availability-blocks/{block_id}` | admin_clinic | — | `DeleteBlockResponse` | retire future slots w/o appt; preserve confirmed (SC-1d, SC-3b); audit `doctor.availability_block_deleted` w/ preserved_appointments |
| POST | `/api/v1/vitalia/assets/upload` | admin_clinic | multipart `file, kind` | `AssetUploadResponse` | proxy -> AssetsService.upload_asset -> R2; 10MB + content-type allow-list |
| GET | `/api/public/clinic/{tenant_slug}/doctors` | **none (public)** | — | `PublicDoctorsResponse` | allow-list serializer; only `visible_en_landing AND active`; channel-guarded |

**Idempotency on writes:** POST doctor uses natural key `(tenant_id, dni_hash)` unique constraint -> 409 on dup (SC-5 race). Availability block create is non-idempotent but bounded (reproject deletes+recreates future slots in a transaction). Avatar upload returns new key per call (caller PATCHes).

## § 5 — Repository Interfaces (`clinics/application/ports/` + `infrastructure/repositories/`)

### `DoctorRepository(PhiRepositoryBase)` — ABC + impl
```python
async def get_by_id(self, entity_id, *, tenant_id, clinic_id) -> Doctor | None       # validate_dual_filter; decrypt PII
async def list_by_filter(self, *, tenant_id, clinic_id, q=None, specialty=None, active=None, page=1, page_size=24) -> tuple[list[Doctor], int]
async def get_by_dni_hash(self, dni_hash, *, tenant_id, clinic_id) -> Doctor | None
async def create(self, doctor: Doctor, *, tenant_id, clinic_id) -> Doctor            # pgp_sym_encrypt PII; dni_hash
async def update(self, doctor: Doctor, *, tenant_id, clinic_id) -> Doctor
async def soft_deactivate(self, entity_id, *, tenant_id, clinic_id) -> None
async def list_public(self, *, tenant_id, clinic_id) -> list[Doctor]                  # visible_en_landing AND active
```
SA 2.0 `select(Model).where(Model.tenant_id==..., Model.clinic_id==..., Model.deleted_at.is_(None))`. PII encrypt/decrypt via `pgp_sym_encrypt`/`pgp_sym_decrypt` raw expr with KEK from `KEKClient.from_env()`.

### `AvailabilityBlockRepository(PhiRepositoryBase)` — block + slot CRUD
```python
async def list_blocks(self, *, tenant_id, clinic_id, doctor_id) -> list[AvailabilityBlock]
async def get_block(self, block_id, *, tenant_id, clinic_id) -> AvailabilityBlock | None
async def create_block(self, block, slots, *, tenant_id, clinic_id) -> AvailabilityBlock   # transactional
async def update_block(self, block, new_slots, *, tenant_id, clinic_id) -> AvailabilityBlock
async def delete_block(self, block_id, *, tenant_id, clinic_id) -> int                      # returns preserved_appointments count
async def count_future_confirmed(self, block_id, *, tenant_id, clinic_id) -> int
```

> `availability_block` data is NOT PHI (it's scheduling availability, not patient data) — but lives under `clinics` and uses dual-filter for consistency + cross-clinic isolation. Repo inherits `PhiRepositoryBase` for the dual-filter contract.

## § 6 — Application Services (`clinics/application/`)

### `credential_validator.py::validate_credential(credential, country) -> None`
`credential-validator-country-specific`: PE -> CMP numeric (`^\d+$`); AR -> matricula nacional+provincial (`^\d+/\d+$` or both present); MX -> cedula profesional (`^\d{7,8}$`); CL -> registro nacional (`^\d+$`). Invalid -> raise `CredentialValidationError(field="credential", message="La credencial {label} debe ser ...")` -> 422.

### `availability_projection_service.py::AvailabilityProjectionService`
- `project_block(block: AvailabilityBlock) -> list[Slot]` using `dateutil.rrule`:
  - recurrent weekly/biweekly: `rrule(WEEKLY, interval=1|2, byweekday=block.day_of_week, dtstart=next_occurrence, until=end_date)` or `count=occurrences`; `open_ended` -> `until=today+90d`.
  - one_off: single date.
  - Each occurrence -> slots at tenant slot granularity (default 30min) between start_time/end_time, in UTC (tenant tz -> UTC conversion).
- `reproject_future(block) -> list[Slot]`: delete future slots w/o appt, recreate from rrule for `slot_date >= today`.
- `retire_future(block_id) -> int`: delete future slots w/o appt; count + preserve `has_confirmed_appointment` slots; return preserved count.

### `doctor_service.py::DoctorService`
Orchestrates: create (validate credential -> encrypt -> persist -> audit sync -> telemetry), update (autosave fields -> audit), deactivate (soft + scheduling exclude + audit), list (mask), get (dual-filter). Transaction boundary: 1 session per request; audit write + mutation in same session (atomic). Telemetry best-effort post-commit.

### `bio_generation_service.py::BioGenerationService` (D-4, NOT agentic)
`generate(doctor) -> BioPublic`: builds extractive prompt from `bio_inputs_notes + bio_links + file metadata`; single LLM call via `luana_core_llm.router` with guardrail "usa SOLO el material; no inventes"; parse 3 sections. Timeout + fallback (empty sections + error message) per `tessl__graceful-degradation`. Optional brand voice anchor from `PersonalityProfile.system_instruction` (read-only via port). NO PHI, NO state, NO goldens.

### `public_doctor_serializer.py::to_public_dto(doctor) -> PublicDoctorDTO`
Allow-list mapper (channel guard). Resolves `avatar_url` from `avatar_key` (R2 public URL). `credential_label` optional ("CMP 12345" or "Colegiado/a" per clinic config).

## § 7 — Scheduling integration (CONSUME)

Materialized `vitalia_availability_slots` are read by `scheduling` create-appointment flow. Deactivated/excluded doctors (`active=False`) are filtered out of "crear cita" form (`doctor-soft-deactivate`). No engine modification — slots table is brand-local, scheduling reads it via existing repos (resolve doctor_id -> slots in application layer).

## § 8 — Wiring (`vitalia/backend/src/main.py`)

```python
from src.modules.vitalia.clinics.api.doctors_router import router as doctors_router
from src.modules.vitalia.clinics.api.public_doctors_router import router as public_doctors_router
from src.modules.vitalia.clinics.api.assets_proxy_router import router as assets_proxy_router
app.include_router(doctors_router, prefix="/api/v1/vitalia/clinics/doctors", tags=["staff"])
app.include_router(public_doctors_router, prefix="/api/public/clinic", tags=["public"])
app.include_router(assets_proxy_router, prefix="/api/v1/vitalia/assets", tags=["assets"])
```
(copy wiring pattern from `nicolify/backend/src/main.py` for assets consumption.)

## § File Structure (BE)

```
vitalia/backend/src/modules/vitalia/clinics/
  domain/
    doctor.py                          NEW
    bio.py                             NEW
    availability_block.py              NEW
    credential_country.py             NEW
  infrastructure/models/
    doctor_model.py                    NEW
    availability_block_model.py        NEW
    availability_slot_model.py         NEW
  infrastructure/repositories/
    doctor_repository.py               NEW (PhiRepositoryBase)
    availability_block_repository.py   NEW (PhiRepositoryBase)
  application/
    ports/doctor_repo_port.py          NEW (ABC)
    ports/availability_repo_port.py    NEW (ABC)
    credential_validator.py            NEW
    availability_projection_service.py NEW (dateutil.rrule)
    doctor_service.py                  NEW
    bio_generation_service.py          NEW (NOT agentic)
    public_doctor_serializer.py        NEW (allow-list)
  api/
    doctors_router.py                  NEW
    public_doctors_router.py           NEW
    assets_proxy_router.py             NEW
    dtos.py                            MODIFY (add doctor DTOs)
vitalia/backend/alembic/versions/
  036_f2_s8_vitalia_lisa_staff.py      NEW (down_revision=035)
vitalia/backend/src/main.py            MODIFY (3 include_router)
vitalia/backend/tests/architecture/
  test_public_doctors_allowlist.py     NEW (channel guard)
vitalia/backend/tests/modules/vitalia/clinics/
  test_doctor_repository.py            NEW (dual-filter)
  test_credential_validator.py        NEW
  test_availability_projection.py     NEW (rrule expansion)
  test_availability_block_mutable.py  NEW (reproject/delete-preserve)
  test_bio_generation_service.py      NEW (no-invent guardrail)
  test_doctor_cross_tenant.py         NEW (SC-4 + audit)
  test_doctor_dni_race.py             NEW (SC-5 409)
  test_doctors_api.py                 NEW (response_model + RBAC + masking)
  test_public_doctors_endpoint.py     NEW (allow-list + visible+active filter)
```
